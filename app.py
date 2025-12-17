import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Dashboard Stunting Kabupaten Sidoarjo",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# ===============================
# CUSTOM CSS - MODERN & ELEGANT
# ===============================
st.markdown("""
<style>
    /* Main Background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Container dengan glassmorphism */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Header styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    h2, h3 {
        color: #667eea;
        font-weight: 700;
    }
    
    /* Metric cards enhancement */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        font-size: 1.1rem;
        color: #4a5568;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.6);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        background-color: white;
        border: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: 2px solid white;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    /* Dataframe */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .element-container {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    df = pd.read_csv("data_skrinning_stunting(1).csv")
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(".", "", regex=False)
    )
    df["nama_kecamatan"] = (
        df["nama_kecamatan"]
        .astype(str)
        .str.upper()
        .str.strip()
    )
    df["is_stunting"] = df["stunting_balita"].map({"Ya": 1, "Tidak": 0})
    return df

@st.cache_data
def load_geojson():
    with open("kecamatan_sidoarjo.geojson", "r", encoding="utf-8") as f:
        geojson = json.load(f)
    for feat in geojson["features"]:
        feat["properties"]["NAMOBJ"] = (
            feat["properties"]["NAMOBJ"]
            .upper()
            .strip()
        )
    return geojson

df = load_data()
geojson = load_geojson()

# ===============================
# SIDEBAR - MODERN FILTER
# ===============================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='color: white; margin: 0;'>🔍 Filter Data</h2>
        <p style='color: rgba(255,255,255,0.8); margin: 0.5rem 0;'>Sesuaikan visualisasi data</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.3); margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # Filter Kecamatan dengan search
    kecamatan_opsi = sorted(df["nama_kecamatan"].unique())
    kecamatan_pilih = st.multiselect(
        "📍 Pilih Kecamatan",
        kecamatan_opsi,
        default=kecamatan_opsi,
        help="Pilih satu atau lebih kecamatan untuk analisis"
    )
    
    # Filter Umur dengan range slider jika memungkinkan
    umur_opsi = sorted(df["umur_balita"].dropna().unique())
    
    if len(umur_opsi) > 0:
        umur_min = int(min(umur_opsi))
        umur_max = int(max(umur_opsi))
        
        if umur_max > umur_min:
            umur_range = st.slider(
                "👶 Rentang Umur Balita (bulan)",
                min_value=umur_min,
                max_value=umur_max,
                value=(umur_min, umur_max),
                help="Geser untuk memilih rentang umur"
            )
            umur_pilih = [u for u in umur_opsi if umur_range[0] <= u <= umur_range[1]]
        else:
            umur_pilih = umur_opsi
    else:
        umur_pilih = []
    
    # Filter Jenis Kelamin jika ada
    if 'jenis_kelamin_balita' in df.columns:
        jk_options = df['jenis_kelamin_balita'].dropna().unique().tolist()
        if len(jk_options) > 0:
            jk_pilih = st.multiselect(
                "⚧️ Jenis Kelamin",
                jk_options,
                default=jk_options,
                help="Filter berdasarkan jenis kelamin"
            )
        else:
            jk_pilih = None
    else:
        jk_pilih = None
    
    # Apply filters
    df_filtered = df[
        (df["nama_kecamatan"].isin(kecamatan_pilih)) &
        (df["umur_balita"].isin(umur_pilih))
    ]
    
    if jk_pilih and 'jenis_kelamin_balita' in df.columns:
        df_filtered = df_filtered[df_filtered['jenis_kelamin_balita'].isin(jk_pilih)]
    
    # Info box
    st.markdown("<hr style='border-color: rgba(255,255,255,0.3); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; color: white;'>
        <div style='text-align: center;'>
            <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>📊 Data Terfilter</p>
            <h2 style='margin: 0.5rem 0; color: white;'>{len(df_filtered):,}</h2>
            <p style='margin: 0; font-size: 0.85rem; opacity: 0.8;'>dari {len(df):,} total data</p>
            <div style='margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.3);'>
                <p style='margin: 0; font-size: 0.8rem;'>{len(df_filtered)/len(df)*100:.1f}% data dipilih</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats
    if len(df_filtered) > 0:
        quick_prev = (df_filtered["is_stunting"].sum() / len(df_filtered) * 100)
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.15); padding: 0.8rem; border-radius: 8px; margin-top: 1rem; color: white;'>
            <p style='margin: 0; font-size: 0.85rem; opacity: 0.9;'>⚡ Prevalensi</p>
            <h3 style='margin: 0.3rem 0; color: white;'>{quick_prev:.2f}%</h3>
        </div>
        """, unsafe_allow_html=True)

# ===============================
# HEADER dengan Animasi
# ===============================
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1>📊 Dashboard Analisis Stunting</h1>
    <p style='font-size: 1.3rem; color: #667eea; font-weight: 600;'>Kabupaten Sidoarjo</p>
    <p style='color: #718096; font-size: 1rem;'>Monitoring & Evaluasi Kesehatan Balita</p>
</div>
""", unsafe_allow_html=True)

# ===============================
# KPI CARDS - MODERN DESIGN
# ===============================
total_balita = len(df_filtered)
total_kasus = int(df_filtered["is_stunting"].sum())
prevalensi = (total_kasus / total_balita * 100) if total_balita > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 15px; color: white; 
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);'>
        <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>👶 Total Balita</p>
        <h2 style='margin: 0.5rem 0; color: white; font-size: 2.5rem;'>{:,}</h2>
        <p style='margin: 0; font-size: 0.85rem; opacity: 0.8;'>Diperiksa</p>
    </div>
    """.format(total_balita), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 1.5rem; border-radius: 15px; color: white;
                box-shadow: 0 8px 20px rgba(245, 87, 108, 0.4);'>
        <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>🚨 Kasus Stunting</p>
        <h2 style='margin: 0.5rem 0; color: white; font-size: 2.5rem;'>{:,}</h2>
        <p style='margin: 0; font-size: 0.85rem; opacity: 0.8;'>Balita</p>
    </div>
    """.format(total_kasus), unsafe_allow_html=True)

with col3:
    prev_color = "#f5576c" if prevalensi >= 30 else "#feca57" if prevalensi >= 20 else "#48dbfb"
    st.markdown("""
    <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                padding: 1.5rem; border-radius: 15px; color: white;
                box-shadow: 0 8px 20px rgba(79, 172, 254, 0.4);'>
        <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>📉 Prevalensi</p>
        <h2 style='margin: 0.5rem 0; color: white; font-size: 2.5rem;'>{:.2f}%</h2>
        <p style='margin: 0; font-size: 0.85rem; opacity: 0.8;'>Rata-rata</p>
    </div>
    """.format(prevalensi), unsafe_allow_html=True)

with col4:
    normal_count = total_balita - total_kasus
    st.markdown("""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                padding: 1.5rem; border-radius: 15px; color: white;
                box-shadow: 0 8px 20px rgba(67, 233, 123, 0.4);'>
        <p style='margin: 0; font-size: 0.9rem; opacity: 0.9;'>✅ Normal</p>
        <h2 style='margin: 0.5rem 0; color: white; font-size: 2.5rem;'>{:,}</h2>
        <p style='margin: 0; font-size: 0.85rem; opacity: 0.8;'>Balita Sehat</p>
    </div>
    """.format(normal_count), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===============================
# GAUGE CHART - INTERACTIVE
# ===============================
col_gauge, col_insight = st.columns([2, 1])

with col_gauge:
    st.markdown("### 🎯 Indikator Prevalensi Stunting")
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=prevalensi,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Prevalensi Stunting (%)", 'font': {'size': 22, 'color': '#667eea'}},
        number={'suffix': "%", 'font': {'size': 50, 'color': '#667eea'}},
        delta={
            'reference': 30,
            'increasing': {'color': "#f5576c"},
            'decreasing': {'color': "#43e97b"}
        },
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "#667eea"},
            'bar': {'color': "#667eea", 'thickness': 0.8},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [0, 10], 'color': '#d4f1d4'},
                {'range': [10, 20], 'color': '#b3e5b3'},
                {'range': [20, 30], 'color': '#ffeaa7'},
                {'range': [30, 40], 'color': '#feca57'},
                {'range': [40, 60], 'color': '#ff7675'},
                {'range': [60, 100], 'color': '#d63031'}
            ],
            'threshold': {
                'line': {'color': "#f5576c", 'width': 5},
                'thickness': 0.85,
                'value': 30
            }
        }
    ))
    
    fig_gauge.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'family': "Arial, sans-serif"}
    )
    
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_insight:
    st.markdown("### 💡 Status & Rekomendasi")
    
    if prevalensi < 10:
        status_color = "#43e97b"
        status_emoji = "🟢"
        status_text = "Sangat Baik"
        rekomendasi = "Pertahankan program pencegahan yang ada dan terus lakukan monitoring berkala."
    elif prevalensi < 20:
        status_color = "#feca57"
        status_emoji = "🟡"
        status_text = "Baik"
        rekomendasi = "Tingkatkan program edukasi gizi dan pemantauan pertumbuhan balita."
    elif prevalensi < 30:
        status_color = "#ff7675"
        status_emoji = "🟠"
        status_text = "Perlu Perhatian"
        rekomendasi = "Perlukan intervensi gizi targeted dan koordinasi lintas sektor."
    else:
        status_color = "#d63031"
        status_emoji = "🔴"
        status_text = "Kritis"
        rekomendasi = "Diperlukan intervensi intensif dan program khusus stunting segera!"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {status_color}15 0%, {status_color}05 100%); 
                padding: 1.5rem; border-radius: 15px; border-left: 5px solid {status_color};
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <span style='font-size: 2rem; margin-right: 0.5rem;'>{status_emoji}</span>
            <div>
                <p style='margin: 0; font-size: 0.9rem; color: #718096;'>Status Wilayah</p>
                <h3 style='margin: 0; color: {status_color};'>{status_text}</h3>
            </div>
        </div>
        <p style='margin: 0; color: #4a5568; line-height: 1.6; font-size: 0.95rem;'>
            {rekomendasi}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mini stats
    st.markdown("<br>", unsafe_allow_html=True)
    
    kec_df_temp = df_filtered.groupby("nama_kecamatan").agg(
        total_balita=("is_stunting", "count"),
        total_kasus=("is_stunting", "sum")
    ).reset_index()
    kec_df_temp["prevalensi"] = (kec_df_temp["total_kasus"] / kec_df_temp["total_balita"] * 100)
    
    if len(kec_df_temp) > 0:
        kec_tertinggi = kec_df_temp.loc[kec_df_temp["prevalensi"].idxmax()]
        kec_terendah = kec_df_temp.loc[kec_df_temp["prevalensi"].idxmin()]
        
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <p style='margin: 0; font-size: 0.85rem; color: #718096;'>🔴 Kecamatan Tertinggi</p>
            <p style='margin: 0.3rem 0 0 0; font-weight: 600; color: #2d3748;'>{kec_tertinggi['nama_kecamatan']}</p>
            <p style='margin: 0; font-size: 1.3rem; color: #f5576c; font-weight: 700;'>{kec_tertinggi['prevalensi']:.1f}%</p>
        </div>
        
        <div style='background: white; padding: 1rem; border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <p style='margin: 0; font-size: 0.85rem; color: #718096;'>🟢 Kecamatan Terendah</p>
            <p style='margin: 0.3rem 0 0 0; font-weight: 600; color: #2d3748;'>{kec_terendah['nama_kecamatan']}</p>
            <p style='margin: 0; font-size: 1.3rem; color: #43e97b; font-weight: 700;'>{kec_terendah['prevalensi']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ===============================
# AGREGASI DATA
# ===============================
kec_df = df_filtered.groupby("nama_kecamatan").agg(
    total_balita=("is_stunting", "count"),
    total_kasus=("is_stunting", "sum")
).reset_index()
kec_df["prevalensi"] = (kec_df["total_kasus"] / kec_df["total_balita"] * 100)

def categorize_age(age):
    try:
        age = float(age)
        if pd.isna(age):
            return "Unknown"
        elif age <= 12:
            return "0-12 Bulan"
        elif age <= 24:
            return "13-24 Bulan"
        elif age <= 36:
            return "25-36 Bulan"
        else:
            return "37-60 Bulan"
    except (ValueError, TypeError):
        return "Unknown"

df_temp = df_filtered.copy()
df_temp["kelompok_umur"] = df_temp["umur_balita"].apply(categorize_age)

age_df = df_temp.groupby("kelompok_umur").agg(
    total_balita=("is_stunting", "count"),
    total_kasus=("is_stunting", "sum")
).reset_index()

age_df = age_df[age_df["kelompok_umur"] != "Unknown"]
age_df["prevalensi"] = (age_df["total_kasus"] / age_df["total_balita"] * 100)

age_order = ["0-12 Bulan", "13-24 Bulan", "25-36 Bulan", "37-60 Bulan"]
age_df["kelompok_umur"] = pd.Categorical(age_df["kelompok_umur"], categories=age_order, ordered=True)
age_df = age_df.sort_values("kelompok_umur")

# ===============================
# TAB NAVIGATION - MODERN STYLE
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Peta Interaktif",
    "📊 Analisis Umur", 
    "🏆 Ranking Wilayah",
    "📈 Insight & Tren"
])

# TAB 1: PETA
with tab1:
    st.markdown("### 🗺️ Peta Prevalensi Stunting per Kecamatan")
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    with col_ctrl1:
        map_style = st.selectbox(
            "Style Peta",
            ["Default (Light)", "Default (Dark)", "Street Map", "Outdoor/Topografi"],
            key="map_style"
        )
        
        style_mapping = {
            "Default (Light)": "carto-positron",
            "Default (Dark)": "carto-darkmatter",
            "Street Map": "open-street-map",
            "Outdoor/Topografi": "stamen-terrain"
        }
        mapbox_style = style_mapping[map_style]
    
    with col_ctrl2:
        color_scheme = st.selectbox(
            "Skema Warna",
            ["RdYlGn_r", "Turbo", "Rainbow", "Reds", "Portland"],
            key="color_scheme"
        )
    
    with col_ctrl3:
        zoom_level = st.slider("Level Zoom", 8, 13, 10, key="zoom")
    
    fig_map = px.choropleth_mapbox(
        kec_df,
        geojson=geojson,
        locations="nama_kecamatan",
        featureidkey="properties.NAMOBJ",
        color="prevalensi",
        color_continuous_scale=color_scheme,
        range_color=(0, 100),
        mapbox_style=mapbox_style,
        center={"lat": -7.45, "lon": 112.71},
        zoom=zoom_level,
        opacity=0.85,
        hover_name="nama_kecamatan",
        hover_data={
            "nama_kecamatan": False,
            "total_balita": ":,",
            "total_kasus": ":,",
            "prevalensi": ":.2f"
        },
        labels={
            "prevalensi": "Prevalensi (%)",
            "total_balita": "Total Balita",
            "total_kasus": "Kasus Stunting"
        }
    )
    
    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600
    )
    
    st.plotly_chart(fig_map, use_container_width=True)

# TAB 2: ANALISIS UMUR
with tab2:
    st.markdown("### 📊 Analisis Fase Kritis Berdasarkan Kelompok Umur")
    
    if len(age_df) > 0:
        fig_age = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Prevalensi per Kelompok Umur", "Jumlah Kasus per Kelompok"),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Chart 1: Prevalensi
        fig_age.add_trace(
            go.Bar(
                x=age_df["kelompok_umur"],
                y=age_df["prevalensi"],
                text=age_df["prevalensi"].round(1).astype(str) + "%",
                textposition="outside",
                marker=dict(
                    color=age_df["prevalensi"],
                    colorscale="Plasma",
                    showscale=False
                ),
                name="Prevalensi"
            ),
            row=1, col=1
        )
        
        # Chart 2: Jumlah Kasus
        fig_age.add_trace(
            go.Bar(
                x=age_df["kelompok_umur"],
                y=age_df["total_kasus"],
                text=age_df["total_kasus"],
                textposition="outside",
                marker=dict(color="#f5576c"),
                name="Kasus"
            ),
            row=1, col=2
        )
        
        fig_age.update_layout(
            height=500,
            showlegend=False,
            font=dict(size=12)
        )
        
        fig_age.update_yaxes(title_text="Prevalensi (%)", row=1, col=1)
        fig_age.update_yaxes(title_text="Jumlah Kasus", row=1, col=2)
        
        st.plotly_chart(fig_age, use_container_width=True)
        
        # Cards untuk setiap kelompok
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📋 Detail per Kelompok Umur")
        
        cols = st.columns(len(age_df))
        for idx, (_, row) in enumerate(age_df.iterrows()):
            with cols[idx]:
                color = "#f5576c" if row['prevalensi'] >= 30 else "#feca57" if row['prevalensi'] >= 20 else "#43e97b"
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {color}15 0%, {color}05 100%); 
                            padding: 1.2rem; border-radius: 12px; text-align: center;
                            border: 2px solid {color}30;'>
                    <p style='margin: 0; font-size: 0.9rem; color: #718096; font-weight: 600;'>{row['kelompok_umur']}</p>
                    <h2 style='margin: 0.5rem 0; color: {color}; font-size: 2rem;'>{row['prevalensi']:.1f}%</h2>
                    <p style='margin: 0; font-size: 0.85rem; color: #4a5568;'>{row['total_kasus']:,} / {row['total_balita']:,}</p>
                </div>
                """, unsafe_allow_html=True)

# TAB 3: RANKING
with tab3:
    st.markdown("### 🏆 Ranking Kecamatan Berdasarkan Prevalensi")
    
    top_n_option = st.radio(
        "Tampilkan:",
        ["Top 5", "Top 10", "Semua"],
        horizontal=True,
        key="top_n"
    )
    
    n = 5 if top_n_option == "Top 5" else 10 if top_n_option == "Top 10" else len(kec_df)
    top_data = kec_df.sort_values("prevalensi", ascending=False).head(n)
    
    # Horizontal bar chart
    fig_bar = go.Figure()
    
    colors = px.colors.sequential.Reds_r
    
    fig_bar.add_trace(go.Bar(
        y=top_data["nama_kecamatan"],
        x=top_data["prevalensi"],
        orientation='h',
        text=top_data["prevalensi"].round(1).astype(str) + "%",
        textposition='outside',
        marker=dict(
            color=top_data["prevalensi"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="Prevalensi<br>(%)")
        ),
        hovertemplate="<b>%{y}</b><br>" +
                      "Prevalensi: %{x:.2f}%<br>" +
                      "<extra></extra>"
    ))
    
    fig_bar.update_layout(
        height=max(400, n * 50),
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="Prevalensi Stunting (%)",
        yaxis_title="",
        showlegend=False,
        font=dict(size=12)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Top 3 Cards
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🥇 Podium Prevalensi Tertinggi")
    
    col1, col2, col3 = st.columns(3)
    top3 = top_data.head(3)
    
    medals = ["🥇", "🥈", "🥉"]
    colors_medal = ["#FFD700", "#C0C0C0", "#CD7F32"]
    
    for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], top3.iterrows())):
        with col:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {colors_medal[idx]}20 0%, {colors_medal[idx]}05 100%);
                        padding: 1.5rem; border-radius: 15px; text-align: center;
                        border: 3px solid {colors_medal[idx]}; box-shadow: 0 8px 20px rgba(0,0,0,0.15);'>
                <div style='font-size: 3rem; margin-bottom: 0.5rem;'>{medals[idx]}</div>
                <h4 style='margin: 0; color: #2d3748;'>{row['nama_kecamatan']}</h4>
                <h2 style='margin: 0.5rem 0; color: #f5576c; font-size: 2.5rem;'>{row['prevalensi']:.1f}%</h2>
                <p style='margin: 0; color: #718096; font-size: 0.9rem;'>{row['total_kasus']:,} kasus dari {row['total_balita']:,} balita</p>
            </div>
            """, unsafe_allow_html=True)

# TAB 4: INSIGHT
with tab4:
    st.markdown("### 📈 Insight & Tren Data")
    
    # Comparison chart
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 🍩 Distribusi Status Balita")
        
        status_data = pd.DataFrame({
            'Status': ['Normal', 'Stunting'],
            'Jumlah': [total_balita - total_kasus, total_kasus],
            'Persentase': [(total_balita - total_kasus)/total_balita*100, prevalensi]
        })
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=status_data['Status'],
            values=status_data['Jumlah'],
            hole=0.5,
            marker=dict(colors=['#43e97b', '#f5576c']),
            textinfo='label+percent',
            textfont_size=14,
            hovertemplate="<b>%{label}</b><br>" +
                         "Jumlah: %{value:,}<br>" +
                         "Persentase: %{percent}<br>" +
                         "<extra></extra>"
        )])
        
        fig_pie.update_layout(
            height=400,
            annotations=[dict(text=f'{prevalensi:.1f}%', x=0.5, y=0.5, 
                            font_size=28, showarrow=False, font_color='#667eea')]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 📊 Statistik Wilayah")
        
        # Stats
        stats_metrics = {
            "Total Kecamatan": len(kec_df),
            "Rata-rata Prevalensi": f"{kec_df['prevalensi'].mean():.2f}%",
            "Median Prevalensi": f"{kec_df['prevalensi'].median():.2f}%",
            "Std Deviasi": f"{kec_df['prevalensi'].std():.2f}%"
        }
        
        for label, value in stats_metrics.items():
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem;
                        border-left: 4px solid #667eea; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                <p style='margin: 0; font-size: 0.85rem; color: #718096;'>{label}</p>
                <h3 style='margin: 0.3rem 0 0 0; color: #2d3748;'>{value}</h3>
            </div>
            """, unsafe_allow_html=True)
    
    # Heatmap distribusi
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🗺️ Heatmap Distribusi Prevalensi")
    
    # Categorize prevalensi
    kec_df_cat = kec_df.copy()
    kec_df_cat['kategori'] = pd.cut(
        kec_df_cat['prevalensi'],
        bins=[0, 20, 40, 60, 80, 100],
        labels=['Sangat Rendah', 'Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi']
    )
    
    kategori_count = kec_df_cat['kategori'].value_counts().reindex(
        ['Sangat Rendah', 'Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi'],
        fill_value=0
    )
    
    fig_kategori = go.Figure(data=[go.Bar(
        x=kategori_count.index,
        y=kategori_count.values,
        text=kategori_count.values,
        textposition='outside',
        marker=dict(
            color=['#43e97b', '#feca57', '#ff7675', '#d63031', '#8B0000'],
            line=dict(color='white', width=2)
        ),
        hovertemplate="<b>%{x}</b><br>" +
                     "Jumlah Kecamatan: %{y}<br>" +
                     "<extra></extra>"
    )])
    
    fig_kategori.update_layout(
        height=400,
        xaxis_title="Kategori Prevalensi",
        yaxis_title="Jumlah Kecamatan",
        showlegend=False
    )
    
    st.plotly_chart(fig_kategori, use_container_width=True)
    
    # Rekomendasi
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 💼 Rekomendasi Aksi")
    
    high_prev_kec = kec_df[kec_df['prevalensi'] >= 40]
    medium_prev_kec = kec_df[(kec_df['prevalensi'] >= 20) & (kec_df['prevalensi'] < 40)]
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f5576c15 0%, #f5576c05 100%);
                    padding: 1.5rem; border-radius: 15px; border-left: 5px solid #f5576c;'>
            <h4 style='color: #f5576c; margin-top: 0;'>🚨 Prioritas Tinggi</h4>
            <p style='color: #4a5568; margin: 0;'>
                <strong>{len(high_prev_kec)} kecamatan</strong> dengan prevalensi ≥40% memerlukan:
            </p>
            <ul style='color: #4a5568; margin: 0.5rem 0;'>
                <li>Intervensi gizi intensif</li>
                <li>Program PMT segera</li>
                <li>Monitoring mingguan</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_rec2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #feca5715 0%, #feca5705 100%);
                    padding: 1.5rem; border-radius: 15px; border-left: 5px solid #feca57;'>
            <h4 style='color: #feca57; margin-top: 0;'>⚠️ Prioritas Sedang</h4>
            <p style='color: #4a5568; margin: 0;'>
                <strong>{len(medium_prev_kec)} kecamatan</strong> dengan prevalensi 20-40% perlu:
            </p>
            <ul style='color: #4a5568; margin: 0.5rem 0;'>
                <li>Edukasi gizi keluarga</li>
                <li>Pemantauan rutin</li>
                <li>Program pencegahan</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ===============================
# FOOTER dengan Credits
# ===============================
st.markdown("""
<div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px; color: white; margin-top: 2rem;'>
    <h3 style='margin: 0; color: white;'>📊 Dashboard Stunting Kabupaten Sidoarjo</h3>
    <p style='margin: 0.5rem 0; opacity: 0.9;'>Monitoring & Evaluasi Kesehatan Balita Berkelanjutan</p>
    <p style='margin: 0; font-size: 0.9rem; opacity: 0.8;'>© 2025 Dinas Kesehatan Kabupaten Sidoarjo</p>
</div>
""", unsafe_allow_html=True)
