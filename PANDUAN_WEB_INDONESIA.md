# Research Analyzer Professional v5.0 — Panduan Web

## Menjalankan sebagai aplikasi web di komputer Windows
1. Ekstrak ZIP ke folder biasa (jangan jalankan langsung dari dalam ZIP).
2. Pastikan Python 3.10 atau lebih baru sudah terpasang.
3. Klik dua kali `run_web.bat`.
4. Tunggu instalasi dependensi selesai. Browser akan membuka aplikasi Streamlit.
5. Jika browser tidak terbuka otomatis, akses `http://localhost:8501`.

## Menerbitkan agar dapat diakses melalui internet (Streamlit Community Cloud)
1. Ekstrak ZIP ini.
2. Unggah seluruh ISI folder hasil ekstrak ke root repository GitHub. Jangan unggah ZIP sebagai satu file.
3. Pastikan `app.py`, `requirements.txt`, seluruh modul `.py`, folder `data/`, dan folder `docs/` berada pada repository.
4. Masuk ke `https://share.streamlit.io/` menggunakan akun GitHub yang memiliki akses ke repository.
5. Pilih **Create app**; pilih repository, branch, dan isi **Main file path** dengan `app.py`.
6. Tekan **Deploy**. Setelah build berhasil, Streamlit menampilkan alamat `*.streamlit.app`.

## Jika deployment gagal
- Buka tab **Manage app** lalu periksa **Logs**.
- Pastikan file utama tepat `app.py` (huruf kecil) dan berada di root repository.
- Pastikan semua modul Python ikut terunggah dan `requirements.txt` berada di root.
- Jangan menaruh API key, password, token, atau data identitas responden di repository publik.

## Catatan
Paket ini telah lulus 165 pengujian otomatis (`pytest`). Pengujian tersebut bukan pengganti uji penerimaan pengguna, audit keamanan, atau validasi metodologis pada data penelitian nyata. Hasil analisis tetap perlu diperiksa peneliti.
