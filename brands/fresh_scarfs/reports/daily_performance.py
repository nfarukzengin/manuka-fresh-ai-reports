import streamlit as st
from utils import api_handler as api

def run(sheet_id):
    st.subheader("📈 Günlük Performans Analizi")
    
    # Merkezi API handler'a ID'yi gönderip veriyi alıyoruz
    df = api.fetch_from_sheets(sheet_id, sayfa="Sayfa1")
    
    if not df.empty:
        st.success("Veriler başarıyla yüklendi.")
        st.dataframe(df)
    else:
        st.error("Bu rapor için veri çekilemedi.")
