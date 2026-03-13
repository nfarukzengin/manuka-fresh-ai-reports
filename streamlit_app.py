import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import requests

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

# --- GİZLİ API KÖPRÜSÜ AYARLARI ---
API_URL = "https://script.google.com/macros/s/AKfycbxHd6N9TF2uzqJr-EhEfGyGH3j2oGTEiTRpKShSwwoWpJuVocyXVGHbWHyYNDL9uSQ/exec"
API_TOKEN = "manuka-fresh-reports"
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
    params = {"islem": "sekmeler", "id": sheet_id, "token": API_TOKEN}
    cevap = requests.get(API_URL, params=params)
    try: return cevap.json()
    except Exception: raise Exception(f"Google yanıtı okunamadı: {cevap.text[:100]}")

@st.cache_data(show_spinner=False)
def veri_cek(sheet_id, sayfa_adi):
    params = {"islem": "veri", "id": sheet_id, "sayfa": sayfa_adi, "token": API_TOKEN}
    cevap = requests.get(API_URL, params=params)
    try: veri = cevap.json()
    except Exception: raise Exception(f"Veri okunamadı: {cevap.text[:100]}")
    
    if len(veri) > 1:
        # Akıllı Başlık Bulucu (GA4 için)
        baslik_index = 0
        for i, satir in enumerate(veri[:25]):
            satir_kucuk = [str(hucre).strip().lower() for hucre in satir]
            if any(k in satir_kucuk for k in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium']):
                baslik_index = i
                break
        
        temiz_veri = veri[baslik_index:]
        
        # İkiz Sütun Dedektörü
        ham_kolonlar = [str(k).strip() if str(k).strip() != "" else f"Adsiz_{i}" for i, k in enumerate(temiz_veri[0])]
        temiz_kolonlar = []
        for k in ham_kolonlar:
            orijinal = k
            sayac = 1
            while k in temiz_kolonlar:
                k = f"{orijinal}_{sayac}"
                sayac += 1
            temiz_kolonlar.append(k)
            
        df = pd.DataFrame(temiz_veri[1:], columns=temiz_kolonlar)
    else:
        df = pd.DataFrame(veri)
        
    # --- TAŞ FIRIN VERİ TEMİZLEYİCİ ---
    for col in df.columns:
        if col.lower() not in ['tarih', 'date', 'gün', 'day', 'sessionsourcemedium', 'ürün adı', 'kampanya', 'source', 'medium']:
            def temizle(x):
                if isinstance(x, str):
                    x = x.replace('₺', '').replace('%', '').replace('None', '0').strip()
                    if '.' in x and ',' in x:
                        x = x.replace('.', '').replace(',', '.')
                    elif ',' in x:
                        x = x.replace(',', '.')
                    elif '.' in x:
                        parts = x.split('.')
                        if len(parts) > 2: x = x.replace('.', '')
                        elif len(parts[-1]) == 3: x = x.replace('.', '')
                return x 
            df[col] = df[col].apply(temizle)
            df[col] = pd.to_numeric(df[col], errors='ignore')
            
    return df

# --- HAFIZA (SESSION STATE) ---
if 'giris_yapti_mi' not in st.session_state: st.session_state.giris_yapti_mi = False
if 'marka' not in st.session_state: st.session_state.marka = None
if 'aktif_veri' not in st.session_state: st.session_state.aktif_veri = None
if 'sheets_verileri' not in st.session_state: st.session_state.sheets_verileri = verileri_yukle()

# --- GİRİŞ SAYFASI ---
if not st.session_state.giris_yapti_mi:
    st.title("✋ Hop Hemşerim Nereye? Parolayı Söyle!")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        sifre = st.text_input("Parola", type="password", label_visibility="collapsed")
        if st.button("İçeri Gir", use_container_width=True):
            if sifre == "fresh123": st.session_state.giris_yapti_mi = True; st.rerun()
            else: st.error("Yanlış parola!")

# --- ANA UYGULAMA ---
else:
    if st.session_state.marka is None:
        if st.button("🚪 Çıkış Yap"): st.session_state.giris_yapti_mi = False; st.rerun()
        st.title("🏢 Tarafını Seç :)")
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👗 MANUKA", use_container_width=True): st.session_state.marka = "MANUKA"; st.rerun()
        with col2:
            if st.button("🧣 FRESH SCARFS", use_container_width=True): st.session_state.marka = "FRESH SCARFS"; st.rerun()

    else:
        aktif_marka = st.session_state.marka
        col_b, col_btn = st.columns([4, 1])
        with col_b: st.title(f"📍 {aktif_marka} Dünyasına Hoş Geldin!")
        with col_btn:
            if st.button("⬅️ Tarafını Değiştir", use_container_width=True):
                st.session_state.marka = None; st.session_state.aktif_veri = None; st.rerun()
            
        st.divider()
        
        with st.popover("➕ Yeni Rapor Bağla"):
            with st.form("yeni_sheets", clear_on_submit=True):
                yeni_ad = st.text_input("Raporun Adı")
                yeni_id = st.text_input("Sheets ID")
                if st.form_submit_button("Kaydet") and yeni_ad and yeni_id:
                    st.session_state.sheets_verileri[aktif_marka][yeni_ad] = yeni_id
                    verileri_kaydet(st.session_state.sheets_verileri)
                    st.success("Eklendi!")

        mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]
        if mevcut_raporlar:
            with st.expander("🗑️ Rapor Yönetimi / Sil"):
                silinecek = st.selectbox("Silmek istediğin raporu seç:", ["Seçiniz..."] + list(mevcut_raporlar.keys()), key="silme_kutusu")
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
                    sayfalar = sekmeleri_getir(secilen_id)
                    if isinstance(sayfalar, list):
                        secilen_sayfa = st.selectbox("Hangi sekmeye bakıyoruz?", sayfalar)
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1: baslangic = st.date_input("Nereden Başlayalım?")
                        with col_d2: bitis = st.date_input("Nerede Bitirelim?")
                        
                        if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                            with st.spinner("Arka plandan veriler sökülüp getiriliyor..."):
                                df = veri_cek(secilen_id, secilen_sayfa)
                                
                                tarih_kolonu = None
                                for col in df.columns:
                                    if col.lower() in ['tarih', 'date', 'gün', 'day']:
                                        tarih_kolonu = col
                                        break
                                
                                if tarih_kolonu:
                                    df[tarih_kolonu] = df[tarih_kolonu].astype(str).str.replace(r'\.0$', '', regex=True)
                                    if df[tarih_kolonu].str.match(r'^\d{8}$').all():
                                        df[tarih_kolonu] = pd.to_datetime(df[tarih_kolonu], format='%Y%m%d', errors='coerce')
                                    else:
                                        df[tarih_kolonu] = pd.to_datetime(df[tarih_kolonu], errors='coerce', dayfirst=True)
                                    
                                    df = df.dropna(subset=[tarih_kolonu])
                                    df[tarih_kolonu] = df[tarih_kolonu].dt.date
                                    
                                    maske = (df[tarih_kolonu] >= baslangic) & (df[tarih_kolonu] <= bitis)
                                    df = df.loc[maske].copy()
                                    
                                    df[tarih_kolonu] = pd.to_datetime(df[tarih_kolonu]).dt.strftime('%d.%m.%Y')
                                
                                if not df.empty:
                                    st.session_state.aktif_veri = df
                                else:
                                    st.warning("Bu tarihler arasında veri yok kiral.")
                                    st.session_state.aktif_veri = None
                    else: st.error("API sekme isimlerini alamadı.")
                except Exception as e: st.error(f"Hata: {e}")

        # ==========================================
        # TABLO, GRAFİK VE AI BÖLÜMÜ
        # ==========================================
        if st.session_state.aktif_veri is not None:
            df = st.session_state.aktif_veri.copy()
            # Kampanya Filtresi
            if 'CampaignName' in df.columns:
                secilen_kampanyalar = st.multiselect("🎯 Kampanya Seç:", df['CampaignName'].unique())
                if secilen_kampanyalar:
                    df = df[df['CampaignName'].isin(secilen_kampanyalar)]
                    
         # --- ALERT SİSTEMİ (YAN YANA KUTUCUKLU) ---
            aktif_tarih = next((col for col in df.columns if col.lower() in ['tarih', 'date', 'gün', 'day']), None)
            
            if 'CampaignName' in df.columns and aktif_tarih:
                st.subheader("📊 Performans Durum Merkezi")
                
                alarm_verenler = {}
                isler_yolunda = []
                
                df_alert = df.copy()
                df_alert['gecici_tarih'] = pd.to_datetime(df_alert[aktif_tarih], format='%d.%m.%Y', errors='coerce')
                
                # Metrikleri saf sayıya çevirme
                for metrik in ['Impressions', 'Clicks', 'Conversions']:
                    if metrik in df_alert.columns:
                        df_alert[metrik] = pd.to_numeric(df_alert[metrik].astype(str).str.replace(',', '').str.replace('.', ''), errors='coerce').fillna(0)
                
                for kampanya in df_alert['CampaignName'].unique():
                    k_df = df_alert[df_alert['CampaignName'] == kampanya].sort_values('gecici_tarih').dropna(subset=['gecici_tarih'])
                    
                    if not k_df.empty:
                        # Sadece aktif kampanyalar
                        if 'CampaignStatus' in k_df.columns:
                            son_durum = str(k_df.iloc[-1]['CampaignStatus']).strip().upper()
                            if son_durum != 'ENABLED': continue
                            
                        if len(k_df) >= 8: # 1 güncel + 7 geçmiş gün
                            son_veri = k_df.iloc[-1]
                            gecmis_7 = k_df.iloc[-8:-1]
                            kampanya_uyarilari = []
                            
                            for metrik in ['Impressions', 'Clicks', 'Conversions']:
                                if metrik in k_df.columns:
                                    gecmis_ort = gecmis_7[metrik].mean()
                                    guncel = son_veri[metrik]
                                    if gecmis_ort > 0:
                                        degisim = ((guncel - gecmis_ort) / gecmis_ort) * 100
                                        if degisim <= -20:
                                            kampanya_uyarilari.append(f"{metrik}: %{abs(degisim):.1f} düştü! (Ort: {gecmis_ort:.0f} ➡️ Güncel: {guncel:.0f})")
                            
                            if kampanya_uyarilari:
                                alarm_verenler[kampanya] = kampanya_uyarilari
                            else:
                                isler_yolunda.append(kampanya)
                
                # --- YAN YANA SEÇİM KUTUCUKLARI ---
                durum_secimi = st.radio(
                    "Kampanyaları Filtrele:",
                    ["🔴 Alarm Verenler", "🟢 İşler Yolunda"],
                    horizontal=True
                )
                
                st.write("---")
                
                if durum_secimi == "🔴 Alarm Verenler":
                    if alarm_verenler:
                        for kampanya, hatalar in alarm_verenler.items():
                            with st.expander(f"📉 {kampanya}", expanded=True):
                                for hata in hatalar: st.error(hata)
                    else:
                        st.success("Harika! %20'den fazla düşüş yaşayan aktif kampanya yok.")
                        
                elif durum_secimi == "🟢 İşler Yolunda":
                    if isler_yolunda:
                        for kampanya in isler_yolunda:
                            st.success(f"✅ **{kampanya}** (Kritik düşüş yok, stabil veya artışta)")
                    else:
                        st.warning("Şu an için sorunsuz ilerleyen aktif kampanya bulunmuyor.")
            # -------------------------------------------------------------------
            
            tarih_kolonu = None
            for col in df.columns:
                if col.lower() in ['tarih', 'date', 'gün', 'day']:
                    tarih_kolonu = col
                    break
            
            sayisal_sutunlar = df.select_dtypes(include=['number']).columns
            toplam_degerler = {}
            for col in sayisal_sutunlar:
                c_lower = col.lower()
                if any(x in c_lower for x in ['cos', 'roas', 'cr', 'oran', 'katkı', 'gelir', 'duration']) and 'cost' not in c_lower:
                    toplam_degerler[col] = df[col].mean()
                else:
                    toplam_degerler[col] = df[col].sum()
            
            if toplam_degerler:
                toplam_satiri = pd.DataFrame([toplam_degerler])
                if tarih_kolonu:
                    toplam_satiri[tarih_kolonu] = 'TOPLAM'
                else:
                    toplam_satiri[df.columns[0]] = 'TOPLAM'
                df_tablo = pd.concat([df, toplam_satiri], ignore_index=True)
            else:
                df_tablo = df.copy()
            
            def formatla(val, col_name):
                if pd.isna(val): return val
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
                if col != tarih_kolonu: df_tablo[col] = df_tablo[col].apply(lambda x: formatla(x, col))
            
            st.dataframe(df_tablo.style.apply(lambda row: ['background-color: #004d40; color: white; font-weight: bold'] * len(row) if row.get(tarih_kolonu) == 'TOPLAM' or row.iloc[0] == 'TOPLAM' else [''] * len(row), axis=1), use_container_width=True)
            
            st.divider()

            st.subheader("📈 Veri Trendleri")
            secilen_metrikler = st.multiselect("Metrikler:", sayisal_sutunlar.tolist(), default=sayisal_sutunlar.tolist()[:1] if len(sayisal_sutunlar) > 0 else None)
            if secilen_metrikler and tarih_kolonu:
                df_grafik = df.set_index(tarih_kolonu)
                st.line_chart(df_grafik[secilen_metrikler])
                
            st.divider()

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
                        st.markdown(f'<div style="background-color: #1e1e1e; padding: 25px; border-radius: 10px; border-left: 5px solid #004d40; color: #e0e0e0; line-height: 1.6; font-size: 16px;">{cevap.text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"AI Hatası: {e}")
