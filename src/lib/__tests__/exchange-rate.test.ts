import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { fetchSgdRate, toSgd } from '../exchange-rate';
const today = new Date().toISOString().slice(0, 10);
beforeEach(() => { vi.stubGlobal('fetch', vi.fn()); });
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
it.each([
  { base: 'EUR', quote: 'USD', rate: 1.5, date: today },
  { base: 'EUR', quote: 'SGD', rate: -1, date: today },
  { base: 'EUR', quote: 'SGD', rate: 1.5, date: '2026-02-30' },
  { base: 'EUR', quote: 'SGD', rate: 1.5, date: '2099-01-01' },
  { base: 'EUR', quote: 'SGD', rate: 1.5, date: '2020-01-01' },
])('rejects invalid/stale FX data %j', async data => {
  vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify(data)));
  await expect(fetchSgdRate('EUR')).rejects.toThrow();
});
it('fetches and caches separate EUR and USD rates with no redirects', async () => {
  vi.mocked(fetch).mockImplementation(async url => new Response(JSON.stringify({ base: String(url).includes('/EUR/') ? 'EUR' : 'USD', quote: 'SGD', rate: String(url).includes('/EUR/') ? 1.5 : 1.3, date: today })));
  const [a,b] = await Promise.all([fetchSgdRate('EUR'), fetchSgdRate('EUR')]);
  expect(a).toEqual(b); expect(fetch).toHaveBeenCalledTimes(1);
  expect((await fetchSgdRate('USD')).rate).toBe(1.3);
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/USD/SGD'), expect.objectContaining({ redirect: 'error' }));
  await fetchSgdRate('EUR'); expect(fetch).toHaveBeenCalledTimes(2);
});
it('converts each supported currency, preserves zero and rejects unknown/nonfinite amounts', () => {
  const rates = { EUR: { rate: 1.5, expiresAt: Date.now() + 6 * 3600_000, date: today }, USD: { rate: 1.3, expiresAt: Date.now() + 6 * 3600_000, date: today } };
  expect(toSgd(10, 'EUR', rates)).toBe(15);
  expect(toSgd(10, 'USD', rates)).toBe(13);
  expect(toSgd(0, 'USD', rates)).toBe(0);
  expect(toSgd(10, 'GBP', rates)).toBeNull();
  expect(toSgd(10, 'EUR', {})).toBeNull();
  expect(toSgd(Infinity, 'USD', rates)).toBeNull();
  expect(toSgd(-1, 'USD', rates)).toBeNull();
  expect(toSgd(Number.MAX_VALUE, 'USD', rates)).toBeNull();
});
