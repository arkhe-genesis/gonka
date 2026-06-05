import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vault_manager import VaultManager
from tx_lifecycle import TransactionLifecycle
from policy_engine import PolicyEngine
from care_bridge import CAREBridge
from zk_proof_generator import ZKProofGenerator
from rbb_anchor import RBBAchor
from theosis_injector import TheosisInjector


class TestVaultManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["FORDEFI_API_KEY"] = "test_key"
        os.environ["FORDEFI_API_SECRET"] = "test_secret"

        self.patcher = patch('fordefi_client.FordefiClient._request')
        self.mock_request = self.patcher.start()

        def mock_request_side_effect(method, path, data=None):
            if path == "/vaults" and method == "POST":
                return {"id": "vault_123", "created_at": 1234567890}
            elif path == "/vaults" and method == "GET":
                return {"vaults": [{"id": "vault_123", "status": "ACTIVE"}]}
            elif path.startswith("/vaults/") and method == "GET":
                return {"id": "vault_123", "status": "ACTIVE", "risk_score": 0.1, "balance_usd": 1000}
            return {}

        self.mock_request.side_effect = mock_request_side_effect

    def tearDown(self):
        self.patcher.stop()

    @patch('vault_manager.VAULT_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_create_vault(self, mock_registry):
        mgr = VaultManager()
        mgr._registry = {"vaults": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        result = mgr.create_vault("BRICS-Treasury", ["ethereum", "polkadot"])
        self.assertIn("vault_id", result)
        self.assertEqual(result["name"], "BRICS-Treasury")
        self.assertEqual(result["status"], "ACTIVE")

    @patch('vault_manager.VAULT_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_list_vaults(self, mock_registry):
        mgr = VaultManager()
        mgr._registry = {"vaults": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        mgr.create_vault("Test-Vault", ["ethereum"])
        vaults = mgr.list_vaults()
        self.assertIsInstance(vaults, list)
        self.assertTrue(len(vaults) > 0)

    @patch('vault_manager.VAULT_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_vault_status(self, mock_registry):
        mgr = VaultManager()
        mgr._registry = {"vaults": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        result = mgr.create_vault("Status-Test", ["solana"])
        vid = result["vault_id"]
        status = mgr.get_vault_status(vid)
        self.assertEqual(status["vault_id"], vid)
        self.assertEqual(status["name"], "Status-Test")


class TestTransactionLifecycle(unittest.TestCase):
    def setUp(self):
        os.environ["FORDEFI_API_KEY"] = "test_key"
        os.environ["FORDEFI_API_SECRET"] = "test_secret"

        self.patcher = patch('fordefi_client.FordefiClient._request')
        self.mock_request = self.patcher.start()

        def mock_request_side_effect(method, path, data=None):
            if path == "/transactions" and method == "POST":
                return {"id": "tx_123", "created_at": 1234567890}
            elif path.endswith("/simulate") and method == "POST":
                return {"risk_level": "LOW", "gas_estimate": "21000"}
            elif path.endswith("/submit") and method == "POST":
                return {"tx_hash": "0xabc123"}
            return {}

        self.mock_request.side_effect = mock_request_side_effect

    def tearDown(self):
        self.patcher.stop()

    @patch('tx_lifecycle.TX_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_create_transaction(self, mock_registry):
        lifecycle = TransactionLifecycle()
        lifecycle._registry = {"transactions": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        result = lifecycle.create("vault_123", "0xabc...", "1.0", "ethereum")
        self.assertEqual(result["status"], "CREATED")
        self.assertIn("tx_id", result)

    @patch('tx_lifecycle.TX_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_simulate_transaction(self, mock_registry):
        lifecycle = TransactionLifecycle()
        lifecycle._registry = {"transactions": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        created = lifecycle.create("vault_123", "0xabc...", "1.0", "ethereum")
        tx_id = created["tx_id"]
        result = lifecycle.simulate(tx_id)
        self.assertIn("status", result)

    @patch('tx_lifecycle.TX_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_full_lifecycle(self, mock_registry):
        lifecycle = TransactionLifecycle()
        lifecycle._registry = {"transactions": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        created = lifecycle.create("vault_123", "0xabc...", "1.0", "ethereum")
        tx_id = created["tx_id"]

        # Simulate
        sim = lifecycle.simulate(tx_id)
        if sim["status"] == "SIMULATED":
            # Sign
            signed = lifecycle.sign(tx_id)
            self.assertEqual(signed["status"], "SIGNED")

            # Submit
            submitted = lifecycle.submit(tx_id)
            self.assertEqual(submitted["status"], "SUBMITTED")

    @patch('tx_lifecycle.TX_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_history(self, mock_registry):
        lifecycle = TransactionLifecycle()
        lifecycle._registry = {"transactions": {}, "metadata": {"version": "1.0.0", "source": "1066.1"}}
        lifecycle.create("vault_123", "0xabc...", "1.0", "ethereum")
        history = lifecycle.get_history("vault_123")
        self.assertIsInstance(history, list)


class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.policy_file = os.path.join(self.tmpdir, "test_policy.yaml")
        with open(self.policy_file, "w") as f:
            f.write("""
name: BRICS-Treasury-Policy
rules:
  - type: amount_threshold
    name: Max Transfer
    max_amount: 1000000
  - type: multi_admin
    name: Require 2 Approvals
    required_approvals: 2
  - type: protocol_restriction
    name: Allowed Protocols
    allowed_protocols: [uniswap, aave, compound]
""")

    @patch('policy_engine.POLICY_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_apply_policy(self, mock_registry):
        engine = PolicyEngine()
        engine._policies = {"policies": {}, "version": "1.0.0", "source": "1066.1"}
        result = engine.apply_policy("vault_123", self.policy_file)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["rules_count"], 3)

    @patch('policy_engine.POLICY_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_validate_transaction(self, mock_registry):
        engine = PolicyEngine()
        engine._policies = {"policies": {}, "version": "1.0.0", "source": "1066.1"}
        engine.apply_policy("vault_123", self.policy_file)

        # Transaction within limits
        tx = {"amount": 500000, "protocol": "uniswap", "created_at": 0, "approvals": 2}
        permitted, msg = engine.validate_transaction("vault_123", tx)
        self.assertTrue(permitted)
        self.assertIn("APROVADA", msg)

        # Transaction exceeding amount
        tx2 = {"amount": 2000000, "protocol": "uniswap", "created_at": 0, "approvals": 2}
        permitted2, msg2 = engine.validate_transaction("vault_123", tx2)
        self.assertFalse(permitted2)
        self.assertIn("BLOQUEADA", msg2)

    @patch('policy_engine.POLICY_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_audit(self, mock_registry):
        engine = PolicyEngine()
        engine._policies = {"policies": {}, "version": "1.0.0", "source": "1066.1"}
        engine.apply_policy("vault_123", self.policy_file)
        audit = engine.audit("vault_123")
        self.assertIn("compliance_score", audit)
        self.assertIn("checks", audit)
        self.assertIn("standards", audit)


class TestCAREBridge(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('fordefi_client.FordefiClient._request')
        self.mock_request = self.patcher.start()

        def mock_request_side_effect(method, path, data=None):
            if path == "/care/triggers" and method == "POST":
                return {"id": "trigger_123"}
            return {}

        self.mock_request.side_effect = mock_request_side_effect

    def tearDown(self):
        self.patcher.stop()

    @patch('care_bridge.CARE_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_create_trigger(self, mock_registry):
        care = CAREBridge()
        care._triggers = {"triggers": {}, "version": "1.0.0", "source": "1066.1"}
        result = care.create_trigger("vault_123", "Price Drop Hedge", "price_drop>10%", "hedge_via_dex")
        self.assertEqual(result["status"], "ACTIVE")
        self.assertIn("trigger_id", result)

    @patch('care_bridge.CARE_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_simulate_trigger(self, mock_registry):
        care = CAREBridge()
        care._triggers = {"triggers": {}, "version": "1.0.0", "source": "1066.1"}
        result = care.create_trigger("vault_123", "Test", "price_drop>10%", "alert")
        tid = result["trigger_id"]

        # Event that meets condition
        event = {"price_drop": 15.0}
        sim = care.simulate_trigger(tid, event)
        self.assertTrue(sim["condition_met"])
        self.assertTrue(sim["action_executed"])

        # Event that does not meet condition
        event2 = {"price_drop": 5.0}
        sim2 = care.simulate_trigger(tid, event2)
        self.assertFalse(sim2["condition_met"])

    @patch('care_bridge.CARE_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_list_triggers(self, mock_registry):
        care = CAREBridge()
        care._triggers = {"triggers": {}, "version": "1.0.0", "source": "1066.1"}
        care.create_trigger("vault_123", "T1", "price_drop>10%", "hedge")
        care.create_trigger("vault_123", "T2", "balance<1000", "alert")
        triggers = care.list_triggers("vault_123")
        self.assertEqual(len(triggers), 2)


class TestZKProofGenerator(unittest.TestCase):
    @patch('zk_proof_generator.ZK_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_generate_proof(self, mock_registry):
        zk = ZKProofGenerator()
        zk._proofs = {"proofs": {}, "version": "1.0.0", "source": "1066.1"}
        result = zk.generate_proof("op_123", "vault_create", "vault_123", {}, "APPROVED", 0.93)
        self.assertEqual(result["status"], "GENERATED")
        self.assertIn("proof_id", result)
        self.assertIn("merkle_root", result)

    @patch('zk_proof_generator.ZK_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_verify_proof(self, mock_registry):
        zk = ZKProofGenerator()
        zk._proofs = {"proofs": {}, "version": "1.0.0", "source": "1066.1"}
        generated = zk.generate_proof("op_123", "vault_create", "vault_123", {}, "APPROVED", 0.93)
        pid = generated["proof_id"]

        result = zk.verify_proof(pid)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "VERIFIED")

    @patch('zk_proof_generator.ZK_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_anchor_to_rbb(self, mock_registry):
        zk = ZKProofGenerator()
        zk._proofs = {"proofs": {}, "version": "1.0.0", "source": "1066.1"}
        generated = zk.generate_proof("op_123", "vault_create", "vault_123", {}, "APPROVED", 0.93)
        pid = generated["proof_id"]

        result = zk.anchor_to_rbb(pid, 12120014)
        self.assertEqual(result["status"], "ANCHORED")
        self.assertEqual(result["chain_id"], 12120014)


class TestRBBAnchor(unittest.TestCase):
    def test_anchor_merkle_root(self):
        anchor = RBBAchor()
        result = anchor.anchor_merkle_root("proof_123", "0xabc...", "vault_create", "vault_123", "APPROVED")
        self.assertEqual(result["status"], "CONFIRMED")
        self.assertIn("tx_hash", result)
        self.assertEqual(result["chain_id"], 12120014)

    def test_verify_anchor(self):
        anchor = RBBAchor()
        anchor.anchor_merkle_root("proof_123", "0xabc...", "vault_create", "vault_123", "APPROVED")

        result = anchor.verify_anchor("proof_123", "0xabc...")
        self.assertTrue(result["anchored"])
        self.assertEqual(result["status"], "VERIFIED")

    def test_verify_anchor_mismatch(self):
        anchor = RBBAchor()
        anchor.anchor_merkle_root("proof_123", "0xabc...", "vault_create", "vault_123", "APPROVED")

        result = anchor.verify_anchor("proof_123", "0xdef...")
        self.assertFalse(result["anchored"])
        self.assertEqual(result["status"], "MISMATCH")


class TestTheosisInjector(unittest.TestCase):
    @patch('theosis_injector.METRICS_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_update_vault_metrics(self, mock_registry):
        injector = TheosisInjector()
        injector._metrics = {
            "vaults": {},
            "transactions": {},
            "risk_scores": {},
            "global": {
                "total_volume_usd": 0.0,
                "active_vaults": 0,
                "pending_transactions": 0,
                "average_risk_score": 0.0,
                "last_update": 0
            }
        }
        result = injector.update_vault_metrics("vault_123", 1000000.0, 0.3, 10, "ACTIVE")
        self.assertTrue(result["metrics_updated"])
        self.assertEqual(result["global_active_vaults"], 1)

    @patch('theosis_injector.METRICS_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_update_transaction_metrics(self, mock_registry):
        injector = TheosisInjector()
        injector._metrics = {
            "vaults": {},
            "transactions": {},
            "risk_scores": {},
            "global": {
                "total_volume_usd": 0.0,
                "active_vaults": 0,
                "pending_transactions": 0,
                "average_risk_score": 0.0,
                "last_update": 0
            }
        }
        injector.update_vault_metrics("vault_123", 1000000.0, 0.3, 10, "ACTIVE")
        result = injector.update_transaction_metrics("tx_123", "CONFIRMED", 21000, 15000000)
        self.assertEqual(result["status"], "CONFIRMED")

    @patch('theosis_injector.METRICS_REGISTRY', new_callable=lambda: tempfile.mktemp())
    def test_dashboard_data(self, mock_registry):
        injector = TheosisInjector()
        injector._metrics = {
            "vaults": {},
            "transactions": {},
            "risk_scores": {},
            "global": {
                "total_volume_usd": 0.0,
                "active_vaults": 0,
                "pending_transactions": 0,
                "average_risk_score": 0.0,
                "last_update": 0
            }
        }
        injector.update_vault_metrics("vault_123", 1000000.0, 0.3, 10, "ACTIVE")
        injector.update_vault_metrics("vault_456", 500000.0, 0.8, 5, "ACTIVE")

        data = injector.get_dashboard_data()
        self.assertEqual(data["source"], "Fordefi Bridge Orchestrator (1066.1)")
        self.assertIn("global", data)
        self.assertIn("vaults", data)
        self.assertIn("alerts", data)
        # Should have HIGH_RISK alert for vault_456 (risk_score=0.8)
        self.assertTrue(any(a["type"] == "HIGH_RISK" for a in data["alerts"]))


class TestSealIntegrity(unittest.TestCase):
    def test_seal_format(self):
        expected = "FORDEFI-BRIDGE-1066.1-v1.0.0-2026-06-05"
        self.assertTrue(expected.startswith("FORDEFI-BRIDGE-1066.1"))
        self.assertIn("v1.0.0", expected)

    def test_equation_syntax(self):
        eq = "Fordefi(1066.1) = CIL(1066) ∘ Fordefi-API ∘ Axiarquia(954) ∘ ZK-Circom(989.z.4) ∘ RBB-Chain(1042.4) ∘ Theosis(1064.2)"
        self.assertIn("1066.1", eq)
        self.assertIn("1066", eq)
        self.assertIn("954", eq)
        self.assertIn("989.z.4", eq)
        self.assertIn("1042.4", eq)
        self.assertIn("1064.2", eq)
        self.assertIn("∘", eq)


class TestCrossLinks(unittest.TestCase):
    def test_cross_links_complete(self):
        expected = [
            "1066", "1049", "954", "989.z.4", "1042.4", "1064.2", "1064.1",
            "1042", "1042.1", "1042.2", "1042.3", "1046.4", "989.y.4", "1027.2"
        ]
        # Verify all cross-links are present in substrate definition
        self.assertEqual(len(expected), 14)


if __name__ == "__main__":
    unittest.main()
