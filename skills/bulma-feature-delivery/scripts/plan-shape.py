#!/usr/bin/env python3
"""Choose bounded planning and structural-review depth from known task facts."""
import argparse
import json


def choose(risk, files, units, cross_contract=False, structural=False, uncertain=False):
    compact = risk != 'elevated' and files <= 3 and units == 1 and not cross_contract and not uncertain
    deep = risk == 'elevated' or structural or cross_contract or files > 6
    return {'plan_mode': 'compact' if compact else 'detailed',
            'quality_mode': 'deep' if deep else 'focused',
            'discovery_passes': 1, 'expansion_requires': 'named unresolved implementation decision'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--risk', choices=('low', 'normal', 'elevated'), required=True)
    parser.add_argument('--files', type=int, required=True)
    parser.add_argument('--units', type=int, required=True)
    parser.add_argument('--cross-contract', action='store_true')
    parser.add_argument('--structural', action='store_true')
    parser.add_argument('--uncertain', action='store_true')
    args = parser.parse_args()
    if args.files < 0 or args.units < 1:
        parser.error('files must be nonnegative and units positive')
    print(json.dumps(choose(args.risk, args.files, args.units, args.cross_contract,
                            args.structural, args.uncertain)))


if __name__ == '__main__':
    main()
