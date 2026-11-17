"""Known-only public attribution; runtime evidence is supplied by the host adapter."""
import re

UNKNOWN = {'', 'unknown', 'undefined', 'null', 'none', 'n/a', 'auto', 'default',
           'inherit', 'session_model', 'heavy', 'standard', 'light'}


def known(value):
    return isinstance(value, str) and value.strip().lower() not in UNKNOWN


def identity(value):
    if not isinstance(value, dict) or value.get('source') not in ('runtime', 'system'):
        return {}
    if not known(value.get('model')) or value.get('ambiguous') is True:
        return {}
    return {k: value[k] for k in ('model', 'family', 'source') if known(value.get(k))}


def escape(value):
    return re.sub(r'[\r\n]+', ' ', value).replace('|', '&#124;').replace('<', '&lt;').replace('>', '&gt;')


def contributions(records):
    rows = []
    for record in records:
        model = identity(record.get('identity'))
        if model:
            row = (escape(record['role']), escape(model['model']))
            if row not in rows:
                rows.append(row)
    return rows


def pr_section(records):
    rows = contributions(records)
    if not rows:
        return ''
    return '## Agent run\n\n' + '\n'.join(f'- {role} model: {model}' for role, model in rows)


def review_row(records):
    rows = contributions(records)
    return '| Model | ' + '; '.join(f'{role}: {model}' for role, model in rows) + ' |' if rows else ''


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('pr', 'review'), required=True)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.records.read_text())
    output = pr_section(records) if args.kind == 'pr' else review_row(records)
    if output:
        print(output)
