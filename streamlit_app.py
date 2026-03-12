import streamlit as st

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# Hafıza (Session State) Tanımlamaları
if 'marka' not in st.session_state:
    st.session_state.marka = None

# Markalara özel Sheets verilerini tutacak dinamik depo
if 'sheets_verileri' not in st.session_state:
    st.session_state.sheets_verileri = {
        "MANUKA": {},
        "FRESH SCARFS": {}
    }

# --- 1. EKRAN: MARKA SEÇİMİ ---
if st.session_state.marka is None:
    st.title("🏢 Tarafını Seç :)")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👗 MANUKA", use_container_width=True):
            st.session_state.marka = "MANUKA"
            st.rerun()
    with col2:
        if st.button("🧣 FRESH SCARFS", use_container_width=True):
            st.session_state.marka = "FRESH SCARFS"
            st.rerun()

# --- 2. EKRAN: MARKA İÇERİĞİ ---
else:
    aktif_marka = st.session_state.marka
    st.title(f"📍 {aktif_marka} Dünyasına Hoş Geldin!")
    
    if st.button("⬅️ Marka Seçimine Dön"):
        st.session_state.marka = None
        st.rerun()
        
    st.divider()
    
    # Üst Kısım: Yeni Sheets Ekleme Baloncuğu
    with st.popover("➕ Yeni Sheets Oluştur"):
        with st.form("yeni_sheets_formu", clear_on_submit=True):
            yeni_ad = st.text_input("Koymak İstediğin Sheets Adı")
            yeni_id = st.text_input("Sheets ID")
            kaydet = st.form_submit_button("Kaydet")
            
            if kaydet:
                if yeni_ad and yeni_id:
                    # Girilen veriyi o markanın hafızasına ekle
                    st.session_state.sheets_verileri[aktif_marka][yeni_ad] = yeni_id
                    st.success(f"{yeni_ad} eklendi!")
                else:
                    st.error("Lütfen iki alanı da doldur.")

    st.write("---")

    # Alt Kısım: Eklenen Sheets'leri Gösterme / Seçme
    st.subheader("📁 Kayıtlı Raporlar")
    mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]
    
    if mevcut_raporlar:
        # Eklenenleri bir seçim kutusunda (selectbox) göster
        secilen_rapor = st.selectbox("Çalışmak istediğin raporu seç:", list(mevcut_raporlar.keys()))
        secilen_id = mevcut_raporlar[secilen_rapor]
        
        st.info(f"Seçilen Rapor ID: {secilen_id}")
        
        # İleride "Veriyi Getir" butonu buraya gelecek
    else:
        st.warning("Henüz bu marka için eklenmiş bir rapor yok. Yukarıdan oluşturabilirsin.")
