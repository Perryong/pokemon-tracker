import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import App from '@/App';
import { STORAGE_KEY } from '@/lib/collection-types';
import * as apiModule from '@/lib/api';

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api');
  return {
    ...actual,
    useSets: vi.fn(),
    useSeries: vi.fn(),
  };
});

beforeEach(() => {
  localStorage.clear();

  vi.spyOn(apiModule, 'useSets').mockReturnValue({
    sets: [],
    totalSets: 0,
    loading: false,
    error: null,
  });

  vi.spyOn(apiModule, 'useSeries').mockReturnValue({
    series: [],
    loading: false,
    error: null,
  });
});

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe('App persistence regression', () => {
  it('hydrates ownership state from localStorage across unmount/remount', async () => {
    const persisted = {
      version: 3,
      cardQuantities: {
        'base1-1': 2,
      },
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));

    const { unmount } = render(<App />);

    await waitFor(() => {
      expect(screen.getByText('My Collection')).toBeInTheDocument();
    });

    // Badge appears in nav when at least 1 unique card is owned.
    expect(screen.getAllByText('1').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByText('My Collection'));
    expect(screen.getByRole('heading', { name: 'My Collection' })).toBeInTheDocument();
    expect(screen.getByText('Unique Cards')).toBeInTheDocument();
    expect(screen.getByText('Total Quantity')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();

    unmount();

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('My Collection')).toBeInTheDocument();
    });

    expect(screen.getAllByText('1').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByText('My Collection'));
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});
