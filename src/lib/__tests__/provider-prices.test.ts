import { expect, it } from 'vitest';
import { normalizeProviderPrices } from '../provider-prices';

it('keeps only valid English EUR ungraded Cardmarket rows, preserving date and condition', () => {
  const row = { source: 'CARDMARKET', locale: 'en', currency: 'EUR', variant: 'LOW', amount: 80, condition: 'NEAR_MINT', basis: 'ASKING', as_of: '2026-09-23' };
  const quotes = normalizeProviderPrices({ prices: [row, { ...row, source: 'CARDTRADER' }, { ...row, amount: -1 }, { ...row, locale: 'de' }, { ...row, grading: { score: 10 } }] });
  expect(quotes).toHaveLength(1);
  expect(quotes[0]).toMatchObject({ provider: 'cardmarket', currency: 'EUR', updated: '2026-09-23', source: 'pokemontcgapi.com', values: { low: 80 } });
  expect(quotes[0].variant).toContain('NEAR MINT');
  expect(quotes[0].variant).toContain('ASKING');
});
