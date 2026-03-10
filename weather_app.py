import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="🌤️ Ob-havo Tizimi", page_icon="🌤️",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%); }
    .metric-card {
        background: linear-gradient(135deg, #1e2a3a, #2d3f55);
        border-radius: 16px; padding: 20px; text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin-bottom: 10px;
    }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #e0e6f0; }
    .metric-label { font-size: 0.85rem; color: #8899aa; margin-top: 4px; }
    .weather-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 20px; padding: 28px; color: white; margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .map-info-box {
        background: linear-gradient(135deg, #1e2a3a, #2d3f55);
        border-radius: 16px; padding: 20px;
        border: 1px solid rgba(255,255,255,0.15);
    }
</style>
""", unsafe_allow_html=True)

API_KEY = "ed304f5f1a412948049440ecc9bb0e3f"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

WORLD_CITIES = {
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

# Session state
for key, val in [('map_weather', None), ('map_lat', 41.2995), ('map_lon', 69.2401),
                 ('view_mode', '🏠 Asosiy'), ('search_city', 'Tashkent'), ('do_search', False)]:
    if key not in st.session_state:
        st.session_state[key] = val

@st.cache_data(ttl=600)
def get_weather_by_city(city):
    try:
        r = requests.get(f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric", timeout=10)
        if r.status_code == 200:
            return parse_weather(r.json())
    except:
        pass
    return None

@st.cache_data(ttl=600)
def get_weather_by_coords(lat, lon):
    try:
        r = requests.get(f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric", timeout=10)
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
        'clouds': d['clouds']['all'], 'description': d['weather'][0]['description'],
        'local_time': lt.strftime('%H:%M'), 'local_date': lt.strftime('%d %B %Y'),
        'sunrise': sr.strftime('%H:%M'), 'sunset': ss.strftime('%H:%M'),
        'timezone': f"UTC{tz//3600:+d}", 'lat': d['coord']['lat'], 'lon': d['coord']['lon']
    }

@st.cache_data(ttl=600)
def get_forecast(city):
    try:
        r = requests.get(f"{BASE_URL}forecast?q={city}&appid={API_KEY}&units=metric", timeout=10)
        if r.status_code == 200:
            data = r.json()
            tz = data['city']['timezone']
            items = []
            for item in data['list']:
                lt = datetime.fromtimestamp(item['dt'] + tz)
                items.append({
                    'datetime': lt, 'date': lt.strftime('%Y-%m-%d'),
                    'day_name': lt.strftime('%A'), 'temp': item['main']['temp'],
                    'temp_min': item['main']['temp_min'], 'temp_max': item['main']['temp_max'],
                    'humidity': item['main']['humidity'], 'wind_speed': item['wind']['speed'],
                    'description': item['weather'][0]['description'],
                    'pop': item.get('pop', 0) * 100
                })
            return items
    except:
        pass
    return None

def get_daily_summary(forecast, days=5):
    if not forecast: return None
    daily = {}
    for item in forecast:
        d = item['date']
        if d not in daily:
            daily[d] = {'date': d, 'day_name': item['day_name'],
                        'temps': [], 'temp_mins': [], 'temp_maxs': [],
                        'humidities': [], 'wind_speeds': [], 'descriptions': [], 'pop': []}
        daily[d]['temps'].append(item['temp'])
        daily[d]['temp_mins'].append(item['temp_min'])
        daily[d]['temp_maxs'].append(item['temp_max'])
        daily[d]['humidities'].append(item['humidity'])
        daily[d]['wind_speeds'].append(item['wind_speed'])
        daily[d]['descriptions'].append(item['description'])
        daily[d]['pop'].append(item['pop'])
    summary = []
    for d in daily.values():
        desc = Counter(d['descriptions']).most_common(1)[0][0]
        summary.append({
            'date': d['date'], 'day_name': d['day_name'],
            'temp_avg': np.mean(d['temps']), 'temp_min': min(d['temp_mins']),
            'temp_max': max(d['temp_maxs']), 'humidity_avg': np.mean(d['humidities']),
            'wind_avg': np.mean(d['wind_speeds']), 'description': desc,
            'pop_max': max(d['pop']), 'pop_avg': np.mean(d['pop'])
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

def wind_dir(deg):
    dirs = ['⬆️N','↗️NE','➡️E','↘️SE','⬇️S','↙️SW','⬅️W','↖️NW']
    return dirs[int((deg + 22.5) / 45) % 8]

def show_weather_card(w):
    emo = weather_emoji(w['description'])
    st.markdown(f"""
    <div class="weather-header">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
            <div>
                <h1 style="margin:0;font-size:2.2rem;">📍 {w['city']}, {w['country']}</h1>
                <p style="margin:6px 0 0;opacity:0.85;">{w['local_date']} | {w['local_time']} | {w['timezone']}</p>
            </div>
            <div style="text-align:center;">
                <div style="font-size:4rem;">{emo}</div>
                <div>{w['description'].title()}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:3.5rem;font-weight:900;">{w['temp']:.1f}°C</div>
                <div style="opacity:0.8;">His: {w['feels_like']:.1f}°C</div>
                <div style="opacity:0.7;font-size:0.9rem;">↓{w['temp_min']:.1f}° ↑{w['temp_max']:.1f}°</div>
            </div>
        </div>
        <div style="display:flex;justify-content:space-around;margin-top:16px;
                    background:rgba(255,255,255,0.1);border-radius:12px;padding:12px;">
            <span>🌅 {w['sunrise']}</span><span>☁️ {w['clouds']}%</span><span>🌇 {w['sunset']}</span>
        </div>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, val, label in [
        (c1,"💧",f"{w['humidity']}%","Namlik"),
        (c2,"💨",f"{w['wind_speed']} m/s {wind_dir(w['wind_deg'])}","Shamol"),
        (c3,"🌀",f"{w['pressure']} hPa","Bosim"),
        (c4,"☁️",f"{w['clouds']}%","Bulutlilik"),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div style="font-size:2rem;">{icon}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌤️ Ob-havo Tizimi")
    st.markdown("---")
    city_input = st.text_input("🏙️ Shahar nomi", value=st.session_state.search_city)
    popular = st.selectbox("⚡ Tez tanlash", ["","Tashkent","London","New York","Tokyo",
                           "Paris","Dubai","Moscow","Singapore","Sydney","Berlin","Istanbul"])
    if popular:
        city_input = popular
    if st.button("🔍 Qidirish", use_container_width=True, type="primary"):
        st.session_state.search_city = city_input
        st.session_state.do_search = True
        st.rerun()
    st.markdown("---")
    mode = st.radio("📊 Ko'rinish",
                    ["🏠 Asosiy","📈 Soatlik","📅 Kunlik","🗺️ Interaktiv Xarita","🎯 Dashboard"])
    st.session_state.view_mode = mode
    st.markdown("---")
    st.caption("OpenWeatherMap API\nReal vaqt • 5 kunlik prognoz")

st.markdown("# 🌤️ Mukammal Ob-havo Tizimi")

# ══════════════════════════════════════════════════════════════════════════════
# INTERAKTIV XARITA
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view_mode == "🗺️ Interaktiv Xarita":
    st.markdown("### 🗺️ Interaktiv Dunyo Xaritasi")
    st.info("👇 Quyidagi tugmalardan shahar tanlang — ob-havo chiqadi!")

    col_map, col_info = st.columns([3, 2])

    with col_map:
        lats = [v[0] for v in WORLD_CITIES.values()]
        lons = [v[1] for v in WORLD_CITIES.values()]
        names = list(WORLD_CITIES.keys())

        sel_city = st.session_state.map_weather['city'] if st.session_state.map_weather else ""
        colors = ['#ff6b6b' if sel_city.lower() in n.lower() else '#667eea' for n in names]
        sizes  = [18 if sel_city.lower() in n.lower() else 12 for n in names]

        fig_map = go.Figure(go.Scattergeo(
            lat=lats, lon=lons, text=names,
            mode='markers+text', textposition='top center',
            textfont=dict(size=9, color='white'),
            marker=dict(size=sizes, color=colors, line=dict(width=2, color='white')),
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))
        fig_map.update_layout(
            geo=dict(showland=True, landcolor='#1e2a3a', showocean=True, oceancolor='#0e1117',
                     showcoastlines=True, coastlinecolor='#3d5a80',
                     showcountries=True, countrycolor='#3d5a80',
                     showframe=False, bgcolor='#0e1117', projection_type='natural earth'),
            paper_bgcolor='#0e1117', height=420,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # Shahar tugmalari — 5 qator
        st.markdown("**🌆 Shaharni bosing:**")
        city_list = list(WORLD_CITIES.keys())
        for row in [city_list[i:i+5] for i in range(0, len(city_list), 5)]:
            cols = st.columns(len(row))
            for i, city in enumerate(row):
                with cols[i]:
                    if st.button(city, key=f"mb_{city}", use_container_width=True):
                        lat, lon = WORLD_CITIES[city]
                        st.session_state.map_lat = lat
                        st.session_state.map_lon = lon
                        st.session_state.map_weather = get_weather_by_coords(lat, lon)
                        st.rerun()

    with col_info:
        st.markdown("#### 📍 Ob-havo ma'lumoti")
        if st.session_state.map_weather:
            w = st.session_state.map_weather
            emo = weather_emoji(w['description'])
            st.markdown(f"""
            <div class="map-info-box">
                <h2 style="color:white;margin:0 0 8px;">{emo} {w['city']}, {w['country']}</h2>
                <div style="font-size:3rem;font-weight:900;color:#667eea;margin:10px 0;">{w['temp']:.1f}°C</div>
                <div style="color:#a0b4c8;margin-bottom:16px;">
                    {w['description'].title()}<br>His: {w['feels_like']:.1f}°C
                </div>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <table style="width:100%;color:#e0e6f0;font-size:0.95rem;border-spacing:0 8px;">
                    <tr><td>💧 Namlik</td><td style="text-align:right;font-weight:bold;">{w['humidity']}%</td></tr>
                    <tr><td>💨 Shamol</td><td style="text-align:right;font-weight:bold;">{w['wind_speed']} m/s {wind_dir(w['wind_deg'])}</td></tr>
                    <tr><td>🌀 Bosim</td><td style="text-align:right;font-weight:bold;">{w['pressure']} hPa</td></tr>
                    <tr><td>☁️ Bulut</td><td style="text-align:right;font-weight:bold;">{w['clouds']}%</td></tr>
                    <tr><td>🌡️ Min/Maks</td><td style="text-align:right;font-weight:bold;">{w['temp_min']:.1f}°/{w['temp_max']:.1f}°</td></tr>
                </table>
                <hr style="border-color:rgba(255,255,255,0.1);">
                <div style="display:flex;justify-content:space-between;color:#a0b4c8;font-size:0.9rem;">
                    <span>🌅 {w['sunrise']}</span><span>{w['timezone']}</span><span>🌇 {w['sunset']}</span>
                </div>
                <div style="margin-top:8px;color:#8899aa;font-size:0.8rem;text-align:center;">
                    📅 {w['local_date']} | ⏰ {w['local_time']}
                </div>
            </div>""", unsafe_allow_html=True)

            # Radar
            cats = ['Harorat','Namlik','Shamol','Bosim','Bulut']
            vals = [max(0,min(100,(w['temp']+20)/50*100)), w['humidity'],
                    min(100,w['wind_speed']*10),
                    max(0,min(100,(w['pressure']-950)/100*100)), w['clouds']]
            fig_r = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(102,126,234,0.3)',
                line=dict(color='#667eea', width=2)
            ))
            fig_r.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,100],
                           gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white',size=8)),
                           angularaxis=dict(tickfont=dict(color='white',size=10)),
                           bgcolor='rgba(0,0,0,0)'),
                template='plotly_dark', height=280,
                paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=40,r=40,t=10,b=10)
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.markdown("""
            <div class="map-info-box" style="text-align:center;padding:60px 20px;">
                <div style="font-size:4rem;">🌍</div>
                <p style="color:#8899aa;margin-top:16px;font-size:1.1rem;">
                    Quyidagi tugmalardan shahar tanlang!
                </p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# QIDIRUV NATIJALARI
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.do_search or st.session_state.search_city:
    city = st.session_state.search_city
    with st.spinner(f"🔍 {city} yuklanmoqda..."):
        current = get_weather_by_city(city)
        forecast = get_forecast(city)
        summary = get_daily_summary(forecast) if forecast else None

    if not current:
        st.error(f"❌ **{city}** topilmadi! Inglizcha yozing.")
        st.stop()

    show_weather_card(current)

    mode = st.session_state.view_mode

    if mode == "📈 Soatlik" and forecast:
        st.markdown("### 📈 24 Soatlik Prognoz")
        df = pd.DataFrame(forecast[:8])
        df['label'] = df['datetime'].apply(lambda x: x.strftime('%H:%M'))
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=('Harorat (°C)', 'Namlik % va Shamol m/s'),
                            vertical_spacing=0.15)
        fig.add_trace(go.Scatter(x=df['label'], y=df['temp'], mode='lines+markers',
                                 name='Harorat', line=dict(color='#ff6b6b', width=3),
                                 fill='tozeroy', fillcolor='rgba(255,107,107,0.15)'), row=1, col=1)
        fig.add_trace(go.Bar(x=df['label'], y=df['humidity'], name='Namlik',
                             marker_color='#48dbfb', opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['label'], y=df['wind_speed'], mode='lines+markers',
                                 name='Shamol', line=dict(color='#a29bfe', width=2)), row=2, col=1)
        fig.update_layout(height=500, template='plotly_dark',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    elif mode == "📅 Kunlik" and summary:
        st.markdown("### 📅 5 Kunlik Prognoz")
        cols = st.columns(len(summary))
        for i, day in enumerate(summary):
            with cols[i]:
                emo = weather_emoji(day['description'])
                st.markdown(f"""<div class="metric-card">
                    <div style="font-weight:bold;color:#a0b4c8;">{day['day_name'][:3]}</div>
                    <div style="font-size:1.8rem;margin:8px 0;">{emo}</div>
                    <div class="metric-value">{day['temp_max']:.0f}°/{day['temp_min']:.0f}°</div>
                    <div class="metric-label">💧{day['humidity_avg']:.0f}% 🌧{day['pop_max']:.0f}%</div>
                </div>""", unsafe_allow_html=True)
        df_s = pd.DataFrame(summary)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Maks', x=df_s['day_name'], y=df_s['temp_max'], marker_color='#ff6b6b'))
        fig2.add_trace(go.Bar(name='Min', x=df_s['day_name'], y=df_s['temp_min'], marker_color='#48dbfb'))
        fig2.add_trace(go.Scatter(name="O'rtacha", x=df_s['day_name'], y=df_s['temp_avg'],
                                  mode='lines+markers', line=dict(color='#ffd32a', width=3)))
        fig2.update_layout(height=380, template='plotly_dark', barmode='group',
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    elif mode == "🎯 Dashboard":
        cats = ['Harorat','Namlik','Shamol','Bosim','Bulutlilik']
        vals = [max(0,min(100,(current['temp']+20)/50*100)), current['humidity'],
                min(100,current['wind_speed']*10),
                max(0,min(100,(current['pressure']-950)/100*100)), current['clouds']]
        c1, c2 = st.columns(2)
        with c1:
            fig3 = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(102,126,234,0.3)',
                line=dict(color='#667eea', width=2)
            ))
            fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100],
                               gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
                               angularaxis=dict(tickfont=dict(color='white',size=12))),
                               template='plotly_dark', height=400,
                               paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
        with c2:
            if summary:
                df_s = pd.DataFrame(summary)
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['pop_max'],
                                      name="Yog'in %", marker_color='#48dbfb', opacity=0.7))
                fig4.add_trace(go.Bar(x=df_s['day_name'], y=df_s['wind_avg'],
                                      name='Shamol', marker_color='#a29bfe', opacity=0.7))
                fig4.update_layout(height=400, template='plotly_dark', barmode='group',
                                   paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig4, use_container_width=True)

    elif mode == "🏠 Asosiy":
        st.markdown("### 🗺️ Joylashuv")
        st.map(pd.DataFrame({'lat': [current['lat']], 'lon': [current['lon']]}), zoom=8)

else:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;color:#8899aa;">
        <div style="font-size:5rem;">🌍</div>
        <h2 style="color:#a0b4c8;">Shahar nomini kiriting va qidiring</h2>
        <p>Real vaqt ob-havo • 5 kunlik prognoz • Interaktiv xarita</p>
    </div>""", unsafe_allow_html=True)
    st.markdown("### 🌆 Mashhur Shaharlar")
    for row in [["Tashkent","London","New York"],["Tokyo","Dubai","Paris"]]:
        cols = st.columns(3)
        for i, c in enumerate(row):
            with cols[i]:
                if st.button(f"🏙️ {c}", use_container_width=True, key=f"demo_{c}"):
                    st.session_state.search_city = c
                    st.session_state.do_search = True
                    st.rerun()
