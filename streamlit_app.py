import streamlit as st
import pandas as pd
# Fresh Scarfs klasöründeki logic.py dosyasını içeri alıyoruz
from brands.fresh_scarfs import logic as fs_logic 

# Sayfa Genişlik Ayarı ve Başlık
st.set_page_config(page_title="Neco Dashboard", layout="wide")

# --- 1. GİRİŞ EKRANI (Login Control) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔒 Veri Analiz Paneli")
    password = st.text_input("Şifre Giriniz", type="password")
    if st.button("Giriş Yap"):
        if password == "1234": # Bu şifreyi istediğin zaman değiştirebilirsin
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Hatalı Şifre!")
    st.stop()

# --- 2. MARKA SEÇİMİ (Sidebar) ---
st.sidebar.title("Marka Seçimi")
marka = st.sidebar.selectbox("Lütfen Marka Seçin", 
    ["Fresh Scarfs", "Manuka (Yakında)", "Manuka Global (Yakında)", "Fresh Scarfs Co (Yakında)"])

# --- 3. ANA İÇERİK (Fresh Scarfs Seçiliyse) ---
if marka == "Fresh Scarfs":
    st.title(f"📊 {marka} Dashboard")
    
    # Raporlar ve Alarm Merkezi sekmelerini oluşturuyoruz
    tab_rapor, tab_alarm = st.tabs(["📋 Raporlar", "🚨 Alarm Merkezi"])

    with tab_rapor:
        # brands/fresh_scarfs/logic.py içindeki raporu çalıştırır
        fs_logic.show_report()

    with tab_alarm:
        st.subheader("Kritik Uyarılar")
        st.info("Alarm merkezi için eşik değerleri henüz tanımlanmadı.")

# Diğer markalar için ileride buraya yeni 'elif' blokları ekleyeceğiz.
