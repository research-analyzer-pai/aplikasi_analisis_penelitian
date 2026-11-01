
"""Journal submission readiness checks and manuscript metadata helpers."""
import re
import pandas as pd

REQUIRED_SECTIONS=["Title","Abstract","Keywords","Introduction","Methods","Results",
                   "Discussion","Conclusion","References"]

def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b",str(text),flags=re.UNICODE))

def doi_coverage(references):
    refs=[x.strip() for x in str(references).splitlines() if x.strip()]
    if not refs: return {"total":0,"with_doi":0,"without_doi":0,"coverage":0.0}
    with_doi=sum(bool(re.search(r"10\.\d{4,9}/\S+",r,re.I) or "doi.org/" in r.lower()) for r in refs)
    return {"total":len(refs),"with_doi":with_doi,"without_doi":len(refs)-with_doi,
            "coverage":with_doi/len(refs)*100}

def manuscript_readiness(title,abstract,keywords,sections,references,
                         abstract_limit=250,keyword_min=3,keyword_max=6):
    checks=[]
    checks.append(("Judul tersedia",bool(str(title).strip()),"Lengkapi judul manuskrip."))
    awc=word_count(abstract)
    checks.append(("Abstrak tersedia",awc>0,f"Jumlah kata abstrak: {awc}."))
    checks.append(("Batas kata abstrak",awc<=int(abstract_limit),f"Target maksimum {abstract_limit} kata; periksa panduan jurnal."))
    kws=[x.strip() for x in re.split(r"[,;]",str(keywords)) if x.strip()]
    checks.append(("Jumlah kata kunci",int(keyword_min)<=len(kws)<=int(keyword_max),
                   f"Jumlah kata kunci: {len(kws)}; rentang yang ditetapkan {keyword_min}–{keyword_max}."))
    for sec in REQUIRED_SECTIONS:
        if sec in ["Title","Abstract","Keywords","References"]: continue
        checks.append((f"Bagian {sec}",bool(sections.get(sec,"").strip()),f"Bagian {sec} perlu dilengkapi." if not sections.get(sec,"").strip() else f"Bagian {sec} terisi."))
    refs=doi_coverage(references)
    checks.append(("Referensi tersedia",refs["total"]>0,f"{refs['total']} referensi terdeteksi."))
    passed=sum(1 for _,ok,_ in checks if ok)
    return {"checks":checks,"passed":passed,"total":len(checks),
            "score":passed/len(checks)*100 if checks else 0,"abstract_words":awc,"keywords":kws,
            "reference_doi":refs}

def manuscript_outline_for_journal(title,journal,article_type,abstract_limit,style):
    return f"""# {title or '[Judul manuskrip]'}

**Jurnal sasaran:** {journal or '[Nama jurnal]'}
**Jenis artikel:** {article_type}
**Gaya referensi:** {style}
**Batas abstrak yang ditetapkan pengguna:** {abstract_limit} kata

## Title
[Judul spesifik, informatif, dan sesuai ruang lingkup jurnal.]

## Abstract
[Tujuan; metode; hasil utama terverifikasi; kontribusi. Maksimum {abstract_limit} kata.]

## Keywords
[Masukkan kata kunci sesuai petunjuk jurnal.]

## 1. Introduction
[Masalah, konteks, state of the art, gap berbasis bukti, tujuan dan kontribusi.]

## 2. Methods
[Desain, lokasi/konteks, partisipan/sampel, instrumen, prosedur, analisis, etik.]

## 3. Results
[Hasil sesuai data; tabel/gambar dirujuk secara konsisten.]

## 4. Discussion
[Interpretasi, teori, studi terdahulu terverifikasi, kontribusi, implikasi.]

## 5. Conclusion
[Jawaban ringkas atas tujuan/pertanyaan penelitian.]

## Declarations
[Ethics approval; consent; funding; conflict of interest; data availability; author contributions sesuai kebijakan jurnal.]

## References
[Format {style}; verifikasi setiap DOI dan metadata dari sumber primer.]
"""

def reference_style_note(style):
    notes={
      "APA 7":"Gunakan author–date; urut alfabetis; format DOI sebagai URL https://doi.org/...",
      "Harvard":"Gunakan author–date; aturan detail berbeda antar jurnal, ikuti house style.",
      "Vancouver":"Gunakan sitasi bernomor sesuai urutan kemunculan; cocokkan dengan panduan jurnal.",
      "Chicago":"Pastikan memilih sistem Notes-Bibliography atau Author-Date sesuai pedoman.",
      "IEEE":"Gunakan sitasi bernomor dalam tanda kurung siku sesuai urutan kemunculan."
    }
    return notes.get(style,"Periksa panduan referensi resmi jurnal sasaran.")
