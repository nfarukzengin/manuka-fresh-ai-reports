import streamlit as st

# Sayfa Genişliği Ayarı
st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# Hafıza (Session State) - Hangi markada olduğumuzu aklında tutacak
if 'marka' not in st.session_state:
    st.session_state.marka = None

# --- 1. EKRAN: MARKA SEÇİMİ ---
if st.session_state.marka is None:
    st.title("🏢 Lütfen Bir Marka Seç kiral")
    st.write("---")
    
    # İki dev buton için yan yana kolonlar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👗 MANUKA", use_container_width=True):
            st.session_state.marka = "MANUKA"
            st.rerun() # Sayfayı yenile ve içeri gir
    with col2:
        if st.button("🧣 FRESH SCARFS", use_container_width=True):
            st.session_state.marka = "FRESH SCARFS"
            st.rerun()

# --- 2. EKRAN: MARKA İÇERİĞİ ---
else:
    st.title(f"📍 {st.session_state.marka} Kontrol Paneli")
    
    # Geri Dön Butonu
    if st.button("⬅️ Marka Seçimine Dön"):
        st.session_state.marka = None
        st.rerun()
        
    st.divider()
    st.info("Raporlar, dosyalar ve grafikler buraya gelecek...")
