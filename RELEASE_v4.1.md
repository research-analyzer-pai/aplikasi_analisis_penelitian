# Release v4.1 — Advanced Research Diagnostics

Release date: 1 November 2026
Base: Research Analyzer Professional v4.0

Added module: `research_diagnostics_v41.py`
- Cronbach alpha + corrected item-total correlation + alpha-if-deleted
- KMO and Bartlett's sphericity screening
- Qualitative coding evidence audit and uncoded-segment review
- Integrated Streamlit tab in `app.py`

Verification:
- Python compileall: passed
- Unit tests: 74 passed, 0 failed
- Streamlit browser/UI smoke test: not run (Streamlit executable unavailable in build environment)
- External live API tests: not run

See `README_v4.1.md` and `CHANGELOG_v4.1.md` for methodological limits.
