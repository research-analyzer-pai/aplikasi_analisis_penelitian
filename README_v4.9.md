# Research Analyzer Professional v4.9

## Advanced Qualitative Case Analysis
- Informant-by-theme matrix.
- Cross-case theme comparison.
- Supporting and counter/negative evidence profile.
- Coding-process audit for uncoded segments, analytic memos, quotations and researcher review status.
- Uncoded segment review queue.
- Descriptive code accumulation by interview/observation wave (`wave` column).
- CSV exports through the Streamlit interface.

### Input
Segments CSV: `segment_id`, `source`, `participant`, `text`; optional `wave`.
Coding CSV: `segment_id`, `code`, `theme`; optional `evidence_type`, `analytic_memo`, `evidence_quote`, `researcher_status`.
For counter-evidence, use `evidence_type` values such as `negative`, `counter`, `contradictory`, `disconfirming`, or `deviant`.

### Methodological limits
Counts are descriptive audit aids, not measures of theme importance. Code accumulation by wave is not proof of theoretical/data saturation. Researchers must determine case boundaries, interpret context, review negative cases, and justify saturation based on design, information power, and evidence.
