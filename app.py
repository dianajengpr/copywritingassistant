import streamlit as st
import openai
import os
import tempfile
from typing import List
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
# Load your OpenAI key from Streamlit secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")
if not openai.api_key:
    st.error("⚠️ OpenAI API Key belum diatur. Tambahkan ke Secrets di Streamlit.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# App config & header
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide",
)
st.title("📝 Copywriting Assistant by **PERKA**")
st.markdown(
    """
    **Asisten Copywriting TikTok kamu— otomatis, praktis, dan siap jualan!**
    Isi data produk, unggah atau link video referensi (opsional), lalu generate copywriting.
    """
)

# ─────────────────────────────────────────────────────────────────────────────
# 1) Form inputs
with st.form("copy_form", clear_on_submit=False):
    st.subheader("Input Data Produk")
    nama_produk = st.text_input("📌 Nama Produk", placeholder="Contoh: Silikon Keran Air", help="(wajib)")
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
    if video_link or uploaded_file:
        with st.spinner("🔊 Mengambil & transkrip video…"):
            # simpan video temporary
            tmp_vid = os.path.join(tempfile.gettempdir(), "ref_video.mp4")
            if video_link:
                opts = {"format":"bestvideo[ext=mp4]+bestaudio[ext=m4a]/best","outtmpl":tmp_vid,
                        "logger":StreamlitLogger(),"progress_hooks":[progress_hook],
                        "http_headers":{"User-Agent":"Mozilla/5.0"}}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(video_link, download=False)
                    ydl.download([video_link])
            else:
                tmp_vid = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(tmp_vid, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            # transkrip langsung via OpenAI Whisper API (tanpa ffmpeg lokal)
            with open(tmp_vid, "rb") as audio_f:
                res = openai.Audio.transcribe("whisper-1", audio_f)
            transcript = res.get("text", "").strip()

    # siapkan prompt
    system_msg = {"role":"system","content":(
        "Kamu ahli copywriting TikTok: gaya lucu, santai, perhatian; "
        "struktur utuh: hook – body – CTA."
    )}
    user_msg = f"Buatkan {jumlah} copywriting promosi produk TikTok.\nProduk: {nama_produk}.\n"
    if fitur_produk.strip(): user_msg += f"Keunggulan: {fitur_produk.strip()}.\n"
    if prompt_tambahan.strip(): user_msg += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"
    if transcript: user_msg += f"Transkrip video referensi: {transcript}.\n"
    user_msg += (
        f"Bahasa: {bahasa}.\n" +
        "Syarat:\n" +
        "- Awali dengan kalimat bikin shock.!\n" +
        "- Jelaskan keunggulan natural tanpa kesan formal.\n" +
        "- Akhiri cek keranjang kuning!\n" +
        "- Hindari tanda petik (\" atau ')—emoji tidak usah.\n" +
        "- Pakai ! dan ? untuk penekanan.\n" +
        "- Tanpa bullet, nomor, atau daftar."
    )
    # request ke OpenAI
    with st.spinner("🚀 Menghubungi OpenAI…"):
        try:
            resp = openai.ChatCompletion.create(
                model=model, messages=[system_msg,{"role":"user","content":user_msg}],
                temperature=0.7, max_tokens=jumlah*150
            )
            hasil = resp.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Gagal generate: {e}")
            st.stop()

    # tampil dan export
    st.subheader("Hasil Copywriting")
    ed = st.text_area("✏️ Edit jika perlu:", value=hasil, height=300)
    st.download_button("📥 Unduh .txt", ed, file_name=f"cw_{nama_produk.replace(' ','_')}.txt", mime="text/plain")
