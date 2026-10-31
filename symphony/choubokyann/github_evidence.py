"""Fixed public GitHub evidence acquisition for a trusted, installed host broker.

The injected HTTP client's request(method, url, headers, body=None) must disable
redirects, bound reads to MAX_RESPONSE bytes and return status/headers/body(bytes).
Only that host-owned client holds authentication; this module receives no token.
No caller supplies a URL, query, repository override, field list or HTTP method.
Readable evidence is not an authorization decision or an authenticated receipt.
"""
import copy
from datetime import datetime
import json
import re


REPO = 'Perryong/pokemon-tracker'
ROOT = 'https://api.github.com/repos/' + REPO
GRAPHQL = 'https://api.github.com/graphql'
SELECTABLE = {8, 9, *range(11, 22), 27}
MAX_RESPONSE = 2 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_PAGES = 20
MAX_REQUESTS = 256
SHA = re.compile(r'[0-9a-f]{40}\Z')
HEADERS = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
THREADS_QUERY = '''query($number:Int!,$cursor:String){
  repository(owner:"Perryong",name:"pokemon-tracker") {
    pullRequest(number:$number) { reviewThreads(first:100,after:$cursor) {
      nodes { id isResolved isOutdated path line
        comments(first:100) { nodes { id body createdAt updatedAt author { login } }
          pageInfo { hasNextPage endCursor } } }
      pageInfo { hasNextPage endCursor } } } } }'''
COMMENTS_QUERY = '''query($id:ID!,$cursor:String!){
  node(id:$id) { ... on PullRequestReviewThread {
    comments(first:100,after:$cursor) {
      nodes { id body createdAt updatedAt author { login } }
      pageInfo { hasNextPage endCursor } } } } }'''


class EvidenceError(ValueError):
    """A public-safe, incomplete-evidence refusal."""


def require(condition):
    if not condition:
        raise EvidenceError('Complete public evidence unavailable')


def number(value):
    return type(value) is int and 0 < value < 1000000000


def database_id(value):
    return type(value) is int and value > 0


def timestamp(value, nullable=False):
    if nullable and value is None:
        return
    require(type(value) is str and len(value) <= 64
            and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
                             r'(?:\.[0-9]+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])', value))
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise EvidenceError('Complete public evidence unavailable') from None
    require(parsed.tzinfo is not None)


def identity(raw, key):
    require(key in raw)
    actor = raw[key]
    if actor is None:
        # Deleted accounts remain explicitly unattributed, never an owner grant.
        return None
    require(isinstance(actor, dict) and type(actor.get('login')) is str
            and bool(actor['login'].strip()))
    return {'login': actor['login']}


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def reject_constant(_):
    raise EvidenceError('Complete public evidence unavailable')


def fields(raw, names):
    require(isinstance(raw, dict))
    result = {}
    for name in names:
        if name in raw:
            value = raw[name]
            require(value is None or type(value) in (str, bool, int))
            result[name] = value
    for name in ('user', 'actor', 'author', 'assignee'):
        if raw.get(name) is not None:
            require(isinstance(raw[name], dict))
            result[name] = fields(raw[name], ('login',))
    return result


def required_fields(raw, schema):
    require(isinstance(raw, dict))
    for name, types in schema.items():
        require(name in raw and type(raw[name]) in types)


def comment(raw):
    required_fields(raw, {'id': (int,), 'body': (str,), 'created_at': (str,), 'updated_at': (str,)})
    require(database_id(raw['id']))
    timestamp(raw['created_at'])
    timestamp(raw['updated_at'])
    actor = identity(raw, 'user')
    result = fields(raw, ('id', 'body', 'created_at', 'updated_at', 'html_url', 'author_association'))
    result['user'] = actor
    return result


class FixedEvidenceTransport:
    def __init__(self, http, selected_issues):
        require(type(selected_issues) is list and bool(selected_issues)
                and all(type(n) is int and n in SELECTABLE for n in selected_issues)
                and len(set(selected_issues)) == len(selected_issues))
        self.http = http
        self.selected = frozenset(selected_issues)

    def _call(self, url, query=None, variables=None):
        self.requests += 1
        require(self.requests <= MAX_REQUESTS)
        require(url.startswith(ROOT + '/') or url == ROOT or url == GRAPHQL)
        body = None if query is None else json.dumps({'query': query, 'variables': variables}).encode()
        try:
            response = self.http.request('GET' if body is None else 'POST', url,
                                         dict(HEADERS), body)
            require(isinstance(response, dict) and response.get('status') == 200)
            headers = response.get('headers')
            require(isinstance(headers, dict))
            payload = response.get('body')
            require(type(payload) is bytes and len(payload) <= MAX_RESPONSE)
            self.total += len(payload)
            require(self.total <= MAX_TOTAL)
            result = json.loads(payload, object_pairs_hook=object_pairs,
                                parse_constant=reject_constant)
            return result, headers
        except Exception:
            raise EvidenceError('Complete public evidence unavailable') from None

    def _get(self, path):
        return self._call(ROOT + path)[0]

    def _pages(self, path, key=None):
        result, identifiers = [], set()
        expected_total = None
        for page in range(1, MAX_PAGES + 1):
            value, headers = self._call(ROOT + path + '?per_page=100&page=' + str(page))
            if key is not None:
                require(isinstance(value, dict) and type(value.get('total_count')) is int
                        and value['total_count'] >= 0 and isinstance(value.get(key), list))
                if expected_total is None:
                    expected_total = value['total_count']
                require(expected_total == value['total_count'])
                value = value[key]
            require(isinstance(value, list) and len(value) <= 100)
            for item in value:
                require(isinstance(item, dict))
                ident = item.get('id')
                if ident is not None:
                    require(type(ident) in (str, int) and ident not in identifiers)
                    identifiers.add(ident)
                result.append(item)
            # Derive the next URL ourselves; never follow server-supplied URLs.
            link = next((v for k, v in headers.items() if k.lower() == 'link'), '')
            require(isinstance(link, str))
            has_next = 'rel="next"' in link
            if has_next:
                expected = '<' + ROOT + path + '?per_page=100&page=' + str(page + 1) + '>; rel="next"'
                require(expected in link)
            if len(value) < 100 and not has_next:
                require(expected_total is None or len(result) == expected_total)
                return result
        raise EvidenceError('Complete public evidence unavailable')

    def _public(self):
        repo = self._get('')
        require(isinstance(repo, dict) and repo.get('full_name') == REPO
                and repo.get('private') is False and repo.get('visibility') == 'public')

    def _local_issue(self, raw):
        require(isinstance(raw, dict) and number(raw.get('number')))
        n = raw['number']
        allowed = {'https://github.com/' + REPO + '/issues/' + str(n),
                   'https://github.com/' + REPO + '/pull/' + str(n)}
        require(raw.get('html_url') in allowed)
        repository = raw.get('repository')
        if repository is not None:
            require(isinstance(repository, dict) and repository.get('full_name') == REPO
                    and repository.get('private') is False)
        return n

    def _timeline(self, records):
        result, prs = [], set()
        for raw in records:
            event = fields(raw, ('id', 'event', 'created_at', 'commit_id', 'body', 'state',
                                 'dismissal_message', 'lock_reason'))
            for key, names in (('rename', ('from', 'to')), ('label', ('id', 'name')),
                               ('milestone', ('id', 'number', 'title')),
                               ('dismissed_review', ('review_id', 'state', 'dismissal_message'))):
                if raw.get(key) is not None:
                    event[key] = fields(raw[key], names)
            # Nested references may name private repositories. Only an independently
            # scoped same-repository reference is projected or used for acquisition.
            source = raw.get('source')
            if isinstance(source, dict) and isinstance(source.get('issue'), dict):
                try:
                    n = self._local_issue(source['issue'])
                except EvidenceError:
                    n = None
                if n is not None:
                    event['source_issue'] = n
                    if isinstance(source['issue'].get('pull_request'), dict):
                        prs.add(n)
            result.append(event)
        return result, prs

    def _bundle(self, n):
        raw = self._get('/issues/' + str(n))
        require(self._local_issue(raw) == n)
        required_fields(raw, {'number': (int,), 'title': (str,), 'body': (str, type(None)),
                              'state': (str,), 'html_url': (str,)})
        require(raw['state'] in {'open', 'closed'})
        record = fields(raw, ('number', 'title', 'body', 'state', 'state_reason',
                              'created_at', 'updated_at', 'closed_at', 'html_url'))
        for key, names in (('labels', ('id', 'name')), ('assignees', ('login',))):
            require(isinstance(raw.get(key), list))
            record[key] = [fields(item, names) for item in raw[key]]
        comments = [comment(item)
                    for item in self._pages('/issues/' + str(n) + '/comments')]
        timeline, prs = self._timeline(self._pages('/issues/' + str(n) + '/timeline'))
        if isinstance(raw.get('pull_request'), dict):
            prs.add(n)
        return {'issue': n, 'issue_record': record, 'comments': comments, 'timeline': timeline}, prs

    def _graphql(self, query, variables):
        result, _ = self._call(GRAPHQL, query, variables)
        require(isinstance(result, dict) and not result.get('errors')
                and isinstance(result.get('data'), dict))
        return result['data']

    def _connection(self, value):
        require(isinstance(value, dict) and isinstance(value.get('nodes'), list)
                and len(value['nodes']) <= 100 and isinstance(value.get('pageInfo'), dict))
        info = value['pageInfo']
        require('endCursor' in info and type(info.get('hasNextPage')) is bool)
        cursor = info.get('endCursor')
        require(not info['hasNextPage'] or (isinstance(cursor, str) and 0 < len(cursor) <= 512))
        return value['nodes'], cursor if info['hasNextPage'] else None

    def _thread_comments(self, thread):
        nodes, cursor = self._connection(thread.get('comments'))
        comments = list(nodes)
        cursors = set()
        for _ in range(MAX_PAGES):
            if cursor is None:
                ids = [item.get('id') for item in comments if isinstance(item, dict)]
                require(len(ids) == len(comments) and all(isinstance(n, str) for n in ids)
                        and len(ids) == len(set(ids)))
                for item in comments:
                    required_fields(item, {'id': (str,), 'body': (str,),
                                           'createdAt': (str,), 'updatedAt': (str,)})
                    require(0 < len(item['id']) <= 512 and bool(item['id'].strip()))
                    timestamp(item['createdAt'])
                    timestamp(item['updatedAt'])
                result = []
                for item in comments:
                    actor = identity(item, 'author')
                    projected = fields(item, ('id', 'body', 'createdAt', 'updatedAt'))
                    projected['author'] = actor
                    result.append(projected)
                return result
            require(cursor not in cursors)
            cursors.add(cursor)
            data = self._graphql(COMMENTS_QUERY, {'id': thread['id'], 'cursor': cursor})
            require(isinstance(data.get('node'), dict))
            nodes, cursor = self._connection(data['node'].get('comments'))
            comments.extend(nodes)
        raise EvidenceError('Complete public evidence unavailable')

    def _threads(self, n):
        threads, cursor, cursors, ids = [], None, set(), set()
        for _ in range(MAX_PAGES):
            data = self._graphql(THREADS_QUERY, {'number': n, 'cursor': cursor})
            require(isinstance(data.get('repository'), dict)
                    and isinstance(data['repository'].get('pullRequest'), dict))
            nodes, cursor = self._connection(data['repository']['pullRequest'].get('reviewThreads'))
            for raw in nodes:
                require(isinstance(raw, dict) and isinstance(raw.get('id'), str)
                        and 0 < len(raw['id']) <= 512 and raw['id'] not in ids
                        and type(raw.get('isResolved')) is bool)
                ids.add(raw['id'])
                thread = fields(raw, ('id', 'isResolved', 'isOutdated', 'path', 'line'))
                thread['comments'] = self._thread_comments(raw)
                threads.append(thread)
            if cursor is None:
                return threads
            require(cursor not in cursors)
            cursors.add(cursor)
        raise EvidenceError('Complete public evidence unavailable')

    def _revision(self, raw, n):
        require(isinstance(raw, dict) and raw.get('number') == n)
        base, head = raw.get('base'), raw.get('head')
        require(isinstance(base, dict) and isinstance(head, dict)
                and isinstance(base.get('repo'), dict) and base['repo'].get('full_name') == REPO)
        require(all(isinstance(value, str) and SHA.fullmatch(value)
                    for value in (base.get('sha'), head.get('sha'))))
        require(isinstance(base.get('ref'), str) and isinstance(head.get('ref'), str))
        return dict(number=n, base=base['ref'], base_sha=base['sha'], head_sha=head['sha'])

    def _pr(self, n):
        raw = self._get('/pulls/' + str(n))
        revision = self._revision(raw, n)
        required_fields(raw, {'number': (int,), 'title': (str,), 'body': (str, type(None)), 'state': (str,)})
        require(raw['state'] in {'open', 'closed'})
        result = dict(revision, **fields(raw, ('title', 'body', 'state', 'draft', 'merged',
                                              'mergeable', 'mergeable_state', 'updated_at')))
        conversation, _ = self._bundle(n)
        result.update({key: conversation[key] for key in ('issue_record', 'comments', 'timeline')})
        reviews = self._pages('/pulls/' + str(n) + '/reviews')
        result['reviews'] = []
        for review in reviews:
            required_fields(review, {'id': (int,), 'body': (str,), 'state': (str,),
                                     'submitted_at': (str, type(None))})
            require(database_id(review['id']))
            require(review['state'] in {'APPROVED', 'CHANGES_REQUESTED', 'COMMENTED', 'DISMISSED', 'PENDING'})
            timestamp(review['submitted_at'], nullable=review['state'] == 'PENDING')
            actor = identity(review, 'user')
            projected = fields(review, ('id', 'body', 'state', 'submitted_at', 'commit_id',
                                         'author_association'))
            projected['user'] = actor
            result['reviews'].append(projected)
        result['review_threads'] = self._threads(n)
        commit = '/commits/' + revision['head_sha']
        checks = self._pages(commit + '/check-runs', 'check_runs')
        for check in checks:
            required_fields(check, {'id': (int,), 'name': (str,), 'status': (str,),
                                    'conclusion': (str, type(None)), 'head_sha': (str,)})
            require(database_id(check['id']))
            require(check['head_sha'] == revision['head_sha']
                    and check['status'] in {'queued', 'in_progress', 'completed', 'waiting', 'requested', 'pending'}
                    and check['conclusion'] in {None, 'success', 'failure', 'neutral', 'cancelled',
                                                'skipped', 'timed_out', 'action_required', 'stale', 'startup_failure'})
        result['checks'] = [fields(item, ('id', 'name', 'status', 'conclusion', 'head_sha',
                                        'started_at', 'completed_at')) for item in checks]
        statuses = self._pages(commit + '/statuses')
        for status in statuses:
            required_fields(status, {'id': (int,), 'state': (str,), 'context': (str,)})
            require(database_id(status['id']) and status['state'] in {'error', 'failure', 'pending', 'success'})
        result['statuses'] = [fields(item, ('id', 'state', 'context', 'description', 'created_at',
                                          'updated_at', 'sha')) for item in statuses]
        require(self._revision(self._get('/pulls/' + str(n)), n) == revision)
        return result

    def snapshot(self, repo, issue):
        require(repo == REPO and type(issue) is int and issue in self.selected)
        self.requests, self.total = 0, 0
        try:
            self._public()
            result, prs = self._bundle(issue)
            result.update(repo=REPO, visibility='public')
            dependencies, bundles, active, complete = [], {issue: result}, set(), set()
            def visit(n):
                require(n not in active)
                if n in complete:
                    return
                active.add(n)
                references = self._pages('/issues/' + str(n) + '/dependencies/blocked_by')
                edges = [self._local_issue(reference) for reference in references]
                require(len(edges) == len(set(edges)))
                bundles[n]['blocked_by'] = edges
                for dependency in edges:
                    require(dependency not in active)
                    if dependency not in bundles:
                        require(len(bundles) < 64)
                        bundle, linked = self._bundle(dependency)
                        bundles[dependency] = bundle
                        dependencies.append(bundle)
                        prs.update(linked)
                    visit(dependency)
                active.remove(n)
                complete.add(n)
            visit(issue)
            result['dependencies'] = dependencies
            result['pull_requests'] = [self._pr(n) for n in sorted(prs)]
            self._public()
            require(len(json.dumps(result, allow_nan=False).encode()) <= MAX_TOTAL)
            return copy.deepcopy(result)
        except Exception:
            raise EvidenceError('Complete public evidence unavailable') from None
