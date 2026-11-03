# Research Analyzer Professional v6.0

## Konsep
**One Project – One Data Repository – Three Analytical Approaches.** Buat satu proyek penelitian, masukkan data kuantitatif (tabulasi angket), kualitatif (wawancara, observasi, dokumentasi), atau keduanya. Dataset yang sudah diproses dibagikan ke modul analisis sesuai karakteristik data.

## Fitur utama v6.0
- Pusat input data dari satu tab Data: XLSX, XLS, CSV, DOCX, PDF berbasis teks, TXT, dan MD.
- Dataset tabular dapat dipilih sebagai dataset aktif untuk modul kuantitatif/SEM.
- Dokumen teks diekstrak menjadi unit data kualitatif untuk analisis koding/tema.
- Repositori per proyek dengan autosave: data tabular, beberapa dataset, segmen kualitatif, coding, data SEM impor, metadata sumber, dan hash file.
- Project state dimuat kembali ketika judul proyek yang sama dipilih.
- Mendukung SQLite untuk pengembangan lokal dan PostgreSQL untuk penyimpanan cloud persisten.
- Mempertahankan modul analisis dan fitur dari versi 5.2.

## Menjalankan secara lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```
SQLite akan dibuat sebagai `research_analyzer_v60.db` di direktori aplikasi.

## Deploy Streamlit Community Cloud dengan penyimpanan permanen
Filesystem lokal Streamlit Community Cloud tidak boleh dianggap sebagai penyimpanan permanen. Siapkan database PostgreSQL (misalnya layanan PostgreSQL terkelola), lalu tambahkan secret aplikasi:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Aplikasi akan memakai PostgreSQL secara otomatis jika `DATABASE_URL` tersedia. Jangan masukkan kredensial database ke GitHub atau file kode. Gunakan menu Secrets di pengaturan aplikasi Streamlit.

## Batasan penting
- Jika `DATABASE_URL` tidak dikonfigurasi, aplikasi memakai SQLite sebagai fallback untuk pengembangan lokal. Di Streamlit Cloud, SQLite tidak dijamin bertahan setelah restart/redeploy. Untuk persistensi cloud, PostgreSQL wajib dikonfigurasi. Aplikasi menampilkan panduan koneksi di sidebar dan memeriksa koneksi database saat startup.
- Sistem menyimpan hasil ekstraksi/representasi data yang telah diparsing; file unggahan asli tidak disimpan sebagai arsip biner.
- PDF hasil scan/gambar membutuhkan OCR dan belum didukung pada versi ini.
- Dataset tabular yang berbeda tidak digabung otomatis. Peneliti memilih dataset aktif untuk analisis kuantitatif.
- Sistem tidak otomatis mengubah semua data menjadi analisis yang sama. Peneliti tetap menentukan desain, variabel, indikator, unit analisis, prosedur coding, dan strategi integrasi.
- Mixed methods menghasilkan integrasi setelah analisis kuantitatif dan kualitatif dilakukan sesuai desain (misalnya sequential explanatory, sequential exploratory, atau convergent).
- Autosave menyimpan repositori inti proyek. Sebagian hasil analisis sementara dan unggahan tambahan pada modul khusus tetap dikelola oleh modul masing-masing.

## Privasi dan etika
Gunakan data yang dianonimkan. Jangan mengunggah identitas langsung responden kecuali terdapat dasar etik, persetujuan, dan perlindungan data yang memadai. Batasi akses database dan buat backup berkala.

## Modul artikel ilmiah
Buka tab **Artikel Ilmiah (IMRaD)**. Isi identitas author dan setiap bagian naskah. Referensi dapat dimasukkan manual dalam APA 7 atau dicari metadata awalnya melalui Crossref. Pilih visual yang relevan dengan substansi hasil, kemudian ekspor ke DOCX.

Pencarian Crossref hanya mengambil metadata bibliografis. Metadata bukan jaminan mutu jurnal atau relevansi; peneliti wajib membuka dan memeriksa artikel/penerbit, kecocokan sitasi, status koreksi/retraksi, dan kelengkapan DOI. Sistem tidak membuat kutipan atau referensi fiktif. Isi artikel, interpretasi, dan sitasi tetap harus diverifikasi peneliti. Template DOCX merupakan draf awal dan perlu disesuaikan dengan author guidelines jurnal tujuan.

## AI Automatic International Journal Article Generator
Buka tab **AI Article Generator (Automatic)**. Fitur ini tidak meminta unggahan dokumen. Peneliti mengisi metadata/topik, desain, konteks, metode, dan hasil aktual pada formulir. Jika diaktifkan, aplikasi menggunakan ringkasan dataset tabular dan segmen kualitatif yang telah tersimpan pada proyek aktif. Aplikasi kemudian menelusuri metadata artikel jurnal melalui OpenAlex, lalu mengirim konteks penelitian dan metadata/abstrak yang tersedia ke OpenAI Responses API untuk menyusun draf dengan struktur:
1. Title, Author, Abstract, Keywords
2. Introduction
3. Literature Review
4. Research Method
5. Results
6. Discussion
7. Conclusion
8. References (APA 7)

**Konfigurasi:** masukkan OpenAI API key di tab generator. Penggunaan API dapat dikenai biaya. Model API dapat dipilih sesuai model yang tersedia pada akun API. Aplikasi tidak menyimpan API key dalam source code. Pencarian OpenAlex tidak memerlukan unggahan dokumen. Referensi yang ditemukan adalah metadata/abstrak; bukan full-text review. Peneliti wajib memeriksa artikel asli, kesesuaian kutipan, DOI, reputasi jurnal (misalnya melalui Scopus Sources atau Web of Science Master Journal List), dan status koreksi/retraksi.

**Integritas:** Results hanya boleh berasal dari temuan yang dimasukkan peneliti atau ringkasan data proyek. Jika data/temuan tidak tersedia, model diarahkan untuk menulis placeholder [AUTHOR INPUT REQUIRED], bukan mengarang statistik, kutipan, tema, atau hasil. Draf harus ditinjau dan disunting peneliti. Tidak ada sistem yang dapat menjamin artikel diterima jurnal bereputasi.
