import streamlit as st
import pandas as pd

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# --- VERİ ÇEKME FONKSİYONLARI ---
# Sekme isimlerini bulur (Sistemi yormamak için hafızaya alır)
@st.cache_data(show_spinner=False)
def sekmeleri_getir(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    xls = pd.ExcelFile(url)
    return xls.sheet_names

# Seçilen sekmenin içindeki tüm veriyi çeker
@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url, sheet_name=sayfa_adi)
    return df

# --- HAFIZA (SESSION STATE) ---
if 'marka' not in st.session_state:
    st.session_state.marka = None

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
    
    if st.button("⬅️ Tarafını Değiştir"):
        st.session_state.marka = None
        st.rerun()
        
    st.divider()
    
    # Üst Kısım: Yeni Sheets Ekleme
    with st.popover("➕ Yeni Rapor Bağla"):
        with st.form("yeni_sheets_formu", clear_on_submit=True):
            yeni_ad = st.text_input("Raporun Adı Ne Olsun?")
            yeni_id = st.text_input("Google Sheets ID'sini Yapıştır")
            kaydet = st.form_submit_button("Sisteme Ekle")
            
            if kaydet:
                if yeni_ad and yeni_id:
                    st.session_state.sheets_verileri[aktif_marka][yeni_ad] = yeni_id
                    st.success(f"Süper! {yeni_ad} eklendi.")
                else:
                    st.error("İki alanı da doldurman lazım.")

    st.write("---")

    # Alt Kısım: Kayıtlı Raporlar ve Veri Çekme İşlemleri
    mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]
    
    if mevcut_raporlar:
        st.subheader("📁 Kayıtlı Raporların")
        
        # 1. Rapor Seçimi
        secilen_rapor = st.selectbox("Hangi raporu inceleyeceğiz?", list(mevcut_raporlar.keys()))
        secilen_id = mevcut_raporlar[secilen_rapor]
        
        # Rapor seçildikten sonra içindeki sayfaları bulmaya çalış
        if secilen_id:
            try:
                with st.spinner("Sekmeler aranıyor..."):
                    sayfalar = sekmeleri_getir(secilen_id)
                
                # 2. Sayfa Seçimi
                secilen_sayfa = st.selectbox("Hangi sekmeye bakıyoruz?", sayfalar)
                
                # 3. Tarih Seçimi
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    baslangic = st.date_input("Nereden Başlayalım?")
                with col_d2:
                    bitis = st.date_input("Nerede Bitirelim?")
                
                # 4. Çalıştır Butonu
                st.write("##") # Biraz boşluk
                if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                    with st.spinner("Veriler toparlanıyor, biraz bekle..."):
                        df = veri_cek(secilen_id, secilen_sayfa)
                        st.success(f"Geldi! {secilen_rapor} raporunun {secilen_sayfa} sekmesine bakıyorsun.")
                        
                        # Veriyi Ekrana Bas
                        st.dataframe(df, use_container_width=True)
                        
            except Exception as e:
                st.error("Ufak bir sorun çıktı! ID hatalı olabilir veya dosya 'Bağlantıya sahip herkes görebilir' konumunda değil.")
    else:
        st.info("Burası bomboş. Yukarıdan bir rapor bağlayarak başlayabilirsin.")
