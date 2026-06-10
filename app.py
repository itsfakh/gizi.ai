import streamlit as st
from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# ====================== CONFIG ======================
st.set_page_config(
    page_title="CekGizi",
    page_icon="🍲",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🍲 CekGizi")
st.markdown("**Deteksi Kalori & Nutrisi Makanan dengan AI**")
st.caption("Ambil foto → Langsung tahu gizinya! 📱💻")

# Load API Key
load_dotenv()

def get_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.getenv("GEMINI_API_KEY")

api_key = get_api_key()

if not api_key:
    st.error("❌ API Key Gemini belum ditemukan. Lihat instruksi di bawah.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# System Prompt yang lebih baik
SYSTEM_PROMPT = """
Kamu adalah ahli nutrisi profesional. Analisis gambar makanan dengan teliti.

Jawab **hanya** dalam format JSON berikut, tanpa kata-kata tambahan:

{
  "nama_makanan": "Nama makanan yang jelas",
  "kalori": 0,
  "protein": 0,
  "karbohidrat": 0,
  "lemak": 0,
  "tips": "Tips kesehatan singkat dan berguna (maksimal 1 kalimat)"
}

Gunakan angka bulat untuk nilai nutrisi.
"""

# ====================== UPLOAD GAMBAR ======================
st.subheader("📸 Kirim Foto Makananmu")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader("Pilih foto dari galeri", type=["jpg", "jpeg", "png"])

with col2:
    camera_file = st.camera_input("Atau ambil foto langsung")

# Pilih gambar
if camera_file is not None:
    image_file = camera_file
    st.success("📸 Foto dari kamera diambil")
elif uploaded_file is not None:
    image_file = uploaded_file
else:
    image_file = None

if image_file:
    image = Image.open(image_file)
    st.image(image, caption="Foto yang akan dianalisis", use_column_width=True)

    if st.button("🔍 Analisis dengan AI", type="primary", use_container_width=True):
        with st.spinner("🤖 Gemini AI sedang menganalisis gambar..."):
            try:
                response = model.generate_content(
                    [SYSTEM_PROMPT, image],
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 600,
                    }
                )
                
                # Parse JSON
                result_text = response.text.strip()
                data = json.loads(result_text)
                
                # Hasil
                st.success("✅ Analisis Berhasil!")
                
                st.subheader(f"🍽️ {data['nama_makanan']}")
                
                # Metrics
                cols = st.columns(4)
                cols[0].metric("🔥 Kalori", f"{data['kalori']} kcal")
                cols[1].metric("🥩 Protein", f"{data['protein']} g")
                cols[2].metric("🍚 Karbo", f"{data['karbohidrat']} g")
                cols[3].metric("🧈 Lemak", f"{data['lemak']} g")
                
                st.info(f"💡 **Tips Kesehatan:** {data['tips']}")
                
                st.caption("⚠️ Ini adalah estimasi AI. Gunakan sebagai referensi saja.")
                
            except json.JSONDecodeError:
                st.error("⚠️ AI mengembalikan format yang tidak sesuai. Coba foto dengan pencahayaan lebih terang.")
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# ====================== FOOTER ======================
st.markdown("---")
st.markdown("**CekGizi** • Prototype Gratis menggunakan Streamlit + Google Gemini")

# Sidebar Info
with st.sidebar:
    st.header("Cara Pakai")
    st.markdown("""
    1. Ambil foto makanan/jajanan
    2. Tekan tombol **Analisis dengan AI**
    3. Tunggu hasilnya
    """)
    
    st.info("💡 **Tips foto yang bagus:**\n• Pencahayaan terang\n• Makanan terlihat jelas\n• Tidak terlalu banyak jenis makanan sekaligus")
