# Research Analyzer Professional v4.7

## Advanced multi-group inference
- Bootstrap confidence intervals for differences in structural path coefficients between two groups.
- Two-sided label-permutation p-values for group differences.
- Combined output with the existing MICOM-inspired compositional/mean/variance diagnostics.
- Streamlit interface and CSV exports for both result tables.

## How to use
Upload a CSV containing the group variable and indicator columns. Define construct blocks as JSON, specify structural paths (`X -> Y`), enter the group-column name, and choose bootstrap/permutation counts.

## Methodological limitations
The implementation uses this application's exploratory Mode-A score algorithm. It is a two-group approximation and does not constitute canonical MICOM, PLS-MGA, or SmartPLS equivalence. The MICOM-inspired check is retained as a screening aid; formal measurement-invariance claims should be verified using established software and the canonical three-step MICOM procedure. Interpret nonsignificant tests as failure to reject differences, not proof of equality. Bootstrap confidence intervals and permutation tests are complementary, not interchangeable.
