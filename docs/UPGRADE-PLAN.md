# Upgrade plan — book-procurement-data

Score: 5.5/10 -> 7.5/10 (pass 1) -> 7.5/10 (pass 2) — one malformed OCDS release (null tag/buyer/period or non-RFC3339 end date) crashed or invalidated the whole capture; no CI.

## Backlog

- P0: Confirm the new GitHub Actions CI is green on the first push and keep it required.
- P1: Page through Contracts Finder results (`cursor`) instead of the fixed first 100 notices.
  Paging happens in the shared capture runtime (`fetch_query`), so it needs a runtime change
  plus a reviewed live response for the `links.next` shape; not doable offline here.
- P1: Live-source monitoring (drift alerts) stays in the shared runtime; keep adapters pure.
- P2: Fill the PRODUCT.md acceptance-gate table only with evidence that exists (CI run link,
  replay report); do not mark gates passed without it.
- P2: Consider extracting the byte-identical `cli.py` shared by the sibling `book-*-data`
  products into one versioned package once a consumer exists (today each repo vendors it).

## Done in this pass (pass 1)

- Fixed: capture no longer crashes (TypeError/AttributeError) on null `tag`, `buyer`,
  `tenderPeriod`, `value`, `suitability` or `documents`, and non-dict bodies/licence fail as
  drift (ValueError). End dates now use the contract's RFC3339 parser, so one release with a
  space-separated or naive end date is skipped instead of failing validation for every record.
  Fallback notice URLs percent-encode the OCID. Regression tests in `tests/test_source.py`.
- Added `.github/workflows/ci.yml`: Python 3.10/3.12 matrix, `pip install -e ".[dev]"`,
  `ruff check .`, `pytest`, and a `contract`/`validate`/`demo` CLI smoke. Verified by
  replaying those steps in a clean Python 3.10 venv.
- Added `[project.optional-dependencies] dev`, pytest config (`pythonpath = src`) and an
  explicit ruff rule set (E4/E9/F/I/B/UP); fixed the resulting import-order/encode lint.
- Added `tests/test_policy.py`: `sources.json` ↔ `source*.json` ↔ schema category
  consistency, duplicate policy copies identical, https/no-query URLs, 6h minimum
  interval, `--source-id` traversal rejection, capture fail-closed without
  `SOLO_EMPIRE_ROOT`, CLI `validate` exit codes without echoing input, bad demo clock.
- README: documented the developer/CI commands and offline test boundary.

## Done in this pass (pass 2)

- OCDS `tender.eligibilityCriteria` is appended to `terms.vendor_requirements` when it is a
  non-empty string: markup stripped, whitespace collapsed, e-mails/URLs/phone numbers
  redacted (source policy forbids republishing contact bodies; dates and amounts kept),
  capped at 400 characters. Absent/non-string/blank values leave the old text unchanged.
  Regression test in `tests/test_source.py`.
- `source.json` stays content-identical to `source-contracts-finder-open-tenders.json`
  (asserted by `tests/test_policy.py`).
