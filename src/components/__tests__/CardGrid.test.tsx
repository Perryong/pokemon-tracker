import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { useSetCompletion, CompletionStats } from '@/lib/collection';
import CardGrid from '../CardGrid';
import { PokemonSet, PokemonCard } from '@/lib/api';
import * as apiModule from '@/lib/api';
import * as collectionModule from '@/lib/collection';

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

describe('CardGrid Quantity Controls Tests', () => {
  let mockIncrementQuantity: ReturnType<typeof vi.fn>;
  let mockDecrementQuantity: ReturnType<typeof vi.fn>;
  let mockGetQuantity: ReturnType<typeof vi.fn>;
  let mockAddToCollection: ReturnType<typeof vi.fn>;
  let mockRemoveFromCollection: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Mock quantity functions
    mockIncrementQuantity = vi.fn();
    mockDecrementQuantity = vi.fn();
    mockGetQuantity = vi.fn((cardId: string) => {
      // Default quantities for testing
      if (cardId === 'base1-1') return 2;
      if (cardId === 'base1-2') return 0;
      if (cardId === 'base1-3') return 1;
      return 0;
    });
    mockAddToCollection = vi.fn();
    mockRemoveFromCollection = vi.fn();

    // Mock useCollection hook
    vi.spyOn(collectionModule, 'useCollection').mockReturnValue({
      ownedCards: { 'base1-1': true, 'base1-3': true },
      isOwned: (cardId: string) => cardId === 'base1-1' || cardId === 'base1-3',
      isInCollection: (cardId: string) => cardId === 'base1-1' || cardId === 'base1-3',
      toggleOwnership: vi.fn(),
      addToCollection: mockAddToCollection,
      removeFromCollection: mockRemoveFromCollection,
      getQuantity: mockGetQuantity,
      setQuantity: vi.fn(),
      incrementQuantity: mockIncrementQuantity,
      decrementQuantity: mockDecrementQuantity,
      cardQuantities: { 'base1-1': 2, 'base1-3': 1 },
    });

    // Mock useCards API hook
    vi.spyOn(apiModule, 'useCards').mockReturnValue({
      cards: mockCards,
      totalCards: 3,
      loading: false,
      error: null,
    });

    // Mock toast
    vi.mock('@/hooks/use-toast', () => ({
      useToast: () => ({
        toast: vi.fn(),
      }),
    }));
  });

  it('clicking + button calls incrementQuantity', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    // Wait for cards to render
    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    // Find all + buttons (should have aria-label="Increase quantity")
    const plusButtons = screen.getAllByLabelText('Increase quantity');
    expect(plusButtons.length).toBeGreaterThan(0);

    // Click the first + button
    fireEvent.click(plusButtons[0]);

    // Verify incrementQuantity was called
    expect(mockIncrementQuantity).toHaveBeenCalledTimes(1);
  });

  it('clicking - button calls decrementQuantity', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    // Find all - buttons
    const minusButtons = screen.getAllByLabelText('Decrease quantity');
    expect(minusButtons.length).toBeGreaterThan(0);

    // Click the first - button
    fireEvent.click(minusButtons[0]);

    expect(mockDecrementQuantity).toHaveBeenCalledTimes(1);
  });

  it('- button is disabled when quantity is 0', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Blastoise')).toBeInTheDocument();
    });

    // Blastoise has qty=0, so its - button should be disabled
    const minusButtons = screen.getAllByLabelText('Decrease quantity');
    
    // Find the button for card with qty=0 (Blastoise is second card)
    const blastoiseMinusButton = minusButtons[1];
    expect(blastoiseMinusButton).toBeDisabled();
  });

  it('quantity badge displays current quantity', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Alakazam')).toBeInTheDocument();
    });

    // Check that badges with "2" and "1" exist (from our mock quantities)
    const quantityBadges = screen.getAllByText('2');
    expect(quantityBadges.length).toBeGreaterThan(0);
    
    const qtyOneBadges = screen.getAllByText('1');
    expect(qtyOneBadges.length).toBeGreaterThan(0);
  });

  it('footer shows Total Qty metric', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Total Qty:')).toBeInTheDocument();
    });

    // Verify the footer stat is visible
    expect(screen.getByText('Total Qty:')).toBeInTheDocument();
  });

  it('fast toggle still works (add sets qty to 1)', async () => {
    const onBackClick = vi.fn();
    const onCardSelect = vi.fn();

    render(
      <CardGrid
        selectedSet={mockSet}
        onBackClick={onBackClick}
        onCardSelect={onCardSelect}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Blastoise')).toBeInTheDocument();
    });

    // Find the Add button for Blastoise (not owned)
    const addButtons = screen.getAllByRole('button', { name: /Add/i });
    expect(addButtons.length).toBeGreaterThan(0);

    fireEvent.click(addButtons[0]);

    expect(mockAddToCollection).toHaveBeenCalledTimes(1);
  });
});
