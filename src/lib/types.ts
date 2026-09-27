import type { SetResume, Set, SerieResume, Card, CardResume } from './tcgdex'

// ============================================================================
// Normalized App Types (preserve existing interfaces from api.ts)
// ============================================================================

/**
 * PokemonSet interface matching existing component contracts
 * Components expect: images.logo, images.symbol, series, releaseDate, printedTotal, total
 */
export interface PokemonSet {
  id: string;
  name: string;
  series: string;
  printedTotal: number;
  total: number;
  legalities: {
    standard?: string;
    expanded?: string;
    unlimited?: string;
  };
  ptcgoCode?: string;
  releaseDate: string;
  updatedAt: string;
  images: {
    symbol: string;
    logo: string;
  };
}

/**
 * CardImage interface for card image URLs
 * Components expect: images.small, images.large
 */
export interface CardImage {
  small: string;
  large: string;
}

/**
 * PokemonCard interface matching existing component contracts
 * Components expect: images.small, number, rarity, set object
 */
export interface PokemonCard {
  id: string;
  name: string;
  supertype: string;
  subtypes: string[];
  marketPrices?: Array<{ provider: string; source?: string; variant: string; currency: string; updated?: string; values: Record<string, number> }>;
  abilities?: Array<{ name: string; effect: string; type: string }>;
  hp?: string;
  types?: string[];
  evolvesFrom?: string;
  evolvesTo?: string[];
  rules?: string[];
  attacks?: Array<{
    name: string;
    cost: string[];
    convertedEnergyCost: number;
    damage: string;
    text: string;
  }>;
  weaknesses?: Array<{
    type: string;
    value: string;
  }>;
  resistances?: Array<{
    type: string;
    value: string;
  }>;
  retreatCost?: string[];
  convertedRetreatCost?: number;
  set: PokemonSet;
  number: string;
  artist?: string;
  rarity?: string;
  flavorText?: string;
  nationalPokedexNumbers?: number[];
  legalities: {
    standard?: string;
    expanded?: string;
    unlimited?: string;
  };
  images: CardImage;
}

/**
 * Series interface for series metadata
 */
export interface Series {
  id: string;
  name: string;
  logo?: string;
}

// ============================================================================
// Adapter Functions (TCGdex SDK types → App types)
// ============================================================================

/**
 * Normalize TCGdex SetResume or Set to app PokemonSet
 * Handles both SetResume (from sets list) and Set (from set details)
 */
export function normalizeTCGSet(tcgSet: SetResume | Set): PokemonSet {
  // Check if this is a full Set object (has 'serie' property)
  const isFullSet = 'serie' in tcgSet && tcgSet.serie !== undefined
  
  return {
    id: tcgSet.id,
    name: tcgSet.name,
    series: isFullSet ? tcgSet.serie.name : 'Unknown',
    printedTotal: tcgSet.cardCount.official,
    total: tcgSet.cardCount.total,
    legalities: {
      standard: isFullSet && tcgSet.legal?.standard ? 'legal' : undefined,
      expanded: isFullSet && tcgSet.legal?.expanded ? 'legal' : undefined,
      unlimited: 'legal', // TCGdex doesn't track unlimited, default to legal
    },
    ptcgoCode: undefined, // TCGdex doesn't provide PTCGO codes
    releaseDate: isFullSet ? tcgSet.releaseDate : '',
    updatedAt: '', // TCGdex doesn't provide update timestamps
    images: {
      symbol: tcgSet.symbol ? `${tcgSet.symbol}.webp` : '',
      logo: tcgSet.logo ? `${tcgSet.logo}.webp` : '',
    },
  }
}

/**
 * Normalize TCGdex Card or CardResume to app PokemonCard
 * TCGdex uses single 'image' URL vs app's images.small/large structure
 */
export function normalizeTCGCard(tcgCard: Card | CardResume, setData?: Set): PokemonCard {
  // Build set object from setData if provided, otherwise use minimal placeholder
  const cardSet = setData || ('set' in tcgCard ? tcgCard.set : undefined)
  const setInfo: PokemonSet = cardSet
    ? normalizeTCGSet(cardSet)
    : {
        id: '',
        name: '',
        series: '',
        printedTotal: 0,
        total: 0,
        legalities: {},
        releaseDate: '',
        updatedAt: '',
        images: { symbol: '', logo: '' },
      }

  // TCGdex returns an asset base URL; choose quality for each view.
  const imageUrl = 'image' in tcgCard ? tcgCard.image || '' : ''
  
  const marketPrices: NonNullable<PokemonCard['marketPrices']> = []
  const pricing = (tcgCard as Card & { pricing?: Record<string, unknown> }).pricing
  for (const provider of ['tcgplayer', 'cardmarket']) {
    const data = pricing?.[provider]
    if (!data || typeof data !== 'object') continue
    const source = data as Record<string, unknown>
    const variants = provider === 'cardmarket' ? [['All printings', source] as const] : Object.entries(source)
    for (const [variant, quote] of variants) {
      if (!quote || typeof quote !== 'object') continue
      const values = Object.fromEntries(Object.entries(quote).filter(([key, value]) =>
        key !== 'productId' && key !== 'idProduct' && typeof value === 'number' && Number.isFinite(value) && value >= 0
      )) as Record<string, number>
      if (Object.keys(values).length) marketPrices.push({ provider, variant, currency: typeof source.unit === 'string' ? source.unit : provider === 'tcgplayer' ? 'USD' : 'EUR', updated: typeof source.updated === 'string' ? source.updated : undefined, values })
    }
  }
  return {
    marketPrices,
    abilities: 'abilities' in tcgCard ? tcgCard.abilities : undefined,
    attacks: 'attacks' in tcgCard ? tcgCard.attacks?.map(attack => ({ name: attack.name, cost: attack.cost || [], convertedEnergyCost: attack.cost?.length || 0, damage: String(attack.damage ?? ''), text: attack.effect || '' })) : undefined,
    weaknesses: 'weaknesses' in tcgCard ? tcgCard.weaknesses?.map(w => ({ ...w, value: w.value || '' })) : undefined,
    resistances: 'resistances' in tcgCard ? tcgCard.resistances?.map(w => ({ ...w, value: w.value || '' })) : undefined,
    convertedRetreatCost: 'retreat' in tcgCard ? tcgCard.retreat : undefined,
    flavorText: 'description' in tcgCard ? tcgCard.description : undefined,
    rules: 'effect' in tcgCard && tcgCard.effect ? [tcgCard.effect] : undefined,
    id: tcgCard.id,
    name: tcgCard.name,
    supertype: 'category' in tcgCard ? tcgCard.category : 'Pokémon',
    subtypes: 'stage' in tcgCard && tcgCard.stage ? [tcgCard.stage] : [],
    hp: 'hp' in tcgCard ? tcgCard.hp?.toString() : undefined,
    types: 'types' in tcgCard ? tcgCard.types : undefined,
    evolvesFrom: 'evolveFrom' in tcgCard ? tcgCard.evolveFrom : undefined,
    set: setInfo,
    number: tcgCard.localId,
    artist: 'illustrator' in tcgCard ? tcgCard.illustrator : undefined,
    rarity: 'rarity' in tcgCard ? tcgCard.rarity : undefined,
    legalities: {
      standard: undefined, // Card-level legalities inherited from set
      expanded: undefined,
      unlimited: 'legal',
    },
    images: {
      small: imageUrl ? `${imageUrl}/low.webp` : '',
      large: imageUrl ? `${imageUrl}/high.webp` : '',
    },
  }
}

/**
 * Normalize TCGdex SerieResume to app Series
 * Direct mapping - structures are already similar
 */
export function normalizeTCGSeries(tcgSeries: SerieResume): Series {
  return {
    id: tcgSeries.id,
    name: tcgSeries.name,
    logo: tcgSeries.logo,
  }
}
