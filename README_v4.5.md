# Version 4.5 — PLS Predictive Assessment

Repeated k-fold cross-validation for out-of-fold prediction of endogenous construct scores. Reports RMSE, MAE and a Q²-style statistic relative to a training-mean benchmark; exports summary and row-level predictions as CSV.

Use: upload indicator CSV, enter a JSON construct-to-indicator mapping, specify paths (`X -> Y`), choose folds/repeats/seed, then run the assessment.

Limitations: uses the existing exploratory Mode-A score algorithm and OLS inner prediction. It is not a validated reproduction of SmartPLS PLSpredict. Use established software for confirmatory comparisons and report estimator/settings.
