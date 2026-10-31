import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { MARKET_API_URL, MarketCardSchema, MarketQuerySchema, MarketSearchSchema, type MarketCard, type MarketSearchResult } from '@/lib/market';
import { formatSgd, toSgd, type SgdRates } from '@/lib/exchange-rate';

function waitForRetry(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise(resolve => {
    const finish = () => { clearTimeout(timer); signal.removeEventListener('abort', finish); resolve(); };
    const timer = setTimeout(finish, milliseconds);
    signal.addEventListener('abort', finish, { once: true });
    if (signal.aborted) finish();
  });
}

type PriceState = { data?: MarketCard; error?: string };
function reference(data: MarketCard | undefined, rates: SgdRates) {
  const cardmarket = data?.quotes.find(quote => quote.provider === 'cardmarket');
  const amount = cardmarket?.prices.trend ?? cardmarket?.prices.avg;
  if (amount !== undefined && cardmarket) return { amount: toSgd(amount, cardmarket.currency, rates), basis: 'Cardmarket reference', freshness: cardmarket.freshness };
  const tcgplayer = data?.quotes.find(quote => quote.provider === 'tcgplayer' && quote.prices.marketPrice !== undefined);
  return tcgplayer ? { amount: toSgd(tcgplayer.prices.marketPrice!, tcgplayer.currency, rates), basis: `TCGplayer ${tcgplayer.variant}`, freshness: tcgplayer.freshness } : null;
}

export default function MarketSearch({ rates, onSelect }: { rates: SgdRates; onSelect: (id: string) => void }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MarketSearchResult | null>(null);
  const [count, setCount] = useState(0);
  const [prices, setPrices] = useState<Record<string, PriceState>>({});
  const [sort, setSort] = useState('relevance');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pricing, setPricing] = useState(false);
  const [paused, setPaused] = useState(false);
  const [cooldown, setCooldown] = useState<{ until: number; source: string } | null>(null);
  const [clock, setClock] = useState(Date.now);
  useEffect(() => {
    if (!cooldown) return;
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);
  const current = useRef<AbortController>();
  const generation = useRef(0);
  useEffect(() => () => current.current?.abort(), []);

  async function priceBatch(cards: MarketSearchResult['cards'], controller: AbortController, version: number) {
    setPricing(true); setPaused(false);
    let index = 0;
    let retryAt = 0;
    let stopped = '';
    await Promise.all(Array.from({ length: Math.min(3, cards.length) }, async () => {
      while (index < cards.length && !controller.signal.aborted) {
        const card = cards[index++];
        let state: PriceState = {};
        for (let attempt = 0; attempt <= 2; attempt++) {
          if (stopped) { state = { error: stopped }; break; }
          while (retryAt > Date.now() && !controller.signal.aborted) await waitForRetry(Math.min(retryAt - Date.now(), 3600_000), controller.signal);
          if (controller.signal.aborted || version !== generation.current) return;
          setCooldown(previous => previous && previous.until > Date.now() ? previous : null);
          try {
            const response = await fetch(`${MARKET_API_URL}/cards/${encodeURIComponent(card.id)}`, { headers: { 'X-Market-Priority': 'background' }, signal: AbortSignal.any([controller.signal, AbortSignal.timeout(12000)]) });
            if (controller.signal.aborted || version !== generation.current) return;
            if (response.status === 429) {
              const body: unknown = await response.json();
              if (controller.signal.aborted || version !== generation.current) return;
              const limit = body && typeof body === 'object' ? body as Record<string, unknown> : {};
              const seconds = typeof limit.retryAfterSeconds === 'number' && Number.isFinite(limit.retryAfterSeconds) && limit.retryAfterSeconds > 0 ? Math.ceil(limit.retryAfterSeconds) : 60;
              const source = limit.error === 'provider_rate_limited' ? 'Provider' : 'Price API';
              if (seconds > 3600) { stopped = `${source} limit: wait ${seconds} seconds before retrying.`; state = { error: stopped }; break; }
              retryAt = Math.max(retryAt, Date.now() + seconds * 1000);
              setClock(Date.now()); setCooldown({ until: retryAt, source });
              if (attempt === 2) { state = { error: 'Still limited; select this card to retry later.' }; break; }
              continue;
            }
            if (!response.ok) throw new Error('Price unavailable');
            const data = MarketCardSchema.parse(await response.json());
            if (data.card.id !== card.id) throw new Error('Mismatched card');
            state = { data };
          } catch { state = { error: 'Price unavailable; select card to retry.' }; }
          break;
        }
        if (controller.signal.aborted || version !== generation.current) return;
        setPrices(previous => ({ ...previous, [card.id]: state }));
      }
    }));
    if (!controller.signal.aborted && version === generation.current) { setPricing(false); setCooldown(null); }
  }
  function cancel() { current.current?.abort(); generation.current++; setLoading(false); setPricing(false); setCooldown(null); setPaused(false); }
  function select(id: string) { const interrupted = pricing || paused; cancel(); setPaused(interrupted); onSelect(id); }
  function resume() {
    if (!results) return;
    const controller = new AbortController(); current.current = controller;
    void priceBatch(results.cards.slice(0, count).filter(card => !prices[card.id]), controller, generation.current);
  }
  async function search() {
    cancel(); setError(''); setResults(null); setPrices({}); setCount(0); setSort('relevance');
    const parsed = MarketQuerySchema.safeParse(query);
    if (!parsed.success) { setError('Enter 2–60 letters or numbers, such as pika or Pikachu.'); return; }
    const version = generation.current;
    const controller = new AbortController(); current.current = controller;
    setLoading(true);
    try {
      const response = await fetch(`${MARKET_API_URL}/search?q=${encodeURIComponent(parsed.data)}`, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(12000)]) });
      if (!response.ok) throw new Error(response.status === 429 ? 'Search limit reached. Wait a minute and retry.' : 'Search unavailable. Check your connection and try again later.');
      const data = MarketSearchSchema.parse(await response.json());
      if (data.query.toLowerCase() !== parsed.data.toLowerCase()) throw new Error('Mismatched search');
      if (controller.signal.aborted || version !== generation.current) return;
      setResults(data); setCount(Math.min(12, data.cards.length)); setLoading(false);
      await priceBatch(data.cards.slice(0, 12), controller, version);
    } catch (failure) {
      if (!controller.signal.aborted && version === generation.current) { setLoading(false); setError(failure instanceof Error && failure.message.startsWith('Search limit') ? failure.message : 'Search unavailable. Check your connection and try again later.'); }
    }
  }
  function more() {
    if (!results || pricing || paused) return;
    if (!current.current || current.current.signal.aborted) current.current = new AbortController();
    const next = Math.min(count + 12, results.cards.length);
    setCount(next);
    void priceBatch(results.cards.slice(count, next), current.current, generation.current);
  }
  const visible = (results?.cards.slice(0, count) ?? []).map((card, index) => ({ card, index, quote: reference(prices[card.id]?.data, rates) }));
  if (sort !== 'relevance') visible.sort((a,b) => {
    const left = a.quote?.amount, right = b.quote?.amount;
    if (left == null) return right == null ? a.index - b.index : 1;
    if (right == null) return -1;
    return (sort === 'price-desc' ? right - left : left - right) || a.index - b.index;
  });
  return <section className="market-discovery" aria-label="Discover cards">
    <form className="filter-tray" aria-label="Card name search" onSubmit={event => { event.preventDefault(); void search(); }}>
      <div className="filter-field grow"><label htmlFor="market-search">Search card names</label><input className="control" id="market-search" placeholder="Try Pikachu or pika" value={query} maxLength={60} onChange={event => { cancel(); setQuery(event.target.value); setResults(null); setPrices({}); setError(''); }} /></div>
      <Button type="submit" disabled={loading}>{loading ? 'Searching…' : 'Search cards'}</Button>
    </form>
    <p className="market-meta">Relevant name matches and estimated SGD reference prices. Not a popularity ranking.</p>
    {error && <p className="alert-message" role="alert">{error}</p>}
    {results && <>
      <div className="market-results-heading"><p role="status">{count} of {results.cards.length}{results.truncated ? '+' : ''} matches{pricing ? ' · loading prices…' : ''}</p><div className="filter-field"><label htmlFor="market-sort">Sort loaded cards</label><select className="control" id="market-sort" value={sort} onChange={event => setSort(event.target.value)}><option value="relevance">Name relevance</option><option value="price-desc">SGD price: high to low</option><option value="price-asc">SGD price: low to high</option></select></div></div>
      {cooldown && <p className="market-meta" role="status">{cooldown.source} request limit: retrying prices in {Math.max(0, Math.ceil((cooldown.until - clock) / 1000))}s. You can still select a card.</p>}
      {paused && <p className="market-meta">Background prices paused for your selection. <Button type="button" variant="outline" onClick={resume}>Resume price loading</Button></p>}
      {results.cards.length === 0 && <p className="empty-state">No cards match this name. Try a shorter word.</p>}
      {results.truncated && <p className="market-meta">Showing up to 500 matches. Narrow the name to find more specific cards.</p>}
      <div className="market-result-grid">{visible.map(({ card, quote }) => <article className="market-result" key={card.id}>
        <button type="button" onClick={() => select(card.id)} aria-label={`View prices for ${card.name} ${card.id}`}>
          <div className="market-result-art">{card.image ? <img src={`${card.image}/low.webp`} alt={card.name} loading="lazy" decoding="async" /> : <span>Image unavailable</span>}</div>
          <h3>{card.name}</h3><p className="market-meta">{card.id}</p>
          <strong>{quote?.amount != null ? formatSgd(quote.amount) : prices[card.id]?.error ?? (!prices[card.id] ? paused ? 'Price loading paused' : cooldown ? 'Waiting to retry…' : 'Loading price…' : quote ? 'SGD conversion unavailable' : 'No reference price')}</strong>
          {quote && <p className="market-meta">{quote.basis} · {quote.freshness === 'unknown' ? 'freshness unknown' : quote.freshness}</p>}
          <span className="market-open">View prices & chart →</span>
        </button>
      </article>)}</div>
      {count < results.cards.length && <Button type="button" variant="outline" disabled={pricing || paused} onClick={more}>Load more cards</Button>}
      <p className="market-meta">Price order covers loaded cards only. Missing prices sort last; references may describe different printings or conditions.</p>
      <p className="market-meta">{(['EUR', 'USD'] as const).filter(currency => rates[currency]).map(currency => `1 ${currency} = ${rates[currency]!.rate.toFixed(4)} SGD (${rates[currency]!.date})`).join(' · ')} · ECB via Frankfurter</p>
    </>}
  </section>;
}
