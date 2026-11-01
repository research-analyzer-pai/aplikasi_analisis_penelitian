# Research Analyzer Professional v3.7

## Fokus rilis
Integrasi mixed methods yang dapat ditelusuri dan validasi impor hasil SEM.

## Fitur baru
1. **SEM Results Import & Validation**: impor CSV hasil AMOS/lavaan/SmartPLS; normalisasi nama kolom jalur, beta, t, p, dan CI; pemeriksaan kelengkapan, nilai p, duplikasi jalur, serta urutan CI.
2. **Evidence-linked Joint Display**: pemetaan jalur kuantitatif ke tema kualitatif, jumlah bukti, ID bukti, kutipan yang dipilih, dan penjelasan integratif peneliti.
3. **Draft narrative**: membuat narasi ringkas yang hanya menggunakan angka dan bukti yang diimpor/dimasukkan.
4. Mempertahankan modul versi 3.6, termasuk semantic coding opsional dan alat analisis kualitatif.

## Menjalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```
Buka tab **SEM Results Validation v3.7**, unggah CSV hasil SEM. Kemudian buka **Evidence-linked Joint Display v3.7**, unggah CSV kualitatif dengan kolom `theme,evidence`, lalu buat pemetaan jalur-tema.

## Format CSV minimal
Hasil SEM: `path,beta` (opsional `t,p,ci_low,ci_high`). Nama kolom ekspor umum SmartPLS seperti `Path`, `Original sample`, `T statistics`, `P values` juga didukung.

Bukti kualitatif: `theme,evidence`; setiap baris adalah satu bukti/kutipan yang sudah dianonimkan. Gunakan ID informan/kutipan di kolom terpisah bila diperlukan.

## Batasan
- Modul SEM mengimpor dan memeriksa hasil, bukan menjalankan ulang algoritma SmartPLS, AMOS, atau lavaan.
- Pemetaan joint display ditetapkan peneliti; status keterhubungan tidak membuktikan validitas interpretasi.
- Narasi otomatis adalah draf berbasis data yang diimpor; verifikasi seluruh angka, kutipan, konteks, dan teori.
- Hindari mengunggah data identitas langsung. Gunakan data anonim dan patuhi persetujuan etik.
