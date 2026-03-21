import { useState, useEffect, useMemo, useCallback } from 'react';
import { PokemonCard } from './api';
import { CollectionStateV3, STORAGE_KEY } from './collection-types';
import { getInitialState, clearBackup } from './migration';

// Hook for managing the collection
export const useCollection = () => {
  const [collection, setCollection] = useState<CollectionStateV3>(getInitialState);

  // Persist to localStorage whenever collection changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collection));
      // Clear backup after successful save (migration complete)
      clearBackup();
    } catch (e) {
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        console.error('localStorage quota exceeded');
      } else {
        console.error('Failed to save collection:', e);
      }
    }
  }, [collection]);

  // Core quantity operations with sparse storage
  const setQuantity = useCallback((cardId: string, quantity: number): void => {
    setCollection(prev => {
      const newQuantities = { ...prev.cardQuantities };
      const clamped = Math.max(0, Math.min(999, Math.floor(quantity)));
      
      if (clamped === 0) {
        delete newQuantities[cardId]; // Sparse
      } else {
        newQuantities[cardId] = clamped;
      }
      
      return { ...prev, cardQuantities: newQuantities };
    });
  }, []);

  const getQuantity = useCallback((cardId: string): number => {
    return collection.cardQuantities[cardId] || 0;
  }, [collection.cardQuantities]);

  // Derived ownership (single source of truth: qty > 0)
  const isOwned = useCallback((cardId: string): boolean => {
    return !!collection.cardQuantities[cardId];
  }, [collection.cardQuantities]);

  // Backward-compatible derived ownedCards
  const ownedCards = useMemo(() => {
    const derived: Record<string, boolean> = {};
    Object.keys(collection.cardQuantities).forEach(id => {
      derived[id] = true;
    });
    return derived;
  }, [collection.cardQuantities]);

  // Compatibility wrappers
  const toggleOwnership = useCallback((cardId: string): void => {
    setCollection(prev => {
      const current = prev.cardQuantities[cardId] || 0;
      const newQuantities = { ...prev.cardQuantities };
      if (current > 0) {
        delete newQuantities[cardId]; // Toggle off: sparse delete
      } else {
        newQuantities[cardId] = 1; // Toggle on
      }
      return { ...prev, cardQuantities: newQuantities };
    });
  }, []);

  const addToCollection = useCallback((cardOrId: string | PokemonCard | { id: string }): void => {
    const cardId = typeof cardOrId === 'string' ? cardOrId : cardOrId.id;
    setCollection(prev => {
      if (prev.cardQuantities[cardId]) return prev; // Already owned, no-op
      return {
        ...prev,
        cardQuantities: { ...prev.cardQuantities, [cardId]: 1 }
      };
    });
  }, []);

  const removeFromCollection = useCallback((cardId: string): void => {
    setCollection(prev => {
      const { [cardId]: _, ...rest } = prev.cardQuantities;
      return { ...prev, cardQuantities: rest };
    });
  }, []);

  // New quantity APIs for Phase 5
  const incrementQuantity = useCallback((cardId: string): void => {
    setCollection(prev => {
      const current = prev.cardQuantities[cardId] || 0;
      if (current >= 999) return prev;
      return {
        ...prev,
        cardQuantities: { ...prev.cardQuantities, [cardId]: current + 1 }
      };
    });
  }, []);

  const decrementQuantity = useCallback((cardId: string): void => {
    setCollection(prev => {
      const current = prev.cardQuantities[cardId] || 0;
      if (current <= 0) return prev;
      const newQty = current - 1;
      const newQuantities = { ...prev.cardQuantities };
      if (newQty === 0) {
        delete newQuantities[cardId]; // Sparse
      } else {
        newQuantities[cardId] = newQty;
      }
      return { ...prev, cardQuantities: newQuantities };
    });
  }, []);

  return {
    // Backward-compatible API
    ownedCards,
    isOwned,
    isInCollection: isOwned,
    toggleOwnership,
    addToCollection,
    removeFromCollection,
    
    // New quantity API
    getQuantity,
    setQuantity,
    incrementQuantity,
    decrementQuantity,
    cardQuantities: collection.cardQuantities, // Direct access for Phase 5
  };
};

// Completion statistics interface
export interface CompletionStats {
  owned: number;
  missing: number;
  total: number;
  percentage: number;
}

// Hook for computing set completion statistics
export function useSetCompletion(
  setCardIds: string[],
  ownedCards: Record<string, boolean>
): CompletionStats {
  return useMemo(() => {
    const total = setCardIds.length;
    if (total === 0) {
      return { owned: 0, missing: 0, total: 0, percentage: 0 };
    }
    
    const owned = setCardIds.filter(id => ownedCards[id]).length;
    const missing = total - owned;
    const percentage = (owned / total) * 100;
    
    return { owned, missing, total, percentage };
  }, [setCardIds, ownedCards]);
}