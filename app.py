import streamlit as st
import openai

# Ambil API key dari Streamlit Secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()

openai.api_key = api_key

# Konfigurasi halaman
st.set_page_config(page_title="Copywriting Assistant by PERKA", page_icon="🧠")
st.title("📝 Copywriting Assistant by PERKA")
st.markdown("Buat copywriting TikTok yang meniru gaya copywriting dari referensi video atau berdasarkan detail produk.")

# Pilih model ChatGPT
model_choice = st.selectbox(
    "Pilih Model ChatGPT:",
    ["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
    index=0
)

# Form input
with st.form("form_copywriting"):
    # 1. Nama produk
    nama_produk = st.text_input("Nama Produk (wajib)", placeholder="Contoh: Silikon Keran Air 20 pcs")
    
    # 2. Referensi (maksimal 3): link atau upload
    st.markdown("**Referensi Gaya Copywriting (opsional, hingga 3)**")
    ref1_link = st.text_input("Referensi 1 - Link Video (opsional)")
    ref1_file = st.file_uploader("Referensi 1 - Upload File Video (opsional)", type=["mp4", "mov", "webm"], key="file1")
    ref2_link = st.text_input("Referensi 2 - Link Video (opsional)")
    ref2_file = st.file_uploader("Referensi 2 - Upload File Video (opsional)", type=["mp4", "mov", "webm"], key="file2")
    ref3_link = st.text_input("Referensi 3 - Link Video (opsional)")
    ref3_file = st.file_uploader("Referensi 3 - Upload File Video (opsional)", type=["mp4", "mov", "webm"], key="file3")
    
    # 3. Fitur atau keunggulan produk
    fitur_produk = st.text_area("Fitur atau Keunggulan Produk (opsional)", placeholder="Contoh: Anti bocor, mudah dipasang, tanpa alat")
    
    # 4. Prompt tambahan
    prompt_tambahan = st.text_area("Prompt Tambahan (opsional)", placeholder="Contoh: Gaya lucu tapi tidak berlebihan")
    
    # 5. Bahasa output dan jumlah teks
    bahasa = st.selectbox("Bahasa Output (wajib)", ["Indonesia", "Malaysia"])
    jumlah = st.text_input("Jumlah Copywriting yang Diinginkan (wajib)", "3")
    
    submit = st.form_submit_button("Generate Copywriting")

# Proses saat form disubmit
if submit:
    if not nama_produk:
        st.error("Nama Produk wajib diisi!")
    else:
        # Validasi jumlah
        try:
            jumlah_int = int(jumlah)
        except ValueError:
            st.error("Jumlah Copywriting harus berupa angka")
            st.stop()
        with st.spinner("Sedang membuat copywriting..."):
            # Kumpulkan referensi gaya
            refs = []
            for link, file in [(ref1_link, ref1_file), (ref2_link, ref2_file), (ref3_link, ref3_file)]:
                if link:
                    refs.append(link)
                elif file:
                    refs.append("video yang diunggah")
            # Bangun bagian referensi dalam prompt
            ref_text = ""
            if refs:
                ref_list = ", ".join(refs)
                ref_text = f" Gaya copywriting-nya tolong sesuaikan dengan gaya dari video berikut: {ref_list}."

            # Buat prompt dasar
            base_prompt = f"Buatkan {jumlah_int} copywriting promosi produk untuk TikTok. Nama produknya adalah '{nama_produk}'."
            base_prompt += ref_text
            if fitur_produk:
                base_prompt += f" Fitur produk yang perlu disertakan: {fitur_produk}."
            if prompt_tambahan:
                base_prompt += f" Instruksi tambahan: {prompt_tambahan}."
            base_prompt += f" Bahasa yang digunakan: {bahasa}."
            # Tambahkan syarat
            base_prompt += " Syarat:\n"
            base_prompt += "- Awali dengan kalimat yang mengundang perhatian atau bikin shock\n"
            base_prompt += "- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal\n"
            base_prompt += "- Akhiri dengan ajakan like dan komen dengan format: mau promo [kategori produk]!\n"
            base_prompt += "- Hindari tanda petik (\" atau ') dan emoji\n"
            base_prompt += "- Gunakan tanda baca seperti ! dan ? untuk penekanan"

            # Panggil OpenAI
            try:
                response = openai.ChatCompletion.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "Kamu adalah ahli copywriting TikTok dengan gaya kreatif dan menghibur."},
                        {"role": "user", "content": base_prompt}
                    ],
                    temperature=0.9
                )
                hasil = response.choices[0].message.content.strip()

                # Tampilkan hasil
                st.subheader("📋 Hasil Copywriting")
                edited = st.text_area("Edit hasil jika perlu:", value=hasil, height=300)
                st.download_button(
                    label="📥 Download Hasil Copywriting",
                    data=edited,
                    file_name="copywriting.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Terjadi error saat generate copywriting: {e}")
