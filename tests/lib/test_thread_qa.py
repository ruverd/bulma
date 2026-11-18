"""Tests for the approved-case QA executor. No connector or browser credentials."""

from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[2] / "skills/bulma-qa/scripts/thread-repro.py"
SPEC = importlib.util.spec_from_file_location("thread_repro", SOURCE)
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


class ThreadQA(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = {
            "url": "http://127.0.0.1:8123/checkout", "kind": "local",
            "environment": "Synthetic app", "steps": ["Open Checkout", "Click Buy"],
            "clicks": ["#buy"], "evidence_selector": "#result",
            "bug_text": "Checkout failed", "success_text": "Checkout succeeded",
            "synthetic_evidence": True, "isolated_data": True,
        }

    def browser(self, observed, ocr=None):
        def run(*argv):
            if argv[0] == "tesseract":
                return ocr if ocr is not None else observed
            if argv[-2:] == ("get", "url"):
                return self.case["url"]
            if argv[-3:-1] == ("get", "text"):
                return observed
            if argv[-3] == "screenshot":
                Path(argv[-1]).write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            return ""
        return run

    def test_proves_exact_fixture_condition(self):
        for phrase, expected in (
            ("Checkout failed", "reproduced"),
            ("Checkout succeeded", "not_reproduced"),
        ):
            result = qa.qa_repro(self.case, self.root, self.browser(phrase))
            self.assertEqual(result["status"], expected)
            self.assertEqual(result["steps"], self.case["steps"])
            self.assertTrue((self.root / "proof.png").is_file())

    def test_blocks_sensitive_or_inconclusive_proof(self):
        for browser in (self.browser("Checkout failed", "Checkout failed password=fixture-value"),
                        self.browser("Unrelated screen")):
            with self.assertRaises(qa.Blocked):
                qa.qa_repro(self.case, self.root, browser)
            self.assertFalse((self.root / "proof.png").exists())

    def test_refuses_untrusted_origin_and_unisolated_data(self):
        for case in (dict(self.case, url="https://outside.test/checkout"),
                     dict(self.case, isolated_data=False)):
            with self.assertRaises(qa.Blocked):
                qa.qa_repro(case, self.root, lambda *args: self.fail(args))

    def test_shares_existing_bus_slot_and_releases_it(self):
        repo = self.root / "repo"
        environment = {"BULMA_HOME": str(self.root / "bulma")}
        bus = Path(environment["BULMA_HOME"]) / str(repo).lstrip("/").replace("/", "-") / ".bulma-bus"
        bus.mkdir(parents=True)
        (bus / "jobs" / "qa-pr-1").mkdir(parents=True)
        jobs = bus / "JOBS.md"
        initial = qa.TEMPLATE.read_text()
        jobs.write_text(qa.set_fields(initial, {"qa_active": "qa-pr-1",
                                               "qa_claimed_at": datetime.now(timezone.utc).isoformat()}))
        with patch.dict(os.environ, environment):
            with self.assertRaises(qa.Busy):
                with qa.qa_slot(repo, "qa-thread-1"):
                    self.fail("Overlapped existing QA")
            jobs.write_text(initial)
            with qa.qa_slot(repo, "qa-thread-1"):
                self.assertEqual(qa.field(jobs.read_text(), "qa_active"), "qa-thread-1")
            self.assertEqual(qa.field(jobs.read_text(), "qa_active"), "")


if __name__ == "__main__":
    unittest.main()
