import { describe, it, expect } from 'vitest';
import { computeQuantityStats } from '../stats';

describe('computeQuantityStats', () => {
  it('returns zero stats for empty card list', () => {
    const result = computeQuantityStats([], {});
    
    expect(result).toEqual({
      uniqueOwned: 0,
      totalQuantity: 0,
      missing: 0,
      completionPercent: 0,
    });
  });

  it('computes correct stats for partial ownership with duplicates', () => {
    const cardIds = ['a', 'b', 'c'];
    const quantities = { a: 1, b: 2 };
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(2); // a and b
    expect(result.totalQuantity).toBe(3); // 1 + 2
    expect(result.missing).toBe(1); // c
    expect(result.completionPercent).toBeCloseTo(66.67, 2);
  });

  it('adding duplicates does NOT change uniqueOwned or completionPercent', () => {
    const cardIds = ['a', 'b', 'c'];
    const quantities1 = { a: 3 };
    const quantities2 = { a: 4 };
    
    const result1 = computeQuantityStats(cardIds, quantities1);
    const result2 = computeQuantityStats(cardIds, quantities2);
    
    // uniqueOwned and completion should be the same
    expect(result1.uniqueOwned).toBe(result2.uniqueOwned);
    expect(result1.completionPercent).toBe(result2.completionPercent);
    expect(result1.missing).toBe(result2.missing);
    
    // But totalQuantity should increase
    expect(result2.totalQuantity).toBe(result1.totalQuantity + 1);
  });

  it('uses card IDs with qty > 0 for unique count, not sum of quantities', () => {
    const cardIds = ['a', 'b', 'c', 'd'];
    const quantities = { a: 10, b: 20, c: 1 }; // 3 unique cards, 31 total
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(3); // NOT 31
    expect(result.totalQuantity).toBe(31); // 10 + 20 + 1
    expect(result.missing).toBe(1); // d
    expect(result.completionPercent).toBe(75); // 3/4 * 100
  });

  it('handles all cards owned', () => {
    const cardIds = ['a', 'b', 'c'];
    const quantities = { a: 1, b: 1, c: 1 };
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(3);
    expect(result.totalQuantity).toBe(3);
    expect(result.missing).toBe(0);
    expect(result.completionPercent).toBe(100);
  });

  it('handles no cards owned', () => {
    const cardIds = ['a', 'b', 'c'];
    const quantities = {};
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(0);
    expect(result.totalQuantity).toBe(0);
    expect(result.missing).toBe(3);
    expect(result.completionPercent).toBe(0);
  });

  it('handles sparse quantities (undefined values treated as 0)', () => {
    const cardIds = ['a', 'b', 'c', 'd'];
    const quantities = { b: 2, d: 5 };
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(2); // b and d
    expect(result.totalQuantity).toBe(7); // 2 + 5
    expect(result.missing).toBe(2); // a and c
    expect(result.completionPercent).toBe(50); // 2/4 * 100
  });

  it('handles large datasets', () => {
    const cardIds = Array.from({ length: 150 }, (_, i) => `card-${i}`);
    const quantities: Record<string, number> = {};
    
    // Own 100 cards with varying quantities
    for (let i = 0; i < 100; i++) {
      quantities[`card-${i}`] = Math.floor(Math.random() * 5) + 1;
    }
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(100);
    expect(result.missing).toBe(50);
    expect(result.completionPercent).toBeCloseTo(66.67, 2);
    expect(result.totalQuantity).toBeGreaterThanOrEqual(100); // At least 1 per card
    expect(result.totalQuantity).toBeLessThanOrEqual(500); // At most 5 per card
  });

  it('calculates correct percentage with precision', () => {
    const cardIds = Array.from({ length: 7 }, (_, i) => `card-${i}`);
    const quantities = { 'card-0': 1, 'card-1': 1 };
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.completionPercent).toBeCloseTo(28.571428, 5); // 2/7 * 100
  });

  it('ignores quantity entries not in card list', () => {
    const cardIds = ['a', 'b', 'c'];
    const quantities = { a: 1, b: 2, 'x': 99, 'y': 50 };
    
    const result = computeQuantityStats(cardIds, quantities);
    
    expect(result.uniqueOwned).toBe(2); // Only a and b count
    expect(result.totalQuantity).toBe(3); // 1 + 2 (x and y ignored)
    expect(result.missing).toBe(1); // c
  });
});
