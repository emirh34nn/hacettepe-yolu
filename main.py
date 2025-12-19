import streamlit as st
import pandas as pd
import plotly.express as px
import random
import json
import base64
import os
from datetime import datetime, date
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

# Gün sonu verilerini temizleme isteğin üzerine sıfırlama (İlk çalıştırmada tetiklenir)
if 'cleaned_v36' not in st.session_state:
    st.session_state.gunluk = []
    save_json([], FILES["gunluk"])
    st.session_state.cleaned_v36 = True

st.set_page_config(page_title="HACETTEPE YOLU v3.6.0", layout="wide")

# --- GECE MODU ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .game-box {{ background-color: {card}; padding: 25px; border-radius: 15px; border: 2px dashed #3B82F6; text-align: center; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.6.0")
if st.sidebar.button("🌙/☀️ Mod"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "📈 YKS Net Analizörü", "🎭 Edebiyat Oyunu", "🌙 Gün Sonu Kritiği", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar", "🚨 Kritik Eksikler", "📚 Kitap Takibi"]
choice = st.sidebar.radio("Menü Seç:", menu)

# --- GÜN SONU KRİTİĞİ (SADELEŞTİRİLMİŞ) ---
if choice == "🌙 Gün Sonu Kritiği":
    bugun = date.today()
    aylar_tr = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    tarih_str = f"{bugun.day} {aylar_tr[bugun.month]} {bugun.year}"
    
    st.header("🌙 Gün Sonu Değerlendirmesi")
    st.info(f"📅 Bugün: **{tarih_str}**")

    col1, col2 = st.columns(2)
    with col1:
        with st.form("gunluk_form", clear_on_submit=True):
            secilen_tarih = st.date_input("Kritik Tarihi", value=bugun, max_value=bugun)
            saat = st.number_input("Bugün Kaç Saat Çalıştın?", 0.0, 24.0, 5.0)
            verim = st.slider("Verim Puanın (1-10)", 1, 10, 7)
            notlar = st.text_area("Günün Özeti / Ne Öğrendin?")
            
            if st.form_submit_button("Günü Mühürle"):
                yeni_kayit = {"tarih": str(secilen_tarih), "saat": saat, "verim": verim, "not": notlar}
                # Aynı tarihe kayıt varsa güncelle
                st.session_state.gunluk = [k for k in st.session_state.gunluk if k['tarih'] != str(secilen_tarih)]
                st.session_state.gunluk.append(yeni_kayit)
                save_json(st.session_state.gunluk, FILES["gunluk"])
                st.success(f"✅ {secilen_tarih} mühürlendi!"); st.rerun()
    with col2:
        st.subheader("📋 Geçmiş Kayıtlar")
        if st.session_state.gunluk:
            df_gecmis = pd.DataFrame(st.session_state.gunluk).sort_values(by="tarih", ascending=False)
            st.dataframe(df_gecmis, use_container_width=True)
            if st.button("Tüm Verileri Sıfırla"):
                st.session_state.gunluk = []
                save_json([], FILES["gunluk"])
                st.rerun()

# --- 2. YKS NET ANALİZÖRÜ (v3.5.7 Stabil) ---
elif choice == "📈 YKS Net Analizörü":
    st.header("📊 Net Hesaplama")
    t1, t2 = st.tabs(["📥 Yeni Deneme Gir", "📈 Gelişim Grafiği"])
    with t1:
        with st.form("net_f"):
            yayin = st.text_input("Yayın Adı"); tur = st.radio("Tür", ["TYT", "AYT"], horizontal=True)
            dersler = ["Türkçe", "Sosyal", "Matematik", "Fen"] if tur == "TYT" else ["Matematik", "Edebiyat", "Tarih-1", "Coğrafya-1"]
            cols = st.columns(4); sonuclar = {}; toplam_net = 0
            for i, ders in enumerate(dersler):
                with cols[i]:
                    st.write(f"**{ders}**")
                    d = st.number_input("D", 0, 40, key=f"d_{ders}")
                    y = st.number_input("Y", 0, 40, key=f"y_{ders}")
                    n = d - (y * 0.25); sonuclar[ders] = n; toplam_net += n
            if st.form_submit_button("Kaydet"):
                st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m/%Y"), "yayin": yayin, "tur": tur, "toplam_net": toplam_net, "detay": sonuclar})
                save_json(st.session_state.denemeler, FILES["denemeler"]); st.rerun()
    with t2:
        if st.session_state.denemeler:
            st.plotly_chart(px.line(pd.DataFrame(st.session_state.denemeler), x="tarih", y="toplam_net", color="tur", markers=True))

# --- DASHBOARD VE DİĞERLERİ ---
elif choice == "📊 Dashboard":
    st.title("🏛️ Strateji Merkezi")
    tyt_h = datetime(2026, 6, 20, 10, 15); fark = tyt_h - datetime.now()
    st.info(f"🚀 TYT 2026'ya **{fark.days} Gün** Kaldı!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Soru", len(st.session_state.sorular))
    c2.metric("Eser Kaydı", len(st.session_state.edebiyat))
    if st.session_state.denemeler: c3.metric("Son Net", f"{st.session_state.denemeler[-1]['toplam_net']:.2f}")

elif choice == "🎭 Edebiyat Oyunu":
    st.header("🎭 Eser-Yazar Oyunu")
    if len(st.session_state.edebiyat) > 5:
        dg = random.choice(st.session_state.edebiyat)
        st.write(f"### {dg['eser']}?")
        ans = st.text_input("Yazar kim?")
        if st.button("Kontrol"):
            if ans.lower() == dg['yazar'].lower(): st.balloons(); st.success("Doğru!")
            else: st.error(f"Cevap: {dg['yazar']}")

elif choice == "📥 Soru Ekle":
    st.header("📸 Soru Kaydı")
    with st.form("sr_e", clear_on_submit=True):
        res = st.file_uploader("Görsel", type=["png","jpg","jpeg"])
        ders = st.selectbox("Ders", ["Matematik", "Geometri", "Türkçe", "Edebiyat", "Tarih", "Coğrafya"])
        zor = st.slider("Zorluk", 1, 10, 5)
        if st.form_submit_button("Mühürle") and res:
            img = Image.open(res).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            enc = base64.b64encode(buf.getvalue()).decode()
            st.session_state.sorular.append({"id":random.randint(1,9999), "ders":ders, "resim":enc, "hac_puani":zor})
            save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

elif choice == "🔍 Soru Arşivi":
    for s in reversed(st.session_state.sorular):
        with st.expander(f"{s['ders']} | Zorluk: {s['hac_puani']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            if st.button("Sil", key=f"s_{s['id']}"):
                st.session_state.sorular.remove(s); save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

elif choice == "🗂️ Sözel Kartlar":
    for k in st.session_state.kartlar:
        st.write(f"**{k['on']}**")
        if st.button("Cevap", key=f"c_{k['id']}"): st.info(k['arka'])

elif choice == "🚨 Kritik Eksikler":
    for s in [i for i in st.session_state.sorular if int(i.get('hac_puani',0)) >= 8]:
        st.image(f"data:image/png;base64,{s['resim']}")

elif choice == "📚 Kitap Takibi":
    for i, k in enumerate(st.session_state.kitaplar):
        yeni = st.slider(k['ad'], 0, k['toplam'], k['su_an'], key=f"sl_{k['id']}")
        if st.button("Güncelle", key=f"up_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
