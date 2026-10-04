from django.test import TestCase
from django.core.management import call_command
from cases.models import Case
from .services import append_event, verify_case


class LedgerTests(TestCase):
    def setUp(self):
        call_command("seed_demo")
        self.case = Case.objects.get(reference="DEMO-PHASE3-0001")

    def test_valid_ledger_and_worker_identity(self):
        self.assertTrue(verify_case(self.case)["valid"])
        completed = self.case.audit_events.filter(action="processing.completed").first()
        self.assertEqual(completed.service, "metadata-worker")
        self.assertEqual(completed.actor_id, self.case.owner_id)

    def test_modified_missing_and_reordered_events_detected(self):
        event = self.case.audit_events.filter(sequence=2).get()
        old = event.action
        event.action = "tampered"
        event.save()
        self.assertFalse(verify_case(self.case)["valid"])
        event.action = old
        event.save()
        self.assertTrue(verify_case(self.case)["valid"])
        event.delete()
        self.assertFalse(verify_case(self.case)["valid"])

    def test_custody_tampering_detected_even_after_new_append(self):
        row = self.case.custody_events.first()
        row.details = {"modified": True}
        row.save()
        append_event(self.case, self.case.owner, "test.later_append")
        self.assertFalse(verify_case(self.case)["valid"])

    def test_external_checkpoint_detects_deleted_tail_without_repair(self):
        checkpoint = verify_case(self.case)["checkpoint"]
        self.case.audit_events.filter(sequence=checkpoint["sequence"]).delete()
        before = self.case.audit_events.count()
        self.assertFalse(verify_case(self.case, checkpoint)["valid"])
        self.assertEqual(before, self.case.audit_events.count())
