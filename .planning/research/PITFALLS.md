# Pitfalls Research

**Domain:** Pokemon TCG Collection Tracker
**Researched:** 2024-01-20
**Confidence:** HIGH (based on domain expertise, existing codebase analysis, and TCG tracker patterns)

## Critical Pitfalls

### Pitfall 1: Card Identity Crisis (Set Reprints & Variants)

**What goes wrong:**
Collection tracking breaks when the same Pokemon card exists across multiple sets with different artwork, numbers, or variants (reverse holo, first edition, etc.). Users lose track of which specific version they own, or worse, the system merges different prints as the same card.

**Why it happens:**
Developers assume card name + set is sufficient identity, but Pokemon TCG has:
- Same card reprinted in multiple sets
- Reverse holofoil vs regular vs special variants
- Promotional cards with same name but different numbers
- Regional variants (English vs Japanese sets)
- Special editions (1st Edition, Shadowless, etc.)

**How to avoid:**
- **Always use `card.id` as the primary key** — TCGdex provides unique IDs per variant
- Store the full card object reference (with set details) in localStorage, not just card name
- Display set name + card number prominently in UI (e.g., "Charizard - Base Set 4/102")
- Never merge cards by name alone — treat each set/variant combination as distinct

**Warning signs:**
- Users report "I marked this card owned, but it's not showing in my collection"
- Collection count doesn't match what user expects
- Duplicate card names appearing in collection without set context
- User says "I have the old version, not the new one"

**Phase to address:**
**Phase 1 (Data Foundation)** — Card identity must be correct from day one. The existing codebase already uses `card.id` as key in collection.ts, which is correct. Verify this pattern is maintained when integrating TCGdex SDK.

---

### Pitfall 2: localStorage Size Explosion

**What goes wrong:**
localStorage hits the 5-10MB browser limit when users track large collections (500+ cards). The app crashes silently, loses data, or stops persisting changes. Users discover weeks of tracking work is gone.

**Why it happens:**
Each card object from Pokemon TCG API/TCGdex includes:
- Full card images (small + large URLs)
- Complete set metadata
- Price history objects
- Attack descriptions, abilities, rules text
- Legalities across formats

Storing 1000 full card objects = ~8-12MB of JSON. One large collection = quota exceeded.

**How to avoid:**
- **Store minimal card references** — Only store card IDs and ownership metadata
- Implement projection pattern:
  ```typescript
  // BAD: Store full card
  localStorage.setItem('collection', JSON.stringify(fullCardObjects))
  
  // GOOD: Store minimal ownership data
  const collectionData = {
    [cardId]: { 
      quantity: 3, 
      condition: 'Near Mint',
      acquiredDate: '2024-01-15',
      // NO full card data
    }
  }
  ```
- Fetch card details from TCGdex on-demand when displaying
- Implement quota monitoring: `navigator.storage.estimate()`
- Add export/backup functionality BEFORE users hit limits

**Warning signs:**
- `localStorage.setItem()` throws `QuotaExceededError` (check browser console)
- Collection persists for small collections but fails silently for large ones
- User reports "my collection disappeared after adding more cards"
- Dev tools show localStorage approaching 5MB

**Phase to address:**
**Phase 1 (Data Foundation)** — The existing codebase already stores full card objects in localStorage. This MUST be refactored to store only ownership metadata + card IDs before launch. Current implementation will fail at ~200-500 cards depending on card complexity.

**Recovery cost:** HIGH if discovered after users have large collections (data migration required)

---

### Pitfall 3: Stale Card Data & Price Drift

**What goes wrong:**
Card prices, legalities, and set metadata become outdated because the app never refreshes data from TCGdex. Users see prices from 6 months ago, tournament-legal status is wrong, or new sets don't appear.

**Why it happens:**
Developers cache TCGdex responses aggressively to reduce API calls, but Pokemon TCG data changes frequently:
- Card prices fluctuate daily (especially for competitive meta cards)
- New sets release every 3 months
- Legalities change with format rotations
- Set completion totals corrected (secret rares added post-launch)

Without a refresh strategy, cached data becomes stale and users lose trust.

**How to avoid:**
- **Implement cache expiration strategy:**
  - Card list data: 24 hour TTL
  - Price data: 6-12 hour TTL (or real-time fetch on demand)
  - Set metadata: 7 day TTL
- Store cache timestamp alongside data
- Add manual "Refresh Data" button for user-initiated updates
- Show data freshness indicator: "Prices as of 2 hours ago"
- On app load, check if cache is stale and background refresh

**Warning signs:**
- User reports "this card is worth $50 but your app shows $5"
- Set completion shows 78/78 but set actually has 82 cards (secret rares)
- New set released but doesn't appear in app
- Card legality shows "Standard" but card rotated out 2 months ago

**Phase to address:**
**Phase 2 (TCGdex Integration)** — Implement caching with TTL when integrating SDK. The project requirements mention using TCGdex SDK endpoints, so cache strategy must be built alongside integration.

---

### Pitfall 4: Set Completion False Positives

**What goes wrong:**
Users see "100% Complete" for a set but they're missing secret rares, alternate arts, or promotional variants that aren't in the base set count. Or completion percentage calculates based on `printedTotal` but user wants to include secret rares (which are numbered beyond printedTotal).

**Why it happens:**
Pokemon TCG sets have confusing completion semantics:
- `printedTotal`: Advertised set size (e.g., "78 cards")
- `total`: Actual card count including secret rares (e.g., 88 cards)
- Promo cards: Same set ID but not part of "completion"
- Regional exclusives: Card exists in set but not available in user's region

Tracker defaults to `printedTotal` but different collectors have different completion goals.

**How to avoid:**
- **Offer multiple completion modes:**
  - "Base Set" (uses `printedTotal`)
  - "Master Set" (uses `total` — includes secret rares)
  - "Custom" (user selects which cards count)
- Display both counts: "Complete: 78/78 (Base), 82/88 (Master)"
- Add setting: "Include secret rares in completion percentage"
- Show visual distinction for secret rares (e.g., gold numbering)
- Document completion logic in UI ("Counting base set only")

**Warning signs:**
- User reports "I'm 100% but I know I'm missing cards"
- Confusion about why set shows "78 cards" but others list 88
- User asks "why doesn't my completion change when I add this card?"
- Set progress bar full but user still searching for cards

**Phase to address:**
**Phase 1 (Sets View)** — Completion percentage is a core feature of the Sets View. The logic must handle `printedTotal` vs `total` distinction from day one. Add UI setting for completion mode.

---

### Pitfall 5: Image Loading Performance Death Spiral

**What goes wrong:**
The Cards Album View loads hundreds of high-resolution card images simultaneously, causing browser freeze, memory crashes, or 30-second page loads. Mobile users can't use the app at all.

**Why it happens:**
Pokemon sets contain 100-300+ cards. Loading all card images at once:
- Downloads 50-100MB of images
- Consumes 500MB+ browser memory (decoded images)
- Blocks rendering until images load
- Mobile devices crash from memory pressure

Developers implement the simple "show all cards" approach without considering performance at scale.

**How to avoid:**
- **Implement virtual scrolling** for large card lists (react-window, react-virtualized)
- Use `loading="lazy"` on all card images (already present in existing code ✓)
- Limit initial render to 50-100 cards, paginate or infinite scroll
- Prefer `images.small` over `images.large` for grid views (already doing this ✓)
- Add "Grid size" control (existing requirements ✓) — fewer cards visible = better performance
- Implement image placeholder/skeleton while loading
- Consider progressive image loading (blur-up technique)

**Warning signs:**
- Page takes 10+ seconds to load when viewing large sets
- Browser tab shows "Page Unresponsive" warning
- Mobile browser crashes when opening Cards Album
- Memory usage spikes to 500MB+ in DevTools Performance tab
- Scrolling is janky/laggy in card grid

**Phase to address:**
**Phase 2 (Cards Album View)** — Performance optimization must be built into initial implementation. Virtual scrolling should be considered for sets with 200+ cards. Current code uses lazy loading (good) but no virtualization.

---

### Pitfall 6: Lost Collection Data (No Backup/Export)

**What goes wrong:**
User accidentally clears browser data, switches browsers, or encounters localStorage corruption. Months of collection tracking disappears instantly with no recovery option.

**Why it happens:**
localStorage is:
- Per-browser (Chrome collection doesn't sync to Firefox)
- Vulnerable to "Clear browsing data" operations
- Not backed up by browser sync
- Can be corrupted by browser crashes or extension conflicts

Developers treat localStorage as "persistent" but it's actually fragile.

**How to avoid:**
- **Implement export/import from day one:**
  ```typescript
  // Export collection to JSON file
  exportCollection(): void {
    const data = JSON.stringify(collection);
    const blob = new Blob([data], { type: 'application/json' });
    // Trigger download
  }
  
  // Import collection from JSON file
  importCollection(file: File): void {
    // Parse and merge with existing collection
  }
  ```
- Add prominent "Export Collection" button in settings/stats view
- Implement auto-backup to browser Download folder (weekly reminder)
- Show collection size and last backup date
- Warn when localStorage quota is low: "Export backup recommended"

**Warning signs:**
- User reports "I cleared my cache and lost everything"
- Support requests: "Can you restore my collection?"
- User asks "How do I transfer my collection to my new computer?"
- Reddit posts: "[App Name] deleted my collection"

**Phase to address:**
**Phase 1 or 2** — Export should be in MVP. Import can be Phase 3. The project is explicitly "personal-use, local-first" which makes backup even more critical (no cloud sync safety net).

---

### Pitfall 7: TCGdex API Rate Limiting & Downtime

**What goes wrong:**
App makes too many TCGdex API requests on page load, gets rate limited, and shows empty sets/cards. Or TCGdex service is down and app becomes completely unusable.

**Why it happens:**
TCGdex is a free community API without guaranteed uptime:
- No SLA or guaranteed availability
- Potential rate limits (not well documented)
- Community-hosted infrastructure
- Can experience downtime during high traffic

Over-eager API calls (fetching every set on load, refetching on every interaction) can trigger limits.

**How to avoid:**
- **Implement aggressive caching** (see Pitfall 3 for TTL strategy)
- Batch API requests: Fetch all sets in one call, not per-set calls
- Add loading states and graceful degradation:
  - Show cached data with "Using cached data" notice
  - Provide offline mode: "Cannot connect to card database"
- Implement exponential backoff for retries
- Monitor API response status, handle 429 (rate limit) and 503 (service unavailable)
- Consider fallback: Store minimal set list in app bundle for offline bootstrap

**Warning signs:**
- Console shows repeated 429 or 503 errors
- Sets view shows "Loading..." forever
- Network tab shows dozens of simultaneous API calls
- User reports "app doesn't work" during TCGdex maintenance
- Intermittent failures during peak hours

**Phase to address:**
**Phase 2 (TCGdex Integration)** — Error handling and caching must be implemented during SDK integration. This is a blocking issue for reliability.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store full card objects in localStorage | Simple implementation, fast initial dev | localStorage quota exceeded at ~200 cards, data migration required | **Never** — Will cause production failures |
| Skip virtual scrolling in card grid | Faster initial build | Poor performance on sets with 200+ cards, mobile crashes | Acceptable for MVP if sets are limited to <100 cards visible |
| No collection export feature | Saves 1-2 days dev time | Users lose collections permanently, trust destroyed | **Never** for v1 — Export is table stakes |
| Hardcode base set completion only | Simpler logic | 30% of users want master set tracking, feature requests pile up | Acceptable for MVP, add setting in v1.1 |
| Use Pokemon TCG API instead of TCGdex SDK | Familiar API, existing code patterns | Against project requirements, maintainability issues | **Never** — Explicit project requirement to use TCGdex |
| Skip price data caching | Real-time prices always accurate | Slow page loads, API rate limit issues | Never — Caching required for performance |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **TCGdex SDK** | Assuming all endpoints return same data shape | Read SDK docs carefully — set list vs set details have different schemas |
| **TCGdex SDK** | Not handling null/undefined fields (rarity, HP, artist) | Defensive coding: `card.rarity ?? 'Unknown'` |
| **TCGdex SDK** | Using wrong endpoint for series list | Use `/series` endpoint, not extracting from `/sets` |
| **localStorage** | Directly storing SDK response objects | Store minimal projection, re-fetch full data from SDK |
| **Image URLs** | Hotlinking without checking CORS/availability | TCGdex images should work, but add error fallback image |
| **Card Prices** | Assuming tcgplayer prices always exist | Many cards have no price data — handle nulls gracefully |
| **Set Data** | Caching set list indefinitely | New sets release every ~3 months — implement 7-day TTL |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| **Loading all card images on mount** | 10+ second page load, browser freeze | Lazy loading (✓ already implemented), virtual scrolling | Sets with 150+ cards |
| **Re-rendering entire card grid on ownership toggle** | UI lag when clicking cards quickly | Optimize React renders, use memo, virtualization | 100+ cards in grid |
| **No image caching strategy** | Same images downloaded repeatedly | Browser cache headers work, but add placeholder while loading | Every page navigation |
| **Fetching individual card details in loop** | Slow collection stats calculation | Batch fetch or use set details endpoint (includes all cards) | Collections with 500+ cards |
| **Recalculating stats on every render** | Stats tab is sluggish | Memoize expensive calculations (`useMemo`) | Collections with 200+ cards |
| **Storing base64 images in localStorage** | Quota exceeded immediately | Never store images, only URLs | Single set |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **No visual feedback on ownership toggle** | User unsure if click registered, double-clicks | Immediate visual feedback (already has checkmark/quantity badge ✓) |
| **Hidden completion criteria** | Confusion about why set shows 100% when cards missing | Display "78/78 Base, 82/88 Master" with info tooltip |
| **No search in large sets** | Can't find specific card in 300-card set | Implement search/filter in Cards Album (required feature ✓) |
| **Ownership displayed as true/false only** | Can't track multiple copies | Support quantity tracking (existing code already does ✓) |
| **No progress visibility from set grid** | Must open each set to see progress | Show progress bars on Sets View (required feature ✓) |
| **Destructive actions without confirmation** | User accidentally removes cards | "Remove from collection" should require confirmation |
| **No indication of stale data** | User trusts outdated prices | Show "Prices as of [date]" label |
| **Mobile-unfriendly card images** | Tiny cards unreadable on phone | Card size toggle (required feature ✓) |

---

## "Looks Done But Isn't" Checklist

- [ ] **Set Completion Logic:** Often missing distinction between `printedTotal` and `total` — verify completion calculates based on user's preference
- [ ] **localStorage Persistence:** Often missing quota checks — verify app handles QuotaExceededError gracefully
- [ ] **Card Identity:** Often missing set context in collection display — verify each card shows "Set Name · Number"
- [ ] **Price Display:** Often missing null checks — verify app handles cards without price data
- [ ] **Image Loading:** Often missing error handlers — verify broken image URLs show fallback
- [ ] **Collection Export:** Often "works" but exports invalid JSON — verify exported file can be re-imported successfully
- [ ] **TCGdex Error Handling:** Often missing 429/503 responses — verify app degrades gracefully when API is down
- [ ] **Search/Filter:** Often missing debounce — verify search doesn't re-render on every keystroke
- [ ] **Responsive Design:** Often works on desktop, breaks on mobile — verify card grid, filters, stats all work on phone
- [ ] **Dark Mode:** Often has contrast issues with card images — verify card images readable in dark theme

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **localStorage quota exceeded** | MEDIUM | 1. Implement data projection (strip full card data), 2. Create migration script, 3. Auto-convert user collections on next load |
| **Lost collection data (no export)** | HIGH | Cannot recover — must add export feature and educate users to back up regularly |
| **Stale cached data** | LOW | Add manual refresh button, implement cache busting via timestamp |
| **Set completion miscalculated** | LOW | Fix calculation logic, re-calculate on next app load (no data loss) |
| **Performance issues from loading all images** | MEDIUM | Add virtual scrolling, may require refactoring grid component |
| **TCGdex API rate limited** | LOW | Implement caching, add exponential backoff, reduce API calls |
| **Card identity collision** | HIGH | If users already have merged cards, need data cleanup script + manual user intervention |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Card Identity Crisis | Phase 1: Data Foundation | Test: Add same Pokemon from 2 different sets, verify both appear separately in collection |
| localStorage Size Explosion | Phase 1: Data Foundation | Test: Import 500-card collection, verify localStorage < 2MB |
| Stale Card Data | Phase 2: TCGdex Integration | Test: Load app, wait 25 hours, reload — verify data refreshes |
| Set Completion False Positives | Phase 1: Sets View | Test: Check set with secret rares, verify completion logic matches user's selected mode |
| Image Loading Performance | Phase 2: Cards Album View | Test: Load set with 200+ cards on mobile, verify page loads in < 3 seconds |
| Lost Collection Data | Phase 1 or 2: MVP | Test: Export collection, clear localStorage, import — verify all data restored |
| TCGdex Rate Limiting | Phase 2: TCGdex Integration | Test: Simulate API downtime, verify app shows cached data + error message |

---

## Domain-Specific Validation Rules

When integrating TCGdex SDK, verify these Pokemon TCG data quirks are handled:

1. **Numbering anomalies:**
   - Secret rares: Numbered beyond printedTotal (e.g., "82/78")
   - Promo cards: Numbered with "SWSH" or other prefixes
   - Some sets have gaps in numbering

2. **Card variants in same set:**
   - Regular, reverse holo, holo, full art, rainbow rare
   - Each variant has different ID — don't merge

3. **Multi-card Pokemon:**
   - LEGEND cards (top/bottom halves)
   - BREAK evolution cards
   - V-UNION cards (4-card combination)
   - Treat each piece as separate card for tracking

4. **Set release patterns:**
   - Main sets every ~3 months
   - Special/holiday sets
   - Promotional releases
   - Don't hardcode set list — always fetch from API

5. **Price data limitations:**
   - Not all cards have prices (especially old/promo cards)
   - Prices vary by variant (holo vs regular)
   - Price data may be USD only (check user's region)

---

## Sources

- **Existing codebase analysis** (collection.ts, CollectionView.tsx, CollectionStats.tsx) — Identified current implementation patterns and risks
- **Domain expertise** — Pokemon TCG collection tracking patterns, API integration challenges, localStorage limitations
- **TCGdex documentation** (general knowledge) — API structure, data schema, endpoint patterns
- **Web storage limits** — Browser localStorage quota constraints (5-10MB across browsers)
- **React performance patterns** — Virtual scrolling, lazy loading, memoization strategies

---

*Pitfalls research for: Pokemon TCG Collection Tracker*  
*Researched: 2024-01-20*  
*Confidence: HIGH*
