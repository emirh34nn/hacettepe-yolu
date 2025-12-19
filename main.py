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

# --- DOSYA VE VERİ YÖNETİMİ ---
DB_FILE = "database.json"
DENEME_FILE = "denemeler.json"
KART_FILE = "kartlar.json"
KITAP_FILE = "kitaplar.json"

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
if 'kitaplar' not in st.session_state: st.session_state.kitaplar = load_json(KITAP_FILE)

st.set_page_config(page_title="HACETTEPE YOLU v3.5", layout="wide")

# --- 1. GECE MODU AYARI ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False

def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# CSS Dokunuşları
bg_color = "#121212" if st.session_state.dark_mode else "#F8FAFC"
text_color = "#E0E0E0" if st.session_state.dark_mode else "#1E293B"
card_bg = "#1E1E1E" if st.session_state.dark_mode else "#FFFFFF"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .stMetric {{ background-color: {card_bg}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {text_color} !important; }}
    .flashcard {{ background-color: {card_bg}; padding: 25px; border-radius: 15px; border: 2px solid #3B82F6; text-align: center; margin-bottom: 10px; color: {text_color}; }}
    .stExpander {{ background-color: {card_bg} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5")
if st.sidebar.button("🌙/☀️ Gece Modu Değiştir"):
    toggle_dark_mode()
    st.rerun()

menu = ["📊 Dashboard", "📈 Net Analizi", "🚨 Kritik Eksikler", "📚 Kitap İlerleme", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar"]
choice = st.sidebar.radio("Bölüm Seç:", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📈 Strateji Merkezi")
    
    # YKS Sayaçları
    tyt_h, ayt_h = datetime(2026, 6, 20, 10, 15), datetime(2026, 6, 21, 10, 15)
    t_f, a_f = tyt_h - datetime.now(), ayt_h - datetime.now()
    
    c_s1, c_s2 = st.columns(2)
    c_s1.info(f"📝 TYT 2026: {t_f.days} GÜN KALDI")
    c_s2.warning(f"🎓 AYT 2026: {a_f.days} GÜN KALDI")

    st.divider()
    
    # Kaynak İlerleme
    st.subheader("📖 Kitap İlerleme Durumu")
    if st.session_state.kitaplar:
        for k in st.session_state.kitaplar:
            yuzde = int((k['su_an'] / k['toplam']) * 100)
            st.write(f"{k['brans']} - {k['ad']} (%{yuzde})")
            st.progress(yuzde / 100)
    else: st.write("Henüz kitap eklenmedi.")

# --- 2. NET ANALİZİ (GRAFİKLİ) ---
elif choice == "📈 Net Analizi":
    st.header("📈 Deneme Gelişim Grafiği")
    if len(st.session_state.denemeler) > 1:
        df = pd.DataFrame(st.session_state.denemeler)
        fig = px.line(df, x="tarih", y="toplam_net", title="Net Değişimi", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Grafik için en az 2 deneme kaydı lazım kanka.")
    
    # Deneme Giriş Formu
    with st.form("deneme_f"):
        d_ad = st.text_input("Deneme Adı"); d_tur = st.selectbox("Tür", ["TYT", "AYT"])
        c1, c2, c3, c4 = st.columns(4)
        n1 = c1.number_input("Ders 1 Net"); n2 = c2.number_input("Ders 2 Net")
        n3 = c3.number_input("Ders 3 Net"); n4 = c4.number_input("Ders 4 Net")
        if st.form_submit_button("Neti Kaydet"):
            st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m"), "toplam_net": n1+n2+n3+n4})
            save_json(st.session_state.denemeler, DENEME_FILE); st.rerun()

# --- 3. KRİTİK EKSİKLER (ZOR SORULAR) ---
elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Can Yakan Sorular (Zorluk 8+)")
    zor_sorular = [s for s in st.session_state.sorular if int(s.get('hac_puani', 0)) >= 8]
    
    if not zor_sorular:
        st.success("Şu an 8 puan ve üzeri zorlukta sorun yok. Harikasın!")
    else:
        for s in zor_sorular:
            with st.expander(f"🔥 {s['ders']} - {s['yayin']} (Zorluk: {s['hac_puani']})"):
                st.image(f"data:image/png;base64,{s['resim']}")
                st.write(f"**Cevap:** {s['cevap']} | **Notun:** {s['not']}")

# --- DİĞER MENÜLER (KİTAP, SORU EKLE, ARŞİV) ÖNCEKİYLE AYNI MANTIK ---
elif choice == "📚 Kitap İlerleme":
    st.header("📚 Kitap Takibi")
    with st.form("k_e"):
        brans = st.selectbox("Branş", ["Mat", "Türkçe", "Sosyal", "Fen", "Edebiyat"])
        ad = st.text_input("Kitap Adı"); top = st.number_input("Toplam Sayfa", 1); gonder = st.form_submit_button("Ekle")
        if gonder:
            st.session_state.kitaplar.append({"id": random.randint(1,99), "brans": brans, "ad": ad, "toplam": top, "su_an": 0})
            save_json(st.session_state.kitaplar, KITAP_FILE); st.rerun()
    
    for i, k in enumerate(st.session_state.kitaplar):
        st.write(f"**{k['ad']}**")
        yeni = st.slider("İlerleme", 0, k['toplam'], k['su_an'], key=f"s_{k['id']}")
        if st.button("Güncelle", key=f"b_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, KITAP_FILE); st.rerun()

elif choice == "📥 Soru Ekle":
    st.header("📥 Soru Kaydet")
    with st.form("s_e", clear_on_submit=True):
        d = st.selectbox("Ders", ["Mat", "Türkçe", "Edebiyat", "Tarih", "Coğrafya"])
        y = st.text_input("Yayın"); zorluk = st.slider("HAC Zorluk", 1, 10, 5)
        cevap = st.text_input("Cevap (Şık veya Metin)")
        img_f = st.file_uploader("Soru Fotoğrafı")
        notum = st.text_area("Analiz Notun")
        if st.form_submit_button("Mühürle") and img_f:
            img = Image.open(img_f).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            enc = base64.b64encode(buf.getvalue()).decode()
            st.session_state.sorular.append({"id": random.randint(1,9999), "ders": d, "yayin": y, "hac_puani": zorluk, "resim": enc, "cevap": cevap, "not": notum})
            save_json(st.session_state.sorular, DB_FILE); st.success("Kaydedildi!"); st.rerun()

elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Arşiv")
    for i, s in enumerate(reversed(st.session_state.sorular)):
        with st.expander(f"{s['ders']} - {s['yayin']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            st.write(f"Cevap: {s['cevap']}")
            if st.button("Sil", key=f"sd_{s['id']}"):
                st.session_state.sorular.pop(len(st.session_state.sorular)-1-i)
                save_json(st.session_state.sorular, DB_FILE); st.rerun()

elif choice == "🗂️ Sözel Kartlar":
    st.header("🗂️ Kartlar")
    with st.form("k_f"):
        on = st.text_input("Soru"); arka = st.text_area("Cevap")
        if st.form_submit_button("Ekle"):
            st.session_state.kartlar.append({"id": random.randint(1,999), "on": on, "arka": arka})
            save_json(st.session_state.kartlar, KART_FILE); st.rerun()
    for i, k in enumerate(st.session_state.kartlar):
        st.markdown(f'<div class="flashcard">{k["on"]}</div>', unsafe_allow_html=True)
        if st.button("Cevap Gör", key=f"cg_{k['id']}"): st.info(k['arka'])
        if st.button("Sil", key=f"ks_{k['id']}"):
            st.session_state.kartlar.pop(i)
            save_json(st.session_state.kartlar, KART_FILE); st.rerun()
