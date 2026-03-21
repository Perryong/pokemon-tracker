import { describe, it, expect } from 'vitest';
import { 
  CollectionStateV1, 
  CollectionStateV3, 
  CollectionV3Schema,
  STORAGE_KEY,
  BACKUP_KEY,
  CollectionState
} from '../collection-types';

describe('Collection Types', () => {
  describe('Constants', () => {
    it('STORAGE_KEY is pokemon-collection-v2', () => {
      expect(STORAGE_KEY).toBe('pokemon-collection-v2');
    });

    it('BACKUP_KEY is pokemon-collection-v2-backup', () => {
      expect(BACKUP_KEY).toBe('pokemon-collection-v2-backup');
    });
  });

  describe('CollectionStateV1 interface', () => {
    it('accepts valid v1 structure', () => {
      const v1: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true, 'card-2': false }
      };
      expect(v1.version).toBe(1);
      expect(v1.ownedCards).toEqual({ 'card-1': true, 'card-2': false });
    });
  });

  describe('CollectionStateV3 interface', () => {
    it('accepts valid v3 structure', () => {
      const v3: CollectionStateV3 = {
        version: 3,
        cardQuantities: { 'card-1': 1, 'card-2': 5 }
      };
      expect(v3.version).toBe(3);
      expect(v3.cardQuantities).toEqual({ 'card-1': 1, 'card-2': 5 });
    });
  });

  describe('CollectionV3Schema Zod validator', () => {
    it('validates correct v3 state', () => {
      const valid = {
        version: 3,
        cardQuantities: { 'card-1': 1, 'card-2': 100 }
      };
      const result = CollectionV3Schema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('rejects non-integer quantities', () => {
      const invalid = {
        version: 3,
        cardQuantities: { 'card-1': 1.5 }
      };
      const result = CollectionV3Schema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rejects negative quantities', () => {
      const invalid = {
        version: 3,
        cardQuantities: { 'card-1': -1 }
      };
      const result = CollectionV3Schema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('rejects quantities over 999', () => {
      const invalid = {
        version: 3,
        cardQuantities: { 'card-1': 1000 }
      };
      const result = CollectionV3Schema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('accepts quantity of 0', () => {
      const valid = {
        version: 3,
        cardQuantities: { 'card-1': 0 }
      };
      const result = CollectionV3Schema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('accepts quantity of 999 (max)', () => {
      const valid = {
        version: 3,
        cardQuantities: { 'card-1': 999 }
      };
      const result = CollectionV3Schema.safeParse(valid);
      expect(result.success).toBe(true);
    });

    it('rejects wrong version number', () => {
      const invalid = {
        version: 2,
        cardQuantities: { 'card-1': 1 }
      };
      const result = CollectionV3Schema.safeParse(invalid);
      expect(result.success).toBe(false);
    });

    it('accepts empty cardQuantities', () => {
      const valid = {
        version: 3,
        cardQuantities: {}
      };
      const result = CollectionV3Schema.safeParse(valid);
      expect(result.success).toBe(true);
    });
  });

  describe('CollectionState union type', () => {
    it('accepts v1 state', () => {
      const state: CollectionState = {
        version: 1,
        ownedCards: { 'card-1': true }
      };
      expect(state.version).toBe(1);
    });

    it('accepts v3 state', () => {
      const state: CollectionState = {
        version: 3,
        cardQuantities: { 'card-1': 1 }
      };
      expect(state.version).toBe(3);
    });
  });
});
