import asyncio
import base64
import hashlib
import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import HTTPException
from imobile_telecom import RouteTest,simulate,capabilities,stable

class IMobileTests(unittest.TestCase):
    def test_public_capabilities_are_not_network_claims(self):
        data=asyncio.run(capabilities())
        self.assertEqual(len(data["components"]),5)
        self.assertFalse(data["camara_api_authorized"])
        self.assertFalse(data["subscriber_authentication_bypassed"])
        self.assertFalse(data["free_public_assistance_provisioned"])
    def test_half_node_blackout_rehearsal(self):
        r=asyncio.run(simulate(RouteTest(total_nodes=12,blackout_fraction=.5)))
        self.assertEqual(r["nodes_offline"],6)
        self.assertEqual(r["nodes_available"],6)
        self.assertEqual(r["status"],"SIMULATED_NOT_TRANSMITTED")
        self.assertFalse(r["packet"]["actually_delivered"])
        self.assertTrue(r["route"])
    def test_signed_test_receipt_is_valid_and_not_certified(self):
        r=asyncio.run(simulate(RouteTest()))
        pub=Ed25519PublicKey.from_public_bytes(base64.b64decode(r["receipt"]["test_public_key"]))
        pub.verify(base64.b64decode(r["receipt"]["test_signature"]),stable(r["packet"]))
        self.assertEqual(hashlib.sha256(stable(r["packet"])).hexdigest(),r["receipt"]["packet_sha256"])
        self.assertFalse(r["receipt"]["production_certified"])
        self.assertFalse(r["receipt"]["network_delivery_verified"])
    def test_no_survivors_rejected_by_schema(self):
        with self.assertRaises(Exception):
            RouteTest(blackout_fraction=1)
    def test_invalid_transport_fails(self):
        with self.assertRaises(HTTPException) as e:
            asyncio.run(simulate(RouteTest(transport="free-unauthorized-carrier")))
        self.assertEqual(e.exception.status_code,422)
    def test_invalid_handle_rejected(self):
        with self.assertRaises(Exception):
            RouteTest(to_handle="1234567890")
    def test_deterministic_path_not_authentic_peer(self):
        a=asyncio.run(simulate(RouteTest(seed=9)))
        b=asyncio.run(simulate(RouteTest(seed=9)))
        self.assertEqual(a["route"],b["route"])
        self.assertFalse(a["packet"]["real_peer_connection"])

if __name__=="__main__":unittest.main()
