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

# Giriş Kontrolü
if 'giris_yapti_mi' not in st.session_state or not st.session_state.giris_yapti_mi:
    st.warning("Önce ana sayfadan giriş yapmalısın!")
    st.stop()

# Marka Kontrolü
aktif_marka = st.session_state.marka
if aktif_marka is None:
    st.warning("Lütfen önce marka seç!")
    st.stop()

st.title(f"📊 {aktif_marka} Rapor Merkezi")

# --- RAPOR EKLEME BÖLÜMÜ ---
with st.popover("➕ Rapor Ekle"):
    with st.form("yeni_rapor_formu", clear_on_submit=True):
        yeni_ad = st.text_input("Sheets Adı (Örn: Mart Reklamları)")
        yeni_id = st.text_input("Sheets ID")
        if st.form_submit_button("Kaydet"):
            if yeni_ad and yeni_id:
                veriler = verileri_yukle()
                veriler[aktif_marka][yeni_ad] = yeni_id
                verileri_kaydet(veriler)
                st.session_state.sheets_verileri = veriler
                st.success(f"'{yeni_ad}' başarıyla eklendi!")
                st.rerun()

# --- RAPOR SEÇİMİ VE VERİ ÇEKME ---
mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]

if not mevcut_raporlar:
    st.info("Henüz kayıtlı rapor yok, yukarıdaki butondan ekleyebilirsin.")
else:
    # Sabit Rapor Listesi
    secilen_rapor = st.selectbox("İncelemek istediğin raporu seç:", list(mevcut_raporlar.keys()))
    secilen_id = mevcut_raporlar[secilen_rapor]
    
    # API Ayarları
    API_URL = "https://script.google.com/macros/s/AKfycbxHd6N9TF2uzqJr-EhEfGyGH3j2oGTEiTRpKShSwwoWpJuVocyXVGHbWHyYNDL9uSQ/exec"
    API_TOKEN = "manuka-fresh-reports"

    # Sayfaları Getir
    params = {"islem": "sekmeler", "id": secilen_id, "token": API_TOKEN}
    try:
        sayfalar = requests.get(API_URL, params=params).json()
        secilen_sayfa = st.selectbox("Sekme Seç:", sayfalar)
        
        col1, col2 = st.columns(2)
        baslangic = col1.date_input("Filtre Başlangıç")
        bitis = col2.date_input("Filtre Bitiş")

        # ÖNEMLİ: Sadece bu butona basınca veri gelecek
        if st.button("🚀 Veriyi Getir", use_container_width=True):
            with st.spinner("Veriler sökülüp getiriliyor..."):
                v_params = {"islem": "veri", "id": secilen_id, "sayfa": secilen_sayfa, "token": API_TOKEN}
                res = requests.get(API_URL, params=v_params).json()
                
                if len(res) > 1:
                    # Başlıkları bul ve tabloyu kur
                    idx = 0
                    for i, s in enumerate(res[:15]):
                        if any(k in [str(x).lower() for x in s] for k in ['tarih', 'date', 'gün']):
                            idx = i
                            break
                    
                    df = pd.DataFrame(res[idx+1:], columns=res[idx])
                    
                    # Tarih Filtresi Uygula
                    t_col = next((c for c in df.columns if c.lower() in ['tarih', 'date', 'gün']), None)
                    if t_col:
                        df[t_col] = pd.to_datetime(df[t_col], errors='coerce', dayfirst=True)
                        df = df[(df[t_col].dt.date >= baslangic) & (df[t_col].dt.date <= bitis)]
                        df[t_col] = df[t_col].dt.strftime('%d.%m.%Y')
                    
                    # Sayısal Temizlik
                    for c in df.columns:
                        if c.lower() not in ['tarih', 'date', 'gün', 'kampanya']:
                            df[c] = pd.to_numeric(df[c].astype(str).str.replace('₺','').replace('%','').replace(',','.').strip(), errors='coerce').fillna(0)
                    
                    st.session_state.aktif_veri = df
                    st.session_state.ham_veri = df.copy()
                else:
                    st.error("Seçili sayfada veri bulunamadı.")

        # Veri Ekrana Basma
        if 'aktif_veri' in st.session_state and st.session_state.aktif_veri is not None:
            st.divider()
            st.dataframe(st.session_state.aktif_veri, use_container_width=True)
            
            # AI Analiz
            if st.button("🧠 AI Analizi Yap"):
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"Verileri analiz et: {st.session_state.aktif_veri.to_string()}"
                cevap = model.generate_content(prompt)
                st.info(cevap.text)

    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
