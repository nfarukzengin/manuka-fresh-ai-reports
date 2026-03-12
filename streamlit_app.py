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
                        if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                        with st.spinner("Veriler toparlanıyor, biraz bekle..."):
                            df = veri_cek(secilen_id, secilen_sayfa)
                            
                            # --- 1. TARİH FİLTRESİ VE TEMİZLİĞİ ---
                            if 'Tarih' in df.columns:
                                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
                                df = df.dropna(subset=['Tarih'])
                                df['Tarih'] = df['Tarih'].dt.date
                                
                                maske = (df['Tarih'] >= baslangic) & (df['Tarih'] <= bitis)
                                df = df.loc[maske].copy()
                                
                                # Tarihi GÜN.AY.YIL formatına çevir
                                df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%d.%m.%Y')
                            
                            # --- 2. DİNAMİK TOPLAM SATIRI ---
                            if not df.empty:
                                sayisal_sutunlar = df.select_dtypes(include=['number']).columns
                                toplam_degerler = {}
                                
                                for col in sayisal_sutunlar:
                                    c_lower = col.lower()
                                    # İçinde 'cos' geçenleri ortalama al ama 'cost' ise alma (TOPLA)!
                                    if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                                        toplam_degerler[col] = df[col].mean()
                                    else:
                                        toplam_degerler[col] = df[col].sum()
                                
                                toplam_satiri = pd.DataFrame([toplam_degerler])
                                toplam_satiri['Tarih'] = 'TOPLAM'
                                df = pd.concat([df, toplam_satiri], ignore_index=True)
                                
                                # --- 3. MAKYAJ: SAYILARI FORMATLAMA ---
                                def formatla(val, col_name):
                                    if isinstance(val, (int, float)):
                                        c_lower = col_name.lower()
                                        
                                        # Oransal değerler (Örn: %7.20)
                                        if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                                            if val < 10 and val > -10: val = val * 100 
                                            return f"% {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                            
                                        # Parasal değerler (Örn: ₺12.500,50)
                                        elif any(x in c_lower for x in ['revenue', 'cost', 'cpc', 'cpa', 'harcama', 'reklam']):
                                            return f"₺ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                            
                                        # Normal sayılar (Küsüratsızsa ,00 kısmını atar)
                                        else:
                                            fmt_val = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                            if fmt_val.endswith(",00"): fmt_val = fmt_val[:-3]
                                            return fmt_val
                                    return val

                                # Bütün sütunları format fonksiyonundan geçir
                                for col in df.columns:
                                    if col != 'Tarih': 
                                        df[col] = df[col].apply(lambda x: formatla(x, col))
                                
                                # Toplam satırını boya
                                def satir_boya(row):
                                    if row['Tarih'] == 'TOPLAM':
                                        return ['background-color: #004d40; color: white; font-weight: bold'] * len(row)
                                    return [''] * len(row)
                                
                                st.success(f"Geldi! {secilen_rapor} raporunun {secilen_sayfa} sekmesine bakıyorsun.")
                                st.dataframe(df.style.apply(satir_boya, axis=1), use_container_width=True)
                            else:
                                st.warning("Seçtiğin tarihler arasında hiç veri yok kiral, tarihleri biraz esnet.")
