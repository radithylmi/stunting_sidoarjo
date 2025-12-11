import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard Skrining Stunting")
st.title("📊 Dashboard Kecerdasan Bisnis: Analisis Skrining Stunting")
st.markdown("---")


# --- 1. PEMUATAN DATA (FIXED & CACHED) ---

@st.cache_data
def load_data():
    """Memuat data dari CSV snippet yang disediakan."""
    data_csv_snippet = """
tgl_pengambilan_data,nik_balita,nama_balita,tgl_lahir_balita,jenis_kelamin_balita,umur_balita,bb_balita_lahir,tb_balita_lahir,bb_balita,tb_balita,zsc_tbu,zsc_bbtb,zsc_bbu,stunting_balita,status_tbu,status_bbtb,status_bbu,nama_responden,nik_responden,no_hp_responden,tgl_lahir_responden,nama_puskesmas,nama_kecamatan,nama_desa,rt,rw
1/3/2025,s0:1wNMg/i1akEl3uEbwDKvZpk6d0IcoGhYprlQsOW47UX659YuPs9PfSCgOyY=,s0:4ZOaffhqPfJ76xo7CblKY2D4SKPaWyj3kZEaMmo5jDSsl8vj20AIXNg1aIJjmTYx,s0:aoBbahZAiUabN3Li0y09myqA2Y01j1O3eKC3Qx+lkeB0T+QlryI=,Laki - Laki,2 Tahun 5 Bulan,1.4,39,10,84,-2.158,-1.695,-2.324,Ya,Pendek,Gizi Baik,BB Kurang,s0:iLFdMgDCkN31FFEsZb/oKlyPlSfGOyBnJmw1fg...,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV8lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
11/18/2025,s0:pOqNnzi7gIsbELF5fwZaTdm3JQZ2P4j+UEZu0tp2om152mUFWQZjnIGRDMw=,s0:KNKG6i1DmDfWxeNlMWkhemhM6ySJEV37fvRToEVObvnNgfjXhA==,s0:/RGgJmWbTO0RERKsOjtZzmfT1U5wFVr...,Laki - Laki,1 Tahun 0 Bulan,3.3,50,7.9,74.5,-0.894,-2.184,-1.997,Tidak,Normal,Gizi Kurang,BB Normal,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV8lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
"""
    df = pd.read_csv(io.StringIO(data_csv_snippet))
    
    # Konversi kolom numerik
    for col in ['zsc_tbu', 'zsc_bbu', 'zsc_bbtb']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df.dropna(subset=['zsc_tbu', 'zsc_bbu', 'zsc_bbtb', 'nama_kecamatan'], inplace=True)
    return df

df = load_data()

if df.empty:
    st.error("Gagal memuat data atau data kosong setelah preprocessing. Harap periksa sumber data.")
    st.stop()

# --- 2. DATA AGREGASI ---

# Data untuk visualisasi (dibuat di sini untuk digunakan pada Insights)
kecamatan_data_sorted = df.groupby('nama_kecamatan').size().reset_index(name='Jumlah Balita').sort_values(by='Jumlah Balita', ascending=False)
stunting_counts = df['stunting_balita'].value_counts().reset_index(name='Jumlah').rename(columns={'index': 'Status'})


# --- 3. INSIGHT UTAMA (KPI) ---

st.subheader("🔑 Key Performance Indicator (KPI)")
col1, col2, col3, col4 = st.columns(4)

total_balita = len(df)
persen_stunting = (stunting_counts[stunting_counts['Status'] == 'Ya']['Jumlah'].sum() / total_balita) * 100 if 'Ya' in stunting_counts['Status'].values else 0

col1.metric("Total Balita Tervisi", total_balita)
col2.metric("Persentase Stunting", f"{persen_stunting:.2f}%")
col3.metric("Kecamatan dengan Balita Terbanyak", kecamatan_data_sorted.iloc[0]['nama_kecamatan'], delta=f"{kecamatan_data_sorted.iloc[0]['Jumlah Balita']} Anak")
col4.metric("Balita Status Gizi Kurang", df[df['status_bbtb'] == 'Gizi Kurang'].shape[0])


# --- 4. VISUALISASI UTAMA (MENGGUNAKAN st.columns) ---

st.subheader("📈 Analisis Distribusi")
col_vis_1, col_vis_2 = st.columns([0.6, 0.4])

with col_vis_1:
    # A. Bar Plot Jumlah Balita per Kecamatan
    fig_bar = px.bar(
        kecamatan_data_sorted, 
        x='nama_kecamatan', 
        y='Jumlah Balita',
        title='Distribusi Jumlah Balita per Kecamatan',
        color='Jumlah Balita',
        color_continuous_scale=px.colors.sequential.Bluyl
    )
    fig_bar.update_xaxes(title_text="Nama Kecamatan")
    fig_bar.update_yaxes(title_text="Jumlah Balita")
    
    # Tambahkan Anotasi (Watermark) ke fig_bar
    fig_bar.add_annotation(
        x=0.5, y=0.5, xref="paper", yref="paper", 
        text="DATA STUNTING 2025", 
        showarrow=False, 
        font=dict(size=30, color="rgba(0,0,0,0.1)", family="Arial"),
        xanchor='center', yanchor='middle'
    )
    
    st.plotly_chart(fig_bar, use_container_width=True) # <-- PENGGANTI fig_dashboard.show()

with col_vis_2:
    # B. Pie Chart Status Stunting
    fig_pie = px.pie(
        stunting_counts, 
        names='Status', 
        values='Jumlah',
        title='Persentase Status Stunting Balita',
        color_discrete_map={'Ya': 'red', 'Tidak': 'green'}
    )
    st.plotly_chart(fig_pie, use_container_width=True) # <-- PENGGANTI fig_dashboard.show()


# C. Scatter Plot Z-Score (Baris kedua)
st.subheader("📉 Analisis Detail Z-Score")

# Plotly Scatter Plot
fig_scatter = go.Figure()

# Menentukan warna berdasarkan status stunting
color_map = {'Pendek': 'red', 'Sangat Pendek': 'darkred', 'Normal': 'green', 'Tinggi': 'blue'}
df['color'] = df['status_tbu'].map(color_map)

fig_scatter.add_trace(
    go.Scatter(
        x=df['zsc_tbu'], 
        y=df['zsc_bbu'],
        mode='markers',
        name='Balita',
        marker=dict(
            size=10, 
            opacity=0.7, 
            color=df['color']
        ),
        hovertemplate="Nama: %{customdata[0]}<br>TB/U: %{x}<br>BB/U: %{y}<extra></extra>",
        customdata=df[['nama_balita']]
    )
)

# Menambahkan garis batas WHO Z-Score (Plotly tidak menyediakan WHO chart secara bawaan)
fig_scatter.add_vline(x=-2, line_width=1, line_dash="dash", line_color="red", annotation_text="Batas Stunting (-2 SD)")
fig_scatter.add_hline(y=-2, line_width=1, line_dash="dash", line_color="orange", annotation_text="Batas Gizi Kurang (-2 SD)")

fig_scatter.update_layout(
    title='Sebaran Z-Score Tinggi Badan menurut Usia (TB/U) vs Berat Badan menurut Usia (BB/U)',
    xaxis_title='Z-Score TB/U (Stunting/Pendek)',
    yaxis_title='Z-Score BB/U (Gizi Kurang/Normal)',
    height=600,
    hovermode="closest"
)

st.plotly_chart(fig_scatter, use_container_width=True)


# --- 5. INSIGHT UTAMA ---
st.markdown("---")
st.subheader("🎯 Insight Utama & Rekomendasi")
st.markdown(f"""
* **Wilayah Prioritas:** Fokuskan intervensi ke Kecamatan **{kecamatan_data_sorted.iloc[0]['nama_kecamatan']}**
    karena memiliki jumlah balita tervisi tertinggi, yaitu **{kecamatan_data_sorted.iloc[0]['Jumlah Balita']}** anak.
* **Tingkat Stunting:** Persentase balita yang teridentifikasi Stunting adalah **{persen_stunting:.2f}%**.
* **Aksi Cepat:** Terdapat **{df[df['status_bbtb'] == 'Gizi Kurang'].shape[0]}** balita dengan status **Gizi Kurang** (BB/TB), yang memerlukan perhatian gizi segera.
""")
