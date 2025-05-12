import streamlit as st
import openai
import os
import tempfile
from typing import List
import yt_dlp

# ─────────────────────────────────────────────────────────────────────────────
# Logger & progress hook untuk yt-dlp agar log tampil di UI
class StreamlitLogger:
    def debug(self, msg):
        st.text(f"DEBUG: {msg}")
    def warning(self, msg):
        st.warning(f"WARNING: {msg}")
    def error(self, msg):
        st.error(f"ERROR: {msg}")

def progress_hook(d):
    if d.get("status") == "downloading":
        st.text(f"Downloading… {d.get('_percent_str', '')} ETA {d.get('_eta_str', '')}")

# ─────────────────────────────────────────────────────────────────────────────
# Muat OpenAI API Key dari Streamlit secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("⚠️ OpenAI API Key belum diatur. Tambahkan ke Settings > Secrets.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Konfigurasi halaman
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide",
)
st.title("📝 Copywriting Assistant by **PERKA**")
st.markdown(
    """
    **Asisten Copywriting TikTok kamu— otomatis, praktis, dan siap jualan!**
    Isi data produk, unggah/link video referensi (opsional), lalu generate copywriting.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
# Form input
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air")
    fitur_produk = st.text_area("⚙️ Keunggulan (opsional)", placeholder="Misal: food-grade, tahan suhu tinggi…")
    prompt_tambahan = st.text_area("📝 Instruksi Tambahan (opsional)", placeholder="Misal: pakai bahasa gaul Gen Z…")

    st.subheader("Referensi Video (opsional)")
    video_link = st.text_input("🔗 Link Video", placeholder="YouTube/TikTok…")
    uploaded_file = st.file_uploader("📁 Upload File Video", type=["mp4","mov","avi"], help="opsional")

    st.subheader("Opsi Output")
    bahasa = st.selectbox("🌐 Bahasa", ["Indonesia","Malaysia","English"])
    jumlah = st.number_input("🔢 Jumlah Copywriting", min_value=1, max_value=20, value=3)
    model = st.selectbox("🤖 Model ChatGPT", ["gpt-4o-mini","gpt-4o","gpt-4","gpt-3.5-turbo"])

    submitted = st.form_submit_button("Generate")

# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    if not nama_produk.strip():
        st.warning("Mohon isi Nama Produk dulu.")
        st.stop()

    transcript = None
    # Jika ada video referensi, download & transkrip via Whisper API
    if video_link or uploaded_file:
        with st.spinner("🔊 Mengunduh dan mentranskrip video…"):
            tmp_path = os.path.join(tempfile.gettempdir(), "ref_video.mp4")
            if video_link:
                ydl_opts = {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
                    "outtmpl": tmp_path,
                    "logger": StreamlitLogger(),
                    "progress_hooks": [progress_hook],
                    "http_headers": {"User-Agent": "Mozilla/5.0"},
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(video_link, download=False)
                    ydl.download([video_link])
            else:
                tmp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            # Transkrip langsung via OpenAI Whisper API
            with open(tmp_path, "rb") as audio_file:
                transcription = openai.Audio.transcribe("whisper-1", audio_file)
            transcript = transcription.get("text", "").strip()

    # Susun prompt untuk ChatGPT
    system_msg = {
        "role": "system",
        "content": (
            "Kamu ahli copywriting TikTok: gaya lucu, santai, mengundang perhatian; "
            "struktur utuh: hook – body – CTA."
        )
    }
    user_msg = f"Buatkan {jumlah} copywriting promosi produk TikTok.\nProduk: {nama_produk}.\n"
    if fitur_produk:
        user_msg += f"Keunggulan: {fitur_produk}.\n"
    if prompt_tambahan:
        user_msg += f"Instruksi tambahan: {prompt_tambahan}.\n"
    if transcript:
        user_msg += f"Transkrip video referensi: {transcript}.\n"
    user_msg += (
        f"Bahasa: {bahasa}.\n"
        "Syarat:\n"
        "- Awali dengan kalimat bikin shock!\n"
        "- Jelaskan keunggulan singkat, natural, tanpa kesan formal.\n"
        "- Akhiri dengan ajakan cek keranjang kuning!\n"
        "- Hindari tanda petik (\" atau '), emoji tidak usah.\n"
        "- Gunakan ! dan ? untuk penekanan.\n"
        "- Tanpa bullet, nomor, atau daftar."
    )
    # Panggil OpenAI ChatCompletion
    with st.spinner("🚀 Menghubungi OpenAI…"):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[system_msg, {"role": "user", "content": user_msg}],
                temperature=0.7,
                max_tokens=jumlah * 150,
            )
            hasil = response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"❌ Generate gagal: {e}")
            st.stop()

    # Tampilkan dan unduh
    st.subheader("Hasil Copywriting")
    edited = st.text_area("✏️ Edit jika perlu:", value=hasil, height=300)
    st.download_button(
        "📥 Unduh (.txt)", edited,
        file_name=f"copywriting_{nama_produk.replace(' ','_')}.txt",
        mime="text/plain"
    )
