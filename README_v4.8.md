# Research Analyzer Professional v4.8

## Mixed Methods Evidence Integration
This release adds an evidence-linked joint display workflow. It links imported quantitative paths and coefficients with qualitative themes and unique evidence IDs, checks path/evidence/theme matching, summarizes linkage quality, and exports the joint display, audit, and path-level synthesis as CSV.

### Input CSV schemas
- Quantitative: `path`, `beta`, optional `p`.
- Qualitative: `theme`, `evidence_id`, `evidence`, optional `source`, `technique`.
- Mapping: `quant_path`, `theme`, `evidence_id`, `integration_rationale`.

### Methodological limits
Structural link validation does not establish substantive validity, convergence, complementarity, or contradiction. The application does not automatically decide meta-inferences. Researchers must inspect original transcripts/field notes, contextualize quotations, and document how the qualitative evidence explains, expands, contradicts, or fails to relate to quantitative findings.
