import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Stunting Kabupaten Sidoarjo",
    layout="wide"
)

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
    # Normalisasi nama kecamatan
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
    # Normalisasi NAMOBJ
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
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

# FILTER UMUR
umur_opsi = sorted(df["umur_balita"].dropna().unique())
umur_pilih = st.sidebar.multiselect(
    "Pilih Umur Balita",
    umur_opsi,
    default=umur_opsi
)
df_filtered = df[df["umur_balita"].isin(umur_pilih)]

# ===============================
# KPI
# ===============================
total_balita = len(df_filtered)
total_kasus = int(df_filtered["is_stunting"].sum())
prevalensi = (total_kasus / total_balita * 100) if total_balita > 0 else 0

st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")
c1, c2, c3 = st.columns(3)
c1.metric("👶 Total Balita", f"{total_balita:,}")
c2.metric("🚨 Kasus Stunting", f"{total_kasus:,}")
c3.metric("📉 Prevalensi", f"{prevalensi:.2f}%")
st.divider()

# ===============================
# AGREGASI KECAMATAN
# ===============================
kec_df = (
    df_filtered.groupby("nama_kecamatan")
    .agg(
        total_balita=("is_stunting", "count"),
        total_kasus=("is_stunting", "sum")
    )
    .reset_index()
)
kec_df["prevalensi"] = (
    kec_df["total_kasus"] / kec_df["total_balita"] * 100
)

# ===============================
# MAP MENGGUNAKAN CHOROPLETH_MAPBOX (LEBIH BAGUS!)
# ===============================
st.subheader("🗺️ Peta Prevalensi Stunting per Kecamatan")

# Buat peta dengan mapbox (lebih bagus dari choropleth biasa)
fig_map = px.choropleth_mapbox(
    kec_df,
    geojson=geojson,
    locations="nama_kecamatan",
    featureidkey="properties.NAMOBJ",
    color="prevalensi",
    color_continuous_scale="Reds",
    range_color=(0, kec_df["prevalensi"].max() if len(kec_df) > 0 else 100),
    mapbox_style="carto-positron",
    center={"lat": -7.45, "lon": 112.71},  # Koordinat Sidoarjo
    zoom=10,
    opacity=0.7,
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
    height=600,
    coloraxis_colorbar={
        "title": "Prevalensi<br>Stunting (%)",
        "thickness": 15,
        "len": 0.7,
        "x": 1.02
    }
)

st.plotly_chart(fig_map, use_container_width=True)

# ===============================
# LAYOUT 2 KOLOM: BAR CHART & TOP 5
# ===============================
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Top 10 Kecamatan dengan Prevalensi Tertinggi")
    
    top10 = kec_df.sort_values("prevalensi", ascending=False).head(10)
    
    fig_bar = px.bar(
        top10,
        x="prevalensi",
        y="nama_kecamatan",
        orientation="h",
        text=top10["prevalensi"].round(2).astype(str) + "%",
        color="prevalensi",
        color_continuous_scale="Reds"
    )
    
    fig_bar.update_traces(
        textposition="outside",
        textfont_size=12
    )
    
    fig_bar.update_layout(
        xaxis_title="Prevalensi (%)",
        yaxis_title="",
        showlegend=False,
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("🏆 Top 5 Kecamatan")
    
    top5 = kec_df.sort_values("prevalensi", ascending=False).head(5)
    
    for i, (idx, row) in enumerate(top5.iterrows(), 1):
        # Tentukan warna berdasarkan ranking
        if i == 1:
            border_color = "#dc2626"  # Merah tua
            bg_color = "#fee2e2"
        elif i == 2:
            border_color = "#ea580c"  # Orange
            bg_color = "#ffedd5"
        elif i == 3:
            border_color = "#f59e0b"  # Kuning
            bg_color = "#fef3c7"
        else:
            border_color = "#f97316"
            bg_color = "#fff7ed"
        
        st.markdown(f"""
        <div style="
            background-color: {bg_color};
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 5px solid {border_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="flex: 1;">
                    <div style="font-size: 14px; color: #666; font-weight: 600;">
                        #{i} {row['nama_kecamatan']}
                    </div>
                    <div style="font-size: 32px; color: {border_color}; font-weight: bold; margin: 8px 0;">
                        {row['prevalensi']:.2f}%
                    </div>
                    <div style="font-size: 13px; color: #666;">
                        {row['total_kasus']:,} dari {row['total_balita']:,} balita
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ===============================
# STATISTIK TAMBAHAN
# ===============================
st.subheader("📊 Statistik Prevalensi")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    st.metric(
        "Rata-rata Prevalensi",
        f"{kec_df['prevalensi'].mean():.2f}%"
    )

with stat_col2:
    st.metric(
        "Median Prevalensi",
        f"{kec_df['prevalensi'].median():.2f}%"
    )

with stat_col3:
    st.metric(
        "Prevalensi Tertinggi",
        f"{kec_df['prevalensi'].max():.2f}%"
    )

with stat_col4:
    st.metric(
        "Prevalensi Terendah",
        f"{kec_df['prevalensi'].min():.2f}%"
    )

# ===============================
# TABEL DATA DENGAN GRADIENT (TANPA MATPLOTLIB)
# ===============================
with st.expander("📋 Lihat Data Lengkap per Kecamatan"):
    kec_sorted = kec_df.sort_values("prevalensi", ascending=False).reset_index(drop=True)
    
    # Buat HTML table dengan gradient
    max_prev = kec_sorted["prevalensi"].max()
    min_prev = kec_sorted["prevalensi"].min()
    
    html_table = """
    <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Source Sans Pro', sans-serif;
        }
        .custom-table th {
            background-color: #f0f2f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }
        .custom-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }
        .custom-table tr:hover {
            background-color: #f9fafb;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 5%;">Rank</th>
                <th style="width: 35%;">Kecamatan</th>
                <th style="width: 20%;">Total Balita</th>
                <th style="width: 20%;">Kasus Stunting</th>
                <th style="width: 20%;">Prevalensi</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for idx, row in kec_sorted.iterrows():
        # Hitung intensitas warna berdasarkan prevalensi
        if max_prev > min_prev:
            intensity = (row["prevalensi"] - min_prev) / (max_prev - min_prev)
        else:
            intensity = 0.5
        
        # Warna gradient dari putih ke merah
        red = 255
        green = int(255 * (1 - intensity * 0.8))
        blue = int(255 * (1 - intensity * 0.8))
        bg_color = f"rgb({red}, {green}, {blue})"
        
        html_table += f"""
        <tr>
            <td style="text-align: center; font-weight: 600;">#{idx + 1}</td>
            <td><strong>{row['nama_kecamatan']}</strong></td>
            <td style="text-align: right;">{row['total_balita']:,}</td>
            <td style="text-align: right;">{row['total_kasus']:,}</td>
            <td style="text-align: right; background-color: {bg_color}; font-weight: 600;">
                {row['prevalensi']:.2f}%
            </td>
        </tr>
        """
    
    html_table += """
        </tbody>
    </table>
    """
    
    st.markdown(html_table, unsafe_allow_html=True)

# ===============================
# DEBUG
# ===============================
with st.expander("🧪 Debug Data"):
    st.write("**Jumlah baris data:**", len(df_filtered))
    st.write("**Jumlah kecamatan:**", len(kec_df))
    st.write("**Preview data agregasi:**")
    st.dataframe(kec_df.head(10))
