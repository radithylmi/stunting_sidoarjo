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
# CUSTOM PAGE STYLING
# ===============================
st.markdown(
    """
    <style>
    /* Global background */
    .stApp {
        background: linear-gradient(135deg, #f9fafb 0%, #eff6ff 50%, #fdf2f8 100%);
    }
    /* Cards */
    .metric-card {
        padding: 16px 20px;
        border-radius: 14px;
        background-color: rgba(255,255,255,0.9);
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(226, 232, 240, 0.9);
    }
    .metric-title {
        font-size: 13px;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: .05em;
    }
    .metric-value {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 11px;
        color: #9ca3af;
        margin-top: 2px;
    }
    .section-title {
        font-weight: 800 !important;
        letter-spacing: .06em;
        text-transform: uppercase;
        font-size: 12px !important;
        color: #6b7280 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

# FILTER JENIS KELAMIN (JIKA ADA)
jk_pilih = None
if "jenis_kelamin_balita" in df.columns:
    jk_opsi = sorted(df["jenis_kelamin_balita"].dropna().unique())
    jk_pilih = st.sidebar.multiselect(
        "🚻 Jenis Kelamin",
        jk_opsi,
        default=jk_opsi
    )

# Mode tampilan angka (bisa kamu pakai di beberapa grafik kalau mau beda)
display_mode = st.sidebar.radio(
    "📈 Mode Tampilan Angka",
    ("Persentase", "Jumlah Absolut"),
    horizontal=True
)

# Terapkan filter
mask = (
    df["nama_kecamatan"].isin(kecamatan_pilih) &
    df["umur_balita"].isin(umur_pilih)
)
if jk_pilih is not None:
    mask &= df["jenis_kelamin_balita"].isin(jk_pilih)

df_filtered = df[mask]

# Info jumlah data terfilter
st.sidebar.markdown("---")
st.sidebar.info(f"📊 **{len(df_filtered):,}** data balita terfilter dari **{len(df):,}** total data")

# ===============================
# MAIN TITLE
# ===============================
col_title, col_desc = st.columns([2, 3])
with col_title:
    st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")
with col_desc:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-title">RINGKASAN</div>
            <div style="font-size:13px; color:#4b5563; margin-top:4px;">
                Dashboard ini menampilkan hasil skrining stunting balita di Kabupaten Sidoarjo.
                Gunakan filter di sisi kiri untuk melakukan eksplorasi interaktif per kecamatan, umur, dan jenis kelamin.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ===============================
# KPI CARDS
# ===============================
total_balita = len(df_filtered)
total_kasus = int(df_filtered["is_stunting"].sum())
prevalensi = (total_kasus / total_balita * 100) if total_balita > 0 else 0

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL BALITA TERSKRINING</div>
            <div class="metric-value">{total_balita:,}</div>
            <div class="metric-sub">Setelah filter diterapkan</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">KASUS STUNTING</div>
            <div class="metric-value">{total_kasus:,}</div>
            <div class="metric-sub">Balita dengan status stunting</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">PREVALENSI STUNTING</div>
            <div class="metric-value">{prevalensi:.2f}%</div>
            <div class="metric-sub">Dari total balita terskrining</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ===============================
# GAUGE CHART - KPI PREVALENSI
# ===============================
st.markdown('<p class="section-title">KPI UTAMA</p>', unsafe_allow_html=True)
st.subheader("🎯 Prevalensi Stunting vs Target Nasional")

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=prevalensi,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Prevalensi Stunting", 'font': {'size': 20}},
    number={'suffix': "%", 'font': {'size': 40}},
    delta={
        'reference': 14,  # contoh target nasional 14%
        'increasing': {'color': "red"},
        'decreasing': {'color': "green"}
    },
    gauge={
        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkblue"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 10], 'color': '#1a9850'},
            {'range': [10, 20], 'color': '#91cf60'},
            {'range': [20, 30], 'color': '#d9ef8b'},
            {'range': [30, 40], 'color': '#fee08b'},
            {'range': [40, 60], 'color': '#fc8d59'},
            {'range': [60, 100], 'color': '#d73027'}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 14
        }
    }
))

fig_gauge.update_layout(
    height=330,
    margin=dict(l=20, r=20, t=60, b=10),
    paper_bgcolor="white"
)

st.plotly_chart(fig_gauge, use_container_width=True, key="gauge_chart_main")

with st.expander("ℹ️ Penjelasan Indikator Prevalensi"):
    st.write(
        """
        - **Jarum** menunjukkan prevalensi stunting berdasarkan filter yang sedang aktif.
        - **Delta (%)** membandingkan dengan target acuan (misal target nasional 14%).
        - Warna latar gauge menunjukkan level risiko:
            - Hijau: rendah
            - Kuning: sedang
            - Merah: tinggi
        """
    )

st.divider()

# ===============================
# AGREGASI DATA
# ===============================

# AGREGASI PER KECAMATAN
kec_df = df_filtered.groupby("nama_kecamatan").agg(
    total_balita=("is_stunting", "count"),
    total_kasus=("is_stunting", "sum")
).reset_index()

kec_df["prevalensi"] = (kec_df["total_kasus"] / kec_df["total_balita"] * 100)

# AGREGASI PER KELOMPOK UMUR
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

# Filter out "Unknown" jika ada
age_df = age_df[age_df["kelompok_umur"] != "Unknown"]

age_df["prevalensi"] = (age_df["total_kasus"] / age_df["total_balita"] * 100)

age_order = ["0-12 Bulan", "13-24 Bulan", "25-36 Bulan", "37-60 Bulan"]
age_df["kelompok_umur"] = pd.Categorical(age_df["kelompok_umur"], categories=age_order, ordered=True)
age_df = age_df.sort_values("kelompok_umur")

# ===============================
# TAB NAVIGATION
# ===============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Peta Prevalensi",
    "📊 Kelompok Umur", 
    "🏆 Ranking Kecamatan",
    "🔬 Diagnostik Z-Score",
    "📋 Data Lengkap"
])

# ===============================
# TAB 1: PETA PREVALENSI
# ===============================
with tab1:
    st.subheader("🗺️ Peta Prevalensi Stunting per Kecamatan")

    col_style, col_color, col_metric, col_zoom = st.columns([2, 2, 2, 1])

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
            index=0,
            key="map_style_tab1"
        )
        
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
            index=0,
            key="color_scheme_tab1"
        )

    with col_metric:
        map_metric = st.selectbox(
            "📌 Warna berdasarkan:",
            ["Prevalensi (%)", "Jumlah Kasus", "Total Balita"],
            index=0,
            key="metric_map_tab1"
        )

    with col_zoom:
        zoom_level = st.slider(
            "🔍 Zoom:",
            min_value=8,
            max_value=13,
            value=10,
            step=1,
            key="zoom_tab1"
        )

    if map_metric == "Prevalensi (%)":
        color_col = "prevalensi"
        color_label = "Prevalensi (%)"
        range_color = (0, 100)
    elif map_metric == "Jumlah Kasus":
        color_col = "total_kasus"
        color_label = "Jumlah Kasus"
        range_color = (0, int(max(10, kec_df["total_kasus"].max() if len(kec_df) else 0)))
    else:
        color_col = "total_balita"
        color_label = "Total Balita"
        range_color = (0, int(max(10, kec_df["total_balita"].max() if len(kec_df) else 0)))

    fig_map = px.choropleth_mapbox(
        kec_df,
        geojson=geojson,
        locations="nama_kecamatan",
        featureidkey="properties.NAMOBJ",
        color=color_col,
        color_continuous_scale=color_scheme,
        range_color=range_color,
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

    colorbar = {
        "title": color_label,
        "thickness": 20,
        "len": 0.7,
        "x": 1.02
    }
    if map_metric == "Prevalensi (%)":
        colorbar["tickvals"] = [0, 20, 40, 60, 80, 100]
        colorbar["ticktext"] = ["0%", "20%", "40%", "60%", "80%", "100%"]

    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600,
        coloraxis_colorbar=colorbar
    )

    st.plotly_chart(fig_map, use_container_width=True, key="map_chart_tab1")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("""
        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin-top: 10px; border: 1px solid #e5e7eb;">
            <strong>📌 Tips Interaksi:</strong><br>
            • Arahkan kursor ke kecamatan untuk melihat detail angka.<br>
            • Ubah <em>Skema Warna</em> dan <em>Style Peta</em> untuk tampilan berbeda.<br>
            • Gunakan filter di kiri untuk fokus pada kelompok tertentu.
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        kec_focus = st.selectbox(
            "🎯 Fokus kecamatan:",
            ["(Semua)"] + kecamatan_opsi,
            key="focus_kec_tab1"
        )
        if kec_focus != "(Semua)" and kec_focus in kec_df["nama_kecamatan"].values:
            row = kec_df[kec_df["nama_kecamatan"] == kec_focus].iloc[0]
            st.markdown(f"""
            <div style="
                background-color: #eef2ff;
                padding: 12px;
                border-radius: 10px;
                margin-top: 10px;
                border-left: 4px solid #4f46e5;
            ">
                <div style="font-size: 13px; color: #4b5563; font-weight: 600;">
                    {row['nama_kecamatan']}
                </div>
                <div style="font-size: 24px; color: #4f46e5; font-weight: bold; margin: 5px 0;">
                    {row['prevalensi']:.2f}% prevalensi
                </div>
                <div style="font-size: 12px; color: #6b7280;">
                    {int(row['total_kasus']):,} kasus dari {int(row['total_balita']):,} balita terskrining
                </div>
            </div>
            """, unsafe_allow_html=True)

# ===============================
# TAB 2: KELOMPOK UMUR
# ===============================
with tab2:
    st.subheader("📊 Fase Kritis: Prevalensi Berdasarkan Kelompok Umur")
    
    if len(age_df) > 0:
        col_top, _ = st.columns([2, 1])
        with col_top:
            metric_age = st.radio(
                "Tampilkan indikator:",
                ["Prevalensi (%)", "Jumlah Kasus", "Total Balita"],
                horizontal=True,
                key="metric_age_tab2"
            )

        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            if metric_age == "Prevalensi (%)":
                y_col = "prevalensi"
                y_title = "Prevalensi Stunting (%)"
                text_vals = age_df["prevalensi"].round(1).astype(str) + "%"
            elif metric_age == "Jumlah Kasus":
                y_col = "total_kasus"
                y_title = "Jumlah Kasus Stunting"
                text_vals = age_df["total_kasus"].astype(int).astype(str)
            else:
                y_col = "total_balita"
                y_title = "Jumlah Balita Terskrining"
                text_vals = age_df["total_balita"].astype(int).astype(str)

            fig_age = px.bar(
                age_df,
                x="kelompok_umur",
                y=y_col,
                text=text_vals,
                color="prevalensi",
                color_continuous_scale="Plasma",
                labels={
                    "kelompok_umur": "Kelompok Umur",
                    y_col: y_title
                }
            )

            fig_age.update_traces(
                textposition="outside",
                textfont_size=14
            )

            layout_args = dict(
                height=500,
                showlegend=False,
            )
            if metric_age == "Prevalensi (%)":
                layout_args["yaxis_range"] = [0, age_df["prevalensi"].max() * 1.15]

            fig_age.update_layout(**layout_args)

            st.plotly_chart(fig_age, use_container_width=True, key="age_chart_tab2")
        
        with col_table:
            st.markdown("#### 📋 Detail Data")
            for _, row in age_df.iterrows():
                st.markdown(f"""
                <div style="
                    background-color: #f8f9fa;
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-left: 4px solid #6366f1;
                ">
                    <div style="font-size: 13px; color: #666; font-weight: 600;">
                        {row['kelompok_umur']}
                    </div>
                    <div style="font-size: 24px; color: #6366f1; font-weight: bold; margin: 5px 0;">
                        {row['prevalensi']:.1f}% prevalensi
                    </div>
                    <div style="font-size: 12px; color: #888;">
                        {int(row['total_kasus']):,} / {int(row['total_balita']):,} balita
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("💡 Insight")
        
        max_idx = age_df["prevalensi"].idxmax()
        max_age_group = age_df.loc[max_idx, "kelompok_umur"]
        max_prevalensi = age_df.loc[max_idx, "prevalensi"]
        
        min_idx = age_df["prevalensi"].idxmin()
        min_age_group = age_df.loc[min_idx, "kelompok_umur"]
        min_prevalensi = age_df.loc[min_idx, "prevalensi"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.error(f"🔴 **Kelompok Tertinggi:** {max_age_group} ({max_prevalensi:.1f}%)")
        with col2:
            st.success(f"🟢 **Kelompok Terendah:** {min_age_group} ({min_prevalensi:.1f}%)")
    else:
        st.warning("⚠️ Tidak ada data untuk ditampilkan. Silakan sesuaikan filter.")

# ===============================
# TAB 3: RANKING KECAMATAN
# ===============================
with tab3:
    st.subheader("🏆 Ranking Kecamatan Berdasarkan Prevalensi")
    
    col_top3 = st.columns([2, 2, 2])
    with col_top3[0]:
        top_n = st.radio(
            "Tampilkan:",
            ["Top 5", "Top 10", "Top 15", "Semua Kecamatan"],
            horizontal=True,
            key="top_n_radio"
        )
    with col_top3[1]:
        sort_by = st.selectbox(
            "Urutkan berdasarkan:",
            ["Prevalensi", "Jumlah Kasus", "Total Balita"],
            key="sort_by_tab3"
        )
    with col_top3[2]:
        search_kec = st.text_input(
            "🔍 Cari nama kecamatan (opsional)",
            "",
            key="search_kec_tab3"
        )
    
    # Tentukan jumlah data
    if top_n == "Top 5":
        n = 5
    elif top_n == "Top 10":
        n = 10
    elif top_n == "Top 15":
        n = 15
    else:
        n = len(kec_df)
    
    df_rank = kec_df.copy()
    if search_kec:
        df_rank = df_rank[df_rank["nama_kecamatan"].str.contains(search_kec.upper(), na=False)]
    
    if sort_by == "Prevalensi":
        df_rank = df_rank.sort_values("prevalensi", ascending=False)
        x_col = "prevalensi"
        x_label = "Prevalensi (%)"
    elif sort_by == "Jumlah Kasus":
        df_rank = df_rank.sort_values("total_kasus", ascending=False)
        x_col = "total_kasus"
        x_label = "Jumlah Kasus"
    else:
        df_rank = df_rank.sort_values("total_balita", ascending=False)
        x_col = "total_balita"
        x_label = "Total Balita"

    top_data = df_rank.head(n)
    
    col_chart, col_cards = st.columns([2, 1])
    
    with col_chart:
        fig_bar_rank = px.bar(
            top_data,
            x=x_col,
            y="nama_kecamatan",
            orientation="h",
            text=top_data[x_col].round(2).astype(str),
            color="prevalensi",
            color_continuous_scale="Reds",
            labels={x_col: x_label}
        )
        
        fig_bar_rank.update_traces(
            textposition="outside",
            textfont_size=12
        )
        
        fig_bar_rank.update_layout(
            xaxis_title=x_label,
            yaxis_title="",
            showlegend=False,
            height=max(500, n * 40),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_bar_rank, use_container_width=True, key="bar_chart_tab3")
    
    with col_cards:
        st.markdown(f"#### 🎯 Highlight {min(5, len(top_data))} Teratas")
        
        for i, (_, row) in enumerate(top_data.head(5).iterrows(), 1):
            if i == 1:
                border_color = "#dc2626"
                bg_color = "#fee2e2"
            elif i == 2:
                border_color = "#ea580c"
                bg_color = "#ffedd5"
            elif i == 3:
                border_color = "#f59e0b"
                bg_color = "#fef3c7"
            else:
                border_color = "#f97316"
                bg_color = "#fff7ed"
            
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 10px;
                border-left: 5px solid {border_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 12px; color: #666; font-weight: 600;">
                    #{i} {row['nama_kecamatan']}
                </div>
                <div style="font-size: 28px; color: {border_color}; font-weight: bold; margin: 5px 0;">
                    {row['prevalensi']:.2f}% prevalensi
                </div>
                <div style="font-size: 11px; color: #666;">
                    {int(row['total_kasus']):,} kasus dari {int(row['total_balita']):,} balita
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Fokus kecamatan tertentu
        st.markdown("---")
        kec_focus_tab3 = st.selectbox(
            "🔎 Lihat detail kecamatan:",
            ["(Pilih kecamatan)"] + list(kec_df["nama_kecamatan"].sort_values().unique()),
            key="focus_kec_tab3"
        )
        if kec_focus_tab3 != "(Pilih kecamatan)":
            row_f = kec_df[kec_df["nama_kecamatan"] == kec_focus_tab3].iloc[0]
            st.metric(
                f"Prevalensi {kec_focus_tab3}",
                f"{row_f['prevalensi']:.2f}%",
                help=f"{int(row_f['total_kasus']):,} kasus dari {int(row_f['total_balita']):,} balita"
            )
    
    # Statistik
    st.markdown("---")
    st.subheader("📊 Statistik Ringkas")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric(
            f"Rata-rata Prevalensi ({top_n})",
            f"{top_data['prevalensi'].mean():.2f}%"
        )
    
    with stat_col2:
        st.metric(
            "Kecamatan Tertinggi",
            f"{top_data.iloc[0]['nama_kecamatan']}",
            f"{top_data.iloc[0]['prevalensi']:.1f}%"
        )
    
    with stat_col3:
        total_kasus_top = top_data["total_kasus"].sum()
        st.metric(
            f"Total Kasus ({top_n})",
            f"{int(total_kasus_top):,}"
        )

# ===============================
# TAB 4: DIAGNOSTIK Z-SCORE
# ===============================
with tab4:
    st.subheader("🔬 Diagnostik Z-Score (TB/U vs BB/U)")
    
    # Cek kolom z-score - lebih fleksibel
    zscore_cols = [col for col in df_filtered.columns if ('z' in col.lower() or 'score' in col.lower() or 'tb' in col.lower() or 'bb' in col.lower()) and col != 'is_stunting']
    
    if len(zscore_cols) >= 2:
        col_z1, col_z2 = st.columns(2)
        
        with col_z1:
            col_tbu = st.selectbox("📏 Pilih Kolom TB/U", zscore_cols, key="tbu_tab4")
        
        with col_z2:
            col_bbu = st.selectbox("⚖️ Pilih Kolom BB/U", zscore_cols, key="bbu_tab4", index=min(1, len(zscore_cols)-1))
        
        # Bersihkan data
        df_plot = df_filtered[[col_tbu, col_bbu, "is_stunting"]].copy().dropna()
        df_plot = df_plot.loc[:, ~df_plot.columns.duplicated()]
        
        if col_tbu != col_bbu and len(df_plot) > 0:
            fig_scatter = px.scatter(
                df_plot,
                x=col_tbu,
                y=col_bbu,
                color="is_stunting",
                color_discrete_map={0: "green", 1: "red"},
                labels={
                    col_tbu: "Z-Score TB/U",
                    col_bbu: "Z-Score BB/U",
                    "is_stunting": "Status"
                }
            )
            
            fig_scatter.add_hline(y=-2, line_dash="dash", line_color="orange", annotation_text="Threshold BB/U (-2)")
            fig_scatter.add_vline(x=-2, line_dash="dash", line_color="orange", annotation_text="Threshold TB/U (-2)")
            
            fig_scatter.update_layout(
                height=600,
                showlegend=True
            )
            
            fig_scatter.for_each_trace(lambda t: t.update(name="Normal" if t.name == "0" else "Stunting"))
            
            st.plotly_chart(fig_scatter, use_container_width=True, key="scatter_chart_tab4")
            
            # Statistik
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            stunting = df_plot[df_plot["is_stunting"] == 1]
            normal = df_plot[df_plot["is_stunting"] == 0]
            
            with col1:
                st.metric("Total Balita", len(df_plot))
            
            with col2:
                st.metric("Stunting", len(stunting), delta=f"{len(stunting)/len(df_plot)*100:.1f}%")
            
            with col3:
                if len(stunting) > 0:
                    st.metric("Rata-rata TB/U (Stunting)", f"{stunting[col_tbu].mean():.2f}")
                else:
                    st.metric("Rata-rata TB/U (Stunting)", "N/A")
            
            with col4:
                if len(normal) > 0:
                    st.metric("Rata-rata TB/U (Normal)", f"{normal[col_tbu].mean():.2f}")
                else:
                    st.metric("Rata-rata TB/U (Normal)", "N/A")
            
            st.markdown("---")
            st.subheader("💡 Interpretasi Z-Score")
            
            st.info("""
            **Klasifikasi Z-Score WHO:**
            - **Normal**: Z-Score ≥ -2 SD
            - **Stunted (Pendek)**: -3 SD ≤ Z-Score < -2 SD
            - **Severely Stunted (Sangat Pendek)**: Z-Score < -3 SD
            
            **Kuadran pada scatter plot:**
            - 🟢 **Kanan atas**: Normal TB/U dan BB/U
            - 🔴 **Kiri bawah**: Berisiko stunting dan underweight
            - 🟡 **Kiri atas**: Pendek tapi berat badan cukup
            - 🟡 **Kanan bawah**: Tinggi normal tapi underweight
            """)
        else:
            if col_tbu == col_bbu:
                st.warning("⚠️ Pilih kolom yang berbeda untuk TB/U dan BB/U")
            else:
                st.warning("⚠️ Tidak ada data untuk ditampilkan setelah filter diterapkan")
    else:
        st.info("ℹ️ Kolom Z-Score tidak tersedia dalam dataset. Kamu bisa menambahkan analisis alternatif seperti di kode awalmu.")

# ===============================
# TAB 5: DATA LENGKAP
# ===============================
with tab5:
    st.subheader("📋 Data Lengkap per Kecamatan")
    
    kec_sorted = kec_df.sort_values("prevalensi", ascending=False).reset_index(drop=True)
    kec_sorted.insert(0, "Rank", range(1, len(kec_sorted) + 1))
    
    display_df = pd.DataFrame({
        "Rank": kec_sorted["Rank"].apply(lambda x: f"#{x}"),
        "Kecamatan": kec_sorted["nama_kecamatan"],
        "Total Balita": kec_sorted["total_balita"],
        "Kasus Stunting": kec_sorted["total_kasus"],
        "Prevalensi": kec_sorted["prevalensi"].apply(lambda x: f"{x:.2f}%")
    })
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    st.markdown("---")
    csv = kec_sorted.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data CSV",
        data=csv,
        file_name="data_prevalensi_kecamatan.csv",
        mime="text/csv"
    )

# ===============================
# LAYOUT 2 KOLOM: BAR CHART & TOP 5
# ===============================
st.divider()
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Top 10 Kecamatan dengan Prevalensi Tertinggi")
    
    top10 = kec_df.sort_values("prevalensi", ascending=False).head(10)
    
    fig_bar_bottom = px.bar(
        top10,
        x="prevalensi",
        y="nama_kecamatan",
        orientation="h",
        text=top10["prevalensi"].round(2).astype(str) + "%",
        color="prevalensi",
        color_continuous_scale="Reds"
    )
    
    fig_bar_bottom.update_traces(
        textposition="outside",
        textfont_size=12
    )
    
    fig_bar_bottom.update_layout(
        xaxis_title="Prevalensi (%)",
        yaxis_title="",
        showlegend=False,
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig_bar_bottom, use_container_width=True, key="bar_chart_bottom")

with col2:
    st.subheader("🏆 Top 5 Kecamatan")
    
    top5 = kec_df.sort_values("prevalensi", ascending=False).head(5)
    
    for i, (_, row) in enumerate(top5.iterrows(), 1):
        if i == 1:
            border_color = "#dc2626"
            bg_color = "#fee2e2"
        elif i == 2:
            border_color = "#ea580c"
            bg_color = "#ffedd5"
        elif i == 3:
            border_color = "#f59e0b"
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
                        {int(row['total_kasus']):,} dari {int(row['total_balita']):,} balita
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ===============================
# STATISTIK RINGKAS
# ===============================
st.subheader("📊 Statistik Prevalensi Keseluruhan")

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
