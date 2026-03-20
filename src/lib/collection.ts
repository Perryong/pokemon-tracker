import { useState, useEffect, useMemo } from 'react';
import { PokemonCard } from './api';

// New storage key for minimal schema (prevents breaking existing data)
const STORAGE_KEY = 'pokemon-collection-v2';

// Minimal collection state interface
interface CollectionState {
  version: 1;
  ownedCards: Record<string, boolean>;
}

// Helper function to get initial state from localStorage
const getInitialState = (): CollectionState => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.version === 1 && typeof parsed.ownedCards === 'object') {
        return parsed;
      }
    }
  } catch (e) {
    console.warn('Failed to load collection:', e);
  }
  return { version: 1, ownedCards: {} };
};

// Hook for managing the collection
export const useCollection = () => {
  const [collection, setCollection] = useState<CollectionState>(getInitialState);

  // Persist to localStorage whenever collection changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collection));
    } catch (e) {
      if (e instanceof DOMException && e.name === 'QuotaExceededError') {
        console.error('localStorage quota exceeded');
      } else {
        console.error('Failed to save collection:', e);
      }
    }
  }, [collection]);

  // Check if a card is owned
  const isOwned = (cardId: string): boolean => {
    return !!collection.ownedCards[cardId];
  };

  // Alias for backward compatibility with CardGrid.tsx
  const isInCollection = isOwned;

  // Toggle ownership of a card
  const toggleOwnership = (cardId: string): void => {
    setCollection((prev) => ({
      ...prev,
      ownedCards: {
        ...prev.ownedCards,
        [cardId]: !prev.ownedCards[cardId],
      },
    }));
  };

  // Add a card to the collection (mark as owned)
  // Accepts either cardId string or card object for backward compatibility
  const addToCollection = (cardOrId: string | PokemonCard | { id: string }): void => {
    const cardId = typeof cardOrId === 'string' ? cardOrId : cardOrId.id;
    setCollection((prev) => ({
      ...prev,
      ownedCards: {
        ...prev.ownedCards,
        [cardId]: true,
      },
    }));
  };

  // Remove a card from the collection (mark as not owned)
  const removeFromCollection = (cardId: string): void => {
    setCollection((prev) => {
      const { [cardId]: removed, ...rest } = prev.ownedCards;
      return {
        ...prev,
        ownedCards: rest,
      };
    });
  };

  return {
    ownedCards: collection.ownedCards,
    isOwned,
    isInCollection,
    toggleOwnership,
    addToCollection,
    removeFromCollection,
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