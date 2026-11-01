# Research Analyzer Professional v4.6

## PLS indicator-level predictive assessment
Repeated k-fold cross-validation reports out-of-fold predictions for each indicator of endogenous reflective constructs. It compares PLS-inspired back-projected predictions against indicator-specific linear-model (LM) and training-mean benchmarks. Metrics include RMSE, MAE and Q²_predict-style scores.

## Workflow
Upload CSV, define constructs and indicators as JSON, specify paths (`X -> Y`), choose folds/repeats/seed, run, and export summary and row-level predictions.

## Methodological boundaries
This is an exploratory Mode-A construct-score procedure with training-fold loadings and OLS benchmarks. It is not a certified or identical SmartPLS PLSpredict implementation. Predictions target observed indicator values and are out-of-fold. Compare with established software on identical data/model/settings before claiming equivalence.
