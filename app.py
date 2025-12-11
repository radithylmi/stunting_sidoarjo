import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Atur style visualisasi
sns.set_style("whitegrid")

# --- 1. PEMUATAN DATA ---
# Menggunakan path yang Anda tentukan
file_path = '/content/data_skrinning_stunting(1).csv' 
try:
    df = pd.read_csv(file_path)
    print("✅ Data berhasil dimuat.")
except FileNotFoundError:
    print(f"❌ Error: File tidak ditemukan di path: {file_path}")
    # Karena ini adalah eksekusi, kita harus memastikan data_skrinning_stunting(1).csv ada
    # Jika Anda menjalankan ini di Colab, pastikan file sudah di-upload.
    exit()

# Mengubah nama kolom yang panjang agar mudah diakses
df.columns = [col.lower().replace(' ', '_').replace('.', '') for col in df.columns]

# --- 2. DATA CLEANING & FEATURE ENGINEERING ---

# 2.1. Feature Engineering: Membuat Kolom Target Biner dan Umur
# Target: Stunting (Ya=1, Tidak=0)
df['is_stunting'] = df['stunting_balita'].apply(lambda x: 1 if x == 'Ya' else 0)

# Kategori Umur Balita (Fase Kritis BI)
def categorize_age(umur_str):
    """Mengkonversi string umur menjadi total bulan dan mengkategorikannya."""
    if pd.isna(umur_str) or not isinstance(umur_str, str):
        return 'Tidak Diketahui'
    
    parts = umur_str.split(' ')
    tahun = 0
    bulan = 0
    
    # Mencari dan mengkonversi komponen tahun dan bulan
    for i, part in enumerate(parts):
        if part.isdigit():
            if i + 1 < len(parts):
                if parts[i+1] == 'Tahun':
                    tahun = int(part)
                elif parts[i+1] == 'Bulan':
                    bulan = int(part)
    
    # Jika format standar (misal '1 Tahun 0 Bulan')
    if len(parts) >= 3 and parts[1] == 'Tahun' and parts[3] == 'Bulan':
        try:
            tahun = int(parts[0])
            bulan = int(parts[2])
        except ValueError:
            pass # Lanjut menggunakan parsing parsial jika ada error
            
    total_bulan = tahun * 12 + bulan
    
    # Pengkategorian yang terurut (A, B, C, D) untuk visualisasi yang rapi
    if total_bulan <= 12:
        return 'A. 0-12 Bulan (Bayi)'
    elif total_bulan <= 24:
        return 'B. 13-24 Bulan (Tahun Kritis)'
    elif total_bulan <= 36:
        return 'C. 25-36 Bulan'
    elif total_bulan <= 60:
        return 'D. 37-60 Bulan'
    else:
        return 'E. > 60 Bulan'

df['kelompok_umur'] = df['umur_balita'].apply(categorize_age)


# 2.2. Cleaning Data Kontinu
# Mengganti nilai 0 pada BB/TB Lahir dengan NaN (asumsi data hilang/tidak valid)
df['bb_balita_lahir'] = df['bb_balita_lahir'].replace(0, np.nan)
df['tb_balita_lahir'] = df['tb_balita_lahir'].replace(0, np.nan)


# 2.3. Filtering: Hapus baris dengan nilai lokasi/status gizi yang hilang
df.dropna(subset=['nama_kecamatan', 'stunting_balita'], inplace=True)
print(f"Jumlah baris setelah cleaning: {len(df)}")


# --- 3. ANALISIS PERHITUNGAN UNTUK DASHBOARD ---

# Menghitung prevalensi stunting
total_balita = len(df)
prevalensi_stunting = (df['is_stunting'].sum() / total_balita) * 100

# Segmentasi Berdasarkan Kecamatan (Area Prioritas)
kecamatan_data = df.groupby('nama_kecamatan')['is_stunting'].agg(
    total_kasus='sum',
    total_populasi='count'
).reset_index()
kecamatan_data['prevalensi'] = (kecamatan_data['total_kasus'] / kecamatan_data['total_populasi']) * 100
kecamatan_data_sorted = kecamatan_data.sort_values(by='prevalensi', ascending=False)

# Segmentasi Berdasarkan Kelompok Umur (Fase Kritis)
umur_data = df.groupby('kelompok_umur')['is_stunting'].agg(
    total_kasus='sum',
    total_populasi='count'
).reset_index()
umur_data['prevalensi'] = (umur_data['total_kasus'] / umur_data['total_populasi']) * 100
umur_data_sorted = umur_data.sort_values(by='kelompok_umur', ascending=True)


# --- 4. VISUALISASI PLOTLY UNTUK DASHBOARD ---

# 4.1. Visualisasi Area Prioritas (Kecamatan) - Bar Chart Horizontal Interaktif
# Mengambil Top 10 dan mengurutkan secara ascending agar yang tertinggi di atas pada plot horizontal
top_10_kecamatan = kecamatan_data_sorted.head(10).sort_values(by='prevalensi', ascending=True)

fig_kecamatan = px.bar(
    top_10_kecamatan,
    x='prevalensi',
    y='nama_kecamatan',
    orientation='h', 
    labels={'prevalensi': 'Prevalensi (%)', 'nama_kecamatan': 'Kecamatan'},
    color='prevalensi',
    color_continuous_scale=px.colors.sequential.Reds,
    text=top_10_kecamatan['prevalensi'].round(1).astype(str) + '%' 
)
fig_kecamatan.update_traces(textposition='outside')


# 4.2. Visualisasi Fase Kritis (Kelompok Umur) - Bar Chart Vertikal Interaktif
fig_umur = px.bar(
    umur_data_sorted,
    x='kelompok_umur',
    y='prevalensi',
    labels={'prevalensi': 'Prevalensi (%)', 'kelompok_umur': 'Kelompok Umur'},
    color='prevalensi',
    color_continuous_scale=px.colors.sequential.Blues,
    text=umur_data_sorted['prevalensi'].round(1).astype(str) + '%'
)
fig_umur.update_traces(textposition='auto')


# 4.3. Visualisasi Z-Score (Diagnostik) - Scatter Plot Interaktif
fig_zscore = px.scatter(
    df, 
    x='zsc_tbu', 
    y='zsc_bbu', 
    color='stunting_balita',
    labels={'zsc_tbu': 'Z-Score TB/U', 'zsc_bbu': 'Z-Score BB/U'},
    color_discrete_map={'Ya': 'red', 'Tidak': 'green'},
    hover_data=['umur_balita', 'nama_kecamatan', 'jenis_kelamin_balita']
)
# Menambahkan garis batas WHO (Z-Score = -2)
# Garis-garis ini akan ditambahkan ke subplot di langkah selanjutnya

# 4.4. KPI Card (Prevalensi Total)
fig_kpi = go.Figure(go.Indicator(
    mode="number+gauge",
    value=prevalensi_stunting,
    title={'text': "<b>Prevalensi Stunting Total (%)</b>"},
    number={'suffix': "%", 'font': {'size': 48}},
    gauge={
        'axis': {'range': [None, 30], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkred"},
        'steps': [
            {'range': [0, 10], 'color': "lightgreen"},
            {'range': [10, 20], 'color': "yellow"}, 
            {'range': [20, 30], 'color': "red"},
        ],
        'threshold': {
            'line': {'color': "black", 'width': 4},
            'thickness': 0.75,
            'value': 20 
        }
    }
))
fig_kpi.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))


# --- 5. MERANGKAI SEMUA KOMPONEN MENJADI DASHBOARD AKHIR ---

# Membuat layout subplots 2x2
fig_dashboard = make_subplots(
    rows=2,
    cols=2,
    specs=[
        [{"type": "indicator"}, {"type": "xy"}], 
        [{"type": "xy"}, {"type": "xy"}]        
    ],
    subplot_titles=(
        "KPI: Prevalensi Stunting Total",
        "Fase Kritis: Prevalensi Berdasarkan Kelompok Umur",
        "Area Prioritas: Top 10 Kecamatan (Prevalensi Stunting %)",
        "Diagnostik Z-Score (TB/U vs BB/U)"
    )
)

# Row 1
fig_dashboard.add_trace(fig_kpi.data[0], row=1, col=1)
for trace in fig_umur.data: fig_dashboard.add_trace(trace, row=1, col=2)

# Row 2
for trace in fig_kecamatan.data: fig_dashboard.add_trace(trace, row=2, col=1)
for trace in fig_zscore.data: fig_dashboard.add_trace(trace, row=2, col=2)

# Menambahkan garis batas Z-Score pada subplot diagnostik (Rata-rata 2, Kolom 2)
fig_dashboard.add_shape(
    type="line", x0=-2, y0=-5, x1=-2, y1=5, 
    line=dict(color="gray", width=1, dash="dash"), row=2, col=2
)
fig_dashboard.add_shape(
    type="line", x0=-5, y0=-2, x1=5, y1=-2, 
    line=dict(color="gray", width=1, dash="dash"), row=2, col=2
)
# Mengatur label sumbu untuk Scatter Plot di Subplot (karena Plotly Subplot tidak otomatis membawa label sumbu dari px.scatter)
fig_dashboard.update_xaxes(title_text='Z-Score TB/U', row=2, col=2)
fig_dashboard.update_yaxes(title_text='Z-Score BB/U', row=2, col=2)
# Tambahkan diagram WHO Z-Score Chart untuk konteks visual
# Visualisasi ini membantu interpretasi bagaimana Z-Score dihubungkan dengan Stunting (TB/U) dan Gizi Kurang (BB/U). 
fig_dashboard.add_annotation(
    x=0.5, y=0.5, xref="paper", yref="paper", 
    text="", 
    showarrow=False, font=dict(size=12, color="blue")
)


# Layout Akhir Dashboard
fig_dashboard.update_layout(
    height=850,
    width=1100,
    title_text="**Dashboard Kecerdasan Bisnis: Analisis Skrining Stunting**",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
)

fig_dashboard.show()

print("\n--- Insight Utama Dashboard ---")
print(f"1. **Wilayah Prioritas:** Fokuskan intervensi ke Kecamatan **{kecamatan_data_sorted.iloc[0]['nama_kecamatan']}** (terlihat jelas pada grafik Area Prioritas).")
print(f"2. **Fase Kritis:** Kelompok usia **{umur_data_sorted.iloc[0]['kelompok_umur']}** menunjukkan risiko tertinggi, menuntut intervensi gizi intensif pada fase tersebut.")
print("3. **Diagnostik Z-Score:** Plot menunjukkan sebaran status gizi, membantu mengidentifikasi balita yang menderita Stunting (TB/U < -2) atau Gizi Kurang (BB/U < -2) secara visual.")
