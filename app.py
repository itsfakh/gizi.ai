import json
import streamlit as st
from PIL import Image
from google import genai

# ==========================
# KONFIGURASI HALAMAN
# ==========================

st.set_page_config(
    page_title="CekGizi AI",
    page_icon="🥗",
    layout="wide"
)

st.title("🥗 CekGizi - Deteksi Kalori Jajananmu")

st.write("""
Upload foto makanan atau ambil foto langsung dari kamera.

AI akan memberikan:
- Nama makanan
- Estimasi kalori
- Protein
- Karbohidrat
- Lemak
- Tips kesehatan
""")

# ==========================
# API KEY
# ==========================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    st.error("GEMINI_API_KEY tidak ditemukan.")
    st.stop()

client = genai.Client(api_key=api_key)

# ==========================
# INPUT FOTO
# ==========================

tab1, tab2 = st.tabs(["📷 Kamera", "📁 Upload"])

with tab1:
    camera_image = st.camera_input("Ambil Foto Makanan")

with tab2:
    uploaded_file = st.file_uploader(
        "Upload Foto",
        type=["jpg", "jpeg", "png"]
    )

image_file = camera_image if camera_image else uploaded_file

# ==========================
# ANALISIS
# ==========================

if image_file:

    image = Image.open(image_file)

    st.image(
        image,
        caption="Gambar yang dianalisis",
        use_container_width=True
    )

    if st.button("🔍 Analisis Nutrisi"):

        with st.spinner("Sedang menganalisis..."):

            prompt = """
Anda adalah ahli gizi profesional.

Lihat gambar makanan yang diberikan.

Balas HANYA dalam format JSON berikut:

{
  "nama_makanan": "",
  "kalori_kcal": "",
  "protein_g": "",
  "karbohidrat_g": "",
  "lemak_g": "",
  "tips": ""
}

Jangan menambahkan markdown.
Jangan menambahkan penjelasan lain.
"""

            try:

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        prompt,
                        image
                    ]
                )

                result_text = response.text

                # Bersihkan jika model menambahkan ```json
                result_text = result_text.replace(
                    "```json",
                    ""
                ).replace(
                    "```",
                    ""
                ).strip()

                data = json.loads(result_text)

                st.success("Analisis berhasil!")

                st.subheader(
                    f"🍽️ {data['nama_makanan']}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Kalori",
                        data["kalori_kcal"]
                    )

                with col2:
                    st.metric(
                        "Protein",
                        data["protein_g"]
                    )

                with col3:
                    st.metric(
                        "Karbohidrat",
                        data["karbohidrat_g"]
                    )

                with col4:
                    st.metric(
                        "Lemak",
                        data["lemak_g"]
                    )

                st.info(
                    f"💡 {data['tips']}"
                )

            except Exception as e:

                st.error(
                    f"Gagal menganalisis gambar: {e}"
                )
