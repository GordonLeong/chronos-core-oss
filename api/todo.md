git # chronos-core-oss

## TODO — Current Slice (Target: ~6 Hours)

## Explicit Goal (Current Priority)

Deliver a coherent, modern workflow UI on top of the backend already built:
`Select/Create Universe -> Add Ticker (with validation feedback) -> Select/Edit Template Rules -> Run Scan -> Review Candidates`

This means reducing `web/src/app/page.tsx` complexity and replacing debug-style output with focused workflow panels.

## Time Budget

`~6.0h total`

## Status Snapshot

- [x] `Backend: Scan orchestration endpoint` (`POST /universes/{universe_id}/scan`)
- [x] `Backend: Template rule shape validation` (`entry_rules` checks in create/update)
- [x] `Backend integration tests exist` (invalid ticker / missing universe / missing template / scan happy path)
- [ ] `Backend: Scan run telemetry` (`scan_runs` + `scan_run_id` not implemented yet)
- [ ] `Frontend: Workflow-first UI` (still mixed debug + action logic in `page.tsx`)
- [ ] `Frontend: Template rule editor` (still JSON-driven)

## Checklist (Execution Order)

- [-x] `1) Frontend: Split page into workflow panels` (`~1.25h`)
Done when:
`web/src/app/page.tsx` becomes composition-only, with feature sections for:
`Universe`, `Template`, `Run Scan`, `Candidates`.
`stocks` JSON and `signal keys` debug blocks are removed from the main flow.

- [-x] `2) Frontend: Move server actions out of page` (`~0.75h`)
Done when:
Server actions move to `web/src/app/actions.ts` (or similar) and `page.tsx` only loads data and renders sections.

- [-x] `3) Frontend: Universe feedback polish` (`~0.75h`)
Done when:
Create/update/add ticker each show visible in-page success/error messages.
Invalid ticker remains explicit and actionable.

- [x] `4) Frontend: Template rule editor (minimal)` (`~1.25h`)
Done when:
User can add/remove/edit rules with `field/op/value` controls.
Save uses existing `/templates` API without requiring raw JSON editing.

- [x] `5) Backend: Scan run telemetry` (`~1.25h`)
Done when:
A `scan_runs` table (or equivalent) tracks `started_at`, `ended_at`, `status`, metrics, and error text.
`POST /universes/{id}/scan` returns `scan_run_id`.

- [x] `6) Tests: Cover updated scan + UI-facing contracts` (`~0.75h`)
Done when:
Backend tests verify telemetry contract and deterministic error mapping.
Frontend contract assumptions (response shape) are documented and checked.

## Non-Goals (Current Slice)

- Broker integration
- Candlestick chart rendering
- Additional TA packages/indicators
- Full E2E browser automation

## End-of-Slice Acceptance

- [x] UI flow is linear and understandable for non-React users:
`create/select universe -> add ticker -> choose/edit template rules -> run scan -> view candidates`
- [x] No silent no-op actions.
- [x] Core failures are visible in-page with actionable copy.

## Next Action (Do This First)

`Frontend Step 1`: split `web/src/app/page.tsx` into 4 workflow panels and remove debug blocks from the primary user path.

## Detour: UX Refinement (Tailwind)

Goal: Clean up the UI to resemble a modern web application using Tailwind CSS, keeping the structure generic enough for an easy migration to shadcn later.

- [ ] `1) Layout & Typography Polish`
Done when: Global page layout has a modern container, clean background, and updated typography.
- [ ] `2) Card/Panel Styling`
Done when: Workflow panels (Universe, Template, Scan, Candidates) look like modern UI cards (borders, subtle shadows, rounded corners).
- [ ] `3) Form Controls & Buttons`
Done when: Inputs, selects, and buttons have consistent padding, focus states, and hover effects resembling standard shadcn components.

- [ ] `4) Delete Universe`
Done when: A "Delete" button on the Universe panel calls `DELETE /universes/{id}` and redirects cleanly.

- [ ] `5) Rule editor field hints`
Done when: The `field` input in the template rule editor shows the valid signal fields as a datalist/dropdown (`rsi`, `macd`, `ema_20`, `ema_50`, `bb_upper`, `bb_lower`, `macd_signal`).

- [ ] `6) Candidates deduplication / "latest only" view`
Done when: The Candidates panel shows only the most recent scan's results (or groups by ticker+date) instead of accumulating all historical rows.
