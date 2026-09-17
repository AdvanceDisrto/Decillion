"""Length-prefixed JSON frames over TCP."""

from __future__ import annotations

import asyncio
import json
import struct

MAX_FRAME = 4 * 1024 * 1024


async def send_frame(writer: asyncio.StreamWriter, value: dict) -> None:
    body = json.dumps(value, separators=(",", ":")).encode()
    if not body or len(body) > MAX_FRAME:
        raise ValueError(f"invalid frame size: {len(body)}")
    writer.write(struct.pack(">I", len(body)) + body)
    await writer.drain()


async def recv_frame(reader: asyncio.StreamReader) -> dict:
    header = await reader.readexactly(4)
    (size,) = struct.unpack(">I", header)
    if size <= 0 or size > MAX_FRAME:
        raise ValueError(f"invalid frame size: {size}")
    return json.loads((await reader.readexactly(size)).decode())
