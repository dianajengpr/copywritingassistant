import streamlit as st
import openai
import os

# Judul dan branding
st.set_page_config(page_title="Copywriting Assistant", layout="centered")
st.title("📝 Copywriting Assistant")
st.caption("Built by PERKA")

# API Key (isi manual langsung di Streamlit secret atau variable lokal)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Form Input
with st.form("input_form"):
    nama_produk = st.text_input("Nama Produk (wajib)")
    link_video = st.text_input("Link Video Contoh (opsional)")
    fitur_produk = st.text_area("Fitur / Keunggulan Produk (opsional)")
    prompt_tambahan = st.text_area("Prompt Tambahan (opsional)")
    bahasa = st.selectbox("Bahasa", ["Bahasa Indonesia", "Bahasa Malaysia"])
    jumlah = st.slider("Jumlah Copywriting yang Ingin Dihasilkan", 1, 10, 3)
    submit = st.form_submit_button("Generate")

if submit:
    if not nama_produk:
        st.error("⚠️ Nama produk wajib diisi.")
    else:
        with st.spinner("⏳ Generating copywriting..."):
            # Buat prompt dasar
            base_prompt = f"Buatkan {jumlah} copywriting promosi produk untuk TikTok. Nama produknya adalah '{nama_produk}'."
            if link_video:
                base_prompt += f" Gaya copywriting-nya tolong sesuaikan dengan gaya dari video ini: {link_video}."
            if fitur_produk:
                base_prompt += f" Fitur produk yang perlu disertakan: {fitur_produk}."
            if prompt_tambahan:
                base_prompt += f" Instruksi tambahan: {prompt_tambahan}."
            base_prompt += f" Bahasa yang digunakan: {bahasa}. "
            base_prompt += "Hindari penggunaan tanda petik satu (') dan dua (\"). Gunakan tanda seru (!) dan tanda tanya (?) jika perlu. Jangan beri penomoran atau bullet point."

            # Request ke OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Kamu adalah copywriter profesional spesialis konten TikTok."},
                        {"role": "user", "content": base_prompt}
                    ],
                    temperature=0.8
                )

                hasil = response.choices[0].message.content.strip()
                st.subheader("Hasil Copywriting")
                result_text = st.text_area("Hasil (bisa diedit)", value=hasil, height=300)
                st.download_button("📥 Download hasil", result_text, file_name="copywriting.txt")

            except Exception as e:
                st.error(f"❌ Error: {e}")
