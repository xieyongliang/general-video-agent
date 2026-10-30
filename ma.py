"""Minimal client extracted from the October 2026 video MA experiment."""
import argparse
import json
import os
from pathlib import Path
from string import Template
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent


def request(method, path, payload=None):
    base = os.environ.get('ARK_API_BASE', 'https://ark.cn-beijing.volces.com/api/v3')
    if not base.startswith('https://'):
        raise ValueError('ARK_API_BASE must use HTTPS')
    req = urllib.request.Request(
        base.rstrip('/') + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'Bearer ' + os.environ['ARK_API_KEY'],
                 'Content-Type': 'application/json'}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Do not expose backend response bodies or credentials in shared logs.
        raise RuntimeError(f'{method} failed: HTTP {error.code}') from None


def create_once(label, path, payload):
    state = ROOT / 'state'
    state.mkdir(exist_ok=True)
    result = state / (label + '.json')
    intent = state / (label + '.intent.json')
    if result.exists():
        raise RuntimeError(f'{result.name} exists; reuse its ID, do not resubmit')
    with intent.open('x') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
    # Never retry writes automatically: a timeout can hide a successful creation.
    data = request('POST', path, payload)
    result.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f'Saved {result}; ID: {data.get("id", "see saved response")}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('create-agent')
    session = commands.add_parser('create-session')
    session.add_argument('--agent-id', required=True)
    session.add_argument('--version', type=int, default=1)
    session.add_argument('--environment-id', required=True)
    session.add_argument('--reference-file-id', required=True)
    submit = commands.add_parser('submit')
    submit.add_argument('--session-id', required=True)
    for name in ['status', 'events', 'files']:
        cmd = commands.add_parser(name)
        cmd.add_argument('--session-id', required=True)
    args = parser.parse_args()
    if args.command == 'create-agent':
        body = json.loads(Template((ROOT / 'agent.template.json').read_text()).substitute(os.environ))
        body['system'] = (ROOT / 'prompts/system.txt').read_text()
        create_once('agent', '/agents', body)
    elif args.command == 'create-session':
        create_once('session', '/sessions', {
            'agent': {'id': args.agent_id, 'version': args.version},
            'environment_id': args.environment_id,
            'resources': [{'type': 'file', 'file_id': args.reference_file_id,
                           'mount_path': 'references.zip'}],
            'title': 'Handmade MA ecommerce video'})
    else:
        sid = urllib.parse.quote(args.session_id, safe='')
        if args.command == 'submit':
            create_once('submission', f'/sessions/{sid}/events', {'events': [{
                'type': 'user.message', 'content': [{'type': 'text',
                'text': (ROOT / 'prompts/task.txt').read_text()}]}]})
        elif args.command == 'status':
            data = request('GET', f'/sessions/{sid}')
            print(json.dumps({k: data.get(k) for k in ['id', 'status', 'usage', 'stats']}, indent=2))
        else:
            items, cursor, seen = [], None, set()
            while True:
                if args.command == 'events':
                    params = {'limit': 100, 'order': 'asc'}
                    if cursor:
                        params['page'] = cursor
                    path = f'/sessions/{sid}/events?' + urllib.parse.urlencode(params)
                else:
                    params = {'scope_id': args.session_id, 'purpose': 'agent'}
                    if cursor:
                        params['after'] = cursor
                    path = '/files?' + urllib.parse.urlencode(params)
                data = request('GET', path)
                batch = data.get('data') or []
                items.extend(batch)
                cursor = (data.get('next_page') if args.command == 'events' else
                          batch[-1]['id'] if data.get('has_more') and batch else None)
                if not cursor:
                    break
                if cursor in seen:
                    raise RuntimeError('Repeated pagination cursor; collection incomplete')
                seen.add(cursor)
            dest = ROOT / 'state'
            dest.mkdir(exist_ok=True)
            target = dest / (args.command + '.json')
            target.write_text(json.dumps(items, ensure_ascii=False, indent=2))
            print(f'Saved {len(items)} records to {target}')


if __name__ == '__main__':
    main()
