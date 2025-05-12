import streamlit as st
import openai
import os
import tempfile
from typing import List

# ─────────────────────────────────────────────────────────────────────────────
# Load OpenAI API key dari Streamlit Secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("⚠️ OpenAI API Key belum diatur. Tambahkan melalui Streamlit Secrets.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Konfigurasi UI
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide",
)
st.title("📝 Copywriting Assistant by **PERKA**")
st.markdown(
    """
    **Asisten Copywriting TikTok kamu—otomatis, praktis, dan siap jualan!**
    Isi data produk, upload file video referensi (opsional), lalu generate copywriting.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
# Form Input
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Tatakan Kompor Ajaib")
    fitur_produk = st.text_area(
        "⚙️ Fitur/Keunggulan (opsional)",
        placeholder="Misal: Bahan tebal anti goyang, hemat gas…"
    )
    prompt_tambahan = st.text_area(
        "📝 Instruksi Tambahan (opsional)",
        placeholder="Misal: Gunakan bahasa Gen Z, fun…"
    )

    st.subheader("Upload Video Referensi (opsional)")
    uploaded_file = st.file_uploader(
        "📁 Upload File Video", type=["mp4", "mov", "avi"], help="opsional"
    )

    st.subheader("Opsi Output")
    bahasa = st.selectbox("🌐 Bahasa", ["Indonesia", "Malaysia", "English"])
    jumlah = st.number_input("🔢 Jumlah Copywriting", min_value=1, max_value=10, value=3)
    model = st.selectbox(
        "🤖 Model ChatGPT", ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
    )
    submitted = st.form_submit_button("Generate")

# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    # Validasi nama produk
    if not nama_produk.strip():
        st.warning("Mohon isi Nama Produk dulu.")
        st.stop()

    transcript = None
    hook_template = None

    # Transkripsi jika file video diupload
    if uploaded_file:
        with st.spinner("🔊 Transkripsi video referensi…"):
            tmp_vid = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(tmp_vid, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Transkripsi via OpenAI Whisper API
            with open(tmp_vid, "rb") as audio_f:
                res = openai.Audio.transcribe("whisper-1", audio_f)
            transcript = res.get("text", "").strip()

            # Tampilkan transkrip mentah
            st.subheader("Transkrip Mentah dari Video Referensi")
            st.code(transcript or "(kosong)", language="text")

            # Ambil kalimat pertama sebagai hook template
            if transcript:
                first_line = transcript.split("\n")[0].strip()
                hook_template = first_line[:50]

    # System prompt untuk AI
    system_msg = {
        "role": "system",
        "content": (
            "Kamu adalah copywriter TikTok Gen Z: bahasa santai, tidak formal, "
            "relatable, struktur hook–keunggulan–CTA."
        )
    }

    # Siapkan user prompt
    user_msg = f"Buat {jumlah} copywriting promosi produk TikTok untuk {nama_produk}.\n"

    # Jika ada transkrip, jadikan dasar utama + hook template
    if transcript and hook_template:
        user_msg += (
            f"Gunakan transkrip ini sebagai sumber utama dan tiru gaya hook pertama: ‘{hook_template}…’.\n"
            f"Transkrip lengkap: {transcript}.\n"
        )

    # Tambahkan detail produk jika ada
    if fitur_produk.strip():
        user_msg += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip():
        user_msg += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"

    # Aturan gaya final dengan fokus variasi hook + jumlah kata
    user_msg += (
        f"Bahasa: {bahasa}.\n"
        "- Jangan gunakan kata formal, brosur, atau cringe seperti 'hemat gas dan waktu', 'lebih efisien', atau 'lebih nyaman'.\n"
        "- Hindari kata ganti orang seperti: aku, kamu, lo, gue, dia.\n"
        "- Jika ada transkrip, tiru makna hook-nya dengan variasi kreatif. Misal jika hook adalah 'Beli satu aja, nanti nyesel!', "
        "maka boleh diganti dengan:\n"
        "  'Yakin cuma beli 1?', 'Beli dua lebih hemat!', atau 'Kalau beli 1 aja nanti rugi!'.\n"
        "- Semua hasil harus memakai hook yang beda-beda. Jangan copy hook yang sama antar hasil.\n"
        "- Semua hasil harus memiliki jumlah kata kurang lebih sama dengan referensi (±10%).\n"
        "- Hindari kata-kata kaku seperti pada iklan atau brosur brosur seperti ‘kenyamanan dapur’, 'masak kilat'.\n"
        "- Gaya bahasa khas TikTok.\n"
        "- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
        "- Hindari tanda petik, emoji, angka, bullet, atau daftar.\n"
        "- Akhiri dengan ajakan cek keranjang kuning!\n"
    )

    messages = [system_msg, {"role": "user", "content": user_msg}]

    # Kirim request ke OpenAI ChatCompletion
    with st.spinner("🚀 Menghubungi OpenAI…"):
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=jumlah * 150
            )
            hasil = resp.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Gagal generate: {e}")
            st.stop()

    # Tampilkan hasil copywriting
    st.subheader("Hasil Copywriting")
    edited = st.text_area("✏️ Edit jika perlu:", value=hasil, height=300)
    st.download_button(
        "📥 Unduh .txt",
        edited,
        file_name=f"cw_{nama_produk.replace(' ', '_')}.txt",
        mime="text/plain"
    )
