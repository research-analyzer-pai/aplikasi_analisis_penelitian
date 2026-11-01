"""Cross-validated predictive assessment for the exploratory PLS engine.

Uses the package's Mode-A construct scores and OLS inner prediction. This is
not a claim of equivalence with SmartPLS PLSpredict.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
import statsmodels.api as sm
from pls_engine import _fit_scores, _parse_paths, _toposort

def cross_validated_pls_predict(data: pd.DataFrame, blocks: dict, path_text: str,
                                folds: int = 5, repeats: int = 1, seed: int = 2026):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data harus berupa pandas DataFrame.")
    if not isinstance(blocks, dict) or len(blocks) < 2:
        raise ValueError("Definisikan minimal dua konstruk.")
    if folds < 2 or repeats < 1:
        raise ValueError("folds minimal 2 dan repeats minimal 1.")
    all_items = [item for items in blocks.values() for item in items]
    if len(all_items) != len(set(all_items)):
        raise ValueError("Indikator tidak boleh digunakan pada lebih dari satu konstruk.")
    missing = [x for x in all_items if x not in data.columns]
    if missing:
        raise ValueError("Indikator tidak ditemukan: " + ", ".join(missing))
    raw = data[all_items].apply(pd.to_numeric, errors="coerce").dropna()
    if len(raw) < max(20, folds * 4):
        raise ValueError("Jumlah kasus lengkap terlalu sedikit untuk validasi silang.")
    if (raw.std(ddof=0) == 0).any():
        raise ValueError("Terdapat indikator dengan varians nol.")
    paths = _parse_paths(path_text, list(blocks))
    _toposort(list(blocks), paths)
    endogenous = list(dict.fromkeys(y for _, y in paths))
    rng = np.random.default_rng(seed)
    records = []
    for rep in range(repeats):
        splitter = KFold(n_splits=folds, shuffle=True,
                         random_state=int(rng.integers(0, 2**31-1)))
        for fold, (train_idx, test_idx) in enumerate(splitter.split(raw), start=1):
            train, test = raw.iloc[train_idx], raw.iloc[test_idx]
            mu, sd = train.mean(), train.std(ddof=0)
            z_train, z_test = (train-mu)/sd, (test-mu)/sd
            train_scores, weights = _fit_scores(z_train, blocks, paths)
            test_scores = pd.DataFrame({c: z_test[items].to_numpy() @ weights[c]
                                        for c, items in blocks.items()}, index=test.index)
            smu, ssd = train_scores.mean(), train_scores.std(ddof=0)
            train_scores, test_scores = (train_scores-smu)/ssd, (test_scores-smu)/ssd
            for target in endogenous:
                preds = [x for x, y in paths if y == target]
                fit = sm.OLS(train_scores[target], sm.add_constant(train_scores[preds], has_constant="add")).fit()
                predicted = fit.predict(sm.add_constant(test_scores[preds], has_constant="add"))
                observed = test_scores[target]
                benchmark = np.repeat(float(train_scores[target].mean()), len(test))
                for idx, obs, pred, base in zip(test.index, observed, predicted, benchmark):
                    records.append({"repeat":rep+1,"fold":fold,"row_index":idx,"construct":target,
                                    "observed":float(obs),"predicted":float(pred),"benchmark":float(base)})
    pred = pd.DataFrame(records)
    summary=[]
    for target, g in pred.groupby("construct"):
        err=g.observed-g.predicted; base_err=g.observed-g.benchmark
        sse=float(np.sum(err**2)); base_sse=float(np.sum(base_err**2))
        summary.append({"construct":target,"n_predictions":len(g),"RMSE":float(np.sqrt(np.mean(err**2))),
                        "MAE":float(np.mean(np.abs(err))),
                        "Q2_predict_cv":float(1-sse/base_sse) if base_sse>0 else np.nan,
                        "benchmark_RMSE":float(np.sqrt(np.mean(base_err**2))),
                        "prediction_better_than_benchmark":bool(sse<base_sse)})
    return {"summary":pd.DataFrame(summary),"predictions":pred,
            "settings":{"folds":folds,"repeats":repeats,"seed":seed,"n_complete":len(raw),
                        "method":"Mode-A exploratory construct scores + OLS inner prediction",
                        "warning":"Bukan implementasi identik PLSpredict/Q²_predict SmartPLS."}}
