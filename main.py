import streamlit as st
import pandas as pd
import plotly.express as px
import random
import json
import base64
import os
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image

# --- DOSYA YÖNETİMİ ---
FILES = {
    "sorular": "database.json", 
    "denemeler": "denemeler.json", 
    "kartlar": "kartlar.json", 
    "kitaplar": "kitaplar.json",
    "gunluk": "gunluk_kayitlar.json"
}

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_json(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)

# Session State Yükleme
for key, file in FILES.items():
    if key not in st.session_state: st.session_state[key] = load_json(file)

st.set_page_config(page_title="HACETTEPE YOLU v3.5.2", layout="wide")

# --- GECE MODU AYARLARI ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .flashcard {{ background-color: {card}; padding: 30px; border-radius: 20px; border: 2px solid #3B82F6; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); color: {txt}; font-size: 1.2rem; }}
    .stExpander {{ background-color: {card} !important; border-radius: 10px; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.2")
if st.sidebar.button("🌙/☀️ Gece Modu"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "🌙 Gün Sonu Kritiği", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar", "📈 Net Analizi", "🚨 Kritik Eksikler", "📚 Kitap İlerleme"]
choice = st.sidebar.radio("Menü", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("🏛️ Strateji Merkezi")
    tyt_h = datetime(2026, 6, 20, 10, 15)
    fark = tyt_h - datetime.now()
    st.info(f"🚀 TYT 2026 Hedefine: **{fark.days} Gün {fark.seconds//3600} Saat** Kaldı!")

    if len(st.session_state.gunluk) >= 3:
        st.subheader("💡 Haftalık Akıllı Analiz")
        df_g = pd.DataFrame(st.session_state.gunluk)
        df_g['tarih'] = pd.to_datetime(df_g['tarih'])
        son_hafta = df_g[df_g['tarih'] > (datetime.now() - timedelta(days=7))]
        if not son_hafta.empty:
            en_cok_gun = son_hafta.loc[son_hafta['saat'].idxmax()]['tarih'].strftime('%A')
            st.success(f"🔥 Bu hafta toplam **{son_hafta['saat'].sum()} saat** çalıştın. En yoğun günün: **{en_cok_gun}**.")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Soru", len(st.session_state.sorular))
    c2.metric("Hafıza Kartı", len(st.session_state.kartlar))
    if st.session_state.denemeler:
        c3.metric("Son Net", f"{st.session_state.denemeler[-1]['toplam_net']}")

# --- 2. GÜN SONU KRİTİĞİ ---
elif choice == "🌙 Gün Sonu Kritiği":
    st.header("🌙 Gün Sonu Değerlendirmesi")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("gunluk_f"):
            tarih = st.date_input("Tarih", datetime.now())
            saat = st.number_input("Çalışma Saati", 0.0, 24.0, 5.0)
            verim = st.slider("Verim (1-10)", 1, 10, 7)
            notlar = st.text_area("Özet")
            if st.form_submit_button("Mühürle"):
                st.session_state.gunluk = [k for k in st.session_state.gunluk if k['tarih'] != tarih.strftime("%Y-%m-%d")]
                st.session_state.gunluk.append({"tarih": tarih.strftime("%Y-%m-%d"), "saat": saat, "verim": verim, "not": notlar})
                save_json(st.session_state.gunluk, FILES["gunluk"]); st.rerun()
    with col2:
        if st.session_state.gunluk:
            st.table(pd.DataFrame(st.session_state.gunluk).sort_values("tarih", ascending=False).head(7))

# --- 3. SORU EKLE (GÜNCEL) ---
# --- 📥 SORU EKLE (HATA DÜZELTİLMİŞ) ---
elif choice == "📥 Soru Ekle":
    st.header("📸 Yeni Soru Kaydı")
    with st.form("yukle_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tur = st.radio("Sınav Türü", ["TYT", "AYT"], horizontal=True)
            if tur == "TYT": d_list = ["Türkçe", "Matematik", "Geometri", "Tarih", "Coğrafya", "Felsefe - Din", "Fen Bilimleri"]
            else: d_list = ["Matematik", "Edebiyat", "Geometri", "Tarih", "Coğrafya", "Felsefe", "Fizik", "Kimya", "Biyoloji"]
            ders = st.selectbox("Ders", d_list); yayin = st.text_input("Yayın")
        with c2:
            zor = st.slider("HAC Zorluk", 1, 10, 5)
            cevap = st.text_input("Cevap (Şık/Metin)")
            res = st.file_uploader("Soru Görseli", type=["png", "jpg", "jpeg"]) # Sadece resim formatları
        
        notum = st.text_area("Analiz Notu")
        submit = st.form_submit_button("Sisteme Mühürle")
        
        if submit:
            if res is not None: # Resim yüklenmiş mi kontrol et
                try:
                    img = Image.open(res).convert("RGB")
                    buf = BytesIO()
                    img.save(buf, format="JPEG", quality=50)
                    enc = base64.b64encode(buf.getvalue()).decode()
                    
                    st.session_state.sorular.append({
                        "id": random.randint(1,9999), 
                        "tur": tur, "ders": ders, "yayin": yayin, 
                        "resim": enc, "cevap": cevap, 
                        "hac_puani": zor, "not": notum
                    })
                    save_json(st.session_state.sorular, FILES["sorular"])
                    st.success(f"Mühürlendi! {ders} arşive eklendi.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Resim işlenirken hata oluştu: {e}")
            else:
                st.warning("⚠️ Lütfen önce bir soru fotoğrafı yükle kanka!")

# --- 4. SORU ARŞİVİ (GERİ GELDİ) ---
elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Soru Arşivin")
    filtre = st.text_input("Ders veya Yayın Ara...")
    for i, s in enumerate(reversed(st.session_state.sorular)):
        if filtre.lower() in s['ders'].lower() or filtre.lower() in s['yayin'].lower():
            with st.expander(f"📌 {s.get('tur','TYT')} {s['ders']} | {s['yayin']}"):
                col_a1, col_a2 = st.columns([2, 1])
                with col_a1: st.image(f"data:image/png;base64,{s['resim']}")
                with col_a2:
                    st.write(f"**Zorluk:** {s.get('hac_puani',5)}/10")
                    st.write(f"**Not:** {s['not']}")
                    if st.button("👁️ Cevabı Gör", key=f"ans_{s['id']}"): st.success(f"Cevap: {s['cevap']}")
                    if st.button("🗑️ Sil", key=f"del_{s['id']}"):
                        st.session_state.sorular.pop(len(st.session_state.sorular)-1-i)
                        save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

# --- 5. SÖZEL KARTLAR (GÜZELLEŞTİRİLDİ) ---
elif choice == "🗂️ Sözel Kartlar":
    st.header("🗂️ Hafıza Kartları")
    with st.form("k_f", clear_on_submit=True):
        c1, c2 = st.columns(2)
        on = c1.text_input("Kavram/Soru"); arka = c2.text_area("Cevap")
        if st.form_submit_button("Mühürle"):
            st.session_state.kartlar.append({"id": random.randint(1,999), "on": on, "arka": arka})
            save_json(st.session_state.kartlar, FILES["kartlar"]); st.rerun()
    
    st.divider()
    for i, k in enumerate(reversed(st.session_state.kartlar)):
        st.markdown(f'<div class="flashcard"><b>{k["on"]}</b></div>', unsafe_allow_html=True)
        c_k1, c_k2 = st.columns(2)
        if c_k1.button("🔄 Çevir / Cevabı Gör", key=f"f_{k['id']}"): st.info(f"**Cevap:** {k['arka']}")
        if c_k2.button("🗑️ Kartı Sil", key=f"kd_{k['id']}"):
            st.session_state.kartlar.pop(len(st.session_state.kartlar)-1-i)
            save_json(st.session_state.kartlar, FILES["kartlar"]); st.rerun()

# --- DİĞERLERİ (NET ANALİZİ, KRİTİK, KİTAP) ---
elif choice == "📈 Net Analizi":
    st.header("📈 Net Analizi")
    if st.session_state.denemeler:
        df_d = pd.DataFrame(st.session_state.denemeler)
        st.plotly_chart(px.line(df_d, x="tarih", y="toplam_net", markers=True))
    with st.form("d_f"):
        ad = st.text_input("Yayın"); net = st.number_input("Net", 0.0, 120.0)
        if st.form_submit_button("Ekle"):
            st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m"), "toplam_net": net})
            save_json(st.session_state.denemeler, FILES["denemeler"]); st.rerun()

elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Zor Sorular (8+)")
    zorlar = [s for s in st.session_state.sorular if int(s.get('hac_puani', 0)) >= 8]
    for s in zorlar:
        with st.expander(f"🔥 {s['ders']} - {s['yayin']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            st.write(f"Cevap: {s['cevap']} | Not: {s['not']}")

elif choice == "📚 Kitap İlerleme":
    st.header("📚 Kitap Takibi")
    with st.form("kit_f"):
        ad = st.text_input("Kitap Adı"); top = st.number_input("Toplam Sayfa", 1)
        if st.form_submit_button("Ekle"):
            st.session_state.kitaplar.append({"id": random.randint(1,999), "ad": ad, "toplam": top, "su_an": 0})
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
    for i, kit in enumerate(st.session_state.kitaplar):
        yeni = st.slider(f"{kit['ad']}", 0, kit['toplam'], kit['su_an'], key=f"s_{kit['id']}")
        if st.button("Güncelle", key=f"up_{kit['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()

