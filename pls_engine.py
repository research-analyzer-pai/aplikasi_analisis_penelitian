
"""Exploratory PLS path-model engine (reflective Mode A, single-level constructs).

This is a transparent prototype, not a claim of full SmartPLS parity.
Implements standardized Mode-A outer-weight iteration, OLS inner paths,
measurement summaries, bootstrap path intervals and selected diagnostics.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

def _standardize(x: pd.DataFrame) -> pd.DataFrame:
    x = x.apply(pd.to_numeric, errors="coerce").dropna()
    if x.empty or len(x) < 10:
        raise ValueError("Diperlukan minimal 10 baris lengkap untuk estimasi eksploratif.")
    sd = x.std(ddof=0)
    if (sd == 0).any():
        raise ValueError("Item dengan varians nol tidak dapat diestimasi: " + ", ".join(sd[sd==0].index))
    return (x - x.mean()) / sd

def _parse_paths(path_text: str, constructs: list[str]):
    paths=[]
    for line in path_text.splitlines():
        line=line.strip()
        if not line: continue
        if "->" not in line: raise ValueError(f"Format jalur tidak valid: {line}. Gunakan X -> Y.")
        a,b=[s.strip() for s in line.split("->",1)]
        if a not in constructs or b not in constructs:
            raise ValueError(f"Konstruk pada jalur '{line}' tidak terdaftar.")
        if a==b: raise ValueError("Jalur konstruk ke dirinya sendiri tidak diperbolehkan.")
        paths.append((a,b))
    if not paths: raise ValueError("Masukkan minimal satu jalur struktural.")
    if len(set(paths)) != len(paths): raise ValueError("Terdapat jalur duplikat.")
    return paths

def _toposort(constructs, paths):
    indeg={c:0 for c in constructs}
    children={c:[] for c in constructs}
    for a,b in paths:
        indeg[b]+=1; children[a].append(b)
    q=[c for c in constructs if indeg[c]==0]
    order=[]
    while q:
        n=q.pop(0); order.append(n)
        for ch in children[n]:
            indeg[ch]-=1
            if indeg[ch]==0:q.append(ch)
    if len(order)!=len(constructs):
        raise ValueError("Model mengandung siklus. Model jalur harus berupa DAG (tanpa siklus).")
    return order

def _fit_scores(z: pd.DataFrame, blocks: dict, paths, max_iter=500, tol=1e-7):
    constructs=list(blocks)
    order=_toposort(constructs,paths)
    # Initialize Mode A weights equally; scores standardized after each update.
    weights={c:np.ones(len(blocks[c]))/len(blocks[c]) for c in constructs}
    scores=pd.DataFrame(index=z.index)
    for _ in range(max_iter):
        old={c:w.copy() for c,w in weights.items()}
        scores=pd.DataFrame({c:(z[blocks[c]].to_numpy()@weights[c]) for c in constructs},index=z.index)
        scores=(scores-scores.mean())/scores.std(ddof=0)
        for c in constructs:
            preds=[a for a,b in paths if b==c]
            succ=[b for a,b in paths if a==c]
            # Path-weighting inner proxy: regress connected neighbors' scores on construct.
            neighbors=preds+succ
            if neighbors:
                proxy=scores[neighbors].mean(axis=1)
                cor=np.array([np.corrcoef(z[col],proxy)[0,1] for col in blocks[c]])
                cor=np.nan_to_num(cor)
                norm=np.linalg.norm(cor)
                if norm>0: weights[c]=cor/norm
        delta=max(np.max(np.abs(weights[c]-old[c])) for c in constructs)
        if delta<tol: break
    scores=pd.DataFrame({c:(z[blocks[c]].to_numpy()@weights[c]) for c in constructs},index=z.index)
    scores=(scores-scores.mean())/scores.std(ddof=0)
    return scores,weights

def _structural(scores, paths):
    rows=[]; r2={}
    for target in dict.fromkeys(b for a,b in paths):
        preds=[a for a,b in paths if b==target]
        fit=sm.OLS(scores[target],sm.add_constant(scores[preds])).fit()
        r2[target]=float(fit.rsquared)
        for pred in preds:
            rows.append({"path":f"{pred} -> {target}","source":pred,"target":target,
                         "beta":float(fit.params[pred]),"se_ols":float(fit.bse[pred]),
                         "t_ols":float(fit.tvalues[pred]),"p_ols":float(fit.pvalues[pred]),
                         "r_squared_target":float(fit.rsquared)})
    return pd.DataFrame(rows),r2

def _measurement(z, blocks, scores):
    rows=[]
    for c,items in blocks.items():
        load=[]
        for item in items:
            r=np.corrcoef(z[item],scores[c])[0,1]
            load.append(float(r))
            rows.append({"construct":c,"item":item,"loading":float(r),"loading_squared":float(r*r)})
        l=np.asarray(load)
        ave=float(np.mean(l*l))
        cr=float((l.sum()**2)/((l.sum()**2)+np.sum(1-l*l))) if np.sum(1-l*l)>=0 else np.nan
        rows.append({"construct":c,"item":"[CONSTRUCT SUMMARY]","loading":np.nan,
                     "loading_squared":np.nan,"AVE":ave,"CR_approx":cr})
    return pd.DataFrame(rows)

def _vif_for_paths(scores, paths):
    out=[]
    for target in dict.fromkeys(b for a,b in paths):
        preds=[a for a,b in paths if b==target]
        if len(preds)<2:
            out.append({"target":target,"predictor":"; ".join(preds),"VIF":1.0})
        else:
            for p in preds:
                others=[x for x in preds if x!=p]
                r2=sm.OLS(scores[p],sm.add_constant(scores[others])).fit().rsquared
                out.append({"target":target,"predictor":p,"VIF":float(1/(1-r2)) if r2<1 else np.inf})
    return pd.DataFrame(out)

def estimate_pls(data: pd.DataFrame, blocks: dict, path_text: str, bootstrap=500, seed=2026):
    if not isinstance(blocks,dict) or len(blocks)<2: raise ValueError("Definisikan minimal dua konstruk.")
    for c,items in blocks.items():
        if len(items)<2: raise ValueError(f"Konstruk {c} minimal memiliki dua indikator.")
        if len(set(items))!=len(items): raise ValueError(f"Item duplikat pada konstruk {c}.")
    all_items=[i for v in blocks.values() for i in v]
    if len(set(all_items))!=len(all_items):
        raise ValueError("Untuk versi ini, satu indikator hanya boleh digunakan pada satu konstruk.")
    missing=[i for i in all_items if i not in data]
    if missing: raise ValueError("Item tidak ditemukan: "+", ".join(missing))
    z=_standardize(data[all_items])
    if len(z)<20: raise ValueError("Minimal 20 kasus lengkap disarankan untuk estimasi prototipe ini.")
    paths=_parse_paths(path_text,list(blocks))
    _toposort(list(blocks),paths)
    scores,weights=_fit_scores(z,blocks,paths)
    path_table,r2=_structural(scores,paths)
    measurement=_measurement(z,blocks,scores)
    vif=_vif_for_paths(scores,paths)
    # HTMT matrix: mean absolute between-construct item correlations / within-construct correlations.
    htmt=pd.DataFrame(np.eye(len(blocks)),index=blocks.keys(),columns=blocks.keys())
    for i,a in enumerate(blocks):
        for b in list(blocks)[i+1:]:
            between=[abs(z[x].corr(z[y])) for x in blocks[a] for y in blocks[b]]
            within_a=[abs(z[x].corr(z[y])) for ix,x in enumerate(blocks[a]) for y in blocks[a][ix+1:]]
            within_b=[abs(z[x].corr(z[y])) for ix,x in enumerate(blocks[b]) for y in blocks[b][ix+1:]]
            den=np.sqrt(np.mean(within_a)*np.mean(within_b)) if within_a and within_b else np.nan
            val=float(np.mean(between)/den) if den and np.isfinite(den) else np.nan
            htmt.loc[a,b]=htmt.loc[b,a]=val
    # Nonparametric case bootstrap; report percentile CI and two-sided empirical p.
    rng=np.random.default_rng(seed)
    boot={p:[] for p in path_table.path}
    valid=0
    for _ in range(int(bootstrap)):
        ix=rng.integers(0,len(z),len(z))
        zb=z.iloc[ix].reset_index(drop=True)
        try:
            sb,_=_fit_scores(zb,blocks,paths)
            pb,_=_structural(sb,paths)
            vals=dict(zip(pb.path,pb.beta))
            if all(np.isfinite(vals.get(k,np.nan)) for k in boot):
                for k in boot: boot[k].append(vals[k])
                valid+=1
        except Exception:
            continue
    if valid<max(30,int(bootstrap*.5)):
        raise RuntimeError(f"Bootstrap valid hanya {valid}/{bootstrap}; periksa ukuran sampel atau model.")
    bootrows=[]
    for p,vals in boot.items():
        arr=np.asarray(vals)
        lo,hi=np.quantile(arr,[.025,.975])
        p_emp=2*min((np.sum(arr<=0)+1)/(len(arr)+1),(np.sum(arr>=0)+1)/(len(arr)+1))
        bootrows.append({"path":p,"bootstrap_mean":arr.mean(),"bootstrap_sd":arr.std(ddof=1),
                         "ci_2.5":lo,"ci_97.5":hi,"p_empirical":min(1,float(p_emp)),"valid_bootstrap":len(arr)})
    boot_table=pd.DataFrame(bootrows)
    return {"n":len(z),"scores":scores,"weights":pd.DataFrame(
        [{"construct":c,"item":item,"outer_weight":float(w)} for c,items in blocks.items() for item,w in zip(items,weights[c])]),
        "measurement":measurement,"paths":path_table,"r2":pd.DataFrame([{"construct":k,"R2":v} for k,v in r2.items()]),
        "vif":vif,"htmt":htmt,"bootstrap":boot_table,
        "settings":{"algorithm":"Mode A reflective, path-neighbor proxy","bootstrap_requested":int(bootstrap),
                    "bootstrap_valid":valid,"seed":seed}}


def mediation_analysis(scores: pd.DataFrame, x: str, mediator: str, y: str,
                       bootstrap=2000, seed=2026):
    """Single-mediator OLS path decomposition with case-bootstrap a*b interval."""
    for c in [x, mediator, y]:
        if c not in scores: raise ValueError(f"Skor konstruk tidak ditemukan: {c}")
    d=scores[[x,mediator,y]].dropna()
    if len(d)<20: raise ValueError("Minimal 20 kasus lengkap diperlukan.")
    fit_a=sm.OLS(d[mediator],sm.add_constant(d[[x]])).fit()
    fit_b=sm.OLS(d[y],sm.add_constant(d[[x,mediator]])).fit()
    a=float(fit_a.params[x]); b=float(fit_b.params[mediator])
    direct=float(fit_b.params[x]); indirect=a*b
    rng=np.random.default_rng(seed); vals=[]
    for _ in range(int(bootstrap)):
        ix=rng.integers(0,len(d),len(d)); db=d.iloc[ix]
        try:
            fa=sm.OLS(db[mediator],sm.add_constant(db[[x]])).fit()
            fb=sm.OLS(db[y],sm.add_constant(db[[x,mediator]])).fit()
            vals.append(float(fa.params[x]*fb.params[mediator]))
        except Exception: continue
    if len(vals)<max(100,int(bootstrap*.5)):
        raise RuntimeError("Jumlah bootstrap valid tidak memadai.")
    arr=np.asarray(vals); lo,hi=np.quantile(arr,[.025,.975])
    p=2*min((np.sum(arr<=0)+1)/(len(arr)+1),(np.sum(arr>=0)+1)/(len(arr)+1))
    return {"n":len(d),"a":a,"b":b,"indirect_effect":indirect,"direct_effect":direct,
            "total_effect":direct+indirect,"bootstrap_ci_lower":float(lo),
            "bootstrap_ci_upper":float(hi),"bootstrap_p_empirical":float(min(1,p)),
            "bootstrap_valid":len(arr),"interpretation":"Indirect effect did not cross zero" if lo*hi>0 else "Indirect effect CI includes zero"}

def moderation_analysis(scores: pd.DataFrame, x: str, moderator: str, y: str,
                        bootstrap=2000, seed=2026):
    """OLS interaction test on standardized latent scores with case-bootstrap CI."""
    for c in [x, moderator, y]:
        if c not in scores: raise ValueError(f"Skor konstruk tidak ditemukan: {c}")
    d=scores[[x,moderator,y]].dropna().copy()
    if len(d)<20: raise ValueError("Minimal 20 kasus lengkap diperlukan.")
    d["interaction"]=d[x]*d[moderator]
    fit=sm.OLS(d[y],sm.add_constant(d[[x,moderator,"interaction"]])).fit()
    beta=float(fit.params["interaction"])
    rng=np.random.default_rng(seed); vals=[]
    for _ in range(int(bootstrap)):
        ix=rng.integers(0,len(d),len(d)); db=d.iloc[ix].copy()
        try:
            db["interaction"]=db[x]*db[moderator]
            fb=sm.OLS(db[y],sm.add_constant(db[[x,moderator,"interaction"]])).fit()
            vals.append(float(fb.params["interaction"]))
        except Exception: continue
    if len(vals)<max(100,int(bootstrap*.5)):
        raise RuntimeError("Jumlah bootstrap valid tidak memadai.")
    arr=np.asarray(vals); lo,hi=np.quantile(arr,[.025,.975])
    p=2*min((np.sum(arr<=0)+1)/(len(arr)+1),(np.sum(arr>=0)+1)/(len(arr)+1))
    return {"n":len(d),"beta_interaction":beta,"t":float(fit.tvalues["interaction"]),
            "p_ols":float(fit.pvalues["interaction"]),"r_squared":float(fit.rsquared),
            "bootstrap_ci_lower":float(lo),"bootstrap_ci_upper":float(hi),
            "bootstrap_p_empirical":float(min(1,p)),"bootstrap_valid":len(arr)}



def _mode_a_weights(zblock: pd.DataFrame, max_iter=500, tol=1e-8):
    """Iterative Mode-A weights for one reflective block."""
    x=zblock.to_numpy()
    w=np.ones(x.shape[1])/x.shape[1]
    for _ in range(max_iter):
        old=w.copy()
        score=x@w
        cor=np.array([np.corrcoef(x[:,j],score)[0,1] for j in range(x.shape[1])])
        cor=np.nan_to_num(cor)
        norm=np.linalg.norm(cor)
        if norm>0: w=cor/norm
        if np.max(np.abs(w-old))<tol: break
    return w


def formative_weights(data: pd.DataFrame, indicators: list[str], criterion: str):
    """Regression-based formative indicator weights against an explicit criterion.

    This is a diagnostic approximation, not the full PLS Mode-B algorithm.
    """
    needed=indicators+[criterion]
    missing=[c for c in needed if c not in data]
    if missing: raise ValueError("Kolom tidak ditemukan: "+", ".join(missing))
    d=data[needed].apply(pd.to_numeric,errors="coerce").dropna()
    if len(d)<20: raise ValueError("Minimal 20 kasus lengkap diperlukan.")
    if len(indicators)<2: raise ValueError("Konstruk formatif minimal dua indikator.")
    z=(d-d.mean())/d.std(ddof=0)
    if (z.std(ddof=0)==0).any(): raise ValueError("Ada indikator/criterion dengan varians nol.")
    fit=sm.OLS(z[criterion],sm.add_constant(z[indicators])).fit()
    rows=[]
    for item in indicators:
        others=[v for v in indicators if v!=item]
        r2=sm.OLS(z[item],sm.add_constant(z[others])).fit().rsquared if others else 0
        rows.append({"indicator":item,"weight":float(fit.params[item]),"se":float(fit.bse[item]),
                     "t":float(fit.tvalues[item]),"p_value":float(fit.pvalues[item]),
                     "VIF":float(1/(1-r2)) if r2<1 else np.inf})
    return {"n":len(d),"criterion":criterion,"weights":pd.DataFrame(rows),
            "r_squared_criterion":float(fit.rsquared)}

def estimate_hoc_two_stage(data: pd.DataFrame, lower_order_blocks: dict,
                           hoc_name: str, hoc_components: list[str],
                           higher_order_outcomes: dict, stage2_paths: str,
                           bootstrap=500, seed=2026):
    """Two-stage HOC approximation: LOC scores become HOC indicators in stage 2."""
    if len(hoc_components)<2: raise ValueError("HOC harus memiliki minimal dua lower-order components.")
    if any(c not in lower_order_blocks for c in hoc_components):
        raise ValueError("Semua komponen HOC harus didefinisikan sebagai konstruk tahap pertama.")
    all_paths="\\n".join(f"{a} -> {b}" for a,b in [])
    # Stage 1: obtain LOC scores without imposing a structural inner model.
    all_items=[i for items in lower_order_blocks.values() for i in items]
    z=_standardize(data[all_items])
    loc_weights={c:_mode_a_weights(z[items]) for c,items in lower_order_blocks.items()}
    loc_scores=pd.DataFrame({c:(z[items].to_numpy()@loc_weights[c]) for c,items in lower_order_blocks.items()},index=z.index)
    loc_scores=(loc_scores-loc_scores.mean())/loc_scores.std(ddof=0)
    stage2_data=loc_scores[hoc_components].copy()
    stage2_blocks={hoc_name:list(hoc_components)}
    for construct,items in higher_order_outcomes.items():
        if construct==hoc_name: raise ValueError("Nama konstruk outcome tidak boleh sama dengan HOC.")
        missing=[i for i in items if i not in data]
        if missing: raise ValueError("Indikator outcome tidak ditemukan: "+", ".join(missing))
        stage2_data=stage2_data.join(data.loc[stage2_data.index,items])
        stage2_blocks[construct]=items
    stage2=estimate_pls(stage2_data,stage2_blocks,stage2_paths,bootstrap=bootstrap,seed=seed)
    return {"stage1_loc_scores":loc_scores,"stage2":stage2,
            "hoc_specification":{"hoc_name":hoc_name,"components":hoc_components,
                                 "outcomes":list(higher_order_outcomes)}}

def q2_predictive_relevance(scores: pd.DataFrame, paths: list[tuple[str,str]], omission_distance=7):
    """Blindfolding-style cross-validated redundancy approximation for endogenous scores."""
    if omission_distance<2: raise ValueError("Omission distance minimal 2.")
    rows=[]
    for target in dict.fromkeys(b for a,b in paths):
        preds=[a for a,b in paths if b==target]
        y=scores[target].to_numpy()
        n=len(y)
        omitted=np.arange(n)%omission_distance==0
        if omitted.sum()<2 or (~omitted).sum()<=len(preds)+1:
            continue
        pred=np.full(n,np.nan)
        for ix in np.where(omitted)[0]:
            train=np.arange(n)!=ix
            fit=sm.OLS(scores.loc[train,target],sm.add_constant(scores.loc[train,preds])).fit()
            pred[ix]=float(fit.predict(sm.add_constant(scores.loc[[ix],preds],has_constant="add")).iloc[0])
        sso=float(np.sum((y[omitted]-np.mean(y[~omitted]))**2))
        press=float(np.sum((y[omitted]-pred[omitted])**2))
        q2=1-press/sso if sso>0 else np.nan
        rows.append({"construct":target,"omission_distance":omission_distance,
                     "SSE":press,"SSO":sso,"Q2_predictive_relevance":q2})
    return pd.DataFrame(rows)

def _path_coefficients_for_group(df, blocks, paths):
    items=[i for v in blocks.values() for i in v]
    z=_standardize(df[items])
    scores,_=_fit_scores(z,blocks,paths)
    table,_=_structural(scores,paths)
    return dict(zip(table.path,table.beta))

def permutation_mga(data: pd.DataFrame, blocks: dict, path_text: str, group_col: str,
                    permutations=499, seed=2026):
    """Two-group permutation MGA on path-coefficient differences."""
    if group_col not in data: raise ValueError("Kolom kelompok tidak ditemukan.")
    groups=list(data[group_col].dropna().unique())
    if len(groups)!=2: raise ValueError("MGA saat ini memerlukan tepat dua kelompok.")
    paths=_parse_paths(path_text,list(blocks))
    items=[i for v in blocks.values() for i in v]
    d=data[[group_col]+items].dropna()
    g1,g2=groups
    a=d[d[group_col]==g1]; b=d[d[group_col]==g2]
    if min(len(a),len(b))<20: raise ValueError("Setiap kelompok minimal 20 kasus lengkap.")
    obs1=_path_coefficients_for_group(a,blocks,paths); obs2=_path_coefficients_for_group(b,blocks,paths)
    observed={k:obs1[k]-obs2[k] for k in obs1}
    rng=np.random.default_rng(seed); null={k:[] for k in observed}
    labels=d[group_col].to_numpy()
    for _ in range(int(permutations)):
        shuffled=rng.permutation(labels)
        da=d.loc[shuffled==g1,items]; db=d.loc[shuffled==g2,items]
        if min(len(da),len(db))<20: continue
        try:
            pa=_path_coefficients_for_group(da,blocks,paths)
            pb=_path_coefficients_for_group(db,blocks,paths)
            for k in null: null[k].append(pa[k]-pb[k])
        except Exception: continue
    rows=[]
    for k,diff in observed.items():
        arr=np.asarray(null[k])
        p=(np.sum(np.abs(arr)>=abs(diff))+1)/(len(arr)+1)
        rows.append({"path":k,"group_1":str(g1),"group_2":str(g2),
                     "beta_group_1":obs1[k],"beta_group_2":obs2[k],
                     "difference":diff,"permutation_p":float(p),"valid_permutations":len(arr)})
    return pd.DataFrame(rows)


def micom_compositional_check(data: pd.DataFrame, blocks: dict, group_col: str,
                              permutations=499, seed=2026):
    """MICOM-inspired permutation assessment of compositional invariance.

    Computes correlations between pooled-weight and group-specific Mode-A composites
    on the same group cases. Also reports permutation mean/variance differences.
    This is an educational approximation, not a certified MICOM implementation.
    """
    if group_col not in data: raise ValueError("Kolom kelompok tidak ditemukan.")
    groups=list(data[group_col].dropna().unique())
    if len(groups)!=2: raise ValueError("MICOM check saat ini memerlukan tepat dua kelompok.")
    items=[i for v in blocks.values() for i in v]
    d=data[[group_col]+items].dropna().reset_index(drop=True)
    if min((d[group_col]==g).sum() for g in groups)<20:
        raise ValueError("Setiap kelompok minimal 20 kasus lengkap.")
    z=_standardize(d[items])
    pooled_weights={c:_mode_a_weights(z[inds]) for c,inds in blocks.items()}
    labels=d[group_col].to_numpy()
    rng=np.random.default_rng(seed)
    rows=[]
    for construct,inds in blocks.items():
        wp=pooled_weights[construct]
        observed_corr=[]; observed_means=[]; observed_vars=[]
        for g in groups:
            ix=np.where(labels==g)[0]
            zg=z.iloc[ix][inds]
            wg=_mode_a_weights(zg)
            pooled_score=zg.to_numpy()@wp
            group_score=zg.to_numpy()@wg
            corr=float(np.corrcoef(pooled_score,group_score)[0,1])
            observed_corr.append(corr)
            observed_means.append(float(np.mean(pooled_score)))
            observed_vars.append(float(np.var(pooled_score,ddof=1)))
        obs_corr=min(observed_corr)
        obs_mean_diff=observed_means[0]-observed_means[1]
        obs_var_ratio=(observed_vars[0]/observed_vars[1]) if observed_vars[1]>0 else np.nan
        perm_corr=[]; perm_mean=[]; perm_var=[]
        for _ in range(int(permutations)):
            sh=rng.permutation(labels)
            corrs=[]; means=[]; variances=[]
            for g in groups:
                ix=np.where(sh==g)[0]
                zg=z.iloc[ix][inds]
                wg=_mode_a_weights(zg)
                corrs.append(float(np.corrcoef(zg.to_numpy()@wp,zg.to_numpy()@wg)[0,1]))
                ps=zg.to_numpy()@wp
                means.append(float(np.mean(ps))); variances.append(float(np.var(ps,ddof=1)))
            perm_corr.append(min(corrs))
            perm_mean.append(means[0]-means[1])
            perm_var.append(variances[0]/variances[1] if variances[1]>0 else np.nan)
        pc=np.asarray(perm_corr); pm=np.asarray(perm_mean); pv=np.asarray(perm_var)
        p_comp=(np.sum(pc<=obs_corr)+1)/(len(pc)+1)
        p_mean=(np.sum(np.abs(pm)>=abs(obs_mean_diff))+1)/(len(pm)+1)
        p_var=(np.sum(np.abs(np.log(pv))>=abs(np.log(obs_var_ratio)))+1)/(np.sum(np.isfinite(pv))+1) if obs_var_ratio>0 else np.nan
        rows.append({"construct":construct,"group_1":str(groups[0]),"group_2":str(groups[1]),
                     "compositional_correlation_min":obs_corr,"step2_permutation_p":float(p_comp),
                     "mean_difference":obs_mean_diff,"step3_mean_permutation_p":float(p_mean),
                     "variance_ratio":obs_var_ratio,"step3_variance_permutation_p":float(p_var),
                     "valid_permutations":len(pc),
                     "warning":"MICOM-inspired approximation; verify against canonical MICOM implementation"})
    return pd.DataFrame(rows)
