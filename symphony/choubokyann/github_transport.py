"""Private trusted-host HTTPS client for the fixed public evidence reader.

Not a model tool, broker mutation transport, receipt issuer or runtime boundary.
Only the trusted host may construct this object or access its credential.
"""
import http.client
import json
import re
import ssl

from github_evidence import (COMMENTS_QUERY, GRAPHQL, HEADERS, MAX_PAGES,
                             MAX_RESPONSE, ROOT, THREADS_QUERY)


_NUMBER = r'[1-9][0-9]{0,8}'
_SHA = r'[0-9a-f]{40}'
_SINGLE = re.compile(r'/(?:issues|pulls)/' + _NUMBER + r'\Z')
_PAGED = re.compile(
    r'(?:/issues/' + _NUMBER + r'/(?:comments|timeline|dependencies/blocked_by)'
    r'|/pulls/' + _NUMBER + r'/reviews'
    r'|/commits/' + _SHA + r'/(?:check-runs|statuses))'
    r'\?per_page=100&page=([1-9][0-9]?)\Z')
_TOKEN = re.compile(r'[A-Za-z0-9_-]{1,512}\Z')


def _require(condition):
    if not condition:
        raise ValueError('Public GitHub transport unavailable') from None


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_):
    raise ValueError('Public GitHub transport unavailable') from None


def _number(value):
    return type(value) is int and 0 < value < 1000000000


def _cursor(value, nullable=False):
    return (nullable and value is None) or (
        type(value) is str and 0 < len(value) <= 512)


class FixedGitHubHTTP:
    """Credential-bearing host dependency, intentionally not publicly generic."""

    def __init__(self, token):
        _require(type(token) is str and _TOKEN.fullmatch(token) is not None)
        self._token = token
        self._threads = set()

    def _validate(self, method, url, headers, body):
        _require(type(method) is str and type(url) is str
                 and type(headers) is dict and headers == HEADERS)
        if method == 'GET':
            _require(body is None and url.startswith(ROOT))
            path = url[len(ROOT):]
            paged = _PAGED.fullmatch(path)
            _require(path == '' or _SINGLE.fullmatch(path) is not None
                     or (paged is not None and int(paged[1]) <= MAX_PAGES))
            return '/repos/Perryong/pokemon-tracker' + path, None
        _require(method == 'POST' and url == GRAPHQL and type(body) is bytes
                 and 0 < len(body) <= 8192)
        value = json.loads(body, object_pairs_hook=_unique, parse_constant=_constant)
        _require(type(value) is dict and set(value) == {'query', 'variables'})
        query, variables = value['query'], value['variables']
        _require(type(query) is str and type(variables) is dict)
        if query == THREADS_QUERY:
            _require(set(variables) == {'number', 'cursor'}
                     and _number(variables['number'])
                     and _cursor(variables['cursor'], nullable=True))
        else:
            _require(query == COMMENTS_QUERY and set(variables) == {'id', 'cursor'}
                     and type(variables['id']) is str and variables['id'] in self._threads
                     and _cursor(variables['cursor']))
        return '/graphql', value

    def _observe(self, query, payload):
        if query is None or query['query'] != THREADS_QUERY:
            return
        value = json.loads(payload, object_pairs_hook=_unique, parse_constant=_constant)
        # Semantic completeness remains the evidence reader's responsibility.
        # Only IDs inside a successful fixed-repository PR query enter node scope.
        found = set()
        if type(value) is dict and not value.get('errors'):
            current = value
            for key in ('data', 'repository', 'pullRequest', 'reviewThreads'):
                current = current.get(key) if type(current) is dict else None
            nodes = current.get('nodes') if type(current) is dict else None
            if type(nodes) is list and len(nodes) <= 100:
                for node in nodes:
                    if type(node) is dict and _cursor(node.get('id')):
                        found.add(node['id'])
        prior = set() if query['variables']['cursor'] is None else self._threads
        _require(len(prior | found) <= MAX_PAGES * 100)
        self._threads = prior | found

    def request(self, method, url, headers, body=None):
        connection = None
        try:
            path, query = self._validate(method, url, headers, body)
            outbound = dict(HEADERS)
            outbound['Authorization'] = 'Bearer ' + self._token
            if body is not None:
                outbound['Content-Type'] = 'application/json'
            # Direct HTTPSConnection uses no proxy environment or redirect logic.
            connection = http.client.HTTPSConnection(
                'api.github.com', timeout=15, context=ssl.create_default_context())
            connection.request(method, path, body=body, headers=outbound)
            response = connection.getresponse()
            _require(response.status == 200)
            returned = {}
            for key, value in response.getheaders():
                _require(type(key) is str and type(value) is str)
                if key.lower() == 'content-length':
                    _require(re.fullmatch(r'[0-9]{1,10}', value) is not None
                             and int(value) <= MAX_RESPONSE)
                if key.lower() == 'link':
                    _require('Link' not in returned and len(value) <= 8192)
                    returned['Link'] = value
            payload = response.read(MAX_RESPONSE + 1)
            _require(type(payload) is bytes and len(payload) <= MAX_RESPONSE)
            self._observe(query, payload)
            return {'status': 200, 'headers': returned, 'body': payload}
        except Exception:
            raise ValueError('Public GitHub transport unavailable') from None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
