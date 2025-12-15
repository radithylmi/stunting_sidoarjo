import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Diagnostik Z-Score", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data_skrinning_stunting(1).csv")
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace(".", "", regex=False)
    df["nama_kecamatan"] = df["nama_kecamatan"].astype(str).str.upper().str.strip()
    df["is_stunting"] = df["stunting_balita"].map({"Ya": 1, "Tidak": 0})
    return df

df = load_data()

# Cek kolom z-score (sesuaikan dengan nama kolom Anda)
zscore_cols = [col for col in df.columns if 'z' in col.lower() or 'score' in col.lower()]

st.sidebar.header("🔎 Filter & Pengaturan")

# Filter kecamatan
kecamatan_opsi = ["Semua Kecamatan"] + sorted(df["nama_kecamatan"].unique().tolist())
kecamatan_pilih = st.sidebar.selectbox("📍 Pilih Kecamatan", kecamatan_opsi)

if kecamatan_pilih != "Semua Kecamatan":
    df_plot = df[df["nama_kecamatan"] == kecamatan_pilih].copy()
else:
    df_plot = df.copy()

# Judul
st.title("🔬 Diagnostik Z-Score (TB/U vs BB/U)")
st.markdown(f"**Wilayah:** {kecamatan_pilih}")

# Cek apakah ada kolom z-score
if len(zscore_cols) >= 2:
    # Pilih kolom z-score
    st.sidebar.subheader("Pilih Kolom Z-Score")
    
    col_tbu = st.sidebar.selectbox(
        "📏 Tinggi Badan/Umur (TB/U)",
        zscore_cols,
        index=0
    )
    
    col_bbu = st.sidebar.selectbox(
        "⚖️ Berat Badan/Umur (BB/U)",
        zscore_cols,
        index=min(1, len(zscore_cols)-1)
    )
    
    # Bersihkan data
    df_plot = df_plot[[col_tbu, col_bbu, "is_stunting"]].dropna()
    
    # Scatter plot
    fig = px.scatter(
        df_plot,
        x=col_tbu,
        y=col_bbu,
        color="is_stunting",
        color_discrete_map={0: "green", 1: "red"},
        labels={
            col_tbu: "Z-Score TB/U",
            col_bbu: "Z-Score BB/U",
            "is_stunting": "Status"
        },
        hover_data={
            col_tbu: ":.2f",
            col_bbu: ":.2f"
        }
    )
    
    # Tambahkan garis referensi
    fig.add_hline(y=-2, line_dash="dash", line_color="orange", annotation_text="Threshold BB/U (-2)")
    fig.add_vline(x=-2, line_dash="dash", line_color="orange", annotation_text="Threshold TB/U (-2)")
    
    # Tambahkan zona
    fig.add_shape(
        type="rect",
        x0=-25, y0=-25, x1=-2, y1=-2,
        fillcolor="rgba(255,0,0,0.1)",
        line_width=0,
        layer="below"
    )
    
    fig.update_layout(
        height=600,
        xaxis_title="Z-Score Tinggi Badan/Umur (TB/U)",
        yaxis_title="Z-Score Berat Badan/Umur (BB/U)",
        showlegend=True,
        legend_title_text="Status Stunting",
        plot_bgcolor="rgba(240,240,240,0.5)"
    )
    
    # Update legend labels
    fig.for_each_trace(lambda t: t.update(name="Normal" if t.name == "0" else "Stunting"))
    
    st.plotly_chart(fig, use_container_width=True)
    
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
    st.warning("""
    ⚠️ **Kolom Z-Score tidak ditemukan dalam dataset!**
    
    Untuk membuat scatter plot Z-Score, pastikan dataset Anda memiliki kolom seperti:
    - `zscore_tbu` atau `z_score_tb_u` (Tinggi Badan/Umur)
    - `zscore_bbu` atau `z_score_bb_u` (Berat Badan/Umur)
    
    **Kolom yang tersedia:** {', '.join(df.columns.tolist())}
    """.format(df=df))
    
    st.markdown("---")
    st.subheader("📊 Alternatif: Distribusi Status Stunting")
    
    # Buat pie chart sebagai alternatif
    status_count = df_plot["is_stunting"].value_counts()
    
    fig_pie = px.pie(
        values=status_count.values,
        names=["Normal", "Stunting"],
        color_discrete_sequence=["green", "red"],
        hole=0.4
    )
    
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=400)
    
    st.plotly_chart(fig_pie, use_container_width=True)
