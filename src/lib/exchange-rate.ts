import { useEffect, useState } from 'react';
import { z } from 'zod';

type Currency = 'EUR' | 'USD';
export type ExchangeRate = { rate: number; date: string; expiresAt: number };
export type SgdRates = Partial<Record<Currency, ExchangeRate>>;
const cached = new Map<Currency, { value: ExchangeRate; expires: number }>();
const pending = new Map<Currency, Promise<ExchangeRate>>();
const rateSchema = z.object({ base: z.enum(['EUR', 'USD']), quote: z.literal('SGD'), rate: z.number().finite().positive(), date: z.string().date() });

export function fetchSgdRate(currency: Currency): Promise<ExchangeRate> {
  const hit = cached.get(currency);
  if (hit && hit.expires > Date.now()) return Promise.resolve(hit.value);
  const inFlight = pending.get(currency);
  if (inFlight) return inFlight;
  const request = (async () => {
    const response = await fetch(`https://api.frankfurter.dev/v2/rate/${currency}/SGD?providers=ecb`, { signal: AbortSignal.timeout(8000), redirect: 'error' });
    if (!response.ok) throw new Error('Exchange rate unavailable');
    const data = rateSchema.parse(await response.json());
    const age = Date.now() - Date.parse(data.date);
    if (data.base !== currency || age < 0 || age > 7 * 86400_000) throw new Error('Invalid or stale exchange rate');
    const value = { rate: data.rate, date: data.date, expiresAt: Math.min(Date.now() + 6 * 3600_000, Date.parse(data.date) + 7 * 86400_000) };
    cached.set(currency, { value, expires: value.expiresAt });
    return value;
  })().finally(() => pending.delete(currency));
  pending.set(currency, request);
  return request;
}

export function useSgdExchangeRates(enabled: boolean) {
  const [rates, setRates] = useState<SgdRates>({});
  const [errors, setErrors] = useState<Partial<Record<Currency, boolean>>>({});
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    const timers: Partial<Record<Currency, ReturnType<typeof setTimeout>>> = {};
    const renew = async (currency: Currency) => {
      setRates(previous => { const next = { ...previous }; delete next[currency]; return next; });
      setErrors(previous => ({ ...previous, [currency]: false }));
      let retryAt = Date.now() + 6 * 3600_000;
      try {
        const value = await fetchSgdRate(currency);
        if (active) { setRates(previous => ({ ...previous, [currency]: value })); retryAt = value.expiresAt; }
      } catch { if (active) setErrors(previous => ({ ...previous, [currency]: true })); }
      if (active) timers[currency] = setTimeout(() => { void renew(currency); }, Math.max(1, retryAt - Date.now()));
    };
    for (const currency of ['EUR', 'USD'] as const) void renew(currency);
    return () => { active = false; Object.values(timers).forEach(clearTimeout); };

  }, [enabled]);
  return { rates, errors };
}

export function getSgdRate(currency: string, rates: SgdRates): ExchangeRate | undefined {
  const rate = currency === 'EUR' || currency === 'USD' ? rates[currency] : undefined;
  if (!rate) return undefined;
  const age = Date.now() - Date.parse(rate.date);
  return Number.isFinite(rate.rate) && rate.rate > 0 && rate.expiresAt > Date.now() && age >= 0 && age <= 7 * 86400_000 ? rate : undefined;
}
export function toSgd(value: number, currency: string, rates: SgdRates): number | null {
  const rate = getSgdRate(currency, rates)?.rate;
  const result = rate && rate > 0 ? value * rate : NaN;
  return value >= 0 && Number.isFinite(value) && Number.isFinite(result) ? result : null;
}
export const formatSgd = (value: number) => `SGD ${value.toLocaleString('en-SG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
