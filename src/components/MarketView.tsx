import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import PriceChart from './PriceChart';
import MarketSearch from './MarketSearch';
import { useSgdExchangeRates, toSgd, formatSgd } from '@/lib/exchange-rate';
import { MarketCardSchema, MarketHealthSchema, MarketIdSchema, type MarketCard } from '@/lib/market';

const errors: Record<string, string> = {
  card_not_found: 'Card not found. Check the TCGdex card ID.',
  provider_unavailable: 'Price provider unavailable. Try again later.',
  provider_timeout: 'Price provider timed out. Try again later.',
  rate_limited: 'Request limit reached. Wait a minute before trying again.',
};
const date = (value: string) => new Date(value).toLocaleString();

export default function MarketView() {
  const { rates, errors: rateErrors } = useSgdExchangeRates(true);
  const [id, setId] = useState('base1-1');
  const [backend, setBackend] = useState<'checking' | 'reachable' | 'unavailable'>('checking');
  const [data, setData] = useState<MarketCard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const detailHeading = useRef<HTMLHeadingElement>(null);
  const request = useRef<AbortController>();
  const backendSettled = useRef(false);
  const generation = useRef(0);

  useEffect(() => {
    const controller = new AbortController();

    const timer = setTimeout(() => { controller.abort(); if (!backendSettled.current) setBackend('unavailable'); }, 12000);
    controller.signal.addEventListener('abort', () => clearTimeout(timer), { once: true });
    void (async () => {
      try {
        const response = await fetch('/api/market/health', { signal: controller.signal });
        const valid = response.ok && MarketHealthSchema.safeParse(await response.json()).success;
        if (!controller.signal.aborted && !backendSettled.current) setBackend(valid ? 'reachable' : 'unavailable');
      } catch { if (!controller.signal.aborted && !backendSettled.current) setBackend('unavailable'); }
      finally { clearTimeout(timer); }
    })();
    // Invalidate the latest request counter on unmount, not a captured DOM reference.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { clearTimeout(timer); controller.abort(); request.current?.abort(); generation.current++; };
  }, []);

  async function load(selected = id.trim()) {
    request.current?.abort();
    const version = ++generation.current;
    if (!MarketIdSchema.safeParse(selected).success) { setLoading(false); setError('Enter a card ID such as base1-1 or sv03-199.'); return; }
    setId(selected);
    const controller = new AbortController();
    request.current = controller;
    setLoading(true); setError('');
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(`/api/market/cards/${encodeURIComponent(selected)}`, { signal: controller.signal });
      const raw: unknown = await response.json();
      if (version !== generation.current || controller.signal.aborted) return;
      backendSettled.current = true;
      if (!response.ok) {
        const code = raw && typeof raw === 'object' && 'error' in raw ? String(raw.error) : '';
        if (!errors[code]) throw new Error('Invalid response');
        setBackend('reachable'); setError(errors[code]); return;
      }
      const parsed = MarketCardSchema.parse(raw);
      if (parsed.card.id !== selected) throw new Error('Mismatched card');
      setBackend('reachable'); setData(parsed);
    } catch {
      if (version === generation.current) { backendSettled.current = true; setBackend('unavailable'); setError(controller.signal.aborted ? 'Backend request timed out. Try again.' : 'Backend response unavailable. Open the Mac-hosted view and check its connection.'); }
    } finally {
      clearTimeout(timer);
      if (version === generation.current) setLoading(false);
    }
  }

  const previous = Boolean(data && (loading || error || data.card.id !== id.trim()));
  return <section className="page market-view" aria-label="Market View">
    <header className="page-heading"><div><h1>Market</h1><p className="page-description">Find a card by name, compare estimated SGD prices, and explore its average-price chart.</p></div></header>
    <div className="market-status" role="status"><span className={`backend-dot ${backend}`} />{backend === 'checking' ? 'Checking backend…' : backend === 'reachable' ? 'Backend reachable' : 'Backend unavailable'}</div>
    <p className="page-description market-limit">Market Agent remains simulated. These reference prices are not completed-sale evidence or a buy recommendation. Approved policy and exact sale evidence are required before any real qualification.</p>
    <MarketSearch rates={rates} onSelect={selected => { void load(selected); detailHeading.current?.focus(); }} />
    <h2 ref={detailHeading} tabIndex={-1} className="market-detail-heading">Card price details</h2>
    <form className="filter-tray" aria-label="Price lookup" onSubmit={event => { event.preventDefault(); void load(); }}>
      <div className="filter-field grow"><label htmlFor="market-id">TCGdex card ID</label><input id="market-id" className="control" value={id} maxLength={80} autoCapitalize="none" spellCheck={false} aria-describedby="market-examples" onChange={event => { request.current?.abort(); generation.current++; setLoading(false); setError(''); setId(event.target.value); }} /><span id="market-examples" className="market-meta">Examples: base1-1 · sv03-199</span></div>
      <Button type="submit" disabled={loading}>{loading ? 'Loading…' : data?.card.id === id.trim() ? 'Refresh prices' : 'Load prices'}</Button>
    </form>
    {error && <p role="alert" className="alert-message">{error}</p>}
    {loading && <p role="status" className="market-meta">Fetching reference prices…</p>}
    {data && <div aria-live="polite">
      {previous && <p className="market-previous">Previous result — {data.card.name} ({data.card.id}). It does not confirm a successful current lookup.</p>}
      <h2 className="market-card-title">{data.card.name} <span>{data.card.id}</span></h2>
      <p className="market-meta">Fetched from TCGdex: <time dateTime={data.fetchedAt}>{date(data.fetchedAt)}</time>. Backend cache: up to 1 hour.</p>
      {data.quotes.length === 0 && <p className="empty-state">No reference prices available for this card.</p>}
      <div className="market-quotes">{data.quotes.map((quote, index) => <article className="market-quote" key={`${quote.provider}-${quote.variant}-${index}`}>
        <h3>{quote.provider === 'cardmarket' ? 'Cardmarket' : 'TCGplayer'} <span>SGD</span></h3>
        <p className="market-meta">{quote.variant}</p>
        <p className={`market-freshness ${quote.freshness}`}>{quote.freshness === 'current' ? 'Current · within 48 hours' : quote.freshness === 'stale' ? 'Stale · older than 48 hours' : 'Freshness unknown'}</p>
        <p className="market-meta">{rates[quote.currency] ? `Estimated SGD · 1 ${quote.currency} = ${rates[quote.currency]!.rate.toFixed(4)} SGD · Rate date ${rates[quote.currency]!.date} · ECB via Frankfurter` : rateErrors[quote.currency] ? 'SGD conversion unavailable. Reopen Market to retry.' : 'Loading SGD conversion…'}</p>
        {rates[quote.currency] && <PriceChart prices={quote.prices} rate={rates[quote.currency]!.rate} />}
        <table className="market-table"><caption className="sr-only">{quote.provider} reference prices in SGD</caption><tbody>{Object.entries(quote.prices).map(([metric, value]) => { const amount = toSgd(value, quote.currency, rates); return <tr key={metric}><th scope="row">{metric}</th><td>{amount === null ? 'Unavailable' : formatSgd(amount)}</td></tr>; })}</tbody></table>
        <p className="market-meta">Provider updated: {quote.updatedAt ? <time dateTime={quote.updatedAt}>{date(quote.updatedAt)}</time> : 'Unknown'}</p>
      </article>)}</div>
    </div>}
  </section>;
}
