import pandas as pd
import streamlit as st
import requests

def get_data():
    # Makroyu "Web Uygulaması" olarak yayınladığında sana verdiği URL
    # Sonu muhtemelen /exec ile bitiyordur
    API_URL = "hhttp://script.google.com/u/0/home/projects/1j5coLDJcPzFVhzMcc5sVj2vxLhGm24Dp1d23okNFzOKctRCjqD0C02SE/edit"
    
    try:
        response = requests.get(API_URL)
        
        # Eğer makron JSON döndürüyorsa:
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
        else:
            st.error(f"Hata: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Makroya bağlanırken hata oluştu: {e}")
        return pd.DataFrame()

def show_report():
    df = get_data()
    if not df.empty:
        # Metrikleri gösterelim
        st.metric("Toplam Harcama", f"{df['Cost'].sum()} TL")
        st.dataframe(df)
    else:
        st.warning("Veri gelmedi. Makro URL'sini ve 'Erişim' ayarlarını kontrol et.")
