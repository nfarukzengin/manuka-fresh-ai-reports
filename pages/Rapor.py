import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests

st.set_page_config(page_title="Rapor Analizi", layout="wide")

# Giriş ve Marka Kontrolü
if 'giris_yapti_mi' not in st.session_state or not st.session_state.giris_yapti_mi:
    st.warning("Önce ana sayfadan giriş yapmalısın Neco!")
    st.stop()

if st.session_state.marka is None:
    st.warning("Lütfen önce bir marka seç!")
    st.stop()

# --- API AYARLARI ---
API_URL = "https://script.google.com/macros/s/AKfycbxHd6N9TF2uzqJr-EhEfGyGH3j2oGTEiTRpKShSwwoWpJuVocyXVGHbWHyYNDL9uSQ/exec"
API_TOKEN = "manuka-fresh-reports"

# --- VERİ ÇEKME MOTORU ---
@st.cache_data(show_spinner=False)
def sekmeleri_getir(sheet_id):
    params = {"islem": "sekmeler", "id": sheet_id, "token": API_TOKEN}
    try:
        cevap = requests.get(API_URL, params=params)
        return cevap.json()
    except: return []

@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    params = {"islem": "veri", "id": sheet_id, "sayfa": sayfa_adi, "token": API_TOKEN}
    try:
        cevap = requests.get(API_URL, params=params)
        veri = cevap.json()
        if len(veri) > 1:
            # Başlık bulucu ve temizleyici
            baslik_index = 0
            for i, satir in enumerate(veri[:25]):
                satir_kucuk = [str(hucre).strip().lower() for hucre in satir]
                if any(k in satir_kucuk for k in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium']):
                    baslik_index = i
                    break
            df = pd.DataFrame(veri[baslik_index+1:], columns=veri[baslik_index])
            
            # Sayısal Temizlik
            for col in df.columns:
                if col.lower() not in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium', 'kampanya']:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace('₺', '').replace('%', '').replace(',', '.').strip(), errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- ARAYÜZ ---
st.title(f"📊 {st.session_state.marka} Rapor Merkezi")

mevcut_raporlar = st.session_state.sheets_verileri[st.session_state.marka]

if not mevcut_raporlar:
    st.info("Henüz kayıtlı rapor yok. Ana sayfadan 'Yeni Rapor Bağla' diyerek başlayabilirsin.")
else:
    secilen_rapor = st.selectbox("Rapor Seç:", list(mevcut_raporlar.keys()))
    secilen_id = mevcut_raporlar[secilen_rapor]
    
    sayfalar = sekmeleri_getir(secilen_id)
    if sayfalar:
        secilen_sayfa = st.selectbox("Sekme Seç:", sayfalar)
        
        c1, c2 = st.columns(2)
        baslangic = c1.date_input("Başlangıç", value=pd.to_datetime("today") - pd.Timedelta(days=30))
        bitis = c2.date_input("Bitiş")
        
        if st.button("🚀 Veriyi Getir", use_container_width=True):
            with st.spinner("Sheets'ten veriler sökülüyor..."):
                df = veri_cek(secilen_id, secilen_sayfa)
                if not df.empty:
                    st.session_state.ham_veri = df.copy()
                    
                    # Tarih Filtreleme
                    t_col = next((c for c in df.columns if c.lower() in ['tarih', 'date', 'gün', 'day']), None)
                    if t_col:
                        df[t_col] = pd.to_datetime(df[t_col], errors='coerce', dayfirst=True)
                        df = df[(df[t_col].dt.date >= baslangic) & (df[t_col].dt.date <= bitis)]
                        df[t_col] = df[t_col].dt.strftime('%d.%m.%Y')
                    
                    st.session_state.aktif_veri = df
                else:
                    st.error("Veri çekilemedi, Sheets'i kontrol et Neco.")

    # Veri varsa ekrana dök
    if st.session_state.aktif_veri is not None:
        df_goster = st.session_state.aktif_veri.copy()
        
        # Filtreler
        if 'CampaignName' in df_goster.columns:
            k_sec = st.multiselect("Kampanyalar:", df_goster['CampaignName'].unique())
            if k_sec: df_goster = df_goster[df_goster['CampaignName'].isin(k_sec)]

        st.dataframe(df_goster, use_container_width=True)
        
        # AI Analiz Bölümü
        st.divider()
        st.subheader("🤖 AI Uzman Yorumu")
        if st.button("🧠 Veriyi Analiz Et"):
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"Şu verileri analiz et ve bana 3 kritik aksiyon öner: {df_goster.to_string()}"
            with st.spinner("Gemini düşünüyor..."):
                cevap = model.generate_content(prompt)
                st.write(cevap.text)
