import {
  CollectionStateV1,
  CollectionStateV3,
  CollectionV3Schema,
  STORAGE_KEY,
  BACKUP_KEY,
  CollectionState
} from './collection-types';

/**
 * Create a backup of the v1 state before migration
 * @param data V1 state to backup
 * @returns true if backup successful, false otherwise
 */
export const createBackup = (data: CollectionStateV1): boolean => {
  try {
    localStorage.setItem(BACKUP_KEY, JSON.stringify(data));
    return true;
  } catch (e) {
    console.error('Failed to create backup:', e);
    return false;
  }
};

/**
 * Restore collection state from backup
 * @returns Restored v1 state or null if backup doesn't exist
 */
export const restoreFromBackup = (): CollectionStateV1 | null => {
  try {
    const backup = localStorage.getItem(BACKUP_KEY);
    if (!backup) {
      return null;
    }
    return JSON.parse(backup);
  } catch (e) {
    console.error('Failed to restore from backup:', e);
    return null;
  }
};

/**
 * Clear the backup after successful migration
 */
export const clearBackup = (): void => {
  try {
    localStorage.removeItem(BACKUP_KEY);
  } catch (e) {
    console.error('Failed to clear backup:', e);
  }
};

/**
 * Convert v1 state in memory without persistence (for fallback)
 */
const convertToV3InMemory = (v1State: CollectionStateV1): CollectionStateV3 => {
  const cardQuantities: Record<string, number> = {};
  
  Object.entries(v1State.ownedCards).forEach(([id, owned]) => {
    if (owned === true) {
      cardQuantities[id] = 1;
    }
  });
  
  return {
    version: 3,
    cardQuantities
  };
};

/**
 * Migrate v1 boolean ownership to v3 quantity storage
 * @param v1State V1 collection state
 * @returns V3 collection state
 */
export const migrateV1ToV3 = (v1State: CollectionStateV1): CollectionStateV3 => {
  // Create backup first
  createBackup(v1State);
  
  try {
    // Transform: true → 1, false/undefined → omit (sparse storage)
    const cardQuantities: Record<string, number> = {};
    
    Object.entries(v1State.ownedCards).forEach(([id, owned]) => {
      if (owned === true) {
        cardQuantities[id] = 1;
      }
      // Sparse storage: omit false/falsy entries
    });
    
    const v3State: CollectionStateV3 = {
      version: 3,
      cardQuantities
    };
    
    // Validate with Zod
    CollectionV3Schema.parse(v3State);
    
    console.log(`Migration complete: ${Object.keys(cardQuantities).length} cards migrated`);
    return v3State;
    
  } catch (e) {
    console.error('Migration failed:', e);
    
    // Attempt rollback
    const backup = restoreFromBackup();
    if (backup) {
      console.warn('Migration failed, converting backup in-memory');
      return convertToV3InMemory(backup);
    }
    
    // Last resort: empty state
    console.error('Rollback failed, using empty collection');
    return { version: 3, cardQuantities: {} };
  }
};

/**
 * Get initial collection state with automatic migration
 * @returns V3 collection state (migrated if necessary)
 */
export const getInitialState = (): CollectionStateV3 => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    
    // No stored data - return default v3 state
    if (!stored) {
      return { version: 3, cardQuantities: {} };
    }
    
    const parsed = JSON.parse(stored) as CollectionState;
    
    // Already v3 - validate and return
    if (parsed.version === 3) {
      const validated = CollectionV3Schema.safeParse(parsed);
      if (validated.success) {
        return validated.data;
      }
      console.warn('Invalid v3 state found, using empty collection');
      return { version: 3, cardQuantities: {} };
    }
    
    // V1 state - migrate automatically
    if (parsed.version === 1) {
      console.log('Migrating v1 collection to v3 format');
      const v3State = migrateV1ToV3(parsed as CollectionStateV1);
      
      // Attempt to persist migrated state
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(v3State));
      } catch (e) {
        if (e instanceof DOMException && e.name === 'QuotaExceededError') {
          console.error('localStorage quota exceeded during migration');
        } else {
          console.error('Failed to save migrated collection:', e);
        }
        // Keep state in memory even if persistence fails
      }
      
      return v3State;
    }
    
    // Unknown version
    console.warn(`Unknown collection version: ${(parsed as any).version}, using empty collection`);
    return { version: 3, cardQuantities: {} };
    
  } catch (e) {
    console.error('Failed to load collection:', e);
    return { version: 3, cardQuantities: {} };
  }
};
