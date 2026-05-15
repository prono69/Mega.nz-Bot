# Copyright (c) 2021 - Present partiallywritten
# Author: https://github.com/partiallywritten
# Project: https://github.com/partiallywritten/Mega.nz-Bot
# Description: Tools and helper functions related to pyrogram

from time import time
from humans import human_time, human_bytes


# pre compute possible progress bars
PROGRESS_BARS = tuple(
    f"[{'█'*i}{'░'*(20-i)}]"
    for i in range(21)
)

# Porogress bar for pyrogram
# Improved version of SpEcHiDe's AnyDL-Bot
# global dict to track last edit time per message
LAST_EDIT = {}

async def track_progress(
    current, total, client, chat_id: int, msg_id: int, start: float, **kwargs
):
    now = time()

    key = f"{chat_id}_{msg_id}"

    # ⛔ throttle: only update every 5 seconds
    if key in LAST_EDIT and (now - LAST_EDIT[key]) < 5:
        return

    LAST_EDIT[key] = now

    diff = now - start
    if diff == 0:
        return

    percentage = current * 100 / total
    speed = current / diff

    elapsed_time = round(diff) * 1000
    time_to_completion = round((total - current) / speed) * 1000
    estimated_total_time = elapsed_time + time_to_completion

    elapsed_time = human_time(elapsed_time)
    estimated_total_time = human_time(estimated_total_time)

    filled = min(int(percentage) // 5, 20)

    progress = f"{PROGRESS_BARS[filled]}\n**Process**: {percentage:.2f}%\n"

    pmsg = (
        f"{progress}"
        f"{human_bytes(current)} of {human_bytes(total)}\n"
        f"**Speed:** {human_bytes(speed)}/s\n"
        f"**ETA:** {estimated_total_time or '0 s'}\n\n"
        f"**Powered by @Neko_Drive**"
    )

    try:
        await client.edit_message_text(chat_id, msg_id, pmsg, **kwargs)
    except:
        pass