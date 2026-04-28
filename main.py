import streamlit as st
import pandas as pd
from apify_client import ApifyClient

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Maps Scraper - Apify", layout="wide")

st.title("📍 Google Maps Extractor")
st.subheader("Automasi pengambilan data lokasi (Nama, Koordinat, Kategori, Alamat)")

# --- SIDEBAR: KONFIGURASI API ---
with st.sidebar:
    st.header("🔑 API Configuration")
    apify_token = st.text_input("Apify API Token", type="password", help="Dapatkan di console.apify.com")
    st.divider()
    st.info("""
    **Tips Pencarian:**
    - **Keyword**: Jenis usaha (e.g., 'Apotek', 'Bengkel')
    - **Lokasi**: Nama kota saja (e.g., 'Kota Solok')
    """)

# --- INPUT FORM ---
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    keyword = st.text_input("Kategori Usaha", placeholder="Contoh: Coffee Shop")
with col2:
    city_param = st.text_input("Kota (Location)", placeholder="Contoh: Kota Solok")
with col3:
    limit = st.number_input("Limit Data", min_value=1, max_value=200, value=10)

# --- TOMBOL EKSEKUSI ---
if st.button("🚀 Mulai Scraping", use_container_width=True):
    if not apify_token:
        st.error("Silakan masukkan API Token di sidebar!")
    elif not keyword or not city_param:
        st.warning("Keyword dan Kota tidak boleh kosong!")
    else:
        try:
            client = ApifyClient(apify_token)
            
            with st.spinner(f"Sedang mencari '{keyword}' di '{city_param}'..."):
                # Konfigurasi Input menyesuaikan UI aktor compass/google-maps-extractor
                run_input = {
                    "searchStrings": [keyword],
                    "locationQuery": city_param,
                    "maxCrawledPlacesPerSearch": limit,
                    "country": "Indonesia",
                    "city": city_param,
                    "language": "en", # Berdasarkan screenshot Anda
                    "exportPlaceUrls": True,
                }

                # Menjalankan Aktor menggunakan ID: 2Mdma1N6Fd0y3QEjR
                run = client.actor("2Mdma1N6Fd0y3QEjR").call(run_input=run_input)
                
                # Mengambil data dari dataset hasil scraping
                dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
                
                if dataset_items:
                    raw_df = pd.DataFrame(dataset_items)
                    
                    # --- EKSTRAKSI DATA SPESIFIK ---
                    # 1. Ekstrak Koordinat (Lat/Lng biasanya ada di kolom 'location')
                    if 'location' in raw_df.columns:
                        raw_df['Latitude'] = raw_df['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
                        raw_df['Longitude'] = raw_df['location'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)

                    # 2. Pemetaan nama kolom untuk tampilan user
                    mapping = {
                        'title': 'Nama Usaha',
                        'categoryName': 'Kategori',
                        'address': 'Alamat',
                        'Latitude': 'Latitude',
                        'Longitude': 'Longitude'
                    }
                    
                    # Filter hanya kolom yang ada di dataset
                    available_cols = [c for c in mapping.keys() if c in raw_df.columns]
                    df_final = raw_df[available_cols].rename(columns=mapping)

                    # --- TAMPILKAN HASIL ---
                    st.success(f"Berhasil menarik {len(df_final)} data lokasi!")
                    
                    # Layout kolom untuk tabel dan peta
                    tab1, tab2 = st.tabs(["📊 Tabel Data", "🗺️ Visualisasi Peta"])
                    
                    with tab1:
                        st.dataframe(df_final, use_container_width=True)
                        
                        # Tombol Download
                        csv = df_final.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Hasil (CSV)",
                            data=csv,
                            file_name=f"data_{keyword.lower().replace(' ', '_')}_{city_param.lower()}.csv",
                            mime='text/csv',
                        )
                    
                    with tab2:
                        if 'Latitude' in df_final.columns and 'Longitude' in df_final.columns:
                            # Menghapus baris yang tidak punya koordinat untuk peta
                            map_data = df_final.dropna(subset=['Latitude', 'Longitude'])
                            st.map(map_data)
                        else:
                            st.warning("Data koordinat tidak ditemukan untuk peta.")

                else:
                    st.info("Tidak ada data ditemukan. Coba gunakan keyword yang lebih umum atau cek penulisan kota.")

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")

# --- FOOTER ---
st.divider()
st.caption("Workflow: Streamlit -> Apify API -> Google Maps Scraper (Compass)")
