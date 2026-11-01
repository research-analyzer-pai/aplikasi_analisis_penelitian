
"""v3.2 literature discovery, qualitative audit tools, and manuscript scaffolding."""
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from collections import Counter

CROSSREF_URL="https://api.crossref.org/works"

def crossref_search(query, rows=10, timeout=20):
    """Search Crossref public metadata API. Results are candidates, not quality endorsements."""
    if not str(query).strip():
        raise ValueError("Masukkan kata kunci atau judul artikel.")
    rows=max(1,min(int(rows),50))
    params=urllib.parse.urlencode({"query.bibliographic":query.strip(),"rows":rows,
                                   "select":"DOI,title,author,published,container-title,URL,type,publisher"})
    req=urllib.request.Request(CROSSREF_URL+"?"+params,
        headers={"User-Agent":"ResearchAnalyzerProfessional/3.2 (academic-research-assistant)"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            data=json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8",errors="replace")[:1000]
        raise RuntimeError(f"Crossref HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Tidak dapat mengakses Crossref: {e.reason}") from e
    items=data.get("message",{}).get("items",[])
    results=[]
    for x in items:
        authors=[]
        for a in x.get("author",[]) or []:
            name=" ".join(v for v in [a.get("given",""),a.get("family","")] if v).strip()
            if name: authors.append(name)
        date=x.get("published",{}).get("date-parts",[[]])[0]
        year=date[0] if date else ""
        title=(x.get("title") or [""])[0]
        results.append({
            "title":title,"authors":"; ".join(authors),"year":year,
            "journal":(x.get("container-title") or [""])[0],
            "doi":x.get("DOI",""),"url":x.get("URL",""),
            "publisher":x.get("publisher",""),"type":x.get("type","")
        })
    return results

def to_literature_matrix(results):
    """Convert Crossref candidates to v3.0 literature matrix columns."""
    rows=[]
    for r in results:
        rows.append({
            "title":r.get("title",""),"authors":r.get("authors",""),"year":r.get("year",""),
            "journal":r.get("journal",""),"aim":"","theory":"","method":"",
            "sample_context":"","key_findings":"","limitations":"","theme":"",
            "doi_url":("https://doi.org/"+r["doi"]) if r.get("doi") else r.get("url","")
        })
    return rows

def build_codebook_template():
    return [
        {"code":"CODE_01","definition":"","inclusion_criteria":"","exclusion_criteria":"",
         "example_quote":"","theme":"","source_or_theory":"","version":"1.0","review_status":"Draft"}
    ]

def segment_audit_rows(segments, coding):
    """Join segment and researcher-approved coding records using segment_id."""
    if segments is None or segments.empty: return []
    rows=[]
    for _,seg in segments.iterrows():
        sid=seg.get("id",seg.get("segment_id",""))
        matched=coding[coding["segment_id"].astype(str)==str(sid)] if coding is not None and not coding.empty and "segment_id" in coding else None
        codes="; ".join(matched["code"].astype(str).tolist()) if matched is not None and not matched.empty and "code" in matched else ""
        rows.append({"segment_id":sid,"source":seg.get("source",""),"participant":seg.get("participant",""),
                     "text":seg.get("text",""),"approved_codes":codes})
    return rows

def code_frequency(coding):
    if coding is None or coding.empty or "code" not in coding:
        return []
    counts=Counter(str(x).strip() for x in coding["code"].dropna() if str(x).strip())
    return [{"code":k,"count":v} for k,v in counts.most_common()]

def cohens_kappa(rater_a, rater_b):
    """Cohen's kappa for two coders' nominal labels on aligned units."""
    if len(rater_a)!=len(rater_b): raise ValueError("Jumlah penilaian kedua coder harus sama.")
    if not rater_a: raise ValueError("Data penilaian kosong.")
    labels=sorted(set(rater_a)|set(rater_b))
    n=len(rater_a)
    po=sum(a==b for a,b in zip(rater_a,rater_b))/n
    pa={k:sum(x==k for x in rater_a)/n for k in labels}
    pb={k:sum(x==k for x in rater_b)/n for k in labels}
    pe=sum(pa[k]*pb[k] for k in labels)
    if pe==1: return 1.0 if po==1 else 0.0
    return (po-pe)/(1-pe)

def manuscript_outline(title, design, findings, theory="", literature="", method="", limitations=""):
    """Evidence-first manuscript skeleton; does not write unsupported claims."""
    return f"""# {title}

## Abstract
[Write purpose, design, setting/sample, main verified results, and contribution. Do not insert unreported statistics.]

## 1. Introduction
[Establish the problem using the supplied literature. State the research gap only after checking the scope and quality of the literature.]
Theoretical framing supplied by researcher: {theory or '[NOT PROVIDED]'}
Literature evidence supplied: {literature or '[NOT PROVIDED]'}

## 2. Method
Research design and procedures supplied: {method or '[NOT PROVIDED]'}
[Report setting, participants/sampling, instruments, data collection, analysis, ethics, and trustworthiness/validity procedures.]

## 3. Results
Verified findings supplied by researcher:
{findings or '[NOT PROVIDED]'}

## 4. Discussion
[Interpret each finding; compare with supplied literature; explain agreements, contradictions, and plausible mechanisms. Add citations only after source verification.]

## 5. Conclusion and Implications
[Answer research questions; state theoretical, practical, and policy implications proportionately.]

## 6. Limitations and Future Research
{limitations or '[NOT PROVIDED]'}

## References
[Insert only references verified against original publications and required journal style.]
"""
