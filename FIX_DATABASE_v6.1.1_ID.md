# Perbaikan repositori database v6.1.1

## Yang diperbaiki
- Pengecekan koneksi database (`SELECT 1`) saat aplikasi mulai.
- Normalisasi URL PostgreSQL `postgres://` dan `postgresql://` ke driver `psycopg` v3.
- Validasi dasar URL agar kesalahan konfigurasi lebih mudah dikenali.
- Pool koneksi menggunakan `pool_pre_ping` dan `pool_recycle` untuk koneksi cloud.
- Pesan sidebar menjelaskan bahwa SQLite adalah fallback lokal, bukan penyimpanan permanen cloud.
- Panduan pengaturan `DATABASE_URL` ditampilkan langsung di sidebar jika PostgreSQL belum tersambung.
- Tidak menampilkan connection string/password di antarmuka.

## Langkah setelah mengunggah versi ini
1. Buat database PostgreSQL terkelola (misalnya Neon) dan salin connection string.
2. Di Streamlit Cloud, buka Manage app → Settings → Secrets.
3. Tambahkan:
   `DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"`
4. Simpan Secrets lalu reboot aplikasi.
5. Pastikan sidebar menunjukkan `PostgreSQL — penyimpanan cloud persisten`.

## Catatan
Kode aplikasi tidak dapat membuat akun database eksternal atau menerbitkan kredensial database secara otomatis. PostgreSQL harus dibuat oleh pemilik aplikasi pada penyedia database. Jangan pernah mengunggah URL yang berisi password ke GitHub.
