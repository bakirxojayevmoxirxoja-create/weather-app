import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
from collections import Counter

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
    border: 1px solid #1e3a6e;
    border-radius: 24px; padding: 36px;
    box-shadow: 0 0 60px rgba(30,90,200,0.15), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 24px; position: relative; overflow: hidden;
}
.weather-hero::before {
    content: ''; position: absolute; top: -50%; right: -20%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(50,120,255,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-city { font-family: 'Syne', sans-serif; font-size: 2.4rem; font-weight: 800;
             color: #e8f0ff; margin: 0; letter-spacing: -0.5px; }
.hero-date { color: #6080b0; font-size: 0.9rem; margin-top: 4px; }
.hero-temp { font-family: 'Syne', sans-serif; font-size: 5rem; font-weight: 800;
             color: #fff; line-height: 1; letter-spacing: -2px; }
.hero-desc { color: #7090c0; font-size: 1rem; margin-top: 4px; text-transform: capitalize; }
.hero-feels { color: #5070a0; font-size: 0.85rem; margin-top: 2px; }
.sun-row { display: flex; gap: 24px; margin-top: 20px;
           background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px 20px;
           border: 1px solid rgba(255,255,255,0.05); }
.sun-item { color: #7090c0; font-size: 0.85rem; }
.sun-item b { color: #a0c0e8; }

.stat-card {
    background: #0a1525; border: 1px solid #1a2a45;
    border-radius: 18px; padding: 22px; text-align: center;
    transition: all 0.3s ease; position: relative; overflow: hidden;
}
.stat-card:hover { border-color: #2a4a80; transform: translateY(-2px);
                   box-shadow: 0 8px 30px rgba(20,60,150,0.2); }
.stat-card::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0;
                    height: 2px; background: linear-gradient(90deg, transparent, #2a5fc0, transparent); }
.stat-icon { font-size: 1.8rem; margin-bottom: 8px; }
.stat-val { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #d0e4ff; }
.stat-lbl { font-size: 0.75rem; color: #4060a0; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

.day-card {
    background: #0a1525; border: 1px solid #1a2a45;
    border-radius: 16px; padding: 18px; text-align: center;
    transition: all 0.2s; cursor: default;
}
.day-card:hover { border-color: #2a4a80; background: #0e1d35; }
.day-name { color: #4060a0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.day-emoji { font-size: 2rem; margin: 10px 0; }
.day-temps { color: #d0e4ff; font-weight: 600; font-size: 0.95rem; }
.day-meta { color: #304060; font-size: 0.75rem; margin-top: 6px; }

.map-info {
    background: #0a1525; border: 1px solid #1a2a45;
    border-radius: 18px; padding: 24px; height: 100%;
}
.map-city { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #e0eeff; }
.map-temp { font-family: 'Syne', sans-serif; font-size: 3.5rem; font-weight: 800;
            color: #4080ff; line-height: 1; margin: 8px 0; }
.map-table td { padding: 6px 0; color: #8090b0; font-size: 0.9rem; }
.map-table td:last-child { text-align: right; color: #c0d8f8; font-weight: 500; }

.section-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700;
                 color: #4060a0; text-transform: uppercase; letter-spacing: 2px;
                 margin: 28px 0 16px; border-left: 3px solid #2a5fc0; padding-left: 12px; }

div[data-testid="stButton"] button {
    background: #0e1d35 !important; color: #8090b0 !important;
    border: 1px solid #1a2a45 !important; border-radius: 10px !important;
    font-size: 0.8rem !important; transition: all 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    background: #162840 !important; border-color: #2a4a80 !important;
    color: #c0d8f8 !important;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #1a3a7e, #2a5fc0) !important;
    color: white !important; border: none !important;
}
</style>
""", unsafe_allow_html=True)

API_KEY = "ed304f5f1a412948049440ecc9bb0e3f"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

CITIES = {
    "Toshkent": (41.2995, 69.2401), "Samarqand": (39.6542, 66.9597),
    "Namangan": (41.0011, 71.6726), "Andijon": (40.7821, 72.3442),
    "Buxoro": (39.7747, 64.4286), "Nukus": (42.4500, 59.6106),
    "London": (51.5074, -0.1278), "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503), "Paris": (48.8566, 2.3522),
    "Dubai": (25.2048, 55.2708), "Moscow": (55.7558, 37.6176),
    "Singapore": (1.3521, 103.8198), "Sydney": (-33.8688, 151.2093),
    "Beijing": (39.9042, 116.4074), "Berlin": (52.5200, 13.4050),
    "Istanbul": (41.0082, 28.9784), "Cairo": (30.0444, 31.2357),
    "Seoul": (37.5665, 126.9780), "Mumbai": (19.0760, 72.8777),
    "Toronto": (43.6532, -79.3832), "Bangkok": (13.7563, 100.5018),
}

# Session state
for k, v in [('map_weather', None), ('search_city', ''), ('do_search', False), ('view', '🏠 Asosiy')]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── FUNKSIYALAR ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def fetch_weather(city=None, lat=None, lon=None):
    try:
        if city:
            url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric&lang=en"
        else:
            url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=en"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return _parse(r.json())
    except:
        pass
    return None

@st.cache_data(ttl=600)
def fetch_forecast(city):
    try:
        r = requests.get(f"{BASE_URL}forecast?q={city}&appid={API_KEY}&units=metric", timeout=10)
        if r.status_code == 200:
            d = r.json()
            tz_offset = d['city']['timezone']
            items = []
            for item in d['list']:
                lt = datetime.utcfromtimestamp(item['dt']) + pd.Timedelta(seconds=tz_offset)
                items.append({
                    'datetime': lt, 'date': lt.strftime('%Y-%m-%d'),
                    'day_name': lt.strftime('%A'), 'hour': lt.strftime('%H:%M'),
                    'temp': item['main']['temp'], 'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'], 'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed'],
                    'description': item['weather'][0]['description'],
                    'pop': item.get('pop', 0) * 100
                })
            return items
    except:
        pass
    return None

def _parse(d):
    tz = d['timezone']
    # UTC + timezone offset
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

def plotly_dark():
    return dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(6,11,20,0.8)',
                font=dict(color='#6080b0', family='Space Grotesk'))

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⛅ WeatherXoja")
    st.markdown("---")
    city_in = st.text_input("🔍 Shahar", placeholder="London, Tokyo, Toshkent...")
    popular = st.selectbox("⚡ Tez tanlash", [""]+list(CITIES.keys()))
    if popular:
        city_in = popular
    if st.button("Qidirish", use_container_width=True, type="primary"):
        st.session_state.search_city = city_in
        st.session_state.do_search = True
        st.rerun()
    st.markdown("---")
    view = st.radio("Ko'rinish", ["🏠 Asosiy","📈 Soatlik","📅 Kunlik","🗺️ Xarita","🎯 Dashboard"])
    st.session_state.view = view
    st.markdown("---")
    st.caption("⛅ WeatherXoja\nReal vaqt ob-havo tizimi\nPowered by OpenWeatherMap")

# ── SARLAVHA ──────────────────────────────────────────────────────────────────
st.markdown("# ⛅ WeatherXoja")

# ══════════════════════════════════════════════════════════════════════════════
# 🗺️ INTERAKTIV XARITA
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "🗺️ Xarita":
    st.markdown('<div class="section-title">Interaktiv Dunyo Xaritasi</div>', unsafe_allow_html=True)
    st.info("👇 Quyidagi shaharlardan birini bosing → ob-havo ma'lumoti chiqadi!")

    col_map, col_info = st.columns([3, 2])

    with col_map:
        lats = [v[0] for v in CITIES.values()]
        lons = [v[1] for v in CITIES.values()]
        names = list(CITIES.keys())
        sel = st.session_state.map_weather['city'] if st.session_state.map_weather else ""
        colors = ['#ff4757' if sel.lower() in n.lower() else '#2a5fc0' for n in names]
        sizes  = [20 if sel.lower() in n.lower() else 10 for n in names]

        fig_map = go.Figure(go.Scattergeo(
            lat=lats, lon=lons, text=names,
            mode='markers+text', textposition='top center',
            textfont=dict(size=9, color='#8090b0'),
            marker=dict(size=sizes, color=colors,
                        line=dict(width=1.5, color='rgba(255,255,255,0.3)')),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        fig_map.update_layout(
            geo=dict(
                showland=True, landcolor='#0e1d35',
                showocean=True, oceancolor='#060b14',
                showcoastlines=True, coastlinecolor='#1a2a45',
                showcountries=True, countrycolor='#1a2a45',
                showframe=False, bgcolor='#060b14',
                projection_type='natural earth',
                showlakes=True, lakecolor='#060b14',
            ),
            paper_bgcolor='#060b14', height=440,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Tugmalar
        st.markdown('<div class="section-title">Shahar tanlang</div>', unsafe_allow_html=True)
        city_list = list(CITIES.keys())
        for row in [city_list[i:i+6] for i in range(0, len(city_list), 6)]:
            cols = st.columns(len(row))
            for i, city in enumerate(row):
                with cols[i]:
                    if st.button(city, key=f"mb_{city}", use_container_width=True):
                        lat, lon = CITIES[city]
                        w = fetch_weather(lat=lat, lon=lon)
                        st.session_state.map_weather = w
                        st.rerun()

    with col_info:
        if st.session_state.map_weather:
            w = st.session_state.map_weather
            e = emo(w['description'])
            st.markdown(f"""
            <div class="map-info">
                <div style="font-size:3rem;margin-bottom:8px;">{e}</div>
                <div class="map-city">📍 {w['city']}, {w['country']}</div>
                <div class="map-temp">{w['temp']:.1f}°</div>
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
                </table>
                <div style="margin-top:16px;padding-top:16px;border-top:1px solid #1a2a45;
                            color:#304060;font-size:0.8rem;text-align:center;">
                    📅 {w['local_date']}
                </div>
            </div>""", unsafe_allow_html=True)

            # Mini radar
            cats = ['Harorat','Namlik','Shamol','Bosim','Bulut']
            vals = [
                max(0, min(100, (w['temp']+20)/50*100)),
                w['humidity'], min(100, w['wind_speed']*10),
                max(0, min(100, (w['pressure']-950)/100*100)),
                w['clouds']
            ]
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
                **{k: v for k, v in plotly_dark().items() if k not in ['paper_bgcolor','plot_bgcolor']}
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.markdown("""
            <div class="map-info" style="text-align:center;padding:60px 20px;">
                <div style="font-size:4rem;margin-bottom:16px;">🌍</div>
                <div style="color:#4060a0;font-size:1.1rem;font-weight:600;">
                    Quyidagi tugmalardan<br>shahar tanlang
                </div>
                <div style="color:#2a3a5a;font-size:0.85rem;margin-top:8px;">
                    Ob-havo ma'lumoti shu yerda chiqadi
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
        st.error(f"❌ **{city}** topilmadi! Inglizcha yozing (masalan: Tashkent, London).")
        st.stop()

    e = emo(w['description'])

    # Hero karta
    st.markdown(f"""
    <div class="weather-hero">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px;">
            <div>
                <div class="hero-city">📍 {w['city']}, {w['country']}</div>
                <div class="hero-date">{w['local_date']} · {w['local_time']} · {w['timezone']}</div>
                <div style="font-size:4rem;margin:16px 0 4px;">{e}</div>
                <div class="hero-desc">{w['description'].title()}</div>
            </div>
            <div style="text-align:right;">
                <div class="hero-temp">{w['temp']:.1f}°</div>
                <div class="hero-feels">His qilinadi: {w['feels_like']:.1f}°C</div>
                <div style="color:#3050a0;font-size:0.85rem;margin-top:4px;">
                    ↓ {w['temp_min']:.1f}° &nbsp;&nbsp; ↑ {w['temp_max']:.1f}°
                </div>
            </div>
        </div>
        <div class="sun-row">
            <span class="sun-item">🌅 Chiqish: <b>{w['sunrise']}</b></span>
            <span class="sun-item">🌇 Botish: <b>{w['sunset']}</b></span>
            <span class="sun-item">☁️ Bulut: <b>{w['clouds']}%</b></span>
            <span class="sun-item">📍 {w['lat']:.2f}°, {w['lon']:.2f}°</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Stat kartalar
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, val, lbl in [
        (c1,"💧",f"{w['humidity']}%","Namlik"),
        (c2,"💨",f"{w['wind_speed']} m/s","Shamol · "+wdir(w['wind_deg'])),
        (c3,"🌀",f"{w['pressure']}","Bosim hPa"),
        (c4,"👁️",f"{w['clouds']}%","Bulutlilik"),
    ]:
        with col:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-icon">{icon}</div>
                <div class="stat-val">{val}</div>
                <div class="stat-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    view = st.session_state.view

    # SOATLIK
    if view == "📈 Soatlik" and fc:
        st.markdown('<div class="section-title">24 Soatlik Prognoz</div>', unsafe_allow_html=True)
        df = pd.DataFrame(fc[:8])
        df['lbl'] = df['datetime'].apply(lambda x: x.strftime('%H:%M'))
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=('Harorat °C', 'Namlik % · Shamol m/s'),
                            vertical_spacing=0.18)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['temp'], mode='lines+markers', name='Harorat',
                                 line=dict(color='#4080ff', width=3),
                                 marker=dict(size=8, color='#4080ff'),
                                 fill='tozeroy', fillcolor='rgba(64,128,255,0.08)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['temp_max'], mode='lines', name='Maks',
                                 line=dict(color='#ff6040', dash='dot', width=1.5)), row=1, col=1)
        fig.add_trace(go.Bar(x=df['lbl'], y=df['humidity'], name='Namlik',
                             marker_color='rgba(64,160,255,0.5)'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['lbl'], y=df['wind_speed'], mode='lines+markers', name='Shamol',
                                 line=dict(color='#a060ff', width=2)), row=2, col=1)
        fig.update_layout(height=520, **plotly_dark(),
                          legend=dict(orientation='h', y=-0.1))
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.03)')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.03)')
        st.plotly_chart(fig, use_container_width=True)

    # KUNLIK
    elif view == "📅 Kunlik" and ds:
        st.markdown('<div class="section-title">5 Kunlik Prognoz</div>', unsafe_allow_html=True)
        cols = st.columns(len(ds))
        for i, day in enumerate(ds):
            with cols[i]:
                st.markdown(f"""<div class="day-card">
                    <div class="day-name">{day['day_name'][:3]}</div>
                    <div class="day-emoji">{emo(day['desc'])}</div>
                    <div class="day-temps">{day['temp_max']:.0f}° / {day['temp_min']:.0f}°</div>
                    <div class="day-meta">💧{day['hum_avg']:.0f}% &nbsp; 🌧{day['pop_max']:.0f}%</div>
                </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        df_s = pd.DataFrame(ds)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Maks °C', x=df_s['day_name'], y=df_s['temp_max'],
                              marker_color='rgba(255,80,60,0.7)', marker_line_width=0))
        fig2.add_trace(go.Bar(name='Min °C', x=df_s['day_name'], y=df_s['temp_min'],
                              marker_color='rgba(64,160,255,0.7)', marker_line_width=0))
        fig2.add_trace(go.Scatter(name="O'rtacha", x=df_s['day_name'], y=df_s['temp_avg'],
                                  mode='lines+markers', line=dict(color='#ffd32a', width=2.5),
                                  marker=dict(size=8)))
        fig2.update_layout(height=360, barmode='group', **plotly_dark())
        fig2.update_xaxes(gridcolor='rgba(255,255,255,0.03)')
        fig2.update_yaxes(gridcolor='rgba(255,255,255,0.03)')
        st.plotly_chart(fig2, use_container_width=True)

    # DASHBOARD
    elif view == "🎯 Dashboard":
        st.markdown('<div class="section-title">Dashboard</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        cats = ['Harorat','Namlik','Shamol','Bosim','Bulut']
        vals = [max(0,min(100,(w['temp']+20)/50*100)), w['humidity'],
                min(100,w['wind_speed']*10),
                max(0,min(100,(w['pressure']-950)/100*100)), w['clouds']]
        with c1:
            fig3 = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(42,95,192,0.2)',
                line=dict(color='#2a5fc0', width=2), marker=dict(size=7, color='#4080ff')
            ))
            fig3.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,100],
                           gridcolor='rgba(255,255,255,0.05)',
                           tickfont=dict(color='#4060a0')),
                           angularaxis=dict(tickfont=dict(color='#6080b0', size=12)),
                           bgcolor='rgba(0,0,0,0)'),
                height=380, **plotly_dark()
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
                fig4.update_layout(height=380, barmode='group', **plotly_dark())
                st.plotly_chart(fig4, use_container_width=True)

    # ASOSIY — mini xarita
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
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#2a5fc0;margin-bottom:8px;">
            WeatherXoja
        </div>
        <div style="color:#2a3a5a;font-size:1rem;">
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
