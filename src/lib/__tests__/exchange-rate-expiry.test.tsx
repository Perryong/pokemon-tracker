import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook } from '@testing-library/react';
import { useSgdExchangeRates, toSgd, getSgdRate } from '../exchange-rate';
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });
it('renews mounted rates after six hours and removes amounts if renewal fails', async () => {
  vi.useFakeTimers(); vi.setSystemTime(new Date('2026-10-30T00:00:00Z'));
  vi.stubGlobal('fetch', vi.fn(async url => new Response(JSON.stringify({ base: String(url).includes('/EUR/') ? 'EUR' : 'USD', quote: 'SGD', rate: 1.5, date: '2026-10-29' }))));
  const { result } = renderHook(() => useSgdExchangeRates(true));
  await act(async () => { await vi.advanceTimersByTimeAsync(1); });
  expect(toSgd(10, 'EUR', result.current.rates)).toBe(15);
  const previous = result.current.rates;
  vi.mocked(fetch).mockRejectedValue(new Error('offline'));
  await act(async () => { await vi.advanceTimersByTimeAsync(6 * 3600_000); });
  expect(fetch).toHaveBeenCalledTimes(4);
  expect(result.current.rates).toEqual({});
  expect(result.current.errors).toEqual({ EUR: true, USD: true });
  expect(toSgd(10, 'EUR', previous)).toBeNull();
  expect(getSgdRate('EUR', previous)).toBeUndefined();
  vi.mocked(fetch).mockImplementation(async url => new Response(JSON.stringify({ base: String(url).includes('/EUR/') ? 'EUR' : 'USD', quote: 'SGD', rate: 1.6, date: '2026-10-30' })));
  await act(async () => { await vi.advanceTimersByTimeAsync(6 * 3600_000); });
  expect(toSgd(10, 'EUR', result.current.rates)).toBe(16);
  expect(result.current.errors.EUR).toBe(false);
});
it('blocks rate dates beyond seven days even if a retained record claims a later expiry', () => {
  vi.useFakeTimers(); vi.setSystemTime(new Date('2026-11-07T00:00:00Z'));
  const rates = { EUR: { rate: 1.5, date: '2026-10-29', expiresAt: Date.now() + 3600_000 } };
  expect(toSgd(10, 'EUR', rates)).toBeNull();
  expect(getSgdRate('EUR', rates)).toBeUndefined();
});
