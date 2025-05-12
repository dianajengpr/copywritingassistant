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
# Input Form
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air")
    fitur_produk = st.text_area(
        "⚙️ Fitur/Keunggulan (opsional)", placeholder="Misal: food-grade, tahan suhu tinggi…"
    )
    prompt_tambahan = st.text_area(
        "📝 Instruksi Tambahan (opsional)", placeholder="Misal: pakai bahasa gaul Gen Z…"
    )

    st.subheader("Upload Video Referensi (opsional)")
    uploaded_file = st.file_uploader(
        "📁 Upload File Video", type=["mp4","mov","avi"], help="opsional"
    )

    st.subheader("Opsi Output")
    bahasa = st.selectbox("🌐 Bahasa", ["Indonesia","Malaysia","English"])
    jumlah = st.number_input(
        "🔢 Jumlah Copywriting", min_value=1, max_value=20, value=3
    )
    model = st.selectbox(
        "🤖 Model ChatGPT", ["gpt-4o-mini","gpt-4o","gpt-4","gpt-3.5-turbo"]
    )
    submitted = st.form_submit_button("Generate")

# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    if not nama_produk.strip():
        st.warning("Mohon isi Nama Produk dulu.")
        st.stop()

    transcript = None
    # Proses transkripsi jika video referensi diupload
    if uploaded_file:
        with st.spinner("🔊 Transkripsi video referensi…"):
            tmp_vid = os.path.join(tempfile.gettempdir(), uploaded_file.name)
            with open(tmp_vid, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Transkripsi audio dari video via OpenAI Whisper API
            with open(tmp_vid, "rb") as audio_f:
                res = openai.Audio.transcribe("whisper-1", audio_f)
            transcript = res.get("text", "").strip()

            # Tampilkan hasil transkrip mentah
            st.subheader("Transkrip Mentah dari Video Referensi")
            st.code(transcript or "(kosong)", language="text")

            # Filter sederhana: abaikan jika transkrip mengandung lirik lagu TikTok
            lower = transcript.lower()
            if any(kw in lower for kw in [
                "lucky girl syndrome", "lucky girl", "baby", "chorus"
            ]):
                st.warning("⚠️ Transkrip terdeteksi berisi lirik lagu TikTok, diabaikan.")
                transcript = None

    # Siapkan system prompt
    system_msg = {
        "role": "system",
        "content": (
            "Kamu copywriter TikTok Gen Z: bahasa santai, tidak formal, relatable, "
            "struktur hook – keunggulan – CTA."
        )
    }

    # Bangun user prompt
    user_msg = f"Buat {jumlah} copywriting promosi produk TikTok untuk {nama_produk}.\n"
    if transcript:
        user_msg += (
            "Gunakan transkrip berikut sebagai sumber utama:\n" +
            f"{transcript}\n"
        )
    if fitur_produk.strip():
        user_msg += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip():
        user_msg += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"

    # Aturan gaya
    user_msg += (
        f"Bahasa: {bahasa}.\n"
        "- Hindari kata formal atau kaku.\n"
        "- Tidak menggunakan kata ganti orang (aku, kamu, lo, gue, dia).\n"
        "- Gunakan bahasa ringan, dramatis, atau lebay khas TikTok.\n"
        "- Awali dengan hook yang catchy tanpa angka atau bullet.\n"
        "- Hindari tanda petik (\" atau ')—emoji juga tidak usah.\n"
        "- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
        "- Jangan gunakan nomor, bullet point, atau daftar."
        "- Tidak memakai kata ganti orang seperti: aku, kamu, lo, gue, dia."
        "- Gaya netral, tetap ringan dan relatable."
        "- Akhiri dengan ajakan cek keranjang kuning!"
    )

    messages = [system_msg, {"role": "user", "content": user_msg}]

    # Panggil OpenAI ChatCompletion
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

    # Tampilkan hasil dan tombol unduh
    st.subheader("Hasil Copywriting")
    edited = st.text_area("✏️ Edit jika perlu:", value=hasil, height=300)
    st.download_button(
        "📥 Unduh .txt",
        edited,
        file_name=f"cw_{nama_produk.replace(' ', '_')}.txt",
        mime="text/plain"
    )
