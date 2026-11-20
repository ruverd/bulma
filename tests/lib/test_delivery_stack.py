"""Exercise ready PR publication and stack progression without tracker or forge writes."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from check_graphs import parse_edges, reachable

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
FD = SKILLS / "bulma-feature-delivery"
REPO = "fixture/product"
DEFAULT = "trunk"
PARENT_UUID = "parent-uuid"


def linear(*children):
    return {
        "source": "linear", "parent": {"id": "DEV-100", "task": "Parent acceptance criteria"},
        "parent_ids": [PARENT_UUID, "DEV-100"], "children_complete": True,
        "children": list(children),
    }


def child(issue, dependencies=(), status="started"):
    return {
        "id": issue, "task": f"Implement the acceptance criteria for {issue}",
        "parentId": PARENT_UUID, "statusType": status, "depends_on": list(dependencies),
    }


class StackTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.checkout = self.folder / "checkout"
        self.remote = self.folder / "origin.git"
        self.fixture = self.folder / "github.json"
        self.plan_path = self.folder / "STACK.plan.json"
        self.gate_path = self.folder / "gates.json"
        self.gate_path.write_text("{}")
        self.body = self.folder / "body.md"
        self.body.write_text("## How to test\nRun the acceptance scenarios.\n")
        self.env = {**os.environ, "DELIVERY_FIXTURE": str(self.fixture),
                    "PATH": f"{ROOT / 'tests/fixtures/delivery'}{os.pathsep}{os.environ['PATH']}"}
        self.save({"remote": str(self.remote), "pulls": [], "calls": []})
        self.checkout.mkdir()
        self.git("init", "--bare", "-b", DEFAULT, str(self.remote))
        self.git("init", "-b", DEFAULT)
        self.git("config", "user.name", "Stack Test")
        self.git("config", "user.email", "stack-test@example.test")
        self.git("config", "commit.gpgsign", "false")
        self.git("remote", "add", "origin", str(self.remote))
        self.anchor = self.commit("README", "Fixture\n")
        self.git("push", "origin", DEFAULT)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", self.checkout, *args],
                                       text=True, stderr=subprocess.PIPE).strip()

    def commit(self, path, content):
        (self.checkout / path).write_text(content)
        self.git("add", path)
        self.git("commit", "-m", f"Change {path}")
        return self.git("rev-parse", "HEAD")

    def save(self, data):
        self.fixture.write_text(json.dumps(data))

    def forge(self):
        return json.loads(self.fixture.read_text())

    def cli(self, script, *args, data=None, error=None):
        result = subprocess.run(
            [sys.executable, str(FD / "scripts" / script), *(str(arg) for arg in args)],
            cwd=self.checkout, env=self.env, input=json.dumps(data) if data is not None else None,
            capture_output=True, text=True,
        )
        if error:
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(error, result.stderr)
            self.assertEqual(result.stdout, "")
            return None
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def plan(self, data, **kwargs):
        plan = self.cli("stack.py", "plan", "--repo", REPO, "--default", DEFAULT,
                        "--anchor", self.anchor, data=data, **kwargs)
        if plan and plan["mode"] == "stack":
            self.plan_path.write_text(json.dumps(plan))
        return plan

    def reconcile(self, *args, **kwargs):
        return self.cli("stack.py", "reconcile", "--plan", self.plan_path,
                        "--gates", self.gate_path, *args, **kwargs)

    def publish(self, row, **kwargs):
        args = ["--position", row["position"]] if row.get("position") else []
        return self.cli("delivery_pr.py", "--repo", REPO, "--head", row["head"],
                        "--base", row["base"], "--title", row["id"], "--body-file", self.body,
                        "--assignee", "test-user", *args, **kwargs)

    def merge_as_human(self, row, squash=False):
        self.git("fetch", "origin")
        self.git("checkout", "-B", row["base"], f"origin/{row['base']}")
        if squash:
            self.git("merge", "--squash", f"origin/{row['head']}")
            self.git("commit", "-m", f"Squash {row['id']}")
        else:
            self.git("merge", "--no-ff", "-m", f"Merge {row['id']}", f"origin/{row['head']}")
        merged = self.git("rev-parse", "HEAD")
        self.git("push", "origin", row["base"], f":{row['head']}")
        data = self.forge()
        pr = next(pr for pr in data["pulls"] if pr["html_url"] == row["pr_url"])
        pr.update(state="closed", merged=True, merge_commit_sha=merged)
        self.save(data)
        return merged

    def test_normal_bulma_parent_route_and_stack_with_three_children(self):
        route = (SKILLS / "bulma/nodes/route.md").read_text()
        self.assertIn("target: developer", route)
        self.assertIn("tracker discovery", route)
        developer = parse_edges((SKILLS / "bulma-developer/GRAPH.md").read_text())
        self.assertTrue(reachable(developer, "admit", "stack"))
        delivery = parse_edges((FD / "GRAPH.md").read_text())
        self.assertTrue(reachable(delivery, "mcp_context", "stack"))
        self.assertIn("list_issues(parentId:", (FD / "LINEAR.md").read_text())
        self.assertIn("scripts/stack.py", (SKILLS / "bulma-developer/STACKED.md").read_text())
        self.assertIn("scripts/delivery_pr.py", (FD / "nodes/shipper.md").read_text())

        # Responses are scrambled, and the first two dependency edges deliberately oppose ID order.
        self.plan(linear(child("DEV-103", ["DEV-102"]), child("DEV-101", ["DEV-103"]),
                         child("DEV-102"), child("DEV-104", status="completed")))
        paths = ["feature/dev-102", "feature/dev-103", "feature/dev-101", "feature/dev-100", DEFAULT]
        titles = ["[First]", "[Second]", "[Third]", "[Final / Umbrella]"]
        merged = self.anchor
        gates = {}
        for index, title in enumerate(titles):
            report = self.reconcile("--prepare")
            row = report["active"]
            self.assertEqual((row["head"], row["base"], row["start_sha"]),
                             (paths[index], paths[index + 1], merged))
            self.assertEqual(self.reconcile()["active"], row)
            self.assertEqual(row["qa_required"], index == 3)
            self.git("checkout", "-B", row["head"], row["start_sha"])
            if not row["final"]:
                if index:
                    self.assertEqual((self.checkout / "feature").read_text(), "".join(
                        f"slice {i}\n" for i in range(index)))
                candidate = self.commit("feature", "".join(f"slice {i}\n" for i in range(index + 1)))
                self.git("push", "origin", row["head"])
                self.reconcile(error="Unexpected tip")
                self.assertEqual(self.reconcile("--candidate", candidate)["active"]["head_sha"], candidate)
                self.assertEqual(self.git("diff", "--name-only", f"{row['start_sha']}..HEAD"), "feature")
            else:
                self.assertEqual((self.checkout / "feature").read_text(), "slice 0\nslice 1\nslice 2\n")
                self.assertEqual(row["base_sha"], self.anchor)
                self.git("checkout", DEFAULT)
                default_tip = self.commit("upstream", "Default branch advanced.")
                self.git("push", "origin", DEFAULT)
                self.git("checkout", row["head"])
                row = self.reconcile()["active"]
                self.assertEqual(row["base_sha"], default_tip)
                self.assertEqual(row["start_sha"], merged)
            receipt = self.publish(row)
            self.assertFalse(receipt["draft"])
            self.assertEqual(self.publish(row), receipt)
            checked = self.reconcile()
            self.assertEqual(checked["active"]["pr_url"], receipt["url"])
            self.assertEqual(checked["order"][index]["title"], f"{title} {row['id']}")
            self.assertEqual([item["pr_url"] is not None for item in checked["order"]],
                             [i <= index for i in range(4)])
            merged = self.merge_as_human(checked["active"], squash=(index == 1))
            if not row["final"]:
                gates[row["id"]] = {"head": receipt["head_sha"], "base": row["base_sha"],
                                    "ci": "green", "review": "pass"}
                self.gate_path.write_text(json.dumps(gates))

        # Array order and deleted branches cannot change the verified head/base sequence.
        saved = json.loads(self.plan_path.read_text())
        saved["entries"].reverse()
        self.plan_path.write_text(json.dumps(saved))
        report = self.reconcile()
        self.assertEqual(report["status"], "merged")
        self.assertEqual([row["qa_required"] for row in report["order"]], [False, False, False, True])
        self.assertEqual([(entry["head"], entry["base"]) for entry in report["order"]],
                         list(zip(paths, paths[1:])))
        self.assertEqual([entry["pr_url"].rsplit("/", 1)[1] for entry in report["order"]],
                         ["71", "19", "92", "4"])
        self.assertEqual(self.git("show", f"origin/{DEFAULT}:feature"), "slice 0\nslice 1\nslice 2")
        self.assertEqual(self.git("show", f"origin/{DEFAULT}:upstream"), "Default branch advanced.")
        self.assertEqual([call[:2] for call in self.forge()["calls"]], [["pr", "create"]] * 4)

    def test_leaf_and_integrated_plan_use_one_ready_pr_and_preserve_existing_draft(self):
        self.assertEqual(self.plan(linear()), {"mode": "delivery"})
        self.assertEqual(self.plan(linear(child("DEV-101", status="canceled"))), {"mode": "delivery"})
        integrated = linear(child("DEV-101"), child("DEV-102"))
        integrated["source"] = "integrated"
        self.assertEqual(self.plan(integrated), {"mode": "delivery"})
        integrated["source"] = "planned"
        self.assertEqual(self.plan(integrated)["mode"], "stack")
        self.assertEqual(len(self.plan(linear(child("DEV-101")))["entries"]), 2)

        self.git("checkout", "-b", "feature/dev-100")
        self.commit("normal", "This ships as one PR.")
        self.git("push", "origin", "feature/dev-100")
        row = {"id": "DEV-100", "head": "feature/dev-100", "base": DEFAULT}
        pr = self.publish(row)
        self.assertFalse(pr["draft"])
        data = self.forge()
        data["pulls"][0]["draft"] = True
        self.save(data)
        self.assertTrue(self.publish(row)["draft"])
        self.assertEqual(len(self.forge()["calls"]), 1)

    def test_unverified_tracker_data_and_dependency_cycle_fail_before_publication(self):
        data = linear(child("DEV-101", ["DEV-102"]), child("DEV-102", ["DEV-101"]))
        self.plan(data, error="Stack dependency cycle")
        partial = copy.deepcopy(data)
        partial["children_complete"] = False
        self.plan(partial, error="Linear child discovery is incomplete")
        data["children"][0]["parentId"] = "different-parent"
        self.plan(data, error="outside the requested parent")
        self.assertFalse(self.forge()["calls"])

    def test_child_ci_out_of_scope_requires_live_local_proof_and_no_missing_checks(self):
        workflow = ".github/workflows/build.yml"
        (self.checkout / workflow).parent.mkdir(parents=True)
        self.anchor = self.commit(workflow, "name: Build\non:\n  pull_request:\n    branches: [trunk, production]\n")
        self.git("push", "origin", DEFAULT)
        self.plan(linear(child("DEV-101")))
        row = self.reconcile("--prepare")["active"]
        self.git("checkout", "-b", row["head"])
        # A proposed workflow on the head cannot alter the decision for the target.
        self.commit(workflow, "name: Build\non: [pull_request]\n")
        head = self.commit("feature", "A behavior covered by the scoped test.")
        self.git("push", "origin", row["head"])
        pr = self.publish(row)["url"]
        args = ["--repo", REPO, "--pr", pr, "--head-sha", head, "--base", row["base"],
                "--base-sha", self.anchor, "--default", DEFAULT]
        self.cli("stack-ci.py", *args, error="Scoped local test evidence is required")

        runtime = subprocess.check_output(
            [sys.executable, str(SKILLS / "bulma-bus/scripts/runtime.py"), "run", "--repo",
             str(self.checkout), "--directory", str(self.folder / "evidence"),
             "--environment", "fixture-v1", "--", sys.executable, "-c",
             "from pathlib import Path; assert 'covered' in Path('feature').read_text()"],
            text=True,
        )
        proof = self.folder / "proof.json"
        envelope = {"head": head, "base": self.anchor, "receipts": [json.loads(runtime)["evidence"]]}
        proof.write_text(json.dumps(envelope))
        args += ["--proof", proof]
        result = self.cli("stack-ci.py", *args)
        self.assertEqual(result["status"], "out_of_scope")
        self.assertEqual((result["head"], result["base"]), (head, self.anchor))

        data = self.forge()
        data["classic"] = ["External QA"]
        self.save(data)
        self.cli("stack-ci.py", *args, error="Required checks did not pass: External QA")
        data["classic"] = []
        data["rules"] = [{"type": "required_status_checks",
                          "parameters": {"required_status_checks": [{"context": "Org CI"}]}}]
        self.save(data)
        self.cli("stack-ci.py", *args, error="Required checks did not pass: Org CI")
        data["required"] = [{"name": "Org CI", "bucket": "pass"}]
        data["rollup"] = [{"__typename": "StatusContext", "state": "SUCCESS"}]
        self.save(data)
        self.assertEqual(self.cli("stack-ci.py", *args)["status"], "out_of_scope")

        for state in ("ERROR", "PENDING", "FAILURE", "UNKNOWN"):
            data["rollup"] = [{"__typename": "StatusContext", "state": state}]
            self.save(data)
            self.cli("stack-ci.py", *args, error="reported check is failed, pending or unknown")
        data["rollup"] = []
        self.save(data)
        envelope["base"] = head
        proof.write_text(json.dumps(envelope))
        self.cli("stack-ci.py", *args, error="another head/base pair")
        self.assertEqual(self.cli("stack-ci.py", *args, "--base", DEFAULT)["status"], "in_scope")

        self.merge_as_human(self.reconcile()["active"])
        self.reconcile("--prepare", error="without CI and review receipts")
        gates = {"DEV-101": {"head": head, "base": self.anchor, "ci": "out_of_scope",
                             "ci_scope": result, "review": "skip"}}
        self.gate_path.write_text(json.dumps(gates))
        umbrella = self.reconcile("--prepare")["active"]
        self.assertTrue(umbrella["final"])
        self.assertTrue(umbrella["qa_required"])
        self.assertEqual(umbrella["base"], DEFAULT)

    def test_drift_blocks_order_and_managed_markers_can_be_repaired(self):
        self.plan(linear(child("DEV-101"), child("DEV-102", ["DEV-101"])))
        row = self.reconcile("--prepare")["active"]
        self.git("checkout", "-b", row["head"])
        self.commit("delta", "New behavior")
        self.git("push", "origin", row["head"])
        self.publish(row)
        data = self.forge()
        pr = data["pulls"][0]
        pr["title"] = "[Second] Human-edited title"
        self.save(data)
        self.publish(row)
        self.publish(row)
        self.assertEqual(self.forge()["pulls"][0]["title"], "[First] Human-edited title")
        self.assertEqual(len(self.forge()["calls"]), 2)

        data = self.forge()
        data["pulls"][0]["base"]["ref"] = DEFAULT
        self.save(data)
        self.reconcile("--prepare", error="Base drift")
        data["pulls"][0]["base"]["ref"] = row["base"]
        self.git("push", "origin", f"HEAD:refs/heads/{row['base']}")
        self.save(data)
        self.reconcile(error="disagree on refs")
        data["pulls"][0]["base"]["sha"] = self.git("rev-parse", "HEAD")
        self.save(data)
        self.reconcile(error="Unexpected tip on destination")

        data["pulls"][0]["state"] = "closed"
        self.save(data)
        self.reconcile(error="closed without merging")
        self.publish(row, error="closed without merging")
        self.assertEqual(len(self.forge()["calls"]), 2)


if __name__ == "__main__":
    unittest.main()
