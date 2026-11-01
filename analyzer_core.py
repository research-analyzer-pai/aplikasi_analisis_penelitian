
"""Core statistical routines for Research Analyzer Professional v2.5."""
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

def numeric_frame(df, columns):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom tidak ditemukan: {', '.join(missing)}")
    out = df[columns].apply(pd.to_numeric, errors="coerce")
    if out.dropna(how="all").empty:
        raise ValueError("Tidak ada observasi numerik yang dapat dianalisis.")
    return out

def descriptive(df, columns):
    x = numeric_frame(df, columns)
    result = x.describe().T
    result["missing"] = x.isna().sum()
    result["skewness"] = x.skew()
    result["kurtosis"] = x.kurtosis()
    return result.reset_index(names="variable")

def cronbach_alpha(df, items, reverse_items=None):
    x = numeric_frame(df, items).dropna()
    if x.shape[0] < 2 or x.shape[1] < 2:
        raise ValueError("Cronbach's alpha memerlukan minimal 2 responden dan 2 item lengkap.")
    reverse_items = reverse_items or []
    for col in reverse_items:
        if col not in x:
            raise ValueError(f"Item reverse tidak ditemukan: {col}")
        x[col] = x[col].max() + x[col].min() - x[col]
    k = x.shape[1]
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var == 0:
        raise ValueError("Varians skor total bernilai nol.")
    alpha = (k/(k-1)) * (1 - x.var(axis=0, ddof=1).sum()/total_var)
    rows = []
    for col in x:
        rest = x.drop(columns=[col]).sum(axis=1)
        corr = x[col].corr(rest) if rest.std() and x[col].std() else np.nan
        reduced = x.drop(columns=[col])
        kk = reduced.shape[1]
        tv = reduced.sum(axis=1).var(ddof=1)
        a_del = (kk/(kk-1))*(1-reduced.var(axis=0,ddof=1).sum()/tv) if kk > 1 and tv else np.nan
        rows.append({"item":col,"corrected_item_total_corr":corr,"alpha_if_deleted":a_del})
    return {"alpha":float(alpha), "n":int(len(x)), "k":int(k), "item_diagnostics":pd.DataFrame(rows)}

def one_sample_t(df, variable, test_value=0):
    x = numeric_frame(df,[variable])[variable].dropna()
    if len(x)<2: raise ValueError("Uji t memerlukan minimal dua observasi.")
    r=stats.ttest_1samp(x, popmean=float(test_value))
    return {"n":len(x),"mean":x.mean(),"sd":x.std(ddof=1),"t":r.statistic,"p_value":r.pvalue,
            "df":len(x)-1,"mean_difference":x.mean()-float(test_value)}

def independent_t(df, variable, group, equal_var=False):
    if group not in df: raise ValueError(f"Kolom kelompok tidak ditemukan: {group}")
    temp=df[[variable,group]].copy()
    temp[variable]=pd.to_numeric(temp[variable],errors="coerce")
    levels=temp[group].dropna().unique()
    if len(levels)!=2: raise ValueError("Uji t independen memerlukan tepat dua kelompok.")
    a=temp.loc[temp[group]==levels[0],variable].dropna()
    b=temp.loc[temp[group]==levels[1],variable].dropna()
    if min(len(a),len(b))<2: raise ValueError("Setiap kelompok harus memiliki minimal dua observasi.")
    r=stats.ttest_ind(a,b,equal_var=equal_var)
    return {"group_1":str(levels[0]),"n_1":len(a),"mean_1":a.mean(),
            "group_2":str(levels[1]),"n_2":len(b),"mean_2":b.mean(),
            "t":r.statistic,"p_value":r.pvalue,"equal_variance_assumed":equal_var}

def one_way_anova(df, dependent, factor):
    if factor not in df: raise ValueError(f"Kolom faktor tidak ditemukan: {factor}")
    d=df[[dependent,factor]].copy()
    d[dependent]=pd.to_numeric(d[dependent],errors="coerce")
    d=d.dropna()
    if d[factor].nunique()<2: raise ValueError("ANOVA memerlukan minimal dua kelompok.")
    groups=[g[dependent].values for _,g in d.groupby(factor)]
    if min(map(len,groups))<2: raise ValueError("Setiap kelompok harus memiliki minimal dua observasi.")
    f,p=stats.f_oneway(*groups)
    grand=d[dependent].mean()
    ss_between=sum(len(arr)*(np.mean(arr)-grand)**2 for arr in groups)
    ss_total=((d[dependent]-grand)**2).sum()
    eta=ss_between/ss_total if ss_total else np.nan
    return {"n":len(d),"groups":d[factor].nunique(),"F":f,"p_value":p,"eta_squared":eta}

def linear_regression(df, dependent, predictors):
    cols=[dependent]+predictors
    d=numeric_frame(df,cols).dropna()
    if len(d)<=len(predictors)+1: raise ValueError("Observasi tidak cukup untuk jumlah prediktor.")
    y=d[dependent]
    X=sm.add_constant(d[predictors],has_constant="add")
    fit=sm.OLS(y,X).fit()
    ci=fit.conf_int()
    table=pd.DataFrame({"term":fit.params.index,"B":fit.params.values,"SE":fit.bse.values,
                        "t":fit.tvalues.values,"p_value":fit.pvalues.values,
                        "CI_lower":ci[0].values,"CI_upper":ci[1].values})
    return {"n":int(fit.nobs),"r_squared":fit.rsquared,"adjusted_r_squared":fit.rsquared_adj,
            "F":fit.fvalue,"F_p_value":fit.f_pvalue,"coefficients":table,
            "diagnostics":{"durbin_watson":float(sm.stats.stattools.durbin_watson(fit.resid)),
                           "residual_mean":float(fit.resid.mean())}}

def pearson_matrix(df, columns):
    x=numeric_frame(df,columns)
    return x.corr(method="pearson")

def validate_sem_import(df):
    required=["path","beta","p_value"]
    missing=[c for c in required if c not in df]
    if missing: raise ValueError(f"Kolom SEM wajib belum ada: {', '.join(missing)}")
    out=df.copy()
    out["beta"]=pd.to_numeric(out["beta"],errors="coerce")
    out["p_value"]=pd.to_numeric(out["p_value"],errors="coerce")
    if out[["beta","p_value"]].isna().any().any():
        raise ValueError("Kolom beta dan p_value harus berisi angka.")
    if ((out.p_value<0)|(out.p_value>1)).any():
        raise ValueError("p_value harus berada pada rentang 0 sampai 1.")
    return out
