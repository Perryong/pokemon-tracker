import { useEffect, useState } from 'react';
import { z } from 'zod';

type Currency = 'EUR' | 'USD';
export type ExchangeRate = { rate: number; date: string };
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
    const value = { rate: data.rate, date: data.date };
    cached.set(currency, { value, expires: Math.min(Date.now() + 6 * 3600_000, Date.parse(data.date) + 7 * 86400_000) });
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
    setRates({}); setErrors({});
    for (const currency of ['EUR', 'USD'] as const) {
      void fetchSgdRate(currency).then(value => { if (active) setRates(previous => ({ ...previous, [currency]: value })); })
        .catch(() => { if (active) setErrors(previous => ({ ...previous, [currency]: true })); });
    }
    return () => { active = false; };
  }, [enabled]);
  return { rates, errors };
}

export function toSgd(value: number, currency: string, rates: SgdRates): number | null {
  const rate = currency === 'EUR' || currency === 'USD' ? rates[currency]?.rate : undefined;
  const result = rate && rate > 0 ? value * rate : NaN;
  return value >= 0 && Number.isFinite(value) && Number.isFinite(result) ? result : null;
}
export const formatSgd = (value: number) => `SGD ${value.toLocaleString('en-SG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
