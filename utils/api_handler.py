import requests
import pandas as pd
import streamlit as st
import config

def fetch_from_sheets(sheet_id, sayfa="Sayfa1"):
    params = {
        "token": config.TOKEN,
        "id": sheet_id,
        "islem": "veri",
        "sayfa": sayfa
    }
    
    try:
        # 1. İstek Gönder
        response = requests.get(config.API_URL, params=params)
        
        # 2. HTTP Durum Kodunu Kontrol Et (200 OK olmalı)
        if response.status_code != 200:
            st.error(f"HTTP Hatası: {response.status_code}")
            return pd.DataFrame()

        # 3. Yanıt Boş mu Kontrol Et
        if not response.text.strip():
            st.error("API'den boş bir yanıt geldi. URL veya Parametreleri kontrol edin.")
            return pd.DataFrame()

        # 4. JSON Dönüştürmeyi Dene
        try:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                return df
            return pd.DataFrame()
        except Exception as json_err:
            st.error("Gelen veri JSON formatında değil.")
            # Hatanın ne olduğunu anlamak için gelen ham metni gösterelim
            st.code(response.text[:500], language="html") 
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Bağlantı sırasında bir hata oluştu: {e}")
        return pd.DataFrame()
