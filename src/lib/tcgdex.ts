import TCGdex from '@tcgdex/sdk'

// Export SDK types for use in types.ts
export type { SetResume, Set, SerieResume, Card, CardResume } from '@tcgdex/sdk'

// TCGdex singleton instance (English language)
export const tcgdex = new TCGdex('en')

/**
 * Fetch all Pokemon TCG sets
 * @returns Array of SetResume objects with basic set metadata
 */
export async function fetchAllSets(): Promise<import('@tcgdex/sdk').SetResume[]> {
  try {
    const result = await tcgdex.fetch('sets')
    return result || []
  } catch (error) {
    console.error('Failed to fetch sets:', error)
    throw error
  }
}

/**
 * Fetch all series metadata
 * @returns Array of SerieResume objects
 */
export async function fetchAllSeries(): Promise<import('@tcgdex/sdk').SerieResume[]> {
  try {
    const result = await tcgdex.fetch('series')
    return result || []
  } catch (error) {
    console.error('Failed to fetch series:', error)
    throw error
  }
}

/**
 * Fetch a specific set with all its cards
 * @param setId - The set ID (e.g., "base1", "swsh1")
 * @returns Full Set object with cards array
 */
export async function fetchSetWithCards(setId: string): Promise<import('@tcgdex/sdk').Set> {
  try {
    const result = await tcgdex.fetch('sets', setId)
    if (!result) {
      throw new Error(`Set ${setId} not found`)
    }
    return result
  } catch (error) {
    console.error(`Failed to fetch set ${setId}:`, error)
    throw error
  }
}
