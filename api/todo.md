# chronos-core-oss


# TODO — Next 2–3 Days (Target: ~6 Hours)

## Scope Goal

Ship one clean vertical slice:
`Universe -> Refresh/Signals -> Template Rules -> Generate Candidates -> Visible Results`

## Time Budget

`6.0h total`

## Checklist

- [ ] `1) Backend: Add scan orchestration endpoint` (`~1.5h`)
Done when:
`POST /universes/{universe_id}/scan` exists and runs refresh + signal compute + candidate generation in one call.
Response includes:
`universe_id`, `template_id`, `tickers_processed`, `ohlcv_rows_written`, `candidates_created`, `errors`.

- [ ] `2) Backend: Add scan run telemetry` (`~0.75h`)
Done when:
A `scan_runs` table (or equivalent) stores start/end/status/metrics/error text.
`/scan` returns `scan_run_id`.

- [ ] `3) Backend: Tighten template rule validation` (`~0.75h`)
Done when:
Template create/update rejects invalid `entry_rules` shape (missing `field/op/value`, unknown `op`, non-numeric `value`).
Returns deterministic `422` detail.

- [ ] `4) Frontend: Universe manager UX polish` (`~0.75h`)
Done when:
Create/update/add ticker forms show visible success/error feedback.
Invalid ticker message is rendered in-page (not only logs/URL).

- [ ] `5) Frontend: Replace debug blocks with workflow panels` (`~1.0h`)
Done when:
Page has 4 sections:
`Universe`, `Template`, `Run Scan`, `Candidates`.
`signal keys` debug text removed or moved behind a dev toggle.

- [ ] `6) Frontend: Template rule editor (minimal v1)` (`~0.75h`)
Done when:
User can add/remove rules:
`field` dropdown, `op` dropdown, `value` input.
Saves template via existing `/templates` endpoint.
No raw JSON required for normal flow.

- [ ] `7) Tests: Integration first` (`~0.5h`)
Done when:
At least these backend integration tests pass:
`invalid ticker -> 422`
`scan happy path -> 201`
`missing template -> 404`
`missing universe -> 404`

## Non-Goals (for this 6h window)

- Broker integration
- Advanced charting/candlestick rendering
- New TA indicators beyond current set
- Full E2E browser automation (can be next block)

## End-of-Window Acceptance

- [ ] From UI, user can:
`create universe -> add valid ticker -> define template rule (e.g., RSI > 75) -> run scan -> see candidate results`
- [ ] Failures are explicit and actionable (no silent no-op paths).
