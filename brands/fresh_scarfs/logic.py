import pandas as pd
import streamlit as st
import requests

def get_data():
    # 1. Ayarlar
    API_URL = "https://script.google.com/macros/s/AKfycbwPSkft-3lxwcq85HC805Uin0yI-i-d1hcmmGEHCpbfdhiNzgxQ8ZSDS7bsklO3E7qD/exec" # /exec ile biten URL
    SHEET_ID = "1V1_YvNbW3W2qOlk1SnLaPOgSUMO_tuShCXtX81yPEgA"
    TOKEN = "manuka-fresh-reports" # Script'e yazdığın gizli şifre
    
    # 2. Parametreleri Hazırla
    params = {
        "token": TOKEN,
        "id": SHEET_ID,
        "islem": "veri",
        "sayfa": "Sayfa1" # Çekmek istediğin sekme adı
    }
    
    try:
        # Kapıyı doğru anahtarlarla çalıyoruz
        response = requests.get(API_URL, params=params)
        
        if response.status_code == 200:
            raw_data = response.json() # Gelen veri listelerden oluşan bir liste (2D Array)
            
            # App Script 'getValues()' kullandığı için ilk satır başlıklar, diğerleri veridir.
            # Bunu Pandas DataFrame'e düzgünce çevirelim:
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                return df
            else:
                return pd.DataFrame()
        else:
            st.error(f"Bağlantı Hatası: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Veri işlenirken hata oluştu: {e}")
        return pd.DataFrame()

def show_report():
    df = get_data()
    if not df.empty:
        # Sayısal sütunları temizleyelim (Veri bazen metin gelebilir)
        numeric_cols = ['Cost', 'Clicks', 'Impressions', 'Conversions', 'ConversionValue']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Metrikleri Göster
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Harcama", f"{df['Cost'].sum():,.2f} TL")
        c2.metric("Toplam Tıklama", f"{df['Clicks'].sum():,.0f}")
        c3.metric("Ciro", f"{df['ConversionValue'].sum():,.2f} TL")
        
        st.divider()
        st.subheader("Ham Veri Tablosu")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Veri çekilemedi. Parametreleri (Token, ID, Sayfa Adı) kontrol et.")
