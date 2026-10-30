import type { IncomingMessage, ServerResponse } from 'node:http';
import { MarketBriefSchema, MarketImageSchema, MarketQuerySchema, MarketSearchSchema, type MarketSearchResult, MarketCardSchema, MarketDateSchema, MarketIdSchema, cardmarketMetrics, tcgplayerMetrics, type MarketCard } from '../src/lib/market';

const MAX_BODY = 1024 * 1024;
const TTL = 3600_000;
const object = (value: unknown): Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
const freshness = (date: string | null): 'unknown' | 'current' | 'stale' => !date ? 'unknown' : Date.now() - Date.parse(date) > 48 * TTL ? 'stale' : 'current';
function updatedAt(value: unknown) {
  const parsed = MarketDateSchema.safeParse(value);
  return parsed.success && Date.parse(parsed.data) <= Date.now() ? parsed.data : null;
}
function normalize(raw: unknown, id: string): MarketCard {
  const data = object(raw);
  if (data.id !== id) throw new Error('Invalid identity');
  const quotes: MarketCard['quotes'] = [];
  const pricing = object(data.pricing);
  for (const provider of ['cardmarket', 'tcgplayer'] as const) {
    const source = object(pricing[provider]);
    const currency = provider === 'cardmarket' ? 'EUR' : 'USD';
    if (source.unit !== currency) continue;
    const date = updatedAt(source.updated);
    const variants = provider === 'cardmarket' ? [['Reference (see metric)', source] as const] : Object.entries(source).slice(0, 32);
    for (const [variant, values] of variants) {
      if (!variant || variant.length > 80) continue;
      const metrics = provider === 'cardmarket' ? cardmarketMetrics : tcgplayerMetrics;
      const prices: Record<string, number> = {};
      for (const metric of metrics) {
        const price = object(values)[metric];
        if (typeof price === 'number' && Number.isFinite(price) && price >= 0) prices[metric] = price;
      }
      if (Object.keys(prices).length) quotes.push({ provider, currency, variant, updatedAt: date, freshness: freshness(date), prices });
    }
  }
  return MarketCardSchema.parse({ schemaVersion: 1, mode: 'reference', source: 'TCGdex', card: { id: data.id, name: data.name }, fetchedAt: new Date().toISOString(), quotes });
}
function normalizeSearch(raw: unknown, query: string): MarketSearchResult {
  if (!Array.isArray(raw) || raw.length > 501) throw new Error('Invalid search data');
  const cards = raw.map(value => {
    const item = object(value);
    return MarketBriefSchema.parse({ id: item.id, name: item.name, ...(MarketImageSchema.safeParse(item.image).success ? { image: item.image } : {}) });
  });
  const rank = (name: string) => name.toLowerCase() === query ? 0 : name.toLowerCase().startsWith(query) ? 1 : 2;
  const matches = [...new Map(cards.filter(card => card.name.toLowerCase().includes(query)).map(card => [card.id, card])).values()];
  matches.sort((a,b) => rank(a.name) - rank(b.name) || a.name.localeCompare(b.name, 'en'));
  return MarketSearchSchema.parse({ schemaVersion: 1, query, cards: matches.slice(0, 500), truncated: raw.length > 500 });
}
async function readJson(response: Response): Promise<unknown> {
  if (Number(response.headers.get('content-length')) > MAX_BODY || !response.body) throw new Error('Invalid body');
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > MAX_BODY) throw new Error('Oversized body');
      chunks.push(value);
    }
  } finally { await reader.cancel(); reader.releaseLock(); }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

export function marketMiddleware() {
  const cache = new Map<string, { data: MarketCard | MarketSearchResult; expires: number }>();
  const pending = new Map<string, Promise<{ status: number; data: unknown }>>();
  let windowStart = Date.now();
  let calls = 0;
  async function load(id: string, query?: string) {
    try {
      const url = query ? `https://api.tcgdex.net/v2/en/cards?${new URLSearchParams({ name: `like:${query}`, 'pagination:page': '1', 'pagination:itemsPerPage': '501' })}` : `https://api.tcgdex.net/v2/en/cards/${encodeURIComponent(id)}`;
      const response = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(8000) });
      if (!response.ok) { await response.body?.cancel(); return { status: response.status === 404 ? 404 : 502, data: { error: response.status === 404 ? 'card_not_found' : 'provider_unavailable' } }; }
      const raw = await readJson(response);
      const data = query ? normalizeSearch(raw, query) : normalize(raw, id);
      if (cache.size >= 256) cache.delete(cache.keys().next().value!);
      cache.set(id, { data, expires: Date.now() + TTL });
      return { status: 200, data };
    } catch (error) {
      const timeout = error instanceof Error && error.name === 'TimeoutError';
      return { status: timeout ? 504 : 502, data: { error: timeout ? 'provider_timeout' : 'provider_unavailable' } };
    }
  }
  return async (req: IncomingMessage, res: ServerResponse, next: () => void) => {
    const path = req.url ?? '';
    if (path !== '/api/market' && !path.startsWith('/api/market/')) { next(); return; }
    const send = (status: number, data: unknown) => {
      res.statusCode = status;
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Cache-Control', 'no-store');
      res.end(JSON.stringify(data));
    };
    if (req.method !== 'GET') { res.setHeader('Allow', 'GET'); send(405, { error: 'method_not_allowed' }); return; }
    if (path === '/api/market/health') { send(200, { service: 'market-prices', schemaVersion: 1, mode: 'reference', source: 'TCGdex' }); return; }
    let query: string | undefined;
    if (path.split('?')[0] === '/api/market/search') {
      const params = new URL(path, 'http://local').searchParams;
      const parsed = MarketQuerySchema.safeParse(params.get('q'));
      if (!parsed.success || [...params.keys()].length !== 1 || params.has('q') === false) { send(400, { error: 'invalid_search' }); return; }
      query = parsed.data.toLowerCase();
    }
    const id = query ? `search:${query}` : path.startsWith('/api/market/cards/') ? path.slice('/api/market/cards/'.length) : '';
    if (!query && !MarketIdSchema.safeParse(id).success) { send(400, { error: 'invalid_card_id' }); return; }
    const cached = cache.get(id);
    if (cached && cached.expires > Date.now()) {
      send(200, 'quotes' in cached.data ? { ...cached.data, quotes: cached.data.quotes.map(quote => ({ ...quote, freshness: freshness(quote.updatedAt) })) } : cached.data); return;
    }
    cache.delete(id);
    let request = pending.get(id);
    if (!request) {
      if (Date.now() - windowStart >= 60_000) { windowStart = Date.now(); calls = 0; }
      if (calls >= 30) { send(429, { error: 'rate_limited' }); return; }
      calls++;
      request = load(id, query).finally(() => pending.delete(id));
      pending.set(id, request);
    }
    const result = await request;
    send(result.status, result.data);
  };
}
