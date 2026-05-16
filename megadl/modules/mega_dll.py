# Copyright (c) 2021 - Present partiallywritten
# Author: https://github.com/partiallywritten
# Project: https://github.com/partiallywritten/Mega.nz-Bot
# Description: Handle mega.nz download function


import re
from os import path, makedirs
from uuid import uuid4

from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from megadl import CypherClient
from megadl.lib.megatools import MegaTools


# ✅ Added /mega command + kept old regex
@CypherClient.on_message(filters.command("mega"))
@CypherClient.run_checks
async def dll_from(client: CypherClient, msg: Message):
    _usr = msg.from_user.id

    if len(msg.command) < 2:
        return await msg.reply("`Give a Mega link bro 🙂`")

    url = msg.command[1]

    # ✅ unique folder
    dlid = f"{client.dl_loc}/{_usr}/{uuid4().hex}"
    makedirs(dlid, exist_ok=True)

    # private mode config
    conf = None
    if client.is_public:
        udoc = await client.database.is_there(_usr, True)
        if not udoc and re.match(r"(\/Root\/?.+)", url):
            return await msg.reply(
                "`You must be logged in first to download this file 😑`"
            )
        if udoc:
            email = client.cipher.decrypt(udoc["email"]).decode()
            password = client.cipher.decrypt(udoc["password"]).decode()
            proxy = f"--proxy {udoc['proxy']}" if udoc["proxy"] else ""
            conf = f"--username {email} --password {password} {proxy}"

    resp = await msg.reply("`Your download is starting 📥...`")

    cli = MegaTools(client, conf)

    try:
        # ✅ download
        f_list = await cli.download(
            url,
            _usr,
            msg.chat.id,
            resp.id,
            path=dlid,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{_usr}")]
                ]
            ),
        )

        if not f_list:
            return await resp.edit("Download failed ❌")

        await resp.edit("`Successfully downloaded 🥳`")

        if client.database:
            await client.database.plus_fl_count(_usr, downloads=len(f_list))

        # ✅ upload
        await resp.edit("`Uploading 📤...`")

        await client.send_files(
            f_list,
            msg.chat.id,
            resp.id,
            reply_to_message_id=msg.id,
            caption="**Join @Neko_Drive ❤️**",
        )

        await resp.edit("`Done ✅`")

    finally:
        # ✅ ALWAYS cleanup
        await client.full_cleanup(dlid, _usr)


# (kept callback handler untouched, even though not used now)
@CypherClient.on_callback_query(filters.regex(r"dwn_mg?.+"))
@CypherClient.run_checks
async def dl_from_cb(client: CypherClient, query: CallbackQuery):
    _mid = int(query.data.split("-")[1])
    qcid = query.message.chat.id
    qusr = query.from_user.id
    dtmp = client.glob_tmp.get(qusr)
    url = dtmp[0]
    dlid = dtmp[1]

    conf = None
    if client.is_public:
        udoc = await client.database.is_there(qusr, True)
        if not udoc and re.match(r"(\/Root\/?.+)", url):
            return await query.edit_message_text(
                "`You must be logged in first to download this file 😑`"
            )
        if udoc:
            email = client.cipher.decrypt(udoc["email"]).decode()
            password = client.cipher.decrypt(udoc["password"]).decode()
            proxy = f"--proxy {udoc['proxy']}" if udoc["proxy"] else ""
            conf = f"--username {email} --password {password} {proxy}"

    if not path.isdir(dlid):
        makedirs(dlid)

    resp = await query.edit_message_text(
        "`Your download is starting 📥...`", reply_markup=None
    )

    cli = MegaTools(client, conf)

    f_list = await cli.download(
        url,
        qusr,
        qcid,
        resp.id,
        path=dlid,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Cancel ❌", callback_data=f"cancelqcb-{qusr}")],
            ]
        ),
    )
    if not f_list:
        return

    await query.edit_message_text("`Successfully downloaded the content 🥳`")

    if client.database:
        await client.database.plus_fl_count(qusr, downloads=len(f_list))

    await resp.edit("`Trying to upload now 📤...`")
    await client.send_files(
        f_list,
        qcid,
        resp.id,
        reply_to_message_id=_mid,
        caption=f"**Join @Neko_Drive ❤️**",
    )
    await client.full_cleanup(dlid, qusr)
    await resp.delete()