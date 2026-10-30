import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { MarketCardSchema, MarketQuerySchema, MarketSearchSchema, type MarketCard, type MarketSearchResult } from '@/lib/market';
import { formatSgd, toSgd, type SgdRates } from '@/lib/exchange-rate';

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
  const current = useRef<AbortController>();
  const generation = useRef(0);
  useEffect(() => () => current.current?.abort(), []);

  async function priceBatch(cards: MarketSearchResult['cards'], controller: AbortController, version: number) {
    setPricing(true);
    let index = 0;
    await Promise.all(Array.from({ length: Math.min(3, cards.length) }, async () => {
      while (index < cards.length && !controller.signal.aborted) {
        const card = cards[index++];
        let state: PriceState;
        try {
          const response = await fetch(`/api/market/cards/${encodeURIComponent(card.id)}`, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(12000)]) });
          if (!response.ok) throw new Error(response.status === 429 ? 'Rate limit reached; select card to retry later.' : 'Price unavailable; select card to retry.');
          const data = MarketCardSchema.parse(await response.json());
          if (data.card.id !== card.id) throw new Error('Price unavailable; select card to retry.');
          state = { data };
        } catch (failure) { state = { error: failure instanceof Error && failure.message.startsWith('Rate limit') ? failure.message : 'Price unavailable; select card to retry.' }; }
        if (controller.signal.aborted || version !== generation.current) return;
        setPrices(previous => ({ ...previous, [card.id]: state }));
      }
    }));
    if (!controller.signal.aborted && version === generation.current) setPricing(false);
  }
  function cancel() { current.current?.abort(); generation.current++; setLoading(false); setPricing(false); }
  async function search() {
    cancel(); setError(''); setResults(null); setPrices({}); setCount(0); setSort('relevance');
    const parsed = MarketQuerySchema.safeParse(query);
    if (!parsed.success) { setError('Enter 2–60 letters or numbers, such as pika or Pikachu.'); return; }
    const version = generation.current;
    const controller = new AbortController(); current.current = controller;
    setLoading(true);
    try {
      const response = await fetch(`/api/market/search?q=${encodeURIComponent(parsed.data)}`, { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(12000)]) });
      if (!response.ok) throw new Error(response.status === 429 ? 'Search limit reached. Wait a minute and retry.' : 'Search unavailable. Check the Mac backend and retry.');
      const data = MarketSearchSchema.parse(await response.json());
      if (data.query.toLowerCase() !== parsed.data.toLowerCase()) throw new Error('Mismatched search');
      if (controller.signal.aborted || version !== generation.current) return;
      setResults(data); setCount(Math.min(12, data.cards.length)); setLoading(false);
      await priceBatch(data.cards.slice(0, 12), controller, version);
    } catch (failure) {
      if (!controller.signal.aborted && version === generation.current) { setLoading(false); setError(failure instanceof Error && failure.message.startsWith('Search limit') ? failure.message : 'Search unavailable. Check the Mac backend and retry.'); }
    }
  }
  function more() {
    if (!results || !current.current || pricing) return;
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
      {results.cards.length === 0 && <p className="empty-state">No cards match this name. Try a shorter word.</p>}
      {results.truncated && <p className="market-meta">Showing up to 500 matches. Narrow the name to find more specific cards.</p>}
      <div className="market-result-grid">{visible.map(({ card, quote }) => <article className="market-result" key={card.id}>
        <button type="button" onClick={() => onSelect(card.id)} aria-label={`View prices for ${card.name} ${card.id}`}>
          <div className="market-result-art">{card.image ? <img src={`${card.image}/low.webp`} alt={card.name} loading="lazy" decoding="async" /> : <span>Image unavailable</span>}</div>
          <h3>{card.name}</h3><p className="market-meta">{card.id}</p>
          <strong>{quote?.amount != null ? formatSgd(quote.amount) : prices[card.id]?.error ?? (!prices[card.id] ? 'Loading price…' : quote ? 'SGD conversion unavailable' : 'No reference price')}</strong>
          {quote && <p className="market-meta">{quote.basis} · {quote.freshness === 'unknown' ? 'freshness unknown' : quote.freshness}</p>}
          <span className="market-open">View prices & chart →</span>
        </button>
      </article>)}</div>
      {count < results.cards.length && <Button type="button" variant="outline" disabled={pricing} onClick={more}>Load more cards</Button>}
      <p className="market-meta">Price order covers loaded cards only. Missing prices sort last; references may describe different printings or conditions.</p>
      <p className="market-meta">{(['EUR', 'USD'] as const).filter(currency => rates[currency]).map(currency => `1 ${currency} = ${rates[currency]!.rate.toFixed(4)} SGD (${rates[currency]!.date})`).join(' · ')} · ECB via Frankfurter</p>
    </>}
  </section>;
}
