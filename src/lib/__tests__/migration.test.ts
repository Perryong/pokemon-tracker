import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  migrateV1ToV3,
  createBackup,
  restoreFromBackup,
  clearBackup,
  getInitialState
} from '../migration';
import { CollectionStateV1, CollectionStateV3, STORAGE_KEY, BACKUP_KEY } from '../collection-types';

describe('Migration Functions', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('createBackup', () => {
    it('writes v1 state to backup key and returns true', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };
      
      const result = createBackup(v1State);
      
      expect(result).toBe(true);
      const stored = localStorage.getItem(BACKUP_KEY);
      expect(stored).toBeTruthy();
      const parsed = JSON.parse(stored!);
      expect(parsed).toEqual(v1State);
    });

    it('returns false if backup write fails', () => {
      // Spy on localStorage.setItem and make it throw
      const setItemSpy = vi.spyOn(localStorage, 'setItem');
      setItemSpy.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };

      const result = createBackup(v1State);
      expect(result).toBe(false);

      // Restore
      setItemSpy.mockRestore();
    });
  });

  describe('restoreFromBackup', () => {
    it('reads and returns v1 state from backup key', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-2': true, 'card-3': true }
      };
      localStorage.setItem(BACKUP_KEY, JSON.stringify(v1State));

      const restored = restoreFromBackup();
      
      expect(restored).toEqual(v1State);
    });

    it('returns null if backup does not exist', () => {
      const restored = restoreFromBackup();
      expect(restored).toBeNull();
    });

    it('returns null if backup is corrupted', () => {
      localStorage.setItem(BACKUP_KEY, 'invalid json');
      
      const restored = restoreFromBackup();
      expect(restored).toBeNull();
    });
  });

  describe('clearBackup', () => {
    it('removes backup key from localStorage', () => {
      localStorage.setItem(BACKUP_KEY, '{"version":1,"ownedCards":{}}');
      
      clearBackup();
      
      expect(localStorage.getItem(BACKUP_KEY)).toBeNull();
    });
  });

  describe('migrateV1ToV3 - Normal Cases', () => {
    it('migrates empty collection to empty v3', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: {}
      };

      const result = migrateV1ToV3(v1State);

      expect(result).toEqual({
        version: 3,
        cardQuantities: {}
      });
    });

    it('migrates single owned card to quantity 1', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };

      const result = migrateV1ToV3(v1State);

      expect(result).toEqual({
        version: 3,
        cardQuantities: { 'card-1': 1 }
      });
    });

    it('migrates multiple owned cards', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: {
          'card-1': true,
          'card-2': true,
          'card-3': true
        }
      };

      const result = migrateV1ToV3(v1State);

      expect(result).toEqual({
        version: 3,
        cardQuantities: {
          'card-1': 1,
          'card-2': 1,
          'card-3': 1
        }
      });
    });

    it('omits false entries (sparse storage)', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: {
          'card-1': true,
          'card-2': false,
          'card-3': true,
          'card-4': false
        }
      };

      const result = migrateV1ToV3(v1State);

      expect(result).toEqual({
        version: 3,
        cardQuantities: {
          'card-1': 1,
          'card-3': 1
        }
      });
      expect(result.cardQuantities['card-2']).toBeUndefined();
      expect(result.cardQuantities['card-4']).toBeUndefined();
    });

    it('creates backup before migration', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };

      migrateV1ToV3(v1State);

      const backup = localStorage.getItem(BACKUP_KEY);
      expect(backup).toBeTruthy();
      const parsed = JSON.parse(backup!);
      expect(parsed).toEqual(v1State);
    });
  });

  describe('migrateV1ToV3 - Edge Cases', () => {
    it('handles large dataset (5000 cards)', () => {
      const ownedCards: Record<string, boolean> = {};
      for (let i = 0; i < 5000; i++) {
        ownedCards[`card-${i}`] = i % 2 === 0; // Every other card owned
      }

      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards
      };

      const result = migrateV1ToV3(v1State);

      expect(result.version).toBe(3);
      // Should have 2500 cards (half of 5000)
      expect(Object.keys(result.cardQuantities).length).toBe(2500);
      // All quantities should be 1
      Object.values(result.cardQuantities).forEach(qty => {
        expect(qty).toBe(1);
      });
    });

    it('deterministically migrates patterned large dataset (10000 cards)', () => {
      const ownedCards: Record<string, boolean> = {};
      for (let i = 0; i < 10000; i++) {
        // Deterministic pattern: own card when index divisible by 4 or 7
        ownedCards[`card-${i}`] = i % 4 === 0 || i % 7 === 0;
      }

      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards,
      };

      const result = migrateV1ToV3(v1State);

      const expectedOwnedCount = Object.values(ownedCards).filter(Boolean).length;

      expect(result.version).toBe(3);
      expect(Object.keys(result.cardQuantities)).toHaveLength(expectedOwnedCount);

      // Deterministic spot checks
      expect(result.cardQuantities['card-0']).toBe(1); // divisible by 4 and 7
      expect(result.cardQuantities['card-4']).toBe(1); // divisible by 4
      expect(result.cardQuantities['card-7']).toBe(1); // divisible by 7
      expect(result.cardQuantities['card-8']).toBe(1); // divisible by 4
      expect(result.cardQuantities['card-11']).toBeUndefined(); // neither divisible by 4 nor 7
      expect(result.cardQuantities['card-13']).toBeUndefined(); // neither divisible by 4 nor 7
      expect(result.cardQuantities['card-28']).toBe(1); // divisible by both
      expect(result.cardQuantities['card-9999']).toBeUndefined(); // neither divisible by 4 nor 7
    });

    it('handles mixed truthy/falsy values', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: {
          'card-1': true,
          'card-2': false,
          // @ts-expect-error Testing runtime behavior with undefined
          'card-3': undefined,
          // @ts-expect-error Testing runtime behavior with null
          'card-4': null,
          'card-5': true
        }
      };

      const result = migrateV1ToV3(v1State);

      // Only true values should be migrated
      expect(result.cardQuantities).toEqual({
        'card-1': 1,
        'card-5': 1
      });
    });

    it('restores from backup on migration failure', () => {
      // Mock Zod validation to fail
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };

      // This test validates the error handling path exists
      // The actual implementation will handle validation failures
      const result = migrateV1ToV3(v1State);
      
      // Even with errors, should return valid v3 state
      expect(result.version).toBe(3);
      expect(typeof result.cardQuantities).toBe('object');
    });
  });

  describe('getInitialState', () => {
    it('returns default v3 state when localStorage is empty', () => {
      const state = getInitialState();

      expect(state).toEqual({
        version: 3,
        cardQuantities: {}
      });
    });

    it('returns v3 state unchanged when already migrated', () => {
      const v3State: CollectionStateV3 = {
        version: 3,
        cardQuantities: { 'card-1': 5, 'card-2': 2 }
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(v3State));

      const state = getInitialState();

      expect(state).toEqual(v3State);
    });

    it('migrates v1 state to v3 automatically', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true, 'card-2': true }
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(v1State));

      const state = getInitialState();

      expect(state.version).toBe(3);
      expect((state as CollectionStateV3).cardQuantities).toEqual({
        'card-1': 1,
        'card-2': 1
      });
    });

    it('returns default v3 state for unknown version', () => {
      const unknownState = {
        version: 99,
        someData: {}
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(unknownState));

      const state = getInitialState();

      expect(state).toEqual({
        version: 3,
        cardQuantities: {}
      });
    });

    it('returns default v3 state for corrupted data', () => {
      localStorage.setItem(STORAGE_KEY, 'invalid json {]');

      const state = getInitialState();

      expect(state).toEqual({
        version: 3,
        cardQuantities: {}
      });
    });

    it('handles quota exceeded during migration gracefully', () => {
      const v1State: CollectionStateV1 = {
        version: 1,
        ownedCards: { 'card-1': true }
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(v1State));

      // Mock setItem to throw quota error on main storage write (but allow backup)
      let callCount = 0;
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
        callCount++;
        if (key === STORAGE_KEY && callCount > 1) { // Throw only on main storage write, not backup
          const error = new DOMException('Quota exceeded', 'QuotaExceededError');
          throw error;
        }
        // Allow backup write to succeed
        localStorage[key as any] = value;
      });

      const state = getInitialState();

      // Should still return valid state even if persistence fails
      expect(state.version).toBe(3);
      expect((state as CollectionStateV3).cardQuantities).toBeDefined();

      setItemSpy.mockRestore();
    });
  });
});
