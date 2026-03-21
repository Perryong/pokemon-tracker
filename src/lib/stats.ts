/**
 * Quantity statistics computation for collection tracking.
 * 
 * Provides quantity-aware stats that distinguish between:
 * - Unique ownership (# of distinct cards owned, qty > 0)
 * - Total quantity (sum of all card quantities)
 * 
 * Used by CardGrid, SetGrid, and CollectionStats for consistent metrics.
 */

export interface QuantityStats {
  /** Number of distinct cards owned (qty > 0) */
  uniqueOwned: number;
  /** Sum of all card quantities */
  totalQuantity: number;
  /** Number of cards not owned (qty = 0) */
  missing: number;
  /** Percentage of unique cards owned (uniqueOwned / total * 100) */
  completionPercent: number;
}

/**
 * Compute quantity-aware statistics for a set of cards.
 * 
 * @param cardIds - Array of card IDs in the set/collection
 * @param cardQuantities - Map of card ID to quantity (sparse: missing = 0)
 * @returns QuantityStats with unique/total/missing/completion metrics
 */
export function computeQuantityStats(
  cardIds: string[],
  cardQuantities: Record<string, number>
): QuantityStats {
  const total = cardIds.length;
  
  if (total === 0) {
    return {
      uniqueOwned: 0,
      totalQuantity: 0,
      missing: 0,
      completionPercent: 0,
    };
  }
  
  // Count unique cards owned (qty > 0)
  const uniqueOwned = cardIds.filter(id => (cardQuantities[id] ?? 0) > 0).length;
  
  // Sum total quantities (only for cards in this set)
  const totalQuantity = cardIds.reduce((sum, id) => {
    return sum + (cardQuantities[id] ?? 0);
  }, 0);
  
  // Calculate derived metrics
  const missing = total - uniqueOwned;
  const completionPercent = (uniqueOwned / total) * 100;
  
  return {
    uniqueOwned,
    totalQuantity,
    missing,
    completionPercent,
  };
}
