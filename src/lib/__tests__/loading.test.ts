import { afterEach, expect, it, vi } from 'vitest';
import { normalizeTCGCard, normalizeTCGSet } from '../types';
import { fetchAllSets, tcgdex } from '../tcgdex';

afterEach(() => vi.restoreAllMocks());

it('creates usable card and logo URLs while leaving absent images empty', () => {
  const card = normalizeTCGCard({ id: 'base1-1', name: 'Alakazam', localId: '1', image: 'https://assets.tcgdex.net/en/base/base1/1' });
  expect(card.images).toEqual({ small: 'https://assets.tcgdex.net/en/base/base1/1/low.webp', large: 'https://assets.tcgdex.net/en/base/base1/1/high.webp' });
  expect(normalizeTCGSet({ id: 'base1', name: 'Base', cardCount: { official: 102, total: 102 }, logo: 'https://assets.tcgdex.net/en/base/base1/logo' }).images.logo).toBe('https://assets.tcgdex.net/en/base/base1/logo.webp');
  expect(normalizeTCGCard({ id: 'missing', name: 'Missing', localId: '1' }).images.small).toBe('');
});

it('shares pending reads and allows retry after a failed request', async () => {
  const fetch = vi.spyOn(tcgdex, 'fetch').mockRejectedValueOnce(new Error('offline')).mockResolvedValue([]);
  vi.spyOn(console, 'error').mockImplementation(() => {});
  const results = await Promise.allSettled([fetchAllSets(), fetchAllSets()]);
  expect(results.map(r => r.status)).toEqual(['rejected', 'rejected']);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(await fetchAllSets()).toEqual([]);
  expect(fetch).toHaveBeenCalledTimes(2);
});
