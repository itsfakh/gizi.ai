import json
import os
import re
from typing import Optional

import streamlit as st
from PIL import Image
from pydantic import BaseModel, Field, ValidationError

# Optional: mendukung file .env saat development lokal.
# Jika package python-dotenv belum diinstal, aplikasi tetap jalan.
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# SDK resmi Gemini yang direkomendasikan pada dokumentasi terbaru:
# from google import genai
from google import genai


# =========================
# Konfigurasi Halaman
# =========================
st.set_page_config(
    page_title="CekGizi - Deteksi Kalori Jajananmu",
    page_icon="🥗",
    layout="wide",
)

st.title("CekGizi - Deteksi Kalori Jajananmu")
st.caption(
    "Unggah foto makanan atau pakai kamera HP, lalu biarkan AI memberi estimasi nutrisi secara cepat."
)

st.info(
    "Hasil di aplikasi ini adalah estimasi, bukan diagnosis medis atau data gizi laboratorium."
)

# =========================
# Schema Output AI
# =========================
class NutritionAnalysis(BaseModel):
    food_name: str = Field(description="Nama makanan/jajanan yang paling mungkin terdeteksi.")
    calories_kcal: int = Field(ge=0, description="Estimasi kalori dalam kcal untuk 1 porsi.")
    protein_g: float = Field(ge=0, description="Estimasi protein dalam gram.")
    carbs_g: float = Field(ge=0, description="Estimasi karbohidrat dalam gram.")
    fat_g: float = Field(ge=0, description="Estimasi lemak dalam gram.")
    health_tip: str = Field(description="Tips kesehatan singkat terkait makanan tersebut.")
    confidence_note: str = Field(
        default="",
        description="Catatan singkat tentang tingkat keyakinan atau asumsi porsi.",
    )


SYSTEM_PROMPT = """
Kamu adalah asisten analisis nutrisi makanan Indonesia yang sangat hati-hati dan ringkas.

Tugasmu:
- Identifikasi makanan/jajanan pada gambar.
- Berikan estimasi nutrisi untuk 1 porsi yang paling masuk akal.
- Jika porsi tidak jelas, gunakan asumsi porsi umum dan sebutkan di confidence_note.
- Jangan mengarang berlebihan. Jika ragu, tulis estimasi konservatif.

Aturan output:
- Kembalikan HANYA JSON valid.
- Jangan gunakan markdown, bullet, atau penjelasan tambahan di luar JSON.
- Gunakan key berikut persis:
  - food_name
  - calories_kcal
  - protein_g
  - carbs_g
  - fat_g
  - health_tip
  - confidence_note

Panduan isi:
- food_name: nama makanan/jajanan paling mungkin.
- calories_kcal: integer.
- protein_g, carbs_g, fat_g: angka desimal.
- health_tip: 1 kalimat singkat, misalnya aman dikonsumsi harian / batasi karena tinggi natrium / cukup sesekali.
- confidence_note: 1 kalimat singkat tentang asumsi atau tingkat keyakinan.
""".strip()

MODEL_NAME = "gemini-3.5-flash"


# =========================
# Utilitas
# =========================
def get_api_key() -> str:
    """
    Ambil API key dari st.secrets dulu, lalu fallback ke environment variable.
    """
    try:
        if "GEMINI_API_KEY" in st.secrets:
            key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if key:
                return key
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "").strip()


@st.cache_resource(show_spinner=False)
def get_client(api_key: str) -> genai.Client:
    """
    Cache client supaya tidak dibuat ulang setiap rerun.
    """
    return genai.Client(api_key=api_key)


def image_from_uploaded_file(uploaded_file) -> Image.Image:
    """
    Konversi file upload / camera input ke objek PIL Image.
    """
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    return image.convert("RGB")


def parse_analysis_response(raw_text: str) -> NutritionAnalysis:
    """
    Coba parse JSON murni dari model.
    Jika model menambahkan teks liar, ambil blok JSON pertama yang ditemukan.
    """
    try:
        return NutritionAnalysis.model_validate_json(raw_text)
    except ValidationError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if match:
            return NutritionAnalysis.model_validate_json(match.group(0))
        raise


def analyze_food_image(image: Image.Image) -> NutritionAnalysis:
    """
    Kirim gambar ke Gemini Vision dan paksa output JSON sesuai schema.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "API key Gemini belum ditemukan. Isi GEMINI_API_KEY di st.secrets atau environment variable."
        )

    client = get_client(api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            "Analisis gambar makanan ini dan keluarkan hasil sesuai instruksi system.",
            image,
        ],
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.2,
            "response_format": {
                "text": {
                    "mime_type": "application/json",
                    "schema": NutritionAnalysis.model_json_schema(),
                }
            },
        },
    )

    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise RuntimeError("Gemini tidak mengembalikan teks respons.")

    return parse_analysis_response(raw_text)


# =========================
# UI Input
# =========================
left, right = st.columns([1.1, 0.9], vertical_alignment="top")

with left:
    st.subheader("Ambil atau unggah foto")
    tab1, tab2 = st.tabs(["Kamera HP", "Upload Galeri"])

    with tab1:
        camera_file = st.camera_input("Ambil foto makanan")
    with tab2:
        uploaded_file = st.file_uploader(
            "Upload foto makanan",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
        )

    media = camera_file or uploaded_file

    analyze_clicked = st.button("Analisis nutrisi", use_container_width=True)

with right:
    st.subheader("Cara pakai")
    st.write(
        "1. Foto makanan dengan kamera atau upload dari galeri.\n"
        "2. Klik **Analisis nutrisi**.\n"
        "3. Lihat estimasi kalori dan makro di panel hasil."
    )

# =========================
# Proses Analisis
# =========================
if media is not None:
    image = image_from_uploaded_file(media)
    st.image(image, caption="Foto yang dianalisis", use_container_width=True)

    if analyze_clicked:
        with st.spinner("Gemini sedang menganalisis gambar..."):
            try:
                result = analyze_food_image(image)
            except Exception as e:
                st.error(f"Gagal menganalisis gambar: {e}")
                st.stop()

        st.success("Analisis selesai.")

        # Dashboard kecil
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kalori", f"{result.calories_kcal} kcal")
        c2.metric("Protein", f"{result.protein_g:.1f} g")
        c3.metric("Karbohidrat", f"{result.carbs_g:.1f} g")
        c4.metric("Lemak", f"{result.fat_g:.1f} g")

        st.markdown("### Ringkasan")
        st.write(f"**Makanan terdeteksi:** {result.food_name}")
        st.write(f"**Tips kesehatan:** {result.health_tip}")

        if result.confidence_note.strip():
            st.caption(f"Catatan: {result.confidence_note}")

        with st.expander("Lihat JSON hasil AI"):
            st.code(result.model_dump_json(indent=2, exclude_none=True), language="json")
else:
    st.warning("Silakan ambil foto atau unggah gambar makanan dulu.")
