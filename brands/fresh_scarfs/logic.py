import pandas as pd
import streamlit as st

def get_data():
    # Senin paylaştığın Sheet ID
    SHEET_ID = "1V1_YvNbW3W2qOlk1SnLaPOgSUMO_tuShCXtX81yPEgA"
    SHEET_NAME = "Sayfa1" # Script hangi sayfaya yazıyorsa o
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    try:
        df = pd.read_csv(url)
        # Tarih sütununu düzeltelim (Google Ads formatına göre)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        return pd.DataFrame()

def show_report():
    df = get_data()
    
    if not df.empty:
        st.success("Fresh Scarfs verileri başarıyla yüklendi.")
        
        # Özet Metrikler (KPI Cards)
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Harcama", f"{df['Cost'].sum():,.2f} TL")
        col2.metric("Toplam Tıklama", f"{df['Clicks'].sum():,}")
        col3.metric("Dönüşüm Değeri", f"{df['ConversionValue'].sum():,.2f} TL")
        
        # Ham Veri Tablosu
        st.subheader("Günlük Performans Tablosu")
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)
    else:
        st.warning("Henüz görüntülenecek veri yok.")
