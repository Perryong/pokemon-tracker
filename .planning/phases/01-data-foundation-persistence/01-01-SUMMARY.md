---
phase: 01-data-foundation-persistence
plan: 01
subsystem: data-layer
tags: [tcgdex, adapter, types, normalization]
dependency_graph:
  requires: []
  provides: [tcgdex-adapter, normalized-types]
  affects: [api-layer, hooks]
tech_stack:
  added: ["@tcgdex/sdk v2.7.1"]
  patterns: [adapter-pattern, type-normalization]
key_files:
  created:
    - src/lib/tcgdex.ts
    - src/lib/types.ts
  modified: []
decisions:
  - choice: "Single image URL duplication"
    rationale: "TCGdex provides single image URL, duplicated to both small/large fields to match existing component contracts"
    alternatives: ["Modify components to handle single URL", "Fetch higher resolution separately"]
  - choice: "Default 'Pokémon' supertype"
    rationale: "TCGdex CardResume doesn't provide detailed type categorization, defaulting to 'Pokémon' for consistency"
    alternatives: ["Leave undefined", "Infer from card data"]
  - choice: "Minimal legalities mapping"
    rationale: "TCGdex uses boolean legal.standard/expanded vs string 'Legal'/'Illegal', mapped booleans to 'Legal' string or undefined"
    alternatives: ["Map false to 'Illegal'", "Keep boolean structure"]
metrics:
  duration_minutes: 3.8
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
  commits: 2
  completed_date: 2026-03-20
---

# Phase 1 Plan 01: TCGdex SDK Adapter Layer

**One-liner:** Created TCGdex SDK adapter with type normalization layer bridging TCGdex API responses to existing app component contracts

## What Was Built

### Artifacts Created

**src/lib/tcgdex.ts** — TCGdex SDK singleton and fetch wrappers
- Exports singleton `tcgdex` instance initialized for English language
- Provides `fetchAllSets()` for retrieving all set metadata
- Provides `fetchAllSeries()` for retrieving series information
- Provides `fetchSetWithCards(setId)` for full set details with card array
- Re-exports TCGdex SDK types (SetResume, Set, SerieResume, Card, CardResume)
- Includes error handling with console logging for all fetch operations

**src/lib/types.ts** — Normalized types and adapter functions
- Defines `PokemonSet` interface matching existing component contracts (images.logo/symbol, series, printedTotal/total)
- Defines `PokemonCard` interface with images.small/large structure
- Defines `CardImage` interface for image URL structure
- Defines `Series` interface for series metadata
- Implements `normalizeTCGSet()` mapping TCGdex SetResume/Set → PokemonSet
- Implements `normalizeTCGCard()` mapping TCGdex Card/CardResume → PokemonCard
- Implements `normalizeTCGSeries()` mapping TCGdex SerieResume → Series

### Integration Points

**Exports for downstream consumers:**
- `tcgdex` singleton for direct SDK access if needed
- `fetchAllSets()`, `fetchAllSeries()`, `fetchSetWithCards()` for data fetching
- Type interfaces: `PokemonSet`, `PokemonCard`, `CardImage`, `Series`
- Adapter functions: `normalizeTCGSet()`, `normalizeTCGCard()`, `normalizeTCGSeries()`

**Next phase dependencies:**
- Plan 01-02 (Collection Persistence) needs these types for collection data structure
- Plan 01-03 (Hook Migration) will refactor existing hooks to use these adapters

## Success Criteria Met

✅ **TCGdex SDK adapter module exists with singleton and fetch wrappers**
- src/lib/tcgdex.ts exports `tcgdex` singleton and 3 async fetch functions
- All functions include error handling and return type guarantees

✅ **Types module preserves existing component contracts**
- PokemonSet interface includes all fields used by SetGrid (images.logo, images.symbol, series, releaseDate, printedTotal)
- PokemonCard interface includes all fields used by CardGrid (images.small, number, rarity, set)
- CardImage interface provides small/large structure

✅ **Adapter functions normalize TCGdex responses to app types**
- normalizeTCGSet() maps cardCount.official → printedTotal, cardCount.total → total
- normalizeTCGCard() maps single image URL → images.small/large structure
- normalizeTCGCard() maps localId → number field
- normalizeTCGSeries() provides direct mapping for series data

✅ **Both modules compile without TypeScript errors**
- Verified with `npx tsc --noEmit src/lib/tcgdex.ts src/lib/types.ts`
- All type imports and exports resolve correctly

✅ **SDK fetch patterns match research recommendations**
- Uses SDK built-in caching (no custom cache layer added)
- Error handling logs errors and re-throws for upstream handling
- Returns empty arrays for missing data vs null/undefined

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CardResume rarity property access**
- **Found during:** Task 2 TypeScript compilation
- **Issue:** CardResume type doesn't guarantee `rarity` property exists, causing compilation error
- **Fix:** Changed `tcgCard.rarity` to `'rarity' in tcgCard ? tcgCard.rarity : undefined`
- **Files modified:** src/lib/types.ts
- **Commit:** b8292c7 (included in Task 2 commit)

## Implementation Notes

### TCGdex Type Differences Handled

| TCGdex Field | App Field | Transformation |
|--------------|-----------|----------------|
| `cardCount.official` | `printedTotal` | Direct mapping |
| `cardCount.total` | `total` | Direct mapping |
| `logo`, `symbol` | `images.logo`, `images.symbol` | Nested in images object |
| `image` (single URL) | `images.small`, `images.large` | Duplicate URL to both fields |
| `localId` | `number` | Direct mapping |
| `legal.standard` (boolean) | `legalities.standard` (string) | Map `true` → `'Legal'`, else `undefined` |
| `serie.name` | `series` | Extract name from nested serie object |

### Design Decisions

**Image URL Duplication:**  
TCGdex provides a single high-quality image URL per card. Rather than modifying 10+ components to handle single URLs, we duplicate this URL to both `images.small` and `images.large` fields. This preserves existing component contracts with zero downstream changes.

**Legalities String Mapping:**  
TCGdex uses boolean `legal.standard` and `legal.expanded` fields. App components expect string values like `'Legal'` or `undefined`. Mapped `true` → `'Legal'`, `false`/missing → `undefined` for backward compatibility.

**Default Supertype:**  
TCGdex CardResume objects don't provide detailed card categorization. Defaulted to `'Pokémon'` supertype since this is a Pokemon TCG tracker and 95%+ of cards are Pokemon cards.

## Testing Validation

**Type Compilation:**
```bash
npx tsc --noEmit src/lib/tcgdex.ts src/lib/types.ts
# ✓ Both files compile without errors
```

**Export Verification:**
- ✓ tcgdex singleton export: 1
- ✓ async fetch functions: 3 (fetchAllSets, fetchAllSeries, fetchSetWithCards)
- ✓ PokemonSet interface: 1
- ✓ normalize functions: 3 (normalizeTCGSet, normalizeTCGCard, normalizeTCGSeries)

## Known Limitations

1. **No PTCGO codes:** TCGdex doesn't provide PTCGO codes; `ptcgoCode` field always undefined
2. **No update timestamps:** TCGdex doesn't track update timestamps; `updatedAt` field always empty string
3. **Minimal card detail in CardResume:** CardResume (from set.cards array) has fewer fields than full Card object; some fields may be undefined until full card fetch
4. **Legalities inherited from sets:** Card-level legalities mirror set-level legalities; individual card bans not tracked
5. **Single image resolution:** Both small/large use same URL; no separate thumbnail optimization

## Next Steps

**Immediate dependencies (Wave 1):**
- Plan 01-02: Update collection persistence to use new PokemonCard type structure

**Wave 2 (depends on 01-01 + 01-02):**
- Plan 01-03: Refactor existing hooks (useSets, useCards, useCard) to use tcgdex adapter and normalize responses

## Self-Check

**Created files exist:**
```bash
✓ FOUND: src/lib/tcgdex.ts
✓ FOUND: src/lib/types.ts
```

**Commits exist:**
```bash
✓ FOUND: f769ea7 (Task 1: TCGdex SDK adapter module)
✓ FOUND: b8292c7 (Task 2: Normalized types with adapter functions)
```

## Self-Check: PASSED

All artifacts created, all commits verified, all acceptance criteria met.
