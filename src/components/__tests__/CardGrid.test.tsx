import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { useSetCompletion, CompletionStats } from '@/lib/collection';
import CardGrid from '../CardGrid';
import { PokemonSet, PokemonCard } from '@/lib/api';
import * as apiModule from '@/lib/api';
import * as collectionModule from '@/lib/collection';

const toastMock = vi.fn();

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

describe('Stats Calculation Tests', () => {
  it('useSetCompletion returns correct owned/missing/total/percentage for partial ownership', () => {
    const setCardIds = ['card-1', 'card-2', 'card-3'];
    const ownedCards = { 'card-1': true };

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(1);
    expect(stats.missing).toBe(2);
    expect(stats.total).toBe(3);
    expect(stats.percentage).toBeCloseTo(33.33, 2);
  });

  it('useSetCompletion returns 0% for empty ownedCards', () => {
    const setCardIds = ['card-1', 'card-2', 'card-3'];
    const ownedCards = {};

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(0);
    expect(stats.missing).toBe(3);
    expect(stats.total).toBe(3);
    expect(stats.percentage).toBe(0);
  });

  it('useSetCompletion returns 100% when all cards owned', () => {
    const setCardIds = ['card-1', 'card-2', 'card-3'];
    const ownedCards = {
      'card-1': true,
      'card-2': true,
      'card-3': true,
    };

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(3);
    expect(stats.missing).toBe(0);
    expect(stats.total).toBe(3);
    expect(stats.percentage).toBe(100);
  });

  it('useSetCompletion handles empty setCardIds array (0 total, 0%)', () => {
    const setCardIds: string[] = [];
    const ownedCards = { 'card-1': true };

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(0);
    expect(stats.missing).toBe(0);
    expect(stats.total).toBe(0);
    expect(stats.percentage).toBe(0);
  });

  it('useSetCompletion percentage is precise (not truncated)', () => {
    const setCardIds = ['card-1', 'card-2', 'card-3', 'card-4', 'card-5', 'card-6'];
    const ownedCards = { 'card-1': true, 'card-2': true };

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(2);
    expect(stats.missing).toBe(4);
    expect(stats.total).toBe(6);
    // (2/6)*100 = 33.333...
    expect(stats.percentage).toBeCloseTo(33.333333, 5);
  });

  it('useSetCompletion ignores owned cards not in the set', () => {
    const setCardIds = ['card-1', 'card-2', 'card-3'];
    const ownedCards = {
      'card-1': true,
      'card-99': true, // Not in this set
      'other-card': true, // Not in this set
    };

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(1); // Only card-1 from the set
    expect(stats.missing).toBe(2);
    expect(stats.total).toBe(3);
    expect(stats.percentage).toBeCloseTo(33.33, 2);
  });

  it('useSetCompletion handles large numbers correctly', () => {
    // Create a set with 150 cards
    const setCardIds = Array.from({ length: 150 }, (_, i) => `card-${i}`);
    // Own 100 of them
    const ownedCards = Array.from({ length: 100 }, (_, i) => `card-${i}`).reduce(
      (acc, id) => ({ ...acc, [id]: true }),
      {}
    );

    const { result } = renderHook(() => useSetCompletion(setCardIds, ownedCards));

    const stats: CompletionStats = result.current;
    expect(stats.owned).toBe(100);
    expect(stats.missing).toBe(50);
    expect(stats.total).toBe(150);
    expect(stats.percentage).toBeCloseTo(66.666667, 5);
  });
});

// Mock data for CardGrid tests
const mockSet: PokemonSet = {
  id: 'base1',
  name: 'Base Set',
  series: 'Base',
  printedTotal: 102,
  total: 102,
  releaseDate: '1999-01-09',
  images: { symbol: '', logo: '' },
  legalities: { unlimited: 'Legal' },
};

const mockCards: PokemonCard[] = [
  {
    id: 'base1-1',
    name: 'Alakazam',
    number: '1',
    images: { small: 'test-img-1.jpg', large: 'test-img-1-lg.jpg' },
    set: mockSet,
    hp: '80',
    types: ['Psychic'],
  },
  {
    id: 'base1-2',
    name: 'Blastoise',
    number: '2',
    images: { small: 'test-img-2.jpg', large: 'test-img-2-lg.jpg' },
    set: mockSet,
    hp: '100',
    types: ['Water'],
  },
  {
    id: 'base1-3',
    name: 'Chansey',
    number: '3',
    images: { small: 'test-img-3.jpg', large: 'test-img-3-lg.jpg' },
    set: mockSet,
    hp: '120',
    types: ['Colorless'],
  },
];

const createCollectionMock = (quantities: Record<string, number>) => {
  const getQuantity = vi.fn((cardId: string) => quantities[cardId] ?? 0);
  const isOwned = (cardId: string) => (quantities[cardId] ?? 0) > 0;

  return {
    ownedCards: Object.fromEntries(
      Object.entries(quantities)
        .filter(([, qty]) => qty > 0)
        .map(([id]) => [id, true])
    ),
    isOwned,
    isInCollection: isOwned,
    toggleOwnership: vi.fn(),
    addToCollection: vi.fn().mockResolvedValue(undefined),
    removeFromCollection: vi.fn().mockResolvedValue(undefined),
    getQuantity,
    setQuantity: vi.fn(),
    incrementQuantity: vi.fn(),
    decrementQuantity: vi.fn(),
    cardQuantities: Object.fromEntries(
      Object.entries(quantities).filter(([, qty]) => qty > 0)
    ),
  };
};

describe('CardGrid Quantity Controls Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(apiModule, 'useCards').mockReturnValue({
      cards: mockCards,
      totalCards: 3,
      loading: false,
      error: null,
    });
  });

  it('clicking + button calls incrementQuantity for the correct card', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    const alakazamCard = screen.getByText('Alakazam').closest('[class*="group overflow-hidden"]');
    expect(alakazamCard).not.toBeNull();

    const increaseButton = within(alakazamCard as HTMLElement).getByLabelText('Increase quantity');
    fireEvent.click(increaseButton);

    expect(collectionMock.incrementQuantity).toHaveBeenCalledWith('base1-1');
    expect(collectionMock.incrementQuantity).toHaveBeenCalledTimes(1);
  });

  it('clicking - button calls decrementQuantity for the correct card', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Chansey')).toBeInTheDocument();
    });

    const chanseyCard = screen.getByText('Chansey').closest('[class*="group overflow-hidden"]');
    expect(chanseyCard).not.toBeNull();

    const decreaseButton = within(chanseyCard as HTMLElement).getByLabelText('Decrease quantity');
    fireEvent.click(decreaseButton);

    expect(collectionMock.decrementQuantity).toHaveBeenCalledWith('base1-3');
    expect(collectionMock.decrementQuantity).toHaveBeenCalledTimes(1);
  });

  it('- button is disabled when quantity is 0 (zero-floor control)', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Blastoise')).toBeInTheDocument();
    });

    const blastoiseCard = screen.getByText('Blastoise').closest('[class*="group overflow-hidden"]');
    expect(blastoiseCard).not.toBeNull();

    const decreaseButton = within(blastoiseCard as HTMLElement).getByLabelText('Decrease quantity');
    expect(decreaseButton).toBeDisabled();
  });

  it('quantity controls enforce upper boundary by disabling + at 999', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 999, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    const alakazamCard = screen.getByText('Alakazam').closest('[class*="group overflow-hidden"]');
    expect(alakazamCard).not.toBeNull();

    const increaseButton = within(alakazamCard as HTMLElement).getByLabelText('Increase quantity');
    expect(increaseButton).toBeDisabled();
  });

  it('fast toggle add path calls addToCollection for unowned card', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Blastoise')).toBeInTheDocument();
    });

    const blastoiseCard = screen.getByText('Blastoise').closest('[class*="group overflow-hidden"]');
    expect(blastoiseCard).not.toBeNull();

    const addButton = within(blastoiseCard as HTMLElement).getByRole('button', { name: /Add/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(collectionMock.addToCollection).toHaveBeenCalledWith('base1-2');
      expect(collectionMock.addToCollection).toHaveBeenCalledTimes(1);
    });
  });

  it('fast toggle remove path calls removeFromCollection for owned qty > 1 card', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    const alakazamCard = screen.getByText('Alakazam').closest('[class*="group overflow-hidden"]');
    expect(alakazamCard).not.toBeNull();

    const removeButton = within(alakazamCard as HTMLElement).getByRole('button', { name: /Remove/i });
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(collectionMock.removeFromCollection).toHaveBeenCalledWith('base1-1');
      expect(collectionMock.removeFromCollection).toHaveBeenCalledTimes(1);
    });
  });

  it('footer shows Total Qty metric', async () => {
    const collectionMock = createCollectionMock({ 'base1-1': 2, 'base1-2': 0, 'base1-3': 1 });
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue(collectionMock);

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Total Qty:')).toBeInTheDocument();
    });

    expect(screen.getByText('Total Qty:')).toBeInTheDocument();
  });
});
