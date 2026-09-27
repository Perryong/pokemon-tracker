# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Pokémon TCG collectors browsing sets, checking card information and market prices, and recording owned quantities. Collection-first is the working assumption for this redesign, following the user's instruction to proceed.

## Product Purpose

Help collectors find cards, understand what they own, and see what remains missing from each set.

## Operating Context

Responsive browser app with local collection storage. Browse sets by series, open a set, inspect a card, adjust quantities, and revisit the collection.

## Capabilities and Constraints

React, TypeScript, Vite, Tailwind, existing Radix UI components. TCGdex supplies set summaries, series membership, images, full card details, and optional marketplace pricing. Prices retain provider currencies and update dates. Collection quantities stay in the existing version 3 localStorage format. No accounts or cloud synchronization. Preserve existing saved data and API caching. Collection metadata such as condition, notes, and purchase price is outside this redesign.

## Evidence on Hand

Live TCGdex assets and API responses; source in src/lib; regression tests in src/components/__tests__ and src/lib/__tests__. No invented collection counts, values, release dates, or prices.

## Product Principles

- Card artwork is the primary content.
- Browsing and quantity updates should be easy on mobile and desktop.
- Saved quantities must stay consistent between views.
- Missing API data is shown honestly.
