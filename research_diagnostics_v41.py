"""Transparent quantitative and qualitative diagnostics for Research Analyzer v4.1.
These routines provide screening diagnostics, not automatic methodological decisions.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def _numeric_complete(df, columns, min_rows=5):
    missing=[c for c in columns if c not in df.columns]
    if missing: raise ValueError('Kolom tidak ditemukan: '+', '.join(missing))
    x=df[columns].apply(pd.to_numeric,errors='coerce').dropna()
    if len(x)<min_rows: raise ValueError(f'Diperlukan minimal {min_rows} kasus lengkap; tersedia {len(x)}.')
    if x.shape[1]<2: raise ValueError('Minimal dua indikator diperlukan.')
    if (x.std(ddof=1)==0).any(): raise ValueError('Indikator dengan varians nol ditemukan.')
    return x


def reliability_diagnostics(df, items):
    x=_numeric_complete(df,items,min_rows=3)
    k=x.shape[1]
    total=x.sum(axis=1).var(ddof=1)
    if not np.isfinite(total) or total<=0: raise ValueError('Varians skor total tidak memadai.')
    alpha=k/(k-1)*(1-x.var(ddof=1).sum()/total)
    rows=[]
    for item in items:
        rest=x.drop(columns=item)
        corr=x[item].corr(rest.sum(axis=1)) if rest.shape[1] else np.nan
        if rest.shape[1]>=2:
            tv=rest.sum(axis=1).var(ddof=1)
            a=(rest.shape[1]/(rest.shape[1]-1))*(1-rest.var(ddof=1).sum()/tv) if tv>0 else np.nan
        else: a=np.nan
        rows.append({'item':item,'corrected_item_total_correlation':corr,'alpha_if_deleted':a})
    return {'n':len(x),'k':k,'cronbach_alpha':float(alpha),'items':pd.DataFrame(rows)}


def factorability_diagnostics(df, items):
    """KMO and Bartlett sphericity screening from a complete-case correlation matrix."""
    x=_numeric_complete(df,items,min_rows=5)
    n,p=x.shape
    if n<=p: note='Jumlah kasus tidak melebihi jumlah indikator; interpretasikan sangat hati-hati.'
    else: note='Kecukupan sampel tetap perlu dinilai dengan pertimbangan substantif.'
    corr=x.corr().to_numpy()
    try: inv=np.linalg.inv(corr)
    except np.linalg.LinAlgError as e: raise ValueError('Matriks korelasi singular; periksa indikator multikolinear/duplikat.') from e
    r2=corr**2; np.fill_diagonal(r2,0)
    partial=-inv/np.sqrt(np.outer(np.diag(inv),np.diag(inv)))
    p2=partial**2; np.fill_diagonal(p2,0)
    denom=r2.sum()+p2.sum()
    kmo=float(r2.sum()/denom) if denom else np.nan
    sign,logdet=np.linalg.slogdet(corr)
    if sign<=0: raise ValueError('Determinan matriks korelasi tidak positif; Bartlett tidak dapat dihitung.')
    chi=-(n-1-(2*p+5)/6)*logdet
    dof=p*(p-1)//2
    bartlett_p=float(stats.chi2.sf(chi,dof))
    return {'n':n,'items':p,'kmo':kmo,'bartlett_chi_square':float(chi),'bartlett_df':dof,'bartlett_p':bartlett_p,'note':note}


def qualitative_evidence_audit(segments, coding):
    """Evidence traceability audit; uncoded cases are review flags, not negative cases by default."""
    if segments is None or segments.empty: raise ValueError('Data segmen/transkrip masih kosong.')
    if coding is None: coding=pd.DataFrame()
    if 'segment_id' not in segments: raise ValueError('Data segmen memerlukan kolom segment_id atau id.')
    seg=segments.copy()
    if 'text' not in seg: seg['text']=''
    seg['segment_id']=seg.segment_id.astype(str)
    c=coding.copy()
    if not c.empty and 'segment_id' not in c: raise ValueError('Data coding memerlukan kolom segment_id.')
    if not c.empty: c['segment_id']=c.segment_id.astype(str)
    coded=set(c.segment_id) if not c.empty else set()
    uncoded=seg.loc[~seg.segment_id.isin(coded)].copy()
    summary={'segments_total':len(seg),'segments_coded':len(seg)-len(uncoded),'segments_uncoded':len(uncoded),
             'coverage_pct':round(100*(len(seg)-len(uncoded))/len(seg),2) if len(seg) else 0,
             'coding_rows':len(c),'orphan_coding_ids':sorted(set(c.segment_id)-set(seg.segment_id)) if not c.empty else []}
    if not c.empty:
        summary['unique_codes']=int(c.code.nunique()) if 'code' in c else 0
        summary['unique_themes']=int(c.theme.nunique()) if 'theme' in c else 0
    return {'summary':summary,'uncoded_segments':uncoded,'code_frequency':c.code.value_counts().rename_axis('code').reset_index(name='frequency') if 'code' in c else pd.DataFrame(columns=['code','frequency'])}
