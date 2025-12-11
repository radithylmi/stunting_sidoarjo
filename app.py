import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st # <-- PENTING: Tambahkan import Streamlit

# --- 1. PEMUATAN DATA (FIXED) ---

# Data mentah CSV yang Anda unggah (Disertakan di sini agar skrip dapat berjalan)
data_csv_snippet = """
tgl_pengambilan_data,nik_balita,nama_balita,tgl_lahir_balita,jenis_kelamin_balita,umur_balita,bb_balita_lahir,tb_balita_lahir,bb_balita,tb_balita,zsc_tbu,zsc_bbtb,zsc_bbu,stunting_balita,status_tbu,status_bbtb,status_bbu,nama_responden,nik_responden,no_hp_responden,tgl_lahir_responden,nama_puskesmas,nama_kecamatan,nama_desa,rt,rw
1/3/2025,s0:1wNMg/i1akEl3uEbwDKvZpk6d0IcoGhYprlQsOW47UX659YuPs9PfSCgOyY=,s0:4ZOaffhqPfJ76xo7CblKY2D4SKPaWyj3kZEaMmo5jDSsl8vj20AIXNg1aIJjmTYx,s0:aoBbahZAiUabN3Li0y09myqA2Y01j1O3eKC3Qx+lkeB0T+QlryI=,Laki - Laki,2 Tahun 5 Bulan,1.4,39,10,84,-2.158,-1.695,-2.324,Ya,Pendek,Gizi Baik,BB Kurang,s0:iLFdMgDCkN31FFEsZb/oKlyPlSfGOyBnJmw1fg...,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV8lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
11/18/2025,s0:pOqNnzi7gIsbELF5fwZaTdm3JQZ2P4j+UEZu0tp2om152mUFWQZjnIGRDMw=,s0:KNKG6i1DmDfWxeNlMWkhemhM6ySJEV37fvRToEVObvnNgfjXhA==,s0:/RGgJmWbTO0RERKsOjtZzmfT1U5wFVr...,Laki - Laki,1 Tahun 0 Bulan,3.3,50,7.9,74.5,-0.894,-2.184,-1.997,Tidak,Normal,Gizi Kurang,BB Normal,s0:GMgpcLMH9uog+gcuCRkN2hxl7jZ3nBgvp4SfhSi5gak5tg==,s0:Z0DSH4HK+vD1VokPofbaOPdpj2kmTWG8E+dqfIKJ8ULS3iRZw/g4TXlvzOI=,s0:o9mJpfL7c3A94OGkVXN8nIk4wIBm+DEKrJI/AaFsKdBDTC9r5rP/PA==,s0:XEU9oIW2D5WaIc3JmfJq7fVV8lcodGNmP8xbqV0RjkI+hW8gSBU=,Puskesmas Porong,Porong,Pamotan,05,02
"""

# Membaca data dari string ke DataFrame
df = pd.read_csv(io.StringIO(data_csv_snippet))

# Cek apakah DataFrame berhasil dimuat (opsional)
if df.empty:
    st.error("Gagal memuat data dari CSV snippet. Harap periksa format datanya.")
else:
    # --- 2. DATA PREPARATION (Memastikan kolom numerik benar) ---
    try:
        # Mengubah kolom Z-Score menjadi numerik
        df['zsc_tbu'] = pd.to_numeric(df['zsc_tbu'], errors='coerce')
        df['zsc_bbu'] = pd.to_numeric(df['zsc_bbu'], errors='coerce')
        df['zsc_bbtb'] = pd.to_numeric(df['zsc_bbtb'], errors='coerce')
        df.dropna(subset=['zsc_tbu', 'zsc_bbu', 'zsc_bbtb', 'nama_kecamatan'], inplace=True)
    except Exception as e:
        st.error(f"Error saat mengkonversi kolom ke numerik: {e}")
        st.stop()
    
    # Menghitung data agregasi untuk visualisasi
    kecamatan_data_sorted = df.groupby('nama_kecamatan').size().reset_index(name='Jumlah Balita')
    kecamatan_data_sorted = kecamatan_data_sorted.sort_values(by='Jumlah Balita', ascending=False)


    # --- 3. PEMBUATAN SUBPLOTS (DASHBOARD) ---
    
    # Inisialisasi subplot dengan 2 baris dan 2 kolom
    fig_dashboard = make_subplots(
        rows=2, 
        cols=2, 
        specs=[
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "scatter"}]
        ],
        subplot_titles=(
            '1. Jumlah Balita per Kecamatan (Bar Plot)',
            '2. Persentase Status Stunting (Pie Chart)',
            '3. Status BB/TB per Kecamatan (Bar Plot)',
            '4. Sebaran Z-Score TB/U vs BB/U (Scatter Plot)'
        )
    )

    # A. Plot 1: Bar Plot Jumlah Balita per Kecamatan
    fig_dashboard.add_trace(
        go.Bar(
            x=kecamatan_data_sorted['nama_kecamatan'], 
            y=kecamatan_data_sorted['Jumlah Balita'],
            marker_color='blue'
        ),
        row=1, col=1
    )

    # B. Plot 2: Pie Chart Status Stunting
    stunting_counts = df['stunting_balita'].value_counts()
    fig_dashboard.add_trace(
        go.Pie(
            labels=stunting_counts.index, 
            values=stunting_counts.values,
            name='Stunting'
        ),
        row=1, col=2
    )

    # C. Plot 3: Bar Plot Status BB/TB per Kecamatan
    df_bbtb = df.groupby(['nama_kecamatan', 'status_bbtb']).size().reset_index(name='Count')
    # Menggunakan Plotly Express di dalam Subplot bisa rumit, jadi kita pakai go.Bar()
    for status in df_bbtb['status_bbtb'].unique():
        data_status = df_bbtb[df_bbtb['status_bbtb'] == status]
        fig_dashboard.add_trace(
            go.Bar(
                x=data_status['nama_kecamatan'], 
                y=data_status['Count'], 
                name=status
            ),
            row=2, col=1
        )
    fig_dashboard.update_layout(barmode='stack')

    # D. Plot 4: Scatter Plot Z-Score
    fig_dashboard.add_trace(
        go.Scatter(
            x=df['zsc_tbu'], 
            y=df['zsc_bbu'],
            mode='markers',
            name='Balita',
            marker=dict(size=8, opacity=0.6, color=df['status_tbu'].map({'Pendek': 'red', 'Sangat Pendek': 'darkred', 'Normal': 'green'})),
            hovertext=df['nama_balita']
        ),
        row=2, col=2
    )
    fig_dashboard.update_xaxes(title_text='Z-Score TB/U (Stunting)', row=2, col=2)
    fig_dashboard.update_yaxes(title_text='Z-Score BB/U (Gizi)', row=2, col=2)
    
    # --- 4. PENAMBAHAN ANOTASI (Sesuai permintaan Anda) ---
    fig_dashboard.add_annotation(
        x=0.5, 
        y=0.5, 
        xref="paper", 
        yref="paper", 
        text="**Data Skrining Stunting 2025**", # <-- Teks sudah diisi
        showarrow=False, 
        font=dict(
            size=30, # Diperbesar agar terlihat jelas
            color="lightgray", 
            family="Arial, sans-serif"
        ),
        xanchor='center',
        yanchor='middle',
        opacity=0.3 # Diatur agar tidak menutupi visualisasi
    )


    # --- 5. LAYOUT DAN DISPLAY (FIXED) ---
    fig_dashboard.update_layout(
        height=850,
        width=1100,
        title_text="**Dashboard Kecerdasan Bisnis: Analisis Skrining Stunting**",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
    )

    # Hapus fig_dashboard.show() dan ganti dengan st.plotly_chart()
    st.plotly_chart(fig_dashboard, use_container_width=True) # <-- SOLUSI: Menggunakan Streamlit API
    
    
    # --- 6. DISPLAY INSIGHTS DI STREAMLIT (FIXED) ---
    st.subheader("💡 Insight Utama Dashboard")
    
    # Pastikan data agregasi ada sebelum diakses
    if not kecamatan_data_sorted.empty:
        st.markdown(f"""
        1. **Wilayah Prioritas:** Fokuskan intervensi ke Kecamatan **{kecamatan_data_sorted.iloc[0]['nama_kecamatan']}**
        2. **Jumlah Balita Tertinggi:** Wilayah ini memiliki jumlah balita tertinggi, yaitu **{kecamatan_data_sorted.iloc[0]['Jumlah Balita']}** anak.
        """)
