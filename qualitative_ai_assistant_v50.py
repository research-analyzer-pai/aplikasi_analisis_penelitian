"""AI-assisted qualitative coding support (v5.0).

Default mode is an explainable TF-IDF lexical baseline. Optional multilingual
sentence-transformers mode produces embedding-similarity suggestions. Neither
mode performs autonomous interpretation or approves codes.
"""
from __future__ import annotations
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def _clean(value):
    return re.sub(r"\s+"," ",str(value or "")).strip()

def suggest_qualitative_codes(segments: pd.DataFrame, codebook: pd.DataFrame,
                              method="tfidf", top_n=3, threshold=0.05,
                              model_name="paraphrase-multilingual-MiniLM-L12-v2",
                              model=None):
    if not {"segment_id","text"}.issubset(segments.columns):
        raise ValueError("Data segmen harus memiliki segment_id dan text.")
    if not {"code","definition"}.issubset(codebook.columns):
        raise ValueError("Codebook harus memiliki code dan definition.")
    if segments.empty or codebook.empty:
        return pd.DataFrame(columns=["segment_id","suggested_code","similarity","definition","rationale","review_status","method"])
    if codebook.code.astype(str).duplicated().any():
        raise ValueError("Kode dalam codebook harus unik.")
    defs=codebook.definition.fillna("").astype(str).tolist()
    texts=segments.text.fillna("").astype(str).tolist()
    if method=="tfidf":
        corpus=defs+texts
        vec=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)
        matrix=vec.fit_transform(corpus)
        sim=cosine_similarity(matrix[len(defs):],matrix[:len(defs)])
        method_label="TF-IDF lexical similarity"
        threshold=float(threshold)
    elif method=="multilingual_embedding":
        if model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError("Mode embedding memerlukan: pip install sentence-transformers") from e
            model=SentenceTransformer(model_name)
        emb=np.asarray(model.encode(defs+texts,normalize_embeddings=True,show_progress_bar=False))
        sim=emb[len(defs):] @ emb[:len(defs)].T
        method_label="Multilingual sentence embedding similarity"
    else:
        raise ValueError("method harus tfidf atau multilingual_embedding.")
    rows=[]
    for i,seg in enumerate(segments.itertuples(index=False)):
        order=np.argsort(sim[i])[::-1][:max(1,int(top_n))]
        for j in order:
            score=float(sim[i,j])
            if score>=threshold:
                rows.append({"segment_id":str(seg.segment_id),
                    "suggested_code":str(codebook.iloc[j].code),
                    "similarity":round(score,4),
                    "definition":str(codebook.iloc[j].definition),
                    "rationale":method_label,
                    "review_status":"Pending — wajib ditinjau peneliti",
                    "method":method_label})
    return pd.DataFrame(rows,columns=["segment_id","suggested_code","similarity","definition","rationale","review_status","method"])

def apply_researcher_decisions(suggestions: pd.DataFrame, decisions: pd.DataFrame):
    """Join explicit researcher decisions; suggestions are never auto-approved."""
    if not {"segment_id","suggested_code"}.issubset(suggestions.columns):
        raise ValueError("Tabel saran memerlukan segment_id dan suggested_code.")
    if not {"segment_id","suggested_code","decision","reviewer"}.issubset(decisions.columns):
        raise ValueError("Keputusan memerlukan segment_id, suggested_code, decision, reviewer.")
    allowed={"approved","rejected","revise","pending"}
    d=decisions.copy()
    d["decision"]=d.decision.astype(str).str.lower().str.strip()
    if not set(d.decision).issubset(allowed):
        raise ValueError("decision hanya boleh approved, rejected, revise, atau pending.")
    if d.duplicated(["segment_id","suggested_code"]).any():
        raise ValueError("Keputusan ganda untuk segmen dan kode yang sama.")
    return suggestions.merge(d,on=["segment_id","suggested_code"],how="left",validate="one_to_one").assign(
        researcher_status=lambda x:x.decision.fillna("pending"),
        researcher_review=lambda x:x.reviewer.fillna("Belum ditinjau"))

def codebook_coverage(suggestions: pd.DataFrame, segments: pd.DataFrame):
    n=0 if segments is None else len(segments)
    proposed=0 if suggestions is None or suggestions.empty else suggestions.segment_id.nunique()
    reviewed=0 if suggestions is None or suggestions.empty or "researcher_status" not in suggestions else suggestions.loc[suggestions.researcher_status.ne("pending"),"segment_id"].nunique()
    return {"total_segments":int(n),"segments_with_suggestions":int(proposed),
            "segments_with_researcher_decisions":int(reviewed),
            "suggestion_coverage_pct":round(100*proposed/n,2) if n else 0.0,
            "decision_coverage_pct":round(100*reviewed/n,2) if n else 0.0,
            "warning":"Coverage mengukur cakupan teknis, bukan kualitas atau validitas interpretasi."}
