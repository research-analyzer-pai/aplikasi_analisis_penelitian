"""Transparent OLS-based mediation, moderation and collinearity diagnostics.

This module works with observed/composite scores. It is not latent-variable SEM,
does not establish causality, and should not replace a theory-led model.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor


def _clean(df, cols, min_n=20):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError("Kolom tidak ditemukan: " + ", ".join(missing))
    x = df[cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(x) < min_n:
        raise ValueError(f"Diperlukan minimal {min_n} kasus lengkap; tersedia {len(x)}.")
    if any(x[c].nunique() < 2 for c in cols):
        raise ValueError("Variabel konstan tidak dapat dianalisis.")
    return x


def _ols(y, predictors):
    return sm.OLS(y, sm.add_constant(predictors, has_constant="add")).fit()


def mediation_bootstrap(df, x, mediator, y, covariates=None, n_boot=2000,
                        ci=0.95, seed=2026):
    """Single-mediator observed-score mediation with case-resampling percentile CI."""
    covariates = list(covariates or [])
    if len({x, mediator, y, *covariates}) != 3 + len(covariates):
        raise ValueError("X, mediator, Y, dan kovariat harus berupa kolom yang berbeda.")
    if n_boot < 200:
        raise ValueError("Gunakan minimal 200 replikasi bootstrap; 2.000 atau lebih disarankan.")
    if not 0.80 <= ci < 1:
        raise ValueError("CI harus berada pada rentang 0,80 sampai kurang dari 1.")
    cols = [x, mediator, y] + covariates
    d = _clean(df, cols, min_n=20)
    # a path: M ~ X + covariates
    ma = _ols(d[mediator], d[[x] + covariates])
    # b and c': Y ~ X + M + covariates
    by = _ols(d[y], d[[x, mediator] + covariates])
    # total c: Y ~ X + covariates
    total = _ols(d[y], d[[x] + covariates])
    a = float(ma.params[x]); b = float(by.params[mediator])
    direct = float(by.params[x]); total_effect = float(total.params[x])
    indirect = a * b

    rng = np.random.default_rng(seed)
    vals = []
    arr = d.reset_index(drop=True)
    for _ in range(int(n_boot)):
        sample = arr.iloc[rng.integers(0, len(arr), len(arr))]
        try:
            am = _ols(sample[mediator], sample[[x] + covariates]).params[x]
            bm = _ols(sample[y], sample[[x, mediator] + covariates]).params[mediator]
            product = float(am * bm)
            if np.isfinite(product):
                vals.append(product)
        except Exception:
            continue
    if len(vals) < max(100, int(n_boot * 0.8)):
        raise ValueError("Bootstrap valid terlalu sedikit; periksa ukuran sampel dan kolinearitas.")
    tail = (1-ci)/2
    lo, hi = np.quantile(vals, [tail, 1-tail])
    return {
        "n": int(len(d)), "x": x, "mediator": mediator, "y": y,
        "a": a, "b": b, "direct_effect_c_prime": direct,
        "total_effect_c": total_effect, "indirect_effect_ab": float(indirect),
        "bootstrap_ci_level": float(ci), "bootstrap_ci_low": float(lo),
        "bootstrap_ci_high": float(hi), "bootstrap_valid": int(len(vals)),
        "indirect_ci_excludes_zero": bool(lo > 0 or hi < 0),
        "a_model_r2": float(ma.rsquared), "b_model_r2": float(by.rsquared),
        "interpretation_note": "CI bootstrap yang tidak melintasi nol menunjukkan estimasi efek tidak langsung berbeda dari nol dalam model ini; bukan bukti kausalitas."
    }


def moderation_bootstrap(df, x, moderator, y, covariates=None, n_boot=2000,
                         ci=0.95, seed=2026):
    """Mean-centered observed-score interaction with bootstrap percentile CI."""
    covariates = list(covariates or [])
    cols = [x, moderator, y] + covariates
    if len(set(cols)) != len(cols):
        raise ValueError("X, moderator, Y, dan kovariat harus berupa kolom berbeda.")
    if n_boot < 200:
        raise ValueError("Gunakan minimal 200 replikasi bootstrap; 2.000 atau lebih disarankan.")
    d = _clean(df, cols, min_n=20).copy()
    d["_x_c"] = d[x] - d[x].mean()
    d["_w_c"] = d[moderator] - d[moderator].mean()
    d["_interaction"] = d["_x_c"] * d["_w_c"]
    predictors = ["_x_c", "_w_c", "_interaction"] + covariates
    fit = _ols(d[y], d[predictors])
    interaction = float(fit.params["_interaction"])
    rng = np.random.default_rng(seed)
    vals = []
    arr = d.reset_index(drop=True)
    for _ in range(int(n_boot)):
        s = arr.iloc[rng.integers(0, len(arr), len(arr))]
        try:
            m = _ols(s[y], s[predictors])
            v = float(m.params["_interaction"])
            if np.isfinite(v): vals.append(v)
        except Exception:
            continue
    if len(vals) < max(100, int(n_boot * 0.8)):
        raise ValueError("Bootstrap valid terlalu sedikit; periksa data.")
    tail = (1-ci)/2
    lo, hi = np.quantile(vals, [tail, 1-tail])
    return {
        "n": int(len(d)), "x": x, "moderator": moderator, "y": y,
        "interaction_beta": interaction, "interaction_se_ols": float(fit.bse["_interaction"]),
        "interaction_p_ols": float(fit.pvalues["_interaction"]),
        "bootstrap_ci_level": float(ci), "bootstrap_ci_low": float(lo),
        "bootstrap_ci_high": float(hi), "bootstrap_valid": int(len(vals)),
        "interaction_ci_excludes_zero": bool(lo > 0 or hi < 0),
        "r_squared": float(fit.rsquared),
        "interpretation_note": "Koefisien interaksi menguji moderasi statistik pada skor teramati; bukan bukti mekanisme kausal."
    }


def vif_diagnostics(df, predictors):
    """VIF for a predictor set using complete cases and an intercept."""
    if len(predictors) < 2:
        raise ValueError("Minimal dua prediktor diperlukan untuk pemeriksaan VIF.")
    d = _clean(df, predictors, min_n=5)
    if len(d) <= len(predictors) + 1:
        raise ValueError("Kasus lengkap terlalu sedikit dibanding jumlah prediktor.")
    z = (d - d.mean()) / d.std(ddof=0)
    if (z.std(ddof=0) == 0).any():
        raise ValueError("Prediktor konstan tidak dapat dihitung VIF.")
    design = sm.add_constant(z, has_constant="add")
    rows = []
    for i, col in enumerate(design.columns):
        if col == "const":
            continue
        rows.append({"predictor": col, "vif": float(variance_inflation_factor(design.to_numpy(), i))})
    return pd.DataFrame(rows)


def simple_slopes(df, x, moderator, y, moderator_values=None):
    """Conditional X slopes at selected moderator values (default mean and ±1 SD)."""
    d = _clean(df, [x, moderator, y], min_n=20).copy()
    xc = d[x] - d[x].mean()
    wc = d[moderator] - d[moderator].mean()
    interaction = xc * wc
    fit = _ols(d[y], pd.DataFrame({"x_c": xc, "w_c": wc, "xw": interaction}))
    sd = float(d[moderator].std(ddof=1))
    vals = moderator_values if moderator_values is not None else [-sd, 0.0, sd]
    rows = []
    for val in vals:
        slope = float(fit.params["x_c"] + fit.params["xw"] * val)
        rows.append({"moderator_centered_value": float(val), "conditional_x_slope": slope})
    return pd.DataFrame(rows)
