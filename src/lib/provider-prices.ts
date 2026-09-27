import type { PokemonCard } from './types';
export function normalizeProviderPrices(data: unknown): NonNullable<PokemonCard['marketPrices']> {
  if (!data || typeof data !== 'object' || !('prices' in data) || !Array.isArray(data.prices)) return [];
  const labels: Record<string, string> = { LOW: 'low', AVG_7D: 'avg7', AVG_30D: 'avg30', AVG_1D: 'avg1', TREND: 'trend', MARKET: 'marketPrice' };
  const quotes: NonNullable<PokemonCard['marketPrices']> = [];
  for (const row of data.prices) {
    if (!row || row.source !== 'CARDMARKET' || row.locale !== 'en' || row.currency !== 'EUR' || row.grading || typeof row.amount !== 'number' || !Number.isFinite(row.amount) || row.amount < 0 || typeof row.variant !== 'string' || typeof row.as_of !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(row.as_of) || !Number.isFinite(Date.parse(row.as_of))) continue;
    const variant = ['English', row.printing || 'Unspecified printing', row.condition || 'Unspecified condition', row.basis || 'Unspecified basis'].map(value => String(value).replace(/_/g, ' ')).join(' · ');
    let quote = quotes.find(item => item.variant === variant && item.updated === row.as_of);
    if (!quote) { quote = { provider: 'cardmarket', source: 'pokemontcgapi.com', variant, currency: 'EUR', updated: row.as_of, values: {} }; quotes.push(quote); }
    quote.values[labels[row.variant] || row.variant.replace(/_/g, ' ')] = row.amount;
  }
  return quotes;
}
