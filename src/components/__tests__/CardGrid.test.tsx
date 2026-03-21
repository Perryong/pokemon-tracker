import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useSetCompletion, CompletionStats } from '@/lib/collection';

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
