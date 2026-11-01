from __future__ import annotations
import re
import pandas as pd

_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_.]*$')
def _name(value, label='nama'):
    value=str(value).strip()
    if not _NAME.fullmatch(value):
        raise ValueError(f'{label} {value!r} tidak valid. Gunakan huruf, angka, titik, atau garis bawah; karakter pertama harus huruf.')
    return value

def build_cfa_syntax(measurement_map, correlated_errors=None):
    """Create first-order CFA lavaan syntax from {factor: [indicators]} mapping."""
    if not measurement_map: raise ValueError('Peta konstruk CFA kosong.')
    lines=[]; used=[]
    for factor, indicators in measurement_map.items():
        f=_name(factor,'Konstruk')
        if not isinstance(indicators,(list,tuple)) or len(indicators)<2: raise ValueError(f'{f}: minimal dua indikator.')
        items=[_name(x,'Indikator') for x in indicators]
        if len(set(items)) != len(items): raise ValueError(f'{f}: indikator duplikat.')
        lines.append(f"{f} =~ "+' + '.join(items)); used.extend(items)
    if len(set(used)) != len(used): raise ValueError('Satu indikator tercantum pada lebih dari satu konstruk.')
    for pair in correlated_errors or []:
        if len(pair)!=2: raise ValueError('Korelasi error harus berupa pasangan dua indikator.')
        a,b=map(lambda x:_name(x,'Indikator error'),pair)
        if a not in used or b not in used or a==b: raise ValueError('Pasangan korelasi error harus menunjuk dua indikator berbeda yang ada di model.')
        lines.append(f'{a} ~~ {b}')
    return '\n'.join(lines)

def build_hoc_syntax(measurement_map, hoc_map, structural_paths=None):
    """Build lavaan syntax for hierarchical (second-order) reflective constructs."""
    if not hoc_map: raise ValueError('Peta HOC kosong.')
    base=build_cfa_syntax(measurement_map)
    lines=[base]
    lower=set(measurement_map)
    for higher, dimensions in hoc_map.items():
        h=_name(higher,'Konstruk tingkat tinggi')
        if not isinstance(dimensions,(list,tuple)) or len(dimensions)<2: raise ValueError(f'{h}: HOC memerlukan minimal dua dimensi tingkat pertama.')
        ds=[_name(x,'Dimensi') for x in dimensions]
        if len(set(ds))!=len(ds) or set(ds)-lower: raise ValueError(f'{h}: dimensi harus unik dan sudah didefinisikan pada peta pengukuran.')
        lines.append(f'{h} =~ '+' + '.join(ds))
    for outcome,preds in (structural_paths or {}).items():
        y=_name(outcome,'Outcome'); xs=[_name(x,'Prediktor') for x in preds]
        if xs: lines.append(f'{y} ~ '+' + '.join(xs))
    return '\n'.join(lines)

def validate_lavaan_syntax(syntax, data_columns=None):
    if not isinstance(syntax,str) or not syntax.strip(): raise ValueError('Sintaks kosong.')
    allowed={'=~','~','~~','~1','|'}
    issues=[]; variables=set()
    for n,line in enumerate(syntax.splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'): continue
        op=next((o for o in ('=~','~~','~1','~','|') if o in line),None)
        if not op: issues.append(f'Baris {n}: operator lavaan tidak dikenali.'); continue
        left,right=line.split(op,1)
        if not left.strip() or not right.strip(): issues.append(f'Baris {n}: sisi kiri/kanan kosong.'); continue
        tokens=[left.strip()]+[x.strip() for x in re.split(r'\+|\*|,',right) if x.strip()]
        for token in tokens:
            token=re.sub(r'^[-+]?(?:\d*\.)?\d+\s*\*\s*','',token)
            if token in {'1','NA','start','std.lv'}: continue
            if _NAME.fullmatch(token): variables.add(token)
    if data_columns is not None:
        missing=sorted(v for v in variables if v not in set(map(str,data_columns)) and not any(v in line.split('=')[0].split('~')[0].strip() for line in syntax.splitlines()))
        if missing: issues.append('Nama variabel tidak ditemukan pada data: '+', '.join(missing))
    return {'valid_syntax_structure':not issues,'issues':issues,'tokens':sorted(variables)}

def interpret_lavaan_parameters(parameters, alpha=.05):
    """Create cautious, rule-based interpretations from lavaan parameterEstimates output."""
    required={'lhs','op','rhs'}
    if not required.issubset(parameters.columns): raise ValueError('Output parameter lavaan minimal memerlukan kolom lhs, op, rhs.')
    d=parameters.copy(); rows=[]
    for _,r in d.iterrows():
        op=str(r['op']); est=pd.to_numeric(pd.Series([r.get('est')]),errors='coerce').iloc[0]
        p=pd.to_numeric(pd.Series([r.get('pvalue')]),errors='coerce').iloc[0]
        std=pd.to_numeric(pd.Series([r.get('std.all')]),errors='coerce').iloc[0]
        if op=='~': kind='Pengaruh struktural terestimasi'; direction='positif' if pd.notna(est) and est>0 else ('negatif' if pd.notna(est) and est<0 else 'nol/tidak tersedia')
        elif op=='=~': kind='Loading faktor'; direction='positif' if pd.notna(est) and est>0 else ('negatif' if pd.notna(est) and est<0 else 'nol/tidak tersedia')
        else: kind='Parameter lain'; direction='—'
        sig=bool(pd.notna(p) and p<alpha)
        if op in ('~','=~'):
            desc=f"{kind}: {r['lhs']} {op} {r['rhs']}; estimasi {est:.3f}" if pd.notna(est) else f"{kind}: {r['lhs']} {op} {r['rhs']}"
            if pd.notna(std): desc+=f", standardized={std:.3f}"
            desc+=f"; arah {direction}; "+('p di bawah ambang yang dipilih' if sig else 'belum memenuhi ambang signifikansi yang dipilih' if pd.notna(p) else 'p-value tidak tersedia')+'.'
        else: desc='Parameter non-jalur; interpretasikan sesuai jenis parameter.'
        rows.append({'lhs':r['lhs'],'op':op,'rhs':r['rhs'],'estimate':est,'std_all':std,'pvalue':p,'significant_at_alpha':sig if pd.notna(p) else None,'interpretation':desc})
    return pd.DataFrame(rows)

def lavaan_path_dot(parameters, standardized=True):
    """Return Graphviz DOT for regression paths and factor loadings."""
    if not {'lhs','op','rhs'}.issubset(parameters.columns): raise ValueError('Parameter memerlukan kolom lhs, op, rhs.')
    def q(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
    out=['digraph SEM {','rankdir=LR;','graph [fontname="Arial"];','node [fontname="Arial", style=filled, fillcolor="#F4F6F8"];','edge [fontname="Arial"];']
    for _,r in parameters.iterrows():
        op=str(r['op'])
        if op not in ('~','=~'): continue
        lhs=str(r['lhs']); rhs=str(r['rhs'])
        val=r.get('std.all') if standardized and 'std.all' in parameters.columns else r.get('est')
        try: label=f'{float(val):.2f}'
        except (TypeError,ValueError): label=''
        if op=='~': src,dst=rhs,lhs
        else: src,dst=lhs,rhs
        out.append(f'{q(src)} -> {q(dst)} [label={q(label)}];')
    out.append('}')
    return '\n'.join(out)

def build_cbsem_results_summary(fit_indices, parameters, alpha=.05):
    fit=dict(zip(fit_indices['index'],fit_indices['value'])) if isinstance(fit_indices,pd.DataFrame) and {'index','value'}.issubset(fit_indices.columns) else dict(fit_indices)
    audit=[]
    for k,v in fit.items():
        try: val=float(v)
        except (TypeError,ValueError): continue
        audit.append(f'{k.upper()} = {val:.3f}')
    interp=interpret_lavaan_parameters(parameters,alpha)
    paths=interp[interp['op']=='~']
    sig=int(paths['significant_at_alpha'].fillna(False).sum()) if len(paths) else 0
    return {'fit_text':'; '.join(audit) if audit else 'Indeks fit tidak tersedia.','structural_paths':len(paths),'significant_paths':sig,'alpha':alpha,'interpretations':interp}
