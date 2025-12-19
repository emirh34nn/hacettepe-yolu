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

st.set_page_config(page_title="HACETTEPE YOLU v3.5.7", layout="wide")

# --- GECE MODU ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .flashcard {{ background-color: {card}; padding: 30px; border-radius: 20px; border: 2px solid #3B82F6; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); color: {txt}; font-size: 1.2rem; }}
    .game-box {{ background-color: {card}; padding: 25px; border-radius: 15px; border: 2px dashed #3B82F6; text-align: center; }}
    </style>""", unsafe_allow_html=True)

# --- MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.7")
if st.sidebar.button("🌙/☀️ Gece Modu"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "📈 YKS Net Analizörü", "🎭 Edebiyat Oyunu", "🌙 Gün Sonu Kritiği", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar", "🚨 Kritik Eksikler", "📚 Kitap Takibi"]
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
        col3.metric("Son Net", f"{st.session_state.denemeler[-1]['toplam_net']:.2f}")

    st.divider()
    if len(st.session_state.gunluk) >= 3:
        st.subheader("💡 Haftalık Özet")
        df_g = pd.DataFrame(st.session_state.gunluk)
        st.success(f"🔥 Bu hafta toplam **{df_g['saat'].sum()} saat** çalıştın. Beytepe seni bekliyor!")

# --- 2. YKS NET ANALİZÖRÜ ---
elif choice == "📈 YKS Net Analizörü":
    st.header("📊 Deneme Net Hesaplama & Takip")
    t1, t2 = st.tabs(["📥 Yeni Deneme Gir", "📈 Gelişim Grafiği"])
    
    with t1:
        with st.form("net_hesapla"):
            yayin = st.text_input("Yayın Adı", placeholder="Örn: 3D, Bilgi Sarmal")
            tur = st.radio("Sınav Türü", ["TYT", "AYT"], horizontal=True)
            dersler = ["Türkçe", "Sosyal", "Matematik", "Fen"] if tur == "TYT" else ["Matematik", "Edebiyat", "Tarih-1", "Coğrafya-1"]
            
            c1, c2, c3, c4 = st.columns(4)
            cols = [c1, c2, c3, c4]
            sonuclar = {}; toplam_net = 0
            
            for i, ders in enumerate(dersler):
                with cols[i]:
                    st.write(f"**{ders}**")
                    d = st.number_input("D", 0, 40, key=f"d_{ders}")
                    y = st.number_input("Y", 0, 40, key=f"y_{ders}")
                    n = d - (y * 0.25)
                    sonuclar[ders] = n; toplam_net += n
            
            if st.form_submit_button("Hesapla ve Kaydet"):
                st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m/%Y"), "yayin": yayin, "tur": tur, "toplam_net": toplam_net, "detay": sonuclar})
                save_json(st.session_state.denemeler, FILES["denemeler"]); st.success(f"Netin: {toplam_net:.2f}"); st.rerun()

    with t2:
        if st.session_state.denemeler:
            df = pd.DataFrame(st.session_state.denemeler)
            st.plotly_chart(px.line(df, x="tarih", y="toplam_net", color="tur", markers=True))
            st.dataframe(df[['tarih', 'yayin', 'tur', 'toplam_net']])

# --- 3. EDEBİYAT OYUNU ---
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
                st.session_state.game = {"e":dg['eser'], "d":dg['yazar'], "s":random.sample(list(set(diger)), min(3, len(set(diger))))+[dg['yazar']]}
                random.shuffle(st.session_state.game['s'])
            st.markdown(f'<div class="game-box"><h3>"{st.session_state.game["e"]}"</h3> yazarı kimdir?</div>', unsafe_allow_html=True)
            ans = st.radio("Seçenekler:", st.session_state.game['s'])
            if st.button("Onayla"):
                if ans == st.session_state.game['d']: st.balloons(); st.success("Doğru!"); del st.session_state.game; st.button("Sıradaki")
                else: st.error(f"Yanlış! Cevap: {st.session_state.game['d']}"); del st.session_state.game

# --- 4. GÜN SONU KRİTİĞİ ---
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

# --- 5. SORU EKLE ---
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
            img = Image.open(res).convert("RGB")
            buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
            enc = base64.b64encode(buf.getvalue()).decode()
            st.session_state.sorular.append({"id":random.randint(1,9999), "tur":tur, "ders":ders, "resim":enc, "cevap":cvp, "hac_puani":zor, "yayin":yay})
            save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

# --- 6. SORU ARŞİVİ ---
elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Arşiv")
    arama = st.text_input("Ders veya Yayın Ara...")
    for s in reversed(st.session_state.sorular):
        if arama.lower() in s['ders'].lower() or arama.lower() in s.get('yayin','').lower():
            with st.expander(f"{s['tur']} {s['ders']} | {s.get('yayin','')}"):
                st.image(f"data:image/png;base64,{s['resim']}")
                st.write(f"Cevap: {s['cevap']}")
                if st.button("Sil", key=f"ds_{s['id']}"):
                    st.session_state.sorular.remove(s); save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

# --- 7. SÖZEL KARTLAR ---
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

# --- 8. KRİTİK EKSİKLER ---
elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Zor Sorular (8+)")
    for s in [i for i in st.session_state.sorular if int(i.get('hac_puani',0)) >= 8]:
        with st.expander(f"{s['ders']} | Zorluk: {s['hac_puani']}"):
            st.image(f"data:image/png;base64,{s['resim']}")

# --- 9. KİTAP TAKİBİ ---
elif choice == "📚 Kitap Takibi":
    st.header("📚 Kitap Takibi")
    with st.form("kitap_ekle_f", clear_on_submit=True):
        ad = st.text_input("Kitap Adı"); toplam = st.number_input("Toplam Sayfa", 1, 1000, 200)
        if st.form_submit_button("Yeni Kitap Ekle"):
            st.session_state.kitaplar.append({"id":random.randint(1,9999), "ad":ad, "toplam":toplam, "su_an":0})
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
    st.divider()
    for i, k in enumerate(st.session_state.kitaplar):
        yeni = st.slider(f"{k['ad']}", 0, k['toplam'], k['su_an'], key=f"sl_{k['id']}")
        c1, c2 = st.columns(2)
        if c1.button("Güncelle", key=f"gn_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
        if c2.button("Sil", key=f"ksil_{k['id']}"):
            st.session_state.kitaplar.pop(i); save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
