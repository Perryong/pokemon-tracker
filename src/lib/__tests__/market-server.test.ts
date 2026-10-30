import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { marketMiddleware } from '../../../server/market';
import { MarketCardSchema } from '../market';

const now = Date.parse('2026-10-30T04:00:00Z');
const card = (id = 'base1-1') => ({ id, name: 'Alakazam', secret: 'never-return', pricing: {
  cardmarket: { unit: 'EUR', updated: '2026-10-29T10:00:00Z', avg: 48.3, low: 9.99, 'trend-holo': 19.66, idProduct: 273696, unknown: 500, bad: -1 },
  tcgplayer: { unit: 'USD', updated: '2026-10-29T10:00:00Z', holofoil: { marketPrice: 20, lowPrice: null, highPrice: -1, surprise: 99 } },
} });
const reply = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
async function request(middleware: ReturnType<typeof marketMiddleware>, path = '/api/market/cards/base1-1', method = 'GET') {
  const response = { statusCode: 200, setHeader: vi.fn(), end: vi.fn() };
  const next = vi.fn();
  await middleware({ url: path, method } as IncomingMessage, response as unknown as ServerResponse, next);
  return { status: response.statusCode, data: response.end.mock.calls[0] ? JSON.parse(response.end.mock.calls[0][0]) : null, response, next };
}
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(now); vi.stubGlobal('fetch', vi.fn(async () => reply(card()))); });
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

it('serves capability health without probing the provider', async () => {
  const result = await request(marketMiddleware(), '/api/market/health');
  expect(result.data).toEqual({ service: 'market-prices', schemaVersion: 1, mode: 'reference', source: 'TCGdex' });
  expect(fetch).not.toHaveBeenCalled();
});
it('returns bounded reference prices with matching identity, timestamps and original currency', async () => {
  const result = await request(marketMiddleware());
  expect(result.status).toBe(200);
  expect(MarketCardSchema.parse(result.data)).toEqual(result.data);
  expect(result.data.card).toEqual({ id: 'base1-1', name: 'Alakazam' });
  expect(result.data.fetchedAt).toBe(new Date(now).toISOString());
  expect(result.data.quotes[0]).toMatchObject({ provider: 'cardmarket', currency: 'EUR', freshness: 'current', prices: { avg: 48.3, low: 9.99, 'trend-holo': 19.66 } });
  expect(result.data.quotes[1].prices).toEqual({ marketPrice: 20 });
  expect(JSON.stringify(result.data)).not.toMatch(/secret|never-return|idProduct|surprise|unknown/);
  expect(fetch).toHaveBeenCalledWith('https://api.tcgdex.net/v2/en/cards/base1-1', expect.objectContaining({ redirect: 'error', signal: expect.any(AbortSignal) }));
  expect(result.response.setHeader).toHaveBeenCalledWith('Cache-Control', 'no-store');
});
it.each(['/api/market/cards/a%2Fb', '/api/market/cards/base1-1?url=https://evil.test', '/api/market/cards/../health', '/api/market/cards/'+ 'a'.repeat(81), '/api/market/unknown'])('rejects malformed route %s without fetch', async path => {
  expect((await request(marketMiddleware(), path)).status).toBeGreaterThanOrEqual(400);
  expect(fetch).not.toHaveBeenCalled();
});
it('rejects mutations and leaves unrelated paths alone', async () => {
  const middleware = marketMiddleware();
  expect((await request(middleware, '/api/market/health', 'POST')).status).toBe(405);
  expect((await request(middleware, '/api/cardmarket/base1-1')).next).toHaveBeenCalledOnce();
  expect(fetch).not.toHaveBeenCalled();
});
it.each([null, {}, { id: 'other', name: 'Wrong' }, { id: 'base1-1', name: '' }])('rejects invalid identity/data %j', async data => {
  vi.mocked(fetch).mockResolvedValueOnce(reply(data));
  expect((await request(marketMiddleware())).status).toBe(502);
});
it('distinguishes absent card, empty prices and unsupported currencies', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(reply({}, 404));
  expect((await request(marketMiddleware())).status).toBe(404);
  vi.mocked(fetch).mockResolvedValueOnce(reply({ id: 'base1-1', name: 'Alakazam' }));
  expect((await request(marketMiddleware())).data.quotes).toEqual([]);
  const data = card(); data.pricing.cardmarket.unit = 'GBP'; data.pricing.tcgplayer.unit = 'EUR';
  vi.mocked(fetch).mockResolvedValueOnce(reply(data));
  expect((await request(marketMiddleware())).data.quotes).toEqual([]);
});
it.each(['2026-10-31T00:00:00Z', 'garbage', '2026-02-30T00:00:00Z', '2026-10-29T10:00:00'])('labels invalid/future date %s unknown', async updated => {
  const data = card(); data.pricing.cardmarket.updated = updated;
  vi.mocked(fetch).mockResolvedValueOnce(reply(data));
  expect((await request(marketMiddleware())).data.quotes[0]).toMatchObject({ updatedAt: null, freshness: 'unknown' });
});
it('shares requests, keeps original fetch time and recomputes freshness on cache hits', async () => {
  const data = card(); data.pricing.cardmarket.updated = '2026-10-28T04:10:00Z';
  vi.mocked(fetch).mockImplementation(async () => reply(data));
  const middleware = marketMiddleware();
  const [a,b] = await Promise.all([request(middleware),request(middleware)]);
  expect(fetch).toHaveBeenCalledOnce(); expect(a.data).toEqual(b.data);
  expect(a.data.quotes[0].freshness).toBe('current');
  vi.setSystemTime(now + 20*60_000);
  const cached = await request(middleware);
  expect(cached.data.quotes[0].freshness).toBe('stale');
  expect(cached.data.fetchedAt).toBe(a.data.fetchedAt);
  expect(fetch).toHaveBeenCalledOnce();
  vi.setSystemTime(now + 3600_000);
  await request(middleware); expect(fetch).toHaveBeenCalledTimes(2);
});
it('limits upstream calls while still allowing cached results and resets the window', async () => {
  vi.mocked(fetch).mockImplementation(async url => reply(card(String(url).split('/').pop())));
  const middleware = marketMiddleware();
  for(let i=0;i<30;i++) expect((await request(middleware, `/api/market/cards/base1-${i}`)).status).toBe(200);
  expect((await request(middleware, '/api/market/cards/base1-31')).status).toBe(429);
  expect((await request(middleware, '/api/market/cards/base1-0')).status).toBe(200);
  vi.setSystemTime(now+60_000);
  expect((await request(middleware, '/api/market/cards/base1-31')).status).toBe(200);
});
it('bounds cache capacity', async () => {
  vi.mocked(fetch).mockImplementation(async url => reply(card(String(url).split('/').pop())));
  const middleware = marketMiddleware();
  for(let i=0;i<257;i++) { vi.setSystemTime(now + Math.floor(i/30)*60_000); await request(middleware, `/api/market/cards/base1-${i}`); }
  await request(middleware, '/api/market/cards/base1-0'); expect(fetch).toHaveBeenCalledTimes(258);
});
it.each([new DOMException('secret','TimeoutError'), new Error('secret'), new TypeError('redirect failed')])('sanitizes network failures', async error => {
  vi.mocked(fetch).mockRejectedValueOnce(error);
  const result = await request(marketMiddleware());
  expect(result.status).toBe(error.name === 'TimeoutError' ? 504 : 502);
  expect(JSON.stringify(result.data)).not.toContain('secret');
});
it('rejects oversized upstream responses', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(new Response('x'.repeat(1024*1024+1)));
  expect((await request(marketMiddleware())).status).toBe(502);
});
it.each(['sv03.5-199', 'swsh12.5-160'])('accepts real special-set ID %s without broadening the upstream path', async id => {
  vi.mocked(fetch).mockResolvedValueOnce(reply(card(id)));
  const result = await request(marketMiddleware(), `/api/market/cards/${id}`);
  expect(result.status).toBe(200);
  expect(result.data.card.id).toBe(id);
  expect(fetch).toHaveBeenCalledWith(`https://api.tcgdex.net/v2/en/cards/${id}`, expect.objectContaining({ redirect: 'error' }));
});
