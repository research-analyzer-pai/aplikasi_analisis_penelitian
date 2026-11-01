
"""Auditable advanced qualitative workflow helpers for Research Analyzer v3.4."""
import re
import pandas as pd
from collections import Counter

SEGMENT_COLUMNS=["segment_id","source","participant","text"]
CODE_COLUMNS=["segment_id","code","parent_code","category","theme","approach",
              "evidence_quote","analytic_memo","researcher_status","reviewer"]
THEME_COLUMNS=["theme","category","codes","supporting_segments","counter_evidence",
               "interpretation","researcher_decision"]

def normalize_segments(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=SEGMENT_COLUMNS)
    d=df.copy()
    if "segment_id" not in d.columns:
        d["segment_id"]=d.get("id",pd.Series(range(1,len(d)+1))).astype(str)
    if "source" not in d.columns: d["source"]=""
    if "participant" not in d.columns: d["participant"]=""
    if "text" not in d.columns: d["text"]=""
    d["segment_id"]=d["segment_id"].astype(str)
    d["text"]=d["text"].fillna("").astype(str)
    return d[SEGMENT_COLUMNS]

def chunk_segments(df, max_chars=12000):
    """Group whole transcript segments without splitting their text."""
    d=normalize_segments(df)
    chunks=[]; current=[]; size=0
    for _,r in d.iterrows():
        line=f"[ID:{r.segment_id}] [Sumber:{r.source}] [Informan:{r.participant}]\n{r.text}"
        if current and size+len(line)>max_chars:
            chunks.append("\n\n".join(current)); current=[]; size=0
        current.append(line); size+=len(line)
    if current: chunks.append("\n\n".join(current))
    return chunks

def empty_codebook():
    return pd.DataFrame(columns=["code","parent_code","definition","inclusion_criteria",
        "exclusion_criteria","example_quote","theme","approach","version","review_status"])

def validate_codebook(df):
    required=["code","definition","inclusion_criteria","exclusion_criteria"]
    missing=[c for c in required if c not in df.columns]
    if missing: raise ValueError("Kolom codebook kurang: "+", ".join(missing))
    d=df.copy()
    d["code"]=d["code"].fillna("").astype(str).str.strip()
    if d["code"].eq("").any(): raise ValueError("Setiap kode harus memiliki nama.")
    if d["code"].duplicated().any(): raise ValueError("Nama kode harus unik.")
    known=set(d["code"])
    if "parent_code" in d:
        invalid=[x for x in d["parent_code"].fillna("").astype(str).str.strip() if x and x not in known]
        if invalid: raise ValueError("Parent code tidak ditemukan: "+", ".join(sorted(set(invalid))))
    return d

def build_theme_evidence(segments, coding):
    seg=normalize_segments(segments)
    if coding is None or coding.empty:
        return pd.DataFrame(columns=THEME_COLUMNS)
    c=coding.copy()
    if "segment_id" not in c or "theme" not in c:
        raise ValueError("Data coding memerlukan kolom segment_id dan theme.")
    c["segment_id"]=c["segment_id"].astype(str)
    merged=c.merge(seg[["segment_id","text"]],on="segment_id",how="left")
    rows=[]
    for theme,g in merged.groupby("theme",dropna=False):
        theme=str(theme)
        quotes=[]
        for _,r in g.iterrows():
            q=str(r.get("evidence_quote","") or r.get("text",""))
            if q.strip(): quotes.append(f"[{r.segment_id}] {q}")
        rows.append({"theme":theme,
            "category":"; ".join(sorted(set(g.get("category",pd.Series(dtype=str)).dropna().astype(str)))),
            "codes":"; ".join(sorted(set(g.get("code",pd.Series(dtype=str)).dropna().astype(str)))),
            "supporting_segments":"; ".join(sorted(set(g.segment_id))),
            "counter_evidence":"",
            "interpretation":"",
            "researcher_decision":"; ".join(quotes)})
    return pd.DataFrame(rows,columns=THEME_COLUMNS)

def triangulation_matrix(coding, source_col="source", technique_col="technique"):
    if coding is None or coding.empty:
        return pd.DataFrame(columns=["theme","evidence_sources","techniques","segments","coverage"])
    d=coding.copy()
    if "theme" not in d: raise ValueError("Kolom theme tidak tersedia.")
    if source_col not in d: d[source_col]="Tidak dicatat"
    if technique_col not in d: d[technique_col]="Tidak dicatat"
    rows=[]
    for theme,g in d.groupby("theme",dropna=False):
        sources=sorted(set(g[source_col].fillna("Tidak dicatat").astype(str)))
        techniques=sorted(set(g[technique_col].fillna("Tidak dicatat").astype(str)))
        rows.append({"theme":str(theme),"evidence_sources":"; ".join(sources),
            "techniques":"; ".join(techniques),"segments":len(g),
            "coverage":"Beragam" if len(sources)>1 and len(techniques)>1 else "Terbatas / perlu bukti tambahan"})
    return pd.DataFrame(rows)

def audit_summary(coding):
    if coding is None or coding.empty: return {"total":0,"approved":0,"pending":0,"rejected":0}
    status=coding.get("researcher_status",pd.Series(["Pending"]*len(coding))).fillna("Pending").astype(str).str.lower()
    return {"total":len(coding),"approved":int(status.isin(["approved","disetujui"]).sum()),
            "pending":int(status.isin(["pending","belum ditinjau","draft"]).sum()),
            "rejected":int(status.isin(["rejected","ditolak"]).sum())}
