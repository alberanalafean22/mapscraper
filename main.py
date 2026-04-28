import streamlit as st
import pandas as pd
from apify_client import ApifyClient

# Konfigurasi Halaman
st.set_page_config(page_title="Maps Scraper - Apify", layout="wide")

st.title("📍 Google Maps Scraper")
st.subheader("Automasi pengambilan data lokasi menggunakan Apify")

# Sidebar untuk API Key
with st.sidebar:
    st.header("Konfigurasi API")
    apify_token = st.text_input("Masukkan Apify API Token", type="password")
    st.info("Token dapat ditemukan di Console Apify bagian Integrations.")

# Input Form di Area Utama
col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("Kategori Usaha / Kata Kunci", placeholder="Contoh: Coffee Shop")
with col2:
    location_param = st.text_input("Parameter Lokasi", placeholder="Contoh: Solok, West Sumatra")

limit = st.slider("Jumlah Maksimal Tempat", min_value=1, max_value=100, value=10)

# Tombol Eksekusi
if st.button("Mulai Scraping"):
    if not apify_token:
        st.error("Harap masukkan API Token Apify terlebih dahulu!")
    elif not keyword:
        st.warning("Masukkan kategori usaha yang dicari!")
    else:
        try:
            client = ApifyClient(apify_token)
            
            with st.spinner(f"Sedang mengambil data '{keyword}' di {location_param}..."):
                # Konfigurasi Input Actor (google-maps-extractor)
                run_input = {
                    "searchStrings": [f"{keyword} in {location_param}"],
                    "maxCrawledPlacesPerSearch": limit,
                    "language": "id",
                    "exportPlaceUrls": True,
                }

                # Menjalankan Actor
                #run = client.actor("apify/google-maps-scraper").call(run_input=run_input)
                run = client.actor("2Mdma1N6Fd0y3QEjR").call(run_input=run_input)
                
                # Mengambil Data dari Dataset
                dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
                
                if dataset_items:
                    raw_df = pd.DataFrame(dataset_items)
                    
                    # --- PROSES DATA ---
                    # Mengekstrak koordinat dari kolom 'location' (biasanya dictionary lat/lng)
                    if 'location' in raw_df.columns:
                        raw_df['latitude'] = raw_df['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
                        raw_df['longitude'] = raw_df['location'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)

                    # Pemilihan kolom sesuai permintaan: Nama, Koordinat, Kategori, Alamat
                    desired_cols = {
                        'title': 'Nama Usaha',
                        'categoryName': 'Kategori',
                        'address': 'Alamat',
                        'latitude': 'Latitude',
                        'longitude': 'Longitude'
                    }
                    
                    # Memastikan kolom ada sebelum di-filter
                    final_cols = [c for c in desired_cols.keys() if c in raw_df.columns]
                    df_filtered = raw_df[final_cols].rename(columns=desired_cols)

                    st.success(f"Berhasil mengambil {len(df_filtered)} data!")
                    
                    # Tampilkan Preview Tabel
                    st.dataframe(df_filtered, use_container_width=True)

                    # Fitur Download CSV
                    csv = df_filtered.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Hasil (CSV)",
                        data=csv,
                        file_name=f"data_{keyword.lower().replace(' ', '_')}.csv",
                        mime='text/csv',
                    )
                    
                    # Opsional: Tampilkan Peta Sederhana jika ada koordinat
                    if 'Latitude' in df_filtered.columns and 'Longitude' in df_filtered.columns:
                        st.map(df_filtered.dropna(subset=['Latitude', 'Longitude']))

                else:
                    st.info("Tidak ada data yang ditemukan. Coba perjelas parameter lokasi.")

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# Footer
st.divider()
st.caption("Developed for Geospatial and Data Science Workflow")
