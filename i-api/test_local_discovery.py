import asyncio
import unittest
from unittest.mock import patch
from local_discovery import local_interfaces,report,wifi_direct

class DiscoveryTests(unittest.TestCase):
    def test_socket_probe_is_local(self):
        r=local_interfaces()
        self.assertEqual(set(r),{"tcp","udp"})
        self.assertTrue(all(x["loopback_socket_open"] for x in r.values()))
    def test_scans_opt_in_only(self):
        r=asyncio.run(report())
        self.assertFalse(r["bluetooth"]["scan_performed"])
        self.assertFalse(r["lan"]["discovery_performed"])
        self.assertFalse(r["wifi_direct"]["capability_checked"])
        self.assertFalse(r["p2p_authenticated"])
        self.assertFalse(r["encrypted_session_established"])
    def test_driver_probe_is_not_p2p_session(self):
        with patch("local_discovery.platform.system",return_value="OtherOS"):
            r=wifi_direct()
        self.assertFalse(r["session_active"])
        self.assertFalse(r["capability_checked"])

if __name__=="__main__":unittest.main()
