# Catatan validasi dan metodologi v2.5

## Yang diuji pada paket
- Pemeriksaan sintaks Python untuk modul inti dan aplikasi.
- Unit test fungsi Cronbach alpha, regresi OLS, uji t, ANOVA, dan validasi impor SEM.
- Uji aplikasi Streamlit secara interaktif masih perlu dilakukan pada komputer pengguna.

## Interpretasi
- Cronbach's alpha mengukur konsistensi internal di bawah asumsi tertentu; bukan bukti tunggal validitas atau unidimensionalitas.
- Corrected item-total correlation dan alpha-if-deleted adalah diagnostik awal, bukan aturan eliminasi otomatis.
- Uji t independen default menggunakan Welch (equal_var=False).
- ANOVA satu arah menghasilkan eta-squared sebagai ukuran efek sederhana; post-hoc belum tersedia.
- OLS mengasumsikan spesifikasi model memadai; periksa linearitas, independensi, homoskedastisitas, normalitas residual untuk inferensi, multikolinearitas, dan observasi berpengaruh.
- SEM-PLS hanya diimpor. Jangan menganggap tabel impor sebagai estimasi oleh aplikasi.
