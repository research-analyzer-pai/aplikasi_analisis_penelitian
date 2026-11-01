
"""v3.0 evidence workspace: literature matrix, instrument blueprint, and auditable text coding."""
import re
import pandas as pd

LITERATURE_COLUMNS=["title","authors","year","journal","aim","theory","method","sample_context","key_findings","limitations","theme","doi_url"]
INSTRUMENT_COLUMNS=["construct","dimension","indicator","item_code","item_statement","response_scale","reverse_coded","source_theory","source_reference"]
CODE_COLUMNS=["segment_id","text","suggested_code","matched_terms","researcher_decision","memo"]

def literature_template():
    return pd.DataFrame(columns=LITERATURE_COLUMNS)

def instrument_template():
    return pd.DataFrame(columns=INSTRUMENT_COLUMNS)

def validate_literature(df):
    missing=[c for c in ["title","authors","year","key_findings","theme"] if c not in df.columns]
    if missing: raise ValueError("Kolom wajib belum ada: "+", ".join(missing))
    d=df.copy()
    d["year_num"]=pd.to_numeric(d["year"],errors="coerce")
    issues=[]
    if d["title"].fillna("").astype(str).str.strip().eq("").any():
        issues.append("Ada artikel tanpa judul.")
    if d["year_num"].isna().any(): issues.append("Ada tahun publikasi kosong atau bukan angka.")
    dup=d["title"].fillna("").astype(str).str.strip().str.lower().duplicated()
    if dup.any(): issues.append(f"Ada {int(dup.sum())} judul duplikat.")
    if d["doi_url"].fillna("").astype(str).str.strip().eq("").any():
        issues.append("Sebagian entri belum memiliki DOI/URL; verifikasi metadata sebelum sitasi.")
    return d,issues

def literature_summary(df):
    if df is None or df.empty: return {"count":0,"year_range":"-","themes":pd.DataFrame(),"gaps":[]}
    d,issues=validate_literature(df)
    yrs=d.year_num.dropna()
    theme_col=d.theme.fillna("Belum dikategorikan").astype(str).str.strip()
    themes=theme_col.value_counts().rename_axis("theme").reset_index(name="article_count")
    gaps=[]
    for col,label in [("theory","teori"),("method","metode"),("limitations","keterbatasan"),("doi_url","DOI/URL")]:
        if col in d:
            n=int(d[col].fillna("").astype(str).str.strip().eq("").sum())
            if n: gaps.append(f"{n} entri belum mencantumkan {label}.")
    if issues: gaps.extend(issues)
    return {"count":len(d),"year_range":f"{int(yrs.min())}–{int(yrs.max())}" if len(yrs) else "-",
            "themes":themes,"gaps":gaps}

def build_instrument(mapping, scale="Likert 1–5"):
    required=["construct","dimension","indicator"]
    if any(c not in mapping.columns for c in required):
        raise ValueError("Pemetaan harus memiliki construct, dimension, dan indicator.")
    rows=[]
    for idx,r in mapping.reset_index(drop=True).iterrows():
        construct=str(r["construct"]).strip()
        dim=str(r["dimension"]).strip()
        ind=str(r["indicator"]).strip()
        if not (construct and dim and ind): continue
        # A neutral, editable first-person draft; researcher must contextualize and validate.
        statement=f"Saya menunjukkan perilaku yang mencerminkan {ind} dalam konteks {dim}."
        rows.append({"construct":construct,"dimension":dim,"indicator":ind,
                     "item_code":f"{re.sub('[^A-Za-z0-9]','',construct)[:5].upper()}_{idx+1:02d}",
                     "item_statement":statement,"response_scale":scale,"reverse_coded":"Tidak",
                     "source_theory":r.get("theory",""),"source_reference":r.get("source","")})
    return pd.DataFrame(rows,columns=INSTRUMENT_COLUMNS)

def keyword_code_suggestions(segments, dictionary):
    """Dictionary-assisted suggestions; never represents an autonomous AI interpretation."""
    rows=[]
    for idx,txt in enumerate(segments):
        text=str(txt)
        low=text.lower()
        matched=[]
        for code,terms in dictionary.items():
            hits=[t for t in terms if str(t).lower() in low]
            if hits: matched.append((code,hits))
        if matched:
            for code,hits in matched:
                rows.append({"segment_id":idx+1,"text":text,"suggested_code":code,
                             "matched_terms":", ".join(hits),"researcher_decision":"Belum ditinjau","memo":""})
        else:
            rows.append({"segment_id":idx+1,"text":text,"suggested_code":"Tidak ada kecocokan",
                         "matched_terms":"","researcher_decision":"Perlu coding manual","memo":""})
    return pd.DataFrame(rows,columns=CODE_COLUMNS)

def theme_synthesis(df):
    """Evidence-indexed outline from supplied literature; no unsupported claims are generated."""
    if df is None or df.empty: return "Belum ada artikel yang dimasukkan."
    out=[]
    for theme,g in df.groupby(df.theme.fillna("Belum dikategorikan").astype(str)):
        out.append(f"TEMA: {theme} ({len(g)} artikel)")
        for _,r in g.iterrows():
            out.append(f"- {r.get('authors','')} ({r.get('year','')}), {r.get('title','')}: "
                       f"Temuan: {r.get('key_findings','')}. Keterbatasan: {r.get('limitations','')}. "
                       f"Teori: {r.get('theory','')}.")
        out.append("Sintesis peneliti: [Bandingkan kesamaan/perbedaan hasil, konteks, teori, metode, dan kualitas bukti.]")
        out.append("Celah riset: [Rumuskan hanya setelah membaca artikel penuh dan memeriksa keterbatasan secara kritis.]")
    return "\n".join(out)
