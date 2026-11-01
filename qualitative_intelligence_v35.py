"""Auditable qualitative and mixed-methods helpers for Research Analyzer v3.5.
These helpers organize evidence; they do not replace researcher interpretation.
"""
from __future__ import annotations
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def segment_by_sentence(text, segment_prefix="S"):
    parts=[normalize_text(x) for x in re.split(r"(?<=[.!?])\s+", str(text or "")) if normalize_text(x)]
    return pd.DataFrame([{"segment_id":f"{segment_prefix}{i+1:04d}","text":x} for i,x in enumerate(parts)])


def suggest_codes_tfidf(segments: pd.DataFrame, codebook: pd.DataFrame, top_n=3, threshold=0.08):
    """Transparent lexical-semantic baseline; suggestions require human review."""
    if segments is None or segments.empty or codebook is None or codebook.empty:
        return pd.DataFrame(columns=["segment_id","suggested_code","similarity","definition","review_status"])
    required_seg={"segment_id","text"}; required_cb={"code","definition"}
    if not required_seg.issubset(segments.columns) or not required_cb.issubset(codebook.columns):
        raise ValueError("Segmen harus memiliki segment_id,text dan codebook harus memiliki code,definition.")
    docs=[normalize_text(x) for x in codebook.definition.fillna("")]
    corpus=docs+[normalize_text(x) for x in segments.text.fillna("")]
    if not any(corpus): return pd.DataFrame(columns=["segment_id","suggested_code","similarity","definition","review_status"])
    mat=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True).fit_transform(corpus)
    sim=cosine_similarity(mat[len(docs):],mat[:len(docs)])
    rows=[]
    for i,(_,seg) in enumerate(segments.iterrows()):
        for j in np.argsort(sim[i])[::-1][:int(top_n)]:
            score=float(sim[i,j])
            if score>=float(threshold):
                rows.append({"segment_id":str(seg.segment_id),"suggested_code":str(codebook.iloc[j].code),
                    "similarity":round(score,4),"definition":str(codebook.iloc[j].definition),"review_status":"Pending"})
    return pd.DataFrame(rows,columns=["segment_id","suggested_code","similarity","definition","review_status"])


def code_cooccurrence(coding: pd.DataFrame):
    if coding is None or coding.empty or not {"segment_id","code"}.issubset(coding.columns):
        return pd.DataFrame()
    d=coding.dropna(subset=["segment_id","code"])
    sets=d.groupby("segment_id").code.apply(lambda x:sorted(set(map(str,x))))
    codes=sorted(set(d.code.astype(str)))
    out=pd.DataFrame(0,index=codes,columns=codes,dtype=int)
    for items in sets:
        for a in items:
            for b in items: out.loc[a,b]+=1
    out.index.name="code"; return out


def negative_case_matrix(segments: pd.DataFrame, coding: pd.DataFrame, themes=None):
    """List evidence segments not yet linked to a theme/coding decision."""
    if segments is None or segments.empty: return pd.DataFrame(columns=["segment_id","source","participant","text","review_flag"])
    used=set()
    if coding is not None and not coding.empty and "segment_id" in coding:
        used=set(coding.segment_id.astype(str))
    d=segments.copy(); d["segment_id"]=d.segment_id.astype(str)
    d=d[~d.segment_id.isin(used)].copy()
    d["review_flag"]="Uncoded: periksa apakah bukti negatif, menyimpang, atau belum dianalisis"
    for c in ["source","participant"]:
        if c not in d: d[c]=""
    return d[["segment_id","source","participant","text","review_flag"]]


def joint_display(quant: pd.DataFrame, qual: pd.DataFrame, quant_key="construct", qual_key="theme"):
    """Researcher-mediated join on explicitly harmonized construct/theme labels."""
    if quant is None or quant.empty or qual is None or qual.empty:
        return pd.DataFrame(columns=["construct_theme","quantitative_evidence","qualitative_evidence","integration_note","relationship"])
    if quant_key not in quant or qual_key not in qual:
        raise ValueError("Kolom kunci integrasi tidak ditemukan.")
    q=quant.copy(); l=qual.copy()
    q[quant_key]=q[quant_key].astype(str).str.strip(); l[qual_key]=l[qual_key].astype(str).str.strip()
    qsum={}
    for k,g in q.groupby(quant_key):
        qsum[k]="; ".join(f"{r.get('indicator',r.get('path','hasil'))}: {r.get('result',r.get('beta',r.get('value','')))}" for _,r in g.iterrows())
    lsum={}
    for k,g in l.groupby(qual_key):
        col="interpretation" if "interpretation" in g else ("evidence_quote" if "evidence_quote" in g else "code")
        lsum[k]="; ".join(str(x) for x in g[col].dropna().astype(str))
    keys=sorted(set(qsum)|set(lsum))
    return pd.DataFrame([{"construct_theme":k,"quantitative_evidence":qsum.get(k,"Tidak tersedia"),
        "qualitative_evidence":lsum.get(k,"Tidak tersedia"),"integration_note":"Diisi peneliti setelah membandingkan bukti",
        "relationship":"Belum ditentukan"} for k in keys])


def coding_coverage(segments: pd.DataFrame, coding: pd.DataFrame):
    n=0 if segments is None else len(segments)
    used=0 if coding is None or coding.empty else coding.segment_id.astype(str).nunique()
    return {"total_segments":n,"coded_segments":used,"uncoded_segments":max(0,n-used),
            "coverage_pct":round(100*used/n,2) if n else 0.0}
