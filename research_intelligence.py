
"""Transparent rule-based research intelligence helpers.

Outputs are drafting aids based only on user-entered theory/model/results.
They do not retrieve literature or invent citations.
"""
import pandas as pd
import numpy as np

MAPPING_COLUMNS=["theory","theorist","construct","dimension","indicator","role","source"]
HYPOTHESIS_COLUMNS=["hypothesis","source_construct","target_construct","expected_direction","theoretical_rationale"]

def empty_mapping():
    return pd.DataFrame(columns=MAPPING_COLUMNS)

def empty_hypotheses():
    return pd.DataFrame(columns=HYPOTHESIS_COLUMNS)

def validate_mapping(mapping: pd.DataFrame):
    required=["theory","construct","dimension","indicator","role"]
    missing=[c for c in required if c not in mapping.columns]
    if missing: raise ValueError("Kolom pemetaan belum ada: "+", ".join(missing))
    d=mapping.copy()
    for c in required: d[c]=d[c].fillna("").astype(str).str.strip()
    errors=[]
    for c in required:
        if (d[c]=="").any(): errors.append(f"Ada nilai kosong pada kolom {c}.")
    if d.duplicated(["construct","dimension","indicator"]).any():
        errors.append("Terdapat kombinasi konstruk-dimensi-indikator yang duplikat.")
    roles={"independent","dependent","mediator","moderator","control","predictor","outcome","formative","reflective"}
    unknown=sorted(set(x.lower() for x in d.role if x and x.lower() not in roles))
    if unknown: errors.append("Role belum dikenali: "+", ".join(unknown))
    if errors: raise ValueError(" ".join(errors))
    return d

def validate_hypotheses(hypotheses: pd.DataFrame, constructs: list[str]):
    required=["hypothesis","source_construct","target_construct"]
    missing=[c for c in required if c not in hypotheses.columns]
    if missing: raise ValueError("Kolom hipotesis belum ada: "+", ".join(missing))
    issues=[]
    for i,row in hypotheses.iterrows():
        label=str(row.get("hypothesis","")).strip()
        a=str(row.get("source_construct","")).strip()
        b=str(row.get("target_construct","")).strip()
        if not label: issues.append(f"Baris {i+1}: label hipotesis kosong.")
        if a not in constructs: issues.append(f"{label or i+1}: konstruk sumber '{a}' tidak ada dalam pemetaan.")
        if b not in constructs: issues.append(f"{label or i+1}: konstruk target '{b}' tidak ada dalam pemetaan.")
        if a==b: issues.append(f"{label or i+1}: konstruk sumber dan target sama.")
    return issues

def check_model_consistency(mapping: pd.DataFrame, hypotheses: pd.DataFrame,
                            estimated_paths: pd.DataFrame|None=None):
    mapping=validate_mapping(mapping)
    constructs=sorted(mapping.construct.unique().tolist())
    issues=validate_hypotheses(hypotheses,constructs)
    if estimated_paths is not None and not estimated_paths.empty:
        paths=set()
        for _,r in estimated_paths.iterrows():
            raw=str(r.get("path",""))
            if "->" in raw:
                a,b=[x.strip() for x in raw.split("->",1)]
                paths.add((a,b))
        for _,r in hypotheses.iterrows():
            pair=(str(r.source_construct).strip(),str(r.target_construct).strip())
            if pair not in paths:
                issues.append(f"{r.hypothesis}: jalur {pair[0]} -> {pair[1]} tidak ditemukan pada hasil estimasi.")
        for a,b in paths:
            if a not in constructs or b not in constructs:
                issues.append(f"Jalur estimasi {a} -> {b} belum tercakup dalam pemetaan teori/variabel.")
    # role checks
    roles=mapping.groupby("construct").role.apply(lambda x:set(v.lower() for v in x)).to_dict()
    for c,rs in roles.items():
        if len(rs)>1:
            issues.append(f"Konstruk {c} memiliki role yang tidak konsisten: {', '.join(sorted(rs))}.")
    return {"constructs":constructs,"hypothesis_count":len(hypotheses),"issues":issues,
            "status":"Perlu revisi" if issues else "Konsisten secara struktural (perlu telaah teori)"}

def interpret_paths(paths: pd.DataFrame, alpha=0.05):
    if paths is None or paths.empty: return ["Belum ada hasil koefisien jalur untuk diinterpretasikan."]
    lines=[]
    for _,r in paths.iterrows():
        path=str(r.get("path",""))
        beta=pd.to_numeric(pd.Series([r.get("beta",np.nan)]),errors="coerce").iloc[0]
        p=pd.to_numeric(pd.Series([r.get("p_value",r.get("p_ols",np.nan))]),errors="coerce").iloc[0]
        if pd.isna(p): p=pd.to_numeric(pd.Series([r.get("p_ols",np.nan)]),errors="coerce").iloc[0]
        if pd.isna(beta):
            lines.append(f"Jalur {path}: koefisien tidak tersedia; interpretasi belum dapat dibuat.")
            continue
        if pd.isna(p):
            lines.append(f"Jalur {path}: β={beta:.3f}; signifikansi belum dapat disimpulkan karena p-value tidak tersedia.")
            continue
        decision="signifikan secara statistik" if p<alpha else "belum signifikan secara statistik"
        direction="positif" if beta>0 else ("negatif" if beta<0 else "tidak menunjukkan arah")
        lines.append(f"Jalur {path} memiliki koefisien β={beta:.3f} dengan p={p:.4f}; hubungan terestimasi {direction} dan {decision} pada α={alpha:.3f}.")
    return lines

def draft_chapter_four(project, design, mapping, paths=None, qualitative=None, joint=None, alpha=0.05):
    out=[f"BAB IV. HASIL PENELITIAN DAN PEMBAHASAN",f"Judul penelitian: {project}","",
         "4.1 Gambaran Umum dan Strategi Analisis",
         f"Penelitian ini menggunakan desain {design}. Uraian konteks, karakteristik partisipan/responden, prosedur pengumpulan data, dan tahapan analisis perlu dilengkapi berdasarkan catatan lapangan dan dokumen penelitian.",
         "","4.2 Operasionalisasi Konstruk dan Kerangka Analisis"]
    for c,g in mapping.groupby("construct"):
        dims=sorted(set(g.dimension.astype(str)))
        inds=sorted(set(g.indicator.astype(str)))
        out.append(f"Konstruk {c} dipetakan melalui dimensi {', '.join(dims)} dengan indikator {', '.join(inds)}.")
    out += ["","4.3 Hasil Pengujian Model dan Hipotesis"]
    out += interpret_paths(paths,alpha)
    out += ["","4.4 Temuan Kualitatif dan Integrasi"]
    if qualitative is not None and not qualitative.empty:
        for theme,g in qualitative.groupby("theme"):
            if str(theme).strip() and str(theme).lower()!="nan":
                codes=", ".join(sorted(set(g.code.astype(str))))
                out.append(f"Tema {theme} dibangun dari kode {codes}. Peneliti perlu menambahkan kutipan autentik, konteks informan, dan bukti observasi/dokumentasi.")
    else:
        out.append("Temuan kualitatif belum dimasukkan. Tambahkan tema, kutipan, identitas anonim informan, dan triangulasi bukti.")
    if joint is not None and not joint.empty:
        out += ["","4.5 Joint Display dan Meta-Inference"]
        for _,r in joint.iterrows():
            out.append(f"Temuan kuantitatif: {r.get('Temuan kuantitatif','')}; tema kualitatif: {r.get('Tema','')}; relasi: {r.get('Relasi','')}; meta-inference: {r.get('Meta-inference','')}.")
    out += ["","Catatan penulisan: narasi ini merupakan draf berbasis data yang dimasukkan pengguna. Lengkapi tabel, angka deskriptif, kutipan verbatim, konteks lokasi, serta sitasi sumber yang telah diverifikasi. Jangan mengisi bagian yang belum didukung data."]
    return "\n".join(out)

def draft_chapter_five(project, paths=None, alpha=0.05, mapping=None):
    out=["BAB V. PEMBAHASAN, KESIMPULAN, DAN SARAN",f"Judul penelitian: {project}","",
         "5.1 Pembahasan"]
    out.append("Pembahasan perlu mengaitkan setiap temuan dengan teori yang benar-benar digunakan, konteks penelitian, serta hasil studi terdahulu yang telah dibaca dan diverifikasi.")
    out += interpret_paths(paths,alpha)
    out += ["","5.2 Kesimpulan","Kesimpulan harus menjawab rumusan masalah dan tujuan penelitian satu per satu. Hindari klaim kausal apabila desain dan strategi identifikasi tidak mendukung inferensi kausal.",
            "","5.3 Implikasi","Jelaskan implikasi teoretis, praktis, dan kebijakan hanya sejauh didukung oleh temuan.",
            "","5.4 Keterbatasan","Nyatakan keterbatasan desain, sampling, instrumen, kualitas data, cakupan lokasi, serta batas algoritma analisis yang digunakan.",
            "","5.5 Rekomendasi","Susun rekomendasi yang spesifik untuk pemangku kepentingan dan agenda penelitian berikutnya.",
            "","Catatan: sistem tidak membuat referensi atau temuan terdahulu secara otomatis. Masukkan literatur terverifikasi untuk membangun argumentasi pembahasan."]
    return "\n".join(out)
