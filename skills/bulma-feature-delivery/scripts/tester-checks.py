#!/usr/bin/env python3
"""Run scoped verified regressions and measure changed feature lines in the fd tester."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from tempfile import mkdtemp

sys.dont_write_bytecode = True
BUS_SCRIPTS = Path(__file__).resolve().parents[2] / 'bulma-bus/scripts'
sys.path.insert(0, str(BUS_SCRIPTS))
import runtime

DEFAULT_MINIMUM = 80
HUNK = re.compile(rb'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)


def memory_settings(memory):
    section = ''
    fenced = False
    for line in memory.splitlines():
        if line.lstrip().startswith('```'):
            fenced = not fenced
        if fenced:
            continue
        if line.startswith('## '):
            section = line[3:].strip()
        elif line.startswith('- '):
            key, _, value = line[2:].partition(':')
            yield section, key, value.strip()


def valid_argv(argv):
    return (isinstance(argv, list) and bool(argv)
            and all(isinstance(arg, str) and arg and '\0' not in arg for arg in argv))


def relative_path(path):
    if not isinstance(path, str) or not path or '\0' in path:
        return False
    parts = PurePosixPath(path).parts
    return bool(parts) and not path.startswith('/') and '..' not in parts


def changes(repo, base):
    """Current paths, with old names for rename-aware line diffs and prevention."""
    names = runtime.git(repo, 'diff', '--name-status', '--find-renames', '-z', base, '--')
    fields = iter(os.fsdecode(part) for part in names.split(b'\0')[:-1])
    tracked = {}
    renamed = set()
    for status in fields:
        old = next(fields)
        if status.startswith(('R', 'C')):
            tracked[next(fields)] = old
            renamed.add(old)
        else:
            tracked[old] = old
    untracked = set(os.fsdecode(path) for path in runtime.git(
        repo, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if path)
    return tracked, untracked, renamed


def receipt(path, repo):
    path = Path(path)
    if not path.is_absolute() or path.resolve().is_relative_to(repo):
        raise ValueError('receipt needs an absolute path outside the checkout')
    record = json.loads(path.read_text(encoding='utf-8'))
    log = path.parent / 'output.log'
    if (record['version'] != 1 or record['stable'] is not True
            or record['fingerprint'] != runtime.digest(record['identity'])
            or Path(record['log']) != log or sha256(log.read_bytes()).hexdigest() != record['log_sha256']):
        raise ValueError('runtime receipt is unstable or its evidence changed')
    return record


def execute(args, argv):
    result = subprocess.run(
        [sys.executable, str(BUS_SCRIPTS / 'runtime.py'), 'run', '--repo', str(args.repo),
         '--directory', str(args.directory), '--environment', args.environment, '--', *argv],
        text=True, capture_output=True)
    if not result.stdout:
        raise ValueError(result.stderr.strip() or 'runtime did not return evidence')
    summary = json.loads(result.stdout)
    evidence = summary['evidence']
    if summary['exit_code'] != 0:
        return {'status': 'fail', 'exit_code': summary['exit_code'], 'evidence': evidence}
    try:
        receipt(evidence, args.repo)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        return {'status': 'error', 'reason': str(exc), 'evidence': evidence}
    return {'status': 'pass', 'exit_code': 0, 'evidence': evidence}


def verify_prevention(args, entry):
    path = entry['feedback']
    root = (args.project / 'feedback').resolve()
    if not relative_path(path) or len(PurePosixPath(path).parts) != 2 or Path(path).suffix != '.md':
        raise ValueError('expected feedback/<pattern>/<assessment>.md')
    assessment = (root / path).resolve()
    if not root.is_relative_to(args.project) or not assessment.is_relative_to(root):
        raise ValueError('assessment must live in local project feedback')
    categories = re.findall(r'^- Category: (.*)$', assessment.read_text(encoding='utf-8'), re.M | re.I)
    if [item.strip().lower() for item in categories] != ['confirmed defect']:
        raise ValueError('assessment does not confirm a defect')
    argv = entry['argv']
    if not valid_argv(argv):
        raise ValueError('expected a regression test argv')
    red, green = (receipt(entry[key], args.repo) for key in ('red', 'green'))
    if (not 0 < red['exit_code'] < 124 or green['exit_code'] != 0
            or any(record['identity']['command'] != argv for record in (red, green))
            or all(red['identity'][key] == green['identity'][key] for key in ('head', 'diff', 'untracked'))):
        raise ValueError('expected RED and GREEN receipts for the registered test on different trees')
    return tuple(argv)


def run_prevention(args, settings, touched):
    runs = {}
    for path in args.ran if args.environment else ():
        try:
            record = receipt(path, args.repo)
            command = record['identity']['command']
            if runtime.reusable(record, runtime.identity(args.repo, command, args.environment)):
                runs[tuple(command)] = {'status': 'pass', 'exit_code': 0, 'evidence': path}
        except (ValueError, KeyError, TypeError, OSError):
            continue

    for section, key, value in settings:
        if (section, key) != ('Checks', 'prevention'):
            continue
        try:
            entry = json.loads(value)
            paths = entry['paths']
            if not isinstance(paths, list) or not paths or not all(map(relative_path, paths)):
                raise ValueError('expected repository-relative paths')
        except (ValueError, KeyError, TypeError):
            print('tester-checks: ignored malformed prevention registration', file=sys.stderr)
            continue
        if not any(name == path or (path.endswith('/') and name.startswith(path))
                   for path in paths for name in touched):
            continue
        try:
            argv = verify_prevention(args, entry)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            yield {'feedback': entry.get('feedback'), 'status': 'unavailable', 'reason': str(exc)}
            continue
        if argv not in runs:
            runs[argv] = execute(args, list(argv))
        yield {'feedback': entry['feedback'], **runs[argv]}


def added_lines(repo, base, path, tracked, untracked):
    if path in untracked:
        return set(range(1, len((repo / path).read_bytes().splitlines()) + 1))
    old = tracked[path]
    patch = runtime.git(repo, '--literal-pathspecs', 'diff', '--find-renames', '--no-ext-diff',
                        '--no-textconv', '--no-color', '--unified=0', '--inter-hunk-context=0',
                        base, '--', *dict.fromkeys((old, path)))
    return {line for start, count in HUNK.findall(patch)
            for line in range(int(start), int(start) + int(count or 1))}


def feature_lines(args, base, tracked, untracked):
    paths = set(args.feature_path)
    if not paths or any(not relative_path(path) or not (args.repo / path).resolve().is_relative_to(args.repo)
                        or not (args.repo / path).is_file()
                        or path not in tracked and path not in untracked for path in paths):
        raise ValueError('provide changed production paths for the feature scope')
    lines = {path: added_lines(args.repo, base, path, tracked, untracked) for path in sorted(paths)}
    scope = {}
    for value in args.feature_lines:
        match = re.fullmatch(r'(.+):([1-9]\d*)-([1-9]\d*)', value)
        if not match or match[1] not in lines or int(match[2]) > int(match[3]):
            raise ValueError('expected --feature-lines FILE:START-END for a feature path')
        path = match[1]
        start, end = int(match[2]), int(match[3])
        selected = {line for line in lines[path] if start <= line <= end}
        if not selected:
            raise ValueError(f'feature range has no added or modified lines: {value}')
        scope.setdefault(path, set()).update(selected)
    return {**lines, **scope}


def read_lcov(report, repo):
    files = {}
    source = None
    for row in report.read_text(encoding='utf-8').splitlines():
        if not row or row.startswith('#') or (source is None and row.startswith('TN:')):
            continue
        if row.startswith('SF:') and source is None and row[3:]:
            source = files.setdefault((repo / row[3:]).resolve(), {})
        elif row == 'end_of_record' and source is not None:
            source = None
        elif row.startswith('DA:') and source is not None:
            match = re.fullmatch(r'DA:([1-9]\d*),(\d+)(?:,[^,]+)?', row)
            if not match:
                raise ValueError('invalid LCOV line record')
            number, hits = map(int, match.groups())
            source[number] = source.get(number, False) or hits > 0
        elif source is None or not row.startswith(
                ('VER:', 'FN:', 'FNDA:', 'FNL:', 'FNA:', 'FNF:', 'FNH:',
                 'BRDA:', 'BRF:', 'BRH:', 'MCDC:', 'MCF:', 'MCH:', 'LF:', 'LH:')):
            raise ValueError('invalid LCOV report')
    if source is not None or not files:
        raise ValueError('incomplete LCOV report')
    return files


def feature_coverage(args, settings, base, tracked, untracked):
    if args.work_kind != 'feature':
        return {'status': 'not_applicable', 'reason': 'work kind is not feature'}
    if args.no_feature_code:
        return {'status': 'not_applicable', 'reason': args.no_feature_code}

    result = {}
    try:
        config = [json.loads(value) for section, key, value in settings
                  if (section, key) == ('Preferences', 'feature_coverage')]
        if len(config) > 1:
            raise ValueError('expected one project feature_coverage preference')
        profile = config[0] if config else {}
        minimum = profile.get('minimum', DEFAULT_MINIMUM)
        if type(minimum) is not int or not 1 <= minimum <= 100:
            raise ValueError('feature coverage minimum must be an integer from 1 to 100')
        result['minimum'] = minimum
        argv = profile.get('argv', args.coverage_argv)
        if not valid_argv(argv) or not any('{report}' in arg or '{report_dir}' in arg for arg in argv):
            raise ValueError('configure a coverage runner that writes {report} or {report_dir}/lcov.info')
        lines = feature_lines(args, base, tracked, untracked)
        result['scope'] = {'base': base, 'paths': list(lines), 'ranges': args.feature_lines}
        report = Path(mkdtemp(prefix='coverage-', dir=args.directory)) / 'lcov.info'
        command = [arg.replace('{report_dir}', str(report.parent)).replace('{report}', str(report))
                   for arg in argv]
        result.update(execute(args, command))
        if result['status'] != 'pass':
            return result
        if not report.is_file() or report.is_symlink():
            raise ValueError('coverage runner did not produce a fresh LCOV report')
        result.update(report=str(report), report_sha256=sha256(report.read_bytes()).hexdigest())
        files = read_lcov(report, args.repo)
        covered = executable = 0
        for path, added in lines.items():
            data = files.get((args.repo / path).resolve())
            if data is None:
                raise ValueError(f'LCOV report has no source record for {path}')
            selected = added & data.keys()
            if not selected:
                raise ValueError(f'LCOV report has no executable changed lines for {path}')
            executable += len(selected)
            covered += sum(data[line] for line in selected)
        return {**result, 'status': 'pass' if 100 * covered >= minimum * executable else 'fail',
                'covered': covered, 'executable': executable}
    except (ValueError, AttributeError, OSError) as exc:
        return {**result, 'status': 'unavailable', 'reason': str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--base', required=True)
    parser.add_argument('--project', required=True, type=Path, help='shared local BULMA_REPO directory')
    parser.add_argument('--directory', required=True, type=Path, help='tester evidence directory')
    parser.add_argument('--work-kind', required=True, choices=('feature', 'bug', 'regression', 'chore', 'spike'))
    parser.add_argument('--ran', action='append', default=[], help='current tester attempt receipt')
    parser.add_argument('--environment', default='', help='current runtime environment fingerprint')
    parser.add_argument('--coverage-argv', type=json.loads, help='discovered project coverage runner argv')
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--feature-path', action='append', default=[])
    scope.add_argument('--no-feature-code', metavar='REASON')
    parser.add_argument('--feature-lines', action='append', default=[], metavar='FILE:START-END')
    args = parser.parse_args()
    if args.feature_lines and not args.feature_path:
        parser.error('--feature-lines requires --feature-path')
    try:
        args.repo = Path(os.fsdecode(runtime.git(args.repo, 'rev-parse', '--show-toplevel').rstrip(b'\n'))).resolve()
        args.project = runtime.outside_repo(args.project, args.repo)
        args.directory = runtime.outside_repo(args.directory, args.repo)
        memory = args.project / 'memory.md'
        if not memory.resolve().is_relative_to(args.project):
            raise ValueError('project checks must come from shared local memory')
        settings = list(memory_settings(memory.read_text(encoding='utf-8'))) if memory.is_file() else []
        base = os.fsdecode(runtime.git(args.repo, 'merge-base', 'HEAD', args.base).strip())
        tracked, untracked, renamed = changes(args.repo, base)
        prevention = list(run_prevention(args, settings, tracked.keys() | untracked | renamed))
        args.directory.mkdir(parents=True, exist_ok=True)
        coverage = feature_coverage(args, settings, base, tracked, untracked)
        passed = (all(row['status'] in ('pass', 'unavailable') for row in prevention)
                  and coverage['status'] in ('pass', 'not_applicable'))
        print(json.dumps({'hard_gate': 'pass' if passed else 'fail', 'prevention': prevention,
                          'feature_coverage': coverage}, indent=2))
        return 0 if passed else 1
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f'tester-checks: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
