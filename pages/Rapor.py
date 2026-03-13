import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests

# Sayfa Ayarı
st.set_page_config(page_title="Rapor Analizi", layout="wide")

# Giriş Kontrolü
if 'giris_yapti_mi' not in st.session_state or not st.session_state.giris_yapti_mi:
    st.warning("Önce ana sayfadan giriş yapmalısın kiral!")
    st.stop()

if st.session_state.marka is None:
    st.warning("Lütfen önce bir marka seç!")
    st.stop()

# --- GİZLİ AYARLAR ---
API_URL = "https://script.google.com/macros/s/AKfycbxHd6N9TF2uzqJr-EhEfGyGH3j2oGTEiTRpKShSwwoWpJuVocyXVGHbWHyYNDL9uSQ/exec"
API_TOKEN = "manuka-fresh-reports"

# --- FONKSİYONLAR ---
@st.cache_data(show_spinner=False)
def sekmeleri_getir(sheet_id):
    params = {"islem": "sekmeler", "id": sheet_id, "token": API_TOKEN}
    cevap = requests.get(API_URL, params=params)
    try: return cevap.json()
    except: return []

@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    params = {"islem": "veri", "id": sheet_id, "sayfa": sayfa_adi, "token": API_TOKEN}
    cevap = requests.get(API_URL, params=params)
    try: 
        veri = cevap.json()
        if len(veri) > 1:
            baslik_index = 0
            for i, satir in enumerate(veri[:25]):
                satir_kucuk = [str(hucre).strip().lower() for hucre in satir]
                if any(k in satir_kucuk for k in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium']):
                    baslik_index = i
                    break
            temiz_veri = veri[baslik_index:]
            ham_kolonlar = [str(k).strip() if str(k).strip() != "" else f"Adsiz_{i}" for i, k in enumerate(temiz_veri[0])]
            temiz_kolonlar = []
            for k in ham_kolonlar:
                orijinal = k
                sayac = 1
                while k in temiz_kolonlar:
                    k = f"{orijinal}_{sayac}"
                    sayac += 1
                temiz_kolonlar.append(k)
            df = pd.DataFrame(temiz_veri[1:], columns=temiz_kolonlar)
        else:
            df = pd.DataFrame(veri)
        
        # TAŞ FIRIN TEMİZLEYİCİ
        for col in df.columns:
            if col.lower() not in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium', 'ürün adı', 'kampanya', 'source', 'medium']:
                def temizle(x):
                    if isinstance(x, str):
                        x = x.replace('₺', '').replace('%', '').replace('None', '0').strip()
                        if '.' in x and ',' in x: x = x.replace('.', '').replace(',', '.')
                        elif ',' in x: x = x.replace(',', '.')
                        elif '.' in x:
                            parts = x.split('.')
                            if len(parts) > 2: x = x.replace('.', '')
                            elif len(parts[-1]) == 3: x = x.replace('.', '')
                    return x 
                df[col] = df[col].apply(temizle)
                df[col] = pd.to_numeric(df[col], errors='ignore')
        return df
    except: return pd.DataFrame()

# --- EKRAN BAŞLIYOR ---
aktif_marka = st.session_state.marka
st.title(f"📊 {aktif_marka} - Rapor Analiz Merkezi")

mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]

if not mevcut_raporlar:
    st.info("Henüz bu marka için kayıtlı bir rapor yok.")
else:
    secilen_rapor = st.selectbox("İncelenecek Rapor:", list(mevcut_raporlar.keys()))
    secilen_id = mevcut_raporlar[secilen_rapor]
    
    sayfalar = sekmeleri_getir(secilen_id)
    if sayfalar:
        secilen_sayfa = st.selectbox("Sekme Seçin:", sayfalar)
        
        c1, c2 = st.columns(2)
        baslangic = c1.date_input("Başlangıç")
        bitis = c2.date_input("Bitiş")
        
        if st.button("🚀 Verileri Analiz Et", use_container_width=True):
            df = veri_cek(secilen_id, secilen_sayfa)
            st.session_state.ham_veri = df.copy() # Alarmlar için ham hali sakla
            
            # Tarih Filtreleme
            tarih_kolonu = next((col for col in df.columns if col.lower() in ['tarih', 'date', 'gün', 'day']), None)
            if tarih_kolonu:
                df[tarih_kolonu] = pd.to_datetime(df[tarih_kolonu], errors='coerce', dayfirst=True)
                df = df.dropna(subset=[tarih_kolonu])
                maske = (df[tarih_kolonu].dt.date >= baslangic) & (df[tarih_kolonu].dt.date <= bitis)
                df = df.loc[maske].copy()
                df[tarih_kolonu] = df[tarih_kolonu].dt.strftime('%d.%m.%Y')
                st.session_state.aktif_veri = df

    if st.session_state.aktif_veri is not None:
        df = st.session_state.aktif_veri.copy()
        
        # Kampanya Filtresi
        if 'CampaignName' in df.columns:
            secilen = st.multiselect("🎯 Kampanya Filtresi:", df['CampaignName'].unique())
            if secilen: df = df[df['CampaignName'].isin(secilen)]

        # --- TABLO VE FORMATLAMA (Senin Orijinal Kodun) ---
        sayisal_sutunlar = df.select_dtypes(include=['number']).columns
        toplam_degerler = {}
        for col in sayisal_sutunlar:
            c_lower = col.lower()
            if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                toplam_degerler[col] = df[col].mean()
            else:
                toplam_degerler[col] = df[col].sum()
        
        tarih_kolonu = next((col for col in df.columns if col.lower() in ['tarih', 'date', 'gün', 'day']), None)
        toplam_satiri = pd.DataFrame([toplam_degerler])
        toplam_satiri[tarih_kolonu if tarih_kolonu else df.columns[0]] = 'TOPLAM'
        df_tablo = pd.concat([df, toplam_satiri], ignore_index=True)

        def formatla(val, col_name):
            if pd.isna(val) or not isinstance(val, (int, float)): return val
            c_lower = col_name.lower()
            if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                if 10 > val > -10: val *= 100 
                return f"% {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif any(x in c_lower for x in ['revenue', 'cost', 'cpc', 'cpa', 'harcama']):
                return f"₺ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").replace(",00", "")

        for col in df_tablo.columns:
            if col != tarih_kolonu: df_tablo[col] = df_tablo[col].apply(lambda x: formatla(x, col))
        
        st.dataframe(df_tablo.style.apply(lambda row: ['background-color: #004d40; color: white; font-weight: bold'] * len(row) if 'TOPLAM' in str(row.values) else [''] * len(row), axis=1), use_container_width=True)

        # GRAFİK
        st.subheader("📈 Trendler")
        metrikler = st.multiselect("Grafik için metrik:", sayisal_sutunlar.tolist(), default=sayisal_sutunlar.tolist()[:1])
        if metrikler and tarih_kolonu:
            st.line_chart(df.set_index(tarih_kolonu)[metrikler])

        # AI ANALİZ
        st.subheader("🤖 AI Analiz")
        kullanici_sorusu = st.text_input("Verilerle ilgili ne bilmek istersin?", "CPA ve ROAS dengesini analiz et.")
        if st.button("🧠 Uzmana Sor"):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"Sen bir dijital pazarlama uzmanısın. Veriler: {df.to_string()} \nSoru: {kullanici_sorusu}"
                with st.spinner("Analiz ediliyor..."):
                    cevap = model.generate_content(prompt)
                    st.markdown(f"> {cevap.text}")
            except Exception as e:
                st.error(f"AI Hatası: {e}")
