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
# Load API key
openai.api_key = st.secrets.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("⚠️ OpenAI API Key belum diatur. Tambahkan melalui Streamlit Secrets.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Config UI
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide",
)
st.title("📝 Copywriting Assistant by **PERKA**")
st.markdown(
    """
    **Asisten Copywriting TikTok kamu—otomatis, praktis, dan siap jualan!**
    Isi data produk, unggah atau link video referensi (opsional), lalu generate copywriting.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
# Form Input
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air")
    fitur_produk = st.text_area("⚙️ Fitur/Keunggulan (opsional)", placeholder="Misal: food-grade, tahan suhu tinggi…")
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
    # Proses transkripsi jika ada video referensi
    if video_link or uploaded_file:
        with st.spinner("🔊 Mengambil & transkrip video…"):
            tmp_vid = os.path.join(tempfile.gettempdir(), "ref_video.mp4")
            if video_link:
                ydl_opts = {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
                    "outtmpl": tmp_vid,
                    "logger": StreamlitLogger(),
                    "progress_hooks": [progress_hook],
                    "http_headers": {"User-Agent": "Mozilla/5.0"},
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(video_link, download=False)
                    ydl.download([video_link])
            else:
                tmp_vid = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(tmp_vid, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Transkripsi via OpenAI Whisper API
            with open(tmp_vid, "rb") as audio_f:
                res = openai.Audio.transcribe("whisper-1", audio_f)
            transcript = res.get("text", "").strip()

    # Siapkan prompt dengan gaya TikTok Gen Z
    system_msg = {
        "role": "system",
        "content": (
            "Kamu adalah penulis copywriting TikTok yang jago bikin konten Gen Z: "
            "bahasa santai, tidak formla, dan relatable. "
            "Gunakan struktur hook – keunggulan – CTA."
        )
    }
    user_msg = f"Buat {jumlah} copywriting promosi produk TikTok untuk {nama_produk}.\n"
    if transcript:
        user_msg += (
            "Pakai transkrip ini sebagai sumber utama:\n" +
            f"{transcript}\n"
            "Buat ulang copywriting sesuai cerita di transkrip, "
            "Awali dengan kalimat yang mengundang perhatian atau bikin shock,"
            "Hindari tanda petik (\" atau ')—emoji juga tidak usah.\n"
            "Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
            "Jangan gunakan nomor, bullet point, atau daftar."
            "tapi tetap hook-body-CTA.\n"
        )
    if fitur_produk.strip():
        user_msg += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip():
        user_msg += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"
    user_msg += (
        f"Bahasa: {bahasa}.\n"
        "-- Gunakan bahasa ala ala TikTok.\n"
        "-- Hindari kata-kata kaku seperti ‘kenyamanan dapur’.\n"
        "-- Boleh lebay, bisa curhat atau satire, asal tetap promosi.\n"
        "-- Awali dengan kalimat yang mengundang perhatian atau bikin shock,"
        "-- Hindari tanda petik (\" atau ')—emoji juga tidak usah.\n"
        "-- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
        "-- Jangan gunakan nomor, bullet point, atau daftar."
        "-- Akhiri dengan ajakan cek keranjang kuning!"
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
