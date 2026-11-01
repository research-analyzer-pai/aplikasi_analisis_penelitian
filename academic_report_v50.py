"""Evidence-traceable academic report generator for v5.0."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

def build_academic_report_docx(output_path, title, study_context, method_note,
        quantitative=None, qualitative=None, joint_display=None, meta_inference=None,
        chapter_v=None, appendices=None):
    try:
        from docx import Document
        from docx.shared import Pt, Cm
    except ImportError as e:
        raise ImportError("Instal python-docx.") from e
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=Cm(2.5); sec.bottom_margin=Cm(2.5)
    sec.left_margin=Cm(3); sec.right_margin=Cm(2.5)
    styles=doc.styles
    styles["Normal"].font.name="Times New Roman"
    styles["Normal"].font.size=Pt(12)
    doc.add_heading("LAPORAN HASIL PENELITIAN",0)
    doc.add_paragraph(title or "[Judul penelitian]")
    doc.add_heading("BAB IV. HASIL PENELITIAN DAN PEMBAHASAN",level=1)
    doc.add_heading("A. Konteks Penelitian",level=2)
    doc.add_paragraph(study_context or "[Lengkapi konteks penelitian berdasarkan data]")
    doc.add_heading("B. Metode dan Prosedur Analisis",level=2)
    doc.add_paragraph(method_note or "[Lengkapi metode, sampel, instrumen, estimator, dan prosedur]")
    def add_frame(heading, frame):
        doc.add_heading(heading,level=2)
        if frame is None or not isinstance(frame,pd.DataFrame) or frame.empty:
            doc.add_paragraph("[Data belum disediakan]")
            return
        cols=list(frame.columns)
        table=doc.add_table(rows=1,cols=len(cols))
        table.style="Table Grid"
        for cell,name in zip(table.rows[0].cells,cols): cell.text=str(name)
        for _,row in frame.iterrows():
            cells=table.add_row().cells
            for cell,val in zip(cells,row.tolist()):
                cell.text="" if pd.isna(val) else str(val)
    add_frame("C. Hasil Kuantitatif",quantitative)
    add_frame("D. Temuan Kualitatif",qualitative)
    add_frame("E. Joint Display",joint_display)
    add_frame("F. Meta-Inferensi",meta_inference)
    doc.add_paragraph("Catatan: tabel dan narasi harus diverifikasi terhadap output analisis dan bukti sumber. Generator tidak menambahkan statistik, kutipan, teori, atau referensi yang tidak disediakan.")
    doc.add_heading("BAB V. PENUTUP",level=1)
    doc.add_paragraph(chapter_v or "[Lengkapi kesimpulan, implikasi, keterbatasan, dan rekomendasi berdasarkan hasil]")
    if appendices:
        doc.add_heading("LAMPIRAN",level=1)
        for name,frame in appendices.items(): add_frame(str(name),frame)
    path=Path(output_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    doc.save(path)
    return str(path)
