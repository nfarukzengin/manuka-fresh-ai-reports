import requests
import pandas as pd
import streamlit as st
import config # Ortak ayarları alıyoruz

def fetch_from_sheets(sheet_id, sayfa="Sayfa1"):
    params = {
        "token": config.TOKEN,
        "id": sheet_id,
        "islem": "veri",
        "sayfa": sayfa
    }
    try:
        response = requests.get(config.API_URL, params=params)
        if response.status_code == 200:
            raw_data = response.json()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"API Hatası: {e}")
        return pd.DataFrame()
