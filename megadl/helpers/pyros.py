# Copyright (c) 2021 - Present partiallywritten
# Author: https://github.com/partiallywritten
# Project: https://github.com/partiallywritten/Mega.nz-Bot
# Description: Tools and helper functions related to pyrogram

import asyncio
from time import time

from humans import human_bytes, human_time
from pyrogram.errors import FloodWait, MessageNotModified

# ── Constants ─────────────────────────────────────────────────────────────────

THROTTLE_SECONDS = 5  # minimum gap between edits per message
BAR_LENGTH = 20

# Pre-computed progress bar strings  ░░░░░░░░░░░░░░░░░░░░  →  ████████████████████
PROGRESS_BARS: tuple[str, ...] = tuple(
    f"[{'█' * i}{'░' * (BAR_LENGTH - i)}]"
    for i in range(BAR_LENGTH + 1)
)

# ── State ──────────────────────────────────────────────────────────────────────

# {chat_id_msg_id: last_edit_timestamp}
_last_edit: dict[str, float] = {}


def _make_key(chat_id: int, msg_id: int) -> str:
    return f"{chat_id}:{msg_id}"


def cleanup_progress(chat_id: int, msg_id: int) -> None:
    """Call this after a transfer completes to free memory."""
    _last_edit.pop(_make_key(chat_id, msg_id), None)


# ── Progress bar ───────────────────────────────────────────────────────────────

async def track_progress(
    current: int,
    total: int,
    client,
    chat_id: int,
    msg_id: int,
    start: float,
    **kwargs,
) -> None:
    """
    Pyrogram-compatible progress callback with flood-wait handling.

    • Throttled to one edit per THROTTLE_SECONDS per message.
    • Respects FloodWait by sleeping the required delay before retrying.
    • Silently drops MessageNotModified (content unchanged) and any
      other non-critical errors so the transfer is never interrupted.
    """
    now = time()
    key = _make_key(chat_id, msg_id)

    # ── Throttle ──────────────────────────────────────────────────────────────
    if now - _last_edit.get(key, 0) < THROTTLE_SECONDS:
        return
    _last_edit[key] = now

    # ── Calculations ──────────────────────────────────────────────────────────
    elapsed = now - start
    if elapsed == 0 or total == 0:
        return

    percentage = current * 100 / total
    speed = current / elapsed                          # bytes / second
    eta_ms = round((total - current) / speed) * 1000  # milliseconds remaining

    # ── Build message ─────────────────────────────────────────────────────────
    filled = min(int(percentage) // 5, BAR_LENGTH)
    bar = PROGRESS_BARS[filled]

    text = (
        f"{bar}\n"
        f"**Progress:** `{percentage:.1f}%`\n\n"
        f"**Done:** `{human_bytes(current)}` of `{human_bytes(total)}`\n"
        f"**Speed:** `{human_bytes(speed)}/s`\n"
        f"**ETA:** `{human_time(eta_ms) or '< 1 s'}`\n\n"
        f"**Powered by @Neko_Drive**"
    )

    # ── Send edit with flood-wait retry ───────────────────────────────────────
    try:
        await client.edit_message_text(chat_id, msg_id, text, **kwargs)

    except FloodWait as e:
        # Telegram told us exactly how long to wait — respect it.
        await asyncio.sleep(e.value)
        # Bump throttle timestamp so we don't immediately re-edit after waking.
        _last_edit[key] = time()

    except MessageNotModified:
        # Content was identical — harmless, ignore.
        pass

    except Exception:
        # Any other error (network blip, message deleted, etc.)
        # must not crash the upload/download coroutine.
        pass