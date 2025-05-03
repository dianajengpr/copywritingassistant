import streamlit as st
import openai
import os
from dotenv import load_dotenv
from typing import List

# ——————————————————————————————————————————————————————————————
#              Inisialisasi & Authentication
# ——————————————————————————————————————————————————————————————
load_dotenv()  # baca .env kalau jalan lokal
# Ambil API key dari env atau Streamlit Secrets
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()
openai.api_key = api_key

st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="✍️",
    layout="centered"
)

# ——————————————————————————————————————————————————————————————
#                       Judul & Deskripsi
# ——————————————————————————————————————————————————————————————
st.title("✍️ Copywriting Assistant by PERKA")
st.markdown(
    "Buat copywriting **lucu**, **santai**, dan **mengundang perhatian** untuk video TikTok, "
    "Instagram Reels, YouTube Shorts, atau platform serupa."
)

# ——————————————————————————————————————————————————————————————
#                         Input Form
# ——————————————————————————————————————————————————————————————
# 1. Nama Produk
nama_produk = st.text_input("🔖 Nama Produk (wajib)", placeholder="Misal: Silikon Keran Air")

# 2. Pilih Model
model = st.selectbox(
    "🤖 Pilih Model ChatGPT",
    ["gpt-3.5-turbo", "gpt-4o-mini"]
)

# 3. Referensi Gaya Copywriting (opsional, hingga 3)
st.markdown("#### 📑 Referensi Gaya Copywriting (opsional, hingga 3)")
link_refs: List[str] = []
file_refs: List[bytes] = []
for i in range(1, 4):
    col_link, col_file = st.columns([2, 3])
    link = col_link.text_input(
        f"Referensi {i} – Link Video (opsional)",
        placeholder="https://...",
        key=f"link_ref_{i}"
    )
    file = col_file.file_uploader(
        f"Referensi {i} – Upload File Video (opsional)",
        type=["mp4", "mov", "webm", "mpeg4"],
        key=f"file_ref_{i}"
    )
    link_refs.append(link)
    file_refs.append(file)

# 4. Fitur atau Keunggulan (opsional)
fitur_produk = st.text_area(
    "💡 Fitur atau Keunggulan Produk (opsional)",
    placeholder="Misal: Mudah dipasang tanpa alat"
)

# 5. Prompt Tambahan (opsional)
prompt_tambahan = st.text_area(
    "✏️ Prompt Tambahan (opsional)",
    placeholder="Instruksi khusus, contohnya: 'gunakan gaya gaul anak muda'"
)

# 6. Bahasa Output
bahasa = st.selectbox(
    "🌐 Bahasa Output (wajib)",
    ["Indonesia", "English", "Malaysia"]
)

# 7. Jumlah Copywriting
jumlah = st.number_input(
    "🔢 Jumlah Copywriting yang Diinginkan (wajib)",
    min_value=1, max_value=20, value=5, step=1
)

# ——————————————————————————————————————————————————————————————
#                    Tombol Generate & Proses
# ——————————————————————————————————————————————————————————————
if st.button("🚀 Generate"):
    if not nama_produk:
        st.error("Nama Produk harus diisi.")
        st.stop()

    # — bangun prompt dasar
    base_prompt = f"Buatkan {jumlah} copywriting promosi produk untuk TikTok dengan format hook lucu, deskripsi singkat, dan call to action.\n"
    base_prompt += f"Nama produk: {nama_produk}.\n"

    # masukkan referensi jika ada
    refs = []
    for idx in range(3):
        if link_refs[idx]:
            refs.append(f"Referensi{idx+1} Link: {link_refs[idx]}")
        elif file_refs[idx]:
            refs.append(f"Referensi{idx+1} (video diunggah).")
    if refs:
        base_prompt += "Sesuaikan gaya copywriting dengan referensi: " + "; ".join(refs) + ".\n"

    # fitur & prompt tambahan
    if fitur_produk:
        base_prompt += f"Fitur produk yang perlu disertakan: {fitur_produk}.\n"
    if prompt_tambahan:
        base_prompt += f"Instruksi tambahan: {prompt_tambahan}.\n"

    base_prompt += f"Bahasa: {bahasa}.\n"

    # syarat‐syarat khusus
    base_prompt += (
        "Syarat:\n"
        "- Awali dengan kalimat yang mengundang perhatian atau bikin shock\n"
        "- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal\n"
        "- Akhiri dengan ajakan like dan komen dengan format: mau promo [kategori produk]!\n"
        "- Hindari tanda petik (\" atau ')\n"
        "- Gunakan tanda baca seperti ! dan ? untuk penekanan\n"
        "Jangan beri nomor atau bullet point.\n"
    )

    # panggil API
    with st.spinner("Generating..."):
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Kamu adalah ahli copywriting TikTok dengan gaya lucu dan santai."},
                {"role": "user", "content": base_prompt}
            ],
            max_tokens=800,
            temperature=0.8,
            n=1
        )
    teks_hasil = resp.choices[0].message.content.strip()

    # tampilkan hasil
    st.success("✅ Copywriting berhasil dibuat!")
    st.text_area("📄 Hasil Copywriting", value=teks_hasil, height=300)

