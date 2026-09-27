---
name: "Pokémon Tracker — Collector's archive"
description: "A quiet field catalogue for browsing cards and recording a local collection."
colors:
  background: "hsl(60 24% 96%)"
  foreground: "hsl(140 16% 16%)"
  card: "hsl(0 0% 100%)"
  card-foreground: "hsl(140 16% 16%)"
  popover: "hsl(0 0% 100%)"
  popover-foreground: "hsl(140 16% 16%)"
  primary: "hsl(151 43% 25%)"
  primary-foreground: "hsl(60 24% 96%)"
  secondary: "hsl(88 21% 91%)"
  secondary-foreground: "hsl(140 16% 16%)"
  muted: "hsl(60 20% 91%)"
  muted-foreground: "hsl(132 6% 37%)"
  accent: "hsl(114 22% 91%)"
  accent-foreground: "hsl(151 43% 25%)"
  destructive: "hsl(0 60% 39%)"
  destructive-foreground: "hsl(0 0% 100%)"
  border: "hsl(88 14% 83%)"
  input: "hsl(88 14% 78%)"
  ring: "hsl(151 43% 25%)"
  well: "#eeeee4"
  rail: "#efefe7"
typography:
  display:
    fontFamily: "Georgia, 'Times New Roman', serif"
    fontSize: "42px"
    fontWeight: 400
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Georgia, serif"
    fontSize: "32px"
    fontWeight: 400
    letterSpacing: "-0.025em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 650
    lineHeight: 1.35
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "13px"
    lineHeight: 1.7
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "11px"
    fontWeight: 600
  control:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "12px"
rounded:
  badge: "4px"
  stepper: "5px"
  chip: "6px"
  control: "7px"
  navigation: "8px"
  button: "10px"
  surface: "12px"
spacing:
  inline: "8px"
  control: "12px"
  art-inline: "13px"
  compact: "14px"
  mobile-gap: "16px"
  filter: "18px"
  content: "20px"
  set-gap: "22px"
  art: "25px"
  section: "27px"
  narrow-page: "30px"
  page: "38px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.button}"
    padding: "8px 16px"
    height: "36px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.button}"
    padding: "8px 16px"
    height: "36px"
  button-ghost:
    textColor: "{colors.foreground}"
    rounded: "{rounded.button}"
    padding: "8px 16px"
    height: "36px"
  input:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "42px"
  series-chip:
    textColor: "{colors.muted-foreground}"
    rounded: "{rounded.chip}"
    padding: "0 13px"
    height: "42px"
  series-chip-selected:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary}"
    rounded: "{rounded.chip}"
    padding: "0 13px"
    height: "42px"
  navigation-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.navigation}"
    padding: "0 12px"
    height: "46px"
  specimen:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.surface}"
  quantity-stepper:
    rounded: "{rounded.stepper}"
    width: "42px"
    height: "42px"
---

# Design System: Pokémon Tracker

## Overview

**Creative North Star: "Collector's archive"**

A museum’s field catalogue translated into a collector’s binder: quiet cream paper, forest selection states, and carefully separated card specimens. Serif subject headings give the collection character while sans controls keep inventory work clear.

Artwork is evidence. Real logos and cards occupy neutral wells; counts and prices remain factual, and ownership is visible beside the controls that change it. The collection is local to this device and retains the existing version 3 storage format.

**Key Characteristics:**

- Cream paper and forest green
- Serif subjects, sans inventory controls
- Contained artwork and visible ownership

## Colors

### Primary

Forest is the action and ownership color; primary-foreground is its readable inverse. Ring shares the primary hue.

### Secondary

Pale foliage supports quiet secondary surfaces. Accent highlights selected chips and hover states. Destructive marks failed saves and data errors.

### Neutral

Background is cream canvas, card/popover is paper, well contains artwork, and rail separates navigation. Foreground is dark botanical ink; muted-foreground supports metadata. Border separates specimens; input provides a stronger control boundary. Canonical values are the HSL expressions in frontmatter, sourced from `src/index.css`, not approximate hex translations.

Dark appearance replaces the same semantic CSS variables: deep green canvas and paper, pale green primary, and light botanical ink. Exact overrides live in the sidecar; maintain semantic assignments across themes.

**The The Ownership Rule.** Use forest to identify active navigation, selected filters, owned cards, and collection actions.

## Typography

Georgia with serif fallbacks gives subjects a bookish voice. System sans carries the inventory. Display headings reduce to (34px) below the mobile breakpoint; detail titles reduce to (28px). Body descriptions are bounded to (65ch). Set titles use the title token; card titles are (13px / 1.4, weight 650). Metadata and inventory numbers use (10–12px). Quantities, summaries, and prices use tabular numerals.

**The The Subject Rule.** Use Georgia for subject headings; keep controls, metadata, quantities, and prices in system sans.

## Layout

The fixed desktop rail is (224px); it narrows to (200px) at (1050px). The main page is bounded to (1350px), including padding, with gutters (38px), (30px) below (1250px), and (20px) below (760px). The context bar is (65px) high and disappears on mobile.

Set grids use three columns with (22px) gaps, two below (1050px), and one below (480px). Card grids use five columns, four below (1250px), three below (1050px), and two below (480px). Compact cards use six, five, three, and two columns at those same widths. Mobile card gaps are (13px); mobile set gaps are (16px).

Below (760px), the rail becomes a compact static header with horizontal navigation. Filters wrap; the search field occupies a full row. Set artwork wells are (174px) high on desktop, (155px) on mobile, and (190px) at the smallest breakpoint. Card artwork retains its (245 / 337) aspect ratio with contained images. The detail dialog is bounded to (850px / 92vh), with two columns that stack below (760px).

## Elevation & Depth

Most hierarchy comes from cream canvas, paper surfaces, warm artwork wells, and one-pixel borders. Generic primary buttons carry the standard Tailwind shadow; outline buttons carry shadow-sm. The detail dialog carries shadow-lg over a black (80%) overlay. These restrained existing elevations do not imply shadows on inventory specimens.

**The The Specimen Rule.** Keep inventory cards flat; separate artwork wells from information with tone and borders.

## Shapes

Specimens, filter trays, and artwork panels share soft surface corners. Controls, navigation, chips, and ownership badges use smaller radii from the frontmatter. The generic button radius resolves from the root radius minus (2px), so it is (10px), not the (7px) native filter-control radius. Progress rails are fully rounded and only (4px) high in set specimens.

## Components

**Buttons:** Forest primary, bordered outline, and transparent ghost variants share system sans (14px, weight 500). Primary hover uses forest at (90%) opacity; outline/ghost hover uses accent. Disabled controls are visibly muted. Quantity stepper buttons are (42 × 42px); native inputs, series chips, theme control, and dialog close are (42px) high. Generic action buttons currently remain (36px), and the set back link (30px): these are implementation drift against the intended touch-target floor, not standards for new controls.

**Filters:** Use labelled native search, select, date, and number inputs inside a paper tray. Inputs retain explicit borders, cream fill, and a (2px) forest focus outline. Unknown summary fields disable unavailable selectors and explain the absence.

**Navigation:** Active items use forest with inverse text; hover uses muted paper. Desktop items are (46px) high, mobile items (43px). Real collection totals drive the count and binder summary.

**Set specimens:** Contained logos sit above set names, card totals, and owned progress. Logo failure falls through to a symbol, then an explicitly labelled catalogue emblem. The emblem is a fallback identifier, not invented official artwork. Hover strengthens the specimen border over (180ms).

**Card specimens:** Owned borders and badges mark state. Artwork lifts by (3px) on hover over (180ms), without hiding actions. Missing images have explicit text. Quantity controls disable at zero and the (999) ceiling; saved ownership is shared with collection and detail.

**Detail and collection:** A scrollable dialog pairs large contained artwork with Card Info, Market Data, and Collection tabs. Prices are provider-labelled tables with original currency and update dates. Local save errors stay visible; failed collection metadata requests preserve quantities. Empty and loading states retain bounded catalogue surfaces. Reduced motion disables animation and transitions.

**The The Visible Quantity Rule.** Keep Add/Remove and quantity controls visible beneath artwork, never available only on hover.

## Do's and Don'ts

### Do:

- Do preserve contained card artwork and honest missing-data states.
- Do keep focus visible and respect reduced motion.
- Do keep quantity updates consistent across the set, collection, and detail views.

### Don't:

- Don't invent card counts, prices, release dates, or ownership.
- Don't hide collection controls behind hover.
- Don't add accounts, cloud synchronization, or replace version 3 saved quantities as part of visual work.
