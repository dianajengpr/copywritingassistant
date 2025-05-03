import streamlit as st
import openai
import os
from dotenv import load_dotenv
from typing import List

# ——————————————————————————————————————————————————————————————
#            Inisialisasi API Key
# ——————————————————————————————————————————————————————————————
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")

if not openai.api_key:
    st.error("OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()

# ——————————————————————————————————————————————————————————————
#                 Konfigurasi Halaman
# ——————————————————————————————————————————————————————————————
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Copywriting Assistant by PERKA")

# ——————————————————————————————————————————————————————————————
#                        Form Input Utama
# ——————————————————————————————————————————————————————————————

# 1) Nama Produk (wajib)
nama_produk = st.text_input("Nama Produk (wajib)", placeholder="Contoh: Silikon Keran Air")
if not nama_produk:
    st.warning("Mohon isi Nama Produk.")
    st.stop()

# 2) Referensi: Upload File Video (opsional)
st.markdown("#### Upload File Video (opsional)")
col_u1, col_u2, col_u3 = st.columns(3)
file_ref1 = col_u1.file_uploader("Kolom 1", type=["mp4","mov","webm","mpeg4"], key="file1")
file_ref2 = col_u2.file_uploader("Kolom 2", type=["mp4","mov","webm","mpeg4"], key="file2")
file_ref3 = col_u3.file_uploader("Kolom 3", type=["mp4","mov","webm","mpeg4"], key="file3")

# 3) Referensi: Link Video (opsional)
st.markdown("#### Link Video (opsional)")
col_l1, col_l2, col_l3 = st.columns(3)
link_ref1 = col_l1.text_input("Kolom 1", key="link1", placeholder="https://...")
link_ref2 = col_l2.text_input("Kolom 2", key="link2", placeholder="https://...")
link_ref3 = col_l3.text_input("Kolom 3", key="link3", placeholder="https://...")

# 4) Fitur atau Keunggulan Produk (opsional)
fitur = st.text_area("Fitur atau Keunggulan Produk (opsional)", height=60, placeholder="Bahan tahan panas; Mudah dipasang; dll.")

# 5) Prompt Tambahan (opsional)
prompt_tambahan = st.text_area("Prompt Tambahan (opsional)", height=60, placeholder="Contoh: Tonya harus menonjolkan sisi kekinian.")

# 6) Bahasa Output (wajib)
bahasa = st.selectbox(
    "Bahasa Output (wajib)",
    ["Indonesia", "Malaysia", "English"],
    index=0
)

# 7) Jumlah Copywriting yang Diinginkan (wajib)
jumlah = st.number_input(
    "Jumlah Copywriting yang Diinginkan (wajib)",
    min_value=1, max_value=20, value=5, step=1
)

# 8) Pilih Model
model = st.selectbox(
    "Pilih Model ChatGPT",
    ["gpt-4o-mini","gpt-4o","gpt-3.5-turbo","gpt-4"],
    index=0
)

# ——————————————————————————————————————————————————————————————
#                              Generate Button
# ——————————————————————————————————————————————————————————————
if st.button("Generate"):
    with st.spinner("Membuat copywriting…"):
        # 1) Buat base prompt sesuai syarat
        base_prompt = (
            f"Buatkan {jumlah} copywriting promosi produk untuk TikTok. "
            f"Nama produknya adalah '{nama_produk}'. "
        )
        # referensi link/video
        refs = []
        for i, (lf, ll) in enumerate([(file_ref1, link_ref1),
                                      (file_ref2, link_ref2),
                                      (file_ref3, link_ref3)], start=1):
            if ll:
                refs.append(f"Link{ i }:{ ll }")
            elif lf:
                refs.append(f"File{ i } diberikan sebagai referensi gaya.")
        if refs:
            base_prompt += "Sesuaikan gaya copywriting dengan referensi berikut: " + "; ".join(refs) + ". "
        # fitur, tambahan, bahasa
        if fitur:
            base_prompt += f"Fitur produk yang perlu disertakan: {fitur}. "
        if prompt_tambahan:
            base_prompt += f"Instruksi tambahan: {prompt_tambahan}. "
        base_prompt += f"Bahasa yang digunakan: {bahasa}. "
        # syarat khusus
        base_prompt += (
            "Awali dengan kalimat yang mengundang perhatian atau bikin shock. "
            "Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal. "
            "Akhiri dengan ajakan like dan komen dengan format: mau promo [kategori produk]! "
            "Hindari tanda petik (\" atau ') dan emoji. "
            "Gunakan tanda baca ! dan ? untuk penekanan. "
            "Jangan pakai nomor atau bullet point."
        )

        # 2) Bangun messages
        messages = [
            {"role": "system", "content": "Kamu adalah ahli copywriting TikTok dengan gaya lucu dan santai."},
            {"role": "user", "content": base_prompt}
        ]

        # 3) Panggil OpenAI
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        hasil = resp.choices[0].message.content.strip()

    # 4) Tampilkan hasil, editable
    st.markdown("#### Hasil Copywriting (boleh edit sebelum disalin)")
    hasil_edit = st.text_area("Copywriting", value=hasil, height=300)

    # 5) Tombol untuk salin ke clipboard
    if st.button("📋 Salin ke Clipboard"):
        st.write("✓ Tersalin!")

