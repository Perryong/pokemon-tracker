import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import MarketSearch from '../MarketSearch';
const rates = { EUR: { rate: 1.5, expiresAt: Date.now() + 6 * 3600_000, date: '2026-10-29' }, USD: { rate: 1.3, expiresAt: Date.now() + 6 * 3600_000, date: '2026-10-29' } };
const briefs = (count = 2) => Array.from({ length: count }, (_,i) => ({ id: `base1-${i}`, name: `Pikachu ${i}` }));
const details = (id: string) => ({ schemaVersion: 1, mode: 'reference', source: 'TCGdex', card: { id, name: `Pikachu ${id.split('-').pop()}` }, fetchedAt: '2026-10-30T04:00:00Z', quotes: [{ provider: 'cardmarket', currency: 'EUR', variant: 'Reference', updatedAt: null, freshness: 'unknown', prices: { trend: Number(id.split('-').pop()) + 10 } }] });
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
const search = (name = 'pika') => { fireEvent.change(screen.getByLabelText('Search card names'), { target: { value: name } }); fireEvent.submit(screen.getByRole('form', { name: 'Card name search' })); };
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async url => response(String(url).includes('/search?') ? { schemaVersion: 1, query: 'pika', cards: briefs(), truncated: false } : details(String(url).split('/').pop()!)))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it('finds partial-name matches, converts prices and selects an exact card', async () => {
  const select = vi.fn(); render(<MarketSearch rates={rates} onSelect={select} />); search();
  expect(await screen.findByText('SGD 15.00')).toBeInTheDocument();
  expect(screen.getByText('SGD 16.50')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Sort loaded cards'), { target: { value: 'price-desc' } });
  expect(screen.getAllByRole('button', { name: /View prices for/ })[0]).toHaveAccessibleName('View prices for Pikachu 1 base1-1');
  fireEvent.click(screen.getAllByRole('button', { name: /View prices for/ })[0]); expect(select).toHaveBeenCalledWith('base1-1');
  expect(screen.getByText(/Not a popularity ranking/)).toBeInTheDocument();
});
it('loads 12 at a time without pricing every match', async () => {
  vi.mocked(fetch).mockImplementation(async url => response(String(url).includes('/search?') ? { schemaVersion: 1, query: 'pika', cards: briefs(14), truncated: false } : details(String(url).split('/').pop()!)));
  render(<MarketSearch rates={rates} onSelect={vi.fn()} />); search();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(13));
  expect(screen.getAllByRole('button', { name: /View prices for/ })).toHaveLength(12);
  fireEvent.click(screen.getByRole('button', { name: 'Load more cards' }));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(15));
  expect(screen.getAllByRole('button', { name: /View prices for/ })).toHaveLength(14);
});
it('shows no matches and safe failures without fake prices', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(response({ schemaVersion: 1, query: 'pika', cards: [], truncated: false }));
  render(<MarketSearch rates={{}} onSelect={vi.fn()} />); search();
  expect(await screen.findByText(/No cards match/)).toBeInTheDocument();
  vi.mocked(fetch).mockResolvedValueOnce(response({ error: 'rate_limited' }, 429)); search('pika v');
  expect(await screen.findByRole('alert')).toHaveTextContent(/limit/i);
});
it('ignores an old search after the input changes', async () => {
  let finish!: (r: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  render(<MarketSearch rates={rates} onSelect={vi.fn()} />); search();
  fireEvent.change(screen.getByLabelText('Search card names'), { target: { value: 'char' } });
  await act(async () => finish(response({ schemaVersion: 1, query: 'pika', cards: briefs(), truncated: false })));
  expect(screen.queryByRole('button', { name: /View prices for/ })).not.toBeInTheDocument();
});
it('limits concurrent card requests to three and aborts on unmount', async () => {
  const signals: AbortSignal[] = [];
  vi.mocked(fetch).mockImplementation(async (url, init) => {
    if (String(url).includes('/search?')) return response({ schemaVersion: 1, query: 'pika', cards: briefs(12), truncated: false });
    signals.push(init!.signal as AbortSignal);
    return new Promise(() => {});
  });
  const { unmount } = render(<MarketSearch rates={rates} onSelect={vi.fn()} />); search();
  await waitFor(() => expect(signals).toHaveLength(3));
  expect(fetch).toHaveBeenCalledTimes(4);
  unmount(); expect(signals.every(signal => signal.aborted)).toBe(true);
});
