import streamlit as st
import json
import os

st.set_page_config(page_title="Fresh AI - Giriş", layout="wide")

# --- VERİTABANI FONKSİYONLARI ---
DATA_FILE = "rapor_veritabanı.json"

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"MANUKA": {}, "FRESH SCARFS": {}}

# --- HAFIZA AYARLARI ---
if 'giris_yapti_mi' not in st.session_state: st.session_state.giris_yapti_mi = False
if 'marka' not in st.session_state: st.session_state.marka = None
if 'sheets_verileri' not in st.session_state: st.session_state.sheets_verileri = verileri_yukle()
if 'aktif_veri' not in st.session_state: st.session_state.aktif_veri = None
if 'ham_veri' not in st.session_state: st.session_state.ham_veri = None

# --- GİRİŞ KONTROLÜ ---
if not st.session_state.giris_yapti_mi:
    st.title("✋ Hop Hemşerim Nereye? Parolayı Söyle!")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        sifre = st.text_input("Parola", type="password")
        if st.button("İçeri Gir", use_container_width=True):
            if sifre == "fresh123":
                st.session_state.giris_yapti_mi = True
                st.rerun()
            else:
                st.error("Yanlış parola!")
else:
    # --- MARKA SEÇİMİ ---
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
    else:
        st.title(f"📍 {st.session_state.marka} Dünyasındasın")
        st.success("Giriş Başarılı! Sol taraftaki menüden 'Rapor' veya 'Alarm' sayfasını seçebilirsin.")
        if st.button("⬅️ Marka Değiştir / Çıkış"):
            st.session_state.marka = None
            st.rerun()
