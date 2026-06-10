import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="CekGizi - Deteksi Nutrisi", page_icon="🍔", layout="centered")

# ==========================================
# MENGAMBIL API KEY DARI STREAMLIT SECRETS
# ==========================================
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ API Key belum dimasukkan! Pastikan kamu sudah mengisi Advanced Settings > Secrets di Streamlit.")
    st.stop()

# Menyalakan mesin AI Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# FUNGSI BERTANYA KE AI
# ==========================================
def analyze_food_image(image):
    system_prompt = """
Kamu adalah ahli gizi profesional asal Indonesia. Tugasmu adalah menganalisis foto makanan ini.
    Fokus utamamu adalah mengenali makanan, lauk-pauk, dan jajanan khas Indonesia (seperti bakso, siomay, cilok, martabak, gorengan, nasi goreng, dll).
    
    Identifikasi apa nama makanan/jajanan ini, lalu berikan estimasi nutrisinya untuk 1 porsi standar masyarakat Indonesia.
    Jika gambar kurang jelas, tetap berikan tebakan terbaikmu yang paling mendekati bentuk visual tersebut.
    
    PENTING: Kamu HANYA boleh merespons dengan format JSON yang valid. Jangan tambahkan teks lain atau penjelasan apapun.
    Gunakan format ini persis:
    {
        "nama_makanan": "Nama Jajanan/Makanan",
        "kalori": 250,
        "protein": 10,
        "karbohidrat": 30,
        "lemak": 15,
        "tips_kesehatan": "Kalimat singkat tentang saran konsumsi dengan gaya bahasa santai."
    }
    """

    try:
        response = model.generate_content([system_prompt, image])
        response_text = response.text.replace('```json\n', '').replace('```', '').strip()
        data = json.loads(response_text)
        return data
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# TAMPILAN APLIKASI WEB
# ==========================================
st.title("🥗 CekGizi")
st.markdown("**Deteksi Kalori dan Gizi Jajananmu Sekali Jepret!**")

tab_kamera, tab_galeri = st.tabs(["📸 Ambil Foto", "📂 Unggah Galeri"])

image_file = None

with tab_kamera:
    kamera = st.camera_input("Foto jajananmu:")
    if kamera:
        image_file = kamera

with tab_galeri:
    galeri = st.file_uploader("Atau pilih foto dari galeri HP...", type=["jpg", "jpeg", "png"])
    if galeri:
        image_file = galeri

if image_file is not None:
    image = Image.open(image_file)
    st.image(image, caption="Foto yang akan dianalisis", use_container_width=True)

    if st.button("🔍 Cek Kandungan Gizinya", type="primary"):
        with st.spinner("AI sedang menerawang makanan ini..."):
            hasil = analyze_food_image(image)
            if "error" in hasil:
                st.error("Terjadi kesalahan. Pastikan fotonya jelas atau cek koneksi internet.")
            else:
                st.success(f"Ketemu! Ini sepertinya: **{hasil.get('nama_makanan', 'Makanan Tidak Diketahui')}**")
                kolom1, kolom2, kolom3, kolom4 = st.columns(4)
                with kolom1:
                    st.metric(label="🔥 Kalori", value=f"{hasil.get('kalori', 0)} kcal")
                with kolom2:
                    st.metric(label="🥩 Protein", value=f"{hasil.get('protein', 0)} g")
                with kolom3:
                    st.metric(label="🍚 Karbo", value=f"{hasil.get('karbohidrat', 0)} g")
                with kolom4:
                    st.metric(label="🧈 Lemak", value=f"{hasil.get('lemak', 0)} g")
                st.info(f"💡 **Tips:** {hasil.get('tips_kesehatan', 'Makan sewajarnya saja.')}")
