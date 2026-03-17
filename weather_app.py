import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from collections import Counter
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="WeatherXoja", page_icon="⛅",
    layout="wide", initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;700;800&display=swap');
* { font-family: 'Space Grotesk', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: #060b14; }
[data-testid="stSidebar"] { background: #0a1020 !important; border-right: 1px solid #1a2540; }
[data-testid="stSidebar"] * { color: #c8d8f0 !important; }
.weather-hero {
    background: linear-gradient(135deg, #0f2040 0%, #1a3a6e 50%, #0f2040 100%);
    border: 1px solid #1e3a6e; border-radius: 24px; padding: 36px;
    box-shadow: 0 0 60px rgba(30,90,200,0.15); margin-bottom: 24px;
}
.hero-city { font-family:'Syne',sans-serif; font-size:2.4rem; font-weight:800; color:#e8f0ff; margin:0; }
.hero-date { color:#6080b0; font-size:0.9rem; margin-top:4px; }
.hero-temp { font-family:'Syne',sans-serif; font-size:5rem; font-weight:800; color:#fff; line-height:1; }
.hero-desc { color:#7090c0; font-size:1rem; text-transform:capitalize; }
.sun-row { display:flex; gap:24px; margin-top:20px; background:rgba(255,255,255,0.03);
           border-radius:12px; padding:12px 20px; border:1px solid rgba(255,255,255,0.05); }
.sun-item { color:#7090c0; font-size:0.85rem; }
.sun-item b { color:#a0c0e8; }
.stat-card { background:#0a1525; border:1px solid #1a2a45; border-radius:18px; padding:22px;
             text-align:center; }
.stat-val { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:700; color:#d0e4ff; }
.stat-lbl { font-size:0.75rem; color:#4060a0; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }
.map-info { background:#0a1525; border:1px solid #1a2a45; border-radius:18px; padding:24px; }
.map-city { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:700; color:#e0eeff; }
.map-temp { font-family:'Syne',sans-serif; font-size:3.5rem; font-weight:800; color:#4080ff; line-height:1; margin:8px 0; }
.map-table td { padding:7px 0; color:#8090b0; font-size:0.9rem; border-bottom:1px solid #0e1d35; }
.map-table td:last-child { text-align:right; color:#c0d8f8; font-weight:500; }
.section-title { font-family:'Syne',sans-serif; font-size:1rem; font-weight:700; color:#4060a0;
                 text-transform:uppercase; letter-spacing:2px; margin:28px 0 16px;
                 border-left:3px solid #2a5fc0; padding-left:12px; }
.day-card { background:#0a1525; border:1px solid #1a2a45; border-radius:16px; padding:18px; text-align:center; }
.day-name { color:#4060a0; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; font-weight:600; }
.day-temps { color:#d0e4ff; font-weight:600; font-size:0.95rem; }
.day-meta { color:#304060; font-size:0.75rem; margin-top:6px; }
.click-hint { background:linear-gradient(135deg,#0a1525,#0e1d35); border:1px solid #1a2a45;
              border-radius:12px; padding:14px 20px; color:#6080b0; font-size:0.9rem;
              text-align:center; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

API_KEY = "ed304f5f1a412948049440ecc9bb0e3f"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# Session state
for k, v in [('map_weather', None), ('search_city', ''), ('do_search', False),
             ('view', '🏠 Asosiy'), ('map_lat', None), ('map_lon', None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── O'ZBEK/RUS → INGLIZ LUG'AT ──────────────────────────────────────────────
CITY_ALIASES = {
    "toshkent": "Tashkent", "samarqand": "Samarkand", "buxoro": "Bukhara",
    "andijon": "Andijan", "farg'ona": "Fergana", "fargona": "Fergana",
    "qarshi": "Karshi", "urganch": "Urgench", "termiz": "Termez",
    "navoiy": "Navoi", "nukus": "Nukus",
    "moskva": "Moscow", "moskow": "Moscow",
    "peterburg": "Saint Petersburg", "sankt-peterburg": "Saint Petersburg",
    "parij": "Paris", "pariz": "Paris",
    "nyu-york": "New York", "nyyork": "New York",
    "tokio": "Tokyo", "pekin": "Beijing", "rim": "Rome",
    "dubay": "Dubai", "stambul": "Istanbul", "qohira": "Cairo",
    "mumbay": "Mumbai", "sidney": "Sydney", "singapur": "Singapore",
    "toronto": "Toronto", "seul": "Seoul", "bangkok": "Bangkok",
}

@st.cache_data(ttl=600)
def geocode_city(city_name):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=3&appid={API_KEY}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
    except:
        pass
    return None, None

def resolve_city(city_input):
    """Lug'at + geocoding orqali shaharni aniqlash"""
    key = city_input.strip().lower()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    return city_input

# ── FUNKSIYALAR ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_weather(city=None, lat=None, lon=None):
    try:
        if city:
            resolved = resolve_city(city)
            lat_g, lon_g = geocode_city(resolved)
            if lat_g and lon_g:
                url = f"{BASE_URL}weather?lat={lat_g}&lon={lon_g}&appid={API_KEY}&units=metric"
            else:
                url = f"{BASE_URL}weather?q={resolved}&appid={API_KEY}&units=metric"
        else:
            url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return _parse(r.json())
    except:
        pass
    return None

@st.cache_data(ttl=600)
def fetch_forecast(city):
    try:
        resolved = resolve_city(city)
        lat_g, lon_g = geocode_city(resolved)
        if lat_g and lon_g:
            fc_url = f"{BASE_URL}forecast?lat={lat_g}&lon={lon_g}&appid={API_KEY}&units=metric"
        else:
            fc_url = f"{BASE_URL}forecast?q={resolved}&appid={API_KEY}&units=metric"
        r = requests.get(fc_url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            tz = d['city']['timezone']
            items = []
            for item in d['list']:
                lt = datetime.utcfromtimestamp(item['dt']) + pd.Timedelta(seconds=tz)
                items.append({
                    'datetime': lt, 'date': lt.strftime('%Y-%m-%d'),
                    'day_name': lt.strftime('%A'),
                    'temp': item['main']['temp'],
                    'temp_min': item['main']['temp_min'], 'temp_max': item['main']['temp_max'],
                    'humidity': item['main']['humidity'], 'wind_speed': item['wind']['speed'],
                    'description': item['weather'][0]['description'],
                    'pop': item.get('pop', 0) * 100
                })
            return items
    except:
        pass
    return None

def _parse(d):
    tz = d['timezone']
    lt = datetime.utcfromtimestamp(d['dt']) + pd.Timedelta(seconds=tz)
    sr = datetime.utcfromtimestamp(d['sys']['sunrise']) + pd.Timedelta(seconds=tz)
    ss = datetime.utcfromtimestamp(d['sys']['sunset']) + pd.Timedelta(seconds=tz)
    return {
        'city': d['name'], 'country': d['sys']['country'],
        'temp': d['main']['temp'], 'feels_like': d['main']['feels_like'],
        'temp_min': d['main']['temp_min'], 'temp_max': d['main']['temp_max'],
        'humidity': d['main']['humidity'], 'pressure': d['main']['pressure'],
        'wind_speed': d['wind']['speed'], 'wind_deg': d['wind'].get('deg', 0),
        'clouds': d['clouds']['all'], 'description': d['weather'][0]['description'],
        'local_time': lt.strftime('%H:%M'), 'local_date': lt.strftime('%d %B %Y'),
        'sunrise': sr.strftime('%H:%M'), 'sunset': ss.strftime('%H:%M'),
        'timezone': f"UTC{tz//3600:+d}",
        'lat': d['coord']['lat'], 'lon': d['coord']['lon']
    }

def daily_summary(forecast, days=5):
    if not forecast: return None
    daily = {}
    for item in forecast:
        d = item['date']
        if d not in daily:
            daily[d] = {'date': d, 'day_name': item['day_name'],
                        'temps': [], 'mins': [], 'maxs': [],
                        'hums': [], 'winds': [], 'descs': [], 'pop': []}
        daily[d]['temps'].append(item['temp'])
        daily[d]['mins'].append(item['temp_min'])
        daily[d]['maxs'].append(item['temp_max'])
        daily[d]['hums'].append(item['humidity'])
        daily[d]['winds'].append(item['wind_speed'])
        daily[d]['descs'].append(item['description'])
        daily[d]['pop'].append(item['pop'])
    out = []
    for d in daily.values():
        out.append({
            'date': d['date'], 'day_name': d['day_name'],
            'temp_avg': np.mean(d['temps']), 'temp_min': min(d['mins']),
            'temp_max': max(d['maxs']), 'hum_avg': np.mean(d['hums']),
            'wind_avg': np.mean(d['winds']),
            'desc': Counter(d['descs']).most_common(1)[0][0],
            'pop_max': max(d['pop'])
        })
    return out[:days]

def emo(desc):
    d = desc.lower()
    if 'clear' in d or 'sunny' in d: return '☀️'
    if 'cloud' in d: return '☁️'
    if 'rain' in d: return '🌧️'
    if 'snow' in d: return '❄️'
    if 'thunder' in d: return '⛈️'
    if 'mist' in d or 'fog' in d: return '🌫️'
    return '🌤️'

def wdir(deg):
    d = ['N','NE','E','SE','S','SW','W','NW']
    return d[int((deg+22.5)/45)%8]

def plotly_cfg():
    return dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(6,11,20,0.8)', font=dict(color='#6080b0'))

def show_hero(w):
    e = emo(w['description'])
    st.markdown(f"""
    <div class="weather-hero">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px;">
            <div>
                <div class="hero-city">📍 {w['city']}, {w['country']}</div>
                <div class="hero-date">{w['local_date']} · {w['local_time']} · {w['timezone']}</div>
                <div style="font-size:3.5rem;margin:16px 0 4px;">{e}</div>
                <div class="hero-desc">{w['description'].title()}</div>
            </div>
            <div style="text-align:right;">
                <div class="hero-temp">{w['temp']:.1f}°</div>
                <div style="color:#5070a0;font-size:0.9rem;">His: {w['feels_like']:.1f}°C</div>
                <div style="color:#3050a0;font-size:0.85rem;margin-top:4px;">
                    ↓{w['temp_min']:.1f}° &nbsp; ↑{w['temp_max']:.1f}°
                </div>
            </div>
        </div>
        <div class="sun-row">
            <span class="sun-item">🌅 Chiqish: <b>{w['sunrise']}</b></span>
            <span class="sun-item">🌇 Botish: <b>{w['sunset']}</b></span>
            <span class="sun-item">☁️ Bulut: <b>{w['clouds']}%</b></span>
            <span class="sun-item">🕐 <b>{w['local_time']}</b></span>
        </div>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,val,lbl in [
        (c1,"💧",f"{w['humidity']}%","Namlik"),
        (c2,"💨",f"{w['wind_speed']} m/s","Shamol · "+wdir(w['wind_deg'])),
        (c3,"🌀",f"{w['pressure']}","Bosim hPa"),
        (c4,"☁️",f"{w['clouds']}%","Bulutlilik"),
    ]:
        with col:
            st.markdown(f"""<div class="stat-card">
                <div style="font-size:1.8rem;">{icon}</div>
                <div class="stat-val">{val}</div>
                <div class="stat-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⛅ WeatherXoja")
    st.markdown("---")
    city_in = st.text_input("🔍 Shahar", placeholder="London, Toshkent, Tokyo...")
    if st.button("Qidirish", use_container_width=True, type="primary"):
        st.session_state.search_city = city_in
        st.session_state.do_search = True
        st.rerun()
    st.markdown("---")
    view = st.radio("Ko'rinish", ["🏠 Asosiy","📈 Soatlik","📅 Kunlik","🗺️ Interaktiv Xarita","🎯 Dashboard"])
    st.session_state.view = view
    st.markdown("---")
    st.caption("⛅ WeatherXoja\nReal vaqt ob-havo\nPowered by OpenWeatherMap")

st.markdown("# ⛅ WeatherXoja")

# ══════════════════════════════════════════════════════════════════════════════
# 🗺️ INTERAKTIV XARITA — FOLIUM
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "🗺️ Interaktiv Xarita":
    st.markdown('<div class="section-title">Interaktiv Xarita — Istalgan joyni bosing!</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="click-hint">
        🖱️ <b>Xaritada istalgan joyni bosing</b> → O'sha joyning ob-havosi chiqadi!<br>
        <small>Shaharni yaqinlashtirish uchun scroll yoki + tugmasidan foydalaning</small>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_info = st.columns([3, 2])

    with col_map:
        # Folium xarita yaratish
        center_lat = st.session_state.map_lat or 30.0
        center_lon = st.session_state.map_lon or 50.0
        zoom = 10 if st.session_state.map_lat else 3

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=None,
            scrollWheelZoom=True,
            dragging=True,
        )

        # OpenStreetMap — asosiy
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='🗺️ Oddiy xarita',
            attr='OpenStreetMap'
        ).add_to(m)

        # Satellite xarita — ESRI
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='🛰️ Satellite',
        ).add_to(m)

        # Google Maps uslubi
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='🌐 Google Maps',
        ).add_to(m)

        # Google Satellite
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='🌍 Google Satellite',
        ).add_to(m)

        # Qatlam tanlash tugmasi
        folium.LayerControl(position='topright').add_to(m)

        # Agar joy tanlangan bo'lsa marker qo'y
        if st.session_state.map_lat and st.session_state.map_weather:
            w = st.session_state.map_weather
            popup_html = f"""
            <div style="font-family:Arial;min-width:150px;">
                <b style="font-size:14px;">{w['city']}, {w['country']}</b><br>
                <span style="font-size:22px;font-weight:bold;color:#4080ff;">{w['temp']:.1f}°C</span><br>
                {w['description'].title()}<br>
                💧 {w['humidity']}% &nbsp; 💨 {w['wind_speed']} m/s
            </div>
            """
            folium.Marker(
                location=[st.session_state.map_lat, st.session_state.map_lon],
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"📍 {w['city']} — {w['temp']:.1f}°C",
                icon=folium.Icon(color='blue', icon='cloud', prefix='fa')
            ).add_to(m)

        # Xaritani ko'rsat va klik ma'lumotini ol
        map_data = st_folium(
            m,
            width="100%",
            height=520,
            returned_objects=["last_clicked"],
            key="main_map"
        )

        # Klik bo'lsa ob-havoni ol
        if map_data and map_data.get("last_clicked"):
            clicked = map_data["last_clicked"]
            lat = clicked["lat"]
            lon = clicked["lng"]

            if lat != st.session_state.map_lat or lon != st.session_state.map_lon:
                st.session_state.map_lat = lat
                st.session_state.map_lon = lon
                with st.spinner("⛅ Ob-havo yuklanmoqda..."):
                    st.session_state.map_weather = fetch_weather(lat=round(lat,4), lon=round(lon,4))
                st.rerun()

    with col_info:
        if st.session_state.map_weather:
            w = st.session_state.map_weather
            e = emo(w['description'])
            st.markdown(f"""
            <div class="map-info">
                <div style="font-size:3rem;margin-bottom:8px;">{e}</div>
                <div class="map-city">📍 {w['city']}, {w['country']}</div>
                <div class="map-temp">{w['temp']:.1f}°C</div>
                <div style="color:#4060a0;font-size:0.9rem;margin-bottom:20px;">
                    {w['description'].title()} · His: {w['feels_like']:.1f}°C
                </div>
                <table class="map-table" style="width:100%;">
                    <tr><td>💧 Namlik</td><td>{w['humidity']}%</td></tr>
                    <tr><td>💨 Shamol</td><td>{w['wind_speed']} m/s {wdir(w['wind_deg'])}</td></tr>
                    <tr><td>🌀 Bosim</td><td>{w['pressure']} hPa</td></tr>
                    <tr><td>☁️ Bulutlilik</td><td>{w['clouds']}%</td></tr>
                    <tr><td>🌡️ Min/Maks</td><td>{w['temp_min']:.1f}°/{w['temp_max']:.1f}°</td></tr>
                    <tr><td>🌅 Quyosh chiqishi</td><td>{w['sunrise']}</td></tr>
                    <tr><td>🌇 Quyosh botishi</td><td>{w['sunset']}</td></tr>
                    <tr><td>🕐 Mahalliy vaqt</td><td>{w['local_time']} ({w['timezone']})</td></tr>
                    <tr><td>📍 Koordinata</td><td>{w['lat']:.2f}°, {w['lon']:.2f}°</td></tr>
                </table>
                <div style="margin-top:14px;padding-top:14px;border-top:1px solid #1a2a45;
                            color:#304060;font-size:0.8rem;text-align:center;">
                    📅 {w['local_date']}
                </div>
            </div>""", unsafe_allow_html=True)

            # Radar
            cats = ['Harorat','Namlik','Shamol','Bosim','Bulut']
            vals = [max(0,min(100,(w['temp']+20)/50*100)), w['humidity'],
                    min(100,w['wind_speed']*10),
                    max(0,min(100,(w['pressure']-950)/100*100)), w['clouds']]
            fig_r = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(42,95,192,0.2)',
                line=dict(color='#2a5fc0', width=2)
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0,100],
                        gridcolor='rgba(255,255,255,0.05)',
                        tickfont=dict(color='#4060a0', size=8)),
                    angularaxis=dict(tickfont=dict(color='#6080b0', size=10)),
                    bgcolor='rgba(0,0,0,0)'
                ),
                height=280, paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40,r=40,t=10,b=10),
                template='plotly_dark'
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.markdown("""
            <div class="map-info" style="text-align:center;padding:80px 20px;">
                <div style="font-size:4rem;margin-bottom:16px;">🖱️</div>
                <div style="color:#4060a0;font-size:1.2rem;font-weight:600;">
                    Xaritada istalgan<br>joyni bosing!
                </div>
                <div style="color:#2a3a5a;font-size:0.85rem;margin-top:12px;">
                    Dunyoning istalgan nuqtasi<br>ob-havosi chiqadi
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# QIDIRUV SAHIFALARI
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.do_search or st.session_state.search_city:
    city = st.session_state.search_city
    if not city:
        st.warning("Shahar nomini kiriting!")
        st.stop()

    with st.spinner(f"⛅ {city} yuklanmoqda..."):
        w = fetch_weather(city=city)
        fc = fetch_forecast(city)
        ds = daily_summary(fc) if fc else None

    if not w:
        st.error(f"❌ **{city}** topilmadi! Inglizcha yozing.")
        st.stop()

    show_hero(w)
    view = st.session_state.view

    if view == "📈 Soatlik" and fc:
        st.markdown('<div class="section-title">24 Soatlik Prognoz</div>', unsafe_allow_html=True)
        df = pd.DataFrame(fc[:8])
        df['lbl'] = df['datetime'].apply(lambda x: x.strftime('%H:%M'))
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=('Harorat °C', 'Namlik % · Shamol m/s'),
                            vertical_spacing=0.18)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['temp'], mode='lines+markers', name='Harorat',
                                 line=dict(color='#4080ff', width=3),
                                 fill='tozeroy', fillcolor='rgba(64,128,255,0.08)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['temp_max'], mode='lines', name='Maks',
                                 line=dict(color='#ff6040', dash='dot', width=1.5)), row=1, col=1)
        fig.add_trace(go.Bar(x=df['lbl'], y=df['humidity'], name='Namlik',
                             marker_color='rgba(64,160,255,0.5)'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['wind_speed'], mode='lines+markers', name='Shamol',
                                 line=dict(color='#a060ff', width=2)), row=2, col=1)
        fig.update_layout(height=520, **plotly_cfg(), legend=dict(orientation='h', y=-0.1))
        st.plotly_chart(fig, use_container_width=True)

    elif view == "📅 Kunlik" and ds:
        st.markdown('<div class="section-title">5 Kunlik Prognoz</div>', unsafe_allow_html=True)
        cols = st.columns(len(ds))
        for i, day in enumerate(ds):
            with cols[i]:
                st.markdown(f"""<div class="day-card">
                    <div class="day-name">{day['day_name'][:3]}</div>
                    <div style="font-size:2rem;margin:10px 0;">{emo(day['desc'])}</div>
                    <div class="day-temps">{day['temp_max']:.0f}° / {day['temp_min']:.0f}°</div>
                    <div class="day-meta">💧{day['hum_avg']:.0f}% 🌧{day['pop_max']:.0f}%</div>
                </div>""", unsafe_allow_html=True)
        df_s = pd.DataFrame(ds)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Maks', x=df_s['day_name'], y=df_s['temp_max'],
                              marker_color='rgba(255,80,60,0.7)'))
        fig2.add_trace(go.Bar(name='Min', x=df_s['day_name'], y=df_s['temp_min'],
                              marker_color='rgba(64,160,255,0.7)'))
        fig2.add_trace(go.Scatter(name="O'rtacha", x=df_s['day_name'], y=df_s['temp_avg'],
                                  mode='lines+markers', line=dict(color='#ffd32a', width=2.5)))
        fig2.update_layout(height=360, barmode='group', **plotly_cfg())
        st.plotly_chart(fig2, use_container_width=True)

    elif view == "🎯 Dashboard":
        cats = ['Harorat','Namlik','Shamol','Bosim','Bulut']
        vals = [max(0,min(100,(w['temp']+20)/50*100)), w['humidity'],
                min(100,w['wind_speed']*10),
                max(0,min(100,(w['pressure']-950)/100*100)), w['clouds']]
        c1, c2 = st.columns(2)
        with c1:
            fig3 = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(42,95,192,0.2)',
                line=dict(color='#2a5fc0', width=2)
            ))
            fig3.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,100],
                           gridcolor='rgba(255,255,255,0.05)',
                           tickfont=dict(color='#4060a0')),
                           angularaxis=dict(tickfont=dict(color='#6080b0', size=12)),
                           bgcolor='rgba(0,0,0,0)'),
                height=380, **plotly_cfg()
            )
            st.plotly_chart(fig3, use_container_width=True)
        with c2:
            if ds:
                df_s = pd.DataFrame(ds)
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['pop_max'],
                                      name="Yog'in %", marker_color='rgba(64,160,255,0.6)'))
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['wind_avg'],
                                      name='Shamol m/s', marker_color='rgba(160,96,255,0.6)'))
                fig4.update_layout(height=380, barmode='group', **plotly_cfg())
                st.plotly_chart(fig4, use_container_width=True)

    elif view == "🏠 Asosiy":
        st.markdown('<div class="section-title">Joylashuv</div>', unsafe_allow_html=True)
        st.map(pd.DataFrame({'lat': [w['lat']], 'lon': [w['lon']]}), zoom=9)

# ══════════════════════════════════════════════════════════════════════════════
# BOSHLANG'ICH EKRAN
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;">
        <div style="font-size:5rem;margin-bottom:16px;">⛅</div>
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#2a5fc0;">
            WeatherXoja
        </div>
        <div style="color:#2a3a5a;margin-top:8px;">
            Real vaqt ob-havo · 5 kunlik prognoz · Interaktiv xarita
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Mashhur shaharlar</div>', unsafe_allow_html=True)
    demo = ["Toshkent","London","New York","Tokyo","Dubai","Paris","Moscow","Berlin"]
    for row in [demo[:4], demo[4:]]:
        cols = st.columns(4)
        for i, c in enumerate(row):
            with cols[i]:
                if st.button(f"⛅ {c}", use_container_width=True, key=f"d_{c}"):
                    st.session_state.search_city = c
                    st.session_state.do_search = True
                    st.rerun()
