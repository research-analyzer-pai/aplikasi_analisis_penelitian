# Changelog v4.0 — 1 November 2026

## Added
- Crossref DOI lookup and title search.
- Batch reference metadata audit from CSV.
- Metadata comparison report that preserves user-supplied values.
- Journal submission checklist and user-defined word/keyword limit checks.
- Author declaration draft template.
- AI task prompts for literature-matrix synthesis and journal submission audit.
- Two Streamlit tabs for Crossref and journal submission workflows.

## Validation
- 70 unit tests passed.
- Python compileall passed.
- Crossref HTTP behavior tested with mocked responses; live endpoint not certified.
- Full Streamlit browser workflow and live AI API not tested.

## Known limitations
- Existing PLS-SEM estimator remains an explicitly labelled prototype.
- Crossref metadata coverage depends on deposits and is not a journal-quality metric.
- Journal requirements are user-supplied; no automated scraping or submission is performed.
