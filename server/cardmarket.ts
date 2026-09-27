import type { IncomingMessage, ServerResponse } from 'node:http';
import { normalizeProviderPrices } from '../src/lib/provider-prices';

export function cardmarketMiddleware(apiKey: string) {
  // ponytail: process-local cache capped at 512 cards; use shared storage if deploying multiple instances.
  const cache = new Map<string, { expires: number; quotes: ReturnType<typeof normalizeProviderPrices> }>();
  const pending = new Map<string, Promise<ReturnType<typeof normalizeProviderPrices>>>();
  let requests = 0;
  let reset = Date.now() + 60000;
  return async (req: IncomingMessage, res: ServerResponse, next: () => void) => {
    const url = new URL(req.url || '/', 'http://localhost');
    if (!url.pathname.startsWith('/api/cardmarket/')) return next();
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Cache-Control', 'private, max-age=300');
    const id = url.pathname.slice('/api/cardmarket/'.length);
    if (req.method !== 'GET' || !/^[a-zA-Z0-9]+-[a-zA-Z0-9.]+$/.test(id) || id.length > 80) { res.statusCode = 400; res.end('{"error":"Invalid card request"}'); return; }
    if (!apiKey) { res.statusCode = 503; res.end('{"error":"Price provider not configured"}'); return; }
    try {
      const hit = cache.get(id);
      let quotes = hit && hit.expires > Date.now() ? hit.quotes : undefined;
      if (!quotes) {
        if (Date.now() > reset) { requests = 0; reset = Date.now() + 60000; }
        let task = pending.get(id);
        if (!task) {
          if (++requests > 20) { res.statusCode = 429; res.end('{"error":"Price request limit reached"}'); return; }
          task = fetch(`https://api.pokemontcgapi.com/v1/cards/${encodeURIComponent(id)}?include=prices`, { headers: { 'X-Api-Key': apiKey }, signal: AbortSignal.timeout(8000) }).then(async response => {
            if (response.status === 404) return [];
            if (!response.ok) throw new Error('Provider unavailable');
            const data = await response.json();
            if (!data || typeof data !== 'object' || (!('legacy_id' in data) || data.legacy_id !== id) && (!('id' in data) || data.id !== id)) throw new Error('Card identity mismatch');
            return normalizeProviderPrices(data);
          }).then(value => {
            if (cache.size >= 512) cache.delete(cache.keys().next().value!);
            cache.set(id, { quotes: value, expires: Date.now() + 6 * 60 * 60 * 1000 });
            return value;
          }).finally(() => { pending.delete(id); });
          pending.set(id, task);
        }
        quotes = await task;
      }
      res.end(JSON.stringify({ quotes }));
    } catch { res.statusCode = 502; res.end('{"error":"Price provider unavailable"}'); }
  };
}
