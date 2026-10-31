import { useEffect, useState } from 'react';
import { z } from 'zod';
import { MARKET_API_URL } from './market';

type Currency = 'EUR' | 'USD';
export type ExchangeRate = { rate: number; date: string; expiresAt: number };
export type SgdRates = Partial<Record<Currency, ExchangeRate>>;
const cached: SgdRates = {};
let pending: Promise<Record<Currency, ExchangeRate>> | undefined;
const rateSchema = z.object({ rate: z.number().finite().positive(), date: z.string().date(), expiresAt: z.number().finite().positive() });
const ratesSchema = z.object({ EUR: rateSchema, USD: rateSchema });

export async function fetchSgdRate(currency: Currency): Promise<ExchangeRate> {
  const hit = getSgdRate(currency, cached);
  if (hit) return hit;
  if (!pending) {
    pending = (async () => {
      const response = await fetch(`${MARKET_API_URL}/rates`, { signal: AbortSignal.timeout(8000), redirect: 'error' });
      if (!response.ok) throw new Error('Exchange rate unavailable');
      const rates = ratesSchema.parse(await response.json());
      const now = Date.now();
      for (const rate of Object.values(rates)) {
        const observation = Date.parse(rate.date);
        rate.expiresAt = Math.min(rate.expiresAt, now + 6 * 3600_000, observation + 7 * 86400_000);
        if (observation > now || rate.expiresAt <= now) throw new Error('Invalid or stale exchange rate');
      }
      Object.assign(cached, rates);
      return rates;
    })().finally(() => { pending = undefined; });
  }
  return (await pending)[currency];
}

export function useSgdExchangeRates(enabled: boolean) {
  const [rates, setRates] = useState<SgdRates>({});
  const [errors, setErrors] = useState<Partial<Record<Currency, boolean>>>({});
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    const timers: Partial<Record<Currency, ReturnType<typeof setTimeout>>> = {};
    const currentRates: SgdRates = {};
    const renewing = new Set<Currency>();
    const renew = async (currency: Currency) => {
      if (!active || renewing.has(currency)) return;
      renewing.add(currency);
      clearTimeout(timers[currency]);
      delete currentRates[currency];
      setRates(previous => { const next = { ...previous }; delete next[currency]; return next; });
      setErrors(previous => ({ ...previous, [currency]: false }));
      let retryAt = Date.now() + 6 * 3600_000;
      try {
        const value = await fetchSgdRate(currency);
        if (active) { currentRates[currency] = value; setRates(previous => ({ ...previous, [currency]: value })); retryAt = value.expiresAt; }
      } catch { if (active) setErrors(previous => ({ ...previous, [currency]: true })); }
      renewing.delete(currency);
      if (active) timers[currency] = setTimeout(() => { void renew(currency); }, Math.max(1, retryAt - Date.now()));
    };
    // Sleep can advance wall time without running the expiry timer.
    const resume = () => {
      if (document.visibilityState === 'hidden') return;
      for (const currency of ['EUR', 'USD'] as const) if (!getSgdRate(currency, currentRates)) void renew(currency);
    };
    for (const event of ['focus', 'pageshow', 'online']) window.addEventListener(event, resume);
    document.addEventListener('visibilitychange', resume);
    for (const currency of ['EUR', 'USD'] as const) void renew(currency);
    return () => {
      active = false; Object.values(timers).forEach(clearTimeout);
      for (const event of ['focus', 'pageshow', 'online']) window.removeEventListener(event, resume);
      document.removeEventListener('visibilitychange', resume);
    };

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
