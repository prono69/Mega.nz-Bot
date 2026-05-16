# Copyright (c) 2021 - Present partiallywritten
# Author: https://github.com/partiallywritten
# Project: https://github.com/partiallywritten/Mega.nz-Bot
# Description: Handle mega.nz download function


import re
from uuid import uuid4
from os import path, makedirs

from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from megadl import CypherClient
from megadl.lib.megatools import MegaTools


@CypherClient.on_message(
    filters.regex(r"^(https?:\/\/mega\.nz\/(file|folder|#)?.+)|^\/Root\/.+")
)
@CypherClient.run_checks
async def dl_from(client: CypherClient, msg: Message):
    _mid = msg.id
    _usr = msg.from_user.id

    

    # ✅ UNIQUE folder per request
    dlid = f"{client.dl_loc}/{_usr}/{uuid4().hex}"

    # ✅ store using message id (NOT user id)
    client.glob_tmp[_mid] = {
        "url": msg.text,
        "dlid": dlid,
        "user": _usr,
    }

    await msg.reply(
        "**Select what you want to do 🤗**",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Download 💾", callback_data=f"dwn_mg-{_mid}")],
                [InlineKeyboardButton("Info ℹ️", callback_data=f"info_mg-{_mid}")],
                [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{_usr}")],
            ]
        ),
    )


prv_rgx = r"(\/Root\/?.+)"


@CypherClient.on_callback_query(filters.regex(r"dwn_mg?.+"))
@CypherClient.run_checks
async def dl_from_cb(client: CypherClient, query: CallbackQuery):
    _mid = int(query.data.split("-")[1])

    data = client.glob_tmp.get(_mid)
    if not data:
        return await query.answer("Expired ❌", show_alert=True)

    url = data["url"]
    dlid = data["dlid"]
    qusr = data["user"]

    qcid = query.message.chat.id

    # private mode config
    conf = None
    if client.is_public:
        udoc = await client.database.is_there(qusr, True)
        if not udoc and re.match(prv_rgx, url):
            return await query.edit_message_text(
                "`You must be logged in first to download this file 😑`"
            )
        if udoc:
            email = client.cipher.decrypt(udoc["email"]).decode()
            password = client.cipher.decrypt(udoc["password"]).decode()
            proxy = f"--proxy {udoc['proxy']}" if udoc["proxy"] else ""
            conf = f"--username {email} --password {password} {proxy}"

    # ✅ create folder safely
    makedirs(dlid, exist_ok=True)

    resp = await query.edit_message_text(
        "`Your download is starting 📥...`", reply_markup=None
    )

    cli = MegaTools(client, conf)

    try:
        # ✅ Download
        f_list = await cli.download(
            url,
            qusr,
            qcid,
            resp.id,
            path=dlid,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{qusr}")]
                ]
            ),
        )

        if not f_list:
            return await resp.edit("Download failed ❌")

        await resp.edit("`Successfully downloaded 🥳`")

        if client.database:
            await client.database.plus_fl_count(qusr, downloads=len(f_list))

        # ✅ Upload
        await resp.edit("`Uploading 📤...`")

        await client.send_files(
            f_list,
            qcid,
            resp.id,
            reply_to_message_id=_mid,
            caption="**Join @Neko_Drive ❤️**",
        )

        await resp.edit("`Done ✅`")

    finally:
        # ✅ ALWAYS cleanup
        await client.full_cleanup(dlid, qusr)

        # ✅ remove temp data
        client.glob_tmp.pop(_mid, None)
