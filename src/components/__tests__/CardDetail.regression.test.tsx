import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CardDetail from '../CardDetail';
import { normalizeTCGCard } from '@/lib/types';
import { STORAGE_KEY } from '@/lib/collection-types';

afterEach(() => { cleanup(); localStorage.clear(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it('opens a card and saves quantity with the current storage API', async () => {
  const { tcgdex } = await import('@/lib/tcgdex');
  vi.spyOn(tcgdex, 'fetch').mockResolvedValue(undefined);
  const card = normalizeTCGCard({ id: 'base1-1', name: 'Alakazam', localId: '1' });
  render(<CardDetail card={card} open onOpenChange={() => {}} />);
  await userEvent.click(screen.getByRole('tab', { name: 'Collection' }));
  fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '3' } });
  fireEvent.click(screen.getByRole('button', { name: 'Add to Collection' }));
  expect(JSON.parse(localStorage.getItem(STORAGE_KEY)! ).cardQuantities['base1-1']).toBe(3);
});

it('loads full card information and prices when opened', async () => {
  const { tcgdex } = await import('@/lib/tcgdex');
  const fetch = vi.spyOn(tcgdex, 'fetch').mockResolvedValue({
    id: 'base1-1', localId: '1', name: 'Alakazam', category: 'Pokemon', hp: 80,
    rarity: 'Rare', illustrator: 'Ken Sugimori', types: ['Psychic'],
    set: { id: 'base1', name: 'Base Set', cardCount: { total: 102, official: 102 } },
    legal: { standard: false, expanded: false },
    attacks: [{ name: 'Confuse Ray', damage: 30, effect: 'Flip a coin.' }],
    pricing: { tcgplayer: { unit: 'USD', updated: '2026-09-26', holofoil: { marketPrice: 67.51, lowPrice: 43.99 } } },
  } as never);
  const card = normalizeTCGCard({ id: 'base1-1', name: 'Alakazam', localId: '1' });
  render(<CardDetail card={card} open onOpenChange={() => {}} />);
  expect(await screen.findByText('Confuse Ray')).toBeInTheDocument();
  expect(screen.getByText('Ken Sugimori')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('tab', { name: 'Market Data' }));
  expect(await screen.findByText(/67.51/)).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith('cards', 'base1-1');
});

it('keeps original EUR prices when the exchange response is invalid', async () => {
  const { tcgdex } = await import('@/lib/tcgdex');
  vi.spyOn(tcgdex, 'fetch').mockResolvedValue({ id: 'base1-3', name: 'Chansey', localId: '3', pricing: { cardmarket: { unit: 'EUR', avg: 10 } } } as never);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ base: 'EUR', quote: 'USD', rate: -1, date: 'bad' }) }));
  render(<CardDetail card={normalizeTCGCard({ id: 'base1-3', name: 'Chansey', localId: '3' })} open onOpenChange={() => {}} />);
  await userEvent.click(screen.getByRole('tab', { name: 'Market Data' }));
  expect(await screen.findByText(/SGD conversion unavailable/)).toBeInTheDocument();
  expect(screen.getByText('EUR 10.00')).toBeInTheDocument();
});

it('converts only Cardmarket prices to SGD and shows the reference rate date', async () => {
  const { tcgdex } = await import('@/lib/tcgdex');
  vi.spyOn(tcgdex, 'fetch').mockResolvedValue({
    id: 'base1-2', localId: '2', name: 'Blastoise',
    pricing: { cardmarket: { unit: 'EUR', avg: 10, low: 0 }, tcgplayer: { unit: 'USD', holofoil: { marketPrice: 20 } } },
  } as never);
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ base: 'EUR', quote: 'SGD', rate: 1.5, date: '2026-09-25' }) }));
  render(<CardDetail card={normalizeTCGCard({ id: 'base1-2', name: 'Blastoise', localId: '2' })} open onOpenChange={() => {}} />);
  await userEvent.click(screen.getByRole('tab', { name: 'Market Data' }));
  expect(await screen.findByText('SGD 15.00')).toBeInTheDocument();
  expect(screen.getByText('SGD 0.00')).toBeInTheDocument();
  expect(screen.getByText('USD 20.00')).toBeInTheDocument();
  expect(screen.getByText(/1 EUR = 1.5000 SGD/)).toHaveTextContent('2026-09-25');
});
