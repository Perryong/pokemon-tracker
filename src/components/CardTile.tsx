import { useState } from 'react';
import { toast } from '@/hooks/use-toast';
import { Check, Minus, Plus } from 'lucide-react';
import { PokemonCard } from '@/lib/types';
import { useCollection } from '@/lib/collection';
export default function CardTile({ card, onSelect }: { card: PokemonCard; onSelect?: (card: PokemonCard) => void }) {
  const { getQuantity, incrementQuantity, decrementQuantity, addToCollection, removeFromCollection } = useCollection();
  const [imageFailed, setImageFailed] = useState(false);
  const save = (action: () => void) => { try { action(); } catch { toast({ title: 'Could not save your collection', description: 'Device storage may be full or unavailable. Your saved cards are unchanged.', variant: 'destructive' }); } };
  const quantity = getQuantity(card.id);
  return <article className={`group overflow-hidden card-specimen${quantity ? ' owned' : ''}`}>
    <button type="button" className="card-art-button" onClick={() => onSelect?.(card)} aria-label={`View ${card.name}`}>
      {card.images.small && !imageFailed ? <img src={card.images.small} alt={card.name} loading="lazy" decoding="async" onError={() => setImageFailed(true)} /> : <div className="card-placeholder">No image</div>}
      {quantity > 0 && <span className="owned-tag"><Check size={10} />Owned</span>}
    </button>
    <button type="button" className="card-information w-full text-left" onClick={() => onSelect?.(card)}><h3>{card.name}</h3><p className="card-number">{card.number} / {card.set.printedTotal || '—'}</p></button>
    <div className="quantity-actions">
      <button type="button" className="collection-toggle" onClick={() => save(() => quantity ? removeFromCollection(card.id) : addToCollection(card.id))}>{quantity ? <><Check size={12} />Remove</> : <><Plus size={12} />Add</>}</button>
      <div className="quantity-stepper"><button type="button" aria-label="Decrease quantity" disabled={quantity === 0} onClick={() => save(() => decrementQuantity(card.id))}><Minus size={12} /></button><output aria-label={`Quantity: ${quantity}`}>{quantity}</output><button type="button" aria-label="Increase quantity" disabled={quantity >= 999} onClick={() => save(() => incrementQuantity(card.id))}><Plus size={12} /></button></div>
    </div>
  </article>;
}
