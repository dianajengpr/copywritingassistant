import streamlit as st
import openai
import os

# ————————————————
# 🔑 Load API Key dari Streamlit Secrets
# ————————————————
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai.api_key:
    st.error("OpenAI API Key belum diatur. Silakan tambahkan ke Secrets di Streamlit.")
    st.stop()

# ————————————————
# ⚙️ Setup halaman
# ————————————————
st.set_page_config(
    page_title="Copywriting Assistant by PERKA",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Copywriting Assistant by PERKA")
st.markdown(
    "Buat copywriting santai & lucu untuk video TikTok produkmu. "
    "Isi form di bawah, lalu tekan **Generate**!"
)

# ————————————————
# 🖊️ Form Input Utama
# ————————————————
nama_produk = st.text_input(
    "📌 Nama Produk (wajib)", 
    placeholder="Contoh: Silikon Keran Air"
)

# ————————————————
# 📑 Referensi Gaya Copywriting (opsional, hingga 3)
# ————————————————
st.header("📑 Referensi Gaya Copywriting (opsional, hingga 3)")
link_refs = []
file_refs = []
for i in range(1, 4):
    col_link, col_file = st.columns(2)
    link = col_link.text_input(
        f"Referensi {i} – Link Video (opsional)",
        placeholder="https://...",
        key=f"link_ref_{i}"
    )
    file = col_file.file_uploader(
        f"Referensi {i} – File Video (opsional)",
        type=["mp4", "mov", "webm", "mpeg4"],
        key=f"file_ref_{i}"
    )
    link_refs.append(link)
    file_refs.append(file)

# ————————————————
# ➕ Fitur / Keunggulan & Prompt Tambahan
# ————————————————
fitur_produk = st.text_area(
    "💡 Fitur atau Keunggulan Produk (opsional)",
    placeholder="Contoh: Anti bocor, mudah dipasang"
)
prompt_tambahan = st.text_area(
    "✏️ Prompt Tambahan (opsional)",
    placeholder="Instruksi khusus …"
)

# ————————————————
# 🌐 Pilihan Bahasa & Jumlah & Model
# ————————————————
bahasa = st.selectbox(
    "🌐 Bahasa Output (wajib)",
    ["Indonesia", "Inggris", "Malaysia"]
)
jumlah = st.number_input(
    "🔢 Jumlah Copywriting yang Diinginkan (wajib)",
    min_value=1, value=5, step=1
)
model = st.selectbox(
    "🤖 Pilih Model ChatGPT",
    ["gpt-3.5-turbo", "gpt-4o-mini"]
)

# ————————————————
# ▶️ Tombol Generate
# ————————————————
if st.button("Generate"):
    if not nama_produk:
        st.error("⚠️ Nama Produk wajib diisi!")
    else:
        with st.spinner("⌛ Generating copywriting..."):
            # ————————————————
            # 🔧 Bangun Prompt
            # ————————————————
            system_prompt = (
                "Kamu adalah ahli copywriting TikTok dengan gaya lucu dan santai."
            )
            user_prompt = (
                f"Buatkan {jumlah} copywriting promosi produk untuk TikTok. "
                f"Nama produknya adalah '{nama_produk}'."
            )

            # Tambah referensi jika ada
            refs = []
            for lk, fl in zip(link_refs, file_refs):
                if lk:
                    refs.append(lk)
                elif fl:
                    refs.append(f"<video di-upload>")
            if refs:
                user_prompt += (
                    " Gaya copywriting-nya tolong sesuaikan dengan gaya dari referensi berikut: "
                    + ", ".join(refs)
                    + "."
                )

            # Fitur & tambahan
            if fitur_produk:
                user_prompt += f" Fitur produk yang perlu disertakan: {fitur_produk}."
            if prompt_tambahan:
                user_prompt += f" Instruksi tambahan: {prompt_tambahan}."
            user_prompt += f" Bahasa yang digunakan: {bahasa}."

            # Syarat‐syarat final
            user_prompt += (
                "\n\nSyarat:\n"
                "- Awali dengan kalimat yang mengundang perhatian atau bikin shock\n"
                "- Jelaskan keunggulan produk secara singkat dan natural tanpa kesan iklan formal\n"
                "- Akhiri dengan ajakan like dan komen dengan format: mau promo [kategori produk]!\n"
                "- Hindari tanda petik (\" atau ') dan emoji\n"
                "- Gunakan tanda baca seperti ! dan ? untuk penekanan\n"
                "Jangan beri penomoran atau bullet point."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]

            try:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                )
                hasil = resp.choices[0].message.content.strip()

                st.text_area(
                    "✍️ Hasil Copywriting (bisa diedit kalau mau)",
                    value=hasil,
                    height=300
                )
            except Exception as e:
                st.error(f"❌ Error: {e}")

