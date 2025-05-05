import streamlit as st
import openai
import os
from typing import List

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
    Tinggal isi data produk, pilih output, dan dapatkan copywriting yang siap tarik perhatian di FYP.
    """
)

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
#  2) When user clicks generate
if submitted:
    if not nama_produk.strip():
        st.warning("Mohon isi **Nama Produk** terlebih dahulu.")
    else:
        # Build system+user prompt
        messages: List[dict] = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah ahli copywriting TikTok dengan gaya lucu, santai, dan "
                    "mengundang perhatian. Hasil harus dalam kalimat utuh: hook – body – CTA."
                )
            }
        ]

        # Construct user prompt
        user_prompt = (
            f"Buatkan {jumlah} copywriting promosi produk TikTok.\n"
            f"Produk: {nama_produk}.\n"
        )
        if fitur_produk.strip():
            user_prompt += f"Keunggulan: {fitur_produk.strip()}.\n"
        if prompt_tambahan.strip():
            user_prompt += f"Instruksi tambahan: {prompt_tambahan.strip()}.\n"
        user_prompt += (
            f"Bahasa: {bahasa}.\n"
            "Syarat:\n"
            "- Awali dengan kalimat yang mengundang perhatian atau bikin shock.\n"
            "- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal.\n"
            "- Akhiri dengan ajakan cek keranjang kuning!\n"
            "- Hindari tanda petik (\" atau ')—emoji juga tidak usah.\n"
            "- Gunakan tanda seru (!) dan tanya (?) untuk penekanan.\n"
            "- Jangan gunakan nomor, bullet point, atau daftar."
        )
        messages.append({"role": "user", "content": user_prompt})

        # Call OpenAI
        with st.spinner("🚀 Menghubungi OpenAI…"):
            try:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens= jumlah * 150,
                )
                result = response.choices[0].message.content.strip()
            except Exception as e:
                st.error(f"❌ Gagal generate: {e}")
                st.stop()

        # 3) Display and allow editing
        st.subheader("Hasil Copywriting")
        edited = st.text_area(
            "✏️ Anda bisa edit hasil di sini jika perlu:",
            value=result,
            height=300
        )

        # 4) (optional) Export button
        st.download_button(
            "📥 Unduh sebagai .txt",
            edited,
            file_name=f"copywriting_{nama_produk.replace(' ','_')}.txt",
            mime="text/plain",
        )
