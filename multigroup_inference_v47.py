"""Enhanced two-group PLS multi-group inference.

Bootstrap confidence intervals for between-group path differences plus a
permutation test. Uses the repository's exploratory Mode-A score algorithm;
not a validated substitute for SmartPLS MGA/PLS-MGA or MICOM.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pls_engine import _parse_paths, _path_coefficients_for_group, micom_compositional_check


def bootstrap_mga(data: pd.DataFrame, blocks: dict, path_text: str, group_col: str,
                  bootstrap: int = 1000, permutations: int = 999,
                  seed: int = 2026, min_group_n: int = 20):
    if group_col not in data:
        raise ValueError("Kolom kelompok tidak ditemukan.")
    if bootstrap < 100 or permutations < 99:
        raise ValueError("Gunakan minimal 100 bootstrap dan 99 permutasi.")
    groups = list(data[group_col].dropna().unique())
    if len(groups) != 2:
        raise ValueError("Analisis saat ini memerlukan tepat dua kelompok.")
    items = [item for values in blocks.values() for item in values]
    missing = [x for x in items if x not in data]
    if missing:
        raise ValueError("Indikator tidak ditemukan: " + ", ".join(missing))
    d = data[[group_col] + items].dropna().reset_index(drop=True)
    g1, g2 = groups
    a = d[d[group_col] == g1].drop(columns=[group_col])
    b = d[d[group_col] == g2].drop(columns=[group_col])
    if min(len(a), len(b)) < min_group_n:
        raise ValueError(f"Setiap kelompok minimal {min_group_n} kasus lengkap.")
    paths = _parse_paths(path_text, list(blocks))
    obs_a = _path_coefficients_for_group(a, blocks, paths)
    obs_b = _path_coefficients_for_group(b, blocks, paths)
    observed = {k: obs_a[k] - obs_b[k] for k in obs_a}
    rng = np.random.default_rng(seed)
    boot = {k: [] for k in observed}
    for _ in range(bootstrap):
        ia = rng.integers(0, len(a), len(a))
        ib = rng.integers(0, len(b), len(b))
        try:
            pa = _path_coefficients_for_group(a.iloc[ia].reset_index(drop=True), blocks, paths)
            pb = _path_coefficients_for_group(b.iloc[ib].reset_index(drop=True), blocks, paths)
            for k in boot:
                diff = pa[k] - pb[k]
                if np.isfinite(diff): boot[k].append(float(diff))
        except Exception:
            continue
    # Permutation tests preserve observed group sizes.
    null = {k: [] for k in observed}
    labels = d[group_col].to_numpy()
    for _ in range(permutations):
        shuffled = rng.permutation(labels)
        da = d.loc[shuffled == g1, items]
        db = d.loc[shuffled == g2, items]
        try:
            pa = _path_coefficients_for_group(da, blocks, paths)
            pb = _path_coefficients_for_group(db, blocks, paths)
            for k in null:
                val = pa[k] - pb[k]
                if np.isfinite(val): null[k].append(float(val))
        except Exception:
            continue
    rows = []
    for path, diff in observed.items():
        ba = np.asarray(boot[path], dtype=float)
        na = np.asarray(null[path], dtype=float)
        if len(ba) < max(100, int(bootstrap * .5)):
            raise RuntimeError(f"Bootstrap valid tidak memadai untuk {path}: {len(ba)}")
        if len(na) < max(50, int(permutations * .5)):
            raise RuntimeError(f"Permutasi valid tidak memadai untuk {path}: {len(na)}")
        lo, hi = np.quantile(ba, [.025, .975])
        p = (np.sum(np.abs(na) >= abs(diff)) + 1) / (len(na) + 1)
        rows.append({"path": path, "group_1": str(g1), "group_2": str(g2),
            "beta_group_1": obs_a[path], "beta_group_2": obs_b[path],
            "difference_g1_minus_g2": float(diff), "bootstrap_ci_2_5": float(lo),
            "bootstrap_ci_97_5": float(hi), "bootstrap_ci_excludes_zero": bool(lo > 0 or hi < 0),
            "permutation_p_two_sided": float(p), "bootstrap_valid": len(ba),
            "permutation_valid": len(na)})
    return pd.DataFrame(rows)


def multigroup_invariance_report(data: pd.DataFrame, blocks: dict, path_text: str,
                                 group_col: str, bootstrap: int = 1000,
                                 permutations: int = 499, seed: int = 2026):
    """Combine existing MICOM-inspired diagnostics with enhanced bootstrap MGA."""
    micom = micom_compositional_check(data, blocks, group_col,
                                      permutations=permutations, seed=seed)
    mga = bootstrap_mga(data, blocks, path_text, group_col, bootstrap,
                        permutations, seed + 1)
    inv = micom.copy()
    inv["step2_compositional_invariance_supported"] = inv["step2_permutation_p"] >= .05
    inv["step3_mean_equality_supported"] = inv["step3_mean_permutation_p"] >= .05
    inv["step3_variance_equality_supported"] = inv["step3_variance_permutation_p"] >= .05
    inv["interpretation"] = np.where(
        inv["step2_compositional_invariance_supported"],
        "Bukti tidak menolak invariansi komposisional; evaluasi Step 3 untuk invariansi penuh.",
        "Invariansi komposisional belum didukung; interpretasi MGA perlu kehati-hatian.")
    return {"invariance": inv, "mga": mga,
            "settings": {"group_column": group_col, "bootstrap": bootstrap,
                         "permutations": permutations, "seed": seed,
                         "method": "Mode-A score approximation; independent within-group bootstrap and label permutation",
                         "warning": "MICOM-inspired/MGA approximation; verify with canonical MICOM and established PLS-SEM software."}}
