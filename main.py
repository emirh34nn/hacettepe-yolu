import streamlit as st
import pandas as pd
import plotly.express as px
import random
import json
import base64
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

# --- VERİ YÖNETİMİ ---
DB_FILE = "database.json"
DENEME_FILE = "denemeler.json"
KART_FILE = "kartlar.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(data, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

# Verileri Yükle
if 'sorular' not in st.session_state: st.session_state.sorular = load_json(DB_FILE)
if 'denemeler' not in st.session_state: st.session_state.denemeler = load_json(DENEME_FILE)
if 'kartlar' not in st.session_state: st.session_state.kartlar = load_json(KART_FILE)

st.set_page_config(page_title="HACETTEPE YOLU v3.3", layout="wide")

# --- UI TASARIMI ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .stMetric { background-color: white; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; }
    .flashcard { background-color: #FFFFFF; padding: 25px; border-radius: 15px; border: 2px solid #E2E8F0; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .timer-box { background-color: #1E293B; color: #F1F5F9; padding: 20px; border-radius: 15px; text-align: center; margin-top: 10px; border: 2px solid #3B82F6; }
    </style>
    """, unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.3")
menu = ["📊 Dashboard", "📥 Soru Ekle", "🔍 Soru Arşivi", "📝 Deneme Kaydı", "🗂️ Sözel Pratik Kartlar", "🔥 HAC Günü 2.0"]
choice = st.sidebar.radio("Bölüm Seç:", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📈 Başarı & Odak Merkezi")
    
    # --- YKS 2026 SAYACI ---
    tyt_tarih = datetime(2026, 6, 13, 10, 15)
    ayt_tarih = datetime(2026, 6, 14, 10, 15)
    simdi = datetime.now()
    tyt_kalan = tyt_tarih - simdi
    ayt_kalan = ayt_tarih - simdi

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f'<div style="background-color: #E0F2FE; padding: 20px; border-radius: 15px; border-left: 5px solid #0369A1; text-align: center;"><h3 style="margin:0; color: #0369A1;">📝 TYT 2026</h3><h2 style="margin:10px 0;">{tyt_kalan.days} Gün</h2></div>', unsafe_allow_html=True)
    with col_t2:
        st.markdown(f'<div style="background-color: #FEF3C7; padding: 20px; border-radius: 15px; border-left: 5px solid #D97706; text-align: center;"><h3 style="margin:0; color: #D97706;">🎓 AYT 2026</h3><h2 style="margin:10px 0;">{ayt_kalan.days} Gün</h2></div>', unsafe_allow_html=True)

    st.divider()

    # --- ⏱️ KRONOMETRE & POMODORO SİSTEMİ ---
    st.subheader("⏱️ Odaklanma Aracı")
    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.write("🎯 **Pomodoro Modu** (25dk Odak + 5dk Mola)")
        p_button = st.button("🚀 Pomodoro Başlat")
        if p_button:
            progress_bar = st.progress(0)
            status_text = st.empty()
            for i in range(25 * 60):
                mins, secs = divmod((25 * 60) - i, 60)
                status_text.markdown(f"### ⏳ Kalan: {mins:02d}:{secs:02d}")
                progress_bar.progress((i + 1) / (25 * 60))
                time.sleep(1)
            st.balloons()
            st.success("Tebrikler! 25 dakikalık odaklanma bitti. Şimdi 5 dakika mola ver.")

    with col_p2:
        st.write("⏱️ **Serbest Kronometre**")
        if 'start_time' not in st.session_state: st.session_state.start_time = None
        
        c_start, c_stop = st.columns(2)
        if c_start.button("▶️ Başlat"):
            st.session_state.start_time = time.time()
        if c_stop.button("⏹️ Sıfırla"):
            st.session_state.start_time = None
            st.write("Kronometre sıfırlandı.")
        
        if st.session_state.start_time:
            timer_display = st.empty()
            while st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                mins, secs = divmod(int(elapsed), 60)
                timer_display.markdown(f"### 🕒 Geçen Süre: {mins:02d}:{secs:02d}")
                time.sleep(1)

    st.divider()
    
    # --- İSTATİSTİKLER ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Soru", len(st.session_state.sorular))
    c2.metric("Hafıza Kartı", len(st.session_state.kartlar))
    if st.session_state.denemeler:
        df_d = pd.DataFrame(st.session_state.denemeler)
        c3.metric("Son Net", df_d.iloc[-1]['toplam_net'])
    else:
        c3.metric("Son Net", "0.0")

# --- 2. SORU EKLE ---
elif choice == "📥 Soru Ekle":
    st.header("📸 Yeni Soru Kaydı")
    with st.form("yukle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            brans = st.selectbox("Branş", ["TYT", "AYT"])
            ders_list = ["Türkçe", "Sosyal", "Matematik", "Fen"] if brans=="TYT" else ["Matematik", "Edebiyat", "Tarih", "Coğrafya"]
            ders = st.selectbox("Ders", ders_list); yayin = st.text_input("Yayın")
        with col2:
            sayfa = st.number_input("Sayfa", 1); soru_no = st.number_input("Soru No", 1)
            dogru_sik = st.select_slider("Cevap", options=["A", "B", "C", "D", "E", "Boş"])
            hac_puani = st.number_input("HAC Zorluk (1-10)", 1, 10, 5)
        
        resim_f = st.file_uploader("Soru Görseli")
        notum = st.text_area("Yazılı Analiz Notun")
        if st.form_submit_button("Sisteme Mühürle") and resim_f:
            img = Image.open(resim_f).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            encoded_img = base64.b64encode(buf.getvalue()).decode()
            tekrar_tarihi = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
            st.session_state.sorular.append({"id": random.randint(1000,9999), "ders": ders, "yayin": yayin, "sayfa": sayfa, "soru_no": soru_no, "resim": encoded_img, "cevap": dogru_sik, "hac_puani": hac_puani, "not": notum, "tekrar_tarihi": tekrar_tarihi})
            save_json(st.session_state.sorular, DB_FILE); st.success("Soru Mühürlendi!"); st.rerun()

# --- 3. SORU ARŞİVİ ---
elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Soru Bankan")
    search = st.text_input("Ara (Ders/Yayın)")
    for i, s in enumerate(reversed(st.session_state.sorular)):
        if search.lower() in s['ders'].lower() or search.lower() in s['yayin'].lower():
            with st.expander(f"📌 {s['ders']} | {s['yayin']} | S.{s['sayfa']} No.{s['soru_no']}"):
                c1, c2 = st.columns([2, 1])
                with c1: st.image(f"data:image/png;base64,{s['resim']}")
                with c2:
                    st.write(f"**Not:** {s['not']}")
                    if st.button("👁️ Cevap", key=f"ans_{s['id']}"): st.success(f"Cevap: {s['cevap']}")
                    if st.button("🗑️ Sil", key=f"del_{s['id']}"):
                        st.session_state.sorular.pop(len(st.session_state.sorular)-1-i)
                        save_json(st.session_state.sorular, DB_FILE); st.rerun()

# --- 4. DENEME KAYDI ---
elif choice == "📝 Deneme Kaydı":
    st.header("📝 Net Takibi")
    with st.form("deneme_f"):
        d_ad = st.text_input("Yayın Adı"); d_tur = st.selectbox("Tür", ["TYT", "AYT"])
        branslar = ["Türkçe", "Sosyal", "Matematik", "Fen"] if d_tur == "TYT" else ["Matematik", "Edebiyat", "Tarih", "Coğrafya"]
        netler = {}; total = 0.0; cols = st.columns(4)
        for i, b in enumerate(branslar):
            with cols[i]:
                d = st.number_input(f"{b} D", 0, 40); y = st.number_input(f"{b} Y", 0, 40)
                n = d - (y*0.25); netler[b] = n; total += n
        if st.form_submit_button("Netleri İşle"):
            st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m"), "deneme_adi": d_ad, "toplam_net": total, "detay": netler})
            save_json(st.session_state.denemeler, DENEME_FILE); st.success(f"Net: {total}"); st.rerun()

# --- 5. SÖZEL PRATİK KARTLAR ---
elif choice == "🗂️ Sözel Pratik Kartlar":
    st.header("🗂️ Hafıza Kartları")
    with st.form("k_form", clear_on_submit=True):
        k_ders = st.selectbox("Ders", ["Edebiyat", "Tarih", "Coğrafya", "Felsefe"])
        k_on = st.text_input("Kavram"); k_arka = st.text_area("Cevap")
        if st.form_submit_button("Mühürle"):
            st.session_state.kartlar.append({"id": random.randint(1,999), "ders": k_ders, "on": k_on, "arka": k_arka})
            save_json(st.session_state.kartlar, KART_FILE); st.success("Kart eklendi!"); st.rerun()
    for k in reversed(st.session_state.kartlar):
        st.markdown(f'<div class="flashcard"><b>{k["ders"]}</b><br>{k["on"]}</div>', unsafe_allow_html=True)
        if st.button("🔄 Çevir", key=f"f_{k['id']}"): st.info(f"Cevap: {k['arka']}")
        st.divider()

# --- 6. HAC GÜNÜ 2.0 ---
elif choice == "🔥 HAC Günü 2.0":
    st.header("🎲 Haftalık Kamp")
    if len(st.session_state.sorular) < 5: st.warning("En az 5 soru biriktir!")
    else:
        if st.button("Rastgele 5 Soru"): st.session_state.hac_secimi = random.sample(st.session_state.sorular, 5)
        if 'hac_secimi' in st.session_state:
            for s in st.session_state.hac_secimi:
                st.image(f"data:image/png;base64,{s['resim']}")
                if st.button("Cevap", key=f"h_{s['id']}"): st.success(s['cevap'])
                st.divider()
