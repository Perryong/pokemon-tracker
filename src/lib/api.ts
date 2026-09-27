import { useState, useEffect } from 'react';
import { fetchAllSets, fetchAllSeries, fetchSetWithCards, fetchCardDetails, fetchSeriesWithSets } from './tcgdex';
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
    if (filters.name && !set.name.toLowerCase().includes(filters.name.toLowerCase())) return false;
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
  const seriesId = filters.series;
  const [sets, setSets] = useState<PokemonSet[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    
    const fetchSets = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Fetch all sets from TCGdex
        const selectedSeries = seriesId ? await fetchSeriesWithSets(seriesId) : null;
        const allSets = selectedSeries ? selectedSeries.sets : await fetchAllSets();
        
        if (cancelled) return;
        
        // Normalize to app types
        const normalizedSets = allSets.map(set => ({
          ...normalizeTCGSet(set),
          ...(selectedSeries ? { series: selectedSeries.name } : {}),
        }));
        
        // Sort by release date (newest first)
        normalizedSets.sort((a, b) => {
          const dateA = new Date(a.releaseDate || '1900-01-01');
          const dateB = new Date(b.releaseDate || '1900-01-01');
          return dateB.getTime() - dateA.getTime();
        });
        
        if (!cancelled) {
          setSets(normalizedSets);
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
  }, [seriesId]);
  
  const filteredSets = applySetFilters(sets, filters);
  return { sets: filteredSets.slice((page - 1) * pageSize, page * pageSize), totalSets: filteredSets.length, loading, error };
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
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!setId) {
      setCards([]);
      setLoading(false);
      setError(null);
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
        
        // Sort by card number
        normalizedCards.sort((a, b) => {
          const numA = parseInt(a.number) || 0;
          const numB = parseInt(b.number) || 0;
          return numA - numB;
        });
        
        if (!cancelled) {
          setCards(normalizedCards);
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
  }, [setId]);
  
  const filteredCards = applyCardFilters(cards, filters);
  return { cards: filteredCards.slice((page - 1) * pageSize, page * pageSize), totalCards: filteredCards.length, loading, error };
};

// Hook for fetching a single card by ID
export const useCard = (cardId: string | null) => {
  const [card, setCard] = useState<PokemonCard | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!cardId) {
      setCard(null);
      setLoading(false);
      setError(null);
      return;
    }
    
    let cancelled = false;
    
    const fetchCard = async () => {
      setCard(null);
      setLoading(true);
      setError(null);
      
      try {
        const tcgCard = await fetchCardDetails(cardId);
        const normalized = normalizeTCGCard(tcgCard);
        if (!cancelled) { setCard(normalized); setLoading(false); }
        // Enrich prices without blocking card information or discarding TCGdex fallback.
        try {
          const response = await fetch(`/api/cardmarket/${encodeURIComponent(cardId)}`, { signal: AbortSignal.timeout(10000) });
          if (response.ok) {
            const data = await response.json();
            const quotes = Array.isArray(data.quotes) ? data.quotes.filter((quote: NonNullable<PokemonCard['marketPrices']>[number]) => quote?.provider === 'cardmarket' && quote.currency === 'EUR' && quote.source === 'pokemontcgapi.com' && typeof quote.values === 'object' && quote.values !== null && Object.values(quote.values).every(value => typeof value === 'number' && Number.isFinite(value) && value >= 0)) : [];
            if (!cancelled && quotes.length) setCard({ ...normalized, marketPrices: [...(normalized.marketPrices || []).filter(quote => quote.provider !== 'cardmarket'), ...quotes] });
          }
        } catch { /* Keep the existing prices when the additional source is unavailable. */ }
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
