"""Journal article drafting and DOCX export utilities."""
from __future__ import annotations
from io import BytesIO
import re
import pandas as pd
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT


SECTIONS = [
    ("Introduction", "introduction"),
    ("Research Method", "method"),
    ("Results", "results"),
    ("Discussion", "discussion"),
    ("Conclusion", "conclusion"),
]


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE))


def make_chart(frame: pd.DataFrame, chart_type: str, x_col: str, y_cols: list[str], title: str = "") -> BytesIO:
    if frame is None or frame.empty or not x_col or not y_cols:
        raise ValueError("Pilih dataset, kolom kategori/X, dan minimal satu kolom numerik.")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    data = frame[[x_col] + y_cols].copy().dropna()
    if data.empty:
        raise ValueError("Tidak ada data lengkap untuk grafik.")
    if chart_type == "Bar":
        data.set_index(x_col)[y_cols].plot(kind="bar", ax=ax)
    elif chart_type == "Line":
        data.set_index(x_col)[y_cols].plot(kind="line", marker="o", ax=ax)
    elif chart_type == "Scatter":
        if len(y_cols) != 1:
            raise ValueError("Scatter plot membutuhkan satu variabel Y.")
        ax.scatter(pd.to_numeric(data[x_col], errors="coerce"), pd.to_numeric(data[y_cols[0]], errors="coerce"))
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_cols[0])
    elif chart_type == "Histogram":
        if len(y_cols) != 1:
            raise ValueError("Histogram membutuhkan satu variabel numerik.")
        ax.hist(pd.to_numeric(data[y_cols[0]], errors="coerce").dropna(), bins="auto")
        ax.set_xlabel(y_cols[0])
        ax.set_ylabel("Frekuensi")
    ax.set_title(title or f"{chart_type}: {', '.join(y_cols)}")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    out = BytesIO()
    fig.savefig(out, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    out.seek(0)
    return out


def make_flow_diagram(labels: list[str]) -> BytesIO:
    labels = [x.strip() for x in labels if x.strip()]
    if not labels:
        raise ValueError("Masukkan minimal dua tahapan diagram.")
    fig, ax = plt.subplots(figsize=(8, max(2.2, len(labels) * 0.85)))
    ax.axis("off")
    n = len(labels)
    for i, label in enumerate(labels):
        y = 1 - (i + 0.5) / n
        ax.text(0.5, y, label, ha="center", va="center", wrap=True,
                bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="black", lw=1.2),
                transform=ax.transAxes, fontsize=10)
        if i < n - 1:
            y2 = 1 - (i + 1.5) / n
            ax.annotate("", xy=(0.5, y2 + 0.04), xytext=(0.5, y - 0.04),
                        xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", lw=1.2))
    out = BytesIO()
    fig.savefig(out, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    out.seek(0)
    return out


def _add_df_table(doc, frame: pd.DataFrame, title: str, max_rows: int = 25):
    if frame is None or frame.empty:
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    view = frame.head(max_rows).copy()
    table = doc.add_table(rows=1, cols=len(view.columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, col in enumerate(view.columns):
        table.rows[0].cells[i].text = str(col)
    for _, row in view.iterrows():
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = "" if pd.isna(value) else str(value)
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def build_article_docx(path: str, metadata: dict, sections: dict, references: str,
                       keywords: str = "", tables: list[tuple[str, pd.DataFrame]] | None = None,
                       figures: list[tuple[str, BytesIO]] | None = None,
                       abstract: str = "", acknowledgements: str = ""):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.85)
    sec.bottom_margin = Inches(0.85)
    styles = doc.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"].font.size = Pt(11)
    styles["Normal"].paragraph_format.line_spacing = 1.5

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(metadata.get("title", "Untitled Research Article"))
    run.bold = True
    run.font.size = Pt(14)
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors.add_run(metadata.get("authors", "Author name(s)"))
    affiliation = doc.add_paragraph()
    affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER
    affiliation.add_run(metadata.get("affiliation", "Institutional affiliation"))
    email = metadata.get("email", "")
    if email:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(email)

    doc.add_heading("Abstract", level=1)
    doc.add_paragraph(abstract)
    if keywords:
        p = doc.add_paragraph()
        p.add_run("Keywords: ").bold = True
        p.add_run(keywords)

    for heading, key in SECTIONS:
        doc.add_heading(heading, level=1)
        body = sections.get(key, "").strip()
        for para in re.split(r"\n\s*\n", body):
            if para.strip():
                doc.add_paragraph(para.strip())

        if key == "results":
            for caption, frame in (tables or []):
                _add_df_table(doc, frame, caption)
            for caption, image in (figures or []):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(image, width=Inches(6.0))
                cp = doc.add_paragraph(caption)
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if acknowledgements.strip():
        doc.add_heading("Acknowledgements", level=1)
        doc.add_paragraph(acknowledgements.strip())
    doc.add_heading("References", level=1)
    for line in references.splitlines():
        if line.strip():
            p = doc.add_paragraph(line.strip())
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
    doc.save(path)
    return path


def crossref_search(query: str, rows: int = 8) -> list[dict]:
    """Retrieve bibliographic metadata from Crossref; researcher must verify suitability."""
    import requests
    if not query.strip():
        return []
    response = requests.get(
        "https://api.crossref.org/works",
        params={"query.bibliographic": query, "rows": max(1, min(int(rows), 20)),
                "select": "title,author,published-print,published-online,container-title,volume,issue,page,DOI,type,publisher"},
        headers={"User-Agent": "ResearchAnalyzerProfessional/6.0 (bibliography assistant)"},
        timeout=15,
    )
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])
    found = []
    for item in items:
        title = (item.get("title") or [""])[0]
        authors = item.get("author") or []
        names = []
        for author in authors[:20]:
            family = author.get("family", "")
            given = author.get("given", "")
            initials = " ".join((x[0] + ".") for x in given.split() if x)
            names.append(f"{family}, {initials}".strip(", "))
        date_parts = (item.get("published-print") or item.get("published-online") or {}).get("date-parts", [[None]])[0]
        year = date_parts[0] if date_parts else None
        journal = (item.get("container-title") or [""])[0]
        volume = item.get("volume", "")
        issue = item.get("issue", "")
        page = item.get("page", "")
        doi = item.get("DOI", "")
        author_text = ", ".join(names[:-1]) + (", & " if len(names)>1 else "") + (names[-1] if names else "")
        if not names:
            author_text = "Author not indexed"
        ref = f"{author_text} ({year or 'n.d.'}). {title}. {journal}"
        if volume:
            ref += f", {volume}"
        if issue:
            ref += f"({issue})"
        if page:
            ref += f", {page}"
        ref += "."
        if doi:
            ref += f" https://doi.org/{doi}"
        found.append({"apa":ref, "title":title, "year":year, "journal":journal,
                      "doi":doi, "type":item.get("type",""), "publisher":item.get("publisher","")})
    return found
def build_markdown_article_docx(path: str, markdown_text: str):
    """Export AI-generated Markdown article draft to a readable Word document."""
    import re
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=Inches(0.85); sec.bottom_margin=Inches(0.85)
    doc.styles["Normal"].font.name="Times New Roman"
    doc.styles["Normal"].font.size=Pt(11)
    doc.styles["Normal"].paragraph_format.line_spacing=1.5
    in_refs=False
    for raw in markdown_text.splitlines():
        line=raw.strip()
        if not line:
            continue
        clean=re.sub(r"\*\*(.*?)\*\*",r"\1",line)
        clean=re.sub(r"\*(.*?)\*",r"\1",clean)
        if re.match(r"^#{1,2}\s*References",clean,re.I): in_refs=True
        m=re.match(r"^(#{1,3})\s+(.+)$",line)
        if m:
            level=min(len(m.group(1)),2)
            doc.add_heading(re.sub(r"\*\*(.*?)\*\*",r"\1",m.group(2)),level=level)
            continue
        if line.startswith("|") and line.endswith("|"):
            cells=[x.strip() for x in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?",x) for x in cells): continue
            # Markdown tables rendered as paragraphs to avoid broken column assumptions.
            p=doc.add_paragraph("  |  ".join(cells))
            p.paragraph_format.space_after=Pt(2)
            continue
        if line.startswith("- ") or line.startswith("* "):
            doc.add_paragraph(clean[2:],style="List Bullet")
            continue
        if re.match(r"^\d+\.\s",clean):
            doc.add_paragraph(re.sub(r"^\d+\.\s*","",clean),style="List Number")
            continue
        p=doc.add_paragraph()
        if in_refs:
            p.paragraph_format.left_indent=Inches(0.3)
            p.paragraph_format.first_line_indent=Inches(-0.3)
        p.add_run(clean)
    doc.save(path)
    return path
