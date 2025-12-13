import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(layout="wide", page_title="Dashboard Analisis Stunting")
st.title("✅ Dashboard Analisis Skrining Stunting")
st.sidebar.markdown("Status: **APP IS RUNNING**")
st.markdown("---")

# --- 1. PEMUATAN DATA (FIXED & CACHED) ---

@st.cache_data
def load_data():
    """Memuat dan membersihkan data dari CSV snippet."""
    data_csv_snippet = """
tgl_pengambilan_data,nik_balita,nama_balita,tgl_lahir_balita,jenis_kelamin_balita,umur_balita,bb_balita_lahir,tb_balita_lahir,bb_balita,tb_balita,zsc_tbu,zsc_bbtb,zsc_bbu,stunting_balita,status_tbu,status_bbtb,status_bbu,nama_responden,nik_responden,no_hp_responden,tgl_lahir_responden,nama_puskesmas,nama_kecamatan,nama_desa,rt,rw
1/3/2025,s0:1wNMg/i1akEl3uEbwDKvZpk6d0IcoGhYprlQsOW47UX659YuPs9PfSCgOyY=,s0:4ZOaffhqPfJ76xo7CblKY2D4SKPaWyj3kZEaMmo5jDSsl8vj20AIXNg1aIJjmTYx,s0:aoBbahZAiUabN3Li0y09myqA2Y01j1O3eKC3Qx+lkeB0T+QlryI=,Laki - Laki,2 Tahun 5 Bulan,1.4,39,10,84,-2.158,-1.695,-2.324,Ya,Pendek,Gizi Baik,BB Kurang,s0:iLFdMgDCkN31FFEsZb/oKlyPlSfGOyBnJmw1fg...,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV6lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
11/18/2025,s0:pOqNnzi7gIsbELF5fwZaTdm3JQZ2P4j+UEZu0tp2om152mUFWQZjnIGRDMw=,s0:KNKG6i1DmDfWxeNlMWkhemhM6ySJEV37fvRToEVObvnNgfjXhA==,s0:/RGgJmWbTO0RERKsOjtZzmfT1U5wFVr...,Laki - Laki,1 Tahun 0 Bulan,3.3,50,7.9,74.5,-0.894,-2.184,-1.997,Tidak,Normal,Gizi Kurang,BB Normal,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV6lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
"""
    df = pd.read_csv(io.StringIO(data_csv_snippet))
    df.columns = [col.lower().replace(' ', '_').replace('.', '') for col in df.columns]
    df['is_stunting'] = df['stunting_balita'].apply(lambda x: 1 if x == 'Ya' else 0)

    def categorize_age(umur_str):
        if pd.isna(umur_str) or not isinstance(umur_str, str): return 'E. > 60 Bulan'
        tahun, bulan = 0, 0
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
    
    for col in ['zsc_tbu', 'zsc_bbu', 'zsc_bbtb']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df.dropna(subset=['nama_kecamatan', 'stunting_balita', 'zsc_tbu', 'zsc_bbu'], inplace=True)
    
    return df

try:
    df = load_data()
    print("CHECKPOINT LOG 2: Data berhasil dimuat dan dibersihkan.") 
except Exception as e:
    st.error(f"❌ Error saat memuat atau membersihkan data: {e}")
    st.stop()
    print(f"ERROR LOG: Data gagal dimuat: {e}") 

if df.empty or len(df) < 2:
    st.error("⚠️ Data tidak cukup setelah cleaning untuk membuat dashboard.")
    st.stop()
    
# --- 2. ANALISIS PERHITUNGAN UNTUK DASHBOARD ---
total_balita = len(df)
prevalensi_stunting = (df['is_stunting'].sum() / total_balita) * 100 if total_balita > 0 else 0

st.markdown(f"**CHECKPOINT 3:** Total Balita Ditemukan: **{total_balita}**")

# Segmentasi Kecamatan
kecamatan_data = df.groupby('nama_kecamatan')['is_stunting'].agg(total_kasus='sum', total_populasi='count').reset_index()
kecamatan_data['prevalensi'] = (kecamatan_data['total_kasus'] / kecamatan_data['total_populasi']) * 100
kecamatan_data_sorted = kecamatan_data.sort_values(by='prevalensi', ascending=False)

# Segmentasi Umur
umur_data = df.groupby('kelompok_umur')['is_stunting'].agg(total_kasus='sum', total_populasi='count').reset_index()
umur_data['prevalensi'] = (umur_data['total_kasus'] / umur_data['total_populasi']) * 100
umur_data_sorted = umur_data.sort_values(by='kelompok_umur', ascending=True)

# Tentukan nilai fallback untuk Insight
kecamatan_fokus = kecamatan_data_sorted.iloc[0]['nama_kecamatan'] if not kecamatan_data_sorted.empty else "Tidak Diketahui"
prevalensi_fokus = kecamatan_data_sorted.iloc[0]['prevalensi'] if not kecamatan_data_sorted.empty else 0
umur_fokus = umur_data_sorted.iloc[0]['kelompok_umur'] if not umur_data_sorted.empty else "Tidak Diketahui"

print("CHECKPOINT LOG 4: Perhitungan agregasi selesai. Memulai pembuatan Plotly figures.")

# --- 3. VISUALISASI PLOTLY (KOMPONEN) ---

# 3.1. KPI Card (Prevalensi Total)
fig_kpi = go.Figure(go.Indicator(
    mode="number+gauge",
    value=prevalensi_stunting,
    title={'text': "<b>1. KPI: Prevalensi Stunting Total (%)</b>"},
    number={'suffix': "%", 'font": {'size': 48}},
    gauge={
        'axis': {'range': [None, 30]},
        'bar': {'color': "darkred"},
        'steps': [{'range': [0, 10], 'color': "lightgreen"}, {'range': [10, 20], 'color': "yellow"}, {'range': [20, 30], 'color': "red"}],
        'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': 20}
    }
))
fig_kpi.update_layout(height=350)


# 3.2. Fase Kritis (Kelompok Umur)
fig_umur = px.bar(
    umur_data_sorted,
    x='kelompok_umur', y='prevalensi',
    title='2. Fase Kritis: Prevalensi Berdasarkan Kelompok Umur',
    color='prevalensi', color_continuous_scale=px.colors.sequential.Blues,
    text=umur_data_sorted['prevalensi'].round(1).astype(str) + '%'
)
fig_umur.update_traces(textposition='auto')

# 3.3. Area Prioritas (Kecamatan)
top_10_kecamatan = kecamatan_data_sorted.head(10).sort_values(by='prevalensi', ascending=True)
fig_kecamatan = px.bar(
    top_10_kecamatan,
    x='prevalensi', y='nama_kecamatan', orientation='h', 
    title='3. Area Prioritas: Top 10 Kecamatan (Prevalensi Stunting %)',
    color='prevalensi', color_continuous_scale=px.colors.sequential.Reds,
    text=top_10_kecamatan['prevalensi'].round(1).astype(str) + '%' 
)
fig_kecamatan.update_traces(textposition='outside')


# 3.4. Diagnostik Z-Score (Scatter Plot)
fig_zscore = px.scatter(
    df, x='zsc_tbu', y='zsc_bbu', 
    title='4. Diagnostik Z-Score (TB/U vs BB/U)',
    color='stunting_balita',
    color_discrete_map={'Ya': 'red', 'Tidak': 'green'},
    hover_data=['umur_balita', 'nama_kecamatan', 'jenis_kelamin_balita']
)
# Menambahkan garis batas WHO (Z-Score = -2)
fig_zscore.add_vline(x=-2, line_width=1, line_dash="dash", line_color="red")
fig_zscore.add_hline(y=-2, line_width=1, line_dash="dash", line_color="orange")
fig_zscore.update_layout(
    xaxis_title='Z-Score TB/U (Stunting)', 
    yaxis_title='Z-Score BB/U (Gizi Kurang)',
    height=500,
    showlegend=True
)

st.markdown("---")
print("CHECKPOINT LOG 5: Figure selesai dibuat. Memulai penempatan Streamlit.") 

# --- 4. LAYOUT STREAMLIT NATIVE ---

# Row 1: KPI and Umur
col1, col2 = st.columns([1, 2])
with col1:
    st.plotly_chart(fig_kpi, use_container_width=True)
with col2:
    st.plotly_chart(fig_umur, use_container_width=True)

st.markdown("---")

# Row 2: Kecamatan and Z-Score
col3, col4 = st.columns([1, 1])
with col3:
    st.plotly_chart(fig_kecamatan, use_container_width=True)
with col4:
    st.plotly_chart(fig_zscore, use_container_width=True)


# --- 5. INSIGHTS STREAMLIT ---
st.markdown("---")
st.subheader("💡 Insight Utama & Rekomendasi")
st.markdown(f"""
1.  **Area Prioritas:** Fokuskan intervensi ke Kecamatan **{kecamatan_fokus}** dengan prevalensi stunting tertinggi ({prevalensi_fokus:.1f}%).
2.  **Fase Kritis:** Kelompok usia **{umur_fokus}** menunjukkan prevalensi tertinggi, menandakan perlunya intervensi gizi intensif.
""")
st.subheader("Raw Data Sample")
st.dataframe(df.head())

print("CHECKPOINT LOG 6: Skrip selesai dieksekusi.")
