import { useEffect, useState } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { useCollection } from '@/lib/collection';
import { PokemonCard, normalizeTCGCard } from '@/lib/types';
import { fetchSetWithCards } from '@/lib/tcgdex';
import { Button } from '@/components/ui/button';
import CardTile from './CardTile';

export default function CollectionView({ onCardSelect }: { onCardSelect?: (card: PokemonCard) => void }) {
  const [search, setSearch] = useState('');
  const { cardQuantities } = useCollection();
  const [cards, setCards] = useState<PokemonCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [failedSets, setFailedSets] = useState<string[]>([]);
  const setIdsKey = JSON.stringify([...new Set(Object.keys(cardQuantities).map(id => id.slice(0, id.lastIndexOf('-'))))].sort());
  useEffect(() => {
    let cancelled = false;
    const setIds: string[] = JSON.parse(setIdsKey);
    setLoading(setIds.length > 0);
    setFailedSets([]);
    Promise.allSettled(setIds.map(id => fetchSetWithCards(id))).then(results => {
      if (cancelled) return;
      setCards(results.flatMap(result => result.status === 'fulfilled' ? (result.value.cards || []).map(card => normalizeTCGCard(card, result.value)) : []));
      setFailedSets(results.flatMap((result, index) => result.status === 'rejected' ? [setIds[index]] : []));
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [setIdsKey]);
  const uniqueCards = Object.keys(cardQuantities).length;
  const totalQuantity = Object.values(cardQuantities).reduce((sum, quantity) => sum + quantity, 0);
  const visible = cards.filter(card => cardQuantities[card.id] > 0 && card.name.toLowerCase().includes(search.toLowerCase().trim()));
  return <section className="page">
    <header className="page-heading"><div><h1>My Collection</h1><p className="page-description">The cards you’ve found. The stories you’re keeping.</p></div><span className="save-indicator"><span />Saved on this device</span></header>
    <section aria-label="Collection View" className="collection-inventory">
      <h2 className="sr-only">Collection View</h2>
      <div className="collection-summary"><div><p>Unique Cards</p><strong>{uniqueCards}</strong></div><div><p>Total Quantity</p><strong>{totalQuantity}</strong></div>{totalQuantity > uniqueCards && <div><p>Extra copies</p><strong>{totalQuantity - uniqueCards}</strong></div>}</div>
      {uniqueCards > 0 && <div className="filter-tray"><div className="filter-field grow"><label htmlFor="collection-search">Find a card in your collection</label><div className="search-control"><Search size={16} /><input id="collection-search" type="search" className="control" placeholder="Search your collection..." value={search} onChange={e => setSearch(e.target.value)} /></div></div></div>}
      {failedSets.length > 0 && <p role="alert" className="alert-message">Could not load cards for {failedSets.join(', ')}. Your quantities are still saved.</p>}
      {loading ? <div className="card-grid" aria-label="Loading collection cards" aria-busy="true">{Array.from({ length: 5 }, (_, i) => <div className="card-specimen skeleton-art h-64" key={i} />)}</div> : uniqueCards === 0 ? <div className="empty-state"><BookOpen size={34} /><h2>Your collection starts with one card.</h2><p>Explore a set and select Add beneath any card.<br />Your cards will be waiting here when you return.</p></div> : visible.length === 0 ? <div className="empty-state"><h2>No matching cards</h2><p>Try a different name, or clear your search.</p><Button onClick={() => setSearch('')}>Clear search</Button></div> : <div className="card-grid">{visible.map(card => <div key={card.id}><CardTile card={card} onSelect={onCardSelect} /><p className="card-number mt-2">Quantity: {cardQuantities[card.id]}</p></div>)}</div>}
    </section>
  </section>;
}
