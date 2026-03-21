import { z } from 'zod';

// Storage keys for collection data
export const STORAGE_KEY = 'pokemon-collection-v2';
export const BACKUP_KEY = 'pokemon-collection-v2-backup';

// V1 schema: boolean ownership
export interface CollectionStateV1 {
  version: 1;
  ownedCards: Record<string, boolean>;
}

// V3 schema: quantity-based ownership
export interface CollectionStateV3 {
  version: 3;
  cardQuantities: Record<string, number>;
}

// Union type for migration input
export type CollectionState = CollectionStateV1 | CollectionStateV3;

// Zod schema for V3 validation
export const CollectionV3Schema = z.object({
  version: z.literal(3),
  cardQuantities: z.record(z.string(), z.number().int().min(0).max(999))
});
