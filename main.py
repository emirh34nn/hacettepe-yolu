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

# Session State Başlatma
if 'sorular' not in st.session_state: st.session_state.sorular = load_json(DB_FILE)
if 'denemeler' not in st.session_state: st.session_state.denemeler = load_json(DENEME_FILE)
if 'kartlar' not in st.session_state: st.session_state.kartlar = load_json(KART_FILE)
if 'kitaplar' not in st.session_state: st.session_state.kitaplar = load_json(KITAP_FILE)

st.set_page_config(page_title="HACETTEPE YOLU v3.4", layout="wide")

# --- UI TASARIMI ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .flashcard { background-color: #FFFFFF; padding: 25px; border-radius: 15px; border: 2px solid #E2E8F0; text-align: center; margin-bottom: 10px; }
    .progress-card { background-color: white; padding: 15px; border-radius: 12px; border-bottom: 4px solid #3B82F6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.4")
menu = ["📊 Dashboard", "📚 Kitap İlerleme", "📥 Soru Ekle", "🔍 Soru Arşivi", "📝 Deneme Kaydı", "🗂️ Sözel Pratik Kartlar"]
choice = st.sidebar.radio("Bölüm Seç:", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("📈 Başarı & Strateji Merkezi")
    
    # --- YKS 2026 HASSAS SAYAÇ ---
    tyt_h, ayt_h = datetime(2026, 6, 20, 10, 15), datetime(2026, 6, 21, 10, 15)
    simdi = datetime.now()
    t_f, a_f = tyt_h - simdi, ayt_h - simdi

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info(f"📝 **TYT 2026:** {t_f.days} Gün {t_f.seconds//3600} Saat")
    with col_t2:
        st.warning(f"🎓 **AYT 2026:** {a_f.days} Gün {a_f.seconds//3600} Saat")

    st.divider()

    # --- KAYNAK İLERLEME GÖSTERGESİ ---
    st.subheader("📖 Kaynak İlerleme Durumum")
    if not st.session_state.kitaplar:
        st.write("Henüz kitap eklenmemiş.")
    else:
        for k in st.session_state.kitaplar:
            yuzde = int((k['su_an'] / k['toplam']) * 100)
            with st.container():
                st.markdown(f"""<div class="progress-card">
                <b>{k['brans']} - {k['ad']}</b><br>
                Sayfa: {k['su_an']} / {k['toplam']} (%{yuzde})
                </div>""", unsafe_allow_html=True)
                st.progress(yuzde / 100)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Soru", len(st.session_state.sorular))
    c2.metric("Hafıza Kartı", len(st.session_state.kartlar))
    if st.session_state.denemeler:
        c3.metric("Son Net", st.session_state.denemeler[-1]['toplam_net'])

# --- 2. KİTAP İLERLEME (YENİ SİSTEM) ---
elif choice == "📚 Kitap İlerleme":
    st.header("📚 Soru Bankası Takibi")
    
    with st.form("kitap_ekle"):
        st.subheader("Yeni Kitap Ekle")
        k_brans = st.selectbox("Branş", ["Türkçe", "Matematik", "Edebiyat", "Tarih", "Coğrafya", "Fizik", "Kimya", "Biyoloji", "Geometri"])
        k_ad = st.text_input("Kitap/Yayın Adı")
        k_toplam = st.number_input("Toplam Sayfa Sayısı", 1, 1000, 200)
        if st.form_submit_button("Kitabı Listeye Ekle"):
            st.session_state.kitaplar.append({"id": random.randint(1,9999), "brans": k_brans, "ad": k_ad, "toplam": k_toplam, "su_an": 0})
            save_json(st.session_state.kitaplar, KITAP_FILE)
            st.rerun()

    st.divider()
    st.subheader("İlerlemeyi Güncelle")
    for i, k in enumerate(st.session_state.kitaplar):
        with st.expander(f"{k['brans']} - {k['ad']} (%{int((k['su_an']/k['toplam'])*100)})"):
            yeni_sayfa = st.number_input(f"Kaçıncı sayfadasın? (Mevcut: {k['su_an']})", 0, k['toplam'], k['su_an'], key=f"kitap_{k['id']}")
            c_col1, c_col2 = st.columns(2)
            if c_col1.button("Güncelle", key=f"upd_{k['id']}"):
                st.session_state.kitaplar[i]['su_an'] = yeni_sayfa
                save_json(st.session_state.kitaplar, KITAP_FILE)
                st.success("İlerleme kaydedildi!")
                st.rerun()
            if c_col2.button("Kitabı Sil 🗑️", key=f"kdel_{k['id']}"):
                st.session_state.kitaplar.pop(i)
                save_json(st.session_state.kitaplar, KITAP_FILE)
                st.rerun()

# --- 3. SORU EKLE ---
elif choice == "📥 Soru Ekle":
    st.header("📸 Yeni Soru Kaydı")
    with st.form("yukle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            brans = st.selectbox("Branş", ["TYT", "AYT"])
            ders = st.selectbox("Ders", ["Türkçe", "Matematik", "Sosyal", "Fen", "Edebiyat", "Tarih", "Coğrafya"])
            yayin = st.text_input("Yayın")
        with col2:
            sayfa = st.number_input("Sayfa", 1); soru_no = st.number_input("Soru No", 1)
            dogru_sik = st.select_slider("Test Şıkkı", options=["A", "B", "C", "D", "E", "Açık Uçlu"])
            acik_cevap = st.text_input("Açık Uçlu Cevap (Varsa)")
        
        resim_f = st.file_uploader("Soru Görseli")
        notum = st.text_area("Yazılı Analiz Notun")
        if st.form_submit_button("Mühürle") and resim_f:
            img = Image.open(resim_f).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            encoded_img = base64.b64encode(buf.getvalue()).decode()
            final_cevap = acik_cevap if acik_cevap else dogru_sik
            st.session_state.sorular.append({"id": random.randint(1000,9999), "ders": ders, "yayin": yayin, "sayfa": sayfa, "soru_no": soru_no, "resim": encoded_img, "cevap": final_cevap, "not": notum})
            save_json(st.session_state.sorular, DB_FILE); st.success("Mühürlendi!"); st.rerun()

# --- 4. SORU ARŞİVİ ---
elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Soru Bankan")
    for i, s in enumerate(reversed(st.session_state.sorular)):
        idx = len(st.session_state.sorular) - 1 - i
        with st.expander(f"📌 {s['ders']} | {s['yayin']} | S.{s['sayfa']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            st.write(f"**Cevap:** {s['cevap']} | **Not:** {s['not']}")
            # SİLME ONAYI
            if st.button(f"🗑️ Soruyu Sil", key=f"del_{s['id']}"):
                st.session_state[f"confirm_{s['id']}"] = True
            if st.session_state.get(f"confirm_{s['id']}"):
                st.error("Bu soruyu silmek istediğine emin misin?")
                if st.button("EVET, SİL", key=f"yes_{s['id']}"):
                    st.session_state.sorular.pop(idx)
                    save_json(st.session_state.sorular, DB_FILE)
                    st.rerun()
                if st.button("HAYIR, VAZGEÇ", key=f"no_{s['id']}"):
                    del st.session_state[f"confirm_{s['id']}"]
                    st.rerun()

# --- 5. SÖZEL PRATİK KARTLAR ---
elif choice == "🗂️ Sözel Pratik Kartlar":
    st.header("🗂️ Hafıza Kartları")
    with st.form("k_form", clear_on_submit=True):
        k_ders = st.selectbox("Ders", ["Edebiyat", "Tarih", "Coğrafya", "Felsefe"])
        k_on = st.text_input("Kavram"); k_arka = st.text_area("Cevap")
        if st.form_submit_button("Mühürle"):
            st.session_state.kartlar.append({"id": random.randint(1,999), "ders": k_ders, "on": k_on, "arka": k_arka})
            save_json(st.session_state.kartlar, KART_FILE); st.rerun()
    
    for i, k in enumerate(reversed(st.session_state.kartlar)):
        idx = len(st.session_state.kartlar) - 1 - i
        st.markdown(f'<div class="flashcard"><b>{k["ders"]}</b><br>{k["on"]}</div>', unsafe_allow_html=True)
        col_k1, col_k2 = st.columns(2)
        if col_k1.button("🔄 Çevir", key=f"f_{k['id']}"): st.info(f"Cevap: {k['arka']}")
        
        # KART SİLME ONAYI
        if col_k2.button("🗑️ Sil", key=f"kdel_btn_{k['id']}"):
            st.session_state[f"k_confirm_{k['id']}"] = True
        if st.session_state.get(f"k_confirm_{k['id']}"):
            st.error("Bu kartı siliyorum?")
            if st.button("SİL", key=f"k_yes_{k['id']}"):
                st.session_state.kartlar.pop(idx)
                save_json(st.session_state.kartlar, KART_FILE)
                st.rerun()
            if st.button("İPTAL", key=f"k_no_{k['id']}"):
                del st.session_state[f"k_confirm_{k['id']}"]
                st.rerun()
        st.divider()

# --- 6. DENEME KAYDI ---
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
            save_json(st.session_state.denemeler, DENEME_FILE); st.rerun()
