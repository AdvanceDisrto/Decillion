"""Deterministic acceptance for real signaling state; not physical call acceptance."""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from imobile_live_signaling import create_room, join_room, signal, events, Signal, _rooms

class TestLiveSignaling(unittest.TestCase):
    def setUp(self):
        _rooms.clear()

    def as_user(self, uid):
        return patch("imobile_live_signaling.actor", new_callable=AsyncMock, return_value=uid)

    def test_authenticated_invite_offer_answer_and_privacy(self):
        with self.as_user("caller"):
            room = asyncio.run(create_room("Bearer valid"))
        key = room["room_id"]
        self.assertGreaterEqual(len(key), 24)
        self.assertFalse(room["media_connected"])
        with self.as_user("caller"):
            asyncio.run(signal(key, Signal(type="offer", sdp="v=0"), "Bearer valid"))
        with self.as_user("callee"):
            accepted = asyncio.run(join_room(key, "Bearer valid"))
            self.assertEqual(accepted["status"], "joined")
            offer = asyncio.run(events(key, 0, "Bearer valid"))
            self.assertEqual(offer["events"][0]["type"], "offer")
            asyncio.run(signal(key, Signal(type="answer", sdp="v=0"), "Bearer valid"))
        with self.as_user("caller"):
            answer = asyncio.run(events(key, 0, "Bearer valid"))
            self.assertEqual([x["type"] for x in answer["events"]], ["answer"])
        with self.as_user("stranger"):
            with self.assertRaises(HTTPException) as e:
                asyncio.run(events(key, 0, "Bearer valid"))
            self.assertEqual(e.exception.status_code, 403)
        with self.as_user("other"):
            with self.assertRaises(HTTPException) as e:
                asyncio.run(join_room(key, "Bearer valid"))
            self.assertEqual(e.exception.status_code, 409)

    def test_offer_restricted_and_input_validation(self):
        with self.as_user("one"):
            key = asyncio.run(create_room("Bearer x"))["room_id"]
        with self.as_user("two"):
            asyncio.run(join_room(key, "Bearer x"))
            with self.assertRaises(HTTPException) as e:
                asyncio.run(signal(key, Signal(type="offer", sdp="v=0"), "Bearer x"))
            self.assertEqual(e.exception.status_code, 403)
        with self.assertRaises(Exception):
            Signal(type="nope", sdp="x")

    def test_no_duplicate_unauthenticated_room_claim(self):
        with self.as_user("caller"):
            key = asyncio.run(create_room("Bearer x"))["room_id"]
            with self.assertRaises(HTTPException):
                asyncio.run(join_room(key, "Bearer x"))
        with self.as_user("guest"):
            with self.assertRaises(HTTPException):
                asyncio.run(events(key, 0, "Bearer x"))

if __name__ == "__main__":
    unittest.main()
