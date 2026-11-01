"""Expanded mixed-methods meta-inference workspace (v5.0).

Integration relationships are researcher-entered; the software checks completeness
and creates traceable reporting structures without classifying findings itself.
"""
from __future__ import annotations
import pandas as pd

RELATIONSHIPS=["convergence","complementarity","expansion","divergence","silence","unrelated","undetermined"]

def build_meta_inference_table(joint_display: pd.DataFrame, decisions: pd.DataFrame):
    required={"quant_path","beta","p","theme","evidence_id","evidence"}
    if not required.issubset(joint_display.columns):
        raise ValueError("Joint display perlu quant_path, beta, p, theme, evidence_id, evidence.")
    dreq={"quant_path","relationship","meta_inference","researcher","evidence_basis"}
    if not dreq.issubset(decisions.columns):
        raise ValueError("Keputusan perlu quant_path, relationship, meta_inference, researcher, evidence_basis.")
    d=decisions.copy()
    d["relationship"]=d.relationship.astype(str).str.lower().str.strip()
    if not set(d.relationship).issubset(RELATIONSHIPS):
        raise ValueError("Relasi integrasi tidak dikenali: "+", ".join(RELATIONSHIPS))
    if d.quant_path.duplicated().any():
        raise ValueError("Satu keputusan meta-inferensi per jalur kuantitatif.")
    out=joint_display.merge(d,on="quant_path",how="left",validate="many_to_one")
    out["decision_status"]=out.relationship.fillna("undetermined")
    out["review_status"]=out.apply(lambda r:
        "Lengkap" if all(str(r.get(c,"")).strip() not in {"","nan","None"} for c in ["meta_inference","researcher","evidence_basis"])
        else "Perlu dilengkapi",axis=1)
    return out

def integration_completeness(meta_table: pd.DataFrame):
    if "decision_status" not in meta_table or "review_status" not in meta_table:
        raise ValueError("Jalankan build_meta_inference_table terlebih dahulu.")
    return pd.DataFrame([
      {"item":"Baris joint display","count":len(meta_table)},
      {"item":"Jalur dengan keputusan relasi eksplisit","count":int(meta_table.decision_status.ne("undetermined").sum())},
      {"item":"Meta-inferensi lengkap","count":int(meta_table.review_status.eq("Lengkap").sum())},
      {"item":"Meta-inferensi perlu dilengkapi","count":int(meta_table.review_status.ne("Lengkap").sum())}
    ])

def meta_inference_narrative(meta_table: pd.DataFrame):
    required={"quant_path","beta","p","theme","relationship","meta_inference","researcher","evidence_basis","review_status"}
    if not required.issubset(meta_table.columns):
        raise ValueError("Tabel meta-inferensi belum lengkap.")
    lines=[]
    for r in meta_table.drop_duplicates("quant_path").itertuples(index=False):
        beta="tidak tersedia" if pd.isna(r.beta) else f"{float(r.beta):.3f}"
        p="tidak tersedia" if pd.isna(r.p) else f"{float(r.p):.4f}"
        lines.append(f"Jalur {r.quant_path} (β={beta}, p={p}) dipetakan dengan tema {r.theme}. "
          f"Relasi integrasi yang ditetapkan peneliti: {r.relationship}. "
          f"Meta-inferensi: {r.meta_inference or '[belum diisi]'}. "
          f"Dasar bukti: {r.evidence_basis or '[belum diisi]'}. "
          f"Penanggung jawab interpretasi: {r.researcher or '[belum diisi]'}. "
          f"Status: {r.review_status}.")
    return "\n\n".join(lines)
