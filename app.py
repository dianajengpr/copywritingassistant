import streamlit as st
import openai
import os
import subprocess
import tempfile
from typing import List

import whisper
import yt_dlp

# ─────────────────────────────────────────────────────────────────────────────
# Logger & progress hook untuk yt-dlp supaya pesannya tampil di Streamlit UI
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
    dan dapatkan copywriting yang siap tarik perhatian di FYP.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
#  1) Form inputs
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air", help="(wajib)")
    fitur_produk = st.text_area("⚙️ Fitur atau Keunggulan Produk (opsional)", placeholder="Misal: Bahan food-grade, tahan suhu tinggi…")
    prompt_tambahan = st.text_area("📝 Prompt Tambahan (opsional)", placeholder="Misal: Gunakan bahasa gaul generasi Z…")
    
    st.subheader("Referensi Video (opsional)")
    video_link = st.text_input("🔗 Link Video", placeholder="YouTube, TikTok, dll")
    uploaded_file = st.file_uploader("📁 Upload File Video", type=["mp4","mov","avi"])

    st.subheader("Opsi Output")
    bahasa = st.selectbox("🌐 Bahasa Output", options=["Indonesia","Malaysia","English"])
    jumlah = st.number_input("🔢 Jumlah Copywriting yang Diinginkan", min_value=1, max_value=20, value=3, step=1)
    model = st.selectbox("🤖 Pilih Model ChatGPT", options=["gpt-4o-mini","gpt-4o","gpt-4","gpt-3.5-turbo"])

    submitted = st.form_submit_button("Generate Copywriting")

# ─────────────────────────────────────────────────────────────────────────────
if submitted:
    if not nama_produk.strip():
        st.warning("Mohon isi **Nama Produk** terlebih dahulu.")
        st.stop()

    # 2) Bila ada video referensi, transcribe dulu
    transcript = None
    if video_link or uploaded_file:
        with st.spinner("🔊 Transcribing video…"):
            # simpan video ke temp
            tmp_vid = os.path.join(tempfile.gettempdir(), "ref_video.mp4")
            if video_link:
                ydl_opts = {
                    "format": "mp4",
                    "outtmpl": tmp_vid,
                    "logger": StreamlitLogger(),
                    "progress_hooks": [progress_hook],
                    "http_headers": {"User-Agent": "Mozilla/5.0"}
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # cek URL dulu
                    ydl.extract_info(video_link, download=False)
                    ydl.download([video_link])
            else:
                tmp_vid = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(tmp_vid, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # ekstrak audio
            audio_path = os.path.join(tempfile.gettempdir(), "ref_audio.wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", tmp_vid,
                "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", audio_path
            ], check=True)

            # transcribe pake Whisper
            whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(audio_path)
            transcript = res.get("text", "").strip()

    # 3) Siapkan pesan ke OpenAI
    messages: List[dict] = [{
        "role": "system",
        "content": (
            "Kamu adalah ahli copywriting TikTok dengan gaya lucu, santai, "
            "dan mengundang perhatian. Hasil harus dalam kalimat utuh: hook – body – CTA."
        )
    }]

    user_prompt = f"Buatkan {jumlah} copywriting promosi produk TikTok.\nProduk: {nama_produk}.\n"
    if fitur_produk.strip():
        user_prompt += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip():
        user_prompt += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"
    if transcript:
        user_prompt += f"Transkrip video referensi: {transcript}.\n"

    # panduan gaya
    guide = """Syarat:
- Awali dengan kalimat yang mengundang perhatian atau bikin shock.
- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal.
- Akhiri dengan ajakan cek keranjang kuning!
- Hindari tanda petik (" atau ')—emoji juga tidak usah.
- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.
- Jangan gunakan nomor, bullet point, atau daftar.
"""
    user_prompt += guide
    messages.append({"role":"user","content":user_prompt})

    # 4) Panggil OpenAI
    with st.spinner("🚀 Menghubungi OpenAI…"):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=jumlah * 150,
            )
        except Exception as e:
            st.error(f"❌ Gagal generate: {e}")
            st.stop()
        result = response.choices[0].message.content.strip()

    # 5) Tampilkan hasil dan beri opsi edit/download
    st.subheader("Hasil Copywriting")
    edited = st.text_area("✏️ Kamu bisa edit hasil di sini:", value=result, height=300)

    st.download_button(
        "📥 Unduh sebagai .txt",
        edited,
        file_name=f"copywriting_{nama_produk.replace(' ','_')}.txt",
        mime="text/plain",
    )
