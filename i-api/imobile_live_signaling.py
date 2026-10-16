"""Ephemeral authenticated signaling for iMobile WebRTC.
No media passes through this module. One process only; not durable or HA.
"""
import asyncio
import secrets
import time
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/imobile/live", tags=["iMobile real calls"])
ROOM_TTL_SECONDS = 600
MAX_ROOMS = 100
_rooms = {}
_guard = asyncio.Lock()

async def actor(auth):
    from main import user_id
    uid, _ = await user_id(auth)
    return uid

def _get(room_id):
    room = _rooms.get(room_id)
    if not room or room["expires"] < time.monotonic():
        raise HTTPException(404, "Call invitation expired or unavailable")
    return room

def _member(room, uid):
    if uid not in (room["caller"], room["callee"]):
        raise HTTPException(403, "Not a participant in this call")

class Signal(BaseModel):
    type: str = Field(pattern="^(offer|answer|candidate|hangup)$")
    sdp: str | None = Field(default=None, max_length=150000)
    candidate: str | None = Field(default=None, max_length=10000)

@router.post("/rooms")
async def create_room(authorization: str = Header(default="")):
    uid = await actor(authorization)
    async with _guard:
        now = time.monotonic()
        for key in list(_rooms):
            if _rooms[key]["expires"] < now:
                del _rooms[key]
        if len(_rooms) >= MAX_ROOMS:
            raise HTTPException(503, "Call capacity temporarily reached")
        if sum(r["caller"] == uid for r in _rooms.values()) >= 3:
            raise HTTPException(429, "Too many pending invitations")
        room_id = secrets.token_urlsafe(24)
        _rooms[room_id] = {"caller": uid, "callee": None, "expires": now + ROOM_TTL_SECONDS,
                           "seq": 0, "events": []}
        return {"room_id": room_id, "expires_in_seconds": ROOM_TTL_SECONDS,
                "status": "invitation_created", "media_connected": False}

@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, authorization: str = Header(default="")):
    uid = await actor(authorization)
    async with _guard:
        room = _get(room_id)
        if uid == room["caller"]:
            raise HTTPException(409, "Use a different account to answer this call")
        if room["callee"] not in (None, uid):
            raise HTTPException(409, "This invitation was already accepted")
        room["callee"] = uid
        return {"status": "joined", "media_connected": False}

@router.post("/rooms/{room_id}/signal")
async def signal(room_id: str, body: Signal, authorization: str = Header(default="")):
    uid = await actor(authorization)
    async with _guard:
        room = _get(room_id)
        _member(room, uid)
        if body.type in ("offer", "answer") and (not body.sdp or len(body.sdp) > 150000):
            raise HTTPException(422, "SDP required")
        if body.type == "offer" and uid != room["caller"]:
            raise HTTPException(403, "Only caller can offer")
        if body.type == "answer" and uid != room["callee"]:
            raise HTTPException(403, "Only callee can answer")
        if body.type == "candidate" and not body.candidate:
            raise HTTPException(422, "Candidate required")
        room["seq"] += 1
        event = {"seq": room["seq"], "sender": uid, "type": body.type,
                 "sdp": body.sdp if body.type in ("offer", "answer") else None,
                 "candidate": body.candidate if body.type == "candidate" else None}
        room["events"].append(event)
        room["events"] = room["events"][-120:]
        if body.type == "hangup":
            room["expires"] = min(room["expires"], time.monotonic() + 30)
        return {"accepted": True, "sequence": room["seq"], "media_connected": False}

@router.get("/rooms/{room_id}/events")
async def events(room_id: str, after: int = 0, authorization: str = Header(default="")):
    uid = await actor(authorization)
    if after < 0:
        raise HTTPException(422, "Invalid cursor")
    async with _guard:
        room = _get(room_id)
        _member(room, uid)
        return {"joined": room["callee"] is not None,
                "events": [{k: v for k, v in event.items() if k != "sender"}
                           for event in room["events"] if event["seq"] > after and event["sender"] != uid],
                "last_sequence": room["seq"], "media_connected": False}
