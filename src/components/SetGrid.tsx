import { useMemo, useState } from 'react';
import { ArrowUpRight, Layers, Search } from 'lucide-react';
import { PokemonSet, useSets, useSeries } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import BrowsePagination from './BrowsePagination';
import SetArtwork from './SetArtwork';

export default function SetGrid({ onSetSelect }: { onSetSelect: (set: PokemonSet) => void }) {
  const [page, setPage] = useState(1);
  const [seriesFilter, setSeriesFilter] = useState('');
  const [search, setSearch] = useState('');
  const [legality, setLegality] = useState('');
  const [datesOpen, setDatesOpen] = useState(false);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const filters: Record<string, string> = {};
  if (seriesFilter) filters.series = seriesFilter;
  if (search.trim()) filters.name = search.trim();
  if (legality) filters[`legalities.${legality}`] = 'legal';
  if (start || end) filters.releaseDate = `${start ? `gte${start.replace(/-/g, '/')}` : ''} ${end ? `lte${end.replace(/-/g, '/')}` : ''}`;
  const { sets, totalSets, loading, error } = useSets(page, 18, filters);
  const { series } = useSeries();
  const { cardQuantities } = useCollection();
  const counts = useMemo(() => {
    const result: Record<string, { owned: number; quantity: number }> = {};
    for (const [id, quantity] of Object.entries(cardQuantities)) {
      if (quantity <= 0) continue;
      const setId = id.slice(0, id.lastIndexOf('-'));
      result[setId] ||= { owned: 0, quantity: 0 };
      result[setId].owned++; result[setId].quantity += quantity;
    }
    return result;
  }, [cardQuantities]);
  const visible = sets.filter(set => set.name.toLowerCase().includes(search.toLowerCase().trim()));
  const clear = () => { setSeriesFilter(''); setSearch(''); setLegality(''); setStart(''); setEnd(''); setPage(1); };
  const chooseSeries = (id: string) => { setSeriesFilter(id); setPage(1); };
  const active = seriesFilter || search || legality || start || end;
  return <section className="page">
    <header className="page-heading"><div><h1>Pokémon TCG Sets</h1><p className="page-description">Explore the eras. Build your collection, one card at a time.</p></div><span className="result-count"><Layers size={15} />{loading ? 'Finding sets…' : <><strong>{totalSets}</strong> sets to explore</>}</span></header>
    <div className="filter-tray">
      <div className="filter-field grow"><label htmlFor="set-search">Find a set</label><div className="search-control"><Search size={16} /><input id="set-search" className="control" type="search" placeholder="Search sets..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} /></div></div>
      <div className="filter-field"><label htmlFor="series">Series</label><select id="series" className="control" value={seriesFilter} onChange={e => chooseSeries(e.target.value)}><option value="">All Series</option>{series.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
      <div className="filter-field"><label htmlFor="legality">Format</label><select id="legality" className="control" value={legality} onChange={e => { setLegality(e.target.value); setPage(1); }}><option value="">All Sets</option><option value="standard">Standard Legal</option><option value="expanded">Expanded Legal</option></select></div>
      <Button variant="outline" className="h-[42px]" onClick={() => setDatesOpen(!datesOpen)} aria-expanded={datesOpen}>Release Date Range</Button>
      {active && <Button variant="ghost" onClick={clear}>Clear Filters</Button>}
      {datesOpen && <div className="flex flex-wrap gap-3 w-full"><div className="filter-field"><label htmlFor="release-start">Released from</label><input id="release-start" type="date" className="control" value={start} onChange={e => { setStart(e.target.value); setPage(1); }} /></div><div className="filter-field"><label htmlFor="release-end">Released before</label><input id="release-end" type="date" className="control" value={end} min={start} onChange={e => { setEnd(e.target.value); setPage(1); }} /></div><p className="page-description">Some set summaries do not include release dates or format legality.</p></div>}
    </div>
    <div className="quick-series" aria-label="Quick series"><button className={`series-chip${!seriesFilter ? ' selected' : ''}`} onClick={() => chooseSeries('')} aria-pressed={!seriesFilter}>All eras</button>{series.filter(item => ['base', 'neo', 'swsh', 'sv', 'me'].includes(item.id)).map(item => <button key={item.id} className={`series-chip${seriesFilter === item.id ? ' selected' : ''}`} aria-pressed={seriesFilter === item.id} onClick={() => chooseSeries(item.id)}>{item.name}</button>)}</div>
    {error ? <div className="empty-state" role="alert"><h2>We couldn’t load these sets.</h2><p>{error.message}</p><Button onClick={() => window.location.reload()}>Retry</Button></div> : loading ? <div className="set-grid" aria-label="Loading sets" aria-busy="true">{Array.from({ length: 6 }, (_, index) => <div className="set-specimen" key={index}><div className="skeleton-art" /><div className="set-information h-28" /></div>)}</div> : visible.length === 0 ? <div className="empty-state"><Layers size={32} /><h2>No Sets Found</h2><p>Try another series or clear the filters to explore every set.</p><Button onClick={clear}>Clear Filters</Button></div> : <>
      <div className="set-grid">{visible.map(set => {
        const count = counts[set.id] || { owned: 0, quantity: 0 };
        const completion = set.total ? Math.min(100, count.owned / set.total * 100) : 0;
        return <article className="set-specimen" key={set.id}><button type="button" className="set-open" onClick={() => onSetSelect(set)}><div className="set-art"><span className="set-index">{set.id}</span><SetArtwork set={set} /></div><div className="set-information"><div className="set-title-row"><h3>{set.name}</h3><ArrowUpRight size={17} /></div><p className="set-meta">{set.total} cards{set.series !== 'Unknown' ? ` · ${set.series}` : ''}{set.releaseDate ? ` · ${new Date(set.releaseDate).getFullYear()}` : ''}</p></div></button><div className="set-progress"><div className="progress-line"><span>Owned {count.owned} / {set.total}</span><span>{completion.toFixed(0)}%</span></div><Progress value={completion} className="h-1" aria-label={`Owned ${count.owned} of ${set.total} cards in ${set.name}`} />{count.quantity > count.owned && <p className="set-meta">Total Qty: {count.quantity}</p>}</div></article>;
      })}</div>
      <BrowsePagination page={page} pages={Math.ceil(totalSets / 18)} onChange={next => { setPage(next); window.scrollTo({ top: 0, behavior: 'instant' }); }} />
    </>}
  </section>;
}
