"""Evidence-grounded academic reporting utilities for Research Analyzer v3.8.
No statistical estimates or citations are invented; all source facts must be supplied by researcher.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_PATHS = {"path", "beta"}

def audit_sem_results(paths: pd.DataFrame) -> pd.DataFrame:
    if not REQUIRED_PATHS.issubset(paths.columns):
        raise ValueError("Tabel jalur memerlukan kolom path dan beta.")
    d=paths.copy()
    d["path"]=d["path"].astype(str).str.strip()
    d["beta"]=pd.to_numeric(d["beta"],errors="coerce")
    issues=[]
    for i,r in d.iterrows():
        row=[]
        if not r["path"] or r["path"].lower()=="nan": row.append("Nama jalur kosong")
        if pd.isna(r["beta"]): row.append("Koefisien beta tidak numerik")
        if "p" in d.columns:
            p=pd.to_numeric(pd.Series([r["p"]]),errors="coerce").iloc[0]
            if not pd.isna(p) and not 0<=p<=1: row.append("P-value di luar rentang 0–1")
        if {"ci_low","ci_high"}.issubset(d.columns):
            lo=pd.to_numeric(pd.Series([r["ci_low"]]),errors="coerce").iloc[0]
            hi=pd.to_numeric(pd.Series([r["ci_high"]]),errors="coerce").iloc[0]
            if not pd.isna(lo) and not pd.isna(hi) and lo>hi: row.append("CI lower lebih besar daripada upper")
        issues.append("; ".join(row) if row else "Tidak ada masalah format yang terdeteksi")
    d["audit_note"]=issues
    d["direction"]=np.where(d.beta>0,"Positif",np.where(d.beta<0,"Negatif","Nol"))
    if "p" in d.columns:
        p=pd.to_numeric(d["p"],errors="coerce")
        d["decision_p05"]=np.where(p.isna(),"Tidak dapat dinilai",np.where(p<.05,"Signifikan pada 0,05","Tidak signifikan pada 0,05"))
    else:
        d["decision_p05"]="Tidak tersedia: p-value tidak diimpor"
    if {"ci_low","ci_high"}.issubset(d.columns):
        lo=pd.to_numeric(d.ci_low,errors="coerce"); hi=pd.to_numeric(d.ci_high,errors="coerce")
        d["ci_decision"]=np.where(lo.isna()|hi.isna(),"CI tidak tersedia",
          np.where((lo>0)|(hi<0),"CI tidak melintasi nol","CI melintasi nol"))
    else: d["ci_decision"]="CI tidak tersedia"
    return d

def hypothesis_table(audit: pd.DataFrame, hypotheses: pd.DataFrame|None=None) -> pd.DataFrame:
    if not {"path","beta","decision_p05"}.issubset(audit.columns):
        raise ValueError("Masukkan hasil audit SEM terlebih dahulu.")
    out=audit[["path","beta","direction","decision_p05","ci_decision"]].copy()
    if hypotheses is not None:
        if not {"path","hypothesis"}.issubset(hypotheses.columns):
            raise ValueError("Tabel hipotesis memerlukan kolom path dan hypothesis.")
        out=out.merge(hypotheses[["path","hypothesis"]],on="path",how="left")
    out["researcher_conclusion"]="Perlu keputusan dan justifikasi peneliti"
    return out

def make_chapter_iv_draft(audit: pd.DataFrame, study_context: str,
                          method_note: str, qualitative_summary: str="",
                          joint_display_summary: str="") -> str:
    if audit.empty: raise ValueError("Hasil SEM kosong.")
    lines=[]
    for r in audit.itertuples(index=False):
        beta="tidak tersedia" if pd.isna(r.beta) else f"{r.beta:.3f}"
        lines.append(f"- {r.path}: koefisien β={beta}; arah hubungan {r.direction}; "
                     f"keputusan berdasarkan p-value: {r.decision_p05}; {r.ci_decision}.")
    return ("BAB IV. HASIL PENELITIAN DAN PEMBAHASAN\n\n"
      "A. Konteks penelitian\n"+(study_context.strip() or "[Lengkapi konteks penelitian berdasarkan data lapangan]")+
      "\n\nB. Catatan metode analisis\n"+(method_note.strip() or "[Lengkapi estimator, perangkat lunak, ukuran sampel, dan penanganan data]")+
      "\n\nC. Hasil pengujian hubungan\n"+"\n".join(lines)+
      "\n\nD. Temuan kualitatif\n"+(qualitative_summary.strip() or "[Masukkan tema, kutipan anonim, sumber, dan kasus yang berbeda]")+
      "\n\nE. Integrasi temuan\n"+(joint_display_summary.strip() or "[Jelaskan konvergensi, komplementaritas, atau divergensi berdasarkan joint display]")+
      "\n\nCatatan: narasi ini merupakan kerangka berbasis hasil impor, bukan interpretasi final. Periksa output sumber, spesifikasi model, asumsi, dan bukti mentah.")

def make_chapter_v_draft(research_questions: str, findings: str,
                         theory_discussion: str, prior_studies: str,
                         limitations: str, implications: str) -> str:
    required=[research_questions,findings,theory_discussion,prior_studies,limitations,implications]
    labels=["Rumusan masalah/tujuan","Ringkasan temuan","Dialog dengan teori","Perbandingan penelitian terdahulu","Keterbatasan","Implikasi"]
    sections=[]
    for label,val in zip(labels,required):
        sections.append(label+"\n"+(val.strip() if val and val.strip() else "[Perlu dilengkapi oleh peneliti; aplikasi tidak mengarang isi atau referensi]"))
    return "BAB V. PENUTUP DAN IMPLIKASI\n\n"+"\n\n".join(sections)

def export_report_docx(chapter_iv: str, chapter_v: str, output_path: str):
    try:
        from docx import Document
    except ImportError as e:
        raise ImportError("Instal python-docx untuk ekspor DOCX: pip install python-docx") from e
    doc=Document()
    for text in [chapter_iv,chapter_v]:
        for para in text.split("\n"):
            if para.startswith("BAB "):
                doc.add_heading(para,level=1)
            elif len(para)<100 and para and para[:1].isalpha() and para[:2] in {"A.","B.","C.","D.","E."}:
                doc.add_heading(para,level=2)
            elif para:
                doc.add_paragraph(para)
            else:
                doc.add_paragraph("")
    doc.save(output_path)
    return output_path
