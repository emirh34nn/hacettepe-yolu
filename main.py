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
    "gunluk": "gunluk_kayitlar.json" # Yeni dosya
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

st.set_page_config(page_title="HACETTEPE YOLU v3.5.1", layout="wide")

# --- GECE MODU ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = False
bg, txt, card = ("#121212", "#E0E0E0", "#1E1E1E") if st.session_state.dark_mode else ("#F8FAFC", "#1E293B", "#FFFFFF")

st.markdown(f"""<style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    .stMetric {{ background-color: {card}; padding: 15px; border-radius: 15px; border-left: 5px solid #3B82F6; }}
    .status-box {{ background-color: {card}; padding: 20px; border-radius: 15px; border: 1px solid #3B82F6; margin-bottom: 10px; }}
    </style>""", unsafe_allow_html=True)

# --- YAN MENÜ ---
st.sidebar.title("🕊️ HAC v3.5.1")
if st.sidebar.button("🌙/☀️ Gece Modu"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

menu = ["📊 Dashboard", "🌙 Gün Sonu Kritiği", "📈 Net Analizi", "🚨 Kritik Eksikler", "📚 Kitap İlerleme", "📥 Soru Ekle", "🔍 Soru Arşivi", "🗂️ Sözel Kartlar"]
choice = st.sidebar.radio("Menü", menu)

# --- 1. DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("🏛️ Strateji Merkezi")
    
    # Geri Sayım
    tyt_h = datetime(2026, 6, 20, 10, 15)
    fark = tyt_h - datetime.now()
    st.info(f"🚀 TYT 2026 Hedefine: **{fark.days} Gün {fark.seconds//3600} Saat** Kaldı!")

    # Haftalık Özet Algoritması
    if len(st.session_state.gunluk) >= 3:
        st.subheader("💡 Haftalık Akıllı Analiz")
        df_g = pd.DataFrame(st.session_state.gunluk)
        df_g['tarih'] = pd.to_datetime(df_g['tarih'])
        son_hafta = df_g[df_g['tarih'] > (datetime.now() - timedelta(days=7))]
        
        if not son_hafta.empty:
            en_cok_gun = son_hafta.loc[son_hafta['saat'].idxmax()]['tarih'].strftime('%A')
            haftalik_toplam = son_hafta['saat'].sum()
            avg_verim = son_hafta['verim'].mean()
            
            st.success(f"🔥 Bu hafta toplam **{haftalik_toplam} saat** çalıştın. En verimli günün: **{en_cok_gun}**. Ortalama odaklanma puanın: **{avg_verim:.1f}/10**")
    
    st.divider()
    # Kitap İlerleme Özeti
    st.subheader("📖 Kitap Durumları")
    if st.session_state.kitaplar:
        for k in st.session_state.kitaplar:
            yuzde = int((k['su_an'] / k['toplam']) * 100)
            st.write(f"{k['ad']} (%{yuzde})")
            st.progress(yuzde / 100)

# --- 2. GÜN SONU KRİTİĞİ (YENİ BÖLÜM) ---
elif choice == "🌙 Gün Sonu Kritiği":
    st.header("🌙 Gün Sonu Değerlendirmesi")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("gunluk_form"):
            tarih = st.date_input("Kritik Tarihi", datetime.now())
            calisma_saati = st.number_input("Bugün Kaç Saat Çalıştın?", 0.0, 24.0, 5.0)
            verim_puani = st.slider("Verim Puanın (1-10)", 1, 10, 7)
            notlar = st.text_area("Bugün neler yaptın? (Kısa özet)")
            
            if st.form_submit_button("Günü Mühürle"):
                yeni_kayit = {
                    "tarih": tarih.strftime("%Y-%m-%d"),
                    "saat": calisma_saati,
                    "verim": verim_puani,
                    "not": notlar
                }
                # Aynı tarihe kayıt varsa güncelle, yoksa ekle
                st.session_state.gunluk = [k for k in st.session_state.gunluk if k['tarih'] != yeni_kayit['tarih']]
                st.session_state.gunluk.append(yeni_kayit)
                save_json(st.session_state.gunluk, FILES["gunluk"])
                st.balloons()
                st.success("Günün kaydedildi kanka, iyi dinlenmeler!")
                st.rerun()

    with col2:
        st.subheader("📅 Yakın Zaman Geçmişi")
        if st.session_state.gunluk:
            df_display = pd.DataFrame(st.session_state.gunluk).sort_values(by="tarih", ascending=False)
            st.table(df_display.head(7)) # Son 7 gün
        else:
            st.write("Henüz kayıtlı gün yok.")

# --- DİĞER FONKSİYONLAR (v3.5 İLE AYNI - BOZULMADI) ---
elif choice == "📈 Net Analizi":
    st.header("📈 Net Gelişimi")
    if len(st.session_state.denemeler) > 0:
        df_d = pd.DataFrame(st.session_state.denemeler)
        st.plotly_chart(px.line(df_d, x="tarih", y="toplam_net", title="Net Grafiğin"))
    
    with st.form("deneme_f"):
        ad = st.text_input("Yayın"); n = st.number_input("Net", 0.0, 120.0)
        if st.form_submit_button("Kaydet"):
            st.session_state.denemeler.append({"tarih": datetime.now().strftime("%d/%m"), "toplam_net": n})
            save_json(st.session_state.denemeler, FILES["denemeler"]); st.rerun()

elif choice == "🚨 Kritik Eksikler":
    st.header("🚨 Can Yakan Sorular (8+)")
    zorlar = [s for s in st.session_state.sorular if int(s.get('hac_puani', 0)) >= 8]
    for s in zorlar:
        with st.expander(f"{s['ders']} - Zorluk: {s['hac_puani']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            st.write(s['not'])

elif choice == "📚 Kitap İlerleme":
    st.header("📚 Kitap Takibi")
    with st.form("k_e"):
        ad = st.text_input("Kitap Adı"); top = st.number_input("Toplam Sayfa", 1)
        if st.form_submit_button("Ekle"):
            st.session_state.kitaplar.append({"id": random.randint(1,999), "ad": ad, "toplam": top, "su_an": 0})
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()
    for i, k in enumerate(st.session_state.kitaplar):
        st.write(f"**{k['ad']}**")
        yeni = st.slider("Sayfa", 0, k['toplam'], k['su_an'], key=f"k_{k['id']}")
        if st.button("Güncelle", key=f"b_{k['id']}"):
            st.session_state.kitaplar[i]['su_an'] = yeni
            save_json(st.session_state.kitaplar, FILES["kitaplar"]); st.rerun()

elif choice == "📥 Soru Ekle":
    st.header("📸 Yeni Soru Kaydı")
    with st.form("yukle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sinav_turu = st.radio("Sınav Türü", ["TYT", "AYT"], horizontal=True)
            
            # Seçime bağlı ders listesi
            if sinav_turu == "TYT":
                dersler = ["Türkçe", "Matematik", "Geometri", "Tarih", "Coğrafya", "Felsefe - Din", "Fen Bilimleri"]
            else:
                dersler = ["Matematik", "Edebiyat", "Geometri", "Tarih", "Coğrafya", "Felsefe", "Fizik", "Kimya", "Biyoloji"]
                
            ders = st.selectbox("Ders", dersler)
            yayin = st.text_input("Yayın")
        with col2:
            zorluk = st.slider("HAC Zorluk (1-10)", 1, 10, 5)
            cevap = st.text_input("Cevap (Şık veya Açık Uçlu)")
            resim_f = st.file_uploader("Soru Görseli")
        
        notum = st.text_area("Analiz Notun")
        submit = st.form_submit_button("Sisteme Mühürle")
        
        if submit and resim_f:
            img = Image.open(resim_f).convert("RGB")
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=50)
            encoded_img = base64.b64encode(buf.getvalue()).decode()
            
            st.session_state.sorular.append({
                "id": random.randint(1000,9999), 
                "tur": sinav_turu,
                "ders": ders, 
                "yayin": yayin, 
                "resim": encoded_img, 
                "cevap": cevap, 
                "hac_puani": zorluk, 
                "not": notum
            })
            save_json(st.session_state.sorular, FILES["sorular"])
            st.success(f"Bravo! {sinav_turu} {ders} sorusu mühürlendi. Beytepe'ye bir adım daha!")
            st.rerun()

elif choice == "🔍 Soru Arşivi":
    for i, s in enumerate(reversed(st.session_state.sorular)):
        with st.expander(f"{s['ders']}"):
            st.image(f"data:image/png;base64,{s['resim']}")
            if st.button("Sil", key=f"ds_{s['id']}"):
                st.session_state.sorular.pop(len(st.session_state.sorular)-1-i)
                save_json(st.session_state.sorular, FILES["sorular"]); st.rerun()

elif choice == "🗂️ Sözel Kartlar":
    with st.form("k_f"):
        on = st.text_input("Soru"); arka = st.text_area("Cevap")
        if st.form_submit_button("Ekle"):
            st.session_state.kartlar.append({"id": random.randint(1,999), "on": on, "arka": arka})
            save_json(st.session_state.kartlar, FILES["kartlar"]); st.rerun()
    for k in st.session_state.kartlar:
        st.write(f"**{k['on']}**")
        if st.button("Cevap", key=f"c_{k['id']}"): st.info(k['arka'])
