import { useState, useEffect } from 'react';
import { PokemonCard, CollectionCard } from './api';

// Collection storage key
const COLLECTION_STORAGE_KEY = 'pokemon-tcg-collection';

// Helper function to get the collection from localStorage
const getStoredCollection = (): Record<string, CollectionCard> => {
  const storedCollection = localStorage.getItem(COLLECTION_STORAGE_KEY);
  return storedCollection ? JSON.parse(storedCollection) : {};
};

// Helper function to save the collection to localStorage
const saveCollection = (collection: Record<string, CollectionCard>) => {
  localStorage.setItem(COLLECTION_STORAGE_KEY, JSON.stringify(collection));
};

// Hook for managing the collection
export const useCollection = () => {
  const [collection, setCollection] = useState<Record<string, CollectionCard>>({});
  const [isLoaded, setIsLoaded] = useState(false);

  // Load collection from localStorage on mount
  useEffect(() => {
    const storedCollection = getStoredCollection();
    setCollection(storedCollection);
    setIsLoaded(true);
  }, []);

  // Save collection to localStorage whenever it changes
  useEffect(() => {
    if (isLoaded) {
      saveCollection(collection);
    }
  }, [collection, isLoaded]);

  // Get all cards in the collection
  const getCollectionCards = (): CollectionCard[] => {
    return Object.values(collection);
  };

  // Check if a card is in the collection
  const isInCollection = (cardId: string): boolean => {
    return !!collection[cardId];
  };

  // Get a card from the collection
  const getCollectionCard = (cardId: string): CollectionCard | null => {
    return collection[cardId] || null;
  };

  // Add a card to the collection or update its information
  const addToCollection = (card: PokemonCard, quantity = 1, condition = 'Near Mint', purchasePrice = 0, notes = '') => {
    setCollection((prev) => {
      const existingCard = prev[card.id];
      
      return {
        ...prev,
        [card.id]: {
          ...card,
          owned: true,
          quantity: existingCard ? existingCard.quantity + quantity : quantity,
          condition: condition,
          purchasePrice: purchasePrice,
          notes: notes,
        },
      };
    });
  };

  // Update a card in the collection
  const updateCollectionCard = (cardId: string, updates: Partial<CollectionCard>) => {
    setCollection((prev) => {
      if (!prev[cardId]) return prev;
      
      return {
        ...prev,
        [cardId]: {
          ...prev[cardId],
          ...updates,
        },
      };
    });
  };

  // Remove a card from the collection
  const removeFromCollection = (cardId: string) => {
    setCollection((prev) => {
      const { [cardId]: removed, ...rest } = prev;
      return rest;
    });
  };

  // Calculate the total value of the collection
  const calculateCollectionValue = (): number => {
    return Object.values(collection).reduce((total, card) => {
      let cardValue = 0;
      
      if (card.tcgplayer?.prices) {
        // Try to get the market price based on rarity or availability
        const prices = card.tcgplayer.prices;
        if (prices.holofoil?.market) {
          cardValue = prices.holofoil.market;
        } else if (prices.reverseHolofoil?.market) {
          cardValue = prices.reverseHolofoil.market;
        } else if (prices.normal?.market) {
          cardValue = prices.normal.market;
        } else {
          // Fallback to the first available market price
          for (const priceType in prices) {
            if (prices[priceType]?.market) {
              cardValue = prices[priceType]!.market!;
              break;
            }
          }
        }
      }
      
      return total + (cardValue * card.quantity);
    }, 0);
  };

  return {
    collection,
    getCollectionCards,
    isInCollection,
    getCollectionCard,
    addToCollection,
    updateCollectionCard,
    removeFromCollection,
    calculateCollectionValue,
  };
};