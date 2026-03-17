import streamlit as st
from brands.fresh_scarfs import constants
# Rapor dosyalarımızı import ediyoruz
from brands.fresh_scarfs.reports import daily_performance, meta_reports

def show_report():
    st.markdown("### 📂 Rapor Gezgini")
    st.caption("İncelemek istediğiniz klasörü açın ve raporu seçin.")

    # --- KLASÖR 1: GOOGLE ADS ---
    with st.expander("📁 01- Google Ads Raporları", expanded=True):
        col_text, col_btn = st.columns([3, 1])
        col_text.write("📄 Günlük Performans Analizi")
        if col_btn.button("Görüntüle", key="fs_ads_daily"):
            st.session_state.fs_active_report = "google_ads_daily"

    # --- KLASÖR 2: META ADS (FB/IG) ---
    with st.expander("📁 02- Meta Ads Raporları"):
        col_text, col_btn = st.columns([3, 1])
        col_text.write("📄 Kampanya Performans")
        if col_btn.button("Görüntüle", key="fs_meta_perf"):
            st.session_state.fs_active_report = "meta_ads_performance"
            
        col_text, col_btn = st.columns([3, 1])
        col_text.write("📄 Kreatif Analizi")
        if col_btn.button("Görüntüle", key="fs_meta_creative"):
            st.session_state.fs_active_report = "meta_creative_analysis"

    # --- KLASÖR 3: PAZARYERLERİ ---
    with st.expander("📁 03- Trendyol & Pazaryeri"):
        st.write("📄 Satış ve İade Raporu (Yakında)")

    st.divider()

    # --- ÇALIŞTIRMA ALANI (Hangi butona basıldıysa o çalışır) ---
    if 'fs_active_report' in st.session_state:
        report_key = st.session_state.fs_active_report
        target_id = constants.SHEET_IDS.get(report_key)

        if report_key == "google_ads_daily":
            daily_performance.run(target_id)
        elif report_key in ["meta_ads_performance", "meta_creative_analysis"]:
            st.info(f"{report_key} raporu için tasarım aşamasındayız.")
