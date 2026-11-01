# Research Analyzer Professional v4.5

- Added repeated k-fold out-of-fold prediction assessment for endogenous construct scores.
- Reports RMSE, MAE, cross-validated Q²-style metric against a training-mean benchmark, and whether prediction beats that benchmark.
- Added Streamlit expander UI and CSV exports for summary and row-level predictions.

## Methodological boundary
This is an exploratory Mode-A construct-score + OLS inner prediction workflow. It is not identical to SmartPLS PLSpredict, does not estimate latent-variable prediction intervals, and does not establish causal prediction. Report the implementation and validation design transparently.
