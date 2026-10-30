import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import MarketView from '../MarketView';
vi.mock('@/lib/exchange-rate', async () => ({ ...await vi.importActual('@/lib/exchange-rate'), useSgdExchangeRates: () => ({ rates: { EUR: { rate: 1.5, expiresAt: Date.now() + 6 * 3600_000, date: '2026-10-29' }, USD: { rate: 1.3, expiresAt: Date.now() + 6 * 3600_000, date: '2026-10-29' } }, errors: {} }) }));
const health = { service: 'market-prices', schemaVersion: 1, mode: 'reference', source: 'TCGdex' };
const card = (id = 'base1-1', name = 'Alakazam') => ({ schemaVersion: 1, mode: 'reference', source: 'TCGdex', card: { id, name }, fetchedAt: '2026-10-30T04:00:00Z', quotes: [{ provider: 'cardmarket', currency: 'EUR', variant: 'Reference (see metric)', updatedAt: '2026-10-29T10:00:00Z', freshness: 'current', prices: { avg: 48.3 } }] });
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
const submit = () => fireEvent.submit(screen.getByRole('form', { name: 'Price lookup' }));
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async url => response(String(url).endsWith('/health') ? health : card()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it('shows provenance, currency, separate timestamps and simulated harness status', async () => {
  render(<MarketView />);
  expect(await screen.findByText('Backend reachable')).toBeInTheDocument();
  expect(screen.getByText(/Market Agent remains simulated/)).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
  submit();
  expect(await screen.findByRole('heading', { name: /Alakazam/ })).toBeInTheDocument();
  expect(screen.getByText('SGD 72.45')).toBeInTheDocument();
  expect(screen.getByText(/Provider updated/)).toBeInTheDocument();
  expect(screen.getByText(/Fetched from TCGdex/)).toBeInTheDocument();
  expect(screen.getByText(/Current/)).toBeInTheDocument();
});
it('rejects invalid IDs locally', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  fireEvent.change(screen.getByLabelText('TCGdex card ID'), { target: { value: '../secret' } }); submit();
  expect(await screen.findByRole('alert')).toHaveTextContent('Enter a card ID');
  expect(fetch).toHaveBeenCalledTimes(1);
});
it('shows unavailable backend for a static HTML response without sample fallback', async () => {
  vi.mocked(fetch).mockResolvedValue(new Response('<html>static</html>'));
  render(<MarketView />);
  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument();
  expect(screen.queryByText('Alakazam')).not.toBeInTheDocument();
});
it('marks retained prices as previous after an upstream refresh fails', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable'); submit();
  await screen.findByRole('heading', { name: /Alakazam/ });
  vi.mocked(fetch).mockResolvedValueOnce(response({ error: 'provider_unavailable' }, 502));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh prices' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Price provider unavailable');
  expect(screen.getByText('Backend reachable')).toBeInTheDocument();
  expect(screen.getByText(/Previous result/)).toBeInTheDocument();
  expect(screen.getByText('SGD 72.45')).toBeInTheDocument();
});
it('shows empty quotes honestly', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...card(), quotes: [] })); submit();
  expect(await screen.findByText(/No reference prices available/)).toBeInTheDocument();
});
it('labels stale and unknown timestamps', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  const data = card(); data.quotes[0].freshness = 'stale';
  vi.mocked(fetch).mockResolvedValueOnce(response(data)); submit();
  expect(await screen.findByText(/Stale/)).toBeInTheDocument();
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...data, quotes: [{ ...data.quotes[0], updatedAt: null, freshness: 'unknown' }] })); submit();
  expect(await screen.findByText(/Freshness unknown/)).toBeInTheDocument();
});
it('ignores late card responses after a new selection, including transports that ignore abort', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; })); submit();
  fireEvent.change(screen.getByLabelText('TCGdex card ID'), { target: { value: 'sv03-199' } });
  vi.mocked(fetch).mockResolvedValueOnce(response(card('sv03-199', 'Ninetales'))); submit();
  await screen.findByRole('heading', { name: /Ninetales/ });
  await act(async () => finish(response(card())));
  expect(screen.queryByRole('heading', { name: /Alakazam/ })).not.toBeInTheDocument();
});
it('aborts on unmount and does not restart requests', async () => {
  const { unmount } = render(<MarketView />); await screen.findByText('Backend reachable');
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; })); submit();
  const signal = vi.mocked(fetch).mock.calls.at(-1)?.[1]?.signal;
  unmount(); expect(signal?.aborted).toBe(true);
  await act(async () => finish(response(card())));
  expect(fetch).toHaveBeenCalledTimes(2);
});
it('rejects mismatched identity instead of displaying another card', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  vi.mocked(fetch).mockResolvedValueOnce(response(card('sv03-199', 'Ninetales'))); submit();
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Backend response unavailable'));
  expect(screen.queryByRole('heading', { name: /Ninetales/ })).not.toBeInTheDocument();
});
it('does not let a late health failure override a successful price request', async () => {
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  render(<MarketView />); submit();
  await screen.findByRole('heading', { name: /Alakazam/ });
  await act(async () => finish(new Response('<html>unavailable</html>')));
  expect(screen.getByText('Backend reachable')).toBeInTheDocument();
});
it('loads a special-set card with a dotted set ID', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  fireEvent.change(screen.getByLabelText('TCGdex card ID'), { target: { value: 'sv03.5-199' } });
  vi.mocked(fetch).mockResolvedValueOnce(response(card('sv03.5-199', 'Charizard ex'))); submit();
  expect(await screen.findByRole('heading', { name: /Charizard ex/ })).toBeInTheDocument();
  expect(fetch).toHaveBeenLastCalledWith('/api/market/cards/sv03.5-199', expect.objectContaining({ signal: expect.any(AbortSignal) }));
});
it('lets the independent health check settle after the first lookup is cancelled', async () => {
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  render(<MarketView />);
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(() => {})); submit();
  fireEvent.change(screen.getByLabelText('TCGdex card ID'), { target: { value: 'sv03-199' } });
  await act(async () => finish(response(health)));
  expect(screen.getByText('Backend reachable')).toBeInTheDocument();
});
it('selects a searched card and takes keyboard focus to its price details', async () => {
  render(<MarketView />); await screen.findByText('Backend reachable');
  vi.mocked(fetch).mockImplementation(async url => response(String(url).includes('/search?') ? { schemaVersion: 1, query: 'pika', cards: [{ id: 'base1-58', name: 'Pikachu' }], truncated: false } : card('base1-58','Pikachu')));
  fireEvent.change(screen.getByLabelText('Search card names'), { target: { value: 'pika' } });
  fireEvent.submit(screen.getByRole('form', { name: 'Card name search' }));
  fireEvent.click(await screen.findByRole('button', { name: 'View prices for Pikachu base1-58' }));
  expect(await screen.findByRole('heading', { name: 'Pikachu base1-58' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'Card price details' })).toHaveFocus();
});
