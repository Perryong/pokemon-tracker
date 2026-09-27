import { useMemo, useState } from 'react';
import { ArrowLeft, Filter, Search } from 'lucide-react';
import { PokemonCard, PokemonSet, useCards } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import { Button } from '@/components/ui/button';
import { computeQuantityStats } from '@/lib/stats';
import CardTile from './CardTile';
import BrowsePagination from './BrowsePagination';

export default function CardGrid({ selectedSet, onBackClick, onCardSelect }: { selectedSet: PokemonSet; onBackClick: () => void; onCardSelect: (card: PokemonCard) => void }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [ownership, setOwnership] = useState('all');
  const [size, setSize] = useState('medium');
  const [showFilters, setShowFilters] = useState(false);
  const [type, setType] = useState('');
  const [rarity, setRarity] = useState('');
  const [subtype, setSubtype] = useState('');
  // Set details already include every summary; filter the whole set before paging.
  const { cards, loading, error } = useCards(selectedSet.id, 1, Number.MAX_SAFE_INTEGER);
  const { cardQuantities, isInCollection } = useCollection();
  const filtered = useMemo(() => cards.filter(card =>
    card.name.toLowerCase().includes(search.toLowerCase().trim()) &&
    (ownership === 'all' || (ownership === 'owned' ? isInCollection(card.id) : !isInCollection(card.id))) &&
    (!type || card.types?.includes(type)) && (!rarity || card.rarity === rarity) && (!subtype || card.subtypes.includes(subtype))
  ), [cards, search, ownership, isInCollection, type, rarity, subtype]);
  const stats = computeQuantityStats(filtered.map(card => card.id), cardQuantities);
  const pages = Math.ceil(filtered.length / 20);
  const currentPage = Math.min(page, Math.max(1, pages));
  const visible = filtered.slice((currentPage - 1) * 20, currentPage * 20);
  const types = [...new Set(cards.flatMap(card => card.types || []))];
  const rarities = [...new Set(cards.flatMap(card => card.rarity ? [card.rarity] : []))];
  const subtypes = [...new Set(cards.flatMap(card => card.subtypes))];
  const clear = () => { setSearch(''); setOwnership('all'); setType(''); setRarity(''); setSubtype(''); setPage(1); };
  return <section className="page">
    <button type="button" className="back-button" onClick={onBackClick}><ArrowLeft size={15} />Back to Sets</button>
    <header className="page-heading"><div><h1>{selectedSet.name}</h1><p className="page-description">{selectedSet.total} cards in this set. A place for every discovery.</p></div><span className="result-count">{selectedSet.series !== 'Unknown' ? selectedSet.series : selectedSet.id.toUpperCase()}</span></header>
    <div className="browse-summary"><span><span>Owned:</span> <strong>{stats.uniqueOwned}</strong></span><span><span>Missing:</span> <strong>{stats.missing}</strong></span><span><span>Completion:</span> <strong>{stats.completionPercent.toFixed(1)}%</strong></span><span><span>Total Qty:</span> <strong>{stats.totalQuantity}</strong></span></div>
    <div className="filter-tray">
      <div className="filter-field grow"><label htmlFor="card-search">Find a card</label><div className="search-control"><Search size={16} /><input id="card-search" type="search" className="control" placeholder="Search cards..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} /></div></div>
      <div className="filter-field"><label htmlFor="ownership">In your binder</label><select id="ownership" className="control" value={ownership} onChange={e => { setOwnership(e.target.value); setPage(1); }}><option value="all">All cards</option><option value="owned">Owned</option><option value="missing">Missing</option></select></div>
      <div className="filter-field"><label htmlFor="card-size">Card size</label><select id="card-size" className="control" value={size} onChange={e => setSize(e.target.value)}><option value="medium">Medium</option><option value="small">Small</option></select></div>
      <Button variant="outline" className="h-[42px]" onClick={() => setShowFilters(!showFilters)} aria-expanded={showFilters}><Filter size={14} className="mr-2" />Filters</Button>
      {(search || ownership !== 'all' || type || rarity || subtype) && <Button variant="ghost" onClick={clear}>Clear Filters</Button>}
      {showFilters && <div className="flex flex-wrap gap-3 w-full"><div className="filter-field"><label htmlFor="type">Type</label><select id="type" className="control" value={type} disabled={!types.length} onChange={e => { setType(e.target.value); setPage(1); }}><option value="">All types</option>{types.map(value => <option key={value}>{value}</option>)}</select></div><div className="filter-field"><label htmlFor="rarity">Rarity</label><select id="rarity" className="control" value={rarity} disabled={!rarities.length} onChange={e => { setRarity(e.target.value); setPage(1); }}><option value="">All rarities</option>{rarities.map(value => <option key={value}>{value}</option>)}</select></div><div className="filter-field"><label htmlFor="subtype">Subtype</label><select id="subtype" className="control" value={subtype} disabled={!subtypes.length} onChange={e => { setSubtype(e.target.value); setPage(1); }}><option value="">All subtypes</option>{subtypes.map(value => <option key={value}>{value}</option>)}</select></div>{!types.length && <p className="page-description">Open a card to see its full type and rarity details. Set summaries don’t include these fields.</p>}</div>}
    </div>
    {error ? <div className="empty-state" role="alert"><h2>We couldn’t load these cards.</h2><p>{error.message}</p><Button onClick={() => window.location.reload()}>Retry</Button></div> : loading ? <div className="card-grid" aria-label="Loading cards" aria-busy="true">{Array.from({ length: 10 }, (_, index) => <div className="card-specimen" key={index}><div className="skeleton-art h-64" /><div className="h-24" /></div>)}</div> : filtered.length === 0 ? <div className="empty-state"><Search size={30} /><h2>No Cards Found</h2><p>No cards match these filters. Try a different name or show all cards.</p><Button onClick={clear}>Clear Filters</Button></div> : <>
      <div className={`card-grid${size === 'small' ? ' compact' : ''}`}>{visible.map(card => <CardTile key={card.id} card={card} onSelect={onCardSelect} />)}</div>
      <BrowsePagination page={currentPage} pages={pages} onChange={next => { setPage(next); window.scrollTo({ top: 0, behavior: 'instant' }); }} />
      <p className="page-description">{visible.length} cards shown · {filtered.length} matching cards</p>
    </>}
  </section>;
}
