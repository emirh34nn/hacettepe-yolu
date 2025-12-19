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

# --- DOSYA VE VERİ YÖNETİMİ ---
FILES = {
    "sorular": "database.json", 
    "denemeler": "denemeler.json", 
    "kartlar": "kartlar.json", 
    "kitaplar": "kitaplar.json",
    "gunluk": "gunluk_kayitlar.json",
    "edebiyat": "edebiyat_oyunu.json"
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

st.set_page_config(page_title="HACETTEPE YOLU v3.5.6", layout="wide")

# --- GECE MODU ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .flashcard {{ background-color: {card}; padding: 30px; border-radius: 20px; border: 2px solid #3B82F6; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); color: {txt}; font-size: 1.2rem; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.6")
if st.sidebar.button("🌙/☀️ Mod"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "🎭 Edebiyat Oyunu", "🌙 Gün Sonu Kritiği", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar", "📈 Net Analizi", "🚨 Kritik Eksikler", "📚 Kitap Takibi"]
choice = st.sidebar.radio("Menü Seç:", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("🏛️ Strateji Merkezi")
    tyt_h = datetime(2026, 6, 20, 10, 15)
    fark = tyt_h - datetime.now()
    st.info(f"🚀 TYT 2026 Hedefine: **{fark.days} Gün {fark.seconds//3600} Saat** Kaldı!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Soru", len(st.session_state.sorular))
    col2.metric("Eser Kaydı", len(st.session_state.edebiyat))
    if st.session_state.denemeler:
        col3.metric("Son Net", f"{st.session_state.denemeler[-1]['toplam_net']}")

# --- 2. EDEBİYAT OYUNU ---
elif choice == "🎭 Edebiyat Oyunu":
    st.header("🎭 Edebiyat Gladyatörü")
    t1, t2 = st.tabs(["🎮 Oyuna Başla", "📥 Eser Ekle"])
    with t2:
        with st.form("ed_ekle", clear_on_submit=True):
            y = st.text_input("Yazar"); e = st.text_input("Eser")
            tr = st.selectbox("Tür", ["Roman", "Şiir", "Tiyatro", "Anı", "Deneme"])
            if st.form_submit_button("Hafızaya Al"):
                st.session_state.edebiyat.append({"yazar":y, "eser":e, "tur":tr, "id":random.randint(1,999)})
                save_json(st.session_state.edebiyat, FILES["edebiyat"]); st.rerun()
    with t1:
        if len(st.session_state.edebiyat) < 10: st.warning("En az 10 eser lazım!")
        else:
            if 'game' not in st.session_state:
                dg = random.choice(st.session_state.edebiyat)
                diger = [i['yazar'] for i in st.session_state.edebiyat if i['yazar'] != dg['yazar']]
                st.session_state.game = {"e":dg['eser'], "d":dg['yazar'], "s":random.sample(list(set(diger)), 3)+[dg['yazar']]}
                random.shuffle(st.session_state.game['s'])
            st.write(f"### \"{st.session_state.game['e']}\" yazarı kimdir?")
            ans = st.radio("Seçenekler:", st.session_state.game['s'])
            if st.button("Onayla"):
                if ans == st.session_state.game['d']: st.balloons(); st.success("Doğru!"); del st.session_state.game; st.button("Sıradaki")
                else: st.error(f"Cevap: {st.session_state.game['d']}"); del st.session_state.game

# --- 3. GÜN SONU KRİTİĞİ ---
elif choice == "🌙 Gün Sonu Kritiği":
    st.header("🌙 Gün Sonu Değerlendirmesi")
    with st.form("gn_f"):
        t = st.date_input("Tarih", datetime.now())
        s = st.number_input("Saat", 0.0, 24.0, 5.0)
        v = st.slider("Verim", 1, 10, 7)
        if st.form_submit_button("Mühürle"):
            st.session_state.gunluk.append({"tarih":str(t), "saat":s, "verim":v})
            save_json(st.session_state.gunluk, FILES["gunluk"]); st.rerun()
    if st.session_state.gunluk: st.table(pd.DataFrame(st.session_state.gunluk).tail(5))

# --- 4. SORU EKLE ---
elif choice == "📥 Soru Ekle":
    st.header("📸 Soru Kaydı")
    with st.form("sr_e", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tur = st.radio("Tür", ["TYT", "AYT"], horizontal=True)
            ders = st.selectbox("Ders", ["Matematik", "Geometri", "Türkçe", "Edebiyat", "Tarih", "Coğrafya", "Felsefe-Din", "Fen"])
            yay = st.text_input("Yayın")
        with c2:
            zor = st.slider("Zorluk", 1, 10, 5)
            res = st.file_uploader("Görsel", type=["png","jpg","jpeg"])
            cvp = st.text_input("Cevap")
        if st.form_submit_button("Mühürle") and res:
            try:
                img = Image.open(res).convert("RGB")
                buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
                enc = base64.b64encode(buf.getvalue()).decode()
                st.session_state.sorular.append({"id":random.randint(1,9999), "tur":tur, "ders":ders, "resim":enc, "cevap":cvp, "hac_puani":zor, "yayin":yay})
                save_json(st.session_state.sorular, FILES["sorular"]); st.success("Mühürlendi!"); st.rerun()
            except: st.error("Resim yüklenemedi!")

# --- 5. SORU ARŞİVİ (ARAMA EKLENDİ) ---
elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Soru Arşivi")
    arama = st.text_input("Ders veya Yayın Ara...", placeholder="Örn: Matematik")
    for s in reversed(st.session_state.sorular):
        if arama.lower() in s['ders'].lower() or arama.lower() in s.get('yayin','').lower():
            with st.expander(f"{s['tur']} {s['ders']} | {s.get('yayin','')}"):
                st.image(f"data:image/png;base64,{s['resim']}")
                st.write(f"Cevap: {s['cevap']}")
                if st.button("Sil", key=f"ds_{s['id']}"):
                    st.session_state.sorular.remove(s); save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

# --- 6. SÖZEL KARTLAR ---
elif choice == "🗂️ Sözel Kartlar":
    st.header("🗂️ Kartlar")
    with st.form("kt_f", clear_on_submit=True):
        o, a = st.text_input("Soru"), st.text_area("Cevap")
        if st.form_submit_button("Ekle"):
            st.session_state.kartlar.append({"id":random.randint(1,999), "on":o, "arka":a})
            save_json(st.session_state.kartlar, FILES["kartlar"]); st.rerun()
    for k in reversed(st.session_state.kartlar):
        st.markdown(f'<div class="flashcard"><b>{k["on"]}</b></div>', unsafe_allow_html=True)
        if st.button("Cevabı Gör", key=f"cv_{k['id']}"): st.info(k['arka'])
        if st.button("Sil", key=f"ks_{k['id']}"):
            st.session_state.kartlar.remove(k); save_json(st.session_state.kartlar, FILES["kartlar"]); st.rerun()

# --- 7. NET ANALİZİ ---
elif choice == "📈 Net Analizi":
    st.header("📈 Net Analizi")
    if st.session_state.denemeler:
        df_d = pd.DataFrame(st.session_state.denemeler)
        st.plotly_chart(px.line(df_d, x="tarih", y="toplam_net", markers=True))
    with st.form("d_f"):
        n = st.number_input("Net", 0.0, 120.0)
        if st.form_submit_button("Ekle"):
            st.session_state.denemeler.append({"tarih":datetime.now().strftime("%d/%m"), "toplam_net":n})
            save_json(st.session_state.denemeler, FILES["denemeler"]); st.rerun()

# --- 8. KRİTİK EKSİKLER ---
elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Zor Sorular (8+)")
    for s in [i for i in st.session_state.sorular if int(i.get('hac_puani',0)) >= 8]:
        with st.expander(f"{s['ders']} | Zorluk: {s['hac_puani']}"):
            st.image(f"data:image/png;base64,{s['resim']}")

# --- 9. KİTAP TAKİBİ (EKLEME GERİ GELDİ) ---
elif choice == "📚 Kitap Takibi":
    st.header("📚 Kitap Takibi")
    with st.form("kitap_ekle_f", clear_on_submit=True):
        ad = st.text_input("Kitap Adı")
        toplam = st.number_input("Toplam Sayfa", 1, 1000, 200)
        if st.form_submit_button("Yeni Kitap Ekle"):
            st.session_state.kitaplar.append({"id":random.randint(1,9999), "ad":ad, "toplam":toplam, "su_an":0})
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
    st.divider()
    for i, k in enumerate(st.session_state.kitaplar):
        yeni = st.slider(f"{k['ad']} (Sayfa)", 0, k['toplam'], k['su_an'], key=f"sl_{k['id']}")
        c1, c2 = st.columns(2)
        if c1.button("Güncelle", key=f"gn_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
        if c2.button("Sil", key=f"ksil_{k['id']}"):
            st.session_state.kitaplar.pop(i)
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
