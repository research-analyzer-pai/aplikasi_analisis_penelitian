# Changelog v6.0

- Memperkenalkan repositori data per proyek dengan autosave.
- Menambahkan dukungan backend SQLite lokal dan PostgreSQL cloud melalui `DATABASE_URL`.
- Menyimpan dataset kuantitatif, dataset tabular tambahan, segmen kualitatif, coding, data SEM impor, metadata sumber, dan hash unggahan.
- Menambahkan pemuatan ulang data berdasarkan judul proyek.
- Mempertahankan modul analisis v5.2.
- Menambahkan dokumentasi deployment dan batasan persistensi.

- Menambahkan modul penyusunan artikel IMRaD maksimal 8.000 kata (abstrak + isi utama).
- Menambahkan pencarian metadata Crossref opsional untuk membantu penyusunan referensi APA 7.
- Menambahkan ekspor DOCX dengan tabel, grafik, diagram alur, dan gambar pilihan.

- Menambahkan AI Automatic International Journal Article Generator tanpa unggah dokumen.
- Menambahkan pencarian literatur akademik OpenAlex (metadata dan abstrak jika tersedia).
- Struktur otomatis menempatkan Literature Review setelah Introduction.
- Menggunakan OpenAI Responses API untuk menyusun draf artikel; Results dibatasi pada temuan/data yang disediakan dan placeholder jika bukti tidak ada.
- Ekspor draf AI ke DOCX.
