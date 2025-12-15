# =====================================================
# STREAMLIT DASHBOARD & PETA INTERAKTIF STUNTING
# KABUPATEN SIDOARJO
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import json
import plotly.express as px

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Dashboard Stunting Sidoarjo",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Dashboard Kecerdasan Bisnis & Peta Interaktif Stunting")
st.markdown("**Kabupaten Sidoarjo**")

# -----------------------------------------------------
# LOAD DATA
# -----------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data_skrinning_stunting(1).csv")
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace(".", "")
    return df

@st.cache_data
def load_geojson():
    gdf = gpd.read_file("kecamatan_sidoarjo (1).geojson")
    gdf.columns = gdf.columns.str.lower().str.replace(" ", "_")
    if "namobj" in gdf.columns:
        gdf = gdf.rename(columns={"namobj": "nama_kecamatan"})
    gdf["nama_kecamatan"] = gdf["nama_kecamatan"].str.upper()
    return gdf

df = load_data()
gdf = load_geojson()

# -----------------------------------------------------
# FEATURE ENGINEERING
# -----------------------------------------------------
df["is_stunting"] = df["stunting_balita"].apply(lambda x: 1 if x == "Ya" else 0)

def kategori_umur(umur):
    if pd.isna(umur):
        return "Tidak diketahui"
    tahun, bulan = 0, 0
    parts = umur.split()
    for i, p in enumerate(parts):
        if p.isdigit() and i + 1 < len(parts):
            if parts[i+1].lower() == "tahun":
                tahun = int(p)
            elif parts[i+1].lower() == "bulan":
                bulan = int(p)
    total = tahun * 12 + bulan
    if total <= 12:
        return "A. 0–12 Bulan"
    elif total <= 24:
        return "B. 13–24 Bulan (Kritis)"
    elif total <= 36:
        return "C. 25–36 Bulan"
    elif total <= 60:
        return "D. 37–60 Bulan"
    else:
        return "E. > 60 Bulan"

df["kelompok_umur"] = df["umur_balita"].apply(kategori_umur)
df.dropna(subset=["nama_kecamatan", "stunting_balita"], inplace=True)
df["nama_kecamatan"] = df["nama_kecamatan"].str.upper()

# -----------------------------------------------------
# FILTER SIDEBAR
# -----------------------------------------------------
st.sidebar.header("🔎 Filter Data")

# Filter Kecamatan
kec_list = ["Semua"] + sorted(df["nama_kecamatan"].unique())
kec_filter = st.sidebar.selectbox("Pilih Kecamatan", kec_list)

if kec_filter != "Semua":
    df = df[df["nama_kecamatan"] == kec_filter]

# ===== FILTER UMUR (BARU) =====
umur_list = sorted(df["kelompok_umur"].unique())
umur_filter = st.sidebar.multiselect(
    "Pilih Kelompok Umur",
    options=umur_list,
    default=umur_list
)

df = df[df["kelompok_umur"].isin(umur_filter)]

# -----------------------------------------------------
# INFO FILTER AKTIF
# -----------------------------------------------------
st.info(
    f"📌 Filter aktif → Kecamatan: **{kec_filter}**, "
    f"Kelompok Umur: **{', '.join(umur_filter)}**"
)

# -----------------------------------------------------
# KPI
# -----------------------------------------------------
total = len(df)
kasus = df["is_stunting"].sum()
prev = (kasus / total) * 100 if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Balita", total)
col2.metric("Kasus Stunting", kasus)
col3.metric("Prevalensi", f"{prev:.2f}%")

# -----------------------------------------------------
# AGREGASI DATA
# -----------------------------------------------------
kec_df = df.groupby("nama_kecamatan")["is_stunting"].agg(
    total_kasus="sum",
    total_populasi="count"
).reset_index()

kec_df["prevalensi"] = kec_df["total_kasus"] / kec_df["total_populasi"] * 100

umur_df = df.groupby("kelompok_umur")["is_stunting"].agg(
    total_kasus="sum",
    total_populasi="count"
).reset_index()

umur_df["prevalensi"] = umur_df["total_kasus"] / umur_df["total_populasi"] * 100
umur_df = umur_df.sort_values("kelompok_umur")

# -----------------------------------------------------
# MERGE DENGAN PETA
# -----------------------------------------------------
gdf_merge = gdf.merge(kec_df, on="nama_kecamatan", how="left")
gdf_merge[["prevalensi","total_kasus","total_populasi"]] = (
    gdf_merge[["prevalensi","total_kasus","total_populasi"]].fillna(0)
)

geojson = json.loads(gdf_merge.to_json())

# -----------------------------------------------------
# VISUALISASI
# -----------------------------------------------------
fig_map = px.choropleth(
    gdf_merge,
    geojson=geojson,
    locations=gdf_merge.index,
    color="prevalensi",
    hover_name="nama_kecamatan",
    hover_data={"total_kasus": True, "total_populasi": True},
    color_continuous_scale="Reds",
    title="🗺️ Peta Prevalensi Stunting per Kecamatan"
)
fig_map.update_geos(fitbounds="locations", visible=False)

fig_umur = px.bar(
    umur_df,
    x="kelompok_umur",
    y="prevalensi",
    text=umur_df["prevalensi"].round(1),
    color="prevalensi",
    color_continuous_scale="Blues",
    title="📊 Prevalensi Stunting Berdasarkan Kelompok Umur"
)

fig_z = px.scatter(
    df,
    x="zsc_tbu",
    y="zsc_bbu",
    color="stunting_balita",
    hover_data=["nama_kecamatan","umur_balita"],
    title="📈 Diagnostik Z-Score WHO"
)

# -----------------------------------------------------
# DISPLAY DASHBOARD
# -----------------------------------------------------
st.plotly_chart(fig_map, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(fig_umur, use_container_width=True)
with col_b:
    st.plotly_chart(fig_z, use_container_width=True)

st.markdown("---")
st.markdown("### 📌 Insight Singkat")
st.write(
    f"""
    • Prevalensi stunting saat ini **{prev:.2f}%**  
    • Fokus intervensi pada kecamatan berisiko tinggi  
    • Usia **13–24 bulan** merupakan fase paling kritis  
    """
)
