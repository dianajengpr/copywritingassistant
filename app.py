import streamlit as st
import openai
import os
import subprocess
import tempfile
from typing import List

import whisper
import yt_dlp

# ─────────────────────────────────────────────────────────────────────────────
#  Load your OpenAI key from Streamlit secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("⚠️ OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
#  App config & header
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide",
)
st.title("📝 Copywriting Assistant by **PERKA**")
st.markdown(
    """
    **Asisten Copywriting TikTok kamu— otomatis, praktis, dan siap jualan!**
    Tinggal isi data produk, unggah/link video referensi (opsional), 
    pilih output, dan dapatkan copywriting yang siap tarik perhatian di FYP.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
#  Custom logger & hook untuk yt-dlp
class StreamlitLogger:
    def debug(self, msg):
        st.text(f"DEBUG: {msg}")
    def warning(self, msg):
        st.warning(f"WARNING: {msg}")
    def error(self, msg):
        st.error(f"ERROR: {msg}")

def progress_hook(d):
    if d.get("status") == "downloading":
        percent = d.get("_percent_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        st.text(f"Downloading… {percent} • ETA {eta}")

# ─────────────────────────────────────────────────────────────────────────────
#  1) Form inputs
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air", help="(wajib)")
    fitur_produk = st.text_area(
        "⚙️ Fitur atau Keunggulan Produk (opsional)",
        placeholder="Misal: Bahan food-grade, tahan suhu tinggi…"
    )
    prompt_tambahan = st.text_area(
        "📝 Prompt Tambahan (opsional)",
        placeholder="Misal: Gunakan bahasa gaul generasi Z…"
    )

    st.subheader("Referensi Video (opsional)")
    video_link = st.text_input("🔗 Link Video", placeholder="YouTube, TikTok, atau link video lain")
    uploaded_file = st.file_uploader("📁 Upload File Video", type=["mp4", "mov", "avi"], help="(opsional)")

    st.subheader("Opsi Output")
    bahasa = st.selectbox(
        "🌐 Bahasa Output",
        options=["Indonesia", "Malaysia", "English"],
    )
    jumlah = st.number_input(
        "🔢 Jumlah Copywriting yang Diinginkan",
        min_value=1, max_value=20, value=3, step=1
    )
    model = st.selectbox(
        "🤖 Pilih Model ChatGPT",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
    )

    submitted = st.form_submit_button("Generate Copywriting")

# ─────────────────────────────────────────────────────────────────────────────
#  2) Ketika tombol generate diklik
if submitted:
    if not nama_produk.strip():
        st.warning("Mohon isi **Nama Produk** terlebih dahulu.")
        st.stop()

    # 2a) Handle video download & transcribe
    transcript = None
    if video_link or uploaded_file:
        st.subheader("Proses Transkripsi Video")
        tmp_dir = tempfile.gettempdir()
        tmp_vid = os.path.join(tmp_dir, "ref_video.mp4")

        # Download atau simpan upload
        try:
            if video_link:
                ydl_opts = {
                    "format": "mp4",
                    "outtmpl": tmp_vid,
                    "logger": StreamlitLogger(),
                    "progress_hooks": [progress_hook],
                    "http_headers": {"User-Agent": "Mozilla/5.0"},
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # cek dulu URL
                    ydl.extract_info(video_link, download=False)
                    ydl.download([video_link])

            elif uploaded_file:
                with open(tmp_vid, "wb") as f:
                    f.write(uploaded_file.getbuffer())

        except Exception as e:
            st.error(f"❌ Gagal download/video: {e}")
            st.stop()

        # Ekstrak audio
        audio_path = os.path.join(tmp_dir, "ref_audio.wav")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", tmp_vid,
                "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", audio_path
            ], check=True)
        except Exception as e:
            st.error(f"❌ Gagal ekstrak audio: {e}")
            st.stop()

        # Transkripsi pake Whisper
        try:
            whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(audio_path)
            transcript = res.get("text", "").strip()
            st.success("✅ Transkripsi selesai.")
        except Exception as e:
            st.error(f"❌ Gagal transkripsi: {e}")
            st.stop()

    # 2b) Build prompt untuk OpenAI
    messages: List[dict] = [
        {
            "role": "system",
            "content": (
                "Kamu adalah ahli copywriting TikTok dengan gaya lucu, santai, "
                "dan mengundang perhatian. Hasil harus dalam kalimat utuh: hook – body – CTA."
            )
        }
    ]

    user_prompt = (
        f"Buatkan {jumlah} copywriting promosi produk TikTok.\n"
        f"Produk: {nama_produk}.\n"
    )
    if fitur_produk.strip():
        user_prompt += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip():
        user_prompt += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"
    if transcript:
        user_prompt += f"Transkrip video referensi: {transcript}.\n"
    user_prompt += (
        f"Bahasa: {bahasa}.\n"
        "Syarat:\n"
        "- Awali dengan kalimat yang mengundang perhatian atau bikin shock.\n"
        "- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal.\n"
        "- Akhiri dengan ajakan cek keranjang kuning!\n"
        "- Hindari tanda petik (\\" atau ')—emoji juga tidak usah.\n"
        "- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
        "- Jangan gunakan nomor, bullet point, atau daftar."
    )
    messages.append({"role": "user", "content": user_prompt})

    # 3) Panggil OpenAI
    with st.spinner("🚀 Menghubungi OpenAI…"):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=jumlah * 150,
            )
            result = response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"❌ Gagal generate copywriting: {e}")
            st.stop()

    # 4) Tampilkan hasil & opsi edit/download
    st.subheader("Hasil Copywriting")
    edited = st.text_area(
        "✏️ Anda bisa edit hasil di sini jika perlu:",
        value=result,
        height=300
    )

    st.download_button(
        "📥 Unduh sebagai .txt",
        edited,
        file_name=f"copywriting_{nama_produk.replace(' ','_')}.txt",
        mime="text/plain",
    )
