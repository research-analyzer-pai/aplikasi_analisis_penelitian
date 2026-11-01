"""Manuscript and APA consistency utilities for Research Analyzer v3.9.
Rule-based checks only; does not verify source existence, DOI resolution, or journal indexing.
"""
from __future__ import annotations
import re
import pandas as pd

APA_DOI_RE = re.compile(r"^https?://doi\.org/10\.\d{4,9}/\S+$", re.I)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s,;]+", re.I)

def _norm_name(s: str) -> str:
    s=re.sub(r"\s+"," ",str(s).strip())
    s=re.sub(r"[.,]","",s)
    return s.lower()

def parse_reference_entry(entry: str) -> dict:
    raw=str(entry).strip()
    doi_match=DOI_RE.search(raw)
    year_match=re.search(r"\((\d{4}[a-z]?)\)",raw)
    # APA reference surname approximation: text before first comma
    surname=raw.split(",",1)[0].strip() if "," in raw else ""
    title_match=re.search(r"\)\.\s*(.+?)(?:\.\s*(?:[A-Z][A-Za-z &-]+:|https?://|doi:|https://doi\.org/)|$)",raw)
    return {"reference":raw,"first_author":surname,"year":year_match.group(1) if year_match else "",
            "doi":doi_match.group(0).rstrip(".)") if doi_match else "",
            "title_candidate":title_match.group(1).strip() if title_match else ""}

def parse_intext_citations(text: str) -> pd.DataFrame:
    """Extract basic author-year parenthetical citations; narrative citations are approximate."""
    rows=[]
    for match in re.finditer(r"\(([^()]{1,180}\b(?:19|20)\d{2}[a-z]?[^()]*)\)",str(text)):
        inside=match.group(1)
        for part in re.split(r";",inside):
            m=re.search(r"(.+?),?\s*((?:19|20)\d{2}[a-z]?)",part.strip())
            if m:
                author=m.group(1).strip()
                author=re.sub(r"\bet al\.?\b","",author,flags=re.I).strip()
                rows.append({"citation_text":part.strip(),"author_key":_norm_name(author),"year":m.group(2),
                             "position":match.start()})
    # Narrative: e.g. Smith (2021)
    for m in re.finditer(r"\b([A-Z][A-Za-z’' -]{1,50})\s+\(((?:19|20)\d{2}[a-z]?)\)",str(text)):
        rows.append({"citation_text":m.group(0),"author_key":_norm_name(m.group(1)),"year":m.group(2),
                     "position":m.start()})
    return pd.DataFrame(rows,columns=["citation_text","author_key","year","position"])

def audit_apa_consistency(manuscript: str, references: list[str]) -> dict:
    citations=parse_intext_citations(manuscript)
    parsed=[parse_reference_entry(x) for x in references if str(x).strip()]
    ref_df=pd.DataFrame(parsed)
    ref_df["author_key"]=ref_df.first_author.map(_norm_name) if not ref_df.empty else []
    citation_keys=set(zip(citations.author_key,citations.year)) if not citations.empty else set()
    reference_keys=set(zip(ref_df.author_key,ref_df.year)) if not ref_df.empty else set()
    unmatched_citations=sorted(citation_keys-reference_keys)
    uncited_references=sorted(reference_keys-citation_keys)
    duplicate_refs=[]
    seen=set()
    for r in parsed:
        key=(_norm_name(r["first_author"]),r["year"],_norm_name(r["title_candidate"]))
        if key in seen: duplicate_refs.append(r["reference"])
        seen.add(key)
    doi_rows=[]
    for r in parsed:
        if r["doi"] and not APA_DOI_RE.match("https://doi.org/"+r["doi"].removeprefix("https://doi.org/")):
            doi_rows.append(r["reference"])
    return {"citations":citations,"references":ref_df,
      "unmatched_in_text_citations":unmatched_citations,
      "uncited_reference_entries":uncited_references,
      "possible_duplicate_references":duplicate_refs,
      "references_with_doi":sum(bool(r["doi"]) for r in parsed),
      "references_without_doi":sum(not bool(r["doi"]) for r in parsed),
      "doi_format_review":doi_rows,
      "limitations":"Pencocokan nama-tahun bersifat heuristik. Tidak memverifikasi keberadaan sumber, metadata, DOI aktif, kualitas jurnal, atau kepatuhan APA secara menyeluruh."}

def manuscript_readiness(manuscript: str, required_sections=None, abstract_max_words=250,
                         keyword_min=3, keyword_max=6) -> pd.DataFrame:
    text=str(manuscript)
    sections=required_sections or ["Title","Abstract","Keywords","Introduction","Methods",
      "Results","Discussion","Conclusion","References"]
    lines=[]
    for section in sections:
        found=bool(re.search(r"(?im)^\s*"+re.escape(section)+r"\s*$",text))
        lines.append({"requirement":f"Bagian {section}","status":"Ada" if found else "Belum terdeteksi",
                      "note":"Pencarian berdasarkan judul bagian; periksa format dan substansinya."})
    abstract=re.search(r"(?is)^\s*Abstract\s*\n(.*?)(?=^\s*(?:Keywords|Introduction)\s*$)",text)
    abstract_words=len(re.findall(r"\b[\w’'-]+\b",abstract.group(1))) if abstract else 0
    lines.append({"requirement":"Panjang abstrak","status":"Dalam batas" if abstract and abstract_words<=abstract_max_words else "Perlu diperiksa",
                  "note":f"{abstract_words} kata; batas yang dimasukkan pengguna {abstract_max_words}."})
    kw=re.search(r"(?im)^\s*Keywords?\s*:\s*(.+)$",text)
    kw_count=len([x for x in re.split(r"[,;]",kw.group(1)) if x.strip()]) if kw else 0
    lines.append({"requirement":"Jumlah kata kunci","status":"Dalam batas" if keyword_min<=kw_count<=keyword_max else "Perlu diperiksa",
                  "note":f"{kw_count} kata kunci; rentang {keyword_min}–{keyword_max}."})
    return pd.DataFrame(lines)

def build_manuscript_outline(title: str, study_design: str, target_journal_requirements: dict|None=None) -> str:
    req=target_journal_requirements or {}
    sections=req.get("sections",["Title","Abstract","Keywords","Introduction","Methods","Results","Discussion","Conclusion","References"])
    return ("MANUSCRIPT OUTLINE\n\nTitle\n"+(title.strip() or "[Masukkan judul penelitian]")+
      "\n\nStudy design\n"+(study_design.strip() or "[Jelaskan desain dan pendekatan penelitian]")+
      "\n\n"+ "\n\n".join(f"{s}\n[Isi berdasarkan data dan pedoman jurnal]" for s in sections)+
      "\n\nJournal-specific checks\n"+ "\n".join(f"- {k}: {v}" for k,v in req.items() if k!="sections")+
      "\n\nCatatan: outline ini bukan bukti bahwa jurnal menerima naskah atau bahwa naskah memenuhi seluruh kebijakan jurnal.")

def apa_reference_quality_check(references: list[str]) -> pd.DataFrame:
    rows=[]
    for entry in references:
        p=parse_reference_entry(entry)
        checks={
          "year_detected":bool(p["year"]),
          "author_detected":bool(p["first_author"]),
          "doi_detected":bool(p["doi"]),
          "doi_as_url":bool(p["doi"] and "doi.org/" in str(entry).lower()),
          "possible_incomplete_entry":not bool(p["year"] and p["first_author"])
        }
        rows.append({"reference":p["reference"],**checks})
    return pd.DataFrame(rows)
