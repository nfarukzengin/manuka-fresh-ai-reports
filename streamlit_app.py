import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# --- VERİ TABANI (JSON DOSYASI) İŞLEMLERİ ---
DATA_FILE = "rapor_veritabanı.json"

def verileri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"MANUKA": {}, "FRESH SCARFS": {}}

def verileri_kaydet(veriler):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

# --- VERİ ÇEKME FONKSİYONLARI ---
@st.cache_data(show_spinner=False)
def sekmeleri_getir(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    xls = pd.ExcelFile(url)
    return xls.sheet_names

@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url, sheet_name=sayfa_adi)
    return df

# --- HAFIZA (SESSION STATE) ---
if 'giris_yapti_mi' not in st.session_state: st.session_state.giris_yapti_mi = False
if 'marka' not in st.session_state: st.session_state.marka = None
if 'aktif_veri' not in st.session_state: st.session_state.aktif_veri = None

# Raporları JSON'dan çek, session_state'e yükle
if 'sheets_verileri' not in st.session_state:
    st.session_state.sheets_verileri = verileri_yukle()

# --- GİRİŞ SAYFASI ---
if not st.session_state.giris_yapti_mi:
    st.title("✋ Hop Hemşerim Nereye? Parolayı Söyle!")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        sifre = st.text_input("Parola", type="password", label_visibility="collapsed", placeholder="Parolayı gir...")
        if st.button("İçeri Gir", use_container_width=True):
            if sifre == "fresh123":
                st.session_state.giris_yapti_mi = True
                st.rerun()
            else: st.error("Yanlış parola!")

# --- ANA UYGULAMA ---
else:
    # 1. EKRAN: MARKA SEÇİMİ
    if st.session_state.marka is None:
        if st.button("🚪 Çıkış Yap"):
            st.session_state.giris_yapti_mi = False
            st.rerun()
        st.title("🏢 Tarafını Seç :)")
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👗 MANUKA", use_container_width=True): st.session_state.marka = "MANUKA"; st.rerun()
        with col2:
            if st.button("🧣 FRESH SCARFS", use_container_width=True): st.session_state.marka = "FRESH SCARFS"; st.rerun()

    # 2. EKRAN: MARKA İÇERİĞİ
    else:
        aktif_marka = st.session_state.marka
        col_baslik, col_buton = st.columns([4, 1])
        with col_baslik: st.title(f"📍 {aktif_marka} Dünyasına Hoş Geldin!")
        with col_buton:
            if st.button("⬅️ Tarafını Değiştir", use_container_width=True):
                st.session_state.marka = None
                st.session_state.aktif_veri = None
                st.rerun()
            
        st.divider()
        
        # Üst Kısım: Yeni Sheets Ekleme (SABİT KAYIT)
        with st.popover("➕ Yeni Rapor Bağla"):
            with st.form("yeni_sheets_formu", clear_on_submit=True):
                yeni_ad = st.text_input("Raporun Adı (Örn: Facebook Ads)")
                yeni_id = st.text_input("Google Sheets ID")
                kaydet = st.form_submit_button("Sisteme ve Dosyaya Kaydet")
                
                if kaydet:
                    if yeni_ad and yeni_id:
                        # Önce session'a sonra dosyaya yazıyoruz
                        st.session_state.sheets_verileri[aktif_marka][yeni_ad] = yeni_id
                        verileri_kaydet(st.session_state.sheets_verileri)
                        st.success(f"Süper! {yeni_ad} artık kalıcı olarak kaydedildi.")
                    else: st.error("Eksik bilgi girdin kiral.")

        st.write("---")

        mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]
        if mevcut_raporlar:
            # SİLME SEÇENEĞİ (Opsiyonel ama lazım olur)
            with st.expander("🗑️ Rapor Yönetimi / Sil"):
                silinecek = st.selectbox("Silmek istediğin raporu seç:", ["Seçiniz..."] + list(mevcut_raporlar.keys()))
                if st.button("Seçili Raporu Sistemden Sil"):
                    if silinecek != "Seçiniz...":
                        del st.session_state.sheets_verileri[aktif_marka][silinecek]
                        verileri_kaydet(st.session_state.sheets_verileri)
                        st.warning(f"{silinecek} silindi.")
                        st.rerun()

            st.subheader("📁 Kayıtlı Raporların")
            secilen_rapor = st.selectbox("Hangi raporu inceleyeceğiz?", list(mevcut_raporlar.keys()))
            secilen_id = mevcut_raporlar[secilen_rapor]
            
            if secilen_id:
                try:
                    with st.spinner("Sekmeler aranıyor..."):
                        sayfalar = sekmeleri_getir(secilen_id)
                    secilen_sayfa = st.selectbox("Hangi sekmeye bakıyoruz?", sayfalar)
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1: baslangic = st.date_input("Nereden Başlayalım?")
                    with col_d2: bitis = st.date_input("Nerede Bitirelim?")
                    
                    if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                        with st.spinner("Veriler toparlanıyor..."):
                            df = veri_cek(secilen_id, secilen_sayfa)
                            if 'Tarih' in df.columns:
                                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
                                df = df.dropna(subset=['Tarih'])
                                df['Tarih'] = df['Tarih'].dt.date
                                maske = (df['Tarih'] >= baslangic) & (df['Tarih'] <= bitis)
                                df = df.loc[maske].copy()
                                df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%d.%m.%Y')
                            
                            if not df.empty:
                                st.session_state.aktif_veri = df
                            else:
                                st.warning("Veri yok!")
                                st.session_state.aktif_veri = None
                except Exception as e:
                    st.error(f"Hata: {e}")

        # ==========================================
        # TABLO, GRAFİK VE AI BÖLÜMÜ (HAFIZADAN OKUR)
        # ==========================================
        if st.session_state.aktif_veri is not None:
            df = st.session_state.aktif_veri.copy()
            
            # --- TABLO VE TOPLAM SATIRI ---
            sayisal_sutunlar = df.select_dtypes(include=['number']).columns
            toplam_degerler = {}
            for col in sayisal_sutunlar:
                c_lower = col.lower()
                if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                    toplam_degerler[col] = df[col].mean()
                else:
                    toplam_degerler[col] = df[col].sum()
            
            toplam_satiri = pd.DataFrame([toplam_degerler])
            toplam_satiri['Tarih'] = 'TOPLAM'
            df_tablo = pd.concat([df, toplam_satiri], ignore_index=True)
            
            # (Formatla fonksiyonu ve styling aynı kalacak...)
            def formatla(val, col_name):
                if isinstance(val, (int, float)):
                    c_lower = col_name.lower()
                    if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir']) and 'cost' not in c_lower:
                        if val < 10 and val > -10: val = val * 100 
                        return f"% {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    elif any(x in c_lower for x in ['revenue', 'cost', 'cpc', 'cpa', 'harcama', 'reklam']):
                        return f"₺ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    else:
                        fmt_val = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        if fmt_val.endswith(",00"): fmt_val = fmt_val[:-3]
                        return fmt_val
                return val

            for col in df_tablo.columns:
                if col != 'Tarih': df_tablo[col] = df_tablo[col].apply(lambda x: formatla(x, col))
            
            st.dataframe(df_tablo.style.apply(lambda row: ['background-color: #004d40; color: white; font-weight: bold'] * len(row) if row['Tarih'] == 'TOPLAM' else [''] * len(row), axis=1), use_container_width=True)
            
            st.divider()

            # --- DİNAMİK GRAFİK ---
            st.subheader("📈 Veri Trendleri")
            secilen_metrikler = st.multiselect("Metrikler:", sayisal_sutunlar.tolist(), default=sayisal_sutunlar.tolist()[:1])
            if secilen_metrikler:
                df_grafik = df.set_index('Tarih')
                st.line_chart(df_grafik[secilen_metrikler])
                
            st.divider()

            # --- YAPAY ZEKA (GEMINI) ---
            st.subheader("🤖 AI'dan Al Haberi")
            soru_onerileri = [
                "✏️ Kendi sorumu yazacağım",
                "📊 CPA ve COS oranlarına göre reklam verimliliğini değerlendir.",
                "📉 En yüksek ve en düşük ciro yapılan günleri kıyasla, sence neden?",
                "🎯 Sadık müşteri kazanımı (CRM) ve ciro artışı için bana 3 stratejik aksiyon öner."
            ]
            secilen_soru = st.selectbox("Soru seç:", soru_onerileri)
            kullanici_sorusu = st.text_area("Sorun:") if secilen_soru == "✏️ Kendi sorumu yazacağım" else secilen_soru
                
            if st.button("🧠 AI Analizini Başlat", use_container_width=True):
                try:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(modeller[0])
                    
                    prompt = f"Sen tecrübeli bir Dijital Pazarlama Uzmanısın. Veriler: {df.to_string()} \nSoru: {kullanici_sorusu}"
                    
                    with st.spinner("Uzman raporu hazırlıyor..."):
                        cevap = model.generate_content(prompt)
                        
                        st.write("---")
                        st.subheader("📋 Uzman Analiz Raporu")
                        
                        # Okunabilirliği artıran özel alan
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #1e1e1e; 
                                padding: 25px; 
                                border-radius: 10px; 
                                border-left: 5px solid #004d40;
                                color: #e0e0e0;
                                line-height: 1.6;
                                font-size: 16px;
                            ">
                                {cevap.text.replace("\n", "<br>")}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                except Exception as e:
                    st.error(f"AI Hatası: {e}")
