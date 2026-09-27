import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import CollectionView from '../CollectionView';
import { STORAGE_KEY } from '@/lib/collection-types';
import * as client from '@/lib/tcgdex';
afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); });
it('displays owned card names, thumbnails, and quantities', async () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 3, cardQuantities: { 'base1-1': 3 } }));
  vi.spyOn(client, 'fetchSetWithCards').mockResolvedValue({ id: 'base1', name: 'Base', cardCount: { total: 102, official: 102 }, cards: [{ id: 'base1-1', localId: '1', name: 'Alakazam', image: 'https://assets.tcgdex.net/en/base/base1/1' }] } as Awaited<ReturnType<typeof client.fetchSetWithCards>>);
  render(<CollectionView />);
  expect(await screen.findByText('Alakazam')).toBeInTheDocument();
  expect(screen.getByAltText('Alakazam')).toHaveAttribute('src', 'https://assets.tcgdex.net/en/base/base1/1/low.webp');
  expect(screen.getByText('Quantity: 3')).toBeInTheDocument();
});
