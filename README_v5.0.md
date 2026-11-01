# Research Analyzer Professional v5.0

## Major release
### 1. AI-assisted qualitative coding
- TF-IDF lexical similarity suggestions.
- Optional multilingual sentence embeddings (`pip install sentence-transformers`; first model use may require downloading model weights).
- Researcher decision import (`approved`, `rejected`, `revise`, `pending`) with reviewer identity.
- Suggestion/decision coverage indicators.
- Suggestions remain pending; no autonomous approval or final thematic interpretation.

### 2. Mixed-methods meta-inference workspace
- Explicit researcher-entered integration relationship: convergence, complementarity, expansion, divergence, silence, unrelated, undetermined.
- Completeness audit and narrative export.
- The application does not decide the relationship automatically.

### 3. Academic Word report
- Builds a DOCX report structure for Bab IV and Bab V.
- Includes quantitative, qualitative, joint-display and meta-inference tables supplied by the researcher.
- Uses Times New Roman 12 and standard page margins.
- Does not invent results, quotations, theory, or references.

## Validation and limits
Unit tests validate core helper functions and input checks. Streamlit interface should be tested in the user's local environment. Embedding quality must be benchmarked with manually coded data; similarity is not coding validity. Report contents require researcher verification and journal/university formatting adjustment.
