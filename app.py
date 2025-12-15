import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px

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

    # Normalisasi nama kecamatan (INI KUNCI MAP MUNCUL)
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

df = df[df["umur_balita"].isin(umur_pilih)]

# ===============================
# KPI
# ===============================
total_balita = len(df)
total_kasus = int(df["is_stunting"].sum())
prevalensi = (total_kasus / total_balita * 100) if total_balita > 0 else 0

st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")

c1, c2, c3 = st.columns(3)
c1.metric("👶 Total Balita", total_balita)
c2.metric("🚨 Kasus Stunting", total_kasus)
c3.metric("📉 Prevalensi", f"{prevalensi:.2f}%")

st.divider()

# ===============================
# AGREGASI KECAMATAN
# ===============================
kec_df = (
    df.groupby("nama_kecamatan")
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
# MAP (PASTI MUNCUL)
# ===============================
st.subheader("🗺️ Peta Prevalensi Stunting per Kecamatan")

fig_map = px.choropleth(
    kec_df,
    geojson=geojson,
    locations="nama_kecamatan",
    featureidkey="properties.NAMOBJ",
    color="prevalensi",
    color_continuous_scale="Reds",
    range_color=(0, kec_df["prevalensi"].max() if len(kec_df) > 0 else 1),
    hover_name="nama_kecamatan",
    hover_data={
        "total_balita": True,
        "total_kasus": True,
        "prevalensi": ":.2f"
    }
)

fig_map.update_geos(
    fitbounds="locations",
    visible=False
)

fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig_map, use_container_width=True)

# ===============================
# BAR CHART KECAMATAN
# ===============================
st.subheader("📍 Top Kecamatan dengan Prevalensi Tertinggi")

fig_bar = px.bar(
    kec_df.sort_values("prevalensi", ascending=False).head(10),
    x="prevalensi",
    y="nama_kecamatan",
    orientation="h",
    text=kec_df.sort_values("prevalensi", ascending=False)
        .head(10)["prevalensi"].round(2).astype(str) + "%"
)

fig_bar.update_layout(
    xaxis_title="Prevalensi (%)",
    yaxis_title="Kecamatan"
)

st.plotly_chart(fig_bar, use_container_width=True)

# ===============================
# DEBUG (AMAN DIHAPUS NANTI)
# ===============================
with st.expander("🧪 Debug Data"):
    st.write("Jumlah baris:", len(df))
    st.dataframe(kec_df.head())
