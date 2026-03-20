# Deferred Items for Phase 01

1. **Collection dashboards contain unresolved legacy code**
   - **Files:** `src/components/CollectionStats.tsx`, `src/components/CollectionView.tsx`
   - **Issue:** Both files include large blocks of legacy UI (price charts, tabs, etc.) appended after the default export, leaving stray braces and causing `tsc --noEmit --project tsconfig.app.json` / `npm run build` to fail with `TS1128: Declaration or statement expected`.
   - **Context:** These files were already modified and failing before Plan 01-03 execution. They are unrelated to the TCGdex hook migration but currently block full-project builds.
   - **Next Step:** Either restore the intended MVP implementations or finish the WIP dashboard code so the files contain a single valid component.
