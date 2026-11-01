"""Indicator-level out-of-sample prediction for the exploratory PLS engine.

Exploratory repeated k-fold prediction; not a certified SmartPLS PLSpredict clone.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import KFold
from pls_engine import _fit_scores, _parse_paths, _toposort

def indicator_level_pls_predict(data: pd.DataFrame, blocks: dict, path_text: str,
                                folds: int = 5, repeats: int = 1, seed: int = 2026):
    if not isinstance(data, pd.DataFrame): raise TypeError("data harus berupa pandas DataFrame.")
    if not isinstance(blocks, dict) or len(blocks) < 2: raise ValueError("Definisikan minimal dua konstruk.")
    if folds < 2 or repeats < 1: raise ValueError("folds minimal 2 dan repeats minimal 1.")
    if any(len(v) < 2 for v in blocks.values()): raise ValueError("Setiap konstruk reflektif memerlukan minimal dua indikator.")
    items=[i for v in blocks.values() for i in v]
    if len(items)!=len(set(items)): raise ValueError("Indikator tidak boleh dipakai pada lebih dari satu konstruk.")
    missing=[i for i in items if i not in data.columns]
    if missing: raise ValueError("Indikator tidak ditemukan: "+", ".join(missing))
    raw=data[items].apply(pd.to_numeric,errors="coerce").dropna()
    if len(raw)<max(30,folds*5): raise ValueError("Kasus lengkap terlalu sedikit; minimal 30 dan sekurangnya 5 per fold.")
    if (raw.std(ddof=0)==0).any(): raise ValueError("Indikator dengan varians nol tidak dapat diprediksi.")
    paths=_parse_paths(path_text,list(blocks)); _toposort(list(blocks),paths)
    endogenous=list(dict.fromkeys(y for _,y in paths)); rng=np.random.default_rng(seed); rows=[]
    for rep in range(repeats):
        cv=KFold(n_splits=folds,shuffle=True,random_state=int(rng.integers(0,2**31-1)))
        for fold,(itr,ite) in enumerate(cv.split(raw),1):
            train,test=raw.iloc[itr],raw.iloc[ite]
            mu,sd=train.mean(),train.std(ddof=0); ztr,zte=(train-mu)/sd,(test-mu)/sd
            tr_scores,weights=_fit_scores(ztr,blocks,paths)
            te_scores=pd.DataFrame({c:zte[inds].to_numpy()@weights[c] for c,inds in blocks.items()},index=test.index)
            score_mu,score_sd=tr_scores.mean(),tr_scores.std(ddof=0)
            tr_scores=(tr_scores-score_mu)/score_sd; te_scores=(te_scores-score_mu)/score_sd
            for target in endogenous:
                predictors=[a for a,b in paths if b==target]
                inner=sm.OLS(tr_scores[target],sm.add_constant(tr_scores[predictors],has_constant="add")).fit()
                pred_score=inner.predict(sm.add_constant(te_scores[predictors],has_constant="add"))
                for indicator in blocks[target]:
                    loading=float(np.corrcoef(ztr[indicator],tr_scores[target])[0,1])
                    if not np.isfinite(loading): loading=0.0
                    pred_raw=pred_score.to_numpy()*loading*float(sd[indicator])+float(mu[indicator])
                    observed=test[indicator].to_numpy()
                    pred_items=[item for p in predictors for item in blocks[p]]
                    lm=sm.OLS(train[indicator],sm.add_constant(train[pred_items],has_constant="add")).fit()
                    lm_pred=lm.predict(sm.add_constant(test[pred_items],has_constant="add")).to_numpy()
                    mean_pred=np.repeat(float(train[indicator].mean()),len(test))
                    for idx,obs,ppls,plm,pmean in zip(test.index,observed,pred_raw,lm_pred,mean_pred):
                        rows.append({"repeat":rep+1,"fold":fold,"row_index":idx,"construct":target,"indicator":indicator,
                                     "observed":float(obs),"pls_predicted":float(ppls),"lm_predicted":float(plm),"mean_benchmark":float(pmean)})
    predictions=pd.DataFrame(rows); summaries=[]
    for (construct,indicator),g in predictions.groupby(["construct","indicator"]):
        y=g.observed.to_numpy(); metrics={}
        for label,col in [("PLS","pls_predicted"),("LM","lm_predicted"),("Mean","mean_benchmark")]:
            e=y-g[col].to_numpy(); metrics[label+"_RMSE"]=float(np.sqrt(np.mean(e**2)))
            metrics[label+"_MAE"]=float(np.mean(np.abs(e)))
            metrics[label+"_Q2_predict"]=float(1-np.sum(e**2)/np.sum((y-y.mean())**2)) if np.sum((y-y.mean())**2)>0 else np.nan
        summaries.append({"construct":construct,"indicator":indicator,"n_predictions":len(g),**metrics,
                          "PLS_better_than_LM_RMSE":bool(metrics["PLS_RMSE"]<metrics["LM_RMSE"])})
    return {"summary":pd.DataFrame(summaries),"predictions":predictions,
            "settings":{"folds":folds,"repeats":repeats,"seed":seed,"n_complete":len(raw),
            "method":"Mode-A scores; training-fold loading back-projection; indicator-level OLS LM benchmark",
            "warning":"Prosedur eksploratif, bukan implementasi identik SmartPLS PLSpredict. Evaluasi eksternal disarankan."}}
