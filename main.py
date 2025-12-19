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

st.set_page_config(page_title="HACETTEPE YOLU v3.5.9", layout="wide")

# --- GECE MODU VE GÖRSEL STİLLER ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; color: {txt} !important; }}
    .flashcard {{ background-color: {card}; padding: 30px; border-radius: 20px; border: 2px solid #3B82F6; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); color: {txt}; font-size: 1.2rem; }}
    .game-box {{ background-color: {card}; padding: 25px; border-radius: 15px; border: 2px dashed #3B82F6; text-align: center; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.9")
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

# --- 2. YKS NET ANALİZÖRÜ (v3.5.7 Stabil Yapı) ---
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

# --- 4. GÜN SONU KRİTİĞİ (YENİ ALGORİTMA) ---
elif choice == "🌙 Gün Sonu Kritiği":
    bugun = date.today()
    aylar_tr = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    tarih_str = f"{bugun.day} {aylar_tr[bugun.month]} {bugun.year}"
    
    st.header("🌙 Gün Sonu Değerlendirmesi")
    st.info(f"📅 Sistem Tarihi: **{tarih_str}**")

    col1, col2 = st.columns(2)
    with col1:
        with st.form("gunluk_form", clear_on_submit=True):
            secilen_tarih = st.date_input("Kritik Tarihi", value=bugun, max_value=bugun) # Gelecek engelli
            saat = st.number_input("Bugün Kaç Saat Çalıştın?", 0.0, 24.0, 5.0)
            verim = st.slider("Verim Puanın (1-10)", 1, 10, 7)
            st.write("---")
            st.write("🎯 **EA Branş Dağılımı (Saat)**")
            c_ea1, c_ea2 = st.columns(2)
            mat_s = c_ea1.number_input("Matematik", 0.0, 15.0, 0.0)
            edeb_s = c_ea2.number_input("Edebiyat", 0.0, 15.0, 0.0)
            notlar = st.text_area("Günün Özeti")
            
            if st.form_submit_button("Sisteme İşle"):
                yeni_kayit = {"tarih": str(secilen_tarih), "saat": saat, "verim": verim, "dagilim": {"Mat": mat_s, "Ed": edeb_s}, "not": notlar}
                st.session_state.gunluk = [k for k in st.session_state.gunluk if k['tarih'] != str(secilen_tarih)]
                st.session_state.gunluk.append(yeni_kayit)
                save_json(st.session_state.gunluk, FILES["gunluk"])
                st.balloons(); st.success("Mühürlendi!"); st.rerun()
    with col2:
        if st.session_state.gunluk:
            df_g = pd.DataFrame(st.session_state.gunluk).sort_values(by="tarih", ascending=False)
            st.table(df_g.head(5))

# --- DİĞER BÖLÜMLER (EKSİKSİZ) ---
elif choice == "📥 Soru Ekle":
    st.header("📸 Soru Kaydı")
    with st.form("sr_e", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tur = st.radio("Sınav", ["TYT", "AYT"], horizontal=True)
            ders = st.selectbox("Ders", ["Matematik", "Geometri", "Türkçe", "Edebiyat", "Tarih", "Coğrafya", "Felsefe-Din", "Fen"])
            yay = st.text_input("Yayın")
        with c2:
            zor = st.slider("HAC Zorluk", 1, 10, 5)
            res = st.file_uploader("Görsel", type=["png","jpg","jpeg"])
            cvp = st.text_input("Cevap")
        if st.form_submit_button("Mühürle") and res:
            try:
                img = Image.open(res).convert("RGB")
                buf = BytesIO(); img.save(buf, format="JPEG", quality=50)
                enc = base64.b64encode(buf.getvalue()).decode()
                st.session_state.sorular.append({"id":random.randint(1,9999), "tur":tur, "ders":ders, "resim":enc, "cevap":cvp, "hac_puani":zor, "yayin":yay})
                save_json(st.session_state.sorular, FILES["sorular"]); st.success("Mühürlendi!"); st.rerun()
            except: st.error("Hata!")

elif choice == "🔍 Soru Arşivi":
    st.header("🔍 Arşiv")
    ara = st.text_input("Ders veya Yayın Ara...")
    for s in reversed(st.session_state.sorular):
        if ara.lower() in s['ders'].lower() or ara.lower() in s.get('yayin','').lower():
            with st.expander(f"{s['tur']} {s['ders']} | {s.get('yayin','')}"):
                st.image(f"data:image/png;base64,{s['resim']}")
                if st.button("Sil", key=f"ds_{s['id']}"):
                    st.session_state.sorular.remove(s); save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

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

elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Zor Sorular (8+)")
    for s in [i for i in st.session_state.sorular if int(i.get('hac_puani',0)) >= 8]:
        with st.expander(f"{s['ders']} | Zorluk: {s['hac_puani']}"):
            st.image(f"data:image/png;base64,{s['resim']}")

elif choice == "📚 Kitap Takibi":
    st.header("📚 Kitap Takibi")
    with st.form("kit_e"):
        ad = st.text_input("Kitap"); top = st.number_input("Sayfa", 1)
        if st.form_submit_button("Ekle"):
            st.session_state.kitaplar.append({"id":random.randint(1,9999), "ad":ad, "toplam":top, "su_an":0})
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
    st.divider()
    for i, k in enumerate(st.session_state.kitaplar):
        yeni = st.slider(k['ad'], 0, k['toplam'], k['su_an'], key=f"sl_{k['id']}")
        if st.button("Güncelle", key=f"gn_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
