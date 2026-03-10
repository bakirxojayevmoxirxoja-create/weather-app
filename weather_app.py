import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from collections import Counter

# ─── SAHIFA SOZLAMALARI ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌤️ Ob-havo Tizimi",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%); }
    .metric-card {
        background: linear-gradient(135deg, #1e2a3a, #2d3f55);
        border-radius: 16px; padding: 20px; text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin-bottom: 10px;
    }
    .metric-icon { font-size: 2rem; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #e0e6f0; }
    .metric-label { font-size: 0.85rem; color: #8899aa; margin-top: 4px; }
    .weather-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px; padding: 28px; color: white;
        margin-bottom: 24px; box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .map-info-box {
        background: linear-gradient(135deg, #1e2a3a, #2d3f55);
        border-radius: 16px; padding: 20px;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
</style>
""", unsafe_allow_html=True)

# ─── API ──────────────────────────────────────────────────────────────────────
API_KEY = "ed304f5f1a412948049440ecc9bb0e3f"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# ─── FUNKSIYALAR ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_weather_by_city(city):
    try:
        url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return parse_weather(r.json())
    except Exception as e:
        st.error(f"Xatolik: {e}")
    return None

@st.cache_data(ttl=600)
def get_weather_by_coords(lat, lon):
    try:
        url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return parse_weather(r.json())
    except:
        pass
    return None

def parse_weather(d):
    tz = d['timezone']
    lt = datetime.fromtimestamp(d['dt'] + tz)
    sr = datetime.fromtimestamp(d['sys']['sunrise'] + tz)
    ss = datetime.fromtimestamp(d['sys']['sunset'] + tz)
    return {
        'city': d['name'], 'country': d['sys']['country'],
        'temp': d['main']['temp'], 'feels_like': d['main']['feels_like'],
        'temp_min': d['main']['temp_min'], 'temp_max': d['main']['temp_max'],
        'humidity': d['main']['humidity'], 'pressure': d['main']['pressure'],
        'wind_speed': d['wind']['speed'], 'wind_deg': d['wind'].get('deg', 0),
        'clouds': d['clouds']['all'],
        'description': d['weather'][0]['description'],
        'icon': d['weather'][0]['icon'],
        'local_time': lt.strftime('%H:%M'), 'local_date': lt.strftime('%d %B %Y'),
        'sunrise': sr.strftime('%H:%M'), 'sunset': ss.strftime('%H:%M'),
        'timezone': f"UTC{tz//3600:+d}",
        'lat': d['coord']['lat'], 'lon': d['coord']['lon']
    }

@st.cache_data(ttl=600)
def get_forecast(city):
    try:
        url = f"{BASE_URL}forecast?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            tz = data['city']['timezone']
            items = []
            for item in data['list']:
                lt = datetime.fromtimestamp(item['dt'] + tz)
                items.append({
                    'datetime': lt, 'date': lt.strftime('%Y-%m-%d'),
                    'time': lt.strftime('%H:%M'), 'day_name': lt.strftime('%A'),
                    'temp': item['main']['temp'], 'feels_like': item['main']['feels_like'],
                    'temp_min': item['main']['temp_min'], 'temp_max': item['main']['temp_max'],
                    'humidity': item['main']['humidity'], 'pressure': item['main']['pressure'],
                    'wind_speed': item['wind']['speed'], 'clouds': item['clouds']['all'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'pop': item.get('pop', 0) * 100
                })
            return items
    except:
        pass
    return None

def get_daily_summary(forecast, days=5):
    if not forecast:
        return None
    daily = {}
    for item in forecast:
        date = item['date']
        if date not in daily:
            daily[date] = {'date': date, 'day_name': item['day_name'],
                           'temps': [], 'temp_mins': [], 'temp_maxs': [],
                           'humidities': [], 'wind_speeds': [], 'descriptions': [], 'pop': []}
        daily[date]['temps'].append(item['temp'])
        daily[date]['temp_mins'].append(item['temp_min'])
        daily[date]['temp_maxs'].append(item['temp_max'])
        daily[date]['humidities'].append(item['humidity'])
        daily[date]['wind_speeds'].append(item['wind_speed'])
        daily[date]['descriptions'].append(item['description'])
        daily[date]['pop'].append(item['pop'])
    summary = []
    for d in daily.values():
        desc = Counter(d['descriptions']).most_common(1)[0][0]
        summary.append({
            'date': d['date'], 'day_name': d['day_name'],
            'temp_avg': np.mean(d['temps']),
            'temp_min': min(d['temp_mins']), 'temp_max': max(d['temp_maxs']),
            'humidity_avg': np.mean(d['humidities']),
            'wind_avg': np.mean(d['wind_speeds']),
            'description': desc, 'pop_max': max(d['pop']), 'pop_avg': np.mean(d['pop'])
        })
    return summary[:days]

def weather_emoji(desc):
    d = desc.lower()
    if 'clear' in d or 'sunny' in d: return '☀️'
    if 'cloud' in d: return '☁️'
    if 'rain' in d: return '🌧️'
    if 'snow' in d: return '❄️'
    if 'thunder' in d: return '⛈️'
    if 'mist' in d or 'fog' in d: return '🌫️'
    return '🌤️'

def wind_direction(deg):
    dirs = ['⬆️N','↗️NE','➡️E','↘️SE','⬇️S','↙️SW','⬅️W','↖️NW']
    return dirs[int((deg + 22.5) / 45) % 8]

def show_weather_card(current):
    emoji = weather_emoji(current['description'])
    st.markdown(f"""
    <div class="weather-header">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
            <div>
                <h1 style="margin:0; font-size:2.2rem;">📍 {current['city']}, {current['country']}</h1>
                <p style="margin:6px 0 0; opacity:0.85; font-size:1rem;">
                    {current['local_date']} &nbsp;|&nbsp; {current['local_time']} &nbsp;|&nbsp; {current['timezone']}
                </p>
            </div>
            <div style="text-align:center;">
                <div style="font-size:4rem;">{emoji}</div>
                <div style="font-size:1rem; opacity:0.9;">{current['description'].title()}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:3.5rem; font-weight:900;">{current['temp']:.1f}°C</div>
                <div style="opacity:0.8;">His: {current['feels_like']:.1f}°C</div>
                <div style="opacity:0.7; font-size:0.9rem;">↓{current['temp_min']:.1f}° &nbsp; ↑{current['temp_max']:.1f}°</div>
            </div>
        </div>
        <div style="display:flex; justify-content:space-around; margin-top:16px;
                    background:rgba(255,255,255,0.1); border-radius:12px; padding:12px;">
            <span>🌅 Chiqish: <b>{current['sunrise']}</b></span>
            <span>☁️ Bulut: <b>{current['clouds']}%</b></span>
            <span>🌇 Botish: <b>{current['sunset']}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "💧", f"{current['humidity']}%", "Namlik"),
        (c2, "💨", f"{current['wind_speed']} m/s {wind_direction(current['wind_deg'])}", "Shamol"),
        (c3, "🌀", f"{current['pressure']} hPa", "Bosim"),
        (c4, "☁️", f"{current['clouds']}%", "Bulutlilik"),
    ]
    for col, icon, val, label in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if 'map_weather' not in st.session_state:
    st.session_state.map_weather = None
if 'map_lat' not in st.session_state:
    st.session_state.map_lat = 41.2995
if 'map_lon' not in st.session_state:
    st.session_state.map_lon = 69.2401

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌤️ Ob-havo Tizimi")
    st.markdown("---")
    city_input = st.text_input("🏙️ Shahar nomi", value="Tashkent",
                               placeholder="Masalan: London, Tokyo...")
    popular = st.selectbox("⚡ Tez tanlash",
                           ["", "Tashkent", "London", "New York", "Tokyo",
                            "Paris", "Dubai", "Moscow", "Singapore", "Sydney",
                            "Beijing", "Berlin", "Istanbul", "Cairo", "Seoul"])
    if popular:
        city_input = popular
    search_btn = st.button("🔍 Qidirish", use_container_width=True, type="primary")
    st.markdown("---")
    view_mode = st.radio("📊 Ko'rinish",
                         ["🏠 Asosiy", "📈 Soatlik", "📅 Kunlik",
                          "🗺️ Interaktiv Xarita", "🎯 Dashboard"])
    st.markdown("---")
    st.caption("OpenWeatherMap API\nReal vaqt • 5 kunlik prognoz\nInteraktiv dunyo xaritasi")

# ─── ASOSIY ───────────────────────────────────────────────────────────────────
st.markdown("# 🌤️ Mukammal Ob-havo Tizimi")

# ══════════════════════════════════════════════════════════════════════════════
# INTERAKTIV XARITA SAHIFASI
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🗺️ Interaktiv Xarita":
    st.markdown("### 🗺️ Interaktiv Dunyo Xaritasi")
    st.info("🌍 Quyidagi shaharlardan birini bosing — o'sha joyning ob-havosi chiqadi!")

    world_cities = {
        "Tashkent": (41.2995, 69.2401), "Samarkand": (39.6542, 66.9597),
        "Namangan": (41.0011, 71.6726), "London": (51.5074, -0.1278),
        "New York": (40.7128, -74.0060), "Tokyo": (35.6762, 139.6503),
        "Paris": (48.8566, 2.3522), "Dubai": (25.2048, 55.2708),
        "Moscow": (55.7558, 37.6176), "Singapore": (1.3521, 103.8198),
        "Sydney": (-33.8688, 151.2093), "Beijing": (39.9042, 116.4074),
        "Berlin": (52.5200, 13.4050), "Istanbul": (41.0082, 28.9784),
        "Cairo": (30.0444, 31.2357), "Seoul": (37.5665, 126.9780),
        "Mumbai": (19.0760, 72.8777), "Toronto": (43.6532, -79.3832),
        "Bangkok": (13.7563, 100.5018), "Buenos Aires": (-34.6037, -58.3816),
    }

    col_map, col_info = st.columns([3, 2])

    with col_map:
        lats = [v[0] for v in world_cities.values()]
        lons = [v[1] for v in world_cities.values()]
        names = list(world_cities.keys())

        # Tanlangan shahar rangini belgilaymiz
        colors = []
        sizes = []
        for name in names:
            if st.session_state.map_weather and st.session_state.map_weather.get('city', '').lower() in name.lower():
                colors.append('#ff6b6b')
                sizes.append(18)
            else:
                colors.append('#667eea')
                sizes.append(12)

        fig_map = go.Figure()
        fig_map.add_trace(go.Scattergeo(
            lat=lats, lon=lons, text=names,
            mode='markers+text',
            textposition='top center',
            textfont=dict(size=10, color='white'),
            marker=dict(size=sizes, color=colors, symbol='circle',
                        line=dict(width=2, color='white'), opacity=0.9),
            hovertemplate='<b>%{text}</b><br>Bosing!<extra></extra>',
            name='Shaharlar'
        ))

        fig_map.update_layout(
            geo=dict(
                showland=True, landcolor='#1e2a3a',
                showocean=True, oceancolor='#0e1117',
                showcoastlines=True, coastlinecolor='#3d5a80',
                showcountries=True, countrycolor='#3d5a80',
                showframe=False, bgcolor='#0e1117',
                projection_type='natural earth',
                showlakes=True, lakecolor='#0e1117',
            ),
            paper_bgcolor='#0e1117',
            height=480,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(bgcolor='rgba(30,42,58,0.8)', font=dict(color='white'))
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Shahar tugmalari
        st.markdown("**🌆 Shaharni tanlang (bosing):**")
        btn_cities = list(world_cities.keys())
        rows = [btn_cities[i:i+5] for i in range(0, len(btn_cities), 5)]
        for row in rows:
            cols_btn = st.columns(len(row))
            for i, city in enumerate(row):
                with cols_btn[i]:
                    if st.button(city, key=f"map_{city}", use_container_width=True):
                        lat, lon = world_cities[city]
                        st.session_state.map_lat = lat
                        st.session_state.map_lon = lon
                        st.session_state.map_weather = get_weather_by_coords(lat, lon)
                        st.rerun()

    with col_info:
        st.markdown("#### 📍 Tanlangan Joy")
        if st.session_state.map_weather:
            w = st.session_state.map_weather
            emo = weather_emoji(w['description'])
            st.markdown(f"""
            <div class="map-info-box">
                <h2 style="color:white; margin:0 0 8px;">{emo} {w['city']}, {w['country']}</h2>
                <div style="font-size:3rem; font-weight:900; color:#667eea; margin:10px 0;">
                    {w['temp']:.1f}°C
                </div>
                <div style="color:#a0b4c8; margin-bottom:16px;">
                    {w['description'].title()}<br>
                    His qilinadi: {w['feels_like']:.1f}°C
                </div>
                <hr style="border-color:rgba(255,255,255,0.1); margin:12px 0;">
                <table style="width:100%; color:#e0e6f0; font-size:0.95rem; border-spacing:0 8px;">
                    <tr>
                        <td>💧 Namlik</td>
                        <td style="text-align:right; font-weight:bold;">{w['humidity']}%</td>
                    </tr>
                    <tr>
                        <td>💨 Shamol</td>
                        <td style="text-align:right; font-weight:bold;">{w['wind_speed']} m/s {wind_direction(w['wind_deg'])}</td>
                    </tr>
                    <tr>
                        <td>🌀 Bosim</td>
                        <td style="text-align:right; font-weight:bold;">{w['pressure']} hPa</td>
                    </tr>
                    <tr>
                        <td>☁️ Bulutlilik</td>
                        <td style="text-align:right; font-weight:bold;">{w['clouds']}%</td>
                    </tr>
                    <tr>
                        <td>🌡️ Min / Maks</td>
                        <td style="text-align:right; font-weight:bold;">{w['temp_min']:.1f}° / {w['temp_max']:.1f}°</td>
                    </tr>
                </table>
                <hr style="border-color:rgba(255,255,255,0.1); margin:12px 0;">
                <div style="display:flex; justify-content:space-between; color:#a0b4c8; font-size:0.9rem;">
                    <span>🌅 {w['sunrise']}</span>
                    <span>{w['timezone']}</span>
                    <span>🌇 {w['sunset']}</span>
                </div>
                <div style="margin-top:10px; color:#8899aa; font-size:0.8rem; text-align:center;">
                    📅 {w['local_date']} &nbsp;|&nbsp; ⏰ {w['local_time']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Mini radar diagramma
            st.markdown("<br>", unsafe_allow_html=True)
            categories = ['Harorat', 'Namlik', 'Shamol', 'Bosim', 'Bulut']
            values = [
                max(0, min(100, (w['temp'] + 20) / 50 * 100)),
                w['humidity'], min(100, w['wind_speed'] * 10),
                max(0, min(100, (w['pressure'] - 950) / 100 * 100)),
                w['clouds']
            ]
            fig_r = go.Figure(go.Scatterpolar(
                r=values + [values[0]], theta=categories + [categories[0]],
                fill='toself', fillcolor='rgba(102,126,234,0.3)',
                line=dict(color='#667eea', width=2), marker=dict(size=6)
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100],
                                   gridcolor='rgba(255,255,255,0.1)',
                                   tickfont=dict(color='white', size=8)),
                    angularaxis=dict(tickfont=dict(color='white', size=10)),
                    bgcolor='rgba(0,0,0,0)'
                ),
                template='plotly_dark', height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=40, t=10, b=10)
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.markdown("""
            <div class="map-info-box" style="text-align:center; padding:60px 20px;">
                <div style="font-size:4rem;">🌍</div>
                <p style="color:#8899aa; margin-top:16px; font-size:1.1rem;">
                    Xarita ostidagi tugmalardan shahar tanlang!
                </p>
                <p style="color:#667eea; font-size:0.9rem;">
                    Ob-havo ma'lumotlari shu yerda chiqadi
                </p>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOSHQA SAHIFALAR
# ══════════════════════════════════════════════════════════════════════════════
elif search_btn or (city_input and city_input != "Tashkent"):
    city = city_input.strip()
    if not city:
        st.warning("Shahar nomini kiriting!")
        st.stop()

    with st.spinner(f"🔍 {city} yuklanmoqda..."):
        current = get_weather_by_city(city)
        forecast = get_forecast(city)
        summary = get_daily_summary(forecast) if forecast else None

    if not current:
        st.error(f"❌ **{city}** topilmadi! Inglizcha yozing.")
        st.stop()

    show_weather_card(current)

    if view_mode == "📈 Soatlik" and forecast:
        st.markdown("### 📈 24 Soatlik Prognoz")
        df = pd.DataFrame(forecast[:8])
        df['label'] = df['datetime'].apply(lambda x: x.strftime('%H:%M\n%d-%b'))
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=('Harorat (°C)', 'Namlik (%) va Shamol (m/s)'),
                            vertical_spacing=0.15)
        fig.add_trace(go.Scatter(x=df['label'], y=df['temp'], mode='lines+markers',
                                 name='Harorat', line=dict(color='#ff6b6b', width=3),
                                 fill='tozeroy', fillcolor='rgba(255,107,107,0.15)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['label'], y=df['temp_max'], mode='lines',
                                 name='Maks', line=dict(color='#ffa502', dash='dot')), row=1, col=1)
        fig.add_trace(go.Bar(x=df['label'], y=df['humidity'], name='Namlik %',
                             marker_color='#48dbfb', opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['label'], y=df['wind_speed'], mode='lines+markers',
                                 name='Shamol m/s', line=dict(color='#a29bfe', width=2)), row=2, col=1)
        fig.update_layout(height=520, template='plotly_dark',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          legend=dict(orientation='h', y=-0.12))
        st.plotly_chart(fig, use_container_width=True)

    elif view_mode == "📅 Kunlik" and summary:
        st.markdown("### 📅 5 Kunlik Prognoz")
        cols = st.columns(len(summary))
        for i, day in enumerate(summary):
            with cols[i]:
                emo = weather_emoji(day['description'])
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight:bold; color:#a0b4c8;">{day['day_name'][:3]}</div>
                    <div style="font-size:1.8rem; margin:8px 0;">{emo}</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#e0e6f0;">
                        {day['temp_max']:.0f}° / {day['temp_min']:.0f}°
                    </div>
                    <div style="font-size:0.8rem; color:#8899aa; margin-top:4px;">
                        💧{day['humidity_avg']:.0f}% &nbsp; 🌧{day['pop_max']:.0f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
        df_s = pd.DataFrame(summary)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Maks °C', x=df_s['day_name'], y=df_s['temp_max'],
                              marker_color='#ff6b6b', opacity=0.8))
        fig2.add_trace(go.Bar(name='Min °C', x=df_s['day_name'], y=df_s['temp_min'],
                              marker_color='#48dbfb', opacity=0.8))
        fig2.add_trace(go.Scatter(name="O'rtacha", x=df_s['day_name'], y=df_s['temp_avg'],
                                  mode='lines+markers', line=dict(color='#ffd32a', width=3),
                                  marker=dict(size=9)))
        fig2.update_layout(height=380, template='plotly_dark', barmode='group',
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    elif view_mode == "🎯 Dashboard":
        categories = ['Harorat', 'Namlik', 'Shamol', 'Bosim', 'Bulutlilik']
        values = [
            max(0, min(100, (current['temp'] + 20) / 50 * 100)),
            current['humidity'], min(100, current['wind_speed'] * 10),
            max(0, min(100, (current['pressure'] - 950) / 100 * 100)),
            current['clouds']
        ]
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("### 🎯 Radar")
            fig3 = go.Figure(go.Scatterpolar(
                r=values + [values[0]], theta=categories + [categories[0]],
                fill='toself', fillcolor='rgba(102,126,234,0.3)',
                line=dict(color='#667eea', width=2), marker=dict(size=8, color='#764ba2')
            ))
            fig3.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100],
                                           gridcolor='rgba(255,255,255,0.1)',
                                           tickfont=dict(color='white')),
                           angularaxis=dict(tickfont=dict(color='white', size=13))),
                template='plotly_dark', height=400,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig3, use_container_width=True)
        with col_r2:
            if summary:
                st.markdown("### 📊 Shamol & Yog'in")
                df_s = pd.DataFrame(summary)
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['pop_max'],
                                      name="Yog'in %", marker_color='#48dbfb', opacity=0.7))
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['wind_avg'],
                                      name='Shamol m/s', marker_color='#a29bfe', opacity=0.7))
                fig4.update_layout(height=400, template='plotly_dark', barmode='group',
                                   paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig4, use_container_width=True)

    elif view_mode == "🏠 Asosiy":
        st.markdown("### 🗺️ Joylashuv")
        map_df = pd.DataFrame({'lat': [current['lat']], 'lon': [current['lon']]})
        st.map(map_df, zoom=8)

else:
    st.markdown("""
    <div style="text-align:center; padding:40px 20px; color:#8899aa;">
        <div style="font-size:5rem;">🌍</div>
        <h2 style="color:#a0b4c8;">Shahar nomini kiriting va qidiring</h2>
        <p>Real vaqt ob-havo • 5 kunlik prognoz • Interaktiv xarita</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🌆 Mashhur Shaharlar")
    cities_demo = ["Tashkent", "London", "New York", "Tokyo", "Dubai", "Paris"]
    cols = st.columns(3)
    for i, c in enumerate(cities_demo):
        with cols[i % 3]:
            if st.button(f"🏙️ {c}", use_container_width=True):
                st.session_state['city'] = c
                st.rerun()
