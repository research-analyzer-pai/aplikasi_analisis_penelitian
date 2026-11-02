# Research Analyzer Professional v5.2 — Unified Research Data Management

## Perubahan utama
- Menambahkan Pusat Data Penelitian (Single Data Entry) pada tab Data.
- Mendukung unggah banyak file sekaligus: XLSX, XLS, CSV, DOCX, PDF, TXT, dan MD.
- Mengklasifikasikan data tabular menjadi dataset kuantitatif atau data teks kualitatif berdasarkan struktur kolom.
- Mengekstrak teks dari dokumen Word/PDF/TXT/MD menjadi unit data kualitatif.
- Menyimpan beberapa dataset tabular dalam repositori sesi proyek dan menyediakan pemilih dataset aktif.
- Modul kuantitatif/SEM memakai dataset aktif dari pusat data.
- Modul kualitatif memakai transkrip yang sama dari pusat data tanpa unggah ulang.
- Menambahkan ringkasan sumber data, pratinjau, dan kontrol untuk mengosongkan repositori proyek.
- Mempertahankan fitur dan modul versi 5.1.1.

## Catatan
- Repositori ini berada dalam `st.session_state` (sesi aplikasi), bukan database permanen lintas sesi/perangkat.
- Data tabular dengan skema berbeda disimpan sebagai dataset terpisah; peneliti memilih dataset aktif.
- File PDF hasil pemindaian gambar memerlukan OCR eksternal sebelum teks dapat diekstrak.
- Untuk penggunaan produksi dengan penyimpanan lintas sesi, diperlukan database persisten dan kebijakan privasi/akses.
