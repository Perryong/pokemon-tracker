import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SetGrid from '../SetGrid';
import { PokemonSet } from '@/lib/api';
import * as apiModule from '@/lib/api';
import * as collectionModule from '@/lib/collection';

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return {
    ...actual,
    useSets: vi.fn(),
    useSeries: vi.fn(),
  };
});

vi.mock('@/lib/collection', async () => {
  const actual = await vi.importActual<typeof import('@/lib/collection')>('@/lib/collection');
  return {
    ...actual,
    useCollection: vi.fn(),
  };
});

const mockSets: PokemonSet[] = [
  {
    id: 'base1',
    name: 'Base Set',
    series: 'Base',
    printedTotal: 102,
    total: 102,
    legalities: { unlimited: 'legal' },
    releaseDate: '1999-01-09',
    updatedAt: '',
    images: { symbol: '', logo: '' },
  },
  {
    id: 'jungle',
    name: 'Jungle',
    series: 'Base',
    printedTotal: 64,
    total: 64,
    legalities: { unlimited: 'legal' },
    releaseDate: '1999-06-16',
    updatedAt: '',
    images: { symbol: '', logo: '' },
  },
  {
    id: 'fossil',
    name: 'Fossil',
    series: 'Base',
    printedTotal: 62,
    total: 62,
    legalities: { unlimited: 'legal' },
    releaseDate: '1999-10-10',
    updatedAt: '',
    images: { symbol: '', logo: '' },
  },
];

describe('SetGrid v1.0 workflow regressions', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.spyOn(apiModule, 'useSets').mockReturnValue({
      sets: mockSets,
      totalSets: mockSets.length,
      loading: false,
      error: null,
    });

    vi.spyOn(apiModule, 'useSeries').mockReturnValue({
      series: [{ id: 'base', name: 'Base', logo: '' }],
      loading: false,
      error: null,
    });

    vi.spyOn(collectionModule, 'useCollection').mockReturnValue({
      ownedCards: {},
      cardQuantities: {},
      isOwned: vi.fn().mockReturnValue(false),
      isInCollection: vi.fn().mockReturnValue(false),
      toggleOwnership: vi.fn(),
      addToCollection: vi.fn(),
      removeFromCollection: vi.fn(),
      getQuantity: vi.fn().mockReturnValue(0),
      setQuantity: vi.fn(),
      incrementQuantity: vi.fn(),
      decrementQuantity: vi.fn(),
    });
  });

  it('renders set cards and invokes onSetSelect with the clicked set', async () => {
    const onSetSelect = vi.fn();
    render(<SetGrid onSetSelect={onSetSelect} />);

    await waitFor(() => {
      expect(screen.getByText('Base Set')).toBeInTheDocument();
      expect(screen.getByText('Jungle')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Jungle'));
    expect(onSetSelect).toHaveBeenCalledWith(mockSets[1]);
  });

  it('search narrows visible sets and clear filters restores baseline list', async () => {
    render(<SetGrid onSetSelect={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Base Set')).toBeInTheDocument();
      expect(screen.getByText('Jungle')).toBeInTheDocument();
      expect(screen.getByText('Fossil')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('Search sets...'), {
      target: { value: 'jungle' },
    });

    expect(screen.queryByText('Base Set')).not.toBeInTheDocument();
    expect(screen.queryByText('Fossil')).not.toBeInTheDocument();
    expect(screen.getByText('Jungle')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Clear Filters' }));

    expect(screen.getByText('Base Set')).toBeInTheDocument();
    expect(screen.getByText('Jungle')).toBeInTheDocument();
    expect(screen.getByText('Fossil')).toBeInTheDocument();
  });
});
