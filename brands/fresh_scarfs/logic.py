import streamlit as st
from utils import api_handler as api
from brands.fresh_scarfs import constants
from brands.fresh_scarfs.reports import daily_performance, meta_reports

def show_report():
    st.markdown("### 📂 Fresh Scarfs Rapor Gezgini")

    # --- GOOGLE ADS KLASÖRÜ ---
    with st.expander("📁 Google Ads Raporları", expanded=True):
        col_text, col_btn = st.columns([3, 1])
        col_text.write("📄 Günlük Performans")
        if col_btn.button("Görüntüle", key="btn_daily"):
            st.session_state.fs_active_report = "daily"

    # --- META REKLAMLARI KLASÖRÜ ---
    with st.expander("📁 Meta (FB/IG) Raporları"):
        col_text, col_btn = st.columns([3, 1])
        col_text.write("📄 Meta Reklam Analizi")
        if col_btn.button("Görüntüle", key="btn_meta"):
            st.session_state.fs_active_report = "meta"

    st.divider()

    # --- RAPOR ÇALIŞTIRMA MANTIĞI ---
    if 'fs_active_report' in st.session_state:
        rep_type = st.session_state.fs_active_report
        
        # Doğru ID'yi constants dosyasından çekiyoruz
        target_id = constants.SHEET_IDS.get(rep_type)

        if rep_type == "daily":
            daily_performance.run(target_id)
        elif rep_type == "meta":
            meta_reports.run(target_id)
