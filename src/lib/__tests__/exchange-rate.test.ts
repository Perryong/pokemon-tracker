import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { toSgd } from '../exchange-rate';
const today = new Date().toISOString().slice(0, 10);
const fresh = () => ({ rate: 1.5, date: today, expiresAt: Date.now() + 3600_000 });
beforeEach(() => { vi.resetModules(); vi.stubGlobal('fetch', vi.fn()); });
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
it.each([
  { rate: -1 }, { rate: '1.5' }, { date: '2026-02-30' },
  { date: '2099-01-01' }, { date: '2020-01-01' },
  { expiresAt: 0 }, { expiresAt: 'tomorrow' },
])('rejects invalid/stale hosted FX data %j', async invalid => {
  const { fetchSgdRate } = await import('../exchange-rate');
  vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ EUR: { ...fresh(), ...invalid }, USD: fresh() })));
  await expect(fetchSgdRate('EUR')).rejects.toThrow();
});
it('shares one hosted request for both currencies and caches rates until the server expiry', async () => {
  const { fetchSgdRate } = await import('../exchange-rate');
  vi.useFakeTimers();
  vi.mocked(fetch).mockImplementation(async url => {
    if (url !== 'https://pokemon-price-api-omega.vercel.app/api/market/rates') throw new Error('Only hosted rates available');
    return new Response(JSON.stringify({ EUR: fresh(), USD: { ...fresh(), rate: 1.3 } }));
  });
  const [a,b,c] = await Promise.all([fetchSgdRate('EUR'), fetchSgdRate('EUR'), fetchSgdRate('USD')]);
  expect(a).toEqual(b); expect(a.rate).toBe(1.5); expect(c.rate).toBe(1.3);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ redirect: 'error' }));
  await fetchSgdRate('EUR'); expect(fetch).toHaveBeenCalledTimes(1);
  vi.setSystemTime(Date.now() + 3600_001);
  await fetchSgdRate('EUR'); expect(fetch).toHaveBeenCalledTimes(2);
});
it('caps a server expiry at six hours or seven days from the observation, whichever is earlier', async () => {
  const { fetchSgdRate } = await import('../exchange-rate');
  vi.useFakeTimers(); vi.setSystemTime(new Date('2026-10-31T22:00:00Z'));
  vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({
    EUR: { rate: 1.5, date: '2026-10-25', expiresAt: Date.now() + 48 * 3600_000 },
    USD: { rate: 1.3, date: '2026-10-30', expiresAt: Date.now() + 48 * 3600_000 },
  })));
  expect((await fetchSgdRate('EUR')).expiresAt).toBe(Date.parse('2026-11-01T00:00:00Z'));
  expect((await fetchSgdRate('USD')).expiresAt).toBe(Date.parse('2026-11-01T04:00:00Z'));
});
it('does not cache failed or incomplete rates and permits a later retry', async () => {
  const { fetchSgdRate } = await import('../exchange-rate');
  vi.mocked(fetch).mockResolvedValueOnce(new Response('{}', { status: 503 }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ EUR: fresh() })))
    .mockResolvedValueOnce(new Response(JSON.stringify({ EUR: fresh(), USD: fresh() })));
  await expect(fetchSgdRate('EUR')).rejects.toThrow();
  await expect(fetchSgdRate('USD')).rejects.toThrow();
  expect((await fetchSgdRate('EUR')).rate).toBe(1.5);
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
