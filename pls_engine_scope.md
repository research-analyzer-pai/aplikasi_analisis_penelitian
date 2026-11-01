# PLS-SEM prototype: scope and validation protocol

## Current implementation
- Reflective constructs only; Mode A iterative outer weights.
- Single-level constructs; one indicator belongs to one construct.
- Acyclic structural path graph.
- Path coefficients estimated by OLS on estimated standardized construct scores.
- Case bootstrap percentile intervals and empirical two-sided sign p-value.
- Exploratory loadings, AVE, approximate CR, R², inner VIF, HTMT.

## Not implemented
Formative measurement, consistent PLS, exact SmartPLS weighting algorithms, higher-order constructs, moderation, specific indirect-effect bootstrap, Q²/PLSpredict, blindfolding, SRMR, MICOM/MGA, permutation tests, HTMT bootstrap inference, complex missing-data treatment, and measurement invariance.

## Minimum validation before research use
1. Run identical public benchmark datasets in this app and a validated PLS-PM package/SmartPLS.
2. Compare standardized loadings, weights, path coefficients, R², CR, AVE, HTMT, and bootstrap intervals.
3. Test sensitivity to random seed, bootstrap count, sample size, collinearity, and model misspecification.
4. Record differences and do not report the app output as final until differences are understood.
