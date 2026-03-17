import pandas as pd
import streamlit as st
import requests

# --- VERİ ÇEKME FONKSİYONU ---
def get_data(sayfa="Sayfa1"):
    API_URL = "SENİN_MAKRO_WEB_APP_URL_BURAYA" # Buraya kendi URL'ni yapıştır
    SHEET_ID = "1V1_YvNbW3W2qOlk1SnLaPOgSUMO_tuShCXtX81yPEgA"
    TOKEN = "manuka-fresh-reports"
    
    params = {
        "token": TOKEN,
        "id": SHEET_ID,
        "islem": "veri",
        "sayfa": sayfa
    }
    
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                # Sayısal sütun dönüşümü
                for col in ['Cost', 'Clicks', 'Impressions', 'Conversions', 'ConversionValue']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- RAPORLAR ---
def gunluk_performans_raporu():
    st.subheader("📈 Günlük Performans Analizi")
    df = get_data(sayfa="Sayfa1")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Harcama", f"{df['Cost'].sum():,.2f} TL")
        c2.metric("Toplam Tıklama", f"{df['Clicks'].sum():,.0f}")
        c3.metric("Toplam Ciro", f"{df['ConversionValue'].sum():,.2f} TL")
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Veri çekilemedi. Makro ayarlarını kontrol et.")

# --- ANA YÖNLENDİRİCİ ---
def show_report():
    rapor_listesi = ["Seçiniz...", "Günlük Performans", "Kampanya Analizi"]
    secilen = st.selectbox("Bir rapor türü seçin:", rapor_listesi)
    
    st.divider()
    
    if secilen == "Seçiniz...":
        st.info("Lütfen işlem yapmak için bir rapor seçin.")
    elif secilen == "Günlük Performans":
        gunluk_performans_raporu()
    elif secilen == "Kampanya Analizi":
        st.write("Bu rapor yakında eklenecek.")
