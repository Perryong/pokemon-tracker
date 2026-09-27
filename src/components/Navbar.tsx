import { useTheme } from 'next-themes';
import { useCollection } from '@/lib/collection';
import { BookOpen, Layers, Moon, Sun, CircleDot, ArrowUpRight } from 'lucide-react';

interface NavbarProps {
  view: 'sets' | 'cards' | 'collection';
  onSetSelectView: (view: 'sets' | 'cards' | 'collection') => void;
}
export default function Navbar({ view, onSetSelectView }: NavbarProps) {
  const { resolvedTheme, setTheme } = useTheme();
  const { cardQuantities } = useCollection();
  const unique = Object.keys(cardQuantities).length;
  const quantity = Object.values(cardQuantities).reduce((sum, value) => sum + value, 0);
  return <aside className="library-rail">
    <button type="button" className="wordmark" onClick={() => onSetSelectView('sets')} aria-label="Pokémon tracker home">
      <CircleDot size={31} strokeWidth={1.6} /><span>Pokémon<span className="wordmark-caption">Collection tracker</span></span>
    </button>
    <nav aria-label="Main" className="library-nav">
      <button type="button" className={view !== 'collection' ? 'nav-item is-active' : 'nav-item'} aria-current={view !== 'collection' ? 'page' : undefined} onClick={() => onSetSelectView('sets')}><Layers size={19} /><span>Sets</span><span className="nav-hint">Explore</span></button>
      <button type="button" className={view === 'collection' ? 'nav-item is-active' : 'nav-item'} aria-current={view === 'collection' ? 'page' : undefined} onClick={() => onSetSelectView('collection')}><BookOpen size={19} /><span>My Collection</span>{unique > 0 && <span className="nav-count">{unique}</span>}</button>
    </nav>
    <div className="binder-note"><BookOpen size={23} strokeWidth={1.5} /><h2>Your binder, at a glance.</h2><p><strong>{unique}</strong> unique cards<br /><strong>{quantity}</strong> total copies</p><span className="save-indicator"><span />Saved on this device</span></div>
    <div className="rail-bottom">
      <button type="button" className="theme-button" aria-label="Toggle theme" onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}>{resolvedTheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}<span>{resolvedTheme === 'dark' ? 'Light appearance' : 'Dark appearance'}</span></button>
      <a className="source-link" href="https://tcgdex.dev" target="_blank" rel="noreferrer">Card data by TCGdex <ArrowUpRight size={14} /></a>
    </div>
  </aside>;
}
