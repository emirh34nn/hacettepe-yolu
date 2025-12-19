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
    "gunluk": "gunluk_kayitlar.json",
    "edebiyat": "edebiyat_oyunu.json" # Yeni dosya
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

st.set_page_config(page_title="HACETTEPE YOLU v3.5.4", layout="wide")

# --- GECE MODU ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .game-card {{ background-color: {card}; padding: 30px; border-radius: 20px; border: 2px dashed #3B82F6; text-align: center; margin-bottom: 20px; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.4")
if st.sidebar.button("🌙/☀️ Gece Modu"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "🎭 Edebiyat Oyunu", "🌙 Gün Sonu Kritiği", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar", "📈 Net Analizi"]
choice = st.sidebar.radio("Menü", menu)

# --- 1. DASHBOARD --- (v3.5 ile aynı, stabil)
if choice == "📊 Dashboard":
    st.title("🏛️ Strateji Merkezi")
    tyt_h = datetime(2026, 6, 20, 10, 15)
    fark = tyt_h - datetime.now()
    st.info(f"🚀 TYT 2026 Hedefine: **{fark.days} Gün {fark.seconds//3600} Saat** Kaldı!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Soru", len(st.session_state.sorular))
    col2.metric("Ezber Verisi", len(st.session_state.edebiyat))
    if st.session_state.denemeler:
        col3.metric("Son Net", st.session_state.denemeler[-1]['toplam_net'])

# --- 2. EDEBİYAT OYUNU (YENİ MODÜL) ---
elif choice == "🎭 Edebiyat Oyunu":
    st.header("🎭 Eser-Yazar-Tür Gladyatörü")
    
    tab1, tab2 = st.tabs(["🎮 Oyuna Başla", "📥 Veri Ekle"])
    
    with tab2:
        st.subheader("Yeni Eser/Yazar Kaydı")
        with st.form("edebiyat_ekle", clear_on_submit=True):
            yazar = st.text_input("Yazar Adı")
            eser = st.text_input("Eser Adı")
            tur = st.selectbox("Tür", ["Roman", "Şiir", "Tiyatro", "Deneme", "Anı", "Öykü", "Gezi Yazısı"])
            if st.form_submit_button("Hafızaya Al"):
                if yazar and eser:
                    st.session_state.edebiyat.append({"yazar": yazar, "eser": eser, "tur": tur, "id": random.randint(1,99999)})
                    save_json(st.session_state.edebiyat, FILES["edebiyat"])
                    st.success(f"{eser} başarıyla kaydedildi!")
                else: st.error("Lütfen yazar ve eser adını boş bırakma.")
        
        st.write(f"📊 Mevcut Veri Sayısı: {len(st.session_state.edebiyat)}")
        if st.session_state.edebiyat:
            with st.expander("Kayıtlı Listeyi Gör"):
                st.table(pd.DataFrame(st.session_state.edebiyat)[['yazar', 'eser', 'tur']])

    with tab1:
        if len(st.session_state.edebiyat) < 10:
            st.warning(f"⚠️ Oyunun başlaması için en az 10 veri lazım. (Şu an: {len(st.session_state.edebiyat)})")
        else:
            if 'soru_hazir' not in st.session_state:
                # Rastgele bir doğru cevap seç
                dogru_cevap = random.choice(st.session_state.edebiyat)
                # Yanlış şıklar için diğer yazarları topla
                diger_yazarlar = list(set([item['yazar'] for item in st.session_state.edebiyat if item['yazar'] != dogru_cevap['yazar']]))
                yanlis_siklar = random.sample(diger_yazarlar, min(4, len(diger_yazarlar)))
                
                tum_siklar = yanlis_siklar + [dogru_cevap['yazar']]
                random.shuffle(tum_siklar)
                
                st.session_state.soru_hazir = {
                    "eser": dogru_cevap['eser'],
                    "dogru": dogru_cevap['yazar'],
                    "tur": dogru_cevap['tur'],
                    "siklar": tum_siklar
                }

            st.markdown(f"""<div class="game-card">
                <h3>"{st.session_state.soru_hazir['eser']}"</h3>
                <p>Bu eserin yazarı kimdir? (Tür: {st.session_state.soru_hazir['tur']})</p>
            </div>""", unsafe_allow_html=True)
            
            answer = st.radio("Şıklar:", st.session_state.soru_hazir['siklar'], index=None)
            
            if st.button("Cevabı Onayla"):
                if answer == st.session_state.soru_hazir['dogru']:
                    st.balloons()
                    st.success(f"DOĞRU! {st.session_state.soru_hazir['eser']} -> {st.session_state.soru_hazir['dogru']}")
                    del st.session_state.soru_hazir
                    st.button("Sıradaki Soru ➡️")
                else:
                    st.error(f"YANLIŞ! Doğru cevap: {st.session_state.soru_hazir['dogru']}")
                    if st.button("Tekrar Dene / Yeni Soru"):
                        del st.session_state.soru_hazir
                        st.rerun()

# --- DİĞER BÖLÜMLER (v3.5.2 İLE AYNI) ---
elif choice == "🌙 Gün Sonu Kritiği":
    st.header("🌙 Gün Sonu Değerlendirmesi")
    with st.form("gunluk_f"):
        tarih = st.date_input("Tarih", datetime.now())
        saat = st.number_input("Çalışma Saati", 0.0, 24.0, 5.0)
        verim = st.slider("Verim (1-10)", 1, 10, 7)
        if st.form_submit_button("Kaydet"):
            st.session_state.gunluk.append({"tarih": tarih.strftime("%Y-%m-%d"), "saat": saat, "verim": verim})
            save_json(st.session_state.gunluk, FILES["gunluk"]); st.rerun()

elif choice == "📥 Soru Ekle":
    # (v3.5.2'deki hatasız soru ekleme bloğu burada)
    st.header("📸 Yeni Soru Kaydı")
    with st.form("s_e", clear_on_submit=True):
        tur = st.radio("Sınav Türü", ["TYT", "AYT"], horizontal=True)
        ders = st.selectbox("Ders", ["Matematik", "Türkçe", "Edebiyat", "Tarih", "Coğrafya", "Geometri"])
        yayin = st.text_input("Yayın")
        zor = st.slider("HAC Zorluk", 1, 10, 5)
        cevap = st.text_input("Cevap")
        res = st.file_uploader("Görsel")
        if st.form_submit_button("Mühürle") and res:
            img = Image.open(res).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            enc = base64.b64encode(buf.getvalue()).decode()
            st.session_state.sorular.append({"id": random.randint(1,9999), "tur": tur, "ders": ders, "resim": enc, "cevap": cevap, "hac_puani": zor})
            save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

elif choice == "🔍 Soru Arşivi":
    for s in reversed(st.session_state.sorular):
        with st.expander(f"{s['ders']} | {s.get('yayin','')}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            if st.button("Sil", key=f"d_{s['id']}"):
                st.session_state.sorular.remove(s)
                save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

elif choice == "🗂️ Sözel Kartlar":
    # (v3.5.2'deki kart tasarımı)
    for k in st.session_state.kartlar:
        st.info(f"Soru: {k['on']}")
        if st.button("Cevap", key=f"c_{k['id']}"): st.write(k['arka'])

elif choice == "📈 Net Analizi":
    if st.session_state.denemeler:
        df = pd.DataFrame(st.session_state.denemeler)
        st.plotly_chart(px.line(df, x="tarih", y="toplam_net"))
