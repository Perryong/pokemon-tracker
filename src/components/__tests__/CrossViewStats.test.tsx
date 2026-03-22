import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import CardGrid from '../CardGrid';
import SetGrid from '../SetGrid';
import CollectionView from '../CollectionView';
import CollectionStats from '../CollectionStats';
import { PokemonCard, PokemonSet } from '@/lib/api';
import * as apiModule from '@/lib/api';
import * as collectionModule from '@/lib/collection';

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return {
    ...actual,
    useSets: vi.fn(),
    useSeries: vi.fn(),
    useCards: vi.fn(),
  };
});

vi.mock('@/lib/collection', async () => {
  const actual = await vi.importActual<typeof import('@/lib/collection')>('@/lib/collection');
  return {
    ...actual,
    useCollection: vi.fn(),
  };
});

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

const selectedSet: PokemonSet = {
  id: 'testset',
  name: 'Regression Set',
  series: 'Regression',
  printedTotal: 3,
  total: 3,
  legalities: { unlimited: 'legal' },
  releaseDate: '2024-01-01',
  updatedAt: '',
  images: { symbol: '', logo: '' },
};

const cardsForSet: PokemonCard[] = [
  {
    id: 'testset-1',
    name: 'Card One',
    number: '1',
    images: { small: '1.jpg', large: '1-lg.jpg' },
    set: selectedSet,
    supertype: 'Pokémon',
    subtypes: [],
    legalities: {},
  },
  {
    id: 'testset-2',
    name: 'Card Two',
    number: '2',
    images: { small: '2.jpg', large: '2-lg.jpg' },
    set: selectedSet,
    supertype: 'Pokémon',
    subtypes: [],
    legalities: {},
  },
  {
    id: 'testset-3',
    name: 'Card Three',
    number: '3',
    images: { small: '3.jpg', large: '3-lg.jpg' },
    set: selectedSet,
    supertype: 'Pokémon',
    subtypes: [],
    legalities: {},
  },
];

describe('Cross-view quantity semantics regression', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    const cardQuantities = {
      'testset-1': 2,
      'testset-2': 1,
      'other-set-1': 3,
    };

    const isOwned = (cardId: string) => (cardQuantities[cardId as keyof typeof cardQuantities] ?? 0) > 0;
    const getQuantity = (cardId: string) => cardQuantities[cardId as keyof typeof cardQuantities] ?? 0;

    vi.spyOn(collectionModule, 'useCollection').mockReturnValue({
      ownedCards: {
        'testset-1': true,
        'testset-2': true,
        'other-set-1': true,
      },
      cardQuantities,
      isOwned,
      isInCollection: isOwned,
      toggleOwnership: vi.fn(),
      addToCollection: vi.fn(),
      removeFromCollection: vi.fn(),
      getQuantity,
      setQuantity: vi.fn(),
      incrementQuantity: vi.fn(),
      decrementQuantity: vi.fn(),
    });

    vi.spyOn(apiModule, 'useSets').mockReturnValue({
      sets: [selectedSet],
      totalSets: 1,
      loading: false,
      error: null,
    });

    vi.spyOn(apiModule, 'useSeries').mockReturnValue({
      series: [{ id: 'reg', name: 'Regression', logo: '' }],
      loading: false,
      error: null,
    });

    vi.spyOn(apiModule, 'useCards').mockReturnValue({
      cards: cardsForSet,
      totalCards: 3,
      loading: false,
      error: null,
    });
  });

  it('CardGrid, SetGrid, CollectionView, and CollectionStats preserve unique-vs-total semantics', async () => {
    render(<SetGrid onSetSelect={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Regression Set')).toBeInTheDocument();
    });
    expect(screen.getByText('Owned 2 / 3')).toBeInTheDocument();
    expect(screen.getByText('Total Qty: 3')).toBeInTheDocument();

    render(
      <CardGrid
        selectedSet={selectedSet}
        onBackClick={vi.fn()}
        onCardSelect={vi.fn()}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('Card One')).toBeInTheDocument();
    });
    expect(screen.getByText('Owned:')).toBeInTheDocument();
    expect(screen.getByText('Missing:')).toBeInTheDocument();
    expect(screen.getByText('Total Qty:')).toBeInTheDocument();

    render(<CollectionView />);
    const collectionViewCard = screen.getByRole('heading', { name: 'Collection View' }).closest('[class*="rounded-xl"]');
    expect(collectionViewCard).not.toBeNull();
    const collectionViewScope = within(collectionViewCard as HTMLElement);
    expect(collectionViewScope.getByText('Unique Cards')).toBeInTheDocument();
    expect(collectionViewScope.getByText('Total Quantity')).toBeInTheDocument();
    expect(collectionViewScope.getByText('3')).toBeInTheDocument();
    expect(collectionViewScope.getByText('6')).toBeInTheDocument();

    render(<CollectionStats />);
    const statsRoot = screen.getByRole('heading', { name: 'Collection Statistics' }).closest('[class*="container"]');
    expect(statsRoot).not.toBeNull();
    const statsScope = within(statsRoot as HTMLElement);
    expect(statsScope.getByText('(3 extra copies)')).toBeInTheDocument();
  });
});
