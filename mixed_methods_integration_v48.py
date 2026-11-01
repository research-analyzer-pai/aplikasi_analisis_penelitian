"""Auditable mixed-methods integration and meta-inference helpers (v4.8).

The functions organize linked evidence and flag gaps. They do not infer
convergence/complementarity or replace researcher interpretation.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

def validate_integration_inputs(quant: pd.DataFrame, qual: pd.DataFrame,
                                mapping: pd.DataFrame):
    qreq={"path","beta"}
    lreq={"theme","evidence","evidence_id"}
    mreq={"quant_path","theme","evidence_id","integration_rationale"}
    if not isinstance(quant,pd.DataFrame) or not qreq.issubset(quant.columns):
        raise ValueError("Data kuantitatif wajib memiliki kolom path dan beta.")
    if not isinstance(qual,pd.DataFrame) or not lreq.issubset(qual.columns):
        raise ValueError("Data kualitatif wajib memiliki theme, evidence, evidence_id.")
    if not isinstance(mapping,pd.DataFrame) or not mreq.issubset(mapping.columns):
        raise ValueError("Pemetaan wajib memiliki quant_path, theme, evidence_id, integration_rationale.")
    if quant.empty or qual.empty or mapping.empty:
        raise ValueError("Ketiga tabel harus berisi data.")
    for frame, cols, label in [(quant,["path"],"jalur kuantitatif"),
                               (qual,["theme","evidence_id"],"bukti kualitatif"),
                               (mapping,["quant_path","theme","evidence_id"],"pemetaan")]:
        for c in cols:
            if frame[c].isna().any() or frame[c].astype(str).str.strip().eq("").any():
                raise ValueError(f"Ada nilai kosong pada {label}: {c}.")
    return True

def build_evidence_linked_joint_display(quant, qual, mapping):
    validate_integration_inputs(quant,qual,mapping)
    q=quant.copy()
    q["path"]=q.path.astype(str).str.strip()
    q["beta"]=pd.to_numeric(q.beta,errors="coerce")
    if q.beta.isna().any():
        raise ValueError("Kolom beta harus numerik.")
    if q.path.duplicated().any():
        raise ValueError("Path kuantitatif duplikat; pastikan satu baris per jalur.")
    l=qual.copy()
    l["theme"]=l.theme.astype(str).str.strip()
    l["evidence_id"]=l.evidence_id.astype(str).str.strip()
    m=mapping.copy()
    m["quant_path"]=m.quant_path.astype(str).str.strip()
    m["theme"]=m.theme.astype(str).str.strip()
    m["evidence_id"]=m.evidence_id.astype(str).str.strip()
    qmap=q.set_index("path",drop=False)
    lmap=l.set_index("evidence_id",drop=False)
    rows=[]
    for r in m.itertuples(index=False):
        path=str(r.quant_path); eid=str(r.evidence_id); theme=str(r.theme)
        qrow=qmap.loc[path] if path in qmap.index else None
        if isinstance(qrow,pd.DataFrame): qrow=qrow.iloc[0]
        ev=lmap.loc[eid] if eid in lmap.index else None
        if isinstance(ev,pd.DataFrame): ev=ev.iloc[0]
        issues=[]
        if qrow is None: issues.append("Jalur kuantitatif tidak ditemukan")
        if ev is None: issues.append("ID bukti kualitatif tidak ditemukan")
        elif str(ev.theme).strip()!=theme: issues.append("Tema pada pemetaan tidak cocok dengan tema bukti")
        rows.append({
          "quant_path":path,"beta":np.nan if qrow is None else float(qrow.beta),
          "p":np.nan if qrow is None or "p" not in qrow.index else pd.to_numeric(pd.Series([qrow.get("p")]),errors="coerce").iloc[0],
          "theme":theme,"evidence_id":eid,
          "evidence":"" if ev is None else str(ev.evidence),
          "source":"" if ev is None else str(ev.get("source","")),
          "technique":"" if ev is None else str(ev.get("technique","")),
          "integration_rationale":str(r.integration_rationale),
          "link_status":"; ".join(issues) if issues else "Terverifikasi secara struktural",
          "researcher_meta_inference":"Diisi dan disahkan oleh peneliti"
        })
    return pd.DataFrame(rows)

def integration_audit(joint_display: pd.DataFrame):
    required={"quant_path","evidence_id","link_status","source","technique"}
    if not required.issubset(joint_display.columns):
        raise ValueError("Joint display tidak memiliki kolom audit yang diperlukan.")
    d=joint_display.copy()
    valid=d.link_status.eq("Terverifikasi secara struktural")
    return pd.DataFrame([
      {"audit":"Jumlah tautan bukti","value":int(len(d)),"status":"Informasi"},
      {"audit":"Tautan struktural terverifikasi","value":int(valid.sum()),"status":"Informasi"},
      {"audit":"Tautan bermasalah","value":int((~valid).sum()),"status":"Perlu ditinjau" if (~valid).any() else "Tidak ada"},
      {"audit":"Sumber data unik","value":int(d.source.replace("",np.nan).nunique()),"status":"Informasi"},
      {"audit":"Teknik pengumpulan unik","value":int(d.technique.replace("",np.nan).nunique()),"status":"Informasi"},
      {"audit":"Jalur kuantitatif unik","value":int(d.quant_path.nunique()),"status":"Informasi"},
      {"audit":"ID bukti unik","value":int(d.evidence_id.nunique()),"status":"Informasi"}
    ])

def summarize_integration_by_path(joint_display: pd.DataFrame):
    required={"quant_path","beta","p","theme","evidence_id","evidence","link_status"}
    if not required.issubset(joint_display.columns):
        raise ValueError("Kolom joint display tidak lengkap.")
    rows=[]
    for path,g in joint_display.groupby("quant_path",dropna=False):
        beta=g.beta.dropna()
        p=g.p.dropna()
        rows.append({"quant_path":path,
          "beta":float(beta.iloc[0]) if len(beta) else np.nan,
          "p":float(p.iloc[0]) if len(p) else np.nan,
          "themes":"; ".join(sorted(set(g.theme.astype(str)))),
          "evidence_count":int(g.evidence_id.nunique()),
          "structurally_valid_links":int(g.link_status.eq("Terverifikasi secara struktural").sum()),
          "evidence_summary":" | ".join(g.evidence.astype(str).drop_duplicates().head(5)),
          "meta_inference_prompt":"Apakah temuan kualitatif menjelaskan, memperluas, mengontradiksi, atau tidak terkait dengan hasil kuantitatif? Jelaskan berdasarkan bukti."
        })
    return pd.DataFrame(rows)

def export_integration_narrative(summary: pd.DataFrame):
    required={"quant_path","beta","p","themes","evidence_count","evidence_summary","meta_inference_prompt"}
    if not required.issubset(summary.columns):
        raise ValueError("Ringkasan integrasi belum lengkap.")
    out=[]
    for r in summary.itertuples(index=False):
        b="tidak tersedia" if pd.isna(r.beta) else f"{float(r.beta):.3f}"
        p="tidak tersedia" if pd.isna(r.p) else f"{float(r.p):.4f}"
        out.append(
          f"Jalur kuantitatif {r.quant_path} memiliki koefisien β={b} dan p={p}. "
          f"Tema kualitatif yang dipetakan: {r.themes}. "
          f"Terdapat {int(r.evidence_count)} ID bukti yang terhubung. "
          f"Bukti yang perlu dibaca peneliti: {r.evidence_summary}. "
          f"Meta-inferensi belum ditetapkan otomatis. Pertanyaan analitis: {r.meta_inference_prompt}"
        )
    return "\n\n".join(out)
