"""Advanced qualitative case comparison and audit tools (v4.9).

These are transparent evidence-organization utilities. Frequencies and coverage
are descriptive only and must not be interpreted as thematic importance,
saturation proof, or causal evidence.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

def _require(df, columns, label):
    if not isinstance(df,pd.DataFrame):
        raise TypeError(f"{label} harus berupa DataFrame.")
    missing=set(columns)-set(df.columns)
    if missing: raise ValueError(f"{label} tidak memiliki kolom: {', '.join(sorted(missing))}.")
    if df.empty: raise ValueError(f"{label} kosong.")
    return df.copy()

def prepare_qualitative_data(segments: pd.DataFrame, coding: pd.DataFrame):
    s=_require(segments,["segment_id","source","participant","text"],"Data segmen")
    c=_require(coding,["segment_id","code","theme"],"Data coding")
    s["segment_id"]=s.segment_id.astype(str).str.strip()
    c["segment_id"]=c.segment_id.astype(str).str.strip()
    if s.segment_id.eq("").any() or s.segment_id.duplicated().any():
        raise ValueError("segment_id pada data segmen harus terisi dan unik.")
    unknown=set(c.segment_id)-set(s.segment_id)
    if unknown: raise ValueError("Coding merujuk segment_id yang tidak ada: "+", ".join(sorted(unknown)))
    for col in ["source","participant","text"]:
        s[col]=s[col].fillna("").astype(str)
    for col in ["code","theme"]:
        c[col]=c[col].fillna("").astype(str).str.strip()
    if (c[["code","theme"]]=="").any().any():
        raise ValueError("Setiap baris coding harus memiliki code dan theme.")
    merged=c.merge(s,on="segment_id",how="left",validate="many_to_one")
    return s,c,merged

def informant_theme_matrix(segments: pd.DataFrame, coding: pd.DataFrame,
                           participant_col="participant"):
    s,c,m=prepare_qualitative_data(segments,coding)
    if participant_col not in s: raise ValueError("Kolom informan tidak ditemukan.")
    counts=m.groupby([participant_col,"theme"]).segment_id.nunique().unstack(fill_value=0)
    counts.index.name="informant"
    return counts.reset_index()

def cross_case_theme_comparison(segments: pd.DataFrame, coding: pd.DataFrame,
                                case_col="participant"):
    s,c,m=prepare_qualitative_data(segments,coding)
    if case_col not in s: raise ValueError(f"Kolom kasus {case_col} tidak ditemukan.")
    rows=[]
    for theme,g in m.groupby("theme",dropna=False):
        cases=sorted(set(g[case_col].astype(str)))
        rows.append({"theme":str(theme),"case_count":len(cases),
          "cases":"; ".join(cases),"segment_count":int(g.segment_id.nunique()),
          "codes":"; ".join(sorted(set(g.code.astype(str)))),
          "interpretation":"Diisi peneliti setelah membaca konteks tiap kasus"})
    return pd.DataFrame(rows)

def theme_evidence_profile(segments: pd.DataFrame, coding: pd.DataFrame):
    s,c,m=prepare_qualitative_data(segments,coding)
    if "evidence_type" not in c:
        c["evidence_type"]="supporting"
    m=c.merge(s,on="segment_id",how="left",validate="many_to_one")
    m["evidence_type"]=m.evidence_type.fillna("supporting").astype(str).str.lower()
    neg={"negative","contradictory","counter","disconfirming","deviant","kasus negatif","kontradiktif"}
    rows=[]
    for theme,g in m.groupby("theme",dropna=False):
        negative=g[g.evidence_type.isin(neg)]
        positive=g[~g.evidence_type.isin(neg)]
        rows.append({"theme":str(theme),"supporting_segments":int(positive.segment_id.nunique()),
          "counter_segments":int(negative.segment_id.nunique()),
          "supporting_evidence":" | ".join(positive.text.drop_duplicates().head(5)),
          "counter_evidence":" | ".join(negative.text.drop_duplicates().head(5)),
          "informants":"; ".join(sorted(set(g.participant.astype(str)))),
          "researcher_interpretation":"Wajib ditelaah peneliti; jumlah bukti bukan ukuran kepentingan tema"})
    return pd.DataFrame(rows)

def qualitative_audit(segments: pd.DataFrame, coding: pd.DataFrame):
    s,c,m=prepare_qualitative_data(segments,coding)
    used=set(c.segment_id)
    uncoded=s[~s.segment_id.isin(used)]
    memo_missing=int(c.analytic_memo.fillna("").astype(str).str.strip().eq("").sum()) if "analytic_memo" in c else len(c)
    quote_missing=int(c.evidence_quote.fillna("").astype(str).str.strip().eq("").sum()) if "evidence_quote" in c else len(c)
    status_missing=int(c.researcher_status.fillna("").astype(str).str.strip().eq("").sum()) if "researcher_status" in c else len(c)
    return pd.DataFrame([
      {"check":"Jumlah segmen","value":len(s),"status":"Deskriptif"},
      {"check":"Segmen terkoding","value":len(used),"status":"Deskriptif"},
      {"check":"Segmen belum terkoding","value":len(uncoded),"status":"Perlu ditinjau" if len(uncoded) else "Tidak ada"},
      {"check":"Baris coding tanpa memo analitis","value":memo_missing,"status":"Perlu ditinjau" if memo_missing else "Lengkap"},
      {"check":"Baris coding tanpa kutipan bukti","value":quote_missing,"status":"Perlu ditinjau" if quote_missing else "Lengkap"},
      {"check":"Baris coding tanpa status peneliti","value":status_missing,"status":"Perlu ditinjau" if status_missing else "Lengkap"},
      {"check":"Jumlah tema","value":int(c.theme.nunique()),"status":"Deskriptif"},
      {"check":"Jumlah informan","value":int(s.participant.nunique()),"status":"Deskriptif"}
    ])

def uncoded_evidence_review(segments: pd.DataFrame, coding: pd.DataFrame):
    s,c,m=prepare_qualitative_data(segments,coding)
    used=set(c.segment_id)
    out=s[~s.segment_id.isin(used)].copy()
    out["review_prompt"]="Periksa apakah segmen ini relevan, kasus negatif, konteks, atau tidak terkait dengan pertanyaan penelitian."
    return out

def saturation_sequence_audit(segments: pd.DataFrame, coding: pd.DataFrame,
                              wave_col="wave"):
    """Descriptive accumulation of newly observed codes across ordered waves."""
    s,c,m=prepare_qualitative_data(segments,coding)
    if wave_col not in s:
        raise ValueError(f"Kolom urutan/wave '{wave_col}' tidak tersedia pada segmen.")
    m[wave_col]=m[wave_col].astype(str)
    # Preserve first-seen order in the supplied segments.
    order=list(dict.fromkeys(s[wave_col].astype(str).tolist()))
    seen=set(); rows=[]
    for i,wave in enumerate(order,1):
        current=set(m.loc[m[wave_col]==wave,"code"].astype(str))
        new=current-seen
        rows.append({"wave_order":i,"wave":wave,"codes_observed":len(current),
          "new_codes":len(new),"new_code_list":"; ".join(sorted(new)),
          "cumulative_unique_codes":len(seen|current),
          "researcher_decision":"Belum dinilai"})
        seen |= current
    return pd.DataFrame(rows)

def participant_profile(segments: pd.DataFrame):
    s=_require(segments,["segment_id","source","participant","text"],"Data segmen")
    return s.groupby("participant",dropna=False).agg(
      segment_count=("segment_id","nunique"),
      source_count=("source","nunique"),
      text_characters=("text",lambda x:sum(len(str(v)) for v in x))
    ).reset_index()
