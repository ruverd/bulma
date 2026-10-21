#!/usr/bin/env python3
"""Diff-scoped floor guard: fail when a change lowers the bar instead of meeting it.

Reads the diff from the merge base to the working tree (staged, unstaged and
untracked files) and flags the moves an agent makes to get to green without
fixing anything: a new suppression, a skipped or focused test, a deleted test
file, assertions stripped from a test that stayed, an empty catch, a stub, a
silenced CI step, a lowered coverage threshold.

Exit 0 clean, 1 at least one violation, 2 the guard could not run. A 2 is never
a pass. Output names the rule and the location, never the matched text.

An intentional line carries `floor-guard: allow <reason>` on that line. A file
level move (deleted test, removed assertions) is allowed with
`--allow RULE:PATH`. Allowed items are still printed.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SKIP_EXT = {'.md', '.mdx', '.txt', '.rst', '.adoc', '.lock', '.svg', '.snap'}
SKIP_NAMES = {'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lockb',
              'Cargo.lock', 'go.sum', 'poetry.lock', 'uv.lock', 'Gemfile.lock'}
SKIP_DIRS = ('node_modules/', 'vendor/', 'dist/', 'build/', '.bulma-')

TEST_PATH = re.compile(
    r'(^|/)(tests?|__tests__|specs?|e2e)/'
    r'|(^|/)test_[^/]+\.py$|_test\.(py|go|rb|exs?)$'
    r'|\.(test|spec)\.[cm]?[jt]sx?$|(Test|Tests|Spec)\.(java|kt|cs|swift|scala)$'
    r'|\.bats$')

SUPPRESSION = re.compile(
    r'@ts-(ignore|expect-error|nocheck)'
    r'|eslint-disable|biome-ignore|oxlint-disable|prettier-ignore'  # floor-guard: allow pattern table
    r'|istanbul ignore|c8 ignore|v8 ignore'  # floor-guard: allow pattern table
    r'|#\s*type:\s*ignore|#\s*noqa|pylint:\s*disable|#\s*pragma:\s*no cover|pyright:\s*ignore'
    r'|//\s*nolint|#\[allow\(|@SuppressWarnings|rubocop:disable|shellcheck disable'  # floor-guard: allow pattern table
    r'|NOSONAR|phpcs:ignore')  # floor-guard: allow pattern table

SKIPPED_TEST = re.compile(
    r'\b(it|test|describe|context|suite)\.(skip|only|todo)\s*\('
    r'|\b(xit|xdescribe|xtest|fit|fdescribe)\s*\('
    r'|@pytest\.mark\.(skip|xfail)|\bpytest\.skip\s*\(|@unittest\.skip'
    r'|@(Disabled|Ignore)\b|\bt\.Skip(f|Now)?\s*\(|#\[ignore\]')

ASSERTION = re.compile(
    r'\bexpect\s*\(|\bassert\w*\b|\.should\b|\bt\.(Errorf?|Fatalf?)\s*\('
    r'|\brequire\.\w+\s*\(|\bXCTAssert\w*|\bassertThat\b')

STUB = re.compile(
    r'\bNotImplementedError\b|not implemented|\btodo!\s*\(|\bunimplemented!\s*\('  # floor-guard: allow pattern table
    r'|\bTODO\s*\(\s*\)', re.I)

EMPTY_CATCH = re.compile(r'\bcatch\s*(\([^)]*\))?\s*\{\s*\}|\bexcept\b[^:]*:\s*(pass|\.\.\.)\s*$')
CATCH_OPEN = re.compile(r'\bcatch\s*(\([^)]*\))?\s*\{\s*$')
EXCEPT_OPEN = re.compile(r'^\s*except\b[^:]*:\s*$')
BLOCK_CLOSE = re.compile(r'^\s*\}')
PASS_ONLY = re.compile(r'^\s*(pass|\.\.\.)\s*$')

CI_FILE = re.compile(r'(^|/)\.github/workflows/[^/]+\.ya?ml$|(^|/)\.gitlab-ci\.ya?ml$'
                     r'|(^|/)\.circleci/|(^|/)azure-pipelines\.ya?ml$|(^|/)Jenkinsfile$')
CI_SILENCED = re.compile(r'continue-on-error:\s*true|allow_failure:\s*true|\|\|\s*true\b'
                         r'|\|\|\s*exit\s+0\b')

THRESHOLD_FILE = re.compile(
    r'(^|/)((jest|vitest|vite|karma|playwright)\.config\.[cm]?[jt]s|package\.json|pyproject\.toml'
    r'|setup\.cfg|tox\.ini|\.coveragerc|codecov\.ya?ml|\.nycrc(\.json)?|\.c8rc(\.json)?'
    r'|\.github/workflows/[^/]+\.ya?ml|Makefile|\.golangci\.ya?ml)$')
THRESHOLD = re.compile(
    r'["\']?(branches|functions|lines|statements|fail[_-]under|cov-fail-under|min[_-]?coverage'
    r'|coverage[_-]?threshold|threshold)["\']?\s*[:=]\s*["\']?(\d+(?:\.\d+)?)', re.I)

ALLOW = re.compile(r'floor-guard:\s*allow\b\s*(.*)')

RULES = {
    'suppression': 'a new checker suppression',
    'skipped-test': 'a test skipped, focused or marked todo',
    'deleted-test': 'a test file deleted',
    'assertions-removed': 'assertions removed from a test that stayed',
    'empty-catch': 'an empty catch or except',
    'stub': 'an unimplemented stub',
    'ci-silenced': 'a CI step made unable to fail',
    'threshold-lowered': 'a coverage threshold lowered',
}


class GuardError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    raise GuardError(f"git {' '.join(args[:2])} failed: {result.stderr.strip()[:200]}")


def resolve_base(repo, base):
    if base:
        return base
    for ref in ('origin/HEAD', 'origin/main', 'origin/master', 'main', 'master'):
        try:
            git(repo, 'rev-parse', '--verify', '--quiet', ref + '^{commit}')
            return ref
        except GuardError:
            continue
    raise GuardError('no base ref found; pass --base')


def skipped(path):
    name = os.path.basename(path)
    _, ext = os.path.splitext(name)
    return ext in SKIP_EXT or name in SKIP_NAMES or any(d in path for d in SKIP_DIRS)


def is_test(path):
    return bool(TEST_PATH.search(path))


def parse_diff(text):
    """Yield (path, old_path, added[(line, text)], removed[(line, text)]) per file."""
    files = []
    current = None
    old_line = new_line = 0
    for raw in text.splitlines():
        if raw.startswith('diff --git '):
            current = {'path': None, 'old': None, 'added': [], 'removed': []}
            files.append(current)
            continue
        if current is None:
            continue
        if raw.startswith('--- '):
            current['old'] = None if raw[4:] == '/dev/null' else raw[6:]
            continue
        if raw.startswith('+++ '):
            current['path'] = None if raw[4:] == '/dev/null' else raw[6:]
            continue
        if raw.startswith('@@'):
            match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', raw)
            if match:
                old_line, new_line = int(match.group(1)), int(match.group(2))
            continue
        if raw.startswith('+'):
            current['added'].append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith('-'):
            current['removed'].append((old_line, raw[1:]))
            old_line += 1
    return files


def collect(repo, merge_base):
    diff = git(repo, 'diff', '-U0', '--no-color', '--no-ext-diff', '-M', merge_base)
    files = parse_diff(diff)
    untracked = git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    for path in filter(None, untracked):
        full = os.path.join(repo, path)
        if not os.path.isfile(full):
            continue
        try:
            with open(full, encoding='utf-8') as handle:
                lines = handle.read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        files.append({'path': path, 'old': None,
                      'added': list(enumerate(lines, 1)), 'removed': []})
    return files


def scan(files, allow_files):
    violations, allowed = [], []

    def hit(rule, path, line, text=''):
        item = {'rule': rule, 'path': path, 'line': line}
        marker = ALLOW.search(text) if text else None
        if marker:
            allowed.append({**item, 'reason': marker.group(1).strip() or 'unstated'})
        elif (rule, path) in allow_files:
            allowed.append({**item, 'reason': 'allowed by --allow'})
        else:
            violations.append(item)

    for entry in files:
        path = entry['path'] or entry['old']
        if not path or skipped(path):
            continue
        added, removed = entry['added'], entry['removed']

        if entry['path'] is None:
            if is_test(entry['old']):
                hit('deleted-test', entry['old'], 0)
            continue

        test = is_test(path)
        for index, (line, text) in enumerate(added):
            if SUPPRESSION.search(text):
                hit('suppression', path, line, text)
            if test and SKIPPED_TEST.search(text):
                hit('skipped-test', path, line, text)
            if not test and STUB.search(text):
                hit('stub', path, line, text)
            if EMPTY_CATCH.search(text):
                hit('empty-catch', path, line, text)
            elif index + 1 < len(added) and added[index + 1][0] == line + 1:
                following = added[index + 1][1]
                if ((CATCH_OPEN.search(text) and BLOCK_CLOSE.match(following))
                        or (EXCEPT_OPEN.match(text) and PASS_ONLY.match(following))):
                    hit('empty-catch', path, line, text)
            if CI_FILE.search(path) and CI_SILENCED.search(text):
                hit('ci-silenced', path, line, text)

        if test and entry['old'] is not None:
            gone = sum(1 for _, text in removed if ASSERTION.search(text))
            came = sum(1 for _, text in added if ASSERTION.search(text))
            if gone > came:
                hit('assertions-removed', path, removed[0][0] if removed else 0)

        if THRESHOLD_FILE.search(path):
            before = {}
            for _, text in removed:
                for key, value in THRESHOLD.findall(text):
                    before[key.lower()] = float(value)
            for line, text in added:
                for key, value in THRESHOLD.findall(text):
                    old = before.get(key.lower())
                    if old is not None and float(value) < old:
                        hit('threshold-lowered', path, line, text)

    return violations, allowed


def parse_allow(values):
    pairs = set()
    for value in values:
        rule, sep, path = value.partition(':')
        if not sep or rule not in RULES or not path:
            raise GuardError(f'bad --allow {value!r}; want RULE:PATH with RULE in {sorted(RULES)}')
        pairs.add((rule, path))
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--repo', default='.')
    parser.add_argument('--base', help='ref to diff against (default: origin/HEAD, then main)')
    parser.add_argument('--allow', action='append', default=[], metavar='RULE:PATH')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    try:
        repo = git(args.repo, 'rev-parse', '--show-toplevel').strip()
        base = resolve_base(repo, args.base)
        merge_base = git(repo, 'merge-base', 'HEAD', base).strip()
        if not merge_base:
            raise GuardError(f'no merge base with {base}')
        violations, allowed = scan(collect(repo, merge_base), parse_allow(args.allow))
    except GuardError as exc:
        print(f'floor-guard: cannot run: {exc}', file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({'base': base, 'merge_base': merge_base,
                          'violations': violations, 'allowed': allowed}, indent=2))
    else:
        for item in violations:
            print(f"VIOLATION {item['rule']} {item['path']}:{item['line']} ({RULES[item['rule']]})")
        for item in allowed:
            print(f"ALLOWED {item['rule']} {item['path']}:{item['line']} reason: {item['reason']}")
        if not violations:
            print(f'floor-guard: clean against {base} ({merge_base[:12]})')
    return 1 if violations else 0


if __name__ == '__main__':
    sys.exit(main())
