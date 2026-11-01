"""Auditable qualitative methods for Research Analyzer v3.6."""
import re
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

BRAUN_CLARKE_PHASES = [
"Familiarisasi dengan data", "Menghasilkan kode awal", "Mencari tema",
"Meninjau tema", "Mendefinisikan dan menamai tema", "Menyusun laporan"]

def semantic_code_suggestions(segments, codebook, model_name="paraphrase-multilingual-MiniLM-L12-v2",
                              top_n=3, threshold=0.35, model=None):
    """Optional multilingual embeddings; suggestions are never auto-approved."""
    if not {"segment_id","text"}.issubset(segments.columns) or not {"code","definition"}.issubset(codebook.columns):
        raise ValueError("Kolom wajib: segment_id,text dan code,definition.")
    if segments.empty or codebook.empty:
        return pd.DataFrame(columns=["segment_id","suggested_code","similarity","definition","review_status"])
    if model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError("Instal fitur opsional: pip install sentence-transformers") from e
        model = SentenceTransformer(model_name)
    defs=codebook.definition.fillna("").astype(str).tolist()
    texts=segments.text.fillna("").astype(str).tolist()
    emb=np.asarray(model.encode(defs+texts, normalize_embeddings=True, show_progress_bar=False))
    sim=emb[len(defs):] @ emb[:len(defs)].T
    rows=[]
    for i, seg in enumerate(segments.itertuples(index=False)):
        for j in np.argsort(sim[i])[::-1][:max(1,int(top_n))]:
            score=float(sim[i,j])
            if score >= threshold:
                rows.append({"segment_id":str(seg.segment_id),"suggested_code":str(codebook.iloc[j].code),
                 "similarity":round(score,4),"definition":str(codebook.iloc[j].definition),
                 "review_status":"Pending researcher review","method":"Multilingual sentence embedding"})
    return pd.DataFrame(rows)

def intercoder_agreement(coder_a, coder_b, labels=None):
    if len(coder_a)!=len(coder_b): raise ValueError("Jumlah unit coding kedua coder harus sama.")
    if len(coder_a)<2: raise ValueError("Minimal dua unit coding diperlukan.")
    if any(pd.isna(x) for x in coder_a) or any(pd.isna(x) for x in coder_b):
        raise ValueError("Data coding tidak boleh kosong.")
    return {"n_units":len(coder_a),
      "observed_agreement":float(np.mean(np.asarray(coder_a,dtype=object)==np.asarray(coder_b,dtype=object))),
      "cohens_kappa":float(cohen_kappa_score(coder_a,coder_b,labels=labels)),
      "interpretation_note":"Baca bersama distribusi kategori dan konteks; jangan gunakan ambang secara mekanis."}

def braun_clarke_tracker(decisions=None):
    base=pd.DataFrame({"phase":BRAUN_CLARKE_PHASES})
    if decisions is None or decisions.empty:
        base["status"]="Belum dimulai"; base["researcher_notes"]=""; base["evidence_reference"]=""; base["review_date"]=""
        return base
    if not {"phase","status"}.issubset(decisions.columns): raise ValueError("Keputusan memerlukan phase dan status.")
    return base.merge(decisions,on="phase",how="left",suffixes=("","_record"))

def coding_hierarchy(codebook):
    if not {"code","definition"}.issubset(codebook.columns): raise ValueError("Codebook perlu code dan definition.")
    out=codebook.copy()
    if "parent_code" not in out: out["parent_code"]=""
    out["code"]=out.code.astype(str).str.strip()
    out["parent_code"]=out.parent_code.fillna("").astype(str).str.strip()
    if out.code.duplicated().any(): raise ValueError("Kode harus unik.")
    known=set(out.code); unknown={p for p in out.parent_code if p and p not in known}
    if unknown: raise ValueError("Parent code tidak ditemukan: "+", ".join(sorted(unknown)))
    parents=dict(zip(out.code,out.parent_code))
    for code in parents:
        seen=set(); cur=code
        while cur:
            if cur in seen: raise ValueError("Hierarki codebook mengandung siklus.")
            seen.add(cur); cur=parents.get(cur,"")
    return out[["code","parent_code","definition"]]

def triangulation_matrix(evidence, theme_col="theme"):
    required={theme_col,"source","technique","evidence"}
    if not required.issubset(evidence.columns): raise ValueError("Kolom wajib: theme, source, technique, evidence.")
    return evidence.groupby(theme_col,dropna=False).agg(
      evidence_count=("evidence","count"),source_count=("source","nunique"),
      sources=("source",lambda x:"; ".join(sorted(set(map(str,x.dropna()))))),
      techniques=("technique",lambda x:"; ".join(sorted(set(map(str,x.dropna())))))).reset_index()

def negative_case_review(segments, coded_ids):
    out=segments.copy(); out["segment_id"]=out.segment_id.astype(str)
    out=out[~out.segment_id.isin(set(map(str,coded_ids)))].copy()
    out["review_reason"]="Belum terkoding: periksa sebagai bukti negatif, menyimpang, atau data terlewat"
    return out
