import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
import json
import os

st.set_page_config(page_title="Rapor Analizi", layout="wide")

# --- VERİ YÖNETİMİ ---
DATA_FILE = "rapor_veritabanı.json"

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"MANUKA": {}, "FRESH SCARFS": {}}

def verileri_kaydet(veriler):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

if 'giris_yapti_mi' not in st.session_state or not st.session_state.giris_yapti_mi:
    st.warning("Önce ana sayfadan giriş yapmalısın!")
    st.stop()

if 'sheets_verileri' not in st.session_state:
    st.session_state.sheets_verileri = verileri_yukle()

aktif_marka = st.session_state.marka
if aktif_marka is None:
    st.warning("Lütfen önce marka seç!")
    st.stop()

st.title(f"📊 {aktif_marka} Rapor Merkezi")

with st.popover("➕ Rapor Ekle"):
    with st.form("yeni_rapor_formu", clear_on_submit=True):
        yeni_ad = st.text_input("Sheets Adı")
        yeni_id = st.text_input("Sheets ID")
        if st.form_submit_button("Kaydet"):
            if yeni_ad and yeni_id:
                veriler = verileri_yukle()
                veriler[aktif_marka][yeni_ad] = yeni_id
                verileri_kaydet(veriler)
                st.session_state.sheets_verileri = veriler
                st.success("Eklendi!")
                st.rerun()

mevcut_raporlar = st.session_state.sheets_verileri.get(aktif_marka, {})

if not mevcut_raporlar:
    st.info("Kayıtlı rapor yok.")
else:
    secilen_rapor = st.selectbox("Rapor Seç:", list(mevcut_raporlar.keys()))
    secilen_id = mevcut_raporlar[secilen_rapor]
    
    API_URL = "https://script.google.com/macros/s/AKfycbxHd6N9TF2uzqJr-EhEfGyGH3j2oGTEiTRpKShSwwoWpJuVocyXVGHbWHyYNDL9uSQ/exec"
    API_TOKEN = "manuka-fresh-reports"

    try:
        params = {"islem": "sekmeler", "id": secilen_id, "token": API_TOKEN}
        sayfalar = requests.get(API_URL, params=params).json()
        secilen_sayfa = st.selectbox("Sekme Seç:", sayfalar)
        
        col1, col2 = st.columns(2)
        baslangic = col1.date_input("Başlangıç")
        bitis = col2.date_input("Bitiş")

        if st.button("🚀 Veriyi Getir", use_container_width=True):
            with st.spinner("Veriler getiriliyor..."):
                v_params = {"islem": "veri", "id": secilen_id, "sayfa": secilen_sayfa, "token": API_TOKEN}
                res = requests.get(API_URL, params=v_params).json()
                
                if len(res) > 1:
                    idx = 0
                    for i, s in enumerate(res[:15]):
                        if any(k in [str(x).lower() for x in s] for k in ['tarih', 'date', 'gün']):
                            idx = i
                            break
                    
                    df = pd.DataFrame(res[idx+1:], columns=res[idx])
                    
                    # --- KORUMA KALKANI: ID SÜTUNLARINI SAYIYA ÇEVİRME ---
                    korunacak = ['tarih', 'date', 'gün', 'day', 'campaign', 'kampanya', 'status', 'source', 'medium']
                    
                    for c in df.columns:
                        c_lower = c.lower()
                        if not any(k in c_lower for k in korunacak):
                            # Sadece metrikleri temizle
                            s = df[c].astype(str).str.replace('₺', '', regex=False).str.replace('%', '', regex=False).str.strip()
                            # Virgül binlik mi ondalık mı? Genelde binliktir, siliyoruz.
                            s = s.str.replace(',', '', regex=False) 
                            df[c] = pd.to_numeric(s, errors='coerce').fillna(0)
                    
                    # Tarih Filtresi
                    t_col = next((c for c in df.columns if c.lower() in ['tarih', 'date', 'gün']), None)
                    if t_col:
                        df[t_col] = pd.to_datetime(df[t_col], errors='coerce', dayfirst=True)
                        df = df.dropna(subset=[t_col])
                        df = df[(df[t_col].dt.date >= baslangic) & (df[t_col].dt.date <= bitis)]
                        df[t_col] = df[t_col].dt.strftime('%d.%m.%Y')
                    
                    st.session_state.aktif_veri = df
                    st.session_state.ham_veri = df.copy()

        if st.session_state.aktif_veri is not None:
            st.divider()
            df_display = st.session_state.aktif_veri.copy()
            
            # --- PROFESYONEL TABLO BİÇİMLENDİRME ---
            def stil_uygula(val, col):
                c_low = col.lower()
                if any(x in c_low for x in ['cost', 'revenue', 'cpc', 'cpa', 'value']):
                    return f"₺ {val:,.2f}"
                if any(x in c_low for x in ['cr', 'roas', 'rate', 'oran']):
                    return f"% {val:,.2f}"
                if isinstance(val, (int, float)):
                    return f"{val:,.0f}"
                return val

            # Tabloyu formatlayarak göster
            styled_df = df_display.copy()
            for col in styled_df.columns:
                if styled_df[col].dtype in ['float64', 'int64']:
                    styled_df[col] = styled_df[col].apply(lambda x: stil_uygula(x, col))

            st.dataframe(styled_df, use_container_width=True)
            
            if st.button("🧠 AI Analizi Yap"):
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"Şu Google Ads verilerini analiz et ve kritik yerleri söyle: {df_display.to_string()}"
                cevap = model.generate_content(prompt)
                st.info(cevap.text)

    except Exception as e:
        st.error(f"Hata: {e}")
