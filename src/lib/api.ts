import { useState, useEffect } from 'react';

// Types for the Pokémon TCG API responses
export interface PokemonSet {
  id: string;
  name: string;
  series: string;
  printedTotal: number;
  total: number;
  legalities: {
    standard?: string;
    expanded?: string;
    unlimited?: string;
  };
  ptcgoCode?: string;
  releaseDate: string;
  updatedAt: string;
  images: {
    symbol: string;
    logo: string;
  };
}

export interface CardImage {
  small: string;
  large: string;
}

export interface CardPrice {
  low: number | null;
  mid: number | null;
  high: number | null;
  market: number | null;
  directLow: number | null;
}

export interface CardPrices {
  holofoil?: CardPrice;
  reverseHolofoil?: CardPrice;
  normal?: CardPrice;
  [key: string]: CardPrice | undefined;
}

export interface Attack {
  name: string;
  cost: string[];
  convertedEnergyCost: number;
  damage: string;
  text: string;
}

export interface PokemonCard {
  id: string;
  name: string;
  supertype: string;
  subtypes: string[];
  hp?: string;
  types?: string[];
  evolvesFrom?: string;
  evolvesTo?: string[];
  rules?: string[];
  attacks?: Attack[];
  weaknesses?: {
    type: string;
    value: string;
  }[];
  resistances?: {
    type: string;
    value: string;
  }[];
  retreatCost?: string[];
  convertedRetreatCost?: number;
  set: PokemonSet;
  number: string;
  artist?: string;
  rarity?: string;
  flavorText?: string;
  nationalPokedexNumbers?: number[];
  legalities: {
    standard?: string;
    expanded?: string;
    unlimited?: string;
  };
  images: CardImage;
  tcgplayer?: {
    url: string;
    updatedAt: string;
    prices: CardPrices;
  };
  cardmarket?: {
    url: string;
    updatedAt: string;
    prices: {
      averageSellPrice: number | null;
      lowPrice: number | null;
      trendPrice: number | null;
      [key: string]: any;
    };
  };
}

export interface CollectionCard extends PokemonCard {
  owned: boolean;
  quantity: number;
  condition: string;
  purchasePrice?: number;
  notes?: string;
}

const API_KEY = '31138e72-dced-469e-9b59-ae3b155ac955';
const BASE_URL = 'https://api.pokemontcg.io/v2';

// Helper function to make API requests
const fetchFromApi = async (endpoint: string, params: Record<string, string> = {}) => {
  const url = new URL(`${BASE_URL}/${endpoint}`);
  
  // Add query parameters
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.append(key, value);
  });
  
  try {
    const response = await fetch(url.toString(), {
      headers: {
        'X-Api-Key': API_KEY,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching from API:', error);
    throw error;
  }
};

// Hook for fetching sets with pagination and filtering
export const useSets = (page: number, pageSize: number, filters: Record<string, string> = {}) => {
  const [sets, setSets] = useState<PokemonSet[]>([]);
  const [totalSets, setTotalSets] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchSets = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Build query parameters
        const params: Record<string, string> = {
          page: page.toString(),
          pageSize: pageSize.toString(),
          orderBy: 'releaseDate',
          ...filters,
        };
        
        const response = await fetchFromApi('sets', params);
        setSets(response.data);
        setTotalSets(response.totalCount);
      } catch (error) {
        setError(error instanceof Error ? error : new Error('Unknown error occurred'));
      } finally {
        setLoading(false);
      }
    };
    
    fetchSets();
  }, [page, pageSize, JSON.stringify(filters)]);
  
  return { sets, totalSets, loading, error };
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
    
    const fetchCards = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Build query parameters
        const params: Record<string, string> = {
          page: page.toString(),
          pageSize: pageSize.toString(),
          q: `set.id:${setId}`,
          orderBy: 'number',
        };
        
        // Add additional filters if any
        Object.entries(filters).forEach(([key, value]) => {
          if (value) {
            params.q += ` ${key}:${value}`;
          }
        });
        
        const response = await fetchFromApi('cards', params);
        setCards(response.data);
        setTotalCards(response.totalCount);
      } catch (error) {
        setError(error instanceof Error ? error : new Error('Unknown error occurred'));
      } finally {
        setLoading(false);
      }
    };
    
    fetchCards();
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
    
    const fetchCard = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetchFromApi(`cards/${cardId}`);
        setCard(response.data);
      } catch (error) {
        setError(error instanceof Error ? error : new Error('Unknown error occurred'));
      } finally {
        setLoading(false);
      }
    };
    
    fetchCard();
  }, [cardId]);
  
  return { card, loading, error };
};