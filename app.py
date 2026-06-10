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
# FUNGSI BERTANYA KE AI (VERSI LEBIH AMAN)
# ==========================================
def analyze_food_image(image):
    system_prompt = """
    Kamu adalah ahli gizi profesional. Tugasmu menganalisis foto makanan ini.
    Berikan estimasi nutrisinya untuk 1 porsi standar.
    
    PENTING: Kamu HANYA boleh merespons dengan format JSON murni. Jangan ada kalimat pembuka/penutup.
    Format wajib:
    {
        "nama_makanan": "Nama Makanan",
        "kalori": 250,
        "protein": 10,
        "karbohidrat": 30,
        "lemak": 15,
        "tips_kesehatan": "Saran konsumsi."
    }
    """
    
    try:
        # PENTING: Mengubah gambar ke format dasar (RGB) agar AI tidak bingung
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        response = model.generate_content([system_prompt, image])
        
        # Mengambil teks balasan
        response_text = response.text
        
        # Membersihkan tanda kutip backtick (```) dari respons AI jika ada
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response_text)
        return data
        
    except json.JSONDecodeError:
        # Jika AI gagal memberikan JSON, tampilkan balasan ngawurnya
        return {"error": f"AI menjawab dengan format yang salah. Jawaban AI: {response.text}"}
    except Exception as e:
        # Jika ada error dari sistem (misal API limit, atau koneksi)
        return {"error": f"Sistem Google merespons: {str(e)}"}

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

# ==========================================
# JIKA GAMBAR SUDAH DIMASUKKAN
# ==========================================
if image_file is not None:
    image = Image.open(image_file)
    st.image(image, caption="Foto yang akan dianalisis", use_container_width=True)
    
    if st.button("🔍 Cek Kandungan Gizinya", type="primary"):
        with st.spinner("AI sedang menerawang makanan ini..."):
            
            hasil = analyze_food_image(image)
            
            if "error" in hasil:
                # Menampilkan pesan error ASLI agar kita tahu masalahnya
                st.error(f"Gagal memproses. Detail teknis: {hasil['error']}")
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
