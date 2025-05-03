import streamlit as st
import openai
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()
openai.api_key = st.secrets["OPENAI_API_KEY"]

if not api_key:
    st.error("OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="Copywriting Assistant by PERKA", page_icon="🧠")

st.title("🧠 Copywriting Assistant by PERKA")

st.markdown("Buat copywriting lucu, santai, dan menghibur untuk video TikTok.")

product_name = st.text_input("Nama Produk (wajib)")
video_url = st.text_input("Link Video Contoh (opsional)")
features = st.text_area("Fitur atau Keunggulan Produk (opsional)")
custom_prompt = st.text_area("Prompt Tambahan (opsional)")
language = st.selectbox("Bahasa", ["Indonesia", "Malaysia"])
num_texts = st.slider("Jumlah Copywriting yang Ingin Dihasilkan", 1, 10, 3)

if st.button("Generate"):
    if not product_name:
        st.error("Nama Produk wajib diisi.")
        st.stop()

    with st.spinner("Sedang membuat copywriting..."):
        prompt = f"""
Buatkan {num_texts} teks voice over TikTok dengan gaya santai, lucu, dan menghibur untuk produk bernama '{product_name}'.
Jika diberikan contoh video, tiru gaya copywriting-nya (bukan suaranya).
Gunakan bahasa {language}.

Fitur produk: {features if features else "-"}
Link video contoh (opsional): {video_url if video_url else "-"}
Permintaan khusus: {custom_prompt if custom_prompt else "-"}

Syarat:
- Awali dengan kalimat yang mengundang perhatian atau bikin shock
- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal
- Akhiri dengan ajakan like dan komen dengan format: mau promo [kategori produk]!
- Hindari tanda petik (" atau ') dan emoji
- Gunakan tanda baca seperti ! dan ? untuk penekanan

Format: hasilkan dalam bentuk kalimat copywriting, bukan poin-poin atau daftar terstruktur.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Kamu adalah copywriter profesional spesialis TikTok."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=1200
            )
            result = response.choices[0].message.content.strip()
            st.success("✅ Copywriting berhasil dibuat!")
            st.text_area("Hasil Copywriting", result, height=400)
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")
