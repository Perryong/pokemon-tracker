import { useState, useEffect } from 'react';
import { fetchAllSets, fetchAllSeries, fetchSetWithCards } from './tcgdex';
import { 
  PokemonSet, 
  PokemonCard, 
  CardImage, 
  Series,
  normalizeTCGSet, 
  normalizeTCGCard, 
  normalizeTCGSeries 
} from './types';

// Re-export types for backward compatibility
export type { PokemonSet, PokemonCard, CardImage, Series };

// Helper function to apply client-side filters to sets
const applySetFilters = (sets: PokemonSet[], filters: Record<string, string>): PokemonSet[] => {
  return sets.filter(set => {
    // Handle legality filters
    if (filters['legalities.standard'] === 'legal' && set.legalities.standard !== 'legal') {
      return false;
    }
    if (filters['legalities.expanded'] === 'legal' && set.legalities.expanded !== 'legal') {
      return false;
    }
    
    // Handle release date range filters
    if (filters['releaseDate']) {
      const dateFilter = filters['releaseDate'];
      if (!set.releaseDate) {
        return false;
      }
      
      const setDate = new Date(set.releaseDate);
      if (Number.isNaN(setDate.getTime())) {
        return false;
      }
      
      // Parse gte/lte format: "gte2020/01/01 lte2023/12/31"
      const gteMatch = dateFilter.match(/gte(\d{4}\/\d{2}\/\d{2})/);
      const lteMatch = dateFilter.match(/lte(\d{4}\/\d{2}\/\d{2})/);
      
      if (gteMatch) {
        const minDate = new Date(gteMatch[1]);
        if (setDate < minDate) return false;
      }
      if (lteMatch) {
        const maxDate = new Date(lteMatch[1]);
        if (setDate > maxDate) return false;
      }
    }
    
    return true;
  });
};

// Hook for fetching sets with pagination and filtering
export const useSets = (page: number, pageSize: number, filters: Record<string, string> = {}) => {
  const [sets, setSets] = useState<PokemonSet[]>([]);
  const [totalSets, setTotalSets] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    
    const fetchSets = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch all sets from TCGdex
        const allSets = await fetchAllSets();
        
        if (cancelled) return;
        
        // Normalize to app types
        const normalizedSets = allSets.map(normalizeTCGSet);
        
        // Apply filters
        const filteredSets = applySetFilters(normalizedSets, filters);
        
        // Sort by release date (newest first)
        filteredSets.sort((a, b) => {
          const dateA = new Date(a.releaseDate || '1900-01-01');
          const dateB = new Date(b.releaseDate || '1900-01-01');
          return dateB.getTime() - dateA.getTime();
        });
        
        // Apply pagination
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedSets = filteredSets.slice(startIndex, endIndex);
        
        if (!cancelled) {
          setSets(paginatedSets);
          setTotalSets(filteredSets.length);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error : new Error('Unknown error occurred'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchSets();
    
    return () => {
      cancelled = true;
    };
  }, [page, pageSize, JSON.stringify(filters)]);
  
  return { sets, totalSets, loading, error };
};

// Helper function to apply client-side filters to cards
const applyCardFilters = (cards: PokemonCard[], filters: Record<string, string>): PokemonCard[] => {
  return cards.filter(card => {
    // Handle type filter
    if (filters['types'] && (!card.types || !card.types.includes(filters['types']))) {
      return false;
    }
    
    // Handle subtype filter
    if (filters['subtypes'] && (!card.subtypes || !card.subtypes.includes(filters['subtypes']))) {
      return false;
    }
    
    // Handle rarity filter
    if (filters['rarity'] && card.rarity !== filters['rarity']) {
      return false;
    }
    
    return true;
  });
};

// Hook for fetching cards from a specific set with filtering
export const useCards = (setId: string | null, page: number, pageSize: number, filters: Record<string, string> = {}) => {
  const [cards, setCards] = useState<PokemonCard[]>([]);
  const [totalCards, setTotalCards] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!setId) {
      setCards([]);
      setTotalCards(0);
      return;
    }
    
    let cancelled = false;
    
    const fetchCards = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch set with all its cards from TCGdex
        const setData = await fetchSetWithCards(setId);
        
        if (cancelled) return;
        
        // Normalize cards with set data
        const normalizedCards = (setData.cards || []).map(card => 
          normalizeTCGCard(card, setData)
        );
        
        // Apply filters
        const filteredCards = applyCardFilters(normalizedCards, filters);
        
        // Sort by card number
        filteredCards.sort((a, b) => {
          const numA = parseInt(a.number) || 0;
          const numB = parseInt(b.number) || 0;
          return numA - numB;
        });
        
        // Apply pagination
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedCards = filteredCards.slice(startIndex, endIndex);
        
        if (!cancelled) {
          setCards(paginatedCards);
          setTotalCards(filteredCards.length);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error : new Error('Unknown error occurred'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchCards();
    
    return () => {
      cancelled = true;
    };
  }, [setId, page, pageSize, JSON.stringify(filters)]);
  
  return { cards, totalCards, loading, error };
};

// Hook for fetching a single card by ID
export const useCard = (cardId: string | null) => {
  const [card, setCard] = useState<PokemonCard | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!cardId) {
      setCard(null);
      return;
    }
    
    let cancelled = false;
    
    const fetchCard = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Extract set ID from card ID (format: setId-cardNumber)
        const setId = cardId.split('-')[0];
        
        // Fetch the full set with cards
        const setData = await fetchSetWithCards(setId);
        
        if (cancelled) return;
        
        // Find the specific card
        const tcgCard = setData.cards?.find(c => c.id === cardId);
        
        if (tcgCard) {
          const normalizedCard = normalizeTCGCard(tcgCard, setData);
          if (!cancelled) {
            setCard(normalizedCard);
          }
        } else {
          if (!cancelled) {
            setError(new Error('Card not found'));
          }
        }
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error : new Error('Unknown error occurred'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchCard();
    
    return () => {
      cancelled = true;
    };
  }, [cardId]);
  
  return { card, loading, error };
};

// Hook for fetching all series
export const useSeries = () => {
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    
    const fetchSeries = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch all series from TCGdex
        const allSeries = await fetchAllSeries();
        
        if (cancelled) return;
        
        // Normalize to app types
        const normalizedSeries = allSeries.map(normalizeTCGSeries);
        
        if (!cancelled) {
          setSeries(normalizedSeries);
        }
      } catch (error) {
        if (!cancelled) {
          setError(error instanceof Error ? error : new Error('Unknown error occurred'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchSeries();
    
    return () => {
      cancelled = true;
    };
  }, []);
  
  return { series, loading, error };
};
