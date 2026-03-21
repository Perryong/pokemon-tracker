import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCollection } from '../collection';

// Storage key constant from collection.ts
const STORAGE_KEY = 'pokemon-collection-v2';

describe('Collection Persistence Tests', () => {
  // Clear localStorage before and after each test for isolation
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('toggleOwnership persists card ID to localStorage under pokemon-collection-v2 key', () => {
    const { result } = renderHook(() => useCollection());

    act(() => {
      result.current.toggleOwnership('card-1');
    });

    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed).toEqual({
      version: 1,
      ownedCards: { 'card-1': true },
    });
  });

  it('addToCollection marks card as owned and persists', () => {
    const { result } = renderHook(() => useCollection());

    act(() => {
      result.current.addToCollection('card-2');
    });

    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed).toEqual({
      version: 1,
      ownedCards: { 'card-2': true },
    });

    expect(result.current.isOwned('card-2')).toBe(true);
  });

  it('removeFromCollection removes card from owned set and persists', () => {
    const { result } = renderHook(() => useCollection());

    // Add a card first
    act(() => {
      result.current.addToCollection('card-3');
    });

    expect(result.current.isOwned('card-3')).toBe(true);

    // Remove the card
    act(() => {
      result.current.removeFromCollection('card-3');
    });

    expect(result.current.isOwned('card-3')).toBe(false);

    const stored = localStorage.getItem(STORAGE_KEY);
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed).toEqual({
      version: 1,
      ownedCards: {},
    });
  });

  it('useCollection initializes from existing localStorage data on mount', () => {
    // Pre-populate localStorage
    const initialData = {
      version: 1,
      ownedCards: { 'card-4': true, 'card-5': true },
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData));

    // Mount the hook
    const { result } = renderHook(() => useCollection());

    // Verify the hook loaded the existing data
    expect(result.current.isOwned('card-4')).toBe(true);
    expect(result.current.isOwned('card-5')).toBe(true);
    expect(result.current.isOwned('card-6')).toBe(false);
  });

  it('QuotaExceededError is handled gracefully without crashing', () => {
    // Mock localStorage.setItem to throw QuotaExceededError
    const originalSetItem = Storage.prototype.setItem;
    const mockSetItem = vi.fn(() => {
      const error = new DOMException('Quota exceeded', 'QuotaExceededError');
      error.name = 'QuotaExceededError';
      throw error;
    });
    Storage.prototype.setItem = mockSetItem;

    const { result } = renderHook(() => useCollection());

    // This should not crash even though localStorage throws
    act(() => {
      result.current.addToCollection('card-7');
    });

    // State should still update in memory
    expect(result.current.isOwned('card-7')).toBe(true);

    // Restore original setItem
    Storage.prototype.setItem = originalSetItem;
  });

  it('toggleOwnership correctly toggles between owned and not owned', () => {
    const { result } = renderHook(() => useCollection());

    // Initially not owned
    expect(result.current.isOwned('card-8')).toBe(false);

    // Toggle to owned
    act(() => {
      result.current.toggleOwnership('card-8');
    });
    expect(result.current.isOwned('card-8')).toBe(true);

    // Toggle back to not owned
    act(() => {
      result.current.toggleOwnership('card-8');
    });
    expect(result.current.isOwned('card-8')).toBe(false);
  });

  it('addToCollection accepts card object with id property', () => {
    const { result } = renderHook(() => useCollection());

    const mockCard = { id: 'card-9', name: 'Pikachu' };

    act(() => {
      result.current.addToCollection(mockCard);
    });

    expect(result.current.isOwned('card-9')).toBe(true);
  });
});
