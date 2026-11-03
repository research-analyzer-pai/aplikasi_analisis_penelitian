# Hotfix v6.1.2 — Streamlit form key collision

## Masalah
StreamlitValueAssignmentNotAllowedError muncul pada `with st.form("joint")`. Nama form tersebut berpotensi bertabrakan dengan key state aplikasi yang juga bernama `joint` pada versi yang dideploy.

## Perbaikan
- Mengganti ID form joint menjadi `joint_entry_form_v612`, terpisah dari `st.session_state.joint`.
- Data joint display tetap disimpan pada key state `joint`; hanya ID form yang berubah.

## Penerapan
1. Unggah isi ZIP v6.1.2 ke root repository GitHub dan timpa file lama.
2. Pastikan `app.py` di GitHub menggunakan `with st.form("joint_entry_form_v612")` dan tidak lagi menggunakan `with st.form("joint")`.
3. Tunggu Streamlit Cloud selesai redeploy atau pilih Reboot app.
4. Jika masih error, periksa Logs dan kirim traceback terbaru.

Jangan mengunggah kredensial API/database ke repository.
