# Research Analyzer Professional v4.0

**Academic Research Intelligence — Crossref & Journal Submission Edition**

## Fokus rilis
v4.0 melanjutkan paket v3.9 dengan dua modul antarmuka baru: verifikasi metadata bibliografis melalui Crossref REST API dan pemeriksaan kesiapan submission berdasarkan ketentuan jurnal yang dimasukkan peneliti.

## Modul baru

### 1. Crossref Metadata Intelligence (`crossref_intelligence_v40.py`)
- Normalisasi DOI dan URL DOI.
- Pencarian metadata berdasarkan DOI.
- Pencarian kandidat artikel berdasarkan judul.
- Verifikasi referensi batch dari CSV dengan kolom `doi` dan/atau `title`.
- Perbandingan metadata input dengan metadata Crossref tanpa menimpa data asli.
- Penanganan DOI tidak ditemukan, metadata tidak lengkap, dan kesalahan jaringan.

### 2. Journal Submission Assistant (`journal_submission_v40.py`)
- Checklist persiapan submission yang dapat diedit.
- Penghitungan kata abstrak dan manuskrip.
- Pemeriksaan jumlah kata kunci berdasarkan batas yang dimasukkan pengguna.
- Template deklarasi etik, persetujuan, pendanaan, konflik kepentingan, ketersediaan data, dan kontribusi penulis.

### 3. AI Research Studio
Menambahkan dua prompt kerja: sintesis literatur berbasis matriks dan audit kesiapan submit jurnal. Pemanggilan API tetap memerlukan tindakan eksplisit pengguna dan API key sendiri.

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pengujian
Jalankan:
```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

Uji rilis lokal v4.0: **70 unit test lulus**, kompilasi Python berhasil. Pengujian Crossref menggunakan respons tiruan (mock) agar pengujian deterministik; koneksi live Crossref, pengujian browser Streamlit end-to-end, dan pengujian API AI belum dinyatakan lulus.

## Batasan metodologis dan teknis
- Crossref menyediakan metadata yang disetorkan penerbit/anggota; kecocokan metadata bukan bukti kualitas jurnal, status peer-review, validitas isi, atau indeksasi Scopus/WoS.
- Hasil pencarian judul merupakan kandidat, bukan identifikasi pasti. Cocokkan penulis, judul, tahun, jurnal, dan DOI pada laman penerbit.
- Pemeriksaan jurnal hanya menggunakan batas dan pedoman yang dimasukkan pengguna; aplikasi tidak mengambil author guidelines atau mengirim submission secara otomatis.
- PLS-SEM pada paket ini tetap prototipe sebagaimana batasan v3.9; bukan pengganti SmartPLS/AMOS/lavaan yang tervalidasi.
- AI dapat menghasilkan kekeliruan. Semua interpretasi, referensi, deklarasi, dan naskah wajib diverifikasi peneliti.
- Jangan mengirim data pribadi/identitas partisipan atau materi rahasia ke API eksternal tanpa dasar etik, persetujuan, dan perlindungan yang sesuai.
