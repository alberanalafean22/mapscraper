import streamlit as st
import pandas as pd
from apify_client import ApifyClient

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Maps Scraper Pro", layout="wide", page_icon="📍")

st.title("📍 Google Maps Data Extractor")
st.markdown("""
Aplikasi ini menarik data **Nama Usaha, Kategori, Alamat, dan Koordinat** langsung dari Google Maps menggunakan API Apify.
""")

# --- SIDEBAR KONFIGURASI ---
with st.sidebar:
    st.header("🔑 Pengaturan API")
    apify_token = st.text_input("Apify API Token", type="password")
    st.divider()
    st.markdown("### 💡 Tips")
    st.caption("- Gunakan keyword umum (contoh: 'Cafe')")
    st.caption("- Gunakan lokasi kota (contoh: 'Padang')")
    debug_mode = st.checkbox("Aktifkan Mode Debug", value=False)

# --- INPUT FORM ---
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    keyword = st.text_input("Kategori Usaha", placeholder="Contoh: Bengkel")
with col2:
    location_input = st.text_input("Lokasi / Kota", placeholder="Contoh: Solok")
with col3:
    limit = st.number_input("Limit", min_value=1, max_value=500, value=10)

# --- LOGIKA SCRAPING ---
if st.button("🚀 Jalankan Scraping Sekarang", use_container_width=True):
    if not apify_token:
        st.error("Token Apify wajib diisi!")
    elif not keyword:
        st.warning("Keyword pencarian tidak boleh kosong!")
    else:
        try:
            client = ApifyClient(apify_token)
            
            with st.spinner(f"Menghubungi robot Apify untuk mencari '{keyword}'..."):
                # Gabungkan keyword dan lokasi untuk akurasi maksimal
                search_query = f"{keyword} di {location_input}" if location_input else keyword
                
                # Input yang paling kompatibel dengan aktor 2Mdma1N6Fd0y3QEjR
                run_input = {
                    "searchStrings": [search_query],
                    "maxCrawledPlacesPerSearch": limit,
                    "language": "id",
                    "exportPlaceUrls": True,
                }

                # Menjalankan Aktor
                run = client.actor("2Mdma1N6Fd0y3QEjR").call(run_input=run_input)
                
                # Mengambil data dari Dataset
                items = client.dataset(run["defaultDatasetId"]).list_items().items
                
                if items:
                    df_raw = pd.DataFrame(items)
                    
                    if debug_mode:
                        st.subheader("🛠️ Debug: Kolom Tersedia")
                        st.write(df_raw.columns.tolist())
                        st.write(df_raw.head(3))

                    # --- PROSES EKSTRAKSI DATA ---
                    # 1. Ekstrak Lat/Lng dari kolom 'location'
                    if 'location' in df_raw.columns:
                        df_raw['Latitude'] = df_raw['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
                        df_raw['Longitude'] = df_raw['location'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)

                    # 2. Pemetaan kolom (Mapping nama kolom agar rapi)
                    # Kami menggunakan get() agar jika kolom tidak ada, aplikasi tidak crash
                    output_data = pd.DataFrame()
                    output_data['Nama Usaha'] = df_raw['title'] if 'title' in df_raw.columns else "N/A"
                    output_data['Kategori'] = df_raw['categoryName'] if 'categoryName' in df_raw.columns else "N/A"
                    output_data['Alamat'] = df_raw['address'] if 'address' in df_raw.columns else "N/A"
                    
                    if 'Latitude' in df_raw.columns:
                        output_data['Latitude'] = df_raw['Latitude']
                        output_data['Longitude'] = df_raw['Longitude']

                    # --- TAMPILKAN HASIL ---
                    st.success(f"Berhasil menemukan {len(output_data)} data!")
                    
                    tab_table, tab_map = st.tabs(["📊 Tabel Data", "🗺️ Peta Lokasi"])
                    
                    with tab_table:
                        st.dataframe(output_data, use_container_width=True)
                        
                        # Download CSV
                        csv = output_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"scraping_{keyword.replace(' ', '_')}.csv",
                            mime='text/csv'
                        )
                        
                    with tab_map:
                        if 'Latitude' in output_data.columns:
                            # Bersihkan data yang koordinatnya kosong
                            map_df = output_data.dropna(subset=['Latitude', 'Longitude'])
                            if not map_df.empty:
                                st.map(map_df[['Latitude', 'Longitude']])
                            else:
                                st.info("Tidak ada data koordinat untuk ditampilkan di peta.")
                        else:
                            st.warning("Kolom koordinat tidak ditemukan.")

                else:
                    st.error("❌ Tidak ada data ditemukan! Coba hapus parameter lokasi atau ganti keyword.")
                    st.info("Saran: Jika mencari 'Kopi', cukup tulis 'Coffee Shop' dan di kolom lokasi tulis 'Solok'.")

        except Exception as e:
            st.error(f"Terjadi Kesalahan: {str(e)}")

# --- FOOTER ---
st.divider()
st.caption("Powered by Apify Scraper Engine | 2026 Update")
