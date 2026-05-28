import unittest
from bridge.interfold.interfold_bridge import (
    E3Adapter,
    CiphernodeClient,
    VerifiableRelease,
    ConfidentialOrchestrator,
    InterfoldBridge
)

class TestInterfoldBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = InterfoldBridge()

    def test_e3_adapter(self):
        adapter = E3Adapter()
        res = adapter.create_e3("test_logic", {"rule": "test"})
        self.assertIn("e3_id", res)
        self.assertEqual(res["status"], "created")

        del_res = adapter.destroy_e3(res["e3_id"])
        self.assertEqual(del_res["status"], "destroyed")

    def test_ciphernode_client(self):
        client = CiphernodeClient()
        comm = client.request_committee("e3_123")
        self.assertEqual(comm["status"], "formed")
        self.assertIn("committee_id", comm)

        sub = client.submit_encrypted_input("e3_123", "secret_data")
        self.assertEqual(sub["status"], "submitted")

    def test_verifiable_release(self):
        vr = VerifiableRelease()
        self.assertTrue(vr.verify_execution("e3_123", "proof_data"))
        self.assertFalse(vr.verify_execution("e3_123", ""))

        rel1 = vr.trigger_release("e3_123", ["sig1", "sig2"])
        self.assertEqual(rel1["status"], "released")

        rel2 = vr.trigger_release("e3_123", ["sig1"])
        self.assertEqual(rel2["status"], "failed")

    def test_orchestrator(self):
        orchestrator = self.bridge.orchestrator
        res = orchestrator.run_confidential_computation(
            "test_logic",
            ["input1", "input2"],
            {"rule": "test"}
        )
        self.assertEqual(res["status"], "completed")
        self.assertIn("e3_id", res)

    def test_bridge_use_cases(self):
        bids_res = self.bridge.execute_sealed_bid_auction(["bid1", "bid2"])
        self.assertEqual(bids_res["status"], "completed")

        votes_res = self.bridge.execute_private_voting(["vote1", "vote2"])
        self.assertEqual(votes_res["status"], "completed")

if __name__ == '__main__':
    unittest.main()
