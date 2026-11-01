# Research Analyzer Professional v4.4

## Fitur baru
- Pembuat sintaks CFA dari peta konstruk-indikator JSON.
- Pembuat model higher-order construct (HOC) reflektif tingkat kedua dengan sintaks lavaan.
- Pemeriksaan struktur sintaks lavaan dasar dan pemeriksaan nama variabel terhadap data.
- Interpretasi berbasis aturan dari parameter `parameterEstimates()` (loading dan jalur struktural), termasuk arah, standardized estimate bila tersedia, dan p-value.
- Ekspor kode diagram jalur dalam format Graphviz DOT.
- Ringkasan ringkas indeks fit dan jumlah jalur signifikan dari hasil lavaan.

## Penggunaan
1. Jalankan aplikasi sebagaimana versi sebelumnya (`streamlit run app.py`).
2. Buka tab **Advanced CB-SEM & HOC v4.4**.
3. Susun peta indikator dan dimensi HOC; unduh sintaks `.lav`.
4. Jalankan estimasi pada tab **CFA & CB-SEM Engine v4.3** menggunakan R dan paket `lavaan`.
5. Impor CSV parameter estimates untuk memperoleh interpretasi dan kode DOT.

## Batasan metodologis dan teknis
- HOC yang dibuat adalah spesifikasi reflektif tingkat kedua; model formative atau tipe HOC lain belum dibangun otomatis.
- Sintaks diperiksa secara struktural, bukan parser penuh bahasa lavaan; validitas akhir ditentukan oleh lavaan.
- Interpretasi otomatis bersifat deskriptif/berbasis aturan, bukan keputusan menerima hipotesis atau klaim kausal.
- Diagram DOT merupakan sumber teks; perlu Graphviz atau aplikasi kompatibel untuk merender menjadi gambar.
- Eksekusi R/lavaan membutuhkan instalasi lokal; R dan lavaan tidak tersedia dalam lingkungan build ini sehingga estimasi nyata belum diuji.
- Antarmuka Streamlit belum diuji end-to-end pada lingkungan build; modul inti dan sintaks Python telah diuji.
