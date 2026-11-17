"""Offline tests for Bulma Answer, including its process boundary."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "skills/bulma/scripts"
sys.path.insert(0, str(SCRIPT))
import answer


class AnswerTest(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.test/org/ui/pull/5"
        self.msg = {
            "ts": "a",
            "user": "u",
            "role": "teammate",
            "in_thread": True,
            "text": "Take my open UI changes through feedback and review.",
        }
        self.plan = {
            "intent": "work",
            "scope": "author_open",
            "repos": ["ui"],
            "source_ts": "a",
            "actions": ["review", "address_feedback"],
            "references": [],
            "terms": [],
            "sources": [],
        }
        self.pr = {
            "url": self.url,
            "headRefOid": "a" * 40,
            "author": {"login": "dev"},
            "state": "OPEN",
            "isDraft": False,
            "reviewDecision": "REVIEW_REQUIRED",
            "threads": [
                {"outdated": False, "pullRequestReview": {"url": self.url + "#review"}}
            ],
        }

    def test_protocol_runs_both_workflows_and_returns_host_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            replies = [
                {
                    "messages": [self.msg],
                    "repositories": ["ui"],
                    "identities": {"u": "dev"},
                },
                {"result": self.plan},
                {"result": [self.url]},
                {"result": [self.pr]},
                {"result": {"review": "queued-12", "feedback": "queued-13"}},
            ]
            run = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT / "bulma.py"),
                    "answer",
                    "--memory",
                    tmp + "/missing",
                ],
                input="".join(json.dumps(r) + "\n" for r in replies),
                text=True,
                capture_output=True,
                check=True,
            )
        records = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(
            [r["call"] for r in records[:-1]],
            ["decide", "resolve_author", "read", "dispatch"],
        )
        self.assertTrue(records[-1]["jobs"][0]["review"])
        self.assertEqual(records[-1]["jobs"][0]["feedback"], [self.url + "#review"])
        self.assertEqual(records[-1]["content"], replies[-1]["result"])

    def test_profiles_are_isolated_and_cannot_add_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "advisory"
            path.write_text(json.dumps({"actions": [], "guidance": "Research only"}))
            advisory = answer.load_memory(path)
            other = answer.load_memory(Path(tmp) / "empty")
            for profile, expected in [
                (advisory, False),
                (other, True),
                ({"actions": ["merge"]}, False),
            ]:
                calls = []

                def decide(_, schema, data):
                    calls.append(data["workflow_preferences"])
                    return dict(self.plan)

                self.pr["reviewDecision"] = "APPROVED"
                intent, _, jobs = answer.investigate(
                    [self.msg],
                    ["ui"],
                    {"u": "dev"},
                    decide,
                    lambda *_: [self.url],
                    lambda *_: [self.pr],
                    lambda _: [],
                    profile,
                )
                self.assertEqual(intent == "work", expected)
                self.assertEqual(calls, [profile.get("guidance", "")])
                if expected:
                    self.assertFalse(jobs[0]["review"])
                    self.assertTrue(jobs[0]["feedback"])

    def test_host_can_supply_a_different_workflow(self):
        def decide(*args):
            return dict(self.plan, actions=["qa", "merge"])

        _, _, jobs = answer.investigate(
            [self.msg],
            ["ui"],
            {"u": "dev"},
            decide,
            lambda *_: [self.url],
            lambda *_: [self.pr],
            lambda _: [],
            {"actions": ["qa", "merge"]},
            workflows=["qa"],
        )
        self.assertEqual(jobs[0]["workflows"], ["qa"])
        self.assertFalse(jobs[0]["review"])

    def test_open_question_requests_more_evidence_before_answer(self):
        hits = []

        def decide(_, schema, data):
            if "messages" in data:
                return dict(
                    self.plan,
                    intent="question",
                    actions=[],
                    terms=["save"],
                    sources=["code"],
                )
            if "policy" not in data["evidence"]:
                return {"answer": "", "need": ["policy"], "terms": []}
            self.assertEqual(
                data["evidence"], {"code": ["app.py:12"], "policy": ["constraint"]}
            )
            return {
                "answer": "The save guard follows the verified constraint.",
                "need": [],
                "terms": [],
            }

        def read(source, *args):
            hits.append(source)
            return ["app.py:12" if source == "code" else "constraint"]

        result = answer.investigate(
            [self.msg], ["ui"], {}, decide, None, read, lambda _: [], {}
        )
        self.assertEqual(hits, ["code", "policy"])
        self.assertIn("verified constraint", result[1]["decision"])


if __name__ == "__main__":
    unittest.main()
