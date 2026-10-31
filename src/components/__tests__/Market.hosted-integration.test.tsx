import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import MarketView from '../MarketView';

const api = 'https://pokemon-price-api-omega.vercel.app/api/market';
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it('loads hosted reference research on entry while keeping operator credentials and state same-origin', async () => {
  const calls: { url: string; options?: RequestInit }[] = [];
  let authenticated = false;
  const now = new Date().toISOString();
  const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
  vi.stubGlobal('fetch', vi.fn(async (input: string, options?: RequestInit) => {
    calls.push({ url: String(input), options });
    if (input === `${api}/health`) return response({ service: 'market-prices', schemaVersion: 1, mode: 'reference', source: 'TCGdex' });
    if (input === `${api}/rates`) return response({ EUR: { rate: 1.5, date: now.slice(0, 10), expiresAt: Date.now() + 3600_000 }, USD: { rate: 1.3, date: now.slice(0, 10), expiresAt: Date.now() + 3600_000 } });
    if (input === `${api}/cards/base1-1`) return response({ schemaVersion: 1, mode: 'reference', source: 'TCGdex', card: { id: 'base1-1', name: 'Alakazam' }, fetchedAt: now, quotes: [{ provider: 'cardmarket', currency: 'EUR', variant: 'Reference', updatedAt: now, freshness: 'current', prices: { avg: 10 } }] });
    if (input === '/api/operations/login') { authenticated = true; return new Response(null, { status: 204 }); }
    if (input === '/api/operations/state') return authenticated ? response({ mode: 'simulation', peer: 'fixture', live_ready: false, paused: true, schedule: { times: [], timezone: 'Asia/Singapore' }, runs: [], assessments: [], mandates: [], inventory: {}, blocked_reasons: [] }) : response({ error: 'unauthorized' }, 401);
    return response({ error: 'not_found' }, 404);
  }));
  render(<MarketView />);
  expect(await screen.findByText('SGD 15.00')).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /Alakazam/ })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Open private operations' }));
  fireEvent.change(await screen.findByLabelText('Access key'), { target: { value: 'test-private-operator-key' } });
  fireEvent.click(screen.getByRole('button', { name: 'Unlock operations' }));
  expect(await screen.findByRole('button', { name: 'Resume schedule' })).toBeInTheDocument();
  expect(calls.filter(call => call.url.startsWith(api)).length).toBeGreaterThanOrEqual(3);
  for (const call of calls.filter(call => call.url.startsWith(api))) {
    expect(call.url).not.toContain('operations');
    expect(call.options?.body).toBeUndefined();
    expect(call.options?.credentials).not.toBe('include');
    expect(new Headers(call.options?.headers).has('Authorization')).toBe(false);
  }
  expect(calls.find(call => call.url === '/api/operations/login')?.options?.body).toContain('test-private-operator-key');
});
