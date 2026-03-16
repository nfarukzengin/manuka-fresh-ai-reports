import streamlit as st
import pandas as pd

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="Neco Dashboard", layout="wide")

# --- 1. GİRİŞ EKRANI (Login) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔒 Veri Analiz Paneli")
    password = st.text_input("Şifre Giriniz", type="password")
    if st.button("Giriş Yap"):
        if password == "1234": # Burayı sonra değiştiririz
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Hatalı Şifre!")
    st.stop()

# --- 2. MARKA SEÇİMİ (Sidebar) ---
st.sidebar.title("Marka Seçimi")
marka = st.sidebar.selectbox("Lütfen Marka Seçin", 
    ["Fresh Scarfs", "Manuka (Soon)", "Manuka Global (Soon)", "Fresh Scarfs Co (Soon)"])

if "Fresh Scarfs" in marka:
    st.title(f"📊 {marka} Dashboard")
    
    # --- 3. RAPORLAR VE ALARM MERKEZİ (Sekmeler) ---
    tab_rapor, tab_alarm = st.tabs(["📋 Raporlar", "🚨 Alarm Merkezi"])

    with tab_rapor:
        st.subheader("Google Ads Veri Kontrolü")
        
        # Veri çekme simülasyonu (Buraya senin Sheets ID gelecek)
        # data = pd.read_csv("GOOGLE_SHEET_URL")
        st.info("Şu an veriler Google Sheets'ten bekleniyor...")
        
        # Örnek Tablo
        st.write("Dataların doğruluğunu kontrol etmek için ham tablo:")
        # st.dataframe(data) 

    with tab_alarm:
        st.subheader("Kritik Uyarılar")
        st.write("Şu an aktif bir alarm kuralı bulunmuyor.")
