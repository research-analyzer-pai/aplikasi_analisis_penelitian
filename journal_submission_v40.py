"""Journal submission readiness utilities; requirements are user-supplied."""
from __future__ import annotations
import re
import pandas as pd

DEFAULT_CHECKS = [
    ("Scope and aims", "Topik dan kontribusi sesuai ruang lingkup jurnal"),
    ("Article type", "Jenis artikel sesuai kategori yang diterima jurnal"),
    ("Anonymization", "Identitas penulis dihapus dari berkas naskah bila double-anonymous review"),
    ("Ethics approval", "Persetujuan etik atau alasan pengecualian dinyatakan"),
    ("Informed consent", "Persetujuan partisipan dinyatakan bila relevan"),
    ("Funding", "Sumber pendanaan dinyatakan atau ditulis tidak ada"),
    ("Conflict of interest", "Konflik kepentingan dinyatakan"),
    ("Data availability", "Pernyataan ketersediaan data disiapkan"),
    ("Author contributions", "Kontribusi penulis disiapkan bila diminta"),
    ("References", "Sitasi dan daftar pustaka diperiksa konsistensinya"),
    ("Figures and tables", "Nomor, judul, catatan, dan kualitas gambar diperiksa"),
    ("Reporting guideline", "Pedoman pelaporan sesuai desain penelitian diperiksa"),
]

def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", str(text or ""), flags=re.UNICODE))

def build_submission_checklist(journal_name: str, requirements: dict | None = None) -> pd.DataFrame:
    requirements = requirements or {}
    rows=[]
    for name, default in DEFAULT_CHECKS:
        rows.append({"journal": journal_name.strip() or "[Jurnal sasaran belum diisi]",
                     "item": name, "requirement": str(requirements.get(name, default)),
                     "status": "Belum diperiksa", "evidence_or_notes": ""})
    for name, requirement in requirements.items():
        if name not in {x[0] for x in DEFAULT_CHECKS}:
            rows.append({"journal": journal_name.strip() or "[Jurnal sasaran belum diisi]",
                         "item": name, "requirement": str(requirement),
                         "status": "Belum diperiksa", "evidence_or_notes": ""})
    return pd.DataFrame(rows)

def validate_user_requirements(manuscript: str, abstract: str, keywords: list[str],
                               abstract_limit: int | None = None,
                               manuscript_word_limit: int | None = None,
                               keyword_min: int | None = None,
                               keyword_max: int | None = None) -> pd.DataFrame:
    checks=[]
    aw=word_count(abstract); mw=word_count(manuscript); kw=len([x for x in keywords if str(x).strip()])
    def add(item, actual, expected, ok):
        checks.append({"item":item,"actual":actual,"requirement":expected,
                       "status":"Memenuhi batas yang dimasukkan" if ok else "Perlu diperiksa"})
    if abstract_limit is not None: add("Panjang abstrak",aw,f"maksimal {abstract_limit} kata",aw<=abstract_limit)
    if manuscript_word_limit is not None: add("Panjang manuskrip",mw,f"maksimal {manuscript_word_limit} kata",mw<=manuscript_word_limit)
    if keyword_min is not None or keyword_max is not None:
        lo=keyword_min if keyword_min is not None else 0
        hi=keyword_max if keyword_max is not None else float("inf")
        add("Jumlah kata kunci",kw,f"{lo}–{hi} kata kunci",lo<=kw<=hi)
    return pd.DataFrame(checks)

def declaration_template() -> str:
    return """AUTHOR DECLARATIONS — DRAFT ONLY\n\nEthics approval: [Insert committee name, approval number/date, or justified exemption.]\nInformed consent: [Describe consent procedure, or state why it was not applicable.]\nFunding: [Insert funder and grant number, or 'The authors received no external funding.']\nConflict of interest: [Declare any competing interests, or state none.]\nData availability: [State repository/link/access conditions, or explain restrictions.]\nAuthor contributions: [Insert contributions using the journal's required taxonomy.]\nAcknowledgements: [Insert acknowledgements, if any.]\n\nComplete and verify every statement before submission. Do not retain a statement that is inaccurate."""
