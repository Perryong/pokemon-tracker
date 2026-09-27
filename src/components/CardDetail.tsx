import { useEffect, useState } from 'react';
import { PokemonCard, useCard } from '@/lib/api';
import { useCardmarketExchangeRate } from '@/lib/exchange-rate';
import { useCollection } from '@/lib/collection';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Check, BookOpen } from 'lucide-react';

interface CardDetailProps { card: PokemonCard | null; open: boolean; onOpenChange: (open: boolean) => void; }
const priceLabels: Record<string, string> = { lowPrice: 'Low', midPrice: 'Median', highPrice: 'High', marketPrice: 'Market price', directLowPrice: 'Direct low', avg: 'Average', low: 'Low', trend: 'Trend', avg1: '1-day average', avg7: '7-day average', avg30: '30-day average', 'avg-holo': 'Holo average', 'low-holo': 'Holo low', 'trend-holo': 'Holo trend', 'avg1-holo': 'Holo 1-day average', 'avg7-holo': 'Holo 7-day average', 'avg30-holo': 'Holo 30-day average' };
export default function CardDetail({ card: summary, open, onOpenChange }: CardDetailProps) {
  const { card: details, loading, error } = useCard(open ? summary?.id || null : null);
  const card = details?.id === summary?.id ? details : summary;
  const { isInCollection, getQuantity, setQuantity, removeFromCollection } = useCollection();
  const { rate: exchangeRate, error: exchangeError } = useCardmarketExchangeRate(open && !!card?.marketPrices?.some(quote => quote.provider === 'cardmarket' && quote.currency === 'EUR'));
  const [quantity, setDraftQuantity] = useState(1);
  const [saveError, setSaveError] = useState('');
  const cardId = summary?.id;
  useEffect(() => { if (open && cardId) { setDraftQuantity(getQuantity(cardId) || 1); setSaveError(''); } }, [cardId, open, getQuantity]);
  if (!card) return null;
  const owned = isInCollection(card.id);
  const save = (remove = false) => {
    try { if (remove) removeFromCollection(card.id); else setQuantity(card.id, quantity); setSaveError(''); }
    catch { setSaveError('Your browser could not save this change. Free up device storage and try again.'); }
  };
  return <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-w-[850px] max-h-[92vh] overflow-y-auto p-6 sm:p-8">
      <DialogHeader className="text-left mb-2"><DialogTitle className="detail-title flex items-center gap-3">{card.name}{owned && <span className="text-xs font-sans text-primary flex items-center gap-1"><Check size={13} />Owned</span>}</DialogTitle><DialogDescription>{card.set.name || 'Pokémon TCG'} · {card.number} / {card.set.printedTotal || '—'}</DialogDescription></DialogHeader>
      <div className="detail-layout">
        <div className="detail-art">{card.images.large ? <img src={card.images.large} alt={card.name} decoding="async" /> : <p className="page-description">Image unavailable</p>}</div>
        <Tabs defaultValue="info" className="min-w-0"><TabsList className="grid w-full grid-cols-3 h-11"><TabsTrigger value="info" className="text-xs">Card Info</TabsTrigger><TabsTrigger value="market" className="text-xs">Market Data</TabsTrigger><TabsTrigger value="collection" className="text-xs">Collection</TabsTrigger></TabsList>
          <TabsContent value="info">
            {loading && <p role="status" className="page-description">Loading card details…</p>}
            {error && <p role="alert" className="alert-message">Could not load card details: {error.message}. Close and reopen to retry.</p>}
            <dl className="detail-facts"><div><dt>Category</dt><dd>{card.supertype} {card.subtypes.join(', ')}</dd></div><div><dt>Rarity</dt><dd>{card.rarity || '—'}</dd></div>{card.hp && <div><dt>HP</dt><dd>{card.hp}</dd></div>}{card.types && <div><dt>Type</dt><dd>{card.types.join(', ')}</dd></div>}{card.evolvesFrom && <div><dt>Evolves from</dt><dd>{card.evolvesFrom}</dd></div>}<div><dt>Artist</dt><dd>{card.artist || '—'}</dd></div></dl>
            {card.abilities?.map(ability => <div key={ability.name} className="detail-ability"><h3>{ability.name}</h3><p>{ability.effect}</p></div>)}
            {card.attacks?.map(attack => <div key={attack.name} className="detail-ability"><div className="flex justify-between gap-2"><h3>{attack.name}</h3><span className="text-sm font-semibold">{attack.damage}</span></div>{attack.cost.length > 0 && <p>{attack.cost.join(' · ')}</p>}<p>{attack.text}</p></div>)}
            <dl className="detail-facts">{card.weaknesses?.length ? <div><dt>Weakness</dt><dd>{card.weaknesses.map(w => `${w.type} ${w.value}`).join(', ')}</dd></div> : null}{card.resistances?.length ? <div><dt>Resistance</dt><dd>{card.resistances.map(w => `${w.type} ${w.value}`).join(', ')}</dd></div> : null}{card.convertedRetreatCost !== undefined && <div><dt>Retreat cost</dt><dd>{card.convertedRetreatCost}</dd></div>}</dl>
            {card.rules?.map(rule => <p key={rule} className="page-description">{rule}</p>)}{card.flavorText && <p className="page-description italic">{card.flavorText}</p>}
          </TabsContent>
          <TabsContent value="market">{loading ? <p role="status" className="page-description">Loading market data…</p> : error ? <p role="alert" className="alert-message">Could not load market data. Close and reopen to retry.</p> : !card.marketPrices?.length ? <div className="py-8"><h3>No prices available yet.</h3><p className="page-description">The marketplaces don’t currently provide prices for this card.</p></div> : card.marketPrices.map(quote => { const convert = quote.provider === 'cardmarket' && quote.currency === 'EUR'; const currency = convert && exchangeRate ? 'SGD' : quote.currency; return <section className="market-provider" key={`${quote.provider}-${quote.variant}-${quote.updated}`}><h3>{quote.provider === 'tcgplayer' ? 'TCGplayer' : 'Cardmarket'}</h3>{quote.provider === 'cardmarket' && <p className="text-xs text-muted-foreground mb-2">Source: {quote.source || 'TCGdex (fallback)'}</p>}<p className="text-xs text-muted-foreground mb-2">{quote.variant === 'All printings' ? 'Card pricing' : quote.variant.replace(/-/g, ' ')} · {currency}</p>{convert && <p className="text-xs text-muted-foreground mb-3">{exchangeRate ? <>Estimated SGD · 1 EUR = {exchangeRate.rate.toFixed(4)} SGD · Rate date {exchangeRate.date} · <a href="https://frankfurter.dev/" target="_blank" rel="noreferrer" className="underline">ECB via Frankfurter</a></> : exchangeError ? 'SGD conversion unavailable. Showing original EUR prices; reopen to retry.' : 'Converting EUR prices to SGD…'}</p>}<table className="market-table"><caption className="sr-only">{quote.provider} prices in {currency}</caption><tbody>{Object.entries(quote.values).map(([label, value]) => <tr key={label}><th scope="row">{priceLabels[label] || label}</th><td>{currency} {(convert && exchangeRate ? value * exchangeRate.rate : value).toFixed(2)}</td></tr>)}</tbody></table>{quote.updated && <p className="updated">Updated {new Date(quote.updated).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}</p>}</section>; })}</TabsContent>
          <TabsContent value="collection" className="space-y-5 pt-5"><BookOpen size={25} className="text-primary" /><div><h3 className="font-semibold">{owned ? 'A part of your collection.' : 'Make room in your binder.'}</h3><p className="page-description">Record how many copies you own. Changes are saved on this device.</p></div><div className="filter-field"><label htmlFor="quantity">Quantity</label><input id="quantity" className="control max-w-[140px]" type="number" min={1} max={999} value={quantity} onChange={e => setDraftQuantity(Math.max(1, Math.min(999, Math.floor(Number(e.target.value) || 1))))} /></div>{saveError && <p role="alert" className="alert-message">{saveError}</p>}<div className="flex flex-wrap gap-2"><Button onClick={() => save()}>{owned ? 'Update' : 'Add to Collection'}</Button>{owned && <Button variant="outline" onClick={() => save(true)}>Remove from Collection</Button>}</div></TabsContent>
        </Tabs>
      </div>
    </DialogContent>
  </Dialog>;
}
