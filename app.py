# =====================================================
# STREAMLIT DASHBOARD STUNTING SIDOARJO
# TANPA GEOPANDAS
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
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

st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")

# -----------------------------------------------------
# LOAD DATA
# -----------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data_skrinning_stunting(1).csv")
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df["nama_kecamatan"] = df["nama_kecamatan"].str.upper()
    return df

@st.cache_data
def load_geojson():
    with open("kecamatan_sidoarjo.geojson", "r", encoding="utf-8") as f:
        geojson = json.load(f)
    return geojson

df = load_data()
geojson = load_geojson()

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
        return "0–12 Bulan"
    elif total <= 24:
        return "13–24 Bulan"
    elif total <= 36:
        return "25–36 Bulan"
    else:
        return "37–60 Bulan"

df["kelompok_umur"] = df["umur_balita"].apply(kategori_umur)

# -----------------------------------------------------
# SIDEBAR FILTER
# -----------------------------------------------------
st.sidebar.header("🔎 Filter Data")

kec_filter = st.sidebar.selectbox(
    "Pilih Kecamatan",
    ["Semua"] + sorted(df["nama_kecamatan"].unique())
)

umur_filter = st.sidebar.multiselect(
    "Pilih Kelompok Umur",
    sorted(df["kelompok_umur"].unique()),
    default=sorted(df["kelompok_umur"].unique())
)

if kec_filter != "Semua":
    df = df[df["nama_kecamatan"] == kec_filter]

df = df[df["kelompok_umur"].isin(umur_filter)]

# -----------------------------------------------------
# KPI
# -----------------------------------------------------
total = len(df)
kasus = df["is_stunting"].sum()
prev = (kasus / total * 100) if total else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Balita", total)
c2.metric("Kasus Stunting", kasus)
c3.metric("Prevalensi", f"{prev:.2f}%")

# -----------------------------------------------------
# AGREGASI KECAMATAN
# -----------------------------------------------------
kec_df = (
    df.groupby("nama_kecamatan")["is_stunting"]
    .agg(total_kasus="sum", total_balita="count")
    .reset_index()
)
kec_df["prevalensi"] = kec_df["total_kasus"] / kec_df["total_balita"] * 100

# -----------------------------------------------------
# CHOROPLETH MAP (TANPA GEOPANDAS)
# -----------------------------------------------------
fig_map = px.choropleth(
    kec_df,
    geojson=geojson,
    locations="nama_kecamatan",
    featureidkey="properties.NAMOBJ",
    color="prevalensi",
    color_continuous_scale="Reds",
    hover_data=["total_kasus", "total_balita"],
    title="🗺️ Peta Prevalensi Stunting per Kecamatan"
)

fig_map.update_geos(fitbounds="locations", visible=False)

# -----------------------------------------------------
# BAR UMUR
# -----------------------------------------------------
umur_df = (
    df.groupby("kelompok_umur")["is_stunting"]
    .mean()
    .reset_index()
)
umur_df["prevalensi"] = umur_df["is_stunting"] * 100

fig_umur = px.bar(
    umur_df,
    x="kelompok_umur",
    y="prevalensi",
    title="📊 Prevalensi Stunting Berdasarkan Umur",
    text=umur_df["prevalensi"].round(1)
)

# ---------------------------------------------------

