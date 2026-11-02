"""Automatic AI article drafting with OpenAlex literature discovery."""
from __future__ import annotations
import json, re, urllib.parse, urllib.request, urllib.error
import pandas as pd
from io import StringIO

OPENALEX_URL="https://api.openalex.org/works"

def _decode_abstract(inv):
    if not isinstance(inv,dict): return ""
    positions=[]
    for word, indexes in inv.items():
        for pos in indexes:
            positions.append((pos,word))
    return " ".join(w for _,w in sorted(positions))

def search_openalex_literature(query: str, limit: int=10, from_year: int=2020):
    if not query.strip(): raise ValueError("Topik literatur belum diisi.")
    params={"search":query,"filter":f"from_publication_date:{from_year}-01-01,type:article","per-page":min(max(int(limit),5),20),
            "sort":"relevance_score:desc","select":"id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,cited_by_count,type"}
    url=OPENALEX_URL+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"ResearchAnalyzerProfessional/6.0 (academic article writing)"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: data=json.loads(r.read().decode("utf-8"))
    except Exception as e: raise RuntimeError(f"Pencarian literatur OpenAlex gagal: {e}") from e
    records=[]
    for w in data.get("results",[]):
        title=w.get("title") or ""
        authors=[]
        for a in (w.get("authorships") or [])[:8]:
            au=(a.get("author") or {}).get("display_name")
            if au: authors.append(au)
        venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        doi=w.get("doi") or ""
        year=w.get("publication_year")
        abstract=_decode_abstract(w.get("abstract_inverted_index"))
        records.append({"title":title,"authors":authors,"year":year,"venue":venue,"doi":doi,
                        "cited_by":w.get("cited_by_count",0),"abstract":abstract,"openalex_id":w.get("id","")})
    return records

def apa_from_openalex(item):
    authors=item.get("authors") or []
    def apa_name(name):
        parts=name.split()
        if not parts: return name
        surname=parts[-1]
        initials=" ".join(p[0]+"." for p in parts[:-1] if p)
        return f"{surname}, {initials}".strip(", ")
    if len(authors)>20:
        author_txt=", ".join(apa_name(x) for x in authors[:19])+", … "+apa_name(authors[-1])
    elif len(authors)>1:
        author_txt=", ".join(apa_name(x) for x in authors[:-1])+", & "+apa_name(authors[-1])
    elif authors: author_txt=apa_name(authors[0])
    else: author_txt="Author not indexed"
    year=item.get("year") or "n.d."
    ref=f"{author_txt} ({year}). {item.get('title','')}. *{item.get('venue','')}*."
    if item.get("doi"): ref+=" "+item["doi"]
    return ref

def generate_full_article(api_key, model, metadata, findings, literature, word_limit=8000, timeout=240):
    from ai_research_engine import call_responses_api
    lit=[]
    for i,x in enumerate(literature,1):
        lit.append(f"[L{i}] {x.get('title')} | Authors: {', '.join(x.get('authors',[]))} | Year: {x.get('year')} | Venue: {x.get('venue')} | DOI: {x.get('doi')} | Citations indexed: {x.get('cited_by')}\nAbstract: {x.get('abstract','')[:2500]}")
    instruction = f"""
You are a senior academic researcher and journal editor. Draft a rigorous, submission-oriented international journal article in polished academic English unless the requested language says otherwise. Maximum {word_limit} words excluding references. Use this exact structure:
Title; Author(s) and affiliation; Abstract (150-250 words); Keywords (4-6);
1. Introduction; 2. Literature Review (with coherent thematic subheadings, theory, empirical synthesis, research gap and conceptual argument); 3. Research Method; 4. Results; 5. Discussion; 6. Conclusion; References (APA 7).
ACADEMIC INTEGRITY RULES:
- Do not invent data, sample sizes, field sites, quotations, statistics, p-values, effects, themes, ethical approvals, findings, citations, DOI, or bibliographic metadata.
- Use only actual findings in the supplied findings/project data. If evidence is absent, insert explicit [AUTHOR INPUT REQUIRED: ...] placeholders, and explain no results can be inferred. Never fabricate Results.
- Literature claims must be supported by supplied indexed literature. Cite author-year only when author/year metadata exists. Do not claim to have read full texts: abstracts/metadata only were supplied. Distinguish abstract-level evidence and mark synthesis cautiously.
- References list must contain only supplied literature records that are actually cited. APA 7 format. DOI only as supplied. If no literature supports a claim, mark [SOURCE REQUIRED].
- Clearly separate established theory, empirical evidence, and author interpretation. Do not falsely claim journal acceptance or guarantee publication.
- Provide a critical literature review, not a list of summaries. Explain conceptual relationships, agreements, disagreements, methodological patterns, contextual gaps, and why this study matters.
- Methods must accurately reflect the user's stated design and procedures. Identify missing method details with placeholders.
- Discussion must interpret only supplied results, compare cautiously with supplied studies, include alternative explanations and limitations.
- If quantitative data summary is supplied, describe it accurately and do not infer significance or causality without the relevant test outputs.
- If qualitative evidence is supplied, use short anonymised excerpts only if explicitly included; do not invent quotations.
- Mixed methods must state the integration design and show where/why strands are integrated; do not claim integration if only one strand is present.
- Use tables/figure callout suggestions in the body where warranted, e.g. [Insert Table 1 here: ...], [Insert Figure 1 here: ...]. Do not create imaginary values. Provide a concise list of recommended tables/figures at end if no values.
- Article should be coherent, precise, critical, methodologically transparent, and aimed at a reputable international peer-reviewed journal. Avoid promotional language and generic claims.
"""
    prompt = {
      "ARTICLE METADATA": metadata,
      "ACTUAL FINDINGS AND PROJECT DATA": findings,
      "LITERATURE RECORDS (OpenAlex metadata and abstracts; not full-text articles)": lit,
      "OUTPUT REQUIREMENTS": f"Write complete article no longer than {word_limit} words excluding References. Academic English. Include APA 7 references for cited literature. Mark missing inputs rather than invent."
    }
    task_name="Automatic international journal article (IMRaD + Literature Review)"
    # Register a task-specific instruction in the existing API client.
    import ai_research_engine as aire
    aire.TASKS[task_name]=instruction
    user_payload=json.dumps(prompt,ensure_ascii=False,default=str)
    if len(user_payload)>aire.MAX_INPUT_CHARS:
        raise ValueError(f"Ringkasan data dan literatur terlalu panjang ({len(user_payload):,} karakter). Kurangi jumlah sumber atau ringkasan data.")
    return call_responses_api(api_key,user_payload,task_name,model=model,
                              max_output_tokens=12000,timeout=timeout)
