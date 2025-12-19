import streamlit as st
import pandas as pd
import plotly.express as px
import random
import json
import base64
import os
from datetime import datetime
from io import BytesIO
from PIL import Image

# --- VERİ YÖNETİMİ ---
FILES = {"sorular": "database.json", "denemeler": "denemeler.json", "kartlar": "kartlar.json", "kitaplar": "kitaplar.json", "konular": "konular.json"}

def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_data(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)

# Session State
for key, file in FILES.items():
    if key not in st.session_state: st.session_state[key] = load_data(file)

st.set_page_config(page_title="HACETTEPE YOLU v3.6", layout="wide")

# --- 1. GECE MODU & TEMA ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; }}
    .beytepe-card {{ background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://upload.wikimedia.org/wikipedia/tr/6/6d/Hacettepe_Logosu.png'); background-size: contain; background-repeat: no-repeat; background-position: center; height: 150px; border-radius: 20px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 24px; text-shadow: 2px 2px 4px #000; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🎓 HAC v3.6")
if st.sidebar.button("🌙/☀️ Mod Değiştir"): 
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["🏛️ Dashboard", "✅ Konu Takibi", "🚨 Kritik & Karalama", "📈 Net Analizi", "📚 Kitaplarım", "📥 Soru Ekle"]
choice = st.sidebar.radio("Menü", menu)

# --- 1. DASHBOARD (BEYTEPE MOTİVASYONU) ---
if choice == "🏛️ Dashboard":
    st.markdown('<div class="beytepe-card">HEDEF: HACETTEPE ÜNİVERSİTESİ</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    tyt_k = (datetime(2026, 6, 20) - datetime.now()).days
    ayt_k = (datetime(2026, 6, 21) - datetime.now()).days
    col1.metric("TYT 2026", f"{tyt_k} Gün")
    col2.metric("AYT 2026", f"{ayt_k} Gün")

    st.divider()
    st.subheader("📊 Kitap İlerleme Durumu")
    for k in st.session_state.kitaplar:
        yuzde = int((k['su_an'] / k['toplam']) * 100)
        st.write(f"{k['ad']} (%{yuzde})")
        st.progress(yuzde / 100)

# --- 2. KONU TAKİBİ (CHECKLIST) ---
elif choice == "✅ Konu Takibi":
    st.header("✅ Müfredat Checklist")
    konu_listesi = ["TYT Matematik", "TYT Türkçe", "AYT Matematik", "AYT Edebiyat"]
    secili_dal = st.selectbox("Ders Seç", konu_listesi)
    
    # Basit bir konu havuzu (Geliştirilebilir)
    konular = {"TYT Matematik": ["Sayılar", "Problemler", "Fonksiyonlar"], "TYT Türkçe": ["Paragraf", "Dil Bilgisi"]}
    
    for konu in konular.get(secili_dal, []):
        checked = st.checkbox(konu, key=f"c_{konu}")
        if checked: st.success(f"{konu} bitti! Beytepe'ye bir adım daha.")

# --- 3. KRİTİK & KARALAMA (S-PEN UYUMLU) ---
elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Zor Sorular & S-Pen Karalama")
    zorlar = [s for s in st.session_state.sorular if int(s.get('hac_puani', 0)) >= 8]
    
    if zorlar:
        for s in zorlar:
            with st.expander(f"🔥 {s['ders']} - Zorluk: {s['hac_puani']}"):
                col1, col2 = st.columns([1, 1])
                col1.image(f"data:image/png;base64,{s['resim']}", caption="Soru")
                col2.write("**Karalama & Çözüm Alanı**")
                # S-Pen için beyaz alan simülasyonu
                col2.markdown('<div style="background-color: white; height: 300px; border: 1px solid #ccc; border-radius: 10px;"></div>', unsafe_allow_html=True)
                st.write(f"**Notun:** {s['not']}")
    else:
        st.info("Henüz 'zor' (8+) olarak işaretlenmiş soru yok.")

# --- DİĞER MENÜLER ---
elif choice == "📈 Net Analizi":
    st.header("📈 Gelişim Grafiği")
    if st.session_state.denemeler:
        df = pd.DataFrame(st.session_state.denemeler)
        st.plotly_chart(px.line(df, x="tarih", y="toplam_net", markers=True))
    
elif choice == "📥 Soru Ekle":
    st.header("📸 Soru Kaydı")
    with st.form("s_f"):
        d = st.selectbox("Ders", ["Mat", "Ed", "Tar", "Coğ"])
        zorluk = st.slider("Zorluk (HAC Puanı)", 1, 10, 5)
        img_f = st.file_uploader("Soru Görseli")
        notum = st.text_area("Notun")
        if st.form_submit_button("Kaydet") and img_f:
            enc = base64.b64encode(img_f.read()).decode()
            st.session_state.sorular.append({"id": random.randint(1,999), "ders": d, "hac_puani": zorluk, "resim": enc, "not": notum})
            save_data(st.session_state.sorular, FILES["sorular"])
            st.rerun()
