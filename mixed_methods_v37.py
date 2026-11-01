"""Evidence-linked mixed methods and SEM-result import utilities (v3.7)."""
from __future__ import annotations
import pandas as pd
import numpy as np

PATH_ALIASES = {
 "path": ["path","relationship","hypothesis","structural_path"],
 "beta": ["beta","original_sample","original sample","coefficient","path_coefficient","estimate"],
 "t": ["t","t_statistic","t statistics","t-value","t value"],
 "p": ["p","p_value","p values","p-value"],
 "ci_low": ["ci_low","2.5%","lower_ci","ci_lower"],
 "ci_high": ["ci_high","97.5%","upper_ci","ci_upper"],
}
def _norm(s): return str(s).strip().lower().replace("-","_").replace(" ","_")
def normalize_sem_paths(df):
    if not isinstance(df,pd.DataFrame) or df.empty: raise ValueError("File hasil SEM kosong atau bukan tabel.")
    lookup={_norm(c):c for c in df.columns}
    out=pd.DataFrame()
    for target, aliases in PATH_ALIASES.items():
        found=next((lookup[_norm(a)] for a in aliases if _norm(a) in lookup),None)
        if found is not None: out[target]=df[found]
    if "path" not in out or "beta" not in out:
        raise ValueError("Minimal harus ada kolom jalur/path dan koefisien beta/estimate.")
    for c in ["beta","t","p","ci_low","ci_high"]:
        if c in out: out[c]=pd.to_numeric(out[c],errors="coerce")
    out["source_row"]=np.arange(1,len(out)+1)
    out["significant_p05"]=out["p"].lt(.05) if "p" in out else pd.NA
    out["ci_excludes_zero"]=(out["ci_low"]*out["ci_high"]>0) if {"ci_low","ci_high"}.issubset(out.columns) else pd.NA
    return out

def sem_import_quality(df):
    norm=normalize_sem_paths(df)
    checks=[
      ("Path terisi",norm.path.notna().all()),
      ("Beta numerik",norm.beta.notna().all()),
      ("Tidak ada jalur duplikat",not norm.path.astype(str).duplicated().any()),
      ("P-value berada pada rentang 0–1",("p" not in norm) or norm.p.dropna().between(0,1).all()),
      ("Interval kepercayaan berurutan",not {"ci_low","ci_high"}.issubset(norm.columns) or (norm.ci_low<=norm.ci_high).all()),
    ]
    return pd.DataFrame(checks,columns=["pemeriksaan","lulus"])

def build_joint_display(quant, qual, mapping):
    """mapping columns: quant_path, theme, explanation, evidence_id."""
    required={"quant_path","theme","explanation","evidence_id"}
    if not required.issubset(mapping.columns): raise ValueError("Pemetaan perlu quant_path, theme, explanation, evidence_id.")
    if "path" not in quant.columns: raise ValueError("Hasil kuantitatif perlu kolom path.")
    if not {"theme","evidence"}.issubset(qual.columns): raise ValueError("Data kualitatif perlu kolom theme dan evidence.")
    q=quant.copy(); q["path"]=q.path.astype(str)
    rows=[]
    for r in mapping.itertuples(index=False):
        qp=q[q.path==str(r.quant_path)]
        ev=qual[qual.theme.astype(str)==str(r.theme)]
        if qp.empty: status="Jalur kuantitatif tidak ditemukan"
        elif ev.empty: status="Bukti kualitatif belum ditemukan"
        else: status="Terhubung; interpretasi perlu telaah peneliti"
        beta=qp.iloc[0].get("beta",np.nan) if not qp.empty else np.nan
        p=qp.iloc[0].get("p",np.nan) if not qp.empty else np.nan
        rows.append({"quant_path":r.quant_path,"beta":beta,"p":p,"theme":r.theme,
          "evidence_count":len(ev),"evidence_ids":str(r.evidence_id),
          "qualitative_evidence":" | ".join(ev.evidence.astype(str).head(5)),
          "integrative_explanation":r.explanation,"integration_status":status})
    return pd.DataFrame(rows)

def evidence_linked_narrative(joint):
    required={"quant_path","beta","p","theme","evidence_count","qualitative_evidence","integrative_explanation"}
    if not required.issubset(joint.columns): raise ValueError("Joint display belum lengkap.")
    lines=[]
    for r in joint.itertuples(index=False):
        beta="tidak tersedia" if pd.isna(r.beta) else f"{float(r.beta):.3f}"
        p="tidak tersedia" if pd.isna(r.p) else f"{float(r.p):.4f}"
        lines.append(f"Jalur {r.quant_path}: koefisien β={beta}, p={p}. Tema kualitatif: {r.theme} "
          f"(jumlah bukti yang terhubung: {int(r.evidence_count)}). "
          f"Penjelasan integratif yang diajukan peneliti: {r.integrative_explanation}. "
          f"Bukti: {r.qualitative_evidence}")
    return "\n\n".join(lines)
