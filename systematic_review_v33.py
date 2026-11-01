
"""Reproducible systematic-review screening and PRISMA-style flow accounting."""
import re
import hashlib
import pandas as pd

COLUMNS=["record_id","title","authors","year","source","doi","url","abstract",
         "duplicate_of","title_abstract_decision","title_abstract_reason",
         "full_text_decision","full_text_reason","reviewer_notes"]

def empty_review_matrix():
    return pd.DataFrame(columns=COLUMNS)

def _record_id(title,doi,authors,year):
    raw="|".join([str(title or ""),str(doi or ""),str(authors or ""),str(year or "")])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()

def parse_ris(text):
    records=[]
    current={}
    for line in text.splitlines():
        line=line.rstrip()
        m=re.match(r"^([A-Z0-9]{2})\s{2}-\s?(.*)$",line)
        if not m: continue
        tag,val=m.groups()
        if tag=="TY" and current:
            records.append(current); current={}
        current.setdefault(tag,[])
        current[tag].append(val.strip())
        if tag=="ER":
            records.append(current); current={}
    if current: records.append(current)
    out=[]
    for r in records:
        def first(*tags):
            for t in tags:
                if r.get(t): return r[t][0]
            return ""
        authors="; ".join(r.get("AU",[]) or r.get("A1",[]))
        title=first("TI","T1")
        doi=first("DO")
        out.append({"title":title,"authors":authors,"year":first("PY","Y1")[:4],
                    "source":first("JO","JF","T2","JA"),"doi":doi,
                    "url":first("UR"),"abstract":first("AB","N2")})
    return out

def parse_bibtex(text):
    """Basic BibTeX importer; handles common fields and brace nesting."""
    entries=[]
    pattern=re.compile(r"@\w+\s*\{\s*([^,]+)\s*,",re.I)
    matches=list(pattern.finditer(text))
    for i,m in enumerate(matches):
        chunk=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        fields={}
        pos=0
        while pos<len(chunk):
            fm=re.search(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*",chunk[pos:])
            if not fm: break
            key=fm.group(1).lower()
            start=pos+fm.end()
            while start<len(chunk) and chunk[start].isspace(): start+=1
            if start>=len(chunk): break
            opener=chunk[start]
            if opener=="{":
                depth=1; j=start+1
                while j<len(chunk) and depth:
                    if chunk[j]=="{": depth+=1
                    elif chunk[j]=="}": depth-=1
                    j+=1
                value=chunk[start+1:j-1]
            elif opener=='"':
                j=start+1
                while j<len(chunk) and chunk[j]!='"': j+=1
                value=chunk[start+1:j]
            else:
                j=start
                while j<len(chunk) and chunk[j] not in ",}\n": j+=1
                value=chunk[start:j]
            fields[key]=re.sub(r"\s+"," ",value).strip()
            pos=max(j,pos+fm.end())
        authors=fields.get("author","").replace(" and ","; ")
        out={"title":fields.get("title",""),"authors":authors,
             "year":fields.get("year","")[:4],"source":fields.get("journal",fields.get("booktitle","")),
             "doi":fields.get("doi",""),"url":fields.get("url",""),
             "abstract":fields.get("abstract","")}
        entries.append(out)
    return entries

def records_to_frame(records):
    rows=[]
    for r in records:
        row={c:"" for c in COLUMNS}
        for key in ["title","authors","year","source","doi","url","abstract"]:
            row[key]=r.get(key,"")
        row["record_id"]=_record_id(row["title"],row["doi"],row["authors"],row["year"])
        row["title_abstract_decision"]="Pending"
        row["full_text_decision"]="Not assessed"
        rows.append(row)
    return pd.DataFrame(rows,columns=COLUMNS)

def mark_duplicates(df):
    if df is None or df.empty: return empty_review_matrix(),0
    d=df.copy()
    d["duplicate_of"]=""
    seen_doi={}
    seen_title={}
    duplicates=0
    for idx,row in d.iterrows():
        doi=str(row.get("doi","")).strip().lower()
        title=re.sub(r"[^a-z0-9]+"," ",str(row.get("title","")).lower()).strip()
        key=None
        if doi and doi in seen_doi: key=seen_doi[doi]
        elif title and title in seen_title: key=seen_title[title]
        if key:
            d.at[idx,"duplicate_of"]=key
            duplicates+=1
        else:
            if doi: seen_doi[doi]=row.get("record_id",str(idx))
            if title: seen_title[title]=row.get("record_id",str(idx))
    return d,duplicates

def prisma_counts(df,not_retrieved=0,fulltext_excluded=0):
    if df is None: df=empty_review_matrix()
    d=df.copy()
    identified=len(d)
    duplicates=int(d.get("duplicate_of",pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum())
    screened=max(0,identified-duplicates)
    valid=d[d.get("duplicate_of",pd.Series([""]*len(d),index=d.index)).fillna("").astype(str).str.strip().eq("")]
    ta=valid.get("title_abstract_decision",pd.Series(["Pending"]*len(valid),index=valid.index)).fillna("Pending")
    ta_excluded=int((ta=="Exclude").sum())
    sought=int((ta=="Include").sum())
    not_retrieved=max(0,min(int(not_retrieved),sought))
    assessed=max(0,sought-not_retrieved)
    fulltext_excluded=max(0,min(int(fulltext_excluded),assessed))
    included=max(0,assessed-fulltext_excluded)
    return {"records_identified":identified,"duplicates_removed":duplicates,
            "records_screened":screened,"records_excluded_title_abstract":ta_excluded,
            "reports_sought":sought,"reports_not_retrieved":not_retrieved,
            "reports_assessed":assessed,"reports_excluded_full_text":fulltext_excluded,
            "studies_included":included}

def prisma_mermaid(counts):
    c=counts
    return f"""flowchart TD
 A[Records identified: {c['records_identified']}] --> B[Duplicates removed: {c['duplicates_removed']}]
 B --> C[Records screened: {c['records_screened']}]
 C --> D[Records excluded at title/abstract: {c['records_excluded_title_abstract']}]
 C --> E[Reports sought for retrieval: {c['reports_sought']}]
 E --> F[Reports not retrieved: {c['reports_not_retrieved']}]
 E --> G[Reports assessed for eligibility: {c['reports_assessed']}]
 G --> H[Full-text reports excluded: {c['reports_excluded_full_text']}]
 G --> I[Studies included: {c['studies_included']}]
"""

def screening_log(df):
    if df is None or df.empty: return pd.DataFrame(columns=["record_id","title","decision","reason","reviewer_notes"])
    d=df.copy()
    return pd.DataFrame({
        "record_id":d.get("record_id",""),"title":d.get("title",""),
        "title_abstract_decision":d.get("title_abstract_decision","Pending"),
        "title_abstract_reason":d.get("title_abstract_reason",""),
        "full_text_decision":d.get("full_text_decision","Not assessed"),
        "full_text_reason":d.get("full_text_reason",""),
        "reviewer_notes":d.get("reviewer_notes","")
    })
