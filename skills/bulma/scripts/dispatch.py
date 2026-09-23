"""bulma.py dispatch: pick, escalate and measure worker tiers (dispatch.tier).

One spawn_worker call = one unit. Jev picks the coder tier; hard rules clamp
it in code; results escalate it; DISPATCH.tsv measures cost and quality.
Contract: ../DISPATCH.md. Loaded by bulma.py, which passes itself to
`register`, so both share one BulmaError and one config.
"""
from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

core = None  # bulma.py module, set by register()

TICKET_TEXT_CAP = 3000
# dispatch.tier: worker tiers, cheapest first. `heavy` is the session model.
TIERS = ("light", "standard", "heavy")
UNIT_KINDS = ("slice", "ci_fix", "lstm_patch")
# Roles that never ask Jev. Gates stay on the session model.
FIXED_ROLES = {
    "tester": "light", "shipper": "light",
    "reviewer": "heavy", "quality": "heavy", "plan_critic": "heavy",
    "debugger": "heavy", "triage": "heavy", "grill": "heavy",
}
UI_SUFFIXES = (".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".html")
COLUMNS = [
    "ts_iso", "unit_id", "decision_id", "unit_kind", "ticket", "files", "ui",
    "risk", "tier_jev", "confidence", "acted", "tier_run", "clamp", "power",
    "criteria_version", "first_pass", "loops_used", "escalated_to",
    "worker_tokens", "outcome", "note", "repo", "pr", "state",
]
# Spawn keys each host can apply per worker call (DISPATCH.md §Hosts).
# `agent` names a worker definition that pins what the host cannot take per
# call, e.g. a Claude Code agent file with `effort: low`.
SPAWN_KEYS = ("model", "effort", "agent")
HOST_KEYS = {
    "claude": ("model", "agent"),
    "codex": ("model", "effort", "agent"),
    "cursor": ("model", "agent"),
    "grok": ("agent",),
}
# Promotion gate defaults; override in bulma.json "dispatch_gate".
GATE_UNITS = 30
GATE_REVERSED = 0.10


# One spawn_worker call = one unit. Jev picks the coder tier; hard rules clamp
# it in code; results escalate it; DISPATCH.tsv measures cost and quality.

def dispatch_path(root):
    return Path(root) / ".ruver-bulma" / "DISPATCH.tsv"


_RISK_SCRIPT = None


def high_risk_path(path):
    """classify-risk.py from ruver-code-review decides high surfaces. Missing script -> high."""
    global _RISK_SCRIPT
    if _RISK_SCRIPT is None:
        script = core.SKILL_DIR.parent / "ruver-code-review" / "scripts" / "classify-risk.py"
        _RISK_SCRIPT = False
        if script.is_file():
            spec = importlib.util.spec_from_file_location("classify_risk", script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _RISK_SCRIPT = module
    if not _RISK_SCRIPT:
        return True
    return _RISK_SCRIPT.path_is_high(path)


TICKET_HEAD = re.compile(r"^##\s+Ticket\s+(\S+?):\s*(.*)$")
TICKET_FIELD = re.compile(r"^-\s+\*\*([A-Za-z ]+):\*\*\s*(.*)$")


def parse_tickets(path):
    """TICKETS.md (fd template) -> [{id, title, text, fields}]."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as err:
        raise core.BulmaError(4, "cannot read %s: %s" % (path, err))
    tickets = []
    field = None
    for line in lines:
        head = TICKET_HEAD.match(line)
        if head:
            tickets.append({"id": head.group(1), "title": head.group(2).strip(), "text": [line], "fields": {}})
            field = None
            continue
        if not tickets:
            continue
        tickets[-1]["text"].append(line)
        match = TICKET_FIELD.match(line.strip())
        if match:
            field = match.group(1).strip().lower()
            tickets[-1]["fields"][field] = match.group(2).strip()
        elif field and line.strip():
            tickets[-1]["fields"][field] = (tickets[-1]["fields"][field] + "\n" + line.strip()).strip()
    for ticket in tickets:
        ticket["text"] = "\n".join(ticket["text"]).strip()
    if not tickets:
        raise core.BulmaError(4, "no `## Ticket N:` sections in %s" % path)
    return tickets


def split_files(value):
    return [f.strip("`* ") for f in re.split(r"[,\s]+", value or "") if f.strip("`* ")]


def acceptance_bullets(value):
    return [line.lstrip("-* ").strip() for line in (value or "").splitlines() if line.lstrip("-* ").strip()]


def unit_state(unit_kind, text, fields, files, risk, path, ui):
    if ui is None:
        ui = "yes" if any(f.lower().endswith(UI_SUFFIXES) for f in files) else "no"
    return {
        "unit_kind": unit_kind,
        "ticket_text": text[:TICKET_TEXT_CAP],
        "acceptance": acceptance_bullets(fields.get("acceptance", "")),
        "files": files,
        "files_count": len(files),
        "seam": fields.get("seam", ""),
        "ui": ui,
        "risk": risk,
        "path": path,
        "prior_failures": 0,
    }


def dispatch_units(args):
    """(ticket id, state) per unit from --tickets or --unit-text."""
    if args.unit_kind not in UNIT_KINDS:
        raise core.BulmaError(4, "unit kind must be one of %s" % ", ".join(UNIT_KINDS))
    extra_files = split_files(",".join(args.files or []))
    if args.tickets:
        tickets = parse_tickets(args.tickets)
        if args.ticket:
            wanted = set(args.ticket)
            tickets = [t for t in tickets if t["id"] in wanted]
            if len(tickets) != len(wanted):
                raise core.BulmaError(4, "ticket(s) not found in %s: %s" % (args.tickets, ", ".join(sorted(wanted - {t["id"] for t in tickets}))))
        return [(t["id"], unit_state(args.unit_kind, t["text"], t["fields"],
                                     split_files(t["fields"].get("files", "")) or extra_files,
                                     args.risk, args.path, args.ui)) for t in tickets]
    if args.unit_text:
        try:
            text = Path(args.unit_text).read_text(encoding="utf-8")
        except OSError as err:
            raise core.BulmaError(4, "cannot read %s: %s" % (args.unit_text, err))
        return [(args.unit_id or args.unit_kind, unit_state(args.unit_kind, text, {}, extra_files, args.risk, args.path, args.ui))]
    raise core.BulmaError(4, "dispatch plan needs --tickets FILE or --unit-text FILE")


def clamp_tier(judged, power, state):
    """Jev answer -> (tier to run, reason). Rules 1, 4, 5 of the dispatch spec."""
    if power == "shadow":
        return "heavy", "shadow"
    tier = judged.get("choice")
    if not judged.get("act") or tier not in TIERS:
        return "heavy", "undecided"
    if tier == "light" and (state.get("risk") == "elevated" or any(high_risk_path(f) for f in state.get("files", []))):
        return "standard", "risk"
    return tier, ""


def escalate(tier):
    return TIERS[min(TIERS.index(tier) + 1, len(TIERS) - 1)] if tier in TIERS else "heavy"


def spawn_args(cfg, host, tier):
    """Host mapping from bulma.json `tiers`; heavy, no host, or no mapping -> inherit."""
    if tier == "heavy" or not host:
        return "inherit"
    mapping = ((cfg.get("tiers") or {}).get(host) or {}).get(tier)
    if not isinstance(mapping, dict) or not mapping:
        return "inherit"
    return " ".join("%s=%s" % (k, v) for k, v in sorted(mapping.items()))


def criteria_version(hook):
    return str(hook["questions"]["tier"].get("criteria_version", ""))


def cmd_dispatch_plan(args):
    catalog = core.load_catalog()
    hook = core.find_hook(catalog, "dispatch.tier")
    root = core.ruver_root(args.ruver_root)
    cfg = core.load_config()
    model = args.model or cfg.get("model") or core.DEFAULT_MODEL
    context = core.parse_kv(args.context)
    jobs = []
    for ticket, state in dispatch_units(args):
        state_path, _ = core.save_state(root, hook["id"], state, None)
        request, thresholds, doc = core.prepare(hook, state, cfg, args.power, model, {})
        jobs.append((ticket, state, state_path, request, thresholds, doc))
    workers = max(1, min(8, len(jobs)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(
            lambda job: job[:3] + core.ask_one(hook, job[3], job[4], job[5], args.replay, {"tier": "heavy"}, dict(context, ticket=job[0])),
            jobs))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    decision_rows, units, out = [], [], []
    code = 0
    for ticket, state, state_path, doc, rows, item_code in results:
        code = max(code, item_code)
        decision_rows.extend(rows)
        judged = doc["answers"]["tier"]
        tier_run, reason = clamp_tier(judged, doc["power"], state)
        if tier_run != "heavy" and spawn_args(cfg, args.host, tier_run) == "inherit":
            # Nothing to spawn it on: log what really runs, so the report stays honest.
            tier_run, reason = "heavy", "unmapped"
        unit_id = "u-%s" % doc["decision_id"]
        units.append({
            "ts_iso": ts, "unit_id": unit_id, "decision_id": doc["decision_id"],
            "unit_kind": state["unit_kind"], "ticket": ticket, "files": ",".join(state["files"]),
            "ui": state["ui"], "risk": state["risk"], "tier_jev": judged.get("choice", ""),
            "confidence": judged.get("confidence", ""), "acted": "true" if judged.get("act") else "false",
            "tier_run": tier_run, "clamp": reason, "power": doc["power"],
            "criteria_version": criteria_version(hook), "first_pass": "", "loops_used": "0",
            "escalated_to": "", "worker_tokens": "", "outcome": "", "note": "",
            "repo": context.get("repo", ""), "pr": context.get("pr", ""), "state": str(state_path),
        })
        out.append(dict(ticket=ticket, unit_id=unit_id, tier=tier_run, clamp=reason,
                        spawn=spawn_args(cfg, args.host, tier_run), j=core.j_line(doc)))
    core.append_rows(root, decision_rows)
    core.append_rows(root, units, dispatch_path(root), COLUMNS)
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for item in out:
            print("ticket %s tier=%s%s spawn=%s unit=%s · %s" % (
                item["ticket"], item["tier"], " (%s)" % item["clamp"] if item["clamp"] else "",
                item["spawn"], item["unit_id"], item["j"]))
    return code


def cmd_dispatch_role(args):
    if args.role not in FIXED_ROLES:
        raise core.BulmaError(4, "unknown role %r; fixed roles: %s (coder goes through `dispatch plan`)" % (args.role, ", ".join(sorted(FIXED_ROLES))))
    cfg = core.load_config()
    power, _ = core.resolve_power(args.power, "dispatch.tier", cfg)
    tier = "heavy" if power == "shadow" else FIXED_ROLES[args.role]
    if spawn_args(cfg, args.host, tier) == "inherit":
        tier = "heavy"
    print("role %s tier=%s spawn=%s" % (args.role, tier, spawn_args(cfg, args.host, tier)))
    return 0


def load_units(root):
    path = dispatch_path(root)
    return path, core.read_rows(path, COLUMNS)


def find_unit(rows, unit_id, path):
    hits = [r for r in rows if r["unit_id"] == unit_id]
    if not hits:
        raise core.BulmaError(4, "no unit %s in %s" % (unit_id, path))
    return hits[-1]


def add_note(row, note):
    if note:
        row["note"] = (row["note"] + " | " if row["note"] else "") + note


def jev_owned(unit):
    """A failure counts against Jev only when Jev's answer lowered the tier."""
    return unit["acted"] == "true" and unit["power"] != "shadow" and unit["tier_jev"] in ("light", "standard")


def cmd_dispatch_result(args):
    root = core.ruver_root(args.ruver_root)
    path, rows = load_units(root)
    unit = find_unit(rows, args.unit_id, path)
    if args.tokens is not None:
        unit["worker_tokens"] = str(int(unit["worker_tokens"] or 0) + args.tokens)
    loops = int(unit["loops_used"] or 0)
    current = unit["escalated_to"] or unit["tier_run"]
    if args.value == "pass":
        if not unit["first_pass"]:
            unit["first_pass"] = "yes" if loops == 0 else "no"
        core.write_rows(path, rows, COLUMNS)
        print("unit %s pass tier=%s loops=%d" % (unit["unit_id"], current, loops))
        return 0
    unit["loops_used"] = str(loops + 1)
    unit["first_pass"] = unit["first_pass"] or "no"
    add_note(unit, "fail:%s" % args.stage)
    nxt = escalate(current)
    if nxt != current:
        unit["escalated_to"] = nxt
    if jev_owned(unit) and unit["outcome"] != "reversed" and current != "heavy":
        unit["outcome"] = "reversed"
        core.set_outcome(root, unit["decision_id"], "tier", "reversed", "escalated %s->%s on %s" % (current, nxt, args.stage))
    core.write_rows(path, rows, COLUMNS)
    print("unit %s fail:%s tier=%s spawn=%s loops=%d" % (
        unit["unit_id"], args.stage, nxt, spawn_args(core.load_config(), args.host, nxt), loops + 1))
    return 0


def cmd_dispatch_reverse(args):
    """A later signal (CI, QA PR_BUG, lstm should-fix) lands on a unit's files."""
    root = core.ruver_root(args.ruver_root)
    path, rows = load_units(root)
    if args.unit_id:
        targets = [find_unit(rows, args.unit_id, path)]
    elif args.file:
        wanted = set(args.file)
        targets = [r for r in rows if wanted & set(split_files(r["files"])) and (not args.pr or r["pr"] == args.pr)]
    else:
        raise core.BulmaError(4, "dispatch reverse needs a unit id or --file PATH")
    changed = 0
    for unit in targets:
        if unit["outcome"] == "reversed":
            continue
        unit["outcome"] = "reversed"
        add_note(unit, "late:%s" % args.source)
        if jev_owned(unit):
            core.set_outcome(root, unit["decision_id"], "tier", "reversed", "late %s" % args.source)
        changed += 1
    core.write_rows(path, rows, COLUMNS)
    print("reversed %d unit(s) from %s" % (changed, args.source))
    return 0


def pct(part, whole):
    return "%d%%" % round(100 * part / whole) if whole else "-"


def dispatch_rows(args):
    paths = [dispatch_path(core.ruver_root(args.ruver_root))] if args.repo_only else sorted(core.ruver_home().glob("*/.ruver-bulma/DISPATCH.tsv"))
    rows = []
    for path in paths:
        rows.extend(core.read_rows(path, COLUMNS))
    if args.since:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(args.since))
        rows = [r for r in rows if (core.parse_ts(r["ts_iso"]) or cutoff) >= cutoff]
    return rows


def tier_stats(items):
    n = len(items)
    done = [r for r in items if r["first_pass"]]
    tokens = [int(r["worker_tokens"]) for r in items if r["worker_tokens"].isdigit()]
    return {
        "n": n,
        "first_pass": pct(sum(1 for r in done if r["first_pass"] == "yes"), len(done)),
        "first_pass_rate": (sum(1 for r in done if r["first_pass"] == "yes") / len(done)) if done else None,
        "reversed": pct(sum(1 for r in items if r["outcome"] == "reversed"), n),
        "reversed_rate": (sum(1 for r in items if r["outcome"] == "reversed") / n) if n else 0.0,
        "loops": "%.2f" % (sum(int(r["loops_used"] or 0) for r in items) / n) if n else "-",
        "tokens": sum(tokens),
        "per_unit": (sum(tokens) // len(tokens)) if tokens else None,
    }


def gate_line(rows, cfg):
    gate = cfg.get("dispatch_gate") or {}
    need = int(gate.get("units", GATE_UNITS))
    max_rev = float(gate.get("reversed", GATE_REVERSED))
    live_light = [r for r in rows if r["power"] != "shadow" and r["tier_run"] == "light"]
    if live_light:
        stats = tier_stats(live_light)
        if len(live_light) < need:
            return "gate: live, %d/%d light units; keep collecting" % (len(live_light), need)
        if stats["reversed_rate"] > max_rev:
            return "gate: demote to shadow (light reversed %s > %d%%)" % (stats["reversed"], round(100 * max_rev))
        return "gate: holds (light reversed %s <= %d%%)" % (stats["reversed"], round(100 * max_rev))
    shadow = [r for r in rows if r["power"] == "shadow"]
    labelled = [r for r in shadow if r["tier_jev"] in ("light", "standard")]
    if len(labelled) < need:
        return "gate: shadow, %d/%d units Jev would lower; keep collecting" % (len(labelled), need)
    light = tier_stats([r for r in shadow if r["tier_jev"] == "light"])
    heavy = tier_stats([r for r in shadow if r["tier_jev"] == "heavy"])
    if light["first_pass_rate"] is None or heavy["first_pass_rate"] is None:
        return "gate: shadow, no finished units on both sides yet"
    if light["first_pass_rate"] >= heavy["first_pass_rate"]:
        return "gate: ready for cautious (Jev-light first pass %s >= heavy %s): `bulma.py power` per hook dispatch.tier=cautious" % (light["first_pass"], heavy["first_pass"])
    return "gate: stay shadow (Jev-light first pass %s < heavy %s)" % (light["first_pass"], heavy["first_pass"])


def cmd_dispatch_report(args):
    rows = dispatch_rows(args)
    if not rows:
        print("no dispatch units found")
        return 0
    print("| version | power | tier_run | n | first_pass | reversed | loops/unit | tokens | tokens/unit |")
    print("|---|---|---|---|---|---|---|---|---|")
    groups = {}
    for row in rows:
        live = "shadow" if row["power"] == "shadow" else "live"
        groups.setdefault((row["criteria_version"], live, row["tier_run"]), []).append(row)
    for (version, live, tier), items in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], TIERS.index(kv[0][2]) if kv[0][2] in TIERS else 9)):
        st = tier_stats(items)
        print("| %s | %s | %s | %d | %s | %s | %s | %d | %s |" % (
            version or "-", live, tier, st["n"], st["first_pass"], st["reversed"], st["loops"],
            st["tokens"], st["per_unit"] if st["per_unit"] is not None else "-"))
    shadow = [r for r in rows if r["power"] == "shadow"]
    if shadow:
        print()
        print("shadow labels (all ran heavy): " + " · ".join(
            "%s %d (first pass %s)" % (t, len(items), tier_stats(items)["first_pass"])
            for t in TIERS for items in [[r for r in shadow if r["tier_jev"] == t]] if items))
    clamped = sum(1 for r in rows if r["clamp"] == "risk")
    if clamped:
        print("clamped light->standard on risk: %d" % clamped)
    print(gate_line(rows, core.load_config()))
    return 0


def cmd_dispatch_review(args):
    """Reversed units grouped by what they share, to drive the next criteria edit."""
    rows = [r for r in dispatch_rows(args) if r["outcome"] == "reversed"]
    if not rows:
        print("no reversed units")
        return 0
    groups = {}
    for row in rows:
        groups.setdefault((row["unit_kind"], "ui" if row["ui"] == "yes" else "non-ui", row["tier_jev"]), []).append(row)
    for (kind, ui, tier), items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print("## %s · %s · jev=%s (%d)" % (kind, ui, tier, len(items)))
        for r in items:
            print("- %s ticket %s conf %s v%s files=%s note=%s state=%s" % (
                r["unit_id"], r["ticket"], r["confidence"], r["criteria_version"] or "-",
                r["files"] or "-", r["note"] or "-", r["state"]))
    return 0


def cmd_dispatch_map(args):
    cfg = core.load_config()
    tiers = cfg.setdefault("tiers", {})
    if args.tier is None:
        for tier in TIERS:
            print("%s %s: %s" % (args.host, tier, spawn_args(cfg, args.host, tier)))
        return 0
    if args.tier not in ("light", "standard"):
        raise core.BulmaError(4, "only light and standard map; heavy is always inherit")
    host_map = tiers.setdefault(args.host, {})
    if not args.pairs or args.pairs == ["inherit"]:
        host_map.pop(args.tier, None)
    else:
        pairs = core.parse_kv(args.pairs)
        allowed = HOST_KEYS.get(args.host, SPAWN_KEYS)
        bad = sorted(set(pairs) - set(allowed))
        if bad:
            raise core.BulmaError(4, "%s cannot take %s per spawn; allowed: %s (see DISPATCH.md Hosts)" % (
                args.host, ", ".join(bad), ", ".join(allowed)))
        host_map[args.tier] = pairs
    path = core.save_config(cfg)
    print("%s %s: %s written to %s" % (args.host, args.tier, spawn_args(cfg, args.host, args.tier), path))
    return 0


def register(sub, bulma):
    """Attach `dispatch` to bulma.py's parser; `bulma` is that module."""
    global core
    core = bulma
    p = sub.add_parser("dispatch", help="dispatch.tier: pick, escalate and measure worker tiers")
    dsub = p.add_subparsers(dest="dispatch_command", required=True)

    q = dsub.add_parser("plan", help="ask Jev a tier per unit (all TICKETS.md slices in one call)")
    q.add_argument("--tickets", help="fd TICKETS.md")
    q.add_argument("--ticket", action="append", help="only these ticket ids (repeatable)")
    q.add_argument("--unit-text", help="text file for a unit outside TICKETS.md (ci_fix, lstm_patch)")
    q.add_argument("--unit-id", help="label for --unit-text units")
    q.add_argument("--unit-kind", default="slice", help="|".join(UNIT_KINDS))
    q.add_argument("--files", action="append", help="paths, comma separated; used when the ticket has no Files")
    q.add_argument("--risk", default="normal", choices=["low", "normal", "elevated"])
    q.add_argument("--path", default="", help="fd path (full_feature, debug_fix, light_change)")
    q.add_argument("--ui", choices=["yes", "no"], help="default: from file suffixes")
    q.add_argument("--host", help="host key in bulma.json tiers (claude, codex, ...)")
    q.add_argument("--power")
    q.add_argument("--model")
    q.add_argument("--replay")
    q.add_argument("--context", action="append", default=[])
    q.add_argument("--ruver-root")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_dispatch_plan)

    q = dsub.add_parser("role", help="tier for a fixed role (tester, shipper, reviewer, ...)")
    q.add_argument("role")
    q.add_argument("--host")
    q.add_argument("--power")
    q.set_defaults(func=cmd_dispatch_role)

    q = dsub.add_parser("result", help="record pass or fail for a unit; fail escalates one tier")
    q.add_argument("unit_id")
    q.add_argument("value", choices=["pass", "fail"])
    q.add_argument("--stage", default="review", choices=["review", "test", "ci"])
    q.add_argument("--tokens", type=int, help="worker tokens the host reported for this round")
    q.add_argument("--host")
    q.add_argument("--ruver-root")
    q.set_defaults(func=cmd_dispatch_result)

    q = dsub.add_parser("reverse", help="a later CI fail, QA PR_BUG or lstm should-fix hit a unit")
    q.add_argument("unit_id", nargs="?")
    q.add_argument("--file", action="append", help="match units that touched this path (repeatable)")
    q.add_argument("--pr", help="with --file: only units logged for this PR")
    q.add_argument("--source", required=True, choices=["ci", "qa", "lstm", "user"])
    q.add_argument("--ruver-root")
    q.set_defaults(func=cmd_dispatch_reverse)

    for name, func, text in (("report", cmd_dispatch_report, "cost and quality per tier, plus the promotion gate"),
                             ("review", cmd_dispatch_review, "reversed units grouped, for the next criteria edit")):
        q = dsub.add_parser(name, help=text)
        q.add_argument("--since", type=int)
        q.add_argument("--repo-only", action="store_true")
        q.add_argument("--ruver-root")
        q.set_defaults(func=func)

    q = dsub.add_parser("map", help="print or set the host tier mapping in bulma.json")
    q.add_argument("host")
    q.add_argument("tier", nargs="?")
    q.add_argument("pairs", nargs="*", help="key=value (model=..., effort=...) or inherit")
    q.set_defaults(func=cmd_dispatch_map)
