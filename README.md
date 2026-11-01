# Research Analyzer Professional v3.5

Research-support application for quantitative, qualitative, mixed-methods, literature-review, and manuscript workflows.

## New in v3.5

### AI Qualitative Intelligence & Mixed Methods
- TF-IDF code suggestions against a researcher-authored codebook (transparent lexical baseline).
- Coding coverage metrics and uncoded-segment review for possible negative/deviant cases.
- Code co-occurrence matrix.
- Editable quantitative–qualitative joint display with explicit researcher integration notes.
- CSV exports for all new outputs.

## Retained capabilities from v3.4

### Advanced Qualitative Intelligence

### Advanced Qualitative Intelligence
- Hierarchical codebook with parent-child code validation.
- Transcript chunking that preserves segment IDs for auditable AI analysis.
- Theme evidence matrix linking themes, codes, and transcript segments.
- Researcher coding audit status (approved, pending, rejected).
- Source/technique triangulation overview.
- CSV exports for codebook, coding audit, theme evidence, and triangulation.

### Journal Publication Readiness
- User-configured target journal, article type, reference style, and abstract word limit.
- Internal checklist for title, abstract, keywords, article sections, and reference availability.
- Word count and DOI-presence indicators.
- Downloadable manuscript outline with declarations placeholders.
- AI journal adaptation prompt available in AI Research Studio.

## Earlier modules
- Statistical analysis and OLS regression.
- PLS-SEM prototype and imported SEM results.
- Research Intelligence and theory/indicator mapping.
- Literature matrix, Crossref metadata discovery, RIS/BibTeX/CSV import.
- PRISMA-style screening workflow.
- AI Research Studio via optional OpenAI Responses API.

## Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important limitations
- Qualitative AI suggestions are not final interpretations. Check original quotations, negative cases, context, reflexivity, and researcher decisions.
- Chunking preserves segment IDs but does not guarantee complete context across batches.
- Theme evidence and triangulation summaries depend on coding and metadata entered by the researcher.
- The journal checklist is a user-configured internal check, not an automatic verification of a journal's current author guidelines, indexing, quality, or acceptance likelihood.
- DOI presence is not a universal requirement for every reference.
- PLS-SEM remains a prototype with approximations; compare results with established software before publication.
- AI requests transmit submitted content to the configured API provider and may incur charges. Anonymize participant data and protect confidential materials.

See `docs/v3.5_scope.md`, `CHANGELOG_v3.5.md`, and previous version scope documents.

## v3.5 methodological boundary
The TF-IDF recommender is not generative AI, not a validated semantic model, and not an automatic thematic-analysis engine. Researcher review is mandatory. PLS-SEM remains an exploratory prototype; compare with validated software before publication.
