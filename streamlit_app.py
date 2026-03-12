import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="Yönetim Paneli", layout="wide")

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
if 'sheets_verileri' not in st.session_state: st.session_state.sheets_verileri = {"MANUKA": {}, "FRESH SCARFS": {}}
if 'aktif_veri' not in st.session_state: st.session_state.aktif_veri = None

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
            elif sifre == "": st.warning("Boş geçemezsin kiral, parolayı yaz.")
            else: st.error("Yanlış parola! Şansını zorlama :)")

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
                st.session_state.aktif_veri = None # Marka değişince veriyi sıfırla
                st.rerun()
            
        st.divider()
        
        # Üst Kısım: Yeni Sheets Ekleme
        with st.popover("➕ Yeni Rapor Bağla"):
            with st.form("yeni_sheets_formu", clear_on_submit=True):
                yeni_ad = st.text_input("Raporun Adı Ne Olsun?")
                yeni_id = st.text_input("Google Sheets ID'sini Yapıştır")
                kaydet = st.form_submit_button("Sisteme Ekle")
                if kaydet:
                    if yeni_ad and yeni_id:
                        st.session_state.sheets_verileri[aktif_marka][yeni_ad] = yeni_id
                        st.success(f"Süper! {yeni_ad} eklendi.")
                    else: st.error("İki alanı da doldurman lazım.")

        st.write("---")

        mevcut_raporlar = st.session_state.sheets_verileri[aktif_marka]
        if mevcut_raporlar:
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
                    
                    st.write("##")
                    if st.button("🚀 Verileri Ekrana Dök", use_container_width=True):
                        with st.spinner("Veriler toparlanıyor, biraz bekle..."):
                            df = veri_cek(secilen_id, secilen_sayfa)
                            
                            # --- TARİH FİLTRESİ ---
                            if 'Tarih' in df.columns:
                                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
                                df = df.dropna(subset=['Tarih'])
                                df['Tarih'] = df['Tarih'].dt.date
                                maske = (df['Tarih'] >= baslangic) & (df['Tarih'] <= bitis)
                                df = df.loc[maske].copy()
                                df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%d.%m.%Y')
                            
                            if not df.empty:
                                st.session_state.aktif_veri = df # Veriyi hafızaya alıyoruz ki grafik vs yenilenmesin
                            else:
                                st.warning("Seçtiğin tarihler arasında hiç veri yok kiral, tarihleri biraz esnet.")
                                st.session_state.aktif_veri = None
                                
                except Exception as e:
                    st.error(f"Kiral, arka planda patlayan asıl hata şu: {e}")
        else:
            st.info("Burası bomboş. Yukarıdan bir rapor bağlayarak başlayabilirsin.")

        # ==========================================
        # EĞER HAFIZADA VERİ VARSA EKRANA BAS (GRAFİK + AI)
        # ==========================================
        if st.session_state.aktif_veri is not None:
            df = st.session_state.aktif_veri.copy()
            
            st.success("Veriler başarıyla yüklendi kiral!")
            
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
            
            def satir_boya(row): return ['background-color: #004d40; color: white; font-weight: bold'] * len(row) if row['Tarih'] == 'TOPLAM' else [''] * len(row)
            
            st.dataframe(df_tablo.style.apply(satir_boya, axis=1), use_container_width=True)
            
            st.divider()

            # --- DİNAMİK GRAFİK ---
            st.subheader("📈 Veri Trendleri")
            secilen_metrikler = st.multiselect("Grafikte Görmek İstediğin Metrikleri Seç:", sayisal_sutunlar.tolist(), default=sayisal_sutunlar.tolist()[:2] if len(sayisal_sutunlar) > 1 else None)
            
            if secilen_metrikler:
                df_grafik = df.copy()
                df_grafik = df_grafik.set_index('Tarih')
                st.line_chart(df_grafik[secilen_metrikler])
                
            st.divider()

            # --- YAPAY ZEKA (GEMINI) BAĞLANTISI ---
            st.subheader("🤖 AI'dan Al Haberi")
            st.info("Ben Dijital Pazarlama Uzmanı manukAI. Bu verilere dair ne öğrenmek istersin?")
            
            soru_onerileri = [
                "✏️ Kendi sorumu yazacağım",
                "📊 CPA ve COS oranlarına göre reklam verimliliğini değerlendir.",
                "📉 En yüksek ve en düşük ciro yapılan günleri kıyasla, sence neden?",
                "💰 Bu verilere göre yarınki reklam bütçesini artırmalı mıyım, kısmalı mıyım?",
                "🎯 Sadık müşteri kazanımı (CRM) ve ciro artışı için bana 3 stratejik aksiyon öner."
            ]
            secilen_soru = st.selectbox("Bir soru seç veya kendin yaz:", soru_onerileri)
            
            if secilen_soru == "✏️ Kendi sorumu yazacağım":
                kullanici_sorusu = st.text_area("Ne sormak istersin?")
            else:
                kullanici_sorusu = secilen_soru
                
            if st.button("🧠 AI'dan Al Haberi", use_container_width=True):
                if not kullanici_sorusu or kullanici_sorusu == "✏️ Kendi sorumu yazacağım":
                    st.warning("Kiral, soruyu boş bıraktın!")
                else:
                    try:
                        # Streamlit Cloud'daki secrets bölümüne GEMINI_API_KEY eklemeyi unutma!
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        uygun_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                        model = genai.GenerativeModel(uygun_modeller[0])
                        
                        
                        # Uzman Promptu
                        prompt = f"""Sen çok tecrübeli bir E-ticaret ve Dijital Pazarlama uzmanısın. 
                        Aşağıdaki güncel rapor verilerini analiz et ve sorulan soruya net, gereksiz uzatmadan, stratejik ve profesyonel bir cevap ver.
                        
                        Kullanıcının Sorusu: {kullanici_sorusu}
                        
                        Veriler:
                        {df.to_string()}
                        """
                        
                        with st.spinner("Uzman analiz ediyor, az bekle..."):
                            cevap = model.generate_content(prompt)
                            st.success("İşte Analiz Sonucu:")
                            st.write(cevap.text)
                    except Exception as e:
                        st.error("AI ile bağlantı kuramadım kiral. Streamlit Secrets ayarlarında GEMINI_API_KEY tanımlı olduğundan emin ol! Hata detayı: " + str(e))
