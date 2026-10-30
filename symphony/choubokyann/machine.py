#!/usr/bin/env python3
"""Offline plan/render for the single machine slot. No GitHub or Docker calls."""
import argparse
import json
from pathlib import Path
import sys

from registry import FIELDS, select_project, validate_record

HERE = Path(__file__).resolve().parent


def render_workflow(scope, project_id='selected'):
    validate_record(scope)
    values = dict(REPO=scope['repo'], ACTOR=scope['actor'], CONTROL_LABEL=scope['control_label'],
                  CONTROL_LABEL_JSON=json.dumps(scope['control_label']),
                  QUEUE_LABEL=scope['queue_label'], CONTROL=str(scope['control_issue']),
                  SESSION=scope['session'], BRANCH=scope['branch'],
                  PROJECT_URL=f"https://github.com/users/{scope['project_owner']}/projects/{scope['project_number']}",
                  EXCLUDED=', '.join(map(str, scope['excluded_issues'])) or 'None',
                  SCOPE=scope['scope'], AUTHORITY=scope['authority_url'], ID=project_id)
    template = (HERE / 'WORKFLOW.template.md').read_text(encoding='utf-8')
    for key, value in values.items():
        template = template.replace('@@' + key + '@@', value)
    if '@@' in template:
        raise ValueError('unresolved workflow placeholder')
    return template


def plan(registry, project):
    selected = select_project(registry, project)
    scope = {key: selected[key] for key in FIELDS}
    # No caller overrides resource caps, profiles, volume names or container slot.
    return dict(selected=selected, workflow=render_workflow(scope, project))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--output', type=Path, help='write rendered workflow; otherwise print offline plan')
    args = parser.parse_args()
    try:
        result = plan(args.registry, args.project)
        if args.output:
            args.output.write_text(result['workflow'], encoding='utf-8')
        else:
            print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, OSError):
        print('Invalid registration or workflow; no runtime started.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
