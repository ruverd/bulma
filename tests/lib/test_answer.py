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

    def test_team_work_scopes_each_pr_and_keeps_unmet_gate(self):
        tool = "https://github.com/example-org/tools/pull/68"
        other = "https://example.test/org/ui/pull/7"
        outside = "https://github.com/outside-org/tools/pull/8"
        current = dict(self.msg, references=[tool, self.url, outside])
        background = dict(self.msg, ts="previous", in_thread=False, references=[other])
        plan = dict(self.plan, scope="linked", waiting_for="", linked_work=[
            {"reference": tool, "actions": ["review", "address_feedback"], "waiting_for": ""},
            {"reference": self.url, "actions": ["review"], "waiting_for": "Real purchase walkthrough"},
            {"reference": other, "actions": ["review"], "waiting_for": ""},
            {"reference": outside, "actions": ["review"], "waiting_for": ""},
        ])

        def decide(policy, schema, data):
            self.assertIn("exclusively to other people", policy)
            self.assertEqual(data["participation"]["audience"], "team_open")
            self.assertIn("linked_work", schema["required"])
            return plan

        def read(kind, urls, *args):
            self.assertEqual(kind, "github")
            self.assertEqual(urls, [tool])
            return [dict(self.pr, url=tool)]

        intent, content, jobs = answer.investigate(
            [background, current], ["ui"], {"u": "dev"}, decide, None, read, lambda _: [],
            {"repositories": ["ui"]},
            participation={"audience": "team_open"}, linked_review_organizations=["example-org"],
        )
        self.assertEqual(intent, "work")
        self.assertEqual(content["waiting"], {self.url: "Real purchase walkthrough"})
        self.assertEqual([item["url"] for item in jobs], [tool])
        self.assertTrue(jobs[0]["review"])
        self.assertEqual(jobs[0]["feedback"], [])
        _, _, jobs = answer.investigate(
            [background, current], ["ui"], {"u": "dev"}, decide, None, self.fail, lambda _: [],
            {"repositories": ["ui"], "linked_review_organizations": []},
            participation={"audience": "team_open"}, linked_review_organizations=["example-org"],
        )
        self.assertEqual(jobs, [])

    def test_team_policy_does_not_treat_sources_as_permission(self):
        previous = dict(self.msg, ts="previous", in_thread=False, references=[self.url])
        current = dict(self.msg, text="Good news!", references=[self.url])

        def decide(policy, schema, data):
            if "current_message" not in data:
                return {"answer": "That unblocks the last check.", "need": [], "terms": []}
            return dict(self.plan, intent="light_reply", scope="none", linked_work=[
                {"reference": self.url, "actions": ["review"], "waiting_for": ""},
            ], waiting_for="")

        intent, _, jobs = answer.investigate(
            [previous, current], ["ui"], {}, decide, self.fail, self.fail, lambda _: [], {},
            participation={"audience": "team_open"},
        )
        self.assertEqual(intent, "light_reply")
        self.assertFalse(jobs)

    def test_attachment_protocol_prioritizes_current_thread_and_relevant_background(self):
        def message(ts, text, in_thread, *image_ids):
            return dict(self.msg, ts=ts, text=text, in_thread=in_thread, files=[
                {"name": image_id + ".png", "image_id": image_id, "status": "pending"}
                for image_id in image_ids
            ])

        messages = [
            message("1", "Premium Catalog checkout error", False, "related"),
            message("2", "Unrelated", False, "spare"),
            message("3", "Thread", True, "thread"),
            message("4", "Unrelated", False, "recent"),
            message("5", "Premium Catalog issue", True, "current", "second"),
        ]

        def read_images(policy, schema, request):
            self.assertIn("untrusted data", policy)
            self.assertEqual([item["image_id"] for item in request["images"]],
                             ["current", "second", "thread", "related"])
            self.assertEqual(request["images"][-1]["ts"], "1")
            return {"current": {"status": "vision", "text": "Purchase dialog shows an error."},
                    "thread": {"status": "OCR", "text": "Error"}}

        updated = answer.inspect_attachments(messages, read_images)
        self.assertEqual(updated[-1]["files"][0]["status"], "vision")
        self.assertEqual(updated[-1]["files"][1]["status"], "unreadable")
        self.assertEqual(updated[2]["files"][0]["status"], "OCR")
        self.assertEqual(updated[3]["files"][0]["status"], "not_inspected")
        self.assertNotIn("image_id", updated[-1]["files"][0])


if __name__ == "__main__":
    unittest.main()
