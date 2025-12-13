import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard Analisis Stunting")
st.title("📊 Dashboard Analisis Skrining Stunting (Sidoarjo)")
st.markdown("---")

# --- 1. PEMUATAN DATA (FIXED & CACHED) ---

@st.cache_data
def load_data():
    """Memuat dan membersihkan data dari CSV snippet."""
    # Konten file data_skrinning_stunting(1).csv Anda
    data_csv_snippet = """
tgl_pengambilan_data,nik_balita,nama_balita,tgl_lahir_balita,jenis_kelamin_balita,umur_balita,bb_balita_lahir,tb_balita_lahir,bb_balita,tb_balita,zsc_tbu,zsc_bbtb,zsc_bbu,stunting_balita,status_tbu,status_bbtb,status_bbu,nama_responden,nik_responden,no_hp_responden,tgl_lahir_responden,nama_puskesmas,nama_kecamatan,nama_desa,rt,rw
1/3/2025,s0:1wNMg/i1akEl3uEbwDKvZpk6d0IcoGhYprlQsOW47UX659YuPs9PfSCgOyY=,s0:4ZOaffhqPfJ76xo7CblKY2D4SKPaWyj3kZEaMmo5jDSsl8vj20AIXNg1aIJjmTYx,s0:aoBbahZAiUabN3Li0y09myqA2Y01j1O3eKC3Qx+lkeB0T+QlryI=,Laki - Laki,2 Tahun 5 Bulan,1.4,39,10,84,-2.158,-1.695,-2.324,Ya,Pendek,Gizi Baik,BB Kurang,s0:iLFdMgDCkN31FFEsZb/oKlyPlSfGOyBnJmw1fg...,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV6lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
11/18/2025,s0:pOqNnzi7gIsbELF5fwZaTdm3JQZ2P4j+UEZu0tp2om152mUFWQZjnIGRDMw=,s0:KNKG6i1DmDfWxeNlMWkhemhM6ySJEV37fvRToEVObvnNgfjXhA==,s0:/RGgJmWbTO0RERKsOjtZzmfT1U5wFVr...,Laki - Laki,1 Tahun 0 Bulan,3.3,50,7.9,74.5,-0.894,-2.184,-1.997,Tidak,Normal,Gizi Kurang,BB Normal,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV6lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
"""
    df = pd.read_csv(io.StringIO(data_csv_snippet))
    
    # Cleaning dan Feature Engineering yang sama
    df.columns = [col.lower().replace(' ', '_').replace('.', '') for col in df.columns]
    df['is_stunting'] = df['stunting_balita'].apply(lambda x: 1 if x == 'Ya' else 0)

    def categorize_age(umur_str):
        if pd.isna(umur_str) or not isinstance(umur_str, str): return 'E. > 60 Bulan'
        tahun = 0
        bulan = 0
        try:
            parts = umur_str.split(' ')
            if 'Tahun' in parts: tahun = int(parts[parts.index('Tahun') - 1])
            if 'Bulan' in parts: bulan = int(parts[parts.index('Bulan') - 1])
        except (ValueError, IndexError): pass
        total_bulan = tahun * 12 + bulan
        
        if total_bulan <= 12: return 'A. 0-12 Bulan (Bayi)'
        elif total_bulan <= 24: return 'B. 13-24 Bulan (Tahun Kritis)'
        elif total_bulan <= 36: return 'C. 25-36 Bulan'
        elif total_bulan <= 60: return 'D. 37-60 Bulan'
        else: return 'E. > 60 Bulan'

    df['kelompok_umur'] = df['umur_balita'].apply(categorize_age)

    for col in ['bb_balita_lahir', 'tb_balita_lahir']:
        df[col] = df[col].replace(0, np.nan)
    
    for col in ['zsc_tbu', 'zsc_bbu', 'zsc_bbtb']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Memastikan kolom krusial ada data numerik
    df.dropna(subset=['nama_kecamatan', 'stunting_balita', 'zsc_tbu', 'zsc_bbu'], inplace=True)
    
    return df

try:
    df = load_data()
except Exception as e:
    # Ini akan menampilkan error jika gagal di level data loading/cleaning
    st.error(f"❌ Error saat memuat atau membersihkan data: {e}")
    st.stop()


if df.empty or len(df) < 2:
    st.error("⚠️ Data tidak cukup (kurang dari 2 baris) setelah cleaning untuk membuat dashboard.")
    st.stop()
    
# --- 2. ANALISIS PERHITUNGAN UNTUK DASHBOARD ---

total_balita = len(df)
prevalensi_stunting = (df['is_stunting'].sum() / total_balita) * 100 if total_balita > 0 else 0

# Segmentasi Kecamatan
kecamatan_data = df.groupby('nama_kecamatan')['is_stunting'].agg(
    total_kasus='sum',
    total_populasi='count'
).reset_index()
kecamatan_data['prevalensi'] = (kecamatan_data['total_kasus'] / kecamatan_data['total_populasi']) * 100
kecamatan_data_sorted = kecamatan_data.sort_values(by='prevalensi', ascending=False)

# Segmentasi Umur
umur_data = df.groupby('kelompok_umur')['is_stunting'].agg(
    total_kasus='sum',
    total_populasi='count'
).reset_index()
umur_data['prevalensi'] = (umur_data['total_kasus'] / umur_data['total_populasi']) * 100
umur_data_sorted = umur_data.sort_values(by='kelompok_umur', ascending=True)


# --- 3. VISUALISASI PLOTLY (KOMPONEN) ---

# 3.1. Area Prioritas (Kecamatan)
if not kecamatan_data_sorted.empty:
    top_10_kecamatan = kecamatan_data_sorted.head(10).sort_values(by='prevalensi', ascending=True)
    fig_kecamatan = px.bar(
        top_10_kecamatan,
        x='prevalensi', y='nama_kecamatan', orientation='h', 
        color='prevalensi', color_continuous_scale=px.colors.sequential.Reds,
        text=top_10_kecamatan['prevalensi'].round(1).astype(str) + '%' 
    )
    fig_kecamatan.update_traces(textposition='outside')
    fig_kecamatan.update_layout(showlegend=False)
else:
    # Fallback figure jika data kosong
    fig_kecamatan = go.Figure(layout=go.Layout(annotations=[go.layout.Annotation(x=0.5, y=0.5, text='Data Kecamatan Kosong', showarrow=False)]))

# 3.2. Fase Kritis (Kelompok Umur)
if not umur_data_sorted.empty:
    fig_umur = px.bar(
        umur_data_sorted,
        x='kelompok_umur', y='prevalensi',
        color='prevalensi', color_continuous_scale=px.colors.sequential.Blues,
        text=umur_data_sorted['prevalensi'].round(1).astype(str) + '%'
    )
    fig_umur.update_traces(textposition='auto')
    fig_umur.update_layout(showlegend=False)
else:
    # Fallback figure jika data kosong
    fig_umur = go.Figure(layout=go.Layout(annotations=[go.layout.Annotation(x=0.5, y=0.5, text='Data Umur Kosong', showarrow=False)]))


# 3.3. Diagnostik Z-Score (Scatter Plot)
fig_zscore = px.scatter(
    df, x='zsc_tbu', y='zsc_bbu', 
    color='stunting_balita',
    color_discrete_map={'Ya': 'red', 'Tidak': 'green'},
    hover_data=['umur_balita', 'nama_kecamatan', 'jenis_kelamin_balita']
)
fig_zscore.update_layout(showlegend=True)

# 3.4. KPI Card (Prevalensi Total)
fig_kpi = go.Figure(go.Indicator(
    mode="number+gauge",
    value=prevalensi_stunting,
    title={'text': "<b>Prevalensi Stunting Total (%)</b>"},
    number={'suffix': "%", 'font': {'size': 48}},
    gauge={
        'axis': {'range': [None, 30]},
        'bar': {'color': "darkred"},
        'steps': [{'range': [0, 10], 'color': "lightgreen"}, {'range': [10, 20], 'color': "yellow"}, {'range': [20, 30], 'color': "red"}],
        'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 20}
    }
))


# --- 4. MERANGKAI SEMUA KOMPONEN MENJADI DASHBOARD AKHIR (SUBPLOT) ---

fig_dashboard = make_subplots(
    rows=2, cols=2,
    specs=[
        [{"type": "indicator"}, {"type": "xy"}], 
        [{"type": "xy"}, {"type": "xy"}]     
    ],
    subplot_titles=(
        "1. KPI: Prevalensi Stunting Total",
        "2. Fase Kritis: Prevalensi Berdasarkan Kelompok Umur",
        "3. Area Prioritas: Top 10 Kecamatan (Prevalensi Stunting %)",
        "4. Diagnostik Z-Score (TB/U vs BB/U)"
    )
)

# Row 1
fig_dashboard.add_trace(fig_kpi.data[0], row=1, col=1)
# Menambahkan traces dari fig_umur
for trace in fig_umur.data: fig_dashboard.add_trace(trace, row=1, col=2)
# Row 2
# Menambahkan traces dari fig_kecamatan
for trace in fig_kecamatan.data: fig_dashboard.add_trace(trace, row=2, col=1)
# Menambahkan traces dari fig_zscore
for trace in fig_zscore.data: fig_dashboard.add_trace(trace, row=2, col=2)


# Menambahkan garis batas Z-Score pada subplot diagnostik
fig_dashboard.add_shape(type="line", x0=-2, y0=-5, x1=-2, y1=5, line=dict(color="gray", width=1, dash="dash"), row=2, col=2)
fig_dashboard.add_shape(type="line", x0=-5, y0=-2, x1=5, y1=-2, line=dict(color="gray", width=1, dash="dash"), row=2, col=2)
fig_dashboard.update_xaxes(title_text='Z-Score TB/U', row=2, col=2)
fig_dashboard.update_yaxes(title_text='Z-Score BB/U', row=2, col=2)

# --- 5. LAYOUT & DISPLAY AKHIR ---

fig_dashboard.update_layout(
    height=850,
    title_text="**Dashboard Kecerdasan Bisnis: Analisis Skrining Stunting**",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
)
fig_dashboard.add_annotation(
    x=0.5, y=0.5, xref="paper", yref="paper", 
    text="DATA SKRINING STUNTING 2025", 
    showarrow=False, 
    font=dict(size=40, color="rgba(0,0,0,0.1)", family="Arial"),
    xanchor='center', yanchor='middle'
)

# TAMPILKAN DI STREAMLIT
st.plotly_chart(fig_dashboard, use_container_width=True)


# --- 6. INSIGHTS STREAMLIT (PROTEKSI INDEX ERROR) ---

# Tentukan nilai fallback jika DataFrame agregasi kosong
kecamatan_fokus = kecamatan_data_sorted.iloc[0]['nama_kecamatan'] if not kecamatan_data_sorted.empty else "Tidak Diketahui"
prevalensi_fokus = kecamatan_data_sorted.iloc[0]['prevalensi'] if not kecamatan_data_sorted.empty else 0
umur_fokus = umur_data_sorted.iloc[0]['kelompok_umur'] if not umur_data_sorted.empty else "Tidak Diketahui"

st.markdown("---")
st.subheader("💡 Insight Utama & Rekomendasi")
st.markdown(f"""
1.  **Area Prioritas:** Fokuskan intervensi ke Kecamatan **{kecamatan_fokus}** dengan prevalensi stunting tertinggi ({prevalensi_fokus:.1f}%).
2.  **Fase Kritis:** Kelompok usia **{umur_fokus}** menunjukkan prevalensi tertinggi. 
3.  **Diagnostik Z-Score:** Plot membantu mengidentifikasi balita yang menderita **Stunting** (TB/U < -2) atau **Gizi Kurang** (BB/U < -2).
""")
