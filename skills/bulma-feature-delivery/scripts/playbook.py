#!/usr/bin/env python3
"""Select a task contract or check its proof checklist in existing STATE."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

SKILL = Path(__file__).resolve().parents[1]


def catalog():
    data = json.loads((SKILL / 'playbooks.json').read_text())
    if type(data['version']) is not int or data['version'] < 1:
        raise ValueError('playbook version must be a positive integer')
    for name, item in data['playbooks'].items():
        path = (SKILL / item['contract']).resolve()
        if not path.is_relative_to(SKILL) or not path.is_file():
            raise ValueError(f'{name}: missing or escaping contract')
        ids = [step['id'] for step in item['steps']]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError(f'{name}: missing or duplicate steps')
        for step in item['steps']:
            if type(step['required']) is not bool or not (SKILL / 'nodes' / (step['node'] + '.md')).is_file():
                raise ValueError(f'{name}: invalid step contract')
    if not set(data['defaults'].values()) <= data['playbooks'].keys():
        raise ValueError('unknown default playbook')
    return data


def select(kind, requested=None):
    data = catalog()
    if kind not in data['defaults']:
        raise ValueError('unknown work kind')
    name = requested or data['defaults'].get(kind)
    if name not in data['playbooks']:
        raise ValueError('unknown work kind or playbook')
    if kind == 'spike' and name != 'investigation':
        raise ValueError('a read-only spike cannot select a delivery playbook')
    item = data['playbooks'][name]
    content = json.dumps([data['version'], name, item], sort_keys=True)
    content += (SKILL / item['contract']).read_text() + (SKILL / 'PLAYBOOKS.md').read_text()
    return {'work_kind': 'spike' if name == 'investigation' else kind,
            'playbook': name, 'playbook_version': data['version'],
            'playbook_digest': hashlib.sha256(content.encode()).hexdigest(), **item}


def checklist(contract):
    lines = ['| Step | Status | Evidence | Reason |', '|---|---|---|---|']
    lines.extend(f"| {step['id']} | pending | | |" for step in contract['steps'])
    return '\n'.join(lines)


def parse_state(path):
    text = Path(path).read_text()
    frontmatter = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.S)
    if not frontmatter:
        raise ValueError('STATE needs frontmatter')
    fields = {}
    for line in frontmatter[1].splitlines():
        key, sep, value = line.partition(':')
        if sep:
            if key in fields:
                raise ValueError(f'duplicate STATE field: {key}')
            fields[key] = value.strip().strip('"\'')
    sections = re.findall(r'^## Playbook\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    if len(sections) != 1:
        raise ValueError('STATE needs one ## Playbook checklist')
    rows = {}
    for line in sections[0].splitlines():
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if cells[0] == 'Step' or set(cells[0]) <= {'-', ':'}:
            continue
        if len(cells) != 4 or cells[0] in rows:
            raise ValueError('malformed or duplicate playbook row')
        rows[cells[0]] = dict(zip(('status', 'evidence', 'reason'), cells[1:]))
    return fields, rows


def check(state, repo, environment=''):
    fields, rows = parse_state(state)
    contract = select(fields.get('work_kind'), fields.get('playbook'))
    for key in ('work_kind', 'playbook', 'playbook_version', 'playbook_digest'):
        if fields.get(key) != str(contract[key]):
            raise ValueError(f'{key} missing or changed; reconcile the contract before continuing')
    expected = {step['id']: step for step in contract['steps']}
    if rows.keys() != expected.keys():
        raise ValueError('checklist must contain exactly the selected contract steps')
    root = Path(subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--show-toplevel'], text=True).strip()).resolve()
    if Path(state).resolve().is_relative_to(root):
        raise ValueError('runtime STATE must live outside the checkout')
    for name, row in rows.items():
        if row['status'] == 'skip' and not expected[name]['required'] and row['reason']:
            continue
        if row['status'] != 'pass':
            raise ValueError(f'{name}: required proof is not complete or skip has no reason')
        proof = Path(row['evidence'])
        if (not proof.is_absolute() or not proof.is_file() or proof.stat().st_size == 0
                or proof.resolve().is_relative_to(root)):
            raise ValueError(f'{name}: proof must be an existing absolute file outside the checkout')
        if contract['playbook'] == 'refactoring' and name == 'equivalence':
            spec = importlib.util.spec_from_file_location('equivalence', SKILL / 'scripts/equivalence.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            report = module.check_report(proof, root, environment)
            if Path(rows['baseline']['evidence']).resolve() != Path(report['baseline']).resolve():
                raise ValueError('baseline row must name the receipt used by the comparison')
    return {'complete': True, 'playbook': contract['playbook'], 'steps': len(rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('select', help='Print the contract identity and checklist; does not write state')
    p.add_argument('--kind', required=True, choices=list(catalog()['defaults']))
    p.add_argument('--playbook', choices=list(catalog()['playbooks']))
    p = sub.add_parser('check', help='Check supplemental proof; never replaces graph gates')
    p.add_argument('--state', required=True, type=Path)
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--environment', default='', help='Fresh environment fingerprint, required for refactoring')
    args = parser.parse_args()
    try:
        result = select(args.kind, args.playbook) if args.action == 'select' else check(args.state, args.repo, args.environment)
        if args.action == 'select':
            result['checklist'] = checklist(result)
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
