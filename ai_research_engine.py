
"""Optional generative-AI layer using the OpenAI Responses API.

No API key is stored in project files. Calls occur only after a user presses an
explicit action button. Inputs are sent to the configured API provider.
"""
import json
import os
import urllib.request
import urllib.error

DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"
MAX_INPUT_CHARS = 60000

TASKS = {
    "Analisis artikel ilmiah": (
        "Analisis artikel secara kritis dalam bahasa Indonesia. Pisahkan secara jelas: "
        "tujuan, pertanyaan riset, kerangka teori, konsep/variabel, metode, konteks/sampel, "
        "temuan yang benar-benar tertulis, keterbatasan yang dinyatakan penulis, dan implikasi. "
        "Sertakan kutipan pendek atau penanda bagian/halaman hanya bila tersedia pada teks. "
        "Jangan mengarang metadata, kutipan, DOI, atau temuan."
    ),
    "Perbandingan teori": (
        "Bandingkan teori yang diberikan berdasarkan asumsi dasar, konsep inti, dimensi, "
        "mekanisme penjelasan, konteks penggunaan, kekuatan, keterbatasan, dan kesesuaian "
        "dengan masalah penelitian. Bedakan informasi dari sumber dengan inferensi analitis. "
        "Jangan menciptakan tokoh, karya, tahun, atau sitasi."
    ),
    "Identifikasi research gap": (
        "Identifikasi kemungkinan research gap hanya dari bukti yang disediakan. Kelompokkan "
        "menjadi gap empiris, teoretis, metodologis, kontekstual, dan praktis. Untuk setiap gap, "
        "tunjukkan artikel/ID sumber yang mendukung dan jelaskan keterbatasan bukti. Jangan "
        "menyatakan novelty sebagai fakta tanpa pemeriksaan literatur yang lebih luas."
    ),
    "Pengembangan instrumen": (
        "Kembangkan draf butir instrumen berdasarkan konstruk, dimensi, indikator, teori, "
        "dan populasi yang diberikan. Buat tabel: kode, indikator, butir, arah butir, alasan "
        "keterkaitan. Hindari dua gagasan dalam satu butir, bahasa menghakimi, dan jargon. "
        "Tandai butir yang perlu penyesuaian konteks. Nyatakan bahwa butir belum tervalidasi."
    ),
    "Analisis transkrip kualitatif": (
        "Lakukan analisis awal secara transparan: unit makna, kode awal, kategori, tema tentatif, "
        "kutipan bukti persis dari transkrip, interpretasi alternatif, dan pertanyaan lanjutan. "
        "Jangan mengubah kutipan. Perhatikan kasus negatif/kontradiktif. Tegaskan bahwa coding "
        "dan interpretasi final harus diverifikasi peneliti."
    ),
    "Pengembangan codebook kualitatif": (
        "Susun codebook kualitatif dari transkrip yang diberikan. Sajikan kode, definisi operasional, "
        "kriteria inklusi, kriteria eksklusi, contoh kutipan persis, kategori, dan tema tentatif. "
        "Bedakan kode induktif dan deduktif bila informasi memungkinkan. Jangan mengubah kutipan; "
        "sertakan ID segmen jika tersedia. Tandai ambiguitas dan kasus negatif."
    ),
    "Analisis tematik lanjutan": (
        "Lakukan thematic analysis secara bertahap dari transkrip. Sajikan tabel unit makna, "
        "kutipan verbatim dengan ID segmen, kode awal, kategori, tema tentatif, interpretasi, "
        "kasus negatif/kontradiktif, dan pertanyaan refleksif peneliti. Jangan memaksakan tema "
        "yang tidak didukung data. Bedakan deskripsi peserta dan interpretasi analis."
    ),
    "Adaptasi manuskrip ke jurnal sasaran": (
        "Bantu adaptasi manuskrip ke jurnal sasaran berdasarkan author guidelines yang diberikan. "
        "Periksa struktur artikel, batas abstrak, jumlah kata kunci, gaya sitasi, declarations, "
        "dan kelengkapan pelaporan. Jangan mengarang persyaratan jurnal. Jika author guidelines "
        "tidak diberikan, tandai hal yang perlu diverifikasi dan jangan mengklaim telah sesuai."
    ),
    "Penyusunan manuskrip ilmiah": (
        "Susun draf manuskrip ilmiah secara terstruktur berdasarkan materi yang diberikan. "
        "Gunakan bagian judul, abstrak terstruktur, pendahuluan, metode, hasil, diskusi, kesimpulan, "
        "keterbatasan, dan referensi. Jangan mengarang data, hasil statistik, lokasi, sampel, atau sitasi. "
        "Gunakan placeholder yang jelas untuk informasi yang belum tersedia."
    ),
    "Sintesis literatur berbasis matriks": (
        "Sintesis artikel yang diberikan dengan membandingkan pertanyaan, teori, konteks, metode, "
        "sampel, temuan, dan keterbatasan. Susun pola konvergensi, divergensi, perkembangan tema, "
        "dan gap yang benar-benar didukung sumber. Cantumkan ID artikel pada setiap klaim. Jangan "
        "menambah referensi eksternal atau mengarang temuan. Pisahkan sintesis deskriptif dan inferensi."
    ),
    "Audit kesiapan submit jurnal": (
        "Audit manuskrip terhadap author guidelines yang disertakan. Buat tabel persyaratan, bukti "
        "dalam manuskrip, status, dan tindakan koreksi. Jika pedoman tidak disediakan, tandai "
        "persyaratan sebagai belum dapat diverifikasi. Jangan mengklaim jurnal terindeks atau cocok "
        "tanpa bukti eksplisit."
    ),
    "Diskusi hasil penelitian": (
        "Susun draf pembahasan dengan alur: temuan utama, interpretasi, hubungan dengan teori, "
        "perbandingan dengan studi terdahulu yang disediakan, kontribusi, implikasi, dan batasan. "
        "Gunakan hanya hasil dan referensi yang diberikan. Jika dukungan literatur tidak tersedia, "
        "tulis [REFERENSI PERLU DITAMBAHKAN], jangan mengarang sitasi atau angka."
    ),
}

def build_payload(model, instructions, user_text, max_output_tokens=2500):
    if not str(model).strip():
        raise ValueError("Nama model harus diisi.")
    if not str(user_text).strip():
        raise ValueError("Materi analisis belum diisi.")
    if len(user_text) > MAX_INPUT_CHARS:
        raise ValueError(f"Materi melebihi batas {MAX_INPUT_CHARS:,} karakter. Bagi menjadi beberapa bagian.")
    return {
        "model": model.strip(),
        "instructions": instructions.strip(),
        "input": user_text,
        "max_output_tokens": int(max_output_tokens),
        "store": False,
    }

def extract_output_text(response_json):
    if isinstance(response_json.get("output_text"), str) and response_json["output_text"].strip():
        return response_json["output_text"].strip()
    chunks=[]
    for item in response_json.get("output", []):
        for part in item.get("content", []):
            if part.get("type") in ("output_text", "text") and part.get("text"):
                chunks.append(part["text"])
    result="\n".join(chunks).strip()
    if not result:
        raise ValueError("API mengembalikan respons tanpa teks. Periksa model, kuota, atau format respons.")
    return result

def call_responses_api(api_key, user_text, task, model=DEFAULT_MODEL,
                       endpoint=DEFAULT_ENDPOINT, max_output_tokens=2500, timeout=120):
    if not api_key or not api_key.strip():
        raise ValueError("API key belum diisi.")
    if task not in TASKS:
        raise ValueError("Jenis tugas tidak dikenal.")
    payload=build_payload(model,TASKS[task],user_text,max_output_tokens)
    request=urllib.request.Request(
        endpoint,
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        headers={"Authorization":f"Bearer {api_key.strip()}",
                 "Content-Type":"application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            data=json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode("utf-8",errors="replace")[:1500]
        raise RuntimeError(f"API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Tidak dapat terhubung ke API: {exc.reason}") from exc
    return extract_output_text(data)

def extract_uploaded_text(uploaded_file):
    name=uploaded_file.name.lower()
    raw=uploaded_file.getvalue()
    if name.endswith(".txt") or name.endswith(".md"):
        return raw.decode("utf-8",errors="replace")
    if name.endswith(".docx"):
        from docx import Document
        doc=Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Pustaka pypdf belum terpasang. Jalankan pip install pypdf.") from exc
        import io
        reader=PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Format file tidak didukung. Gunakan PDF, DOCX, TXT, atau MD.")


def list_available_models(api_key, endpoint="https://api.openai.com/v1/models", timeout=30):
    """Return model IDs visible to this API key; access varies by project/account."""
    if not api_key or not api_key.strip():
        raise ValueError("API key belum diisi.")
    request=urllib.request.Request(endpoint,
        headers={"Authorization":f"Bearer {api_key.strip()}","Content-Type":"application/json"},
        method="GET")
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            data=json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode("utf-8",errors="replace")[:1500]
        raise RuntimeError(f"API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Tidak dapat mengambil daftar model: {exc.reason}") from exc
    return sorted({str(x.get("id")) for x in data.get("data",[]) if x.get("id")})
