
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents import log_agent
from escalation import escalation_manager


class TestSupportIQ(unittest.TestCase):

    def setUp(self):
        """
        Create isolated temporary CSV files.

        Tests must not modify actual support records.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.log_path = (
            Path(self.temp_dir.name) / "support_logs.csv"
        )
        self.action_path = (
            Path(self.temp_dir.name) / "escalation_actions.csv"
        )

        self.log_patcher = patch.object(
            log_agent,
            "LOG_FILE",
            self.log_path,
        )
        self.support_patcher = patch.object(
            escalation_manager,
            "SUPPORT_LOG",
            self.log_path,
        )
        self.action_patcher = patch.object(
            escalation_manager,
            "ESCALATION_LOG",
            self.action_path,
        )

        self.log_patcher.start()
        self.support_patcher.start()
        self.action_patcher.start()

        self.addCleanup(self.log_patcher.stop)
        self.addCleanup(self.support_patcher.stop)
        self.addCleanup(self.action_patcher.stop)

        self.query_analysis = {
            "category": "account",
            "urgency": "high",
            "sentiment": "negative",
            "summary": "Unauthorized account access",
        }

        self.resolution = {
            "customer_response": (
                "Please change your password. "
                "Human security review is required."
            ),
            "resolution_status": "escalated",
            "escalation_required": True,
            "escalation_reason": (
                "Suspected unauthorized account access."
            ),
            "policy_sources": [
                "account_and_login.md"
            ],
        }

    def create_test_ticket(self):
        return log_agent.log_support_case(
            complaint=(
                "Someone accessed my account "
                "without permission!"
            ),
            query_analysis=self.query_analysis,
            resolution=self.resolution,
        )

    def test_01_ticket_creation(self):
        result = self.create_test_ticket()

        self.assertTrue(
            result["ticket_id"].startswith("SIQ-")
        )
        self.assertTrue(self.log_path.exists())

    def test_02_csv_record(self):
        self.create_test_ticket()

        with self.log_path.open(
            newline="",
            encoding="utf-8-sig",
        ) as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "account")
        self.assertEqual(rows[0]["urgency"], "high")
        self.assertEqual(
            rows[0]["resolution_status"],
            "escalated",
        )

    def test_03_escalation_detection(self):
        result = self.create_test_ticket()

        ticket = escalation_manager.get_support_ticket(
            result["ticket_id"]
        )

        self.assertTrue(
            escalation_manager.is_escalated_ticket(
                ticket
            )
        )

    def test_04_initial_review_status(self):
        result = self.create_test_ticket()

        review = escalation_manager.get_escalation_status(
            result["ticket_id"]
        )

        self.assertEqual(
            review["status"],
            "pending_review",
        )

    def test_05_agent_assignment(self):
        result = self.create_test_ticket()

        action = escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="assign",
            agent_name="Support Agent 1",
            notes="Assigned for review",
        )

        self.assertEqual(
            action["status"],
            "assigned",
        )

    def test_06_wrong_agent_rejected(self):
        result = self.create_test_ticket()

        escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="assign",
            agent_name="Support Agent 1",
        )

        with self.assertRaises(ValueError):
            escalation_manager.record_escalation_action(
                ticket_id=result["ticket_id"],
                action="start_progress",
                agent_name="Different Agent",
            )

    def test_07_investigation_progress(self):
        result = self.create_test_ticket()

        escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="assign",
            agent_name="Support Agent 1",
        )

        action = escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="start_progress",
            agent_name="Support Agent 1",
            notes="Investigation started",
        )

        self.assertEqual(
            action["status"],
            "in_progress",
        )

    def test_08_resolution_notes_required(self):
        result = self.create_test_ticket()

        escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="assign",
            agent_name="Support Agent 1",
        )

        escalation_manager.record_escalation_action(
            ticket_id=result["ticket_id"],
            action="start_progress",
            agent_name="Support Agent 1",
        )

        with self.assertRaises(ValueError):
            escalation_manager.record_escalation_action(
                ticket_id=result["ticket_id"],
                action="resolve",
                agent_name="Support Agent 1",
                notes="",
            )

    def test_09_full_human_workflow(self):
        result = self.create_test_ticket()
        ticket_id = result["ticket_id"]

        escalation_manager.record_escalation_action(
            ticket_id,
            "assign",
            "Support Agent 1",
        )

        escalation_manager.record_escalation_action(
            ticket_id,
            "start_progress",
            "Support Agent 1",
        )

        action = escalation_manager.record_escalation_action(
            ticket_id,
            "resolve",
            "Support Agent 1",
            "Demo review completed",
        )

        self.assertEqual(
            action["status"],
            "resolved",
        )

        history = escalation_manager.get_escalation_history(
            ticket_id
        )

        self.assertEqual(len(history), 3)

    def test_10_non_escalated_ticket_rejected(self):
        normal_resolution = {
            **self.resolution,
            "escalation_required": False,
            "resolution_status": "pending_customer_action",
        }

        result = log_agent.log_support_case(
            complaint="Where is my order?",
            query_analysis={
                "category": "shipping",
                "urgency": "medium",
                "sentiment": "neutral",
                "summary": "Shipping question",
            },
            resolution=normal_resolution,
        )

        with self.assertRaises(ValueError):
            escalation_manager.record_escalation_action(
                ticket_id=result["ticket_id"],
                action="assign",
                agent_name="Support Agent 1",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
