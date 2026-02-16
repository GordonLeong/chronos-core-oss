# chronos-core-oss

# TODO — Current Slice (Target: ~6 Hours)

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

- [ ] `1) Frontend: Split page into workflow panels` (`~1.25h`)
Done when:
`web/src/app/page.tsx` becomes composition-only, with feature sections for:
`Universe`, `Template`, `Run Scan`, `Candidates`.
`stocks` JSON and `signal keys` debug blocks are removed from the main flow.

- [ ] `2) Frontend: Move server actions out of page` (`~0.75h`)
Done when:
Server actions move to `web/src/app/actions.ts` (or similar) and `page.tsx` only loads data and renders sections.

- [ ] `3) Frontend: Universe feedback polish` (`~0.75h`)
Done when:
Create/update/add ticker each show visible in-page success/error messages.
Invalid ticker remains explicit and actionable.

- [ ] `4) Frontend: Template rule editor (minimal)` (`~1.25h`)
Done when:
User can add/remove/edit rules with `field/op/value` controls.
Save uses existing `/templates` API without requiring raw JSON editing.

- [ ] `5) Backend: Scan run telemetry` (`~1.25h`)
Done when:
A `scan_runs` table (or equivalent) tracks `started_at`, `ended_at`, `status`, metrics, and error text.
`POST /universes/{id}/scan` returns `scan_run_id`.

- [ ] `6) Tests: Cover updated scan + UI-facing contracts` (`~0.75h`)
Done when:
Backend tests verify telemetry contract and deterministic error mapping.
Frontend contract assumptions (response shape) are documented and checked.

## Non-Goals (Current Slice)

- Broker integration
- Candlestick chart rendering
- Additional TA packages/indicators
- Full E2E browser automation

## End-of-Slice Acceptance

- [ ] UI flow is linear and understandable for non-React users:
`create/select universe -> add ticker -> choose/edit template rules -> run scan -> view candidates`
- [ ] No silent no-op actions.
- [ ] Core failures are visible in-page with actionable copy.

## Next Action (Do This First)

`Frontend Step 1`: split `web/src/app/page.tsx` into 4 workflow panels and remove debug blocks from the primary user path.
