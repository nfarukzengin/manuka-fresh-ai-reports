import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Alarm Merkezi", layout="wide")

# Giriş Kontrolü
if 'giris_yapti_mi' not in st.session_state or not st.session_state.giris_yapti_mi:
    st.warning("Önce ana sayfadan giriş yapmalısın kiral!")
    st.stop()

st.title(f"🚨 {st.session_state.marka} - Alarm Yönetim Merkezi")

# --- KURAL 1: IMPRESSIONS KURGUSU ---
st.write("---")
st.subheader("👁️ Impressions Kurgusu")

with st.container():
    st.info("Kural: Dünün Impressions değeri, ondan önceki 7 günün ortalamasından %20 aşağıdaysa alarm oluşturur.")
    
    col1, col2 = st.columns(2)
    with col1:
        imp_kural_aktif = st.toggle("⚙️ Kuralı Çalıştır", value=True, key="imp_kural")
    with col2:
        imp_slack_aktif = st.toggle("💬 Slack Bildirimi", value=False, key="imp_slack")
        
    if imp_kural_aktif:
        if 'ham_veri' in st.session_state and st.session_state.ham_veri is not None:
            df_alert = st.session_state.ham_veri.copy()
            aktif_tarih = next((col for col in df_alert.columns if col.lower() in ['tarih', 'date', 'gün', 'day']), None)
            
            if aktif_tarih:
                df_alert['gecici_tarih'] = pd.to_datetime(df_alert[aktif_tarih], errors='coerce', dayfirst=True)
                df_alert['Impressions'] = pd.to_numeric(df_alert['Impressions'], errors='coerce').fillna(0)
                
                # Dün ve Öncesi Hesabı
                bugun = pd.Timestamp.today().normalize()
                dun = bugun - pd.Timedelta(days=1)
                df_alert = df_alert[df_alert['gecici_tarih'] <= dun]
                
                # Gruplama ve Hesaplama
                agg_kurallari = {'Impressions': 'sum'}
                if 'CampaignStatus' in df_alert.columns: agg_kurallari['CampaignStatus'] = 'last'
                df_gruplu = df_alert.groupby(['CampaignName', 'gecici_tarih']).agg(agg_kurallari).reset_index()
                
                uyarilar = []
                for kampanya in df_gruplu['CampaignName'].unique():
                    k_df = df_gruplu[df_gruplu['CampaignName'] == kampanya].sort_values('gecici_tarih').dropna()
                    
                    if not k_df.empty and len(k_df) >= 8:
                        if 'CampaignStatus' in k_df.columns and str(k_df.iloc[-1]['CampaignStatus']).strip().upper() != 'ENABLED': 
                            continue 
                        
                        son_veri = k_df.iloc[-1] 
                        gecmis_7 = k_df.iloc[-8:-1]
                        
                        # Son veri dün mü kontrolü
                        if son_veri['gecici_tarih'].date() == dun.date():
                            gecmis_ort = gecmis_7['Impressions'].mean()
                            guncel_imp = son_veri['Impressions']
                            
                            if gecmis_ort > 0:
                                degisim = ((guncel_imp - gecmis_ort) / gecmis_ort) * 100
                                if degisim <= -20:
                                    uyarilar.append(f"📉 **{kampanya}**: Gösterim %{abs(degisim):.1f} düştü! (Ort: {gecmis_ort:.0f} ➡️ Dün: {guncel_imp:.0f})")
                
                if uyarilar:
                    for u in uyarilar: st.error(u)
                    if imp_slack_aktif:
                        st.warning("🔔 Slack bildirimi aktif: Bu uyarılar sabah 11:00'de Slack kanalına iletilecek.")
                else:
                    st.success("✅ Dün için Impressions kuralına takılan kampanya yok.")
        else:
            st.warning("⚠️ Arka planda henüz veri yok. Lütfen 'Rapor' sayfasına gidip bir rapor seç ve 'Verileri Analiz Et' butonuna bas.")
