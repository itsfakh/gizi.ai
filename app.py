import json
import streamlit as st
from PIL import Image
from google import genai

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="CekGizi AI",
    page_icon="🥗",
    layout="wide"
)

# ==================================
# CUSTOM CSS
# ==================================

st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(
        135deg,
        #f0fdf4,
        #ecfeff
    );
}

/* Hero Section */
.hero {
    background: linear-gradient(
        90deg,
        #10b981,
        #22c55e
    );
    padding: 30px;
    border-radius: 25px;
    text-align: center;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
}

/* Cards */
.card {
    background: white;
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white;
    border-radius: 20px;
    padding: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
}

/* Button */
.stButton > button {
    width: 100%;
    height: 55px;
    border-radius: 15px;
    border: none;
    background: #10b981;
    color: white;
    font-size: 18px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #059669;
    color: white;
}

/* Upload */
[data-testid="stFileUploader"] {
    background: white;
    border-radius: 15px;
    padding: 10px;
}

/* Success */
.stSuccess {
    border-radius: 15px;
}

</style>
""", unsafe_allow_html=True)

# ==================================
# HEADER
# ==================================

st.markdown("""
<div class="hero">
    <h1>🥗 CekGizi AI</h1>
    <p style="font-size:18px;">
        Deteksi Kalori & Nutrisi Makanan dengan AI
    </p>
</div>
""", unsafe_allow_html=True)

# ==================================
# DESKRIPSI
# ==================================

st.markdown("""
<div class="card">
<h3>✨ Cara Menggunakan</h3>

1️⃣ Upload foto makanan atau gunakan kamera

2️⃣ Klik tombol Analisis Nutrisi

3️⃣ AI akan memperkirakan:

- Nama makanan
- Kalori
- Protein
- Karbohidrat
- Lemak
- Tips kesehatan

</div>
""", unsafe_allow_html=True)

# ==================================
# API KEY
# ==================================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("GEMINI_API_KEY tidak ditemukan.")
    st.stop()

client = genai.Client(api_key=api_key)

# ==================================
# INPUT FOTO
# ==================================

left_col, right_col = st.columns([1, 1])

with left_col:

    st.markdown("""
    <div class="card">
        <h3>📷 Upload Foto Makanan</h3>
        Gunakan kamera atau unggah dari galeri.
    </div>
    """, unsafe_allow_html=True)

    camera_image = st.camera_input(
        "Ambil Foto"
    )

    uploaded_file = st.file_uploader(
        "Atau Upload Foto",
        type=["jpg", "jpeg", "png"]
    )

image_file = camera_image if camera_image else uploaded_file

with right_col:

    st.markdown("""
    <div class="card">
        <h3>🖼️ Preview Gambar</h3>
    </div>
    """, unsafe_allow_html=True)

    if image_file:

        image = Image.open(image_file)

        st.image(
            image,
            use_container_width=True
        )

    else:

        st.info(
            "Upload foto makanan untuk melihat preview."
        )

# ==================================
# ANALISIS
# ==================================

if image_file:

    image = Image.open(image_file)

    st.markdown("<br>", unsafe_allow_html=True)

    analyze = st.button(
        "🔍 Analisis Nutrisi"
    )

    if analyze:

        with st.spinner(
            "🤖 AI sedang menganalisis makanan..."
        ):

            prompt = """
Anda adalah ahli gizi profesional.

Lihat gambar makanan yang diberikan.

Balas HANYA dalam format JSON berikut:

{
  "nama_makanan":"",
  "kalori_kcal":"",
  "protein_g":"",
  "karbohidrat_g":"",
  "lemak_g":"",
  "tips":""
}

Jangan gunakan markdown.
Jangan gunakan penjelasan tambahan.
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

                result_text = result_text.replace(
                    "```json",
                    ""
                ).replace(
                    "```",
                    ""
                ).strip()

                data = json.loads(
                    result_text
                )

                st.success(
                    "Analisis berhasil!"
                )

                st.markdown(
                    f"""
                    <div class="card">
                    <h2>🍽️ {data['nama_makanan']}</h2>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "🔥 Kalori",
                        data["kalori_kcal"]
                    )

                with col2:
                    st.metric(
                        "💪 Protein",
                        data["protein_g"]
                    )

                with col3:
                    st.metric(
                        "🍚 Karbohidrat",
                        data["karbohidrat_g"]
                    )

                with col4:
                    st.metric(
                        "🥑 Lemak",
                        data["lemak_g"]
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                    f"""
                    <div class="card">
                    <h3>💡 Tips Kesehatan</h3>
                    <p>{data['tips']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            except Exception as e:

                st.error(
                    f"Gagal menganalisis gambar: {e}"
                )

# ==================================
# FOOTER
# ==================================

st.markdown("""
<br><br>

<center>
<p style="color:gray;">
CekGizi AI • Powered by Gemini AI
</p>
</center>
""", unsafe_allow_html=True)
````
