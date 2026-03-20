# Feature Landscape: Pokemon TCG Collection Tracker

**Domain:** Pokemon Trading Card Game collection management
**Researched:** 2024-03-20
**Confidence:** MEDIUM (training data + project context analysis)

## Executive Summary

Pokemon TCG collection trackers exist in a mature ecosystem with established patterns. Based on analysis of major platforms (Pokellector, TCGCollector, TCG Hub, CollX) and community expectations, the feature landscape divides into three categories:

**Table Stakes** features are centered around card ownership tracking, set browsing, visual card display, and progress tracking. Users expect to mark cards as owned, see completion percentages, filter by set/series, and have data persist. Missing these makes a tracker feel incomplete.

**Differentiators** include advanced features like price tracking, multi-condition/quantity tracking, deck building, trade management, and social features. These separate premium products from basic trackers but aren't required for core value.

**Anti-Features** to avoid include marketplace integration, social feeds, and gamification—these add complexity without serving the core "track my collection" use case for personal trackers.

## Table Stakes

Features users expect in any Pokemon TCG collection tracker. Missing these = product feels incomplete or unusable.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Card Ownership Toggle** | Core value proposition—mark cards as owned/not owned | Low | Click/tap to toggle; visual indicator (checkmark, badge, opacity) |
| **Set Browsing** | Users organize by set; must browse full set list | Low | List/grid view with set logos, names, release dates |
| **Set Completion Progress** | Users track "how complete" their collection is per set | Low | Progress bar + percentage (e.g., "45/102 - 44%") |
| **Card Images** | Users need visual confirmation of the right card | Medium | High-quality images; handle missing images gracefully |
| **Series/Era Filtering** | 1000+ sets make browsing overwhelming without grouping | Low | Filter by series (Base Set, Sword & Shield, Scarlet & Violet, etc.) |
| **Card Search** | Users need to find specific cards quickly | Medium | Text search by card name within set or across sets |
| **Persistence** | Collection data must survive app restarts | Medium | localStorage, IndexedDB, or backend storage |
| **Set Statistics** | Per-set owned/missing counts visible at set level | Low | Show "45 owned, 57 missing" before entering set |
| **Responsive Card Grid** | Users view on desktop and mobile | Medium | Grid adapts to screen size; cards remain legible |
| **Set Release Info** | Users want to know set name, code, release date, total cards | Low | Display metadata from TCGdex or similar API |

### Rationale

These features form the minimum viable collection tracker. Users coming from competitors (Pokellector, TCGCollector) expect this baseline. Omitting any of these creates friction that drives users away.

## Differentiators

Features that set products apart. Not expected by default, but valued when present.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multi-Quantity Tracking** | "I own 3 Charizards" vs just "I own this card" | Medium | Numeric input instead of boolean toggle; affects stats |
| **Card Condition Tracking** | Track condition (Mint, Near Mint, Played, Damaged) | Medium | Important for collectors; less so for casual trackers |
| **Price Tracking** | Show current market value of collection | High | Requires price API (TCGPlayer, CardMarket); updates frequently |
| **Wishlist/Want List** | Separate "owned" from "want to own" | Medium | Second toggle state; affects filtering and stats |
| **Card Variants** | Track different prints (1st edition, holo, reverse holo) | High | Complex data model; TCGdex has variant support |
| **Deck Building** | Build decks from owned cards | High | Different mental model; requires legality rules |
| **Import/Export** | Bulk import from CSV or other formats | Medium | Reduces manual entry; format standardization is hard |
| **Collection Value** | Total collection worth based on market prices | High | Depends on price tracking; aspirational metric |
| **Rarity Filtering** | Filter by rarity (Common, Uncommon, Rare, Ultra Rare, etc.) | Low | TCGdex provides rarity data; useful for completion |
| **Card Details View** | Modal/page with full card info (attacks, HP, artist, etc.) | Medium | Enriches experience; not core to ownership tracking |
| **Offline Support** | Full functionality without internet | High | PWA with service worker; complex data sync |
| **Multi-User/Accounts** | Track multiple collections or share across devices | High | Requires backend, auth, sync logic |
| **Trade Management** | Track pending trades, trade history | High | Social/marketplace adjacent; niche use case |
| **Binder View** | Display cards in 9-pocket binder page layout | Medium | Mimics physical organization; strong aesthetic appeal |
| **Completion Badges** | Gamification for completing sets/series | Low | Visual reward system; motivational but not functional |
| **Dark Mode** | Theme toggle for visual preference | Low | Expected in modern apps; not unique to TCG trackers |
| **Bulk Ownership Actions** | Mark all commons as owned, mark full set, etc. | Medium | Efficiency feature for large collections |
| **Set Sorting** | Sort sets by release date, name, completion % | Low | Improves navigation; expected in mature products |
| **Advanced Stats** | Charts for collection growth, rarity breakdown, value over time | High | Analytics layer; appeals to data-driven collectors |

### Rationale

Differentiators separate premium from basic trackers. **Multi-quantity** and **wishlist** are common upgrades. **Price tracking** is highly valued but requires ongoing data partnerships. **Offline support** and **accounts** enable cross-device use but add infrastructure complexity. **Deck building** serves a different use case (competitive play vs collection management).

## Anti-Features

Features to explicitly NOT build in v1 (or ever, depending on product vision).

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Marketplace/Trading Platform** | Requires trust systems, payment processing, dispute resolution; high liability | Link to external marketplaces (TCGPlayer, eBay) |
| **Social Feed** | Content moderation, spam, user engagement metrics; dilutes focus | Keep personal; defer social to v2+ if validated |
| **Card Grading Integration** | Niche use case (PSA/BGS grading); complex data model for small user segment | Treat graded cards as separate "condition" if needed later |
| **Pull Tracker** | Track booster pack openings and pull rates; tangential to collection management | Separate app concept; adds noise to collection view |
| **Authentication/Login (v1)** | Backend dependency, password management, delays core value delivery | Use localStorage; defer accounts until multi-device validated |
| **Collection Sharing/Public Profiles** | Privacy concerns, hosting costs, moderation; unclear value for personal tracker | Keep private; export to shareable format if needed |
| **Gamification Beyond Completion** | Badges, streaks, leaderboards add maintenance and distract from utility | Completion % is sufficient motivation |
| **Card Scanning/OCR** | High development cost; error-prone; marginal time savings over manual entry | Manual toggle is fast enough for personal collections |
| **Multi-Game Support** | Supporting Yu-Gi-Oh, Magic, etc. fragments focus and complicates data model | Stay Pokemon-only; best-in-class for one game beats mediocre for many |
| **Collection Insurance** | Legal/financial complexity; requires partnerships and compliance | Not a software problem |
| **Printable Checklists** | Print is outdated; adds export complexity for niche need | Digital-first experience is sufficient |

### Rationale

Anti-features either add complexity without core value (marketplace, social), serve niche segments (grading, insurance), or conflict with v1 scope (accounts, multi-device). The project explicitly scopes out accounts and social features, which aligns with anti-feature analysis. Staying focused on personal, local-first tracking maximizes v1 velocity.

## Feature Dependencies

```
Card Ownership Toggle
  └─> Set Completion Progress (requires ownership data)
  └─> Set Statistics (requires ownership data)
  └─> Collection Value (requires ownership + price data)

Set Browsing
  └─> Series/Era Filtering (requires set metadata)
  └─> Set Sorting (requires set metadata)

Card Images
  └─> Card Details View (extends image display with metadata)
  └─> Binder View (uses images in layout)

Persistence
  └─> ALL ownership features depend on this

Card Search
  └─> Advanced search (filters + text search combined)

Multi-Quantity Tracking
  └─> Collection Value (quantity * price)
  └─> Trade Management (track quantities in trades)

Price Tracking
  └─> Collection Value (aggregates prices)
  └─> Wishlist Value (shows cost to complete)

Accounts/Backend
  └─> Multi-Device Sync (requires accounts)
  └─> Social Features (requires accounts)
  └─> Trade Management (requires accounts)
```

### Critical Path

For MVP, prioritize this dependency chain:
1. **Persistence** (foundation for everything)
2. **Set Browsing + Series Filtering** (navigation)
3. **Card Images + Ownership Toggle** (core interaction)
4. **Set Completion Progress** (motivation/feedback)
5. **Card Search** (usability at scale)

## MVP Recommendation

### Phase 1: Core Tracking (Table Stakes)

**Must Have:**
1. ✓ Set browsing with set logos and metadata (EXISTING per PROJECT.md)
2. ✓ Series dropdown filtering (ACTIVE requirement)
3. ✓ Card album view with card images (EXISTING pattern)
4. ✓ Click-to-toggle ownership with visual indicator (ACTIVE requirement)
5. ✓ Set completion progress bars and percentage (ACTIVE requirement)
6. ✓ localStorage persistence (EXISTING pattern)
7. ✓ In-set name search (ACTIVE requirement)
8. ✓ Real-time stats footer (owned/missing/completion %) (ACTIVE requirement)

**Defer to Phase 2:**
- Rarity filtering (nice-to-have; rarity data available from TCGdex)
- Card details modal (enhances but not critical)
- Set sorting options (release date default is sufficient for v1)
- Dark mode (polish feature)

**Defer to Phase 3+:**
- Multi-quantity tracking (changes data model; validate basic ownership first)
- Wishlist (second dimension; prove ownership tracking first)
- Price tracking (external dependency; high complexity)
- Offline PWA (polish; localStorage already handles session persistence)
- Bulk ownership actions (efficiency; validate manual flow first)

### Rationale

The project's ACTIVE requirements already target the exact table stakes features. This validates the feature scope against ecosystem expectations. All table stakes are either EXISTING or ACTIVE, which means v1 will deliver a complete basic tracker.

Missing differentiators (multi-quantity, wishlist, price tracking) are appropriate deferrals—prove core value before adding complexity.

## Complexity Analysis

| Complexity | Features | Estimated Effort | Risk |
|------------|----------|------------------|------|
| **Low** | Ownership toggle, set completion, series filter, set stats, search | 1-2 days each | Low; well-understood patterns |
| **Medium** | Card images, responsive grid, persistence, card details, wishlist, import/export, multi-quantity | 3-5 days each | Medium; integration complexity |
| **High** | Price tracking, deck building, offline PWA, accounts, trade management, advanced stats | 1-2 weeks each | High; external dependencies or architecture changes |

## Competitive Landscape

Based on training data knowledge of major Pokemon TCG collection trackers:

### Pokellector
- **Strengths:** Comprehensive set coverage, clean UI, free tier
- **Table Stakes:** All present (ownership, sets, search, progress)
- **Differentiators:** Wishlist, rarity filters, set checklists
- **Notable Gap:** No price tracking, no mobile app (web only)

### TCGCollector
- **Strengths:** Mobile-first, offline support, barcode scanning
- **Table Stakes:** All present
- **Differentiators:** Multi-quantity, condition tracking, deck building
- **Notable Gap:** Limited web version; iOS-centric

### CollX (formerly TCGPlayer Scanner)
- **Strengths:** Price tracking, card scanning, marketplace integration
- **Table Stakes:** All present
- **Differentiators:** Real-time prices, integrated selling, multi-game
- **Notable Gap:** Heavy marketplace focus; less pure collection tracking

### Opportunity

Existing products either:
1. **Web-focused but limited** (Pokellector)—no prices, basic features
2. **Mobile apps with paywalls** (TCGCollector)—gated features, platform lock-in
3. **Marketplace-first** (CollX)—trading/selling overshadows pure collection tracking

**Positioning:** A polished, free, web-first tracker with offline persistence and no account requirement fills a gap between Pokellector's simplicity and TCGCollector's complexity. Focus on personal tracking without marketplace noise.

## Feature Validation Questions

Questions to validate with users/analytics after v1:

1. **Multi-quantity:** Do users track duplicates, or is boolean ownership sufficient?
2. **Wishlist:** Do users want separate "want" vs "own" states?
3. **Price tracking:** Do users care about collection value, or just completion?
4. **Deck building:** Is this tracker for collectors or players? (Separate use cases)
5. **Cross-device:** Do users need to access from multiple devices?
6. **Bulk actions:** Do power users need "mark all commons" efficiency tools?
7. **Binder view:** Does digital binder aesthetic add value vs grid view?

## Sources

**Confidence Level: MEDIUM**

This analysis is based on:
- Training data knowledge of major Pokemon TCG collection tracker products (Pokellector, TCGCollector, CollX/TCGPlayer Scanner, TCG Hub)
- General patterns from trading card collection management software
- Project context from PROJECT.md showing existing architecture and active requirements
- TCGdex API capabilities inferred from SDK usage patterns

**Limitations:**
- No real-time web search available (Brave API key not configured)
- Cannot verify current 2024 feature sets or recent product updates
- Competitive landscape may have shifted since training data cutoff
- User community feedback not directly consulted

**Verification Needed:**
- Current feature sets of major competitors (Pokellector, TCGCollector, CollX)
- User community discussions (Reddit r/PokemonTCG, Discord servers)
- Recent product launches or updates in this space
- Pricing/monetization models of competitors

**Recommendation:** Treat table stakes as validated (consistent across training data), but verify differentiator prioritization with quick user research or competitor analysis before investing in complex features.
