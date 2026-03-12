import streamlit as st
import pandas as pd

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# --- VERİ ÇEKME FONKSİYONLARI ---
@st.cache_data(show_spinner=False)
def sekmeleri_getir(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    xls = pd.ExcelFile(url)
    return xls.sheet_names

@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url, sheet_name=sayfa_adi)
    return df

# --- HAFIZA (SESSION STATE) ---
if 'giris_yapti_mi' not in st.session_state:
    st.session_state.giris_yapti_mi = False

if 'marka' not in st.session_state:
    st.session_state.marka = None

if 'sheets_verileri' not in st.session_state:
    st.session_state.sheets_verileri = {
        "MANUKA": {},
        "FRESH SCARFS": {}
    }

# --- GİRİŞ SAYFASI (KAPIDAKİ GÜVENLİK) ---
if not st.session_state.giris_yapti_mi:
    st.title("✋ Hop Hemşerim Nereye? Parolayı Söyle!")
    
    # Şifre kutusu ve butonu ortalamak için kolon kullanıyoruz
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        sifre = st.text_input("Parola", type="password", label_visibility="collapsed", placeholder="Parolayı gir...")
        if st.button("İçeri Gir", use_container_width=True):
            if sifre == "fresh123":
                st.session_state.giris_yapti_mi = True
                st.rerun() # Sayfayı yenile ve içeri al
            elif sifre == "":
                st.warning("Boş geçemezsin, parolayı yaz.")
            else:
                st.error("Yanlışlıkla mı yanlış yazdın? Yoksa kaçak girmeye çalışan hain misin?")

# --- ANA UYGULAMA (İÇERİSİ) ---
else:
    # 1. EKRAN: MARKA SEÇİMİ
    if st.session_state.marka is None:
        # Çıkış Yap Butonu
        if st.button("🚪 Çıkış Yap"):
            st.session_state.giris_yapti_mi = False
            st.rerun()
            
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

    # 2. EKRAN: MARKA İÇERİĞİ
    else:
        aktif_marka = st.session_state.marka
        
        col_baslik, col_buton = st.columns([4, 1])
        with col_baslik:
            st.title(f"📍 {aktif_marka} Dünyasına Hoş Geldin!")
        with col_buton:
            if st.button("⬅️ Tarafını Değiştir", use_container_width=True):
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
            
            secilen_rapor = st.selectbox("Hangi raporu inceleyeceğiz?", list(mevcut_raporlar.keys()))
            secilen_id = mevcut_raporlar[secilen_rapor]
            
            if secilen_id:
                try:
                    with st.spinner("Sekmeler aranıyor..."):
                        sayfalar = sekmeleri_getir(secilen_id)
                    
                    secilen_sayfa = st.selectbox("Hangi sekmeye bakıyoruz?", sayfalar)
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        baslangic = st.date_input("Nereden Başlayalım?")
                    with col_d2:
                        bitis = st.date_input("Nerede Bitirelim?")
                    
                    st.write("##")
                    if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                        with st.spinner("Veriler toparlanıyor, biraz bekle..."):
                            df = veri_cek(secilen_id, secilen_sayfa)
                            
                            # --- TARİH FİLTRESİ VE SAAT TEMİZLİĞİ ---
                            if 'Tarih' in df.columns:
                                # 1. Saat bilgisini sil ve saf tarih formatına çevir
                                df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
                                
                                # 2. Başlangıç ve bitiş aralığına göre filtrele
                                maske = (df['Tarih'] >= baslangic) & (df['Tarih'] <= bitis)
                                df = df.loc[maske].copy() # Filtrelenmiş veriyi al
                                
                                # Görünümü daha şık yapmak için tarihi tekrar gün.ay.yıl yapabiliriz (opsiyonel)
                                # df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%d.%m.%Y')
                                
                            else:
                                st.warning("Tabloda tam olarak 'Tarih' adında bir sütun bulamadığım için filtreleme yapamadım.")
                            
                            st.success(f"Geldi! {secilen_rapor} raporunun {secilen_sayfa} sekmesine bakıyorsun.")
                            st.dataframe(df, use_container_width=True)
                            
                except Exception as e:
                    st.error(f"Bi' sorun var, arka planda patlayan asıl hata şu: {e}")
        else:
            st.info("Burası bomboş. Yukarıdan bir rapor bağlayarak başlayabilirsin.")
