
import streamlit as st
from qualitative_ai_assistant_v50 import suggest_qualitative_codes, apply_researcher_decisions, codebook_coverage
from mixed_methods_meta_inference_v50 import build_meta_inference_table, integration_completeness, meta_inference_narrative
from academic_report_v50 import build_academic_report_docx

from qualitative_case_engine_v49 import informant_theme_matrix, cross_case_theme_comparison, theme_evidence_profile, qualitative_audit, uncoded_evidence_review, saturation_sequence_audit
from mixed_methods_integration_v48 import build_evidence_linked_joint_display, integration_audit, summarize_integration_by_path, export_integration_narrative
from pls_indicator_predict_v46 import indicator_level_pls_predict
import os
from pathlib import Path
import json
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from docx import Document
import analyzer_core as ac
import pls_engine
import research_intelligence as ri
import research_intelligence_v3 as ri3
import ai_research_engine as aire
import research_intelligence_v32 as ri32
import systematic_review_v33 as sr33
import qualitative_advanced_v34 as qa34
import journal_readiness_v34 as jr34
import qualitative_intelligence_v35 as qi35
import qualitative_intelligence_v36 as qi36
import mixed_methods_v37 as mm37
import research_diagnostics_v41 as rd41
import sem_inference_v42 as si42
import cfa_cbsem_v43 as cfa43
import cbsem_advanced_v44 as cb44

st.set_page_config(page_title="Research Analyzer Professional Web v6.0", page_icon="🔬", layout="wide")
# Optional shared-password gate for a small private deployment.
# Set RA_WEB_PASSWORD in the hosting environment; do not hard-code credentials.
_web_password = os.environ.get("RA_WEB_PASSWORD", "")
if _web_password:
    if not st.session_state.get("_ra_authenticated", False):
        st.title("Research Analyzer Professional")
        _candidate = st.text_input("Kata sandi akses", type="password")
        if st.button("Masuk"):
            if _candidate == _web_password:
                st.session_state["_ra_authenticated"] = True
                st.rerun()
            else:
                st.error("Kata sandi tidak sesuai.")
        st.stop()

st.title("Research Analyzer Professional Web v6.0")
st.caption("Integrated Research Workspace • Quantitative • Qualitative • Mixed Methods • Academic Writing")
st.caption("Statistical Analysis • Qualitative Intelligence • Mixed Methods • Crossref • Publication Readiness • Advanced Diagnostics")
st.info("v2.7 menambahkan analisis mediasi dan moderasi berbasis skor konstruk terestimasi. Baca catatan metodologis: fitur ini merupakan analisis OLS/bootstrap eksploratif, bukan bukti kausal otomatis.")

def init(k,v):
    if k not in st.session_state: st.session_state[k]=v
init("data",pd.DataFrame())
init("segments",pd.DataFrame(columns=["id","source","participant","text"]))
init("codes",pd.DataFrame(columns=["segment_id","code","category","theme","memo","evidence_type"]))
init("sem",pd.DataFrame())
init("joint",[])

with st.sidebar:
    project=st.text_input("Judul penelitian","Penelitian Pendidikan Islam")
    researcher=st.text_input("Peneliti","")
    design=st.selectbox("Desain",["Kuantitatif","Kualitatif","Mixed methods sequential explanatory",
        "Mixed methods sequential exploratory","Mixed methods convergent","Studi kasus","Lainnya"])
    alpha=st.number_input("Ambang signifikansi",0.001,0.20,0.05,0.005)

tabs=st.tabs(["Dashboard","Data","Reliabilitas","Uji Statistik","Regresi OLS","Kualitatif","PLS-SEM Prototype","SEM-PLS Import","Mixed Methods","Research Intelligence","Literature & Instrument","AI Research Studio","Research Intelligence 3.2","Systematic Review & PRISMA","Advanced Qualitative","Journal Readiness","Laporan","AI Qualitative & Joint Display v3.5","SEM Results Validation v3.7","Evidence-linked Joint Display v3.7","Crossref Metadata Intelligence v4.0","Journal Submission Assistant v4.0","Advanced Research Diagnostics v4.1","SEM Inference & Diagnostics v4.2","CFA & CB-SEM Engine v4.3","Advanced CB-SEM & HOC v4.4","Workspace & Project","Developer Studio"])
with tabs[0]:
    a,b,c,d=st.columns(4)
    a.metric("Responden",len(st.session_state.data))
    b.metric("Unit kualitatif",len(st.session_state.segments))
    c.metric("Coding",len(st.session_state.codes))
    d.metric("Jalur SEM impor",len(st.session_state.sem))
    st.markdown("**Alur:** impor data → validasi → analisis → interpretasi → integrasi → pelaporan.")
    st.info("Gunakan data anonim. Pastikan prosedur etik dan perlindungan data dipenuhi.")
with tabs[1]:
    f=st.file_uploader("Unggah data responden CSV",type="csv",key="datafile")
    if f:
        try:
            st.session_state.data=pd.read_csv(f)
            st.success(f"Berhasil memuat {len(st.session_state.data)} baris.")
        except Exception as e: st.error(str(e))
    df=st.session_state.data
    if not df.empty:
        st.dataframe(df.head(100),use_container_width=True)
        profile=pd.DataFrame({"tipe":df.dtypes.astype(str),"missing":df.isna().sum(),
                              "missing_%":(df.isna().mean()*100).round(2),"unik":df.nunique()})
        st.dataframe(profile,use_container_width=True)
        st.download_button("Unduh profil data",profile.to_csv().encode("utf-8-sig"),"data_profile.csv")
with tabs[2]:
    df=st.session_state.data
    if df.empty: st.info("Impor data pada tab Data.")
    else:
        cols=df.select_dtypes(include=np.number).columns.tolist()
        items=st.multiselect("Pilih item dalam satu konstruk",cols)
        reverse=st.multiselect("Item reverse (opsional)",items)
        if st.button("Hitung Cronbach's alpha"):
            try:
                res=ac.cronbach_alpha(df,items,reverse)
                st.metric("Cronbach's alpha",f"{res['alpha']:.4f}")
                st.write(f"N lengkap = {res['n']} | Jumlah item = {res['k']}")
                st.dataframe(res["item_diagnostics"],use_container_width=True)
            except Exception as e: st.error(str(e))
        st.caption("Alpha bukan bukti unidimensionalitas atau validitas konstruk. Evaluasi struktur faktor dan teori tetap diperlukan.")
with tabs[3]:
    df=st.session_state.data
    if df.empty: st.info("Impor data terlebih dahulu.")
    else:
        nums=df.select_dtypes(include=np.number).columns.tolist()
        method=st.selectbox("Jenis uji",["Deskriptif","Uji t satu sampel","Uji t independen","ANOVA satu arah","Korelasi Pearson"])
        if method=="Deskriptif":
            vars=st.multiselect("Variabel",nums,default=nums[:min(5,len(nums))])
            if st.button("Jalankan deskriptif"):
                try: st.dataframe(ac.descriptive(df,vars),use_container_width=True)
                except Exception as e: st.error(str(e))
        elif method=="Uji t satu sampel":
            var=st.selectbox("Variabel",nums); val=st.number_input("Nilai pembanding",value=0.0)
            if st.button("Jalankan uji t"):
                try: st.json(ac.one_sample_t(df,var,val))
                except Exception as e: st.error(str(e))
        elif method=="Uji t independen":
            var=st.selectbox("Variabel dependen",nums); group=st.selectbox("Variabel kelompok",[c for c in df.columns if c!=var])
            eq=st.checkbox("Asumsikan varians sama (Student t)",value=False)
            if st.button("Jalankan uji t independen"):
                try: st.json(ac.independent_t(df,var,group,eq))
                except Exception as e: st.error(str(e))
        elif method=="ANOVA satu arah":
            var=st.selectbox("Variabel dependen",nums); factor=st.selectbox("Faktor kelompok",[c for c in df.columns if c!=var])
            if st.button("Jalankan ANOVA"):
                try: st.json(ac.one_way_anova(df,var,factor))
                except Exception as e: st.error(str(e))
        else:
            vars=st.multiselect("Variabel korelasi",nums)
            if st.button("Hitung korelasi"):
                try: st.dataframe(ac.pearson_matrix(df,vars).round(4),use_container_width=True)
                except Exception as e: st.error(str(e))
with tabs[4]:
    df=st.session_state.data
    if df.empty: st.info("Impor data terlebih dahulu.")
    else:
        nums=df.select_dtypes(include=np.number).columns.tolist()
        y=st.selectbox("Variabel dependen",nums)
        xs=st.multiselect("Prediktor", [c for c in nums if c!=y])
        if st.button("Estimasi regresi OLS"):
            try:
                res=ac.linear_regression(df,y,xs)
                st.metric("R-squared",f"{res['r_squared']:.4f}")
                st.write(f"Adjusted R² = {res['adjusted_r_squared']:.4f}; F = {res['F']:.3f}; p model = {res['F_p_value']:.4g}; N = {res['n']}")
                st.dataframe(res["coefficients"],use_container_width=True)
                st.json(res["diagnostics"])
            except Exception as e: st.error(str(e))
        st.caption("Regresi OLS menguji asosiasi/prediksi dalam spesifikasi model; tidak otomatis membuktikan kausalitas. Periksa asumsi dan rancangan penelitian.")
with tabs[5]:
    f=st.file_uploader("CSV transkrip (kolom text wajib)",type="csv",key="transcripts")
    if f:
        raw=pd.read_csv(f)
        if "text" not in raw: st.error("Kolom text wajib.")
        else:
            for c,default in [("source","Impor"),("participant","NA")]:
                if c not in raw: raw[c]=default
            raw=raw[["source","participant","text"]].dropna(subset=["text"]).copy()
            raw.insert(0,"id",[f"Q{i+1:04d}" for i in range(len(raw))])
            st.session_state.segments=raw
    seg=st.session_state.segments
    if not seg.empty:
        sid=st.selectbox("Unit data",seg.id.tolist())
        st.write(seg.loc[seg.id==sid,"text"].iloc[0])
        code=st.text_input("Kode"); cat=st.text_input("Kategori"); theme=st.text_input("Tema sementara")
        memo=st.text_area("Memo"); ev=st.selectbox("Sumber bukti",["Wawancara","Observasi","Dokumentasi","FGD","Lainnya"])
        if st.button("Simpan coding"):
            if code.strip():
                st.session_state.codes=pd.concat([st.session_state.codes,pd.DataFrame([{"segment_id":sid,"code":code,"category":cat,"theme":theme,"memo":memo,"evidence_type":ev}])],ignore_index=True)
                st.success("Coding tersimpan.")
            else: st.error("Kode harus diisi.")
    st.dataframe(st.session_state.codes,use_container_width=True)

with tabs[6]:
    st.subheader("PLS-SEM Engine — prototipe reflektif")
    st.warning("Cakupan v2.6: konstruk reflektif, Mode A, model satu tingkat, jalur asiklik. Belum mendukung konstruk formatif, moderasi, mediasi bootstrap khusus indirect effect, HOC, PLSpredict, blindfolding/Q², SRMR, atau prosedur weighting lengkap yang identik dengan SmartPLS.")
    df=st.session_state.data
    if df.empty:
        st.info("Impor data responden pada tab Data terlebih dahulu.")
    else:
        st.markdown("Masukkan konstruk dan indikator. Setiap konstruk minimal dua indikator; indikator tidak boleh dipakai lintas konstruk pada versi ini.")
        n_construct=st.number_input("Jumlah konstruk",min_value=2,max_value=8,value=3,step=1)
        blocks={}
        cols=df.columns.tolist()
        for j in range(int(n_construct)):
            c1,c2=st.columns([1,3])
            cname=c1.text_input(f"Nama konstruk {j+1}",value=f"K{j+1}",key=f"pls_c_{j}")
            items=c2.multiselect(f"Indikator {cname or j+1}",cols,key=f"pls_i_{j}")
            if cname.strip(): blocks[cname.strip()]=items
        path_text=st.text_area("Jalur struktural (satu per baris)",value="K1 -> K2\nK2 -> K3")
        boots=st.select_slider("Jumlah bootstrap",options=[100,200,500,1000],value=500)
        if st.button("Estimasi PLS-SEM prototipe"):
            try:
                result=pls_engine.estimate_pls(df,blocks,path_text,bootstrap=int(boots))
                st.session_state["pls_result"]=result
                st.success(f"Estimasi selesai pada {result['n']} kasus lengkap; bootstrap valid {result['settings']['bootstrap_valid']}.")
            except Exception as e: st.error(str(e))
        result=st.session_state.get("pls_result")
        if result:
            st.caption("Algoritma: Mode A reflektif dengan inner proxy tetangga jalur. Hasil eksploratif perlu dibandingkan dengan perangkat lunak tervalidasi.")
            st.metric("Kasus lengkap",result["n"])
            st.write("Outer loading, AVE, dan CR (estimasi ringkas)")
            st.dataframe(result["measurement"],use_container_width=True)
            st.write("Koefisien jalur OLS atas skor konstruk")
            st.dataframe(result["paths"],use_container_width=True)
            st.write("Bootstrap percentile 95% CI")
            st.dataframe(result["bootstrap"],use_container_width=True)
            st.write("R-square"); st.dataframe(result["r2"],use_container_width=True)
            st.write("Inner VIF"); st.dataframe(result["vif"],use_container_width=True)
            st.write("HTMT (eksploratif)"); st.dataframe(result["htmt"],use_container_width=True)
            st.write("Outer weights"); st.dataframe(result["weights"],use_container_width=True)
            st.download_button("Unduh hasil jalur CSV",result["bootstrap"].merge(result["paths"],on="path").to_csv(index=False).encode("utf-8-sig"),"pls_bootstrap_paths.csv")
            st.divider()
            with st.expander("Higher Order Construct (HOC) — Two-Stage"):
                hoc_name=st.text_input("Nama konstruk tingkat tinggi",value="HOC")
                hoc_components=st.multiselect("Lower-order components pembentuk HOC",list(blocks.keys()),key="hoc_components")
                outcome_names=[c for c in blocks if c not in hoc_components]
                hoc_paths=st.text_area("Jalur tahap kedua (gunakan nama HOC dan konstruk outcome)",value=f"{hoc_name} -> {outcome_names[-1]}" if outcome_names else "")
                if st.button("Jalankan HOC Two-Stage"):
                    try:
                        outcomes={c:blocks[c] for c in outcome_names}
                        hr=pls_engine.estimate_hoc_two_stage(df,blocks,hoc_name,hoc_components,outcomes,hoc_paths,bootstrap=300)
                        st.session_state["hoc_result"]=hr
                    except Exception as e: st.error(str(e))
                if st.session_state.get("hoc_result"):
                    st.write("Hasil model tahap kedua")
                    st.dataframe(st.session_state["hoc_result"]["stage2"]["paths"],use_container_width=True)
                    st.dataframe(st.session_state["hoc_result"]["stage2"]["bootstrap"],use_container_width=True)
            with st.expander("Konstruk Formatif — diagnostik bobot berbasis criterion"):
                f_inds=st.multiselect("Indikator formatif",df.select_dtypes(include=np.number).columns.tolist(),key="form_inds")
                f_criterion=st.selectbox("Criterion eksternal",df.select_dtypes(include=np.number).columns.tolist(),key="form_criterion")
                if st.button("Hitung bobot formatif diagnostik"):
                    try:
                        fr=pls_engine.formative_weights(df,f_inds,f_criterion)
                        st.session_state["form_result"]=fr
                    except Exception as e: st.error(str(e))
                if st.session_state.get("form_result"):
                    st.write(f"R² criterion = {st.session_state['form_result']['r_squared_criterion']:.3f}")
                    st.dataframe(st.session_state["form_result"]["weights"],use_container_width=True)
                    st.caption("Ini regresi berbasis criterion untuk diagnostik formatif, bukan algoritma Mode B PLS yang lengkap.")
            with st.expander("Q² — cross-validated predictive relevance"):
                qd=st.slider("Omission distance",2,10,7)
                if st.button("Hitung Q²"):
                    try:
                        pths=pls_engine._parse_paths(path_text,list(blocks))
                        st.session_state["q2_result"]=pls_engine.q2_predictive_relevance(result["scores"],pths,qd)
                    except Exception as e: st.error(str(e))
                if st.session_state.get("q2_result") is not None:
                    st.dataframe(st.session_state["q2_result"],use_container_width=True)
                    st.caption("Q² ini adalah pendekatan cross-validation/omission pada skor konstruk, bukan PLSpredict penuh.")
            with st.expander("MICOM-inspired check dan Multi-Group Analysis"):
                group_cols=[c for c in df.columns if c not in [i for v in blocks.values() for i in v]]
                group_col=st.selectbox("Variabel kelompok",group_cols,key="group_col")
                nperm=st.select_slider("Jumlah permutasi",options=[99,199,499],value=199,key="nperm")
                c1,c2=st.columns(2)
                if c1.button("Jalankan MICOM-inspired check"):
                    try: st.session_state["micom_result"]=pls_engine.micom_compositional_check(df,blocks,group_col,int(nperm))
                    except Exception as e: st.error(str(e))
                if c2.button("Jalankan MGA permutation"):
                    try: st.session_state["mga_result"]=pls_engine.permutation_mga(df,blocks,path_text,group_col,int(nperm))
                    except Exception as e: st.error(str(e))
                if st.session_state.get("micom_result") is not None:
                    st.write("MICOM-inspired"); st.dataframe(st.session_state["micom_result"],use_container_width=True)
                if st.session_state.get("mga_result") is not None:
                    st.write("Permutation MGA"); st.dataframe(st.session_state["mga_result"],use_container_width=True)

            st.divider()
            st.subheader("Analisis Mediasi dan Moderasi")
            construct_names=list(result["scores"].columns)
            m1,m2,m3=st.columns(3)
            with m1: med_x=st.selectbox("Mediasi: X",construct_names,key="med_x")
            with m2: med_m=st.selectbox("Mediasi: Mediator",construct_names,index=min(1,len(construct_names)-1),key="med_m")
            with m3: med_y=st.selectbox("Mediasi: Y",construct_names,index=len(construct_names)-1,key="med_y")
            med_n=st.select_slider("Bootstrap mediasi",options=[500,1000,2000],value=1000,key="med_n")
            if st.button("Uji efek mediasi"):
                try:
                    mr=pls_engine.mediation_analysis(result["scores"],med_x,med_m,med_y,bootstrap=int(med_n))
                    st.session_state["med_result"]=mr
                except Exception as e: st.error(str(e))
            if st.session_state.get("med_result"):
                st.json(st.session_state["med_result"])
                st.caption("Mediasi satu mediator: a×b; interval bootstrap persentil. Untuk inferensi publikasi, bandingkan dengan prosedur bootstrap PLS-SEM tervalidasi.")
            st.divider()
            st.markdown("**Moderasi satu moderator**")
            q1,q2,q3=st.columns(3)
            with q1: mod_x=st.selectbox("Moderasi: X",construct_names,key="mod_x")
            with q2: mod_z=st.selectbox("Moderasi: Z",construct_names,index=min(1,len(construct_names)-1),key="mod_z")
            with q3: mod_y=st.selectbox("Moderasi: Y",construct_names,index=len(construct_names)-1,key="mod_y")
            mod_n=st.select_slider("Bootstrap moderasi",options=[500,1000,2000],value=1000,key="mod_n")
            if st.button("Uji efek moderasi"):
                try:
                    zr=pls_engine.moderation_analysis(result["scores"],mod_x,mod_z,mod_y,bootstrap=int(mod_n))
                    st.session_state["mod_result"]=zr
                except Exception as e: st.error(str(e))
            if st.session_state.get("mod_result"):
                st.json(st.session_state["mod_result"])
                st.caption("Moderasi diuji melalui suku interaksi X×Z pada regresi skor konstruk; bukan algoritma product-indicator PLS.")


with tabs[7]:
    st.write("Impor hasil dari SmartPLS/perangkat lunak lain. Kolom wajib: path, beta, p_value.")
    f=st.file_uploader("Hasil SEM-PLS CSV",type="csv",key="semfile")
    if f:
        try: st.session_state.sem=ac.validate_sem_import(pd.read_csv(f)); st.success("Hasil lolos validasi format.")
        except Exception as e: st.error(str(e))
    if not st.session_state.sem.empty:
        st.dataframe(st.session_state.sem,use_container_width=True)
        for _,r in st.session_state.sem.iterrows():
            st.write(f"{r['path']}: β={r['beta']:.3f}; p={r['p_value']:.4f}; {'signifikan' if r['p_value']<alpha else 'belum signifikan'} pada α={alpha:.3f}.")
with tabs[8]:
    with st.form("joint"):
        q=st.text_input("Temuan kuantitatif"); stat=st.text_input("Statistik")
        theme=st.text_input("Tema kualitatif"); evidence=st.text_area("Bukti/kutipan")
        relation=st.selectbox("Relasi",["Konvergen","Komplementer","Divergen","Ekspansi","Belum ditentukan"])
        inference=st.text_area("Meta-inference")
        ok=st.form_submit_button("Tambah")
    if ok:
        st.session_state.joint.append({"Temuan kuantitatif":q,"Statistik":stat,"Tema":theme,"Bukti":evidence,"Relasi":relation,"Meta-inference":inference})
    if st.session_state.joint: st.dataframe(pd.DataFrame(st.session_state.joint),use_container_width=True)

with tabs[9]:
    st.subheader("Research Intelligence")
    st.caption("Pemetaan teori dan indikator, pemeriksaan konsistensi model, interpretasi hasil, serta draf Bab IV–V berbasis data yang dimasukkan.")
    if "ri_mapping" not in st.session_state:
        st.session_state.ri_mapping=ri.empty_mapping()
    if "ri_hypotheses" not in st.session_state:
        st.session_state.ri_hypotheses=ri.empty_hypotheses()
    st.markdown("**A. Pemetaan teori, konstruk, dimensi, dan indikator**")
    st.write("Isi satu baris untuk setiap indikator. Role gunakan: independent, dependent, mediator, moderator, control, predictor, outcome, formative, atau reflective.")
    edited_map=st.data_editor(st.session_state.ri_mapping,num_rows="dynamic",use_container_width=True,key="ri_map_editor")
    st.session_state.ri_mapping=edited_map
    st.markdown("**B. Hipotesis penelitian**")
    edited_hyp=st.data_editor(st.session_state.ri_hypotheses,num_rows="dynamic",use_container_width=True,key="ri_hyp_editor")
    st.session_state.ri_hypotheses=edited_hyp
    st.markdown("**C. Pemeriksaan konsistensi**")
    if st.button("Periksa teori–variabel–hipotesis–model"):
        try:
            mp=ri.validate_mapping(st.session_state.ri_mapping)
            # Prefer live PLS path table; fall back to imported SEM table.
            ptable=None
            if st.session_state.get("pls_result"):
                ptable=st.session_state["pls_result"]["paths"].copy()
            elif not st.session_state.sem.empty:
                ptable=st.session_state.sem.copy()
            chk=ri.check_model_consistency(mp,st.session_state.ri_hypotheses,ptable)
            st.session_state["ri_check"]=chk
        except Exception as e:
            st.error(str(e))
    if st.session_state.get("ri_check"):
        chk=st.session_state["ri_check"]
        st.metric("Status konsistensi",chk["status"])
        st.write("Konstruk terpetakan:",", ".join(chk["constructs"]))
        if chk["issues"]:
            for issue in chk["issues"]: st.warning(issue)
        else:
            st.success("Tidak ditemukan ketidaksesuaian struktural pada pemeriksaan otomatis. Kesesuaian teori tetap perlu dinilai peneliti.")
    st.markdown("**D. Interpretasi hasil dan draf Bab IV–V**")
    alpha_ri=st.number_input("Ambang signifikansi untuk narasi",0.001,0.20,0.05,0.005,key="ri_alpha")
    result_paths=None
    if st.session_state.get("pls_result"):
        result_paths=st.session_state["pls_result"]["bootstrap"].merge(
            st.session_state["pls_result"]["paths"],on="path",suffixes=("_boot",""))
    elif not st.session_state.sem.empty:
        result_paths=st.session_state.sem
    if st.button("Buat interpretasi hasil"):
        st.session_state["ri_interpretation"]=ri.interpret_paths(result_paths,alpha_ri)
    for line in st.session_state.get("ri_interpretation",[]):
        st.write("• "+line)
    project_name=st.text_input("Judul penelitian untuk draf",value=project,key="ri_project")
    if st.button("Susun draf Bab IV dan Bab V"):
        try:
            mp=ri.validate_mapping(st.session_state.ri_mapping)
            st.session_state["ri_ch4"]=ri.draft_chapter_four(project_name,design,mp,result_paths,
                st.session_state.codes,pd.DataFrame(st.session_state.joint),alpha_ri)
            st.session_state["ri_ch5"]=ri.draft_chapter_five(project_name,result_paths,alpha_ri,mp)
        except Exception as e: st.error(str(e))
    if st.session_state.get("ri_ch4"):
        st.download_button("Unduh draf Bab IV (TXT)",st.session_state["ri_ch4"].encode("utf-8"),"Draf_Bab_IV.txt")
        st.download_button("Unduh draf Bab V (TXT)",st.session_state["ri_ch5"].encode("utf-8"),"Draf_Bab_V.txt")
        st.text_area("Pratinjau Bab IV",st.session_state["ri_ch4"],height=260)
        st.text_area("Pratinjau Bab V",st.session_state["ri_ch5"],height=220)
    st.info("Fitur ini menyusun draf berbasis data dan isian pengguna. Sistem tidak mengarang teori, sitasi, kutipan, atau hasil penelitian yang belum tersedia.")


with tabs[10]:
    st.subheader("Literature Review & Instrument Intelligence")
    st.caption("Workspace berbasis bukti untuk mengorganisasi artikel, merumuskan sintesis, dan menyusun draf awal instrumen.")
    if "ri3_literature" not in st.session_state:
        st.session_state.ri3_literature=ri3.literature_template()
    if "ri3_instrument" not in st.session_state:
        st.session_state.ri3_instrument=ri3.instrument_template()
    if "ri3_coding" not in st.session_state:
        st.session_state.ri3_coding=pd.DataFrame()
    st.markdown("**A. Literature Matrix**")
    st.write("Masukkan metadata artikel yang telah dibaca. Kolom DOI/URL membantu peneliti menelusuri sumber; sistem tidak memverifikasi keaslian DOI atau isi artikel.")
    lit_upload=st.file_uploader("Impor matriks literatur (CSV)",type="csv",key="ri3_lit_upload")
    if lit_upload is not None:
        try:
            incoming=pd.read_csv(lit_upload)
            missing=[c for c in ri3.LITERATURE_COLUMNS if c not in incoming.columns]
            for c in missing: incoming[c]=""
            st.session_state.ri3_literature=incoming[ri3.LITERATURE_COLUMNS]
            st.success("Matriks literatur berhasil dimuat untuk ditinjau.")
        except Exception as e: st.error(f"Gagal membaca CSV: {e}")
    st.download_button("Unduh template Literature Matrix",ri3.literature_template().to_csv(index=False).encode("utf-8-sig"),
                       "Literature_Matrix_Template.csv","text/csv")
    lit_edit=st.data_editor(st.session_state.ri3_literature,num_rows="dynamic",use_container_width=True,key="ri3_lit_editor")
    st.session_state.ri3_literature=lit_edit
    if not lit_edit.empty:
        try:
            summary=ri3.literature_summary(lit_edit)
            m1,m2=st.columns(2)
            m1.metric("Artikel terdata",summary["count"])
            m2.metric("Rentang tahun",summary["year_range"])
            st.dataframe(summary["themes"],use_container_width=True)
            for issue in summary["gaps"]: st.warning(issue)
            st.markdown("**Kerangka sintesis berbasis artikel terdata**")
            st.text_area("Sintesis per tema",ri3.theme_synthesis(lit_edit),height=250)
        except Exception as e: st.error(str(e))
    st.divider()
    st.markdown("**B. Instrument Blueprint Generator**")
    st.write("Generator membuat butir awal dari indikator yang sudah dipetakan pada tab Research Intelligence. Setiap butir wajib disunting dan divalidasi sebelum digunakan.")
    scale=st.selectbox("Skala respons",["Likert 1–5","Likert 1–4","Likert 1–7","Frekuensi 1–5"],key="ri3_scale")
    if st.button("Buat draf instrumen dari pemetaan indikator"):
        try:
            st.session_state.ri3_instrument=ri3.build_instrument(st.session_state.ri_mapping,scale)
            if st.session_state.ri3_instrument.empty: st.warning("Pemetaan indikator masih kosong.")
        except Exception as e: st.error(str(e))
    if not st.session_state.ri3_instrument.empty:
        inst_edit=st.data_editor(st.session_state.ri3_instrument,num_rows="dynamic",use_container_width=True,key="ri3_inst_editor")
        st.session_state.ri3_instrument=inst_edit
        st.download_button("Unduh draf instrumen CSV",inst_edit.to_csv(index=False).encode("utf-8-sig"),
                           "Draft_Instrumen_Penelitian.csv","text/csv")
    st.divider()
    st.markdown("**C. Saran kode awal untuk transkrip kualitatif**")
    st.write("Masukkan kamus istilah yang Anda susun dari kerangka teori atau pembacaan awal. Sistem hanya mencocokkan kata/istilah, bukan memahami makna kontekstual.")
    dictionary_text=st.text_area("Satu baris per kode: Nama kode: istilah1, istilah2",
        placeholder="dukungan kepala sekolah: dukungan, memfasilitasi, membantu\\npartisipasi: terlibat, dilibatkan, musyawarah",
        key="ri3_dictionary")
    if st.button("Jalankan saran kode berbasis kamus"):
        try:
            dictionary={}
            for line in dictionary_text.splitlines():
                if ":" in line:
                    code,terms=line.split(":",1)
                    dictionary[code.strip()]=[x.strip() for x in terms.split(",") if x.strip()]
            if not dictionary: raise ValueError("Masukkan minimal satu kode dan istilah.")
            if st.session_state.segments.empty: raise ValueError("Belum ada segmen transkrip pada tab Kualitatif.")
            st.session_state.ri3_coding=ri3.keyword_code_suggestions(st.session_state.segments["text"].tolist(),dictionary)
        except Exception as e: st.error(str(e))
    if not st.session_state.ri3_coding.empty:
        coding_edit=st.data_editor(st.session_state.ri3_coding,num_rows="dynamic",use_container_width=True,key="ri3_coding_editor")
        st.session_state.ri3_coding=coding_edit
        st.download_button("Unduh saran coding CSV",coding_edit.to_csv(index=False).encode("utf-8-sig"),
                           "Saran_Coding_Transkrip.csv","text/csv")
    st.info("Batas penggunaan: modul ini membantu pengorganisasian bukti dan penyusunan draf. Ia bukan AI generatif, tidak melakukan pencarian web, tidak memverifikasi artikel, dan tidak menggantikan pembacaan kritis, coding interpretatif, validasi ahli, uji coba instrumen, atau uji psikometrik.")


with tabs[11]:
    st.subheader("AI Research Studio — Integrasi API Generatif")
    st.write("Gunakan AI untuk menganalisis artikel, membandingkan teori, merumuskan gap, mengembangkan instrumen, mengode transkrip, dan menyusun diskusi berdasarkan bahan yang Anda berikan.")
    st.warning("Privasi dan biaya: ketika tombol analisis ditekan, teks yang dimasukkan/diekstrak akan dikirim ke API eksternal dan dapat menimbulkan biaya sesuai akun penyedia. Jangan unggah data identitas partisipan, informasi sensitif, atau dokumen yang belum memiliki izin. API key hanya digunakan dalam sesi aplikasi dan tidak ditulis ke file proyek.")
    api_key=st.text_input("OpenAI API key",value=os.environ.get("OPENAI_API_KEY",""),type="password",key="v31_api_key")
    if st.button("Muat daftar model yang tersedia pada API key",key="v31_list_models"):
        try:
            st.session_state["v31_available_models"]=aire.list_available_models(api_key)
            st.success(f"{len(st.session_state['v31_available_models'])} model terdeteksi.")
        except Exception as e: st.error(f"Gagal memuat model: {e}")
    available=st.session_state.get("v31_available_models",[])
    if available:
        default_idx=available.index(aire.DEFAULT_MODEL) if aire.DEFAULT_MODEL in available else 0
        model=st.selectbox("Model API yang tersedia",available,index=default_idx,key="v31_model_choice")
    else:
        model=st.text_input("Nama model API",value=aire.DEFAULT_MODEL,key="v31_model")
    task=st.selectbox("Jenis analisis",list(aire.TASKS.keys()),key="v31_task")
    uploaded=st.file_uploader("Unggah bahan (PDF, DOCX, TXT, MD)",type=["pdf","docx","txt","md"],accept_multiple_files=True,key="v31_files")
    extracted=[]
    for f in uploaded or []:
        try:
            body=aire.extract_uploaded_text(f)
            extracted.append(f"=== SUMBER: {f.name} ===\n{body}")
        except Exception as e:
            st.error(f"Gagal membaca {f.name}: {e}")
    pasted=st.text_area("Teks / data / referensi tambahan",height=180,
        placeholder="Tempelkan bagian artikel, teori, indikator, hasil analisis, atau transkrip yang telah dianonimkan.",key="v31_input")
    combined="\n\n".join(extracted+[pasted.strip() if pasted.strip() else ""])
    if extracted:
        st.caption(f"{len(extracted)} file berhasil dibaca. Panjang teks hasil ekstraksi: {sum(len(x) for x in extracted):,} karakter.")
    st.caption(f"Batas teks per permintaan: {aire.MAX_INPUT_CHARS:,} karakter. Untuk dokumen panjang, analisis per bagian.")
    max_tokens=st.slider("Batas keluaran maksimum",500,6000,2500,250,key="v31_max_tokens")
    if st.button("Jalankan analisis AI",type="primary",key="v31_run"):
        if not api_key:
            st.error("Masukkan API key terlebih dahulu.")
        elif not combined.strip():
            st.error("Unggah dokumen atau masukkan teks yang akan dianalisis.")
        else:
            with st.spinner("Permintaan sedang diproses oleh model API..."):
                try:
                    result=aire.call_responses_api(api_key,combined,task,model=model,max_output_tokens=max_tokens)
                    st.session_state["v31_last_result"]=result
                    st.session_state["v31_last_task"]=task
                except Exception as e:
                    st.error(f"Analisis gagal: {e}")
    if st.session_state.get("v31_last_result"):
        st.markdown("#### Hasil analisis")
        st.markdown(st.session_state["v31_last_result"])
        st.download_button("Unduh hasil analisis (.txt)",
            st.session_state["v31_last_result"].encode("utf-8"),
            "AI_Research_Analysis_v3.1.txt","text/plain")
        st.caption(f"Jenis tugas: {st.session_state.get('v31_last_task','')}")
    st.info("AI menghasilkan bantuan analitis, bukan keputusan ilmiah final. Periksa setiap kutipan terhadap dokumen sumber, validasi metadata dan DOI secara mandiri, evaluasi interpretasi alternatif, dan jangan menganggap research gap atau instrumen otomatis valid. Untuk artikel jurnal, semua klaim dan sitasi tetap menjadi tanggung jawab penulis.")


with tabs[12]:
    st.subheader("Research Intelligence 3.2")
    lit_tab, qual_tab, paper_tab = st.tabs(["Intelligent Literature Review","Advanced Qualitative Intelligence","Academic Manuscript Intelligence"])
    with lit_tab:
        st.markdown("**A. Pencarian metadata publikasi melalui Crossref**")
        st.write("Cari judul atau kata kunci untuk menemukan kandidat metadata publikasi. Crossref bukan pemeringkat kualitas; relevansi dan keabsahan metadata tetap harus diperiksa.")
        q=st.text_input("Kata kunci / judul artikel",key="v32_crossref_query")
        n=st.slider("Jumlah kandidat",5,30,10,key="v32_crossref_rows")
        if st.button("Cari metadata Crossref",key="v32_crossref_search"):
            try:
                found=ri32.crossref_search(q,n)
                st.session_state["v32_crossref_results"]=found
                st.success(f"{len(found)} kandidat metadata ditemukan.")
            except Exception as e: st.error(f"Pencarian gagal: {e}")
        found=st.session_state.get("v32_crossref_results",[])
        if found:
            df_cross=pd.DataFrame(found)
            st.dataframe(df_cross,use_container_width=True)
            if st.button("Tambahkan kandidat ke Literature Matrix",key="v32_crossref_add"):
                rows=ri32.to_literature_matrix(found)
                current=st.session_state.get("ri3_literature",ri3.literature_template())
                combined=pd.concat([current,pd.DataFrame(rows)],ignore_index=True)
                if "doi_url" in combined:
                    combined=combined.drop_duplicates(subset=["doi_url","title"],keep="first")
                st.session_state.ri3_literature=combined
                st.success("Kandidat ditambahkan. Lengkapi teori, metode, temuan, dan tema setelah membaca artikel.")
            csv_cross=df_cross.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Unduh hasil pencarian Crossref CSV",csv_cross,"Crossref_Candidates.csv","text/csv")
        st.caption("Pencarian menggunakan metadata bibliografi Crossref. Tidak mengunduh full text, tidak memastikan artikel telah peer-reviewed, dan tidak mengonfirmasi kualitas jurnal.")
    with qual_tab:
        st.markdown("**B. Codebook dan audit trail kualitatif**")
        st.write("Gunakan AI Research Studio untuk membuat draf codebook, lalu tinjau definisi, kriteria inklusi/eksklusi, kutipan, dan keputusan akhir secara manual.")
        st.download_button("Unduh template codebook CSV",
            pd.DataFrame(ri32.build_codebook_template()).to_csv(index=False).encode("utf-8-sig"),
            "Qualitative_Codebook_Template.csv","text/csv")
        if not st.session_state.codes.empty:
            st.markdown("Frekuensi kode yang tercatat pada workspace kualitatif")
            st.dataframe(pd.DataFrame(ri32.code_frequency(st.session_state.codes)),use_container_width=True)
            st.download_button("Unduh coding workspace CSV",
                st.session_state.codes.to_csv(index=False).encode("utf-8-sig"),
                "Qualitative_Coding_Audit.csv","text/csv")
        st.markdown("**Pemeriksaan kesepakatan dua coder (Cohen's kappa)**")
        ca=st.text_area("Label coder A — satu label per baris",key="v32_coder_a",
            placeholder="dukungan\npartisipasi\nkolaborasi")
        cb=st.text_area("Label coder B — urutan unit yang sama",key="v32_coder_b",
            placeholder="dukungan\nkolaborasi\nkolaborasi")
        if st.button("Hitung Cohen's kappa",key="v32_kappa"):
            try:
                a=[x.strip() for x in ca.splitlines() if x.strip()]
                b=[x.strip() for x in cb.splitlines() if x.strip()]
                k=ri32.cohens_kappa(a,b)
                st.metric("Cohen's kappa",f"{k:.3f}")
                st.caption("Interpretasi harus mempertimbangkan prevalensi kode, jumlah unit, desain coding, dan konteks penelitian; jangan menggunakan ambang interpretasi secara mekanis.")
            except Exception as e: st.error(str(e))
        st.info("Kappa hanya bermakna jika dua coder menilai unit analisis yang sama dengan skema kategori yang sama. Untuk multi-label coding, gunakan prosedur yang sesuai dan jangan memaksakan Cohen's kappa.")
    with paper_tab:
        st.markdown("**C. Academic Manuscript Intelligence**")
        title=st.text_input("Judul manuskrip",key="v32_paper_title")
        design=st.text_input("Desain dan konteks penelitian",key="v32_paper_design")
        theory=st.text_area("Teori / kerangka konseptual",key="v32_paper_theory")
        literature=st.text_area("Temuan literatur dan referensi yang sudah diverifikasi",key="v32_paper_literature")
        method=st.text_area("Metode penelitian",key="v32_paper_method")
        findings=st.text_area("Hasil penelitian terverifikasi",height=140,key="v32_paper_findings")
        limitations=st.text_area("Keterbatasan penelitian",key="v32_paper_limitations")
        outline=ri32.manuscript_outline(title or "Judul penelitian",design,findings,theory,literature,method,limitations)
        st.download_button("Unduh kerangka manuskrip Markdown",outline.encode("utf-8"),
            "Manuscript_Structure_v3.2.md","text/markdown")
        st.markdown("**Draf manuskrip berbantuan AI**")
        ai_key=st.text_input("API key untuk penyusunan manuskrip",type="password",key="v32_paper_key")
        ai_model=st.text_input("Model API",value=aire.DEFAULT_MODEL,key="v32_paper_model")
        if st.button("Susun draf manuskrip dengan AI",key="v32_paper_generate",type="primary"):
            source=f"TITLE: {title}\nDESIGN: {design}\nTHEORY: {theory}\nVERIFIED LITERATURE:\n{literature}\nMETHOD:\n{method}\nVERIFIED FINDINGS:\n{findings}\nLIMITATIONS:\n{limitations}"
            try:
                result=aire.call_responses_api(ai_key,source,"Penyusunan manuskrip ilmiah",model=ai_model,max_output_tokens=5000)
                st.session_state["v32_manuscript_result"]=result
            except Exception as e: st.error(f"Gagal menyusun manuskrip: {e}")
        if st.session_state.get("v32_manuscript_result"):
            st.markdown(st.session_state["v32_manuscript_result"])
            st.download_button("Unduh draf manuskrip AI",
                st.session_state["v32_manuscript_result"].encode("utf-8"),
                "AI_Manuscript_Draft_v3.2.md","text/markdown")
        st.warning("Kerangka dan draf AI bukan artikel siap terbit. Periksa konsistensi tujuan-metode-hasil, kelengkapan pelaporan, etika, orisinalitas, seluruh kutipan, dan ketentuan jurnal sasaran.")


with tabs[13]:
    st.subheader("Systematic Review & PRISMA Workflow")
    st.caption("Mengelola hasil penelusuran, deduplikasi, penyaringan judul/abstrak, pemeriksaan full text, dan ringkasan alur seleksi.")
    if "v33_review_matrix" not in st.session_state:
        st.session_state.v33_review_matrix=sr33.empty_review_matrix()
    st.markdown("**A. Impor rekaman bibliografi**")
    uploaded_review=st.file_uploader("Unggah file RIS, BibTeX, atau CSV",type=["ris","bib","bibtex","csv"],key="v33_review_upload")
    if uploaded_review is not None:
        try:
            raw=uploaded_review.getvalue().decode("utf-8",errors="replace")
            ext=uploaded_review.name.lower().split(".")[-1]
            if ext=="ris": records=sr33.parse_ris(raw)
            elif ext in ("bib","bibtex"): records=sr33.parse_bibtex(raw)
            else:
                imported=pd.read_csv(uploaded_review)
                if "source" not in imported.columns and "journal" in imported.columns:
                    imported=imported.rename(columns={"journal":"source"})
                if "doi" not in imported.columns and "doi_url" in imported.columns:
                    imported=imported.rename(columns={"doi_url":"doi"})
                records=imported.to_dict(orient="records")
            newdf=sr33.records_to_frame(records)
            combined=pd.concat([st.session_state.v33_review_matrix,newdf],ignore_index=True)
            combined,_=sr33.mark_duplicates(combined)
            st.session_state.v33_review_matrix=combined
            st.success(f"{len(newdf)} rekaman diimpor. Periksa metadata dan status duplikasi.")
        except Exception as e: st.error(f"Gagal mengimpor rekaman: {e}")
    st.download_button("Unduh template CSV",sr33.empty_review_matrix().to_csv(index=False).encode("utf-8-sig"),
                       "Systematic_Review_Matrix_Template.csv","text/csv")
    st.markdown("**B. Screening dan keputusan reviewer**")
    st.write("Tinjau setiap rekaman. Tandai keputusan judul/abstrak dan keputusan full text setelah dokumen diperoleh.")
    if not st.session_state.v33_review_matrix.empty:
        edited=st.data_editor(st.session_state.v33_review_matrix,num_rows="dynamic",use_container_width=True,
            column_config={
                "title_abstract_decision":st.column_config.SelectboxColumn("Title/abstract decision",options=["Pending","Include","Exclude"]),
                "full_text_decision":st.column_config.SelectboxColumn("Full-text decision",options=["Not assessed","Include","Exclude","Not retrieved"]),
            },key="v33_review_editor")
        st.session_state.v33_review_matrix=edited
        st.download_button("Unduh matriks screening CSV",edited.to_csv(index=False).encode("utf-8-sig"),
                           "Systematic_Review_Screening.csv","text/csv")
        st.download_button("Unduh screening log CSV",sr33.screening_log(edited).to_csv(index=False).encode("utf-8-sig"),
                           "Screening_Audit_Log.csv","text/csv")
    else:
        st.info("Belum ada rekaman. Impor file RIS/BibTeX/CSV untuk memulai.")
    st.divider()
    st.markdown("**C. PRISMA-style flow accounting**")
    review_df=st.session_state.v33_review_matrix
    if not review_df.empty:
        not_retrieved=int((review_df["full_text_decision"]=="Not retrieved").sum())
        fulltext_excluded=int((review_df["full_text_decision"]=="Exclude").sum())
    else:
        not_retrieved=0
        fulltext_excluded=0
    counts=sr33.prisma_counts(review_df,not_retrieved,fulltext_excluded)
    cols=st.columns(3)
    for col,(label,key) in zip(cols,[("Identifikasi","records_identified"),("Duplikat","duplicates_removed"),("Screening","records_screened")]):
        col.metric(label,counts[key])
    cols2=st.columns(3)
    for col,(label,key) in zip(cols2,[("Lolos judul/abstrak","reports_sought"),("Dinilai full text","reports_assessed"),("Studi disertakan","studies_included")]):
        col.metric(label,counts[key])
    st.dataframe(pd.DataFrame([{"Tahap":k.replace("_"," ").title(),"Jumlah":v} for k,v in counts.items()]),use_container_width=True)
    mermaid=sr33.prisma_mermaid(counts)
    st.code(mermaid,language="mermaid")
    st.download_button("Unduh diagram alur PRISMA (Mermaid)",mermaid.encode("utf-8"),
                       "PRISMA_Flow_v3.3.mmd","text/plain")
    st.warning("Ini adalah alat pencatatan alur seleksi bergaya PRISMA, bukan sertifikasi kepatuhan PRISMA 2020. Lengkapi alasan eksklusi, tanggal dan basis data pencarian, strategi pencarian, protokol, proses reviewer, serta verifikasi jumlah pada diagram. Untuk tinjauan sistematis formal, ikuti checklist dan panduan PRISMA 2020.")


with tabs[14]:
    st.subheader("Advanced Qualitative Intelligence")
    st.caption("Pengelolaan codebook, audit trail, pengelompokan bukti tema, triangulasi, dan persiapan analisis tematik.")
    if "v34_codebook" not in st.session_state:
        st.session_state.v34_codebook=qa34.empty_codebook()
    st.markdown("**A. Codebook hierarkis**")
    cb_upload=st.file_uploader("Impor codebook CSV",type="csv",key="v34_cb_upload")
    if cb_upload is not None:
        try:
            cb=pd.read_csv(cb_upload).fillna("")
            st.session_state.v34_codebook=qa34.validate_codebook(cb)
            st.success("Codebook dimuat.")
        except Exception as e: st.error(f"Codebook tidak valid: {e}")
    cb_edit=st.data_editor(st.session_state.v34_codebook,num_rows="dynamic",use_container_width=True,key="v34_cb_editor")
    st.session_state.v34_codebook=cb_edit
    if st.button("Validasi codebook",key="v34_cb_validate"):
        try:
            st.session_state.v34_codebook=qa34.validate_codebook(cb_edit)
            st.success("Struktur codebook lolos pemeriksaan dasar.")
        except Exception as e: st.error(str(e))
    st.download_button("Unduh codebook CSV",cb_edit.to_csv(index=False).encode("utf-8-sig"),
        "Advanced_Qualitative_Codebook.csv","text/csv")
    st.divider()
    st.markdown("**B. Chunking transkrip untuk analisis AI bertahap**")
    if not st.session_state.segments.empty:
        chunks=qa34.chunk_segments(st.session_state.segments,max_chars=10000)
        st.metric("Jumlah segmen",len(st.session_state.segments))
        st.metric("Jumlah batch",len(chunks))
        st.selectbox("Pratinjau batch",list(range(1,len(chunks)+1)),key="v34_chunk_choice")
        selected=st.session_state.get("v34_chunk_choice",1)-1
        st.text_area("Teks batch",chunks[selected],height=220,key="v34_chunk_preview")
        st.download_button("Unduh batch transkrip teranonymisasi",chunks[selected].encode("utf-8"),
            f"Transcript_Batch_{selected+1}.txt","text/plain")
    else:
        st.info("Impor transkrip pada tab Kualitatif terlebih dahulu.")
    st.divider()
    st.markdown("**C. Evidence matrix dan audit coding**")
    if not st.session_state.codes.empty:
        code_df=st.session_state.codes.copy()
        # Align existing coding schema to the extended audit model.
        if "parent_code" not in code_df: code_df["parent_code"]=""
        if "approach" not in code_df: code_df["approach"]="Induktif"
        if "evidence_quote" not in code_df: code_df["evidence_quote"]=""
        if "analytic_memo" not in code_df: code_df["analytic_memo"]=code_df.get("memo","")
        if "researcher_status" not in code_df: code_df["researcher_status"]="Pending"
        if "reviewer" not in code_df: code_df["reviewer"]=""
        # Add source and technique from existing evidence_type where available.
        if "source" not in code_df: code_df["source"]=code_df.get("evidence_type","Tidak dicatat")
        if "technique" not in code_df: code_df["technique"]=code_df.get("evidence_type","Tidak dicatat")
        edited_codes=st.data_editor(code_df,num_rows="dynamic",use_container_width=True,key="v34_codes_editor")
        st.session_state["v34_codes_reviewed"]=edited_codes
        audit=qa34.audit_summary(edited_codes)
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Total coding",audit["total"]); c2.metric("Disetujui",audit["approved"])
        c3.metric("Menunggu",audit["pending"]); c4.metric("Ditolak",audit["rejected"])
        st.download_button("Unduh audit coding CSV",edited_codes.to_csv(index=False).encode("utf-8-sig"),
            "Qualitative_Audit_Trail_v3.4.csv","text/csv")
        try:
            themes=qa34.build_theme_evidence(st.session_state.segments,edited_codes)
            st.markdown("**Evidence matrix per tema**")
            themes_edit=st.data_editor(themes,num_rows="dynamic",use_container_width=True,key="v34_theme_editor")
            st.download_button("Unduh evidence matrix tema CSV",themes_edit.to_csv(index=False).encode("utf-8-sig"),
                "Theme_Evidence_Matrix.csv","text/csv")
            tri=qa34.triangulation_matrix(edited_codes)
            st.markdown("**Triangulasi sumber dan teknik**")
            st.dataframe(tri,use_container_width=True)
            st.download_button("Unduh matriks triangulasi CSV",tri.to_csv(index=False).encode("utf-8-sig"),
                "Triangulation_Matrix.csv","text/csv")
        except Exception as e: st.warning(f"Matriks tema belum dapat dibuat: {e}")
    else:
        st.info("Belum ada coding pada tab Kualitatif.")
    st.warning("Chunking hanya membagi teks agar mudah dianalisis. AI coding/tema tetap harus diperiksa terhadap transkrip asli, kasus negatif, konteks informan, refleksivitas, dan triangulasi. Jangan mengunggah data yang mengidentifikasi partisipan.")


with tabs[15]:
    st.subheader("Journal Publication Readiness")
    st.caption("Pemeriksaan kesiapan manuskrip berdasarkan parameter yang ditentukan peneliti; bukan jaminan diterima jurnal.")
    journal=st.text_input("Nama jurnal sasaran",key="v34_journal")
    article_type=st.selectbox("Jenis artikel",["Original Research","Systematic Review","Scoping Review","Case Study","Conceptual Paper","Short Communication"],key="v34_article_type")
    style=st.selectbox("Gaya referensi",["APA 7","Harvard","Vancouver","Chicago","IEEE"],key="v34_style")
    title=st.text_input("Judul manuskrip",key="v34_title")
    abstract=st.text_area("Abstrak",height=180,key="v34_abstract")
    abstract_limit=st.number_input("Batas kata abstrak menurut jurnal",min_value=50,max_value=1000,value=250,step=10,key="v34_abs_limit")
    keywords=st.text_input("Kata kunci (pisahkan koma)",key="v34_keywords")
    sections={}
    sec_cols=st.columns(2)
    for i,sec in enumerate(["Introduction","Methods","Results","Discussion","Conclusion"]):
        with sec_cols[i%2]:
            sections[sec]=st.text_area(f"Ringkasan bagian {sec}",height=100,key=f"v34_sec_{sec}")
    references=st.text_area("Daftar referensi (satu referensi per baris)",height=160,key="v34_references")
    if st.button("Periksa kesiapan manuskrip",type="primary",key="v34_check"):
        report=jr34.manuscript_readiness(title,abstract,keywords,sections,references,int(abstract_limit))
        st.session_state["v34_readiness"]=report
    report=st.session_state.get("v34_readiness")
    if report:
        st.metric("Kelengkapan checklist internal",f"{report['score']:.1f}%")
        st.caption(f"Jumlah kata abstrak: {report['abstract_words']}; kata kunci: {len(report['keywords'])}; referensi dengan DOI/URL DOI terdeteksi: {report['reference_doi']['with_doi']}/{report['reference_doi']['total']}.")
        st.dataframe(pd.DataFrame(report["checks"],columns=["Pemeriksaan","Lolos","Catatan"]),use_container_width=True)
        if report["reference_doi"]["without_doi"]:
            st.info("Sebagian referensi tidak mencantumkan DOI. Tidak semua jenis publikasi memiliki DOI; verifikasi metadata, jangan menganggap referensi tanpa DOI otomatis salah.")
    outline=jr34.manuscript_outline_for_journal(title,journal,article_type,int(abstract_limit),style)
    st.download_button("Unduh kerangka manuskrip sesuai parameter",outline.encode("utf-8"),
        "Journal_Manuscript_Outline_v3.4.md","text/markdown")
    st.caption(jr34.reference_style_note(style))
    st.divider()
    st.markdown("**Adaptasi manuskrip dengan AI**")
    st.write("Untuk meminta AI menyesuaikan manuskrip, masukkan author guidelines resmi jurnal ke AI Research Studio dan pilih tugas 'Adaptasi manuskrip ke jurnal sasaran'.")
    st.warning("Checklist ini memeriksa isian dasar dan parameter yang Anda masukkan. Ia tidak mengambil author guidelines secara otomatis, tidak memeriksa kualitas jurnal/indexing, tidak menjamin kesesuaian sitasi, dan tidak memprediksi penerimaan.")

with tabs[16]:
    if st.button("Buat laporan Word"):
        doc=Document(); doc.add_heading("Research Analyzer Professional v3.3",0)
        doc.add_paragraph(f"Judul: {project}\nPeneliti: {researcher}\nDesain: {design}\nTanggal: {datetime.now():%d-%m-%Y %H:%M}")
        doc.add_heading("Ringkasan",1)
        doc.add_paragraph(f"Data kuantitatif: {len(st.session_state.data)} baris; unit kualitatif: {len(st.session_state.segments)}; coding: {len(st.session_state.codes)}.")
        for title,frame in [("Hasil SEM impor",st.session_state.sem),("Coding kualitatif",st.session_state.codes)]:
            doc.add_heading(title,1); doc.add_paragraph(frame.to_string(index=False) if not frame.empty else "Belum tersedia.")
        doc.add_heading("Joint display",1)
        doc.add_paragraph(pd.DataFrame(st.session_state.joint).to_string(index=False) if st.session_state.joint else "Belum tersedia.")
        doc.add_paragraph("Draf ini harus diverifikasi peneliti. Periksa asumsi, kualitas data, prosedur etik, interpretasi, dan sitasi.")
        b=BytesIO(); doc.save(b)
        st.download_button("Unduh laporan DOCX",b.getvalue(),"Research_Analyzer_v3.3_Report.docx")


with tabs[17]:
    st.subheader("AI Qualitative Intelligence & Mixed Methods — v3.5")
    st.caption("Saran berbasis TF-IDF adalah alat eksplorasi, bukan coding otomatis yang tervalidasi. Keputusan tetap pada peneliti.")
    seg=st.session_state.segments.copy()
    if not seg.empty:
        if "segment_id" not in seg: seg["segment_id"]=seg.get("id",pd.Series(range(1,len(seg)+1))).astype(str)
        if "text" not in seg: seg["text"]=""
        seg["segment_id"]=seg.segment_id.astype(str)
        st.metric("Segmen transkrip",len(seg))
        cb=st.session_state.get("v34_codebook",qa34.empty_codebook())
        if not cb.empty and {"code","definition"}.issubset(cb.columns):
            if st.button("Usulkan kode berbasis kemiripan teks",key="v35_suggest"):
                try:
                    st.session_state["v35_suggestions"]=qi35.suggest_codes_tfidf(seg.rename(columns={"id":"segment_id"}),cb,top_n=3,threshold=0.05)
                except Exception as e: st.error(str(e))
            sug=st.session_state.get("v35_suggestions",pd.DataFrame())
            if not sug.empty:
                st.markdown("**Usulan kode untuk ditinjau**")
                reviewed=st.data_editor(sug,num_rows="dynamic",use_container_width=True,key="v35_suggestion_editor")
                st.download_button("Unduh usulan coding CSV",reviewed.to_csv(index=False).encode("utf-8-sig"),"v35_coding_suggestions.csv","text/csv")
        else:
            st.info("Lengkapi codebook pada tab Advanced Qualitative (minimal kolom code dan definition).")
        cov=qi35.coding_coverage(seg.rename(columns={"id":"segment_id"}),st.session_state.codes)
        c1,c2,c3=st.columns(3); c1.metric("Segmen terkoding",cov["coded_segments"]); c2.metric("Belum terkoding",cov["uncoded_segments"]); c3.metric("Cakupan",f"{cov['coverage_pct']}%")
        st.markdown("**Kasus yang belum terhubung dengan coding (periksa sebagai kemungkinan kasus negatif/menyimpang)**")
        neg=qi35.negative_case_matrix(seg.rename(columns={"id":"segment_id"}),st.session_state.codes)
        st.dataframe(neg,use_container_width=True)
        st.download_button("Unduh daftar segmen belum terkoding",neg.to_csv(index=False).encode("utf-8-sig"),"v35_uncoded_segments.csv","text/csv")
        if not st.session_state.codes.empty:
            st.markdown("**Ko-kemunculan kode dalam segmen**")
            co=qi35.code_cooccurrence(st.session_state.codes)
            st.dataframe(co,use_container_width=True)
            st.download_button("Unduh matriks ko-kemunculan",co.to_csv().encode("utf-8-sig"),"v35_code_cooccurrence.csv","text/csv")
    else:
        st.info("Impor transkrip terlebih dahulu pada tab Kualitatif.")
    st.divider()
    st.markdown("**Joint display kuantitatif-kualitatif**")
    qfile=st.file_uploader("Unggah ringkasan hasil kuantitatif CSV (kolom construct/path dan beta/result)",type="csv",key="v35_qfile")
    lfile=st.file_uploader("Unggah ringkasan tema kualitatif CSV (kolom theme dan interpretation/evidence_quote)",type="csv",key="v35_lfile")
    if qfile is not None and lfile is not None:
        try:
            qdf=pd.read_csv(qfile); ldf=pd.read_csv(lfile)
            qkey=st.selectbox("Kunci kuantitatif",qdf.columns.tolist(),index=qdf.columns.tolist().index("construct") if "construct" in qdf else 0)
            lkey=st.selectbox("Kunci kualitatif",ldf.columns.tolist(),index=ldf.columns.tolist().index("theme") if "theme" in ldf else 0)
            jd=qi35.joint_display(qdf,ldf,qkey,lkey)
            jd_edit=st.data_editor(jd,use_container_width=True,key="v35_joint_edit")
            st.download_button("Unduh joint display",jd_edit.to_csv(index=False).encode("utf-8-sig"),"v35_joint_display.csv","text/csv")
        except Exception as e: st.error(f"Integrasi belum dapat dibuat: {e}")
    st.warning("Penyamaan label konstruk dan tema harus memiliki dasar konseptual. Kesesuaian nama tidak membuktikan hubungan substantif. Periksa kutipan asli, kasus negatif, konteks, serta bukti yang bertentangan sebelum menyimpulkan integrasi.")


with tabs[18]:
    st.subheader("SEM Results Import & Validation")
    st.caption("Impor hasil ekspor AMOS/lavaan/SmartPLS dalam CSV. Modul ini memvalidasi dan menata hasil impor; bukan menjalankan estimasi SEM.")
    semfile=st.file_uploader("Unggah CSV hasil SEM",type=["csv"],key="sem_v37_file")
    if semfile:
        try:
            raw=pd.read_csv(semfile)
            normalized=mm37.normalize_sem_paths(raw)
            st.session_state["sem_v37"]=normalized
            st.success("Hasil berhasil dibaca dan dinormalisasi.")
            st.dataframe(normalized,use_container_width=True)
            checks=mm37.sem_import_quality(raw)
            st.dataframe(checks,use_container_width=True)
            st.download_button("Unduh hasil normalisasi",normalized.to_csv(index=False).encode("utf-8-sig"),"sem_results_normalized_v37.csv")
        except Exception as e: st.error(str(e))
    elif "sem_v37" in st.session_state:
        st.dataframe(st.session_state["sem_v37"],use_container_width=True)
    else:
        st.info("Kolom minimum: path/jalur dan beta/estimate. Kolom t, p, serta CI bersifat opsional.")
    st.warning("Pastikan estimator, jenis koefisien (standardized/unstandardized), metode bootstrap, dan penanganan missing data dicatat dari perangkat lunak asal.")

with tabs[19]:
    st.subheader("Evidence-linked Mixed Methods Joint Display")
    st.caption("Hubungkan jalur kuantitatif, tema, kutipan/bukti kualitatif, dan penjelasan integratif yang ditulis peneliti.")
    qdf=st.session_state.get("sem_v37",pd.DataFrame())
    if qdf.empty:
        st.info("Unggah hasil SEM terlebih dahulu pada tab SEM Results Validation.")
    else:
        st.markdown("**1. Data kualitatif**")
        qfile=st.file_uploader("Unggah CSV bukti kualitatif (kolom theme dan evidence)",type=["csv"],key="qual_v37_file")
        qualdf=pd.read_csv(qfile) if qfile else pd.DataFrame(columns=["theme","evidence"])
        if not qualdf.empty: st.dataframe(qualdf,use_container_width=True)
        st.markdown("**2. Pemetaan integrasi**")
        paths=qdf.path.astype(str).tolist()
        themes=qualdf.theme.dropna().astype(str).unique().tolist() if not qualdf.empty else []
        with st.form("joint_v37_form"):
            chosen_path=st.selectbox("Jalur kuantitatif",paths)
            chosen_theme=st.text_input("Tema kualitatif")
            explanation=st.text_area("Penjelasan integratif peneliti",placeholder="Jelaskan apakah temuan kualitatif menjelaskan, memperluas, mengonfirmasi, atau bertentangan dengan hasil kuantitatif.")
            evidence_id=st.text_input("ID bukti/sumber",placeholder="Contoh: W01, OBS02, DOC03")
            add=st.form_submit_button("Tambahkan pemetaan")
        if add:
            mapping=pd.DataFrame([{"quant_path":chosen_path,"theme":chosen_theme,"explanation":explanation,"evidence_id":evidence_id}])
            st.session_state["mapping_v37"]=pd.concat([st.session_state.get("mapping_v37",pd.DataFrame()),mapping],ignore_index=True)
        mapping=st.session_state.get("mapping_v37",pd.DataFrame(columns=["quant_path","theme","explanation","evidence_id"]))
        if not mapping.empty:
            st.dataframe(mapping,use_container_width=True)
            if not qualdf.empty:
                try:
                    joint=mm37.build_joint_display(qdf,qualdf,mapping)
                    st.markdown("**3. Joint display**")
                    st.dataframe(joint,use_container_width=True)
                    st.download_button("Unduh joint display CSV",joint.to_csv(index=False).encode("utf-8-sig"),"joint_display_v37.csv")
                    st.markdown("**4. Draf narasi berbasis bukti**")
                    narrative=mm37.evidence_linked_narrative(joint)
                    st.text_area("Narasi untuk ditelaah peneliti",narrative,height=260)
                    st.download_button("Unduh draf narasi TXT",narrative.encode("utf-8"),"joint_display_narrative_v37.txt")
                except Exception as e: st.error(str(e))
            else:
                st.info("Unggah bukti kualitatif agar pemetaan dapat ditampilkan.")
        st.warning("Aplikasi tidak menyimpulkan integrasi secara otomatis. Periksa kutipan asli, konteks, kasus negatif, dan penjelasan peneliti sebelum memasukkan narasi ke manuskrip.")


# v4.0: explicit, user-initiated Crossref lookup and journal submission checks
import crossref_intelligence_v40 as cr40
import journal_submission_v40 as js40

with tabs[20]:
    st.subheader("Crossref Metadata Intelligence v4.0")
    st.caption("Verifikasi metadata DOI atau pencarian kandidat berdasarkan judul melalui Crossref REST API. Pencarian hanya berjalan setelah tombol ditekan.")
    mode = st.radio("Metode pencarian", ["Periksa DOI", "Cari berdasarkan judul"], horizontal=True, key="cr40_mode")
    if mode == "Periksa DOI":
        doi_input = st.text_input("DOI atau URL DOI", placeholder="10.xxxx/xxxxx atau https://doi.org/...")
        if st.button("Verifikasi metadata DOI", key="cr40_doi_btn"):
            try:
                result = cr40.lookup_doi(doi_input)
                st.session_state["cr40_result"] = result
                if result.get("match_status") == "matched": st.success("Metadata ditemukan di Crossref.")
                elif result.get("match_status") == "not_found": st.warning("DOI tidak ditemukan pada endpoint Crossref.")
                else: st.warning("Respons ditemukan, tetapi metadata DOI belum lengkap.")
            except Exception as e: st.error(str(e))
    else:
        title_input = st.text_input("Judul artikel", placeholder="Masukkan judul artikel secara lengkap")
        n_results = st.slider("Jumlah kandidat", 1, 10, 5, key="cr40_n")
        if st.button("Cari metadata berdasarkan judul", key="cr40_title_btn"):
            try:
                found = cr40.search_title(title_input, rows=n_results)
                st.session_state["cr40_candidates"] = pd.DataFrame(found)
                st.success(f"Crossref mengembalikan {len(found)} kandidat metadata.")
            except Exception as e: st.error(str(e))
    if st.session_state.get("cr40_result"):
        st.json(st.session_state["cr40_result"])
        st.caption("Metadata Crossref merupakan hasil pencocokan bibliografis, bukan bukti mutu jurnal, peer review, atau kesesuaian isi artikel.")
    candidates = st.session_state.get("cr40_candidates", pd.DataFrame())
    if not candidates.empty:
        st.dataframe(candidates, use_container_width=True)
        st.download_button("Unduh kandidat metadata CSV", candidates.to_csv(index=False).encode("utf-8-sig"), "crossref_candidates_v40.csv", "text/csv")
    st.divider()
    st.markdown("**Verifikasi daftar referensi secara batch**")
    ref_file = st.file_uploader("CSV dengan kolom doi dan/atau title", type="csv", key="cr40_batch")
    if ref_file:
        ref_df = pd.read_csv(ref_file)
        st.dataframe(ref_df.head(20), use_container_width=True)
        if st.button("Jalankan verifikasi batch", key="cr40_batch_btn"):
            if not ({"doi", "title"} & set(ref_df.columns)):
                st.error("CSV harus memiliki kolom doi dan/atau title.")
            else:
                with st.spinner("Menghubungi Crossref untuk setiap referensi..."):
                    rows = cr40.verify_reference_rows(ref_df.fillna("").to_dict("records"))
                out = pd.DataFrame(rows)
                st.session_state["cr40_batch_result"] = out
        out = st.session_state.get("cr40_batch_result", pd.DataFrame())
        if not out.empty:
            st.dataframe(out, use_container_width=True)
            st.download_button("Unduh hasil audit Crossref", out.to_csv(index=False).encode("utf-8-sig"), "crossref_reference_audit_v40.csv", "text/csv")
    st.warning("Jangan menganggap hasil title search sebagai identifikasi pasti. Cocokkan judul, penulis, tahun, jurnal, dan DOI dengan laman penerbit. Hindari mengunggah data partisipan atau naskah rahasia ke layanan eksternal.")

with tabs[21]:
    st.subheader("Journal Submission Assistant v4.0")
    st.caption("Checklist persiapan submit berdasarkan persyaratan yang dimasukkan pengguna; bukan validasi otomatis terhadap situs jurnal.")
    journal_name = st.text_input("Nama jurnal sasaran", key="js40_journal")
    with st.expander("Masukkan persyaratan khusus jurnal"):
        abs_limit = st.number_input("Batas kata abstrak (0 = tidak diperiksa)", min_value=0, max_value=2000, value=250)
        ms_limit = st.number_input("Batas kata manuskrip (0 = tidak diperiksa)", min_value=0, max_value=50000, value=8000)
        kw_min = st.number_input("Jumlah kata kunci minimum", min_value=0, max_value=20, value=3)
        kw_max = st.number_input("Jumlah kata kunci maksimum", min_value=0, max_value=20, value=6)
    abstract = st.text_area("Tempel abstrak", key="js40_abstract")
    manuscript = st.text_area("Tempel manuskrip atau bagian naskah untuk menghitung kata", height=180, key="js40_manuscript")
    keywords_text = st.text_input("Kata kunci (pisahkan dengan koma)", key="js40_keywords")
    if st.button("Periksa batas dan buat checklist", key="js40_check"):
        keywords = [x.strip() for x in keywords_text.split(",") if x.strip()]
        checks = js40.validate_user_requirements(manuscript, abstract, keywords,
            abstract_limit=abs_limit or None, manuscript_word_limit=ms_limit or None,
            keyword_min=kw_min if kw_min else None, keyword_max=kw_max if kw_max else None)
        st.session_state["js40_checks"] = checks
        st.session_state["js40_list"] = js40.build_submission_checklist(journal_name)
    checks = st.session_state.get("js40_checks", pd.DataFrame())
    if not checks.empty:
        st.dataframe(checks, use_container_width=True)
    checklist = st.session_state.get("js40_list", pd.DataFrame())
    if not checklist.empty:
        edited = st.data_editor(checklist, num_rows="dynamic", use_container_width=True, key="js40_editor")
        st.download_button("Unduh checklist submission CSV", edited.to_csv(index=False).encode("utf-8-sig"), "journal_submission_checklist_v40.csv", "text/csv")
    st.markdown("**Template deklarasi penulis**")
    st.text_area("Draf deklarasi — wajib disesuaikan dengan fakta penelitian", js40.declaration_template(), height=240)
    st.warning("Pernyataan etik, persetujuan, pendanaan, konflik kepentingan, ketersediaan data, dan kontribusi penulis harus akurat. Jangan mempertahankan deklarasi template yang tidak sesuai fakta.")


with tabs[22]:
    st.subheader("Advanced Research Diagnostics v4.1")
    st.caption("Pemeriksaan kuantitatif dan audit keterlacakan bukti kualitatif. Hasil bersifat diagnostik dan tidak menggantikan keputusan metodologis peneliti.")
    qtab, ltab = st.tabs(["Quantitative Diagnostics", "Qualitative Evidence Audit"])
    with qtab:
        qdata = st.session_state.get("data", pd.DataFrame())
        if qdata.empty:
            st.info("Impor dataset pada tab Data terlebih dahulu.")
        else:
            qitems = st.multiselect("Pilih indikator dalam satu konstruk", list(qdata.columns), key="v41_qitems")
            if st.button("Jalankan reliabilitas dan factorability", key="v41_qrun"):
                try:
                    rel = rd41.reliability_diagnostics(qdata, qitems)
                    fac = rd41.factorability_diagnostics(qdata, qitems)
                    st.session_state["v41_rel"] = rel
                    st.session_state["v41_fac"] = fac
                except Exception as e: st.error(str(e))
            if st.session_state.get("v41_rel"):
                rel=st.session_state["v41_rel"]; fac=st.session_state["v41_fac"]
                a,b,c=st.columns(3); a.metric("Cronbach's alpha",f"{rel['cronbach_alpha']:.3f}"); b.metric("KMO",f"{fac['kmo']:.3f}"); c.metric("Bartlett p-value",f"{fac['bartlett_p']:.4g}")
                st.dataframe(rel["items"],use_container_width=True)
                st.json({k:v for k,v in fac.items() if k not in ["note"]}); st.caption(fac["note"])
                st.download_button("Unduh diagnostik item CSV",rel["items"].to_csv(index=False).encode("utf-8-sig"),"v41_item_diagnostics.csv","text/csv")
    with ltab:
        seg=st.session_state.get("segments",pd.DataFrame()).copy()
        codes=st.session_state.get("codes",pd.DataFrame()).copy()
        if not seg.empty and "segment_id" not in seg and "id" in seg: seg=seg.rename(columns={"id":"segment_id"})
        if st.button("Audit keterlacakan coding",key="v41_lrun"):
            try: st.session_state["v41_audit"]=rd41.qualitative_evidence_audit(seg,codes)
            except Exception as e: st.error(str(e))
        audit=st.session_state.get("v41_audit")
        if audit:
            st.json(audit["summary"])
            st.markdown("**Frekuensi kode**"); st.dataframe(audit["code_frequency"],use_container_width=True)
            st.markdown("**Segmen belum terkoding — perlu ditinjau, bukan otomatis dianggap kasus negatif**")
            st.dataframe(audit["uncoded_segments"],use_container_width=True)
            st.download_button("Unduh segmen belum terkoding CSV",audit["uncoded_segments"].to_csv(index=False).encode("utf-8-sig"),"v41_uncoded_segments.csv","text/csv")
        st.warning("Cakupan coding hanya menunjukkan proporsi segmen yang memiliki kode. Angka ini bukan ukuran saturasi teoretis, kualitas tema, atau validitas temuan.")


with tabs[-1]:
    st.subheader("SEM Inference & Diagnostics v4.2")
    st.caption("Mediasi dan moderasi berbasis skor teramati dengan bootstrap; bukan estimasi latent-variable SEM.")
    df=st.session_state.data
    if df.empty:
        st.info("Impor data responden CSV pada tab Data terlebih dahulu.")
    else:
        numeric=df.select_dtypes(include=np.number).columns.tolist()
        mode=st.selectbox("Analisis",["Mediasi satu mediator","Moderasi satu interaksi","VIF prediktor","Simple slopes"])
        if mode=="Mediasi satu mediator":
            c1,c2,c3=st.columns(3)
            x=c1.selectbox("Prediktor X",numeric,key="v42_mx")
            m=c2.selectbox("Mediator M",[v for v in numeric if v!=x],key="v42_mm")
            y=c3.selectbox("Outcome Y",[v for v in numeric if v not in [x,m]],key="v42_my")
            boots=st.select_slider("Replikasi bootstrap",options=[200,500,1000,2000],value=1000,key="v42_mb")
            if st.button("Jalankan mediasi bootstrap",key="v42_mrun"):
                try:
                    r=si42.mediation_bootstrap(df,x,m,y,n_boot=int(boots))
                    st.json(r)
                    st.download_button("Unduh hasil mediasi JSON",json.dumps(r,indent=2,ensure_ascii=False),"mediation_v42.json")
                except Exception as e: st.error(str(e))
        elif mode=="Moderasi satu interaksi":
            c1,c2,c3=st.columns(3)
            x=c1.selectbox("Prediktor X",numeric,key="v42_rx")
            w=c2.selectbox("Moderator W",[v for v in numeric if v!=x],key="v42_rw")
            y=c3.selectbox("Outcome Y",[v for v in numeric if v not in [x,w]],key="v42_ry")
            boots=st.select_slider("Replikasi bootstrap",options=[200,500,1000,2000],value=1000,key="v42_rb")
            if st.button("Jalankan moderasi bootstrap",key="v42_rrun"):
                try:
                    r=si42.moderation_bootstrap(df,x,w,y,n_boot=int(boots))
                    st.json(r)
                    st.dataframe(si42.simple_slopes(df,x,w,y),use_container_width=True)
                    st.download_button("Unduh hasil moderasi JSON",json.dumps(r,indent=2,ensure_ascii=False),"moderation_v42.json")
                except Exception as e: st.error(str(e))
        elif mode=="VIF prediktor":
            preds=st.multiselect("Pilih prediktor (minimal dua)",numeric,key="v42_vif")
            if st.button("Hitung VIF",key="v42_vifrun"):
                try: st.dataframe(si42.vif_diagnostics(df,preds),use_container_width=True)
                except Exception as e: st.error(str(e))
        else:
            c1,c2,c3=st.columns(3)
            x=c1.selectbox("Prediktor X",numeric,key="v42_sx")
            w=c2.selectbox("Moderator W",[v for v in numeric if v!=x],key="v42_sw")
            y=c3.selectbox("Outcome Y",[v for v in numeric if v not in [x,w]],key="v42_sy")
            if st.button("Hitung simple slopes",key="v42_srun"):
                try: st.dataframe(si42.simple_slopes(df,x,w,y),use_container_width=True)
                except Exception as e: st.error(str(e))
    st.warning("Interpretasikan hasil berdasarkan teori, desain, asumsi, dan kualitas pengukuran. Bootstrap CI bukan bukti kausalitas; analisis ini menggunakan skor teramati, bukan konstruk laten.")


with tabs[-1]:
    st.subheader("CFA & CB-SEM Engine v4.3")
    st.caption("Diagnostik model pengukuran dan jembatan eksekusi CB-SEM melalui R/lavaan.")
    st.warning("CR/AVE dan validitas diskriminan bergantung pada kualitas input serta spesifikasi model. Batas fit adalah heuristik, bukan aturan universal.")
    load_file=st.file_uploader("Impor tabel standardized factor loadings (CSV)",type="csv",key="v43_loadings")
    if load_file:
        try:
            ld=pd.read_csv(load_file)
            st.dataframe(ld,use_container_width=True)
            if st.button("Hitung CR dan AVE",key="v43_quality"):
                q=cfa43.measurement_quality(ld)
                st.dataframe(q,use_container_width=True)
                st.download_button("Unduh CR-AVE CSV",q.to_csv(index=False),"cfa_quality_v43.csv")
        except Exception as e: st.error(str(e))
    with st.expander("HTMT dan Cronbach's alpha dari data indikator"):
        mapping_text=st.text_area("Peta konstruk-indikator dalam JSON",value='{"Konstruk_A":["A1","A2","A3"],"Konstruk_B":["B1","B2","B3"]}',key="v43_map")
        if st.button("Hitung alpha dan HTMT",key="v43_htmt"):
            try:
                mp=json.loads(mapping_text)
                d=st.session_state.data
                if d.empty: st.error("Impor data responden pada tab Data terlebih dahulu.")
                else:
                    st.markdown("**Cronbach's alpha**")
                    st.dataframe(cfa43.cronbach_alpha(d,mp),use_container_width=True)
                    st.markdown("**HTMT matrix**")
                    st.dataframe(cfa43.htmt_matrix(d,mp),use_container_width=True)
            except Exception as e: st.error(str(e))
    with st.expander("Fornell-Larcker"):
        st.caption("Masukkan AVE per konstruk dan matriks korelasi konstruk dalam format CSV; diagonal akan diganti akar kuadrat AVE.")
        ave_file=st.file_uploader("Tabel AVE (kolom construct, average_variance_extracted)",type="csv",key="v43_ave")
        corr_file=st.file_uploader("Matriks korelasi konstruk (CSV; kolom pertama berisi nama konstruk)",type="csv",key="v43_corr")
        if ave_file and corr_file and st.button("Buat matriks Fornell-Larcker",key="v43_fl"):
            try:
                av=pd.read_csv(ave_file)
                co=pd.read_csv(corr_file,index_col=0)
                fl=cfa43.fornell_larcker(av,co)
                st.dataframe(fl,use_container_width=True)
                st.download_button("Unduh Fornell-Larcker CSV",fl.to_csv(),"fornell_larcker_v43.csv")
            except Exception as e: st.error(str(e))
    st.divider()
    st.markdown("**CB-SEM dengan R/lavaan (opsional)**")
    st.caption("Memerlukan R, paket lavaan, dan Rscript terpasang pada komputer yang menjalankan aplikasi.")
    syntax=st.text_area("Sintaks lavaan",value="F1 =~ item1 + item2 + item3\nF2 =~ item4 + item5 + item6\nF2 ~ F1",height=140,key="v43_lavaan_syntax")
    estimator=st.selectbox("Estimator",["ML","MLR","WLSMV","DWLS"],key="v43_estimator")
    ordered_text=st.text_input("Kolom ordinal untuk WLSMV/DWLS (pisahkan koma; opsional)",key="v43_ordered")
    if st.button("Jalankan CB-SEM melalui lavaan",key="v43_run_lavaan"):
        try:
            if st.session_state.data.empty: st.error("Impor data responden pada tab Data terlebih dahulu.")
            else:
                result=cfa43.run_lavaan(st.session_state.data,syntax,estimator,
                    [x.strip() for x in ordered_text.split(",") if x.strip()] or None)
                st.success(f"lavaan berhasil dijalankan: N={result['n']}, estimator={result['estimator']}")
                st.markdown("**Fit indices**")
                fit=result["fit_indices"]
                st.dataframe(fit,use_container_width=True)
                fitdict=dict(zip(fit["index"],fit["value"]))
                audit=cfa43.audit_fit_indices(fitdict)
                st.dataframe(audit,use_container_width=True)
                st.markdown("**Parameter estimates**")
                st.dataframe(result["parameters"],use_container_width=True)
                st.download_button("Unduh parameter estimates CSV",result["parameters"].to_csv(index=False),"lavaan_parameters_v43.csv")
                st.download_button("Unduh fit indices CSV",fit.to_csv(index=False),"lavaan_fit_indices_v43.csv")
        except Exception as e: st.error(str(e))


with tabs[-1]:
    st.subheader("Advanced CB-SEM & Higher-Order Construct v4.4")
    st.caption("Pembangun sintaks CFA/HOC, pemeriksaan struktur sintaks, interpretasi parameter lavaan, dan ekspor diagram jalur Graphviz DOT.")
    st.warning("HOC yang disediakan adalah model reflektif tingkat kedua (second-order reflective). Spesifikasi tetap harus ditentukan berdasarkan teori. Diagram DOT adalah kode sumber diagram, bukan gambar yang telah dirender.")
    with st.expander("1. Bangun sintaks CFA otomatis", expanded=True):
        cfa_map_text=st.text_area("Peta konstruk dan indikator (JSON)", value='{"SelfLeadership":["SL1","SL2","SL3"],"SchoolClimate":["SC1","SC2","SC3"]}', key="v44_cfa_map")
        if st.button("Buat sintaks CFA", key="v44_make_cfa"):
            try:
                st.code(cb44.build_cfa_syntax(json.loads(cfa_map_text)), language="text")
            except Exception as e: st.error(str(e))
    with st.expander("2. Bangun sintaks konstruk tingkat tinggi (HOC)"):
        hoc_map_text=st.text_area("Peta konstruk tingkat pertama dan indikator", value='{"SelfAwareness":["SA1","SA2","SA3"],"SelfRegulation":["SR1","SR2","SR3"],"SelfMotivation":["SM1","SM2","SM3"],"SchoolClimateSupport":["SCS1","SCS2","SCS3"],"SchoolClimateParticipation":["SCP1","SCP2","SCP3"]}', key="v44_hoc_map")
        hoc_text=st.text_area("Peta HOC (JSON)", value='{"SelfLeadership":["SelfAwareness","SelfRegulation","SelfMotivation"],"SchoolClimate":["SchoolClimateSupport","SchoolClimateParticipation"]}', key="v44_hoc")
        paths_text=st.text_area("Jalur struktural (JSON; opsional)", value='{"CharacterDevelopment":["SelfLeadership","SchoolClimate"]}', key="v44_paths")
        if st.button("Bangun sintaks HOC + struktural", key="v44_make_hoc"):
            try:
                syn=cb44.build_hoc_syntax(json.loads(hoc_map_text),json.loads(hoc_text),json.loads(paths_text) if paths_text.strip() else None)
                st.code(syn,language="text")
                st.download_button("Unduh sintaks lavaan",syn,"hoc_model_v44.lav",key="v44_dl_hoc")
            except Exception as e: st.error(str(e))
    with st.expander("3. Audit sintaks lavaan"):
        syn_audit=st.text_area("Tempel sintaks untuk diperiksa", value="F1 =~ item1 + item2 + item3\nF2 =~ item4 + item5 + item6\nF2 ~ F1", key="v44_audit_syntax")
        if st.button("Periksa struktur sintaks",key="v44_validate"):
            try:
                audit=cb44.validate_lavaan_syntax(syn_audit, list(st.session_state.data.columns) if not st.session_state.data.empty else None)
                st.json(audit)
            except Exception as e: st.error(str(e))
    with st.expander("4. Interpretasi parameter dan diagram hasil lavaan"):
        pe_file=st.file_uploader("Impor parameterEstimates lavaan CSV",type="csv",key="v44_pe")
        fit_file=st.file_uploader("Impor fit indices CSV (kolom index,value)",type="csv",key="v44_fit")
        alpha=st.number_input("Ambang signifikansi",min_value=0.001,max_value=0.20,value=0.05,step=0.005,key="v44_alpha")
        if pe_file:
            try:
                pe=pd.read_csv(pe_file)
                interpreted=cb44.interpret_lavaan_parameters(pe,alpha)
                st.dataframe(interpreted,use_container_width=True)
                st.download_button("Unduh interpretasi parameter CSV",interpreted.to_csv(index=False),"lavaan_interpretation_v44.csv",key="v44_dl_interpret")
                dot=cb44.lavaan_path_dot(pe)
                st.download_button("Unduh diagram jalur (Graphviz DOT)",dot,"sem_path_diagram_v44.dot",key="v44_dl_dot")
                if fit_file:
                    summary=cb44.build_cbsem_results_summary(pd.read_csv(fit_file),pe,alpha)
                    st.markdown("**Ringkasan indeks fit**")
                    st.write(summary['fit_text'])
                    st.write(f"Jalur struktural: {summary['structural_paths']}; jalur dengan p < {alpha}: {summary['significant_paths']}.")
            except Exception as e: st.error(str(e))
    st.info("Untuk menjalankan estimasi CFA/CB-SEM, gunakan tab v4.3 dan komputer yang memiliki R + lavaan. Modul ini menyusun sintaks dan mengolah keluaran lavaan; tidak menggantikan estimasi statistik atau evaluasi peneliti.")

with st.expander("PLS Predictive Assessment v4.5 — Cross-validation", expanded=False):
    st.caption("Evaluasi prediksi out-of-fold pada skor konstruk endogen. Metode ini eksploratif dan bukan replikasi identik PLSpredict SmartPLS.")
    pred_file = st.file_uploader("Unggah data indikator (CSV)", type=["csv"], key="v45_predict_data")
    pred_map_text = st.text_area("Peta konstruk dan indikator (JSON)", value='{"X":["x1","x2"],"M":["m1","m2"],"Y":["y1","y2"]}', key="v45_predict_map")
    pred_paths = st.text_area("Jalur struktural (satu jalur per baris)", value="X -> M\nM -> Y\nX -> Y", key="v45_predict_paths")
    c1,c2,c3=st.columns(3)
    with c1: pred_folds=st.number_input("Jumlah fold",min_value=2,max_value=10,value=5,key="v45_folds")
    with c2: pred_repeats=st.number_input("Pengulangan",min_value=1,max_value=20,value=3,key="v45_repeats")
    with c3: pred_seed=st.number_input("Seed",min_value=1,value=2026,key="v45_seed")
    if st.button("Jalankan validasi prediktif",key="v45_run"):
        try:
            import json
            from pls_predictive_v45 import cross_validated_pls_predict
            if pred_file is None: raise ValueError("Unggah data CSV terlebih dahulu.")
            result=cross_validated_pls_predict(pd.read_csv(pred_file),json.loads(pred_map_text),pred_paths,int(pred_folds),int(pred_repeats),int(pred_seed))
            st.dataframe(result["summary"],use_container_width=True)
            st.download_button("Unduh ringkasan prediksi CSV",result["summary"].to_csv(index=False),"pls_predictive_summary_v45.csv","text/csv")
            st.download_button("Unduh prediksi out-of-fold CSV",result["predictions"].to_csv(index=False),"pls_predictive_predictions_v45.csv","text/csv")
            st.json(result["settings"])
        except Exception as exc: st.error(str(exc))


with st.expander("PLS Indicator-level Prediction v4.6", expanded=False):
    st.caption("Prediksi out-of-fold pada indikator konstruk endogen, dibandingkan dengan benchmark regresi linear (LM) dan rerata training. Ini prosedur eksploratif, bukan replika identik PLSpredict SmartPLS.")
    f46=st.file_uploader("Data indikator CSV", type=["csv"], key="v46_indicator_data")
    m46=st.text_area("Peta konstruk-indikator JSON", value='{"X":["x1","x2"],"M":["m1","m2"],"Y":["y1","y2"]}', key="v46_indicator_map")
    p46=st.text_area("Jalur struktural", value="X -> M\nM -> Y\nX -> Y", key="v46_indicator_paths")
    c46a,c46b,c46c=st.columns(3)
    with c46a: k46=st.number_input("Fold",min_value=2,max_value=10,value=5,key="v46_folds")
    with c46b: r46=st.number_input("Pengulangan",min_value=1,max_value=20,value=3,key="v46_repeats")
    with c46c: sd46=st.number_input("Seed",min_value=1,value=2026,key="v46_seed")
    if st.button("Jalankan prediksi indikator",key="v46_run"):
        try:
            import json
            if f46 is None: raise ValueError("Unggah data CSV terlebih dahulu.")
            out46=indicator_level_pls_predict(pd.read_csv(f46),json.loads(m46),p46,int(k46),int(r46),int(sd46))
            st.dataframe(out46["summary"],use_container_width=True)
            st.download_button("Unduh ringkasan indikator",out46["summary"].to_csv(index=False),"pls_indicator_prediction_v46.csv","text/csv")
            st.download_button("Unduh seluruh prediksi",out46["predictions"].to_csv(index=False),"pls_indicator_predictions_v46.csv","text/csv")
            st.json(out46["settings"])
        except Exception as e: st.error(str(e))

with st.expander("Multi-Group Analysis Advanced v4.7 — Bootstrap CI & MICOM-inspired", expanded=False):
    st.caption("Perbandingan dua kelompok dengan bootstrap CI selisih koefisien jalur dan uji permutasi. Gunakan MICOM canonical untuk keputusan invariansi formal.")
    import json as _json47
    gfile47=st.file_uploader("CSV data multigroup",type=["csv"],key="v47_group_file")
    map47=st.text_area("Peta konstruk-indikator JSON",value='{"X":["x1","x2"],"Y":["y1","y2"]}',key="v47_map")
    paths47=st.text_area("Jalur struktural",value="X -> Y",key="v47_paths")
    group47=st.text_input("Nama kolom kelompok",value="group",key="v47_group_col")
    c47a,c47b=st.columns(2)
    with c47a: boots47=st.number_input("Bootstrap",min_value=100,max_value=5000,value=1000,step=100,key="v47_boot")
    with c47b: perms47=st.number_input("Permutasi",min_value=99,max_value=5000,value=499,step=100,key="v47_perm")
    if st.button("Jalankan MICOM-inspired + MGA",key="v47_run"):
        try:
            from multigroup_inference_v47 import multigroup_invariance_report
            if gfile47 is None: raise ValueError("Unggah data CSV terlebih dahulu.")
            result47=multigroup_invariance_report(pd.read_csv(gfile47),_json47.loads(map47),paths47,group47,int(boots47),int(perms47))
            st.subheader("Pemeriksaan invariansi pengukuran")
            st.dataframe(result47["invariance"],use_container_width=True)
            st.subheader("Multi-Group Analysis")
            st.dataframe(result47["mga"],use_container_width=True)
            st.download_button("Unduh hasil MGA CSV",result47["mga"].to_csv(index=False),"mga_bootstrap_v47.csv","text/csv")
            st.download_button("Unduh hasil invariansi CSV",result47["invariance"].to_csv(index=False),"micom_inspired_v47.csv","text/csv")
            st.json(result47["settings"])
        except Exception as e: st.error(str(e))


with st.expander("Mixed Methods Evidence Integration v4.8", expanded=False):
    st.caption("Hubungkan jalur kuantitatif dengan tema dan ID bukti kualitatif. Sistem memeriksa tautan; peneliti tetap menentukan meta-inferensi.")
    qf48=st.file_uploader("Hasil kuantitatif CSV (kolom path, beta, opsional p)",type=["csv"],key="v48_quant")
    lf48=st.file_uploader("Bukti kualitatif CSV (theme, evidence_id, evidence; opsional source, technique)",type=["csv"],key="v48_qual")
    mf48=st.file_uploader("Pemetaan integrasi CSV (quant_path, theme, evidence_id, integration_rationale)",type=["csv"],key="v48_map")
    if st.button("Bangun joint display dan audit",key="v48_run"):
        try:
            if not all([qf48,lf48,mf48]): raise ValueError("Unggah ketiga file CSV.")
            j48=build_evidence_linked_joint_display(pd.read_csv(qf48),pd.read_csv(lf48),pd.read_csv(mf48))
            a48=integration_audit(j48)
            sm48=summarize_integration_by_path(j48)
            st.subheader("Evidence-linked joint display")
            st.dataframe(j48,use_container_width=True)
            st.subheader("Audit integrasi")
            st.dataframe(a48,use_container_width=True)
            st.subheader("Ringkasan per jalur")
            st.dataframe(sm48,use_container_width=True)
            st.download_button("Unduh joint display CSV",j48.to_csv(index=False),"joint_display_v48.csv","text/csv")
            st.download_button("Unduh audit CSV",a48.to_csv(index=False),"integration_audit_v48.csv","text/csv")
            st.download_button("Unduh ringkasan CSV",sm48.to_csv(index=False),"integration_summary_v48.csv","text/csv")
            st.text_area("Narasi awal untuk ditelaah dan dilengkapi peneliti",export_integration_narrative(sm48),height=240)
        except Exception as e: st.error(str(e))


with st.expander("Advanced Qualitative Case Analysis v4.9", expanded=False):
    st.caption("Analisis per informan, perbandingan lintas kasus, bukti pendukung/kasus negatif, audit coding, dan akumulasi kode per gelombang. Angka bersifat deskriptif; keputusan tematik tetap oleh peneliti.")
    qs49=st.file_uploader("Data segmen CSV (segment_id, source, participant, text; opsional wave)",type=["csv"],key="v49_segments")
    qc49=st.file_uploader("Data coding CSV (segment_id, code, theme; opsional evidence_type, analytic_memo, evidence_quote, researcher_status)",type=["csv"],key="v49_coding")
    if st.button("Jalankan analisis kualitatif lanjutan",key="v49_run"):
        try:
            if not qs49 or not qc49: raise ValueError("Unggah data segmen dan coding.")
            ds49=pd.read_csv(qs49); dc49=pd.read_csv(qc49)
            st.subheader("Matriks informan × tema")
            im49=informant_theme_matrix(ds49,dc49); st.dataframe(im49,use_container_width=True)
            st.download_button("Unduh matriks informan",im49.to_csv(index=False),"informant_theme_matrix_v49.csv","text/csv")
            st.subheader("Perbandingan lintas kasus")
            cc49=cross_case_theme_comparison(ds49,dc49); st.dataframe(cc49,use_container_width=True)
            st.download_button("Unduh perbandingan kasus",cc49.to_csv(index=False),"cross_case_comparison_v49.csv","text/csv")
            st.subheader("Profil bukti dan kasus negatif")
            ep49=theme_evidence_profile(ds49,dc49); st.dataframe(ep49,use_container_width=True)
            st.download_button("Unduh profil bukti",ep49.to_csv(index=False),"theme_evidence_profile_v49.csv","text/csv")
            st.subheader("Audit kualitas proses coding")
            au49=qualitative_audit(ds49,dc49); st.dataframe(au49,use_container_width=True)
            ur49=uncoded_evidence_review(ds49,dc49)
            st.subheader("Segmen belum terkoding")
            st.dataframe(ur49,use_container_width=True)
            st.download_button("Unduh segmen untuk review",ur49.to_csv(index=False),"uncoded_evidence_review_v49.csv","text/csv")
            if "wave" in ds49.columns:
                st.subheader("Akumulasi kode per gelombang")
                sat49=saturation_sequence_audit(ds49,dc49)
                st.dataframe(sat49,use_container_width=True)
                st.download_button("Unduh audit gelombang",sat49.to_csv(index=False),"code_accumulation_waves_v49.csv","text/csv")
            else:
                st.info("Tambahkan kolom wave pada data segmen untuk melihat akumulasi kode per gelombang wawancara.")
        except Exception as e: st.error(str(e))


with st.expander("v5.0 — AI-Assisted Qualitative Coding", expanded=False):
    st.caption("Saran kode berbasis TF-IDF atau multilingual embeddings. Semua saran berstatus pending sampai ditinjau peneliti; bukan pengodean otomatis.")
    s50=st.file_uploader("Segmen CSV (segment_id, text)",type=["csv"],key="v50_ai_segments")
    c50=st.file_uploader("Codebook CSV (code, definition)",type=["csv"],key="v50_ai_codebook")
    method50=st.selectbox("Metode saran",["TF-IDF lexical similarity","Multilingual sentence embeddings"],key="v50_method")
    n50=st.number_input("Jumlah saran per segmen",1,10,3,key="v50_topn")
    threshold50=st.slider("Ambang similarity",0.0,1.0,0.05,0.01,key="v50_threshold")
    if st.button("Hasilkan saran kode",key="v50_suggest"):
        try:
            if not s50 or not c50: raise ValueError("Unggah segmen dan codebook.")
            ds50=pd.read_csv(s50); dc50=pd.read_csv(c50)
            method="tfidf" if method50.startswith("TF-IDF") else "multilingual_embedding"
            sug50=suggest_qualitative_codes(ds50,dc50,method=method,top_n=int(n50),threshold=float(threshold50))
            st.session_state["v50_suggestions"]=sug50
            st.session_state["v50_segments"]=ds50
        except Exception as e: st.error(str(e))
    if "v50_suggestions" in st.session_state:
        sug=st.session_state["v50_suggestions"]
        st.dataframe(sug,use_container_width=True)
        st.download_button("Unduh saran kode untuk review",sug.to_csv(index=False),"qualitative_code_suggestions_v50.csv","text/csv")
        st.caption("Keputusan peneliti dapat diunggah pada sesi berikutnya melalui CSV: segment_id, suggested_code, decision, reviewer.")
        dec50=st.file_uploader("Keputusan peneliti CSV (opsional)",type=["csv"],key="v50_decisions")
        if dec50:
            try:
                reviewed=apply_researcher_decisions(sug,pd.read_csv(dec50))
                st.dataframe(reviewed,use_container_width=True)
                st.download_button("Unduh hasil review",reviewed.to_csv(index=False),"qualitative_code_review_v50.csv","text/csv")
                st.json(codebook_coverage(reviewed,st.session_state.get("v50_segments")))
            except Exception as e: st.error(str(e))

with st.expander("v5.0 — Mixed Methods Meta-Inference", expanded=False):
    st.caption("Masukkan keputusan integrasi yang dibuat peneliti. Sistem memeriksa kelengkapan dan menyiapkan narasi yang dapat ditelaah.")
    j50=st.file_uploader("Joint display CSV (quant_path, beta, p, theme, evidence_id, evidence)",type=["csv"],key="v50_joint")
    d50=st.file_uploader("Keputusan meta-inference CSV (quant_path, relationship, meta_inference, researcher, evidence_basis)",type=["csv"],key="v50_meta")
    if st.button("Audit meta-inference",key="v50_meta_run"):
        try:
            if not j50 or not d50: raise ValueError("Unggah joint display dan keputusan peneliti.")
            mt=build_meta_inference_table(pd.read_csv(j50),pd.read_csv(d50))
            st.session_state["v50_meta_table"]=mt
        except Exception as e: st.error(str(e))
    if "v50_meta_table" in st.session_state:
        mt=st.session_state["v50_meta_table"]
        st.dataframe(mt,use_container_width=True)
        st.dataframe(integration_completeness(mt),use_container_width=True)
        st.text_area("Narasi integrasi untuk ditelaah",meta_inference_narrative(mt),height=220)
        st.download_button("Unduh meta-inference CSV",mt.to_csv(index=False),"meta_inference_v50.csv","text/csv")

with st.expander("v5.0 — Automatic Academic Report (Word)", expanded=False):
    st.caption("Menyusun dokumen Bab IV–V dari tabel dan narasi yang diunggah peneliti. Tidak membuat statistik, kutipan, teori, atau referensi baru.")
    title50=st.text_input("Judul penelitian",key="v50_report_title")
    context50=st.text_area("Konteks penelitian",key="v50_report_context")
    methodnote50=st.text_area("Catatan metode dan prosedur analisis",key="v50_report_method")
    chapterv50=st.text_area("Isi Bab V: kesimpulan, implikasi, keterbatasan, rekomendasi",key="v50_report_chapterv")
    q50=st.file_uploader("Tabel kuantitatif CSV (opsional)",type=["csv"],key="v50_report_quant")
    l50=st.file_uploader("Tabel kualitatif CSV (opsional)",type=["csv"],key="v50_report_qual")
    jd50=st.file_uploader("Joint display CSV (opsional)",type=["csv"],key="v50_report_joint")
    mi50=st.file_uploader("Meta-inference CSV (opsional)",type=["csv"],key="v50_report_meta")
    if st.button("Buat laporan Word",key="v50_docx"):
        try:
            import tempfile, os
            frames=[pd.read_csv(f) if f else None for f in [q50,l50,jd50,mi50]]
            with tempfile.NamedTemporaryFile(suffix=".docx",delete=False) as tmp:
                path=tmp.name
            build_academic_report_docx(path,title50,context50,methodnote50,
                quantitative=frames[0],qualitative=frames[1],joint_display=frames[2],
                meta_inference=frames[3],chapter_v=chapterv50)
            with open(path,"rb") as fh: st.download_button("Unduh laporan Bab IV–V (DOCX)",fh.read(),"Research_Analyzer_Report_v50.docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            os.unlink(path)
        except Exception as e: st.error(str(e))


# ---------------------------------------------------------------------------
# WEB v6.0: portable project workspace and extensibility
# ---------------------------------------------------------------------------
from web_workspace import create_project_bundle, read_project_bundle, discover_extensions

with tabs[26]:
    st.subheader("Workspace & Manajemen Proyek")
    st.write("Simpan data kerja penelitian menjadi satu paket proyek yang dapat dipindahkan, diarsipkan, dan dibuka kembali.")
    project_meta = {
        "title": project,
        "researcher": researcher,
        "design": design,
        "alpha": float(alpha),
        "application_version": "6.0"
    }
    frames_to_save = {
        "quantitative_data": st.session_state.get("data"),
        "qualitative_segments": st.session_state.get("segments"),
        "qualitative_codes": st.session_state.get("codes"),
        "sem_results": st.session_state.get("sem"),
    }
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Siapkan paket proyek (.zip)", key="v60_export_project"):
            try:
                bundle = create_project_bundle(project_meta, frames_to_save,
                    notes={"notice": "Anonimkan data sebelum dibagikan."})
                st.session_state["_v60_project_bundle"] = bundle
                st.success("Paket proyek berhasil disiapkan.")
            except Exception as exc:
                st.error(f"Gagal membuat paket proyek: {exc}")
        if "_v60_project_bundle" in st.session_state:
            st.download_button("Unduh paket proyek", st.session_state["_v60_project_bundle"],
                file_name="research_project_v6.zip", mime="application/zip")
    with c2:
        uploaded_project = st.file_uploader("Buka paket proyek (.zip)", type=["zip"], key="v60_import_project")
        if uploaded_project and st.button("Validasi dan muat proyek", key="v60_load_project"):
            try:
                manifest, restored = read_project_bundle(uploaded_project.getvalue())
                mapping = {
                    "quantitative_data": "data",
                    "qualitative_segments": "segments",
                    "qualitative_codes": "codes",
                    "sem_results": "sem"
                }
                for dataset_name, state_name in mapping.items():
                    if dataset_name in restored:
                        st.session_state[state_name] = restored[dataset_name]
                st.session_state["_v60_loaded_manifest"] = manifest
                st.success("Dataset proyek dimuat ke sesi aktif. Periksa kembali variabel sebelum analisis.")
                st.json(manifest.get("metadata", {}))
                st.rerun()
            except Exception as exc:
                st.error(f"Paket proyek tidak dapat dibuka: {exc}")
    st.warning("Paket proyek menyimpan dataset yang sedang berada di memori sesi. File sumber, kredensial, dan hasil unduhan yang tidak dimasukkan secara eksplisit tidak ikut disimpan.")
    st.caption("Untuk penggunaan multi-pengguna permanen, tahap berikutnya memerlukan database, manajemen akun individual, backup, dan kontrol akses berbasis peran.")

with tabs[27]:
    st.subheader("Developer Studio — fasilitas pengembangan")
    st.write("Arsitektur modular disiapkan agar pengembang dapat menambahkan analisis baru tanpa menimpa modul inti.")
    st.markdown("""
    **Struktur pengembangan**
    - `app.py` — antarmuka utama Streamlit.
    - `*_vXX.py` — modul analisis dengan versi terpisah.
    - `extensions/` — ruang pengembangan modul tambahan.
    - `tests/` — pengujian otomatis.
    - `docs/` — dokumentasi metodologi dan batasan.
    """)
    ext_list = discover_extensions("extensions")
    st.dataframe(pd.DataFrame(ext_list) if ext_list else pd.DataFrame(columns=["name","file","bytes"]),
                 use_container_width=True)
    st.info("Extension hanya dideteksi, tidak dieksekusi otomatis. Integrasi harus melalui peninjauan kode dan pengujian untuk mencegah eksekusi kode yang tidak tepercaya.")
    st.markdown("**Siklus penambahan fitur**")
    st.code("1. Buat extensions/nama_modul.py\n2. Tambahkan validasi input dan dokumentasi\n3. Buat tests/test_nama_modul.py\n4. Jalankan: python -m unittest discover -s tests -v\n5. Integrasikan secara eksplisit ke app.py\n6. Uji kembali sebelum deployment", language="text")
    st.download_button("Unduh template extension",
        (Path("extensions/example_extension.py").read_bytes()),
        file_name="example_extension.py", mime="text/x-python")
