import { useState } from 'react';
import { PokemonSet } from '@/lib/types';

export default function SetArtwork({ set }: { set: PokemonSet }) {
  // TCGdex's Wizards Promos artwork returns 404; use the verified Pokémon TCG API logo.
  const sources = [...new Set([set.id === 'basep' ? 'https://images.pokemontcg.io/basep/logo.png' : '', set.images.logo, set.images.symbol].filter(Boolean))];
  const [attempt, setAttempt] = useState(0);
  const source = sources[attempt];
  return source ? <img src={source} alt={`${set.name} ${attempt ? 'symbol' : 'logo'}`} loading="lazy" decoding="async" onError={() => setAttempt(previous => previous + 1)} /> : <div className="catalogue-emblem" aria-label={`${set.name} catalogue emblem`}><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="48" fill="none" stroke="currentColor" strokeWidth="2"/><circle cx="60" cy="60" r="40" fill="none" stroke="currentColor" strokeWidth=".5"/><text x="60" y="72" textAnchor="middle" fill="currentColor" fontFamily="Georgia, serif" fontSize="34">{set.id === 'wp' ? 'W' : set.name.split(' ').map(word => word[0]).slice(0, 3).join('')}</text></svg><span>Catalogue emblem</span></div>;
}
