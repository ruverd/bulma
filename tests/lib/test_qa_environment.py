"""Fixture tests for cross-repository QA resolution and isolated execution."""

import importlib.util
import json
import os
from argparse import Namespace
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import textwrap
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "thread_repro", ROOT / "skills/bulma-qa/scripts/thread-repro.py",
)
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)
import qa_environment as env


WEB = "Fixture/web"
API = "Fixture/api-v2"
WEB_PR = f"https://github.com/{WEB}/pull/1"
API_PR = f"https://github.com/{API}/pull/2"
WEB_APP = """
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import urllib.request

assert not Path("/source/.env.production").exists()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = b"ready"
        elif self.path == "/fixture-login":
            body = b"synthetic session"
        elif self.path == "/summary" and self.headers.get("Cookie") == "qa_fixture=synthetic":
            with urllib.request.urlopen("http://api:8201/status", timeout=2) as response:
                body = response.read()
        elif self.path == "/checkout":
            body = b'''<style>#result {font: 28px sans-serif; padding: 16px}</style>
              <button id="verify">Open fixture account</button><div id="output"></div>
              <script>
              document.querySelector('#verify').onclick=async () => {
                await fetch('/fixture-login');
                const result = document.createElement('div');
                result.id = 'result';
                result.textContent = await (await fetch('/summary')).text();
                document.querySelector('#output').append(result);
              };
              </script>'''
        else:
            self.send_error(404)
            return
        self.send_response(200)
        if self.path == "/fixture-login":
            self.send_header("Set-Cookie", "qa_fixture=synthetic; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(body)

HTTPServer(("0.0.0.0", 8200), Handler).serve_forever()
"""
API_APP = """
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/health", "/status"):
            self.send_error(404)
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Preview unavailable")

HTTPServer(("0.0.0.0", 8201), Handler).serve_forever()
"""


class Revisions(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="bulma-qa-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.sources = {}
        self.heads = {}
        self.metadata = {}
        for repo, url, ref, code in ((WEB, WEB_PR, "1", WEB_APP), (API, API_PR, "2", API_APP)):
            path = self.root / repo.split("/")[1]
            path.mkdir()
            self.git(path, "init", "-b", "main")
            self.git(path, "remote", "add", "origin", f"https://github.com/{repo}")
            (path / "app.py").write_text(textwrap.dedent(code))
            (path / ".env.production").write_text("QA_DEMO=tracked-example\n")
            self.git(path, "add", "app.py", ".env.production")
            self.git(path, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                     "-c", "commit.gpgsign=false", "commit", "-m", "Synthetic QA fixture")
            head = self.git(path, "rev-parse", "HEAD")
            self.git(path, "update-ref", f"refs/pull/{ref}/head", head)
            self.sources[repo] = path
            self.heads[repo] = head
            self.metadata[url] = {"url": url, "state": "OPEN", "headRefOid": head, "body": ""}
        self.profile = {
            "browser": "web", "browser_image": os.environ.get("BULMA_QA_BROWSER_IMAGE", "sha256:" + "a" * 64),
            "payment_mode": "stub", "synthetic_identity": True,
            "services": {
                name: {"repo": repo, "checkout": str(self.sources[repo]), "base_ref": "refs/heads/main",
                       "image": os.environ.get("BULMA_QA_SERVICE_IMAGE", "sha256:" + "b" * 64),
                       "start": ["python", "-u", "/source/app.py"], "port": port, "ready_path": "/health"}
                for name, repo, port in (("web", WEB, 8200), ("api", API, 8201))
            },
        }

    def git(self, path, *argv):
        return env.run(["git", "-C", str(path), *argv])

    def command(self, argv, **kwargs):
        if argv[:3] == ["gh", "pr", "view"]:
            return json.dumps(self.metadata[argv[3]])
        mirrors = {f"https://github.com/{repo}": path.as_uri() for repo, path in self.sources.items()}
        if argv[0] == "git" and ("fetch" in argv or "ls-remote" in argv):
            argv = [mirrors.get(arg, arg) for arg in argv]
        return env.run(argv, **kwargs)

    def test_pins_ui_to_declared_api_and_reverse_dependency(self):
        self.metadata[WEB_PR]["body"] = f"**Requires:** [Fixture API]({API_PR})"
        self.metadata[API_PR]["body"] = f"UI dependency: {WEB_PR}"
        for url in (WEB_PR, API_PR):
            pins = env.resolve_revisions(self.profile, url, self.command)
            self.assertEqual({rev.repository: rev.oid for rev in pins.values()}, self.heads)
            self.assertTrue(all(rev.ref.startswith("refs/pull/") for rev in pins.values()))

    def test_uses_configured_base_and_blocks_missing_conflicting_and_moved_pins(self):
        pins = env.resolve_revisions(self.profile, API_PR, self.command)
        self.assertEqual(pins["web"].ref, "refs/heads/main")
        self.profile["services"]["web"].pop("base_ref")
        with self.assertRaisesRegex(env.Blocked, "compatible base"):
            env.resolve_revisions(self.profile, API_PR, self.command)
        self.metadata[API_PR]["body"] = f"UI branch: {WEB} refs/heads/main"
        self.profile["dependencies"] = {self.heads[API]: {WEB: "e" * 40}}
        with self.assertRaisesRegex(env.Blocked, "conflicts"):
            env.resolve_revisions(self.profile, API_PR, self.command)
        self.metadata[API_PR]["headRefOid"] = "f" * 40
        pins = env.resolve_revisions(self.profile, API_PR, self.command)
        with self.assertRaisesRegex(env.Blocked, "changed during checkout"):
            env.checkout_revision(self.root / "move", pins["api"], self.profile["services"]["api"], self.command)

    @unittest.skipUnless(os.environ.get("BULMA_QA_BROWSER_IMAGE") and os.environ.get("BULMA_QA_SERVICE_IMAGE"),
                         "set fixture image IDs for the local Docker/agent-browser check")
    def test_cold_browser_run_reuse_readiness_and_cleanup(self):
        docker = env.local_engine()
        snapshots = lambda: (
            docker("ps", "-a", "-q", "--filter", "name=bulma-qa-"),
            docker("network", "ls", "-q", "--filter", "name=bulma-qa-"),
        )
        before = snapshots()
        args = Namespace(event="browser-fixture-1", out=self.root / "evidence", pr=WEB_PR, target="fixture")
        config = {"environment": "Synthetic UI and API V2", "kind": "local", "provision": self.profile,
                  "checkout": str(self.sources[WEB]), "isolated_data": True, "synthetic_evidence": True,
                  "surfaces": {"checkout": {
                      "label": "Checkout", "path": "/checkout", "evidence_selector": "#result",
                      "controls": {"verify": {"label": "Open fixture account", "selector": "#verify"}},
                  }}}
        plan = {"surface": "checkout", "actions": ["verify"],
                "bug_text": "Preview unavailable", "success_text": "Preview ready"}
        self.metadata[WEB_PR]["body"] = f"API V2 PR: {API_PR}"
        self.assertEqual(qa.catalog_description({"fixture": config})[0]["repositories"], [WEB, API])
        with (patch.dict(os.environ, {"BULMA_HOME": str(self.root / "bulma")}),
              patch.object(qa, "read_pr", side_effect=lambda pr: env.read_pr(pr, self.command)),
              patch.object(qa, "resolve_revisions", side_effect=lambda p, pr: env.resolve_revisions(p, pr, self.command)),
              patch.object(qa, "provision", side_effect=lambda p, r, folder: env.provision(p, r, folder, self.command))):
            planning = qa.run_job(args, {"fixture": config}, {"inspect_pr": True})
            self.assertEqual(planning["head"], self.heads[WEB])
            self.assertFalse(args.out.exists())
            wrong = Namespace(**vars(args) | {"event": "moved-plan", "out": self.root / "moved"})
            rejected = qa.run_job(wrong, {"fixture": config}, plan | {"head": "f" * 40})
            self.assertEqual(rejected["status"], "blocked")
            self.assertFalse((wrong.out / "proof.png").exists())
            self.assertEqual(snapshots(), before)
            result = qa.run_job(args, {"fixture": config}, plan | {"head": planning["head"]})
            self.assertEqual(result.get("status"), "reproduced", result)
            self.assertEqual(result["revisions"], self.heads)
            self.assertFalse(result["reused_environment"])
            self.assertTrue((args.out / "proof.png").is_file())
            self.assertEqual(snapshots(), before)
        pins = env.resolve_revisions(self.profile, WEB_PR, self.command)
        stack = self.root / "stack"
        stack.mkdir()
        with env.provision(self.profile, pins, stack, self.command) as owner:
            identity = env.environment_hash(self.profile, pins)
            names = docker("ps", "--filter", f"label=bulma.qa.profile={identity}", "--format", "{{.Names}}")
            # Remove the browser only. The outer owner still owns the application services.
            env.remove_owned(docker, "container", owner.name)
            reuse = {name.rsplit("-", 1)[-1]: name for name in names.splitlines()}
            with env.provision(self.profile | {"reuse": reuse}, pins, stack, self.command) as borrowed:
                self.assertTrue(borrowed.reused)
            self.assertEqual(docker("ps", "--filter", f"label=bulma.qa.profile={identity}",
                                    "--format", "{{.Names}}"), names)
            mismatched = self.profile | {"reuse": reuse, "services": {
                **self.profile["services"], "web": self.profile["services"]["web"] | {"ready_path": "/missing"},
            }}
            failing = self.root / "failing"
            failing.mkdir()
            ready = env.wait_ready
            with patch.object(env, "wait_ready", side_effect=lambda run, profile: ready(run, profile, timeout=2)):
                with self.assertRaisesRegex(env.Blocked, "did not become ready: web"):
                    with env.provision(mismatched, pins, failing, self.command):
                        self.fail("Unexpected readiness")
            self.assertEqual(docker("ps", "--filter", f"label=bulma.qa.profile={identity}",
                                    "--format", "{{.Names}}"), names)
        self.assertEqual(snapshots(), before)
        moved = self.root / "failed-checkout"
        moved.mkdir()
        stale = pins | {"api": env.Revision(API, pins["api"].ref, "f" * 40)}
        with self.assertRaisesRegex(env.Blocked, "changed during checkout"):
            with env.provision(self.profile, stale, moved, self.command):
                self.fail("A moving ref entered the QA environment")
        self.assertEqual(snapshots(), before)


if __name__ == "__main__":
    unittest.main()
