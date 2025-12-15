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

# FILTER KECAMATAN
kecamatan_opsi = sorted(df["nama_kecamatan"].unique())
kecamatan_pilih = st.sidebar.multiselect(
    "📍 Pilih Kecamatan",
    kecamatan_opsi,
    default=kecamatan_opsi
)

# FILTER UMUR
umur_opsi = sorted(df["umur_balita"].dropna().unique())
umur_pilih = st.sidebar.multiselect(
    "👶 Pilih Umur Balita",
    umur_opsi,
    default=umur_opsi
)

# Terapkan filter
df_filtered = df[
    (df["nama_kecamatan"].isin(kecamatan_pilih)) &
    (df["umur_balita"].isin(umur_pilih))
]

# Info jumlah data terfilter
st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(df_filtered):,}** data balita terfilter dari **{len(df):,}** total data")

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
# MAP DENGAN STYLE SEPERTI GOOGLE MAPS
# ===============================
st.subheader("🗺️ Peta Prevalensi Stunting per Kecamatan")

# Kontrol peta di atas
col_style, col_color, col_zoom = st.columns([2, 2, 1])

with col_style:
    map_style = st.selectbox(
        "🗺️ Style Peta:",
        [
            "Default (Light)", 
            "Default (Dark)",
            "Street Map",
            "Outdoor/Topografi",
            "Minimalis",
            "Stamen Terrain",
            "Stamen Toner"
        ],
        index=0
    )
    
    # Mapping ke mapbox style (semua gratis, tanpa perlu token)
    style_mapping = {
        "Default (Light)": "carto-positron",
        "Default (Dark)": "carto-darkmatter",
        "Street Map": "open-street-map",
        "Outdoor/Topografi": "stamen-terrain",
        "Minimalis": "basic",
        "Stamen Terrain": "stamen-terrain",
        "Stamen Toner": "stamen-toner"
    }
    mapbox_style = style_mapping[map_style]

with col_color:
    color_scheme = st.selectbox(
        "🎨 Skema Warna:",
        ["RdYlGn_r", "Turbo", "Jet", "Hot", "Rainbow", "Portland", "Picnic", "Reds"],
        index=0
    )

with col_zoom:
    zoom_level = st.slider(
        "🔍 Zoom:",
        min_value=8,
        max_value=13,
        value=10,
        step=1
    )

# Buat peta dengan style yang dipilih
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
    height=600,
    coloraxis_colorbar={
        "title": "Prevalensi<br>Stunting (%)",
        "thickness": 20,
        "len": 0.7,
        "x": 1.02,
        "tickvals": [0, 20, 40, 60, 80, 100],
        "ticktext": ["0%", "20%", "40%", "60%", "80%", "100%"]
    }
)

st.plotly_chart(fig_map, use_container_width=True)

# Info style peta
if map_style == "Default (Dark)":
    st.info("🌙 **Mode Gelap**: Cocok untuk presentasi atau tampilan malam")
elif map_style in ["Outdoor/Topografi", "Stamen Terrain"]:
    st.info("🏞️ **Mode Topografi**: Menampilkan kontur dan ketinggian medan")
elif map_style == "Stamen Toner":
    st.info("🖋️ **Mode Toner**: Tampilan hitam-putih dengan detail tinggi")

# Keterangan warna
st.markdown("""
<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;">
    <strong>📌 Keterangan Prevalensi:</strong><br>
    • <span style="color: #d73027; font-weight: bold;">Merah Tua</span>: Sangat Tinggi (≥80%)<br>
    • <span style="color: #fc8d59; font-weight: bold;">Orange</span>: Tinggi (60-79%)<br>
    • <span style="color: #fee08b; font-weight: bold;">Kuning</span>: Sedang (40-59%)<br>
    • <span style="color: #d9ef8b; font-weight: bold;">Hijau Muda</span>: Rendah (20-39%)<br>
    • <span style="color: #1a9850; font-weight: bold;">Hijau Tua</span>: Sangat Rendah (<20%)
</div>
""", unsafe_allow_html=True)

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
# TABEL DATA LENGKAP
# ===============================
with st.expander("📋 Lihat Data Lengkap per Kecamatan"):
    kec_sorted = kec_df.sort_values("prevalensi", ascending=False).reset_index(drop=True)
    
    # Tambahkan kolom ranking
    kec_sorted.insert(0, "Rank", range(1, len(kec_sorted) + 1))
    
    # Format kolom untuk tampilan
    kec_display = kec_sorted.copy()
    kec_display["Rank"] = kec_display["Rank"].apply(lambda x: f"#{x}")
    kec_display["prevalensi_display"] = kec_display["prevalensi"].apply(lambda x: f"{x:.2f}%")
    
    # Buat dataframe untuk ditampilkan
    display_df = pd.DataFrame({
        "Rank": kec_display["Rank"],
        "Kecamatan": kec_display["nama_kecamatan"],
        "Total Balita": kec_display["total_balita"],
        "Kasus Stunting": kec_display["total_kasus"],
        "Prevalensi": kec_display["prevalensi_display"]
    })
    
    # Tampilkan dengan st.dataframe (lebih reliable)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.TextColumn(
                "Rank",
                width="small"
            ),
            "Kecamatan": st.column_config.TextColumn(
                "Kecamatan",
                width="medium"
            ),
            "Total Balita": st.column_config.NumberColumn(
                "Total Balita",
                format="%d"
            ),
            "Kasus Stunting": st.column_config.NumberColumn(
                "Kasus Stunting",
                format="%d"
            ),
            "Prevalensi": st.column_config.TextColumn(
                "Prevalensi",
                width="small"
            )
        }
    )
    
    # Tambahkan visualisasi mini untuk setiap kecamatan
    st.markdown("---")
    st.markdown("**📊 Detail per Kecamatan:**")
    
    cols = st.columns(3)
    for idx, row in kec_sorted.iterrows():
        with cols[idx % 3]:
            # Tentukan warna berdasarkan prevalensi
            if row["prevalensi"] >= 80:
                color = "🔴"
            elif row["prevalensi"] >= 60:
                color = "🟠"
            elif row["prevalensi"] >= 40:
                color = "🟡"
            else:
                color = "🟢"
            
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 10px;
                border-left: 3px solid #dee2e6;
            ">
                <div style="font-size: 12px; color: #666;">
                    {color} <strong>{row['nama_kecamatan']}</strong>
                </div>
                <div style="font-size: 20px; font-weight: bold; color: #dc3545; margin: 5px 0;">
                    {row['prevalensi']:.2f}%
                </div>
                <div style="font-size: 11px; color: #888;">
                    {row['total_kasus']:,} / {row['total_balita']:,} balita
                </div>
            </div>
            """, unsafe_allow_html=True)

# ===============================
# DEBUG
# ===============================
with st.expander("🧪 Debug Data"):
    st.write("**Jumlah baris data:**", len(df_filtered))
    st.write("**Jumlah kecamatan:**", len(kec_df))
    st.write("**Preview data agregasi:**")
    st.dataframe(kec_df.head(10))
