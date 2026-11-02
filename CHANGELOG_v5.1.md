# Research Analyzer Professional v5.1

## Multi-format data ingestion
- Quantitative data import now supports CSV, Excel XLSX, and legacy XLS workbooks.
- Excel import includes worksheet selection.
- Qualitative source import now supports Word DOCX and text-based PDF, plus CSV/XLSX/XLS/TXT/MD.
- DOCX extraction reads paragraphs and table rows and retains source/location metadata.
- PDF extraction reads text per page and retains page metadata.
- Spreadsheet qualitative imports accept text, teks, transcript, transkrip, kutipan, or isi columns.
- Existing analysis modules, tabs, and v5.0 report-generation features are retained.

## Methodological and technical notes
- Scanned/image-only PDFs need OCR before import; this version does not perform OCR.
- PDF extraction quality depends on the PDF's text layer and document layout.
- DOCX tables are flattened row-by-row into text units; review the extracted segments before coding.
- Excel quantitative import reads the selected worksheet as a data frame. Check variable types and missing values before analysis.
- CSV-only imports in specialist modules remain CSV-specific unless explicitly updated in their own module; the core quantitative and qualitative workflows support the new formats.
