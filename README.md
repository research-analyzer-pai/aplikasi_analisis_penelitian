# Extension SDK — Research Analyzer Web v6.0

Tambahkan modul Python baru sebagai file `.py` di folder ini. File extension **tidak otomatis dieksekusi**; ini sengaja untuk keamanan. Integrasikan secara eksplisit ke `app.py` setelah kode, dependensi, dan pengujian ditinjau.

## Konvensi
- Gunakan fungsi publik dengan nama yang jelas.
- Terima `pandas.DataFrame` atau struktur Python sederhana.
- Validasi kolom dan tipe data; jangan mengubah data sumber secara diam-diam.
- Jangan menaruh kredensial/API key di source code.
- Sertakan unit test di folder `tests/`.
- Dokumentasikan asumsi statistik dan keterbatasan metodologis.

Lihat `example_extension.py` sebagai contoh.
