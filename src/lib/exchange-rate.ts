import { useEffect, useState } from 'react';

type ExchangeRate = { rate: number; date: string };
let cached: { value: ExchangeRate; expires: number } | undefined;
let pending: Promise<ExchangeRate> | undefined;

function fetchRate(): Promise<ExchangeRate> {
  if (cached && cached.expires > Date.now()) return Promise.resolve(cached.value);
  if (!pending) pending = fetch('https://api.frankfurter.dev/v2/rate/EUR/SGD?providers=ecb', { signal: AbortSignal.timeout(8000) })
    .then(async response => {
      if (!response.ok) throw new Error('Exchange rate unavailable');
      const data = await response.json();
      if (data.base !== 'EUR' || data.quote !== 'SGD' || !Number.isFinite(data.rate) || data.rate <= 0 || typeof data.date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(data.date) || !Number.isFinite(Date.parse(data.date))) throw new Error('Invalid exchange rate');
      const value = { rate: data.rate, date: data.date };
      cached = { value, expires: Date.now() + 6 * 60 * 60 * 1000 };
      return value;
    }).finally(() => { pending = undefined; });
  return pending;
}

export function useCardmarketExchangeRate(enabled: boolean) {
  const [rate, setRate] = useState<ExchangeRate | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setError(false);
    setRate(null);
    fetchRate().then(value => { if (active) setRate(value); }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [enabled]);
  return { rate, error };
}
