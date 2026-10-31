"""Uninstalled host-side validation core; no network transport or receipt issuer.

Policy, state and transport must be trusted and inaccessible to model writes.
This library does not authenticate shared native children or interpret review prose.
"""
from contextlib import contextmanager
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import stat
import tempfile


class BrokerError(ValueError):
    """Public-safe refusal; never includes remote output or supplied values."""


REPO = 'Perryong/pokemon-tracker'
BRANCH = 'feature/sales-agent'
ISSUES = {8, 9, *range(11, 22), 27}
MAX_JSON = 262144
MAX_RECORDS = 256
SAFE = re.compile(r'[a-z0-9][a-z0-9-]{0,95}\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')
EVIDENCE = {'authority_digest', 'claim_digest', 'dependency_digest',
            'review_digest', 'checks_digest'}


def require(condition):
    if not condition:
        raise BrokerError('Invalid or unauthorized broker evidence')


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def positive(value):
    return type(value) is int and 0 < value < 1000000000


def canonical(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise BrokerError('Invalid JSON evidence') from exc
    require(len(data) <= MAX_JSON)
    return data


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value)
        value[key] = item
    return value


class Broker:
    def __init__(self, policy, state_dir, transport):
        require(isinstance(policy, dict))
        required = {'project', 'repo', 'selected_issues', 'integration_branch',
                    'parent_session', 'receipts'}
        require(required <= set(policy) <= required | {'merge_enabled'})
        require(policy['project'] == 'pokemon' and policy['repo'] == REPO
                and policy['integration_branch'] == BRANCH)
        selected = policy['selected_issues']
        require(isinstance(selected, list) and bool(selected)
                and all(type(n) is int and n in ISSUES for n in selected)
                and len(selected) == len(set(selected)))
        require(matches(SAFE, policy['parent_session']) and isinstance(policy['receipts'], dict))
        canonical(policy)
        self.policy = copy.deepcopy(policy)
        self.root = Path(state_dir).absolute()
        self.transport = transport
        # Reject symlink ancestors as well as the state directory itself.
        require(all(not path.is_symlink() for path in (self.root, *self.root.parents)))
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.root.stat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid())
        os.chmod(self.root, 0o700)

    def request(self, value):
        require(isinstance(value, dict) and set(value) == {
            'version', 'request_id', 'project', 'operation', 'arguments', 'approval_id'})
        require(type(value['version']) is int and value['version'] == 1)
        require(matches(SAFE, value['request_id']) and value['project'] == self.policy['project'])
        operation, args = value['operation'], value['arguments']
        require(isinstance(operation, str) and isinstance(args, dict))
        shapes = {
            'snapshot': {'issue'}, 'comment': {'issue', 'body'},
            'create_pr': {'issue', 'base', 'head', 'head_sha', 'base_sha', 'title', 'body'},
            'merge': {'issue', 'pr', 'base', 'head_sha', 'base_sha'},
        }
        require(operation in shapes and set(args) == shapes[operation])
        require(type(args['issue']) is int and args['issue'] in self.policy['selected_issues'])
        approval = value['approval_id']
        require(approval is None or matches(SAFE, approval))
        if operation == 'snapshot':
            require(approval is None)
        if operation in {'create_pr', 'merge'}:
            require(args['base'] == BRANCH and matches(SHA, args['head_sha'])
                    and matches(SHA, args['base_sha']))
        if operation == 'merge':
            require(positive(args['pr']))
        if operation == 'create_pr':
            head = args['head']
            require(isinstance(head, str) and 1 <= len(head) <= 200
                    and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*', head) is not None
                    and '..' not in head and '//' not in head and not head.endswith(('/', '.'))
                    and all(not part.startswith('.') and not part.endswith(('.', '.lock'))
                            for part in head.split('/')))
            require(head != 'main' and head != BRANCH)
            require(isinstance(args['title'], str) and 1 <= len(args['title']) <= 200
                    and all(ord(c) >= 32 for c in args['title']))
        if 'body' in args:
            require(isinstance(args['body'], str) and 1 <= len(args['body']) <= 32768
                    and '\x00' not in args['body'])
        canonical(value)
        return copy.deepcopy(value)

    def snapshot(self, issue):
        try:
            raw = self.transport.snapshot(REPO, issue)
        except Exception as exc:
            raise BrokerError('Live evidence unavailable') from exc
        return self.validate_snapshot(raw, issue)

    def validate_snapshot(self, raw, issue):
        require(isinstance(raw, dict))
        canonical(raw)
        required = {'repo', 'visibility', 'issue', 'pr'} | EVIDENCE
        require(required <= set(raw) and raw['repo'] == REPO and raw['visibility'] == 'public'
                and type(raw['issue']) is int and raw['issue'] == issue)
        require(all(matches(HEX, raw[key]) for key in EVIDENCE))
        pr = raw['pr']
        require(isinstance(pr, dict) and set(pr) == {'number', 'base', 'base_sha', 'head_sha'})
        require(positive(pr['number']) and pr['base'] == BRANCH
                and matches(SHA, pr['base_sha']) and matches(SHA, pr['head_sha']))
        return raw, {key: copy.deepcopy(raw[key]) for key in required}

    def authorize(self, request, snapshot):
        receipt = self.policy['receipts'].get(request['approval_id'])
        require(isinstance(receipt, dict) and set(receipt) == {
            'request_sha256', 'snapshot_sha256', 'parent_session'})
        unsigned = dict(request, approval_id=None)
        require(receipt['parent_session'] == self.policy['parent_session']
                and receipt['request_sha256'] == digest(unsigned)
                and receipt['snapshot_sha256'] == digest(snapshot))
        args = request['arguments']
        if request['operation'] in {'merge', 'create_pr'}:
            pr = snapshot['pr']
            require(args['base'] == pr['base'] and args['base_sha'] == pr['base_sha']
                    and args['head_sha'] == pr['head_sha'])
            if request['operation'] == 'merge':
                require(args['pr'] == pr['number'])

    @contextmanager
    def lock(self):
        path = self.root / 'broker.lock'
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            raise BrokerError('Broker locked; reconcile before retrying') from exc
        try:
            os.close(fd)
            yield
        finally:
            path.unlink()

    def read(self, path):
        try:
            require(not path.is_symlink())
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'rb') as stream:
                info = os.fstat(stream.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                        and not info.st_mode & 0o077 and info.st_size <= MAX_JSON)
                raw = stream.read(MAX_JSON + 1)
            require(len(raw) <= MAX_JSON)
            value = json.loads(raw, object_pairs_hook=unique)
            require(isinstance(value, dict) and set(value) == {
                'version', 'request', 'request_sha256', 'status', 'result'})
            request = self.request(value['request'])
            require(type(value['version']) is int and value['version'] == 1
                    and value['request_sha256'] == digest(request)
                    and path.name == request['request_id'] + '.json'
                    and value['status'] in {'running', 'completed', 'unknown'})
            result = value['result']
            if value['status'] == 'running':
                require(result is None)
            else:
                expected = {'request_id', 'status'}
                if value['status'] == 'completed':
                    expected.add('snapshot' if request['operation'] == 'snapshot' else 'number')
                require(isinstance(result, dict) and set(result) == expected
                        and result['request_id'] == request['request_id']
                        and result['status'] == value['status'])
                if 'number' in result:
                    require(positive(result['number']))
                if 'snapshot' in result:
                    raw_snapshot, projected = self.validate_snapshot(result['snapshot'], request['arguments']['issue'])
                    require(raw_snapshot == projected)
            return value
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            raise BrokerError('Invalid durable evidence; reconcile before retrying') from exc

    def persist(self, record):
        path = self.root / (record['request']['request_id'] + '.json')
        require(not path.is_symlink())
        fd, temporary = tempfile.mkstemp(prefix='.broker-', dir=self.root)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(canonical(record))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory = os.open(self.root, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def write(self, request, snapshot):
        self.authorize(request, snapshot)
        record = dict(version=1, request=request, request_sha256=digest(request), status='running', result=None)
        self.persist(record)
        result = {'request_id': request['request_id'], 'status': 'unknown'}
        try:
            remote = self.transport.perform(request['operation'], REPO, request['arguments'])
            require(isinstance(remote, dict) and positive(remote.get('number')))
            result = dict(result, status='completed', number=remote['number'])
        except Exception:
            # Includes malformed remote output: a write may already have happened.
            pass
        record.update(status=result['status'], result=result)
        self.persist(record)
        return result

    def execute(self, value):
        request = self.request(value)
        with self.lock():
            paths = list(itertools.islice(self.root.glob('*.json'), MAX_RECORDS + 1))
            require(len(paths) <= MAX_RECORDS)
            records = [self.read(path) for path in paths]
            prior = next((r for r in records if r['request']['request_id'] == request['request_id']), None)
            if prior is not None:
                require(prior['request'] == request)
                if prior['status'] == 'running':
                    prior.update(status='unknown', result={'request_id': request['request_id'], 'status': 'unknown'})
                    self.persist(prior)
                return copy.deepcopy(prior['result'])
            require(len(records) < MAX_RECORDS)
            operation, args = request['operation'], request['arguments']
            if operation != 'snapshot':
                require(not any(r['status'] in {'running', 'unknown'} for r in records))
            if operation == 'merge':
                require(self.policy.get('merge_enabled') is True)
                guard = getattr(self.transport, 'integration_guard', None)
                require(callable(guard))
                try:
                    with guard(REPO, BRANCH, args['base_sha']) as acquired:
                        require(acquired is True)
                        raw, _ = self.snapshot(args['issue'])
                        return self.write(request, raw)
                except BrokerError:
                    raise
                except Exception as exc:
                    raise BrokerError('Integration guard unavailable; reconcile evidence') from exc
                # A guard may suppress a refusal or interruption. Never let a
                # merge reach the generic write path after leaving its guard.
                raise BrokerError('Integration guard ended without a verified result')
            raw, projected = self.snapshot(args['issue'])
            if operation != 'snapshot':
                return self.write(request, raw)
            result = {'request_id': request['request_id'], 'status': 'completed', 'snapshot': projected}
            self.persist(dict(version=1, request=request, request_sha256=digest(request), status='completed', result=result))
            return result
