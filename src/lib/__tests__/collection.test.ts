import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCollection } from '../collection';
import { STORAGE_KEY } from '../collection-types';

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
      version: 3,
      cardQuantities: { 'card-1': 1 },
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
      version: 3,
      cardQuantities: { 'card-2': 1 },
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
      version: 3,
      cardQuantities: {},
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

describe('Quantity Operations', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('getQuantity returns 0 for unowned card', () => {
    const { result } = renderHook(() => useCollection());
    expect(result.current.getQuantity('card-1')).toBe(0);
  });
  
  it('setQuantity stores quantity and makes card owned', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 5));
    expect(result.current.getQuantity('card-1')).toBe(5);
    expect(result.current.isOwned('card-1')).toBe(true);
  });
  
  it('setQuantity clamps to 0-999 range', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 1500));
    expect(result.current.getQuantity('card-1')).toBe(999);
    
    act(() => result.current.setQuantity('card-2', -5));
    expect(result.current.getQuantity('card-2')).toBe(0);
  });
  
  it('incrementQuantity adds 1 up to 999', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 998));
    act(() => result.current.incrementQuantity('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(999);
    act(() => result.current.incrementQuantity('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(999); // Capped
  });
  
  it('decrementQuantity subtracts 1 down to 0', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 2));
    act(() => result.current.decrementQuantity('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(1);
    act(() => result.current.decrementQuantity('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(0);
    expect(result.current.isOwned('card-1')).toBe(false);
  });

  it('ownedCards derived from cardQuantities', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 3));
    act(() => result.current.setQuantity('card-2', 1));
    
    expect(result.current.ownedCards).toEqual({
      'card-1': true,
      'card-2': true
    });
  });

  it('addToCollection is idempotent (does not increment existing)', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 5));
    act(() => result.current.addToCollection('card-1'));
    expect(result.current.getQuantity('card-1')).toBe(5); // Unchanged
  });
});

describe('Sparse Storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('setQuantity(0) removes card from storage', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 5));
    act(() => result.current.setQuantity('card-1', 0));
    
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    expect(stored.cardQuantities['card-1']).toBeUndefined();
  });
  
  it('decrementQuantity to 0 removes card from storage', () => {
    const { result } = renderHook(() => useCollection());
    act(() => result.current.setQuantity('card-1', 1));
    act(() => result.current.decrementQuantity('card-1'));
    
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    expect(stored.cardQuantities['card-1']).toBeUndefined();
  });
});

describe('Migration Integration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('migrates v1 localStorage data to v3 on hook mount', () => {
    const v1Data = {
      version: 1,
      ownedCards: { 'card-1': true, 'card-2': true, 'card-3': false }
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(v1Data));
    
    const { result } = renderHook(() => useCollection());
    
    // Should have migrated
    expect(result.current.isOwned('card-1')).toBe(true);
    expect(result.current.isOwned('card-2')).toBe(true);
    expect(result.current.isOwned('card-3')).toBe(false); // Was false
    expect(result.current.getQuantity('card-1')).toBe(1);
    expect(result.current.getQuantity('card-2')).toBe(1);
    
    // Storage should now be v3
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)!);
    expect(stored.version).toBe(3);
    expect(stored.cardQuantities).toBeDefined();
  });
});
