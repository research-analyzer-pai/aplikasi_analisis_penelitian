
from __future__ import annotations
import shutil, subprocess, tempfile
from pathlib import Path
import numpy as np
import pandas as pd

def _req(df, cols):
    miss=[c for c in cols if c not in df.columns]
    if miss: raise ValueError("Kolom wajib tidak tersedia: "+", ".join(miss))

def measurement_quality(loadings, construct_col="construct", indicator_col="indicator", loading_col="loading", error_col=None):
    _req(loadings,[construct_col,indicator_col,loading_col])
    d=loadings.copy()
    d[loading_col]=pd.to_numeric(d[loading_col],errors="coerce")
    if d[[construct_col,indicator_col,loading_col]].isna().any().any(): raise ValueError("Nama konstruk/indikator dan loading harus terisi.")
    if d.duplicated([construct_col,indicator_col]).any(): raise ValueError("Kombinasi konstruk-indikator terduplikasi.")
    rows=[]
    for name,g in d.groupby(construct_col,sort=False):
        lam=g[loading_col].to_numpy(float)
        if len(lam)<2: raise ValueError(f"Konstruk {name} memerlukan minimal dua indikator.")
        if np.any(np.abs(lam)>1.000001): raise ValueError("Loading harus berada pada rentang -1 sampai 1.")
        if error_col and error_col in g:
            err=pd.to_numeric(g[error_col],errors="coerce").to_numpy(float)
            if np.any(~np.isfinite(err)) or np.any(err<0): raise ValueError("Error variance tidak valid.")
        else: err=1-lam**2
        s=float(lam.sum()); cr=s*s/(s*s+float(err.sum())) if s*s+err.sum() else np.nan
        rows.append({"construct":name,"indicators":len(lam),"mean_loading":float(lam.mean()),"min_loading":float(lam.min()),"max_loading":float(lam.max()),"composite_reliability":cr,"average_variance_extracted":float(np.mean(lam**2))})
    return pd.DataFrame(rows)

def cronbach_alpha(data,item_map):
    rows=[]
    for construct,items in item_map.items():
        if len(items)<2: raise ValueError(f"{construct}: minimal dua item.")
        _req(data,items); x=data[items].apply(pd.to_numeric,errors="coerce").dropna()
        if len(x)<3: raise ValueError(f"{construct}: kasus lengkap terlalu sedikit.")
        k=len(items); tv=float(x.sum(axis=1).var(ddof=1))
        a=k/(k-1)*(1-float(x.var(ddof=1).sum())/tv) if tv>0 else np.nan
        rows.append({"construct":construct,"items":k,"n_complete":len(x),"cronbach_alpha":a})
    return pd.DataFrame(rows)

def htmt_matrix(data,item_map):
    names=list(item_map)
    if len(names)<2: raise ValueError("HTMT memerlukan minimal dua konstruk.")
    items=[i for v in item_map.values() for i in v]
    if len(set(items))!=len(items): raise ValueError("Indikator tidak boleh dipakai pada dua konstruk.")
    _req(data,items); corr=data[items].apply(pd.to_numeric,errors="coerce").corr().abs()
    mat=pd.DataFrame(np.eye(len(names)),index=names,columns=names)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            between=[corr.loc[u,v] for u in item_map[a] for v in item_map[b]]
            wa=[corr.loc[item_map[a][p],item_map[a][q]] for p in range(len(item_map[a])) for q in range(p+1,len(item_map[a]))]
            wb=[corr.loc[item_map[b][p],item_map[b][q]] for p in range(len(item_map[b])) for q in range(p+1,len(item_map[b]))]
            den=np.sqrt(np.mean(wa)*np.mean(wb)) if wa and wb else np.nan
            val=float(np.mean(between)/den) if den and np.isfinite(den) else np.nan
            mat.loc[a,b]=mat.loc[b,a]=val
    return mat

def fornell_larcker(quality,construct_corr):
    _req(quality,["construct","average_variance_extracted"])
    if not isinstance(construct_corr,pd.DataFrame) or list(construct_corr.index)!=list(construct_corr.columns): raise ValueError("Matriks korelasi harus persegi dengan label sama.")
    q=quality.set_index("construct")["average_variance_extracted"]
    if set(construct_corr.index)-set(q.index): raise ValueError("AVE tidak tersedia untuk semua konstruk.")
    out=construct_corr.copy().astype(float)
    for c in out.columns: out.loc[c,c]=np.sqrt(q[c])
    return out

def audit_fit_indices(fit,thresholds=None):
    thresholds=thresholds or {"cfi":("min",.90),"tli":("min",.90),"rmsea":("max",.08),"srmr":("max",.08),"gfi":("min",.90)}
    rows=[]
    for key,(direction,cut) in thresholds.items():
        try: value=float(fit.get(key))
        except (TypeError,ValueError): value=np.nan
        status="Tidak tersedia" if not np.isfinite(value) else ("Memenuhi batas heuristik" if (value>=cut if direction=="min" else value<=cut) else "Di luar batas heuristik")
        rows.append({"index":key,"value":value,"rule":f"{direction} {cut}","status":status})
    return pd.DataFrame(rows)

def build_lavaan_syntax(measurement_map,structural_paths=None):
    if not measurement_map: raise ValueError("Peta konstruk tidak boleh kosong.")
    lines=[]
    for latent,items in measurement_map.items():
        if not latent or len(items)<2 or any(not str(i).strip() for i in items): raise ValueError(f"Konstruk {latent!r} memerlukan minimal dua indikator valid.")
        lines.append(f"{latent} =~ "+" + ".join(items))
    for outcome,preds in (structural_paths or {}).items():
        if preds: lines.append(f"{outcome} ~ "+" + ".join(preds))
    return "\n".join(lines)

def run_lavaan(data,syntax,estimator="MLR",ordered=None,timeout=180):
    exe=shutil.which("Rscript")
    if not exe: raise RuntimeError("Rscript tidak ditemukan. Instal R dan paket lavaan.")
    if not syntax.strip(): raise ValueError("Sintaks lavaan kosong.")
    rcode = "args <- commandArgs(trailingOnly=TRUE)\n"
    rcode += "suppressPackageStartupMessages(library(lavaan))\n"
    rcode += "dat <- read.csv(args[1], check.names=FALSE)\n"
    rcode += "model <- paste(readLines(args[2], warn=FALSE), collapse='\\n')\n"
    rcode += "est <- args[3]\n"
    rcode += "ord <- if (nzchar(args[4])) strsplit(args[4], ',', fixed=TRUE)[[1]] else NULL\n"
    rcode += "miss <- if (!is.null(ord) && length(ord)>0) 'pairwise' else 'fiml'\nfit <- sem(model, data=dat, estimator=est, ordered=ord, missing=miss)\n"
    rcode += "write.csv(parameterEstimates(fit, standardized=TRUE, ci=TRUE), args[5], row.names=FALSE)\n"
    rcode += "fm <- fitMeasures(fit, c('chisq','df','pvalue','cfi','tli','rmsea','rmsea.ci.lower','rmsea.ci.upper','srmr','gfi','agfi','nfi','aic','bic'))\n"
    rcode += "write.csv(data.frame(index=names(fm), value=as.numeric(fm)), args[6], row.names=FALSE)\n"
    with tempfile.TemporaryDirectory(prefix="ra_lavaan_") as td:
        td=Path(td); csv=td/"data.csv"; syn=td/"model.lav"; rfile=td/"run.R"; po=td/"params.csv"; fo=td/"fit.csv"
        data.to_csv(csv,index=False); syn.write_text(syntax,encoding="utf-8"); rfile.write_text(rcode,encoding="utf-8")
        proc=subprocess.run([exe,str(rfile),str(csv),str(syn),estimator,",".join(ordered or []),str(po),str(fo)],capture_output=True,text=True,timeout=timeout)
        if proc.returncode: raise RuntimeError("lavaan gagal:\n"+proc.stderr[-3000:])
        if not po.exists() or not fo.exists(): raise RuntimeError("R tidak menghasilkan berkas keluaran.")
        return {"parameters":pd.read_csv(po),"fit_indices":pd.read_csv(fo),"stdout":proc.stdout[-2000:],"estimator":estimator,"n":len(data)}
