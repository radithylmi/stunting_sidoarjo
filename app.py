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
# MAIN TITLE
# ===============================
st.title("📊 Dashboard Stunting Kabupaten Sidoarjo")

# ===============================
# KPI CARDS
# ===============================
total_balita = len(df_filtered)
total_kasus = int(df_filtered["is_stunting"].sum())
prevalensi = (total_kasus / total_balita * 100) if total_balita > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("👶 Total Balita", f"{total_balita:,}")
c2.metric("🚨 Kasus Stunting", f"{total_kasus:,}")
c3.metric("📉 Prevalensi", f"{prevalensi:.2f}%")

st.divider()

# ===============================
# GAUGE CHART - KPI PREVALENSI
# ===============================
st.subheader("🎯 KPI Prevalensi Stunting")

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=prevalensi,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Prevalensi Stunting", 'font': {'size': 20}},
    number={'suffix': "%", 'font': {'size': 40}},
    delta={
        'reference': 30,
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
            'value': 30
        }
    }
))

fig_gauge.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=60, b=20),
    paper_bgcolor="white"
)

st.plotly_chart(fig_gauge, width='stretch', key="gauge_chart_main")

st.divider()

# ===============================
# AGREGASI DATA (SEBELUM TAB!)
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
# TAB NAVIGATION UNTUK BERBAGAI VISUALISASI
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

    with col_zoom:
        zoom_level = st.slider(
            "🔍 Zoom:",
            min_value=8,
            max_value=13,
            value=10,
            step=1,
            key="zoom_tab1"
        )

    # Catatan: choropleth_mapbox masih digunakan karena choropleth_map memerlukan migrasi ke MapLibre
    # Untuk sementara gunakan choropleth_mapbox dengan suppressing warning
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

    st.plotly_chart(fig_map, width='stretch', key="map_chart_tab1")

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
# TAB 2: KELOMPOK UMUR
# ===============================
with tab2:
    st.subheader("📊 Fase Kritis: Prevalensi Berdasarkan Kelompok Umur")
    
    # Cek apakah ada data
    if len(age_df) > 0:
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            fig_age = px.bar(
                age_df,
                x="kelompok_umur",
                y="prevalensi",
                text=age_df["prevalensi"].round(1).astype(str) + "%",
                color="prevalensi",
                color_continuous_scale="Plasma",
                labels={
                    "kelompok_umur": "Kelompok Umur",
                    "prevalensi": "Prevalensi Stunting (%)"
                }
            )

            fig_age.update_traces(
                textposition="outside",
                textfont_size=14
            )

            fig_age.update_layout(
                height=500,
                showlegend=False,
                yaxis_range=[0, age_df["prevalensi"].max() * 1.15]
            )

            st.plotly_chart(fig_age, width='stretch', key="age_chart_tab2")
        
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
                        {row['prevalensi']:.1f}%
                    </div>
                    <div style="font-size: 12px; color: #888;">
                        {row['total_kasus']:,} / {row['total_balita']:,} balita
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Insight
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
    
    # Pilihan Top N
    top_n = st.radio(
        "Tampilkan:",
        ["Top 5", "Top 10", "Top 15", "Semua Kecamatan"],
        horizontal=True,
        key="top_n_radio"
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
    
    top_data = kec_df.sort_values("prevalensi", ascending=False).head(n)
    
    col_chart, col_cards = st.columns([2, 1])
    
    with col_chart:
        fig_bar = px.bar(
            top_data,
            x="prevalensi",
            y="nama_kecamatan",
            orientation="h",
            text=top_data["prevalensi"].round(2).astype(str) + "%",
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
            height=max(500, n * 40),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_bar, width='stretch', key="bar_chart_tab3")
    
    with col_cards:
        st.markdown(f"#### 🎯 {top_n}")
        
        for i, (idx, row) in enumerate(top_data.head(5).iterrows(), 1):
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
                    {row['prevalensi']:.2f}%
                </div>
                <div style="font-size: 11px; color: #666;">
                    {row['total_kasus']:,} / {row['total_balita']:,} balita
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Statistik
    st.markdown("---")
    st.subheader("📊 Statistik")
    
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
            f"{total_kasus_top:,}"
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
            
            st.plotly_chart(fig_scatter, width='stretch', key="scatter_chart_tab4")
            
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
            
            # Interpretasi
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
        st.info("ℹ️ Kolom Z-Score tidak tersedia dalam dataset. Menampilkan analisis alternatif.")
        
        # Visualisasi 1: Distribusi Status Stunting
        st.markdown("### 📊 Distribusi Status Stunting")
        
        col_pie, col_bar_status = st.columns(2)
        
        with col_pie:
            status_count = df_filtered["is_stunting"].value_counts()
            
            fig_pie = px.pie(
                values=status_count.values,
                names=["Normal", "Stunting"],
                color_discrete_sequence=["#10b981", "#ef4444"],
                hole=0.4,
                title="Proporsi Stunting vs Normal"
            )
            
            fig_pie.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont_size=14
            )
            fig_pie.update_layout(height=400)
            
                            st.plotly_chart(fig_pie, width='stretch', key="pie_chart_tab4")
        
        with col_bar_status:
            status_df = pd.DataFrame({
                'Status': ['Normal', 'Stunting'],
                'Jumlah': [status_count.get(0, 0), status_count.get(1, 0)]
            })
            
            fig_bar_status = px.bar(
                status_df,
                x='Status',
                y='Jumlah',
                text='Jumlah',
                color='Status',
                color_discrete_map={'Normal': '#10b981', 'Stunting': '#ef4444'},
                title="Jumlah Balita per Status"
            )
            
            fig_bar_status.update_traces(textposition='outside')
            fig_bar_status.update_layout(height=400, showlegend=False)
            
            st.plotly_chart(fig_bar_status, width='stretch', key="bar_status_tab4")
        
        # Visualisasi 2: Stunting per Kecamatan (Top 10)
        st.markdown("---")
        st.markdown("### 🗺️ Top 10 Kecamatan dengan Kasus Stunting Tertinggi")
        
        kec_stunting = df_filtered.groupby("nama_kecamatan").agg(
            total=("is_stunting", "count"),
            stunting=("is_stunting", "sum")
        ).reset_index()
        
        kec_stunting["persen"] = (kec_stunting["stunting"] / kec_stunting["total"] * 100).round(2)
        top10_stunting = kec_stunting.sort_values("stunting", ascending=False).head(10)
        
        fig_kec = px.bar(
            top10_stunting,
            x="stunting",
            y="nama_kecamatan",
            orientation="h",
            text=top10_stunting.apply(lambda x: f"{int(x['stunting'])} ({x['persen']:.1f}%)", axis=1),
            color="persen",
            color_continuous_scale="Reds",
            labels={"stunting": "Jumlah Kasus", "nama_kecamatan": "Kecamatan", "persen": "Prevalensi (%)"}
        )
        
        fig_kec.update_traces(textposition="outside")
        fig_kec.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_kec, width='stretch', key="kec_stunting_tab4")
        
        # Visualisasi 3: Stunting per Kelompok Umur
        st.markdown("---")
        st.markdown("### 👶 Distribusi Stunting per Kelompok Umur")
        
        if len(age_df) > 0:
            col_age1, col_age2 = st.columns(2)
            
            with col_age1:
                fig_age_stunting = px.bar(
                    age_df,
                    x="kelompok_umur",
                    y="total_kasus",
                    text="total_kasus",
                    color="prevalensi",
                    color_continuous_scale="Oranges",
                    labels={"total_kasus": "Jumlah Kasus", "kelompok_umur": "Kelompok Umur"},
                    title="Jumlah Kasus per Kelompok Umur"
                )
                
                fig_age_stunting.update_traces(textposition="outside")
                fig_age_stunting.update_layout(height=400)
                
                st.plotly_chart(fig_age_stunting, width='stretch', key="age_kasus_tab4")
            
            with col_age2:
                fig_age_prev = px.line(
                    age_df,
                    x="kelompok_umur",
                    y="prevalensi",
                    markers=True,
                    text=age_df["prevalensi"].round(1).astype(str) + "%",
                    title="Tren Prevalensi per Kelompok Umur"
                )
                
                fig_age_prev.update_traces(
                    textposition="top center",
                    line=dict(color='#f97316', width=3),
                    marker=dict(size=12)
                )
                fig_age_prev.update_layout(
                    height=400,
                    yaxis_title="Prevalensi (%)"
                )
                
                st.plotly_chart(fig_age_prev, width='stretch', key="age_prev_tab4")
        
        # Statistik Ringkas
        st.markdown("---")
        st.markdown("### 📈 Statistik Ringkas")
        
        stat1, stat2, stat3, stat4 = st.columns(4)
        
        with stat1:
            st.metric(
                "Total Balita Diperiksa",
                f"{len(df_filtered):,}",
                help="Jumlah total balita yang telah diskrining"
            )
        
        with stat2:
            total_stunting = int(df_filtered["is_stunting"].sum())
            st.metric(
                "Total Kasus Stunting",
                f"{total_stunting:,}",
                delta=f"{(total_stunting/len(df_filtered)*100):.1f}%",
                delta_color="inverse",
                help="Jumlah balita dengan status stunting"
            )
        
        with stat3:
            if len(age_df) > 0:
                max_age = age_df.loc[age_df["prevalensi"].idxmax(), "kelompok_umur"]
                max_prev = age_df["prevalensi"].max()
                st.metric(
                    "Kelompok Tertinggi",
                    max_age,
                    delta=f"{max_prev:.1f}%",
                    delta_color="inverse",
                    help="Kelompok umur dengan prevalensi tertinggi"
                )
            else:
                st.metric("Kelompok Tertinggi", "N/A")
        
        with stat4:
            if len(kec_df) > 0:
                max_kec = kec_df.loc[kec_df["prevalensi"].idxmax(), "nama_kecamatan"]
                max_kec_prev = kec_df["prevalensi"].max()
                st.metric(
                    "Kecamatan Tertinggi",
                    max_kec,
                    delta=f"{max_kec_prev:.1f}%",
                    delta_color="inverse",
                    help="Kecamatan dengan prevalensi tertinggi"
                )
            else:
                st.metric("Kecamatan Tertinggi", "N/A")

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
        width='stretch',
        hide_index=True,
        height=600
    )
    
    # Download button
    st.markdown("---")
    csv = kec_sorted.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data CSV",
        data=csv,
        file_name="data_prevalensi_kecamatan.csv",
        mime="text/csv"
    )

st.divider()

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
    
    st.plotly_chart(fig_bar, width='stretch', key="bar_chart_bottom")

with col2:
    st.subheader("🏆 Top 5 Kecamatan")
    
    top5 = kec_df.sort_values("prevalensi", ascending=False).head(5)
    
    for i, (idx, row) in enumerate(top5.iterrows(), 1):
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
                        {row['total_kasus']:,} dari {row['total_balita']:,} balita
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

# ===============================
# DEBUG
# ===============================
with st.expander("🧪 Debug & Informasi Dataset", expanded=False):
    st.markdown("### 📊 Ringkasan Dataset")
    
    # Statistik Umum
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Baris", f"{len(df):,}")
    
    with col2:
        st.metric("🔽 Baris Terfilter", f"{len(df_filtered):,}")
    
    with col3:
        st.metric("📍 Jumlah Kecamatan", f"{len(kec_df)}")
    
    with col4:
        st.metric("📂 Jumlah Kolom", f"{len(df.columns)}")
    
    st.markdown("---")
    
    # Informasi Kolom
    st.markdown("### 📋 Informasi Kolom Dataset")
    
    col_info = []
    for idx, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df) * 100)
        unique_count = df[col].nunique()
        
        # Ambil sample data dengan handling khusus
        try:
            if len(df) > 0:
                sample_val = df[col].iloc[0]
                
                # Jika data terlalu panjang (seperti NIK terenkripsi), potong
                if isinstance(sample_val, str) and len(sample_val) > 30:
                    sample_data = sample_val[:30] + "..."
                # Jika NIK atau nama, sembunyikan untuk privasi
                elif col in ['nik_balita', 'nama_balita']:
                    sample_data = "[PROTECTED]"
                # Jika angka, format dengan baik
                elif pd.notna(sample_val) and isinstance(sample_val, (int, float)):
                    sample_data = f"{sample_val:.2f}" if isinstance(sample_val, float) else str(sample_val)
                else:
                    sample_data = str(sample_val)[:50]
            else:
                sample_data = "N/A"
        except:
            sample_data = "N/A"
        
        col_info.append({
            "No": idx,
            "Nama Kolom": col,
            "Tipe Data": dtype,
            "Unique Values": f"{unique_count:,}",
            "Missing Values": f"{null_count:,} ({null_pct:.1f}%)",
            "Sample Data": sample_data
        })
    
    df_col_info = pd.DataFrame(col_info)
    
    st.dataframe(
        df_col_info,
        width='stretch',
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    
    # Preview Data
    st.markdown("### 👀 Preview Data Agregasi")
    
    tab_preview1, tab_preview2, tab_preview3 = st.tabs([
        "📍 Data per Kecamatan", 
        "👶 Data per Kelompok Umur",
        "🔍 Sample Data Mentah"
    ])
    
    with tab_preview1:
        st.markdown("**Top 10 Kecamatan berdasarkan Prevalensi:**")
        preview_kec = kec_df.sort_values("prevalensi", ascending=False).head(10).copy()
        preview_kec["prevalensi"] = preview_kec["prevalensi"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(
            preview_kec,
            width='stretch',
            hide_index=True
        )
    
    with tab_preview2:
        st.markdown("**Data Prevalensi per Kelompok Umur:**")
        if len(age_df) > 0:
            preview_age = age_df.copy()
            preview_age["prevalensi"] = preview_age["prevalensi"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(
                preview_age,
                width='stretch',
                hide_index=True
            )
        else:
            st.info("Tidak ada data kelompok umur")
    
    with tab_preview3:
        st.markdown("**10 Baris Pertama Data Mentah (Terfilter):**")
        
        # Pilih kolom yang penting dan tampilkan dengan lebih baik
        display_cols = [
            'nama_kecamatan', 'umur_balita', 'jenis_kelamin_balita',
            'bb_balita', 'tb_balita', 'stunting_balita'
        ]
        
        # Filter hanya kolom yang ada
        available_cols = [col for col in display_cols if col in df_filtered.columns]
        
        if len(available_cols) > 0:
            preview_data = df_filtered[available_cols].head(10).copy()
            
            # Format data untuk tampilan lebih baik dengan error handling yang kuat
            if 'umur_balita' in preview_data.columns:
                preview_data['umur_balita'] = preview_data['umur_balita'].apply(
                    lambda x: f"{float(x):.0f} bulan" if pd.notna(x) and str(x).replace('.','').isdigit() else (str(x) if pd.notna(x) else "N/A")
                )
            
            if 'bb_balita' in preview_data.columns:
                preview_data['bb_balita'] = preview_data['bb_balita'].apply(
                    lambda x: f"{float(x):.1f} kg" if pd.notna(x) and str(x).replace('.','').replace('-','').isdigit() else (str(x) if pd.notna(x) else "N/A")
                )
            
            if 'tb_balita' in preview_data.columns:
                preview_data['tb_balita'] = preview_data['tb_balita'].apply(
                    lambda x: f"{float(x):.1f} cm" if pd.notna(x) and str(x).replace('.','').replace('-','').isdigit() else (str(x) if pd.notna(x) else "N/A")
                )
            
            st.dataframe(
                preview_data,
                width='stretch',
                height=400
            )
        else:
            st.dataframe(
                df_filtered.head(10),
                width='stretch',
                height=400
            )
        
        st.info("ℹ️ **Catatan:** Data pribadi seperti NIK dan Nama tidak ditampilkan untuk menjaga privasi.")
    
    st.markdown("---")
    
    # Statistik Tambahan
    st.markdown("### 📈 Statistik Tambahan")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.markdown("**📊 Distribusi Data:**")
        st.write(f"- **Total Kecamatan Unik:** {df['nama_kecamatan'].nunique()}")
        st.write(f"- **Total NIK Unik:** {df['nik_balita'].nunique():,}")
        
        # Handle umur_balita dengan aman
        try:
            umur_valid = df['umur_balita'].dropna()
            if len(umur_valid) > 0:
                umur_min = umur_valid.min()
                umur_max = umur_valid.max()
                st.write(f"- **Rentang Umur:** {umur_min:.0f} - {umur_max:.0f} bulan")
            else:
                st.write(f"- **Rentang Umur:** Data tidak tersedia")
        except:
            st.write(f"- **Rentang Umur:** Data tidak valid")
    
    with stat_col2:
        st.markdown("**🎯 Data Quality:**")
        total_missing = df.isnull().sum().sum()
        missing_pct = (total_missing / (len(df) * len(df.columns)) * 100)
        st.write(f"- **Total Missing Values:** {total_missing:,} ({missing_pct:.2f}%)")
        st.write(f"- **Kelengkapan Data:** {100-missing_pct:.2f}%")
        complete_rows = len(df.dropna())
        st.write(f"- **Baris Lengkap:** {complete_rows:,} ({complete_rows/len(df)*100:.1f}%)")
    
    with stat_col3:
        st.markdown("**⚖️ Balance Dataset:**")
        stunting_count = df["is_stunting"].sum()
        normal_count = len(df) - stunting_count
        st.write(f"- **Stunting:** {stunting_count:,} ({stunting_count/len(df)*100:.1f}%)")
        st.write(f"- **Normal:** {normal_count:,} ({normal_count/len(df)*100:.1f}%)")
        balance_ratio = min(stunting_count, normal_count) / max(stunting_count, normal_count)
        st.write(f"- **Balance Ratio:** {balance_ratio:.2f}")
    
    st.markdown("---")
    
    # Download Options
    st.markdown("### 💾 Download Data")
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
    with dl_col1:
        csv_full = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Terfilter (CSV)",
            data=csv_full,
            file_name="data_stunting_filtered.csv",
            mime="text/csv"
        )
    
    with dl_col2:
        csv_kec = kec_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Kecamatan (CSV)",
            data=csv_kec,
            file_name="data_prevalensi_kecamatan.csv",
            mime="text/csv"
        )
    
    with dl_col3:
        if len(age_df) > 0:
            csv_age = age_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data Umur (CSV)",
                data=csv_age,
                file_name="data_prevalensi_umur.csv",
                mime="text/csv"
            )
        else:
            st.button(
                label="📥 Download Data Umur (CSV)",
                disabled=True
            )
