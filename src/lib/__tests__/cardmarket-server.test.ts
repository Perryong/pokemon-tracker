import { afterEach, expect, it, vi } from 'vitest';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { cardmarketMiddleware } from '../../../server/cardmarket';

afterEach(() => vi.unstubAllGlobals());
function response() {
  return { statusCode: 200, setHeader: vi.fn(), end: vi.fn() };
}
it('keeps credentials upstream and caches normalized prices', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ legacy_id: 'base1-1', prices: [{ source: 'CARDMARKET', locale: 'en', currency: 'EUR', variant: 'LOW', amount: 80, as_of: '2026-09-23' }] }) });
  vi.stubGlobal('fetch', fetch);
  const middleware = cardmarketMiddleware('server-only-secret');
  const req = { method: 'GET', url: '/api/cardmarket/base1-1' } as IncomingMessage;
  const res = response();
  await middleware(req, res as unknown as ServerResponse, vi.fn());
  await middleware(req, res as unknown as ServerResponse, vi.fn());
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[0][1].headers['X-Api-Key']).toBe('server-only-secret');
  expect(res.end.mock.calls[0][0]).toContain('pokemontcgapi.com');
  expect(res.end.mock.calls[0][0]).not.toContain('server-only-secret');
});
it('rejects unsafe paths without spending credits', async () => {
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
  const res = response();
  await cardmarketMiddleware('key')({ method: 'GET', url: '/api/cardmarket/x%2Fy' } as IncomingMessage, res as unknown as ServerResponse, vi.fn());
  expect(res.statusCode).toBe(400); expect(fetch).not.toHaveBeenCalled();
});
it('rejects mismatched card identities', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ legacy_id: 'base1-2', prices: [] }) }));
  const res = response();
  await cardmarketMiddleware('key')({ method: 'GET', url: '/api/cardmarket/base1-1' } as IncomingMessage, res as unknown as ServerResponse, vi.fn());
  expect(res.statusCode).toBe(502);
});
