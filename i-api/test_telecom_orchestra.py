import asyncio
import io
import wave
import unittest
from telecom_orchestra import OrchestraRequest,run_score,simulate,capabilities,audio,sha

class TelecomOrchestraTests(unittest.TestCase):
    def test_half_dropout_conserves_simulated_jobs(self):
        r=run_score(OrchestraRequest(nodes=32,jobs=10000,dropout_fraction=0.5))
        m=r["metrics"]
        self.assertEqual(m["dropped_nodes"],16)
        self.assertEqual(m["surviving_nodes"],16)
        self.assertEqual(m["completed_in_memory"],10000)
        self.assertEqual(m["modeled_job_loss"],0)
        self.assertEqual(m["reassigned_jobs"],m["planned_jobs_on_failed_nodes"])
        self.assertEqual(m["real_radio_packets_sent"],0)
        self.assertFalse(m["physical_failover_verified"])
    def test_hundred_percent_dropout_invalid(self):
        with self.assertRaises(ValueError):
            run_score(OrchestraRequest(nodes=2,jobs=5,dropout_fraction=1))
    def test_deterministic_receipt(self):
        r=run_score(OrchestraRequest(nodes=10,jobs=100,seed=12))
        self.assertEqual(r,run_score(OrchestraRequest(nodes=10,jobs=100,seed=12)))
        self.assertEqual(r["receipt"]["sha256"],sha(r["receipt"]["body"]))
        self.assertIsNone(r["receipt"]["signature"])
        self.assertFalse(r["receipt"]["anchored"])
    def test_revenue_not_actual(self):
        result=run_score(OrchestraRequest(proposed_price_usd_per_gb=20,proposed_cost_usd_per_gb=5))
        self.assertGreater(result["metrics"]["hypothetical_revenue_usd"],0)
        self.assertEqual(result["metrics"]["actual_revenue_usd"],0)
    def test_capabilities_not_fake_carrier(self):
        r=asyncio.run(capabilities())
        self.assertEqual(len(r["instruments"]),5)
        self.assertTrue(all(i["connected"] is False for i in r["instruments"]))
        self.assertFalse(r["actual_monetization_active"])
    def test_audio_is_playable_pcm(self):
        r=asyncio.run(audio())
        with wave.open(io.BytesIO(r.body)) as w:
            self.assertEqual(w.getnchannels(),1)
            self.assertEqual(w.getframerate(),8000)
            self.assertEqual(w.getnframes(),16000)
    def test_bounds(self):
        with self.assertRaises(Exception):OrchestraRequest(nodes=1)
        with self.assertRaises(Exception):OrchestraRequest(jobs=10001)

if __name__=="__main__":unittest.main()
