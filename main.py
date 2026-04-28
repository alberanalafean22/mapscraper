# ... (kode streamlit lainnya)

        try:
            client = ApifyClient(apify_token)
            
            with st.spinner(f"Sedang mengambil data '{keyword}' di {location_param}..."):
                # Konfigurasi Input khusus untuk aktor compass/google-maps-extractor
                run_input = {
                    "searchStrings": [keyword],  # Kata kunci usaha saja
                    "maxCrawledPlacesPerSearch": limit,
                    "language": "en", # Sesuaikan dengan gambar kamu (English)
                    
                    # Parameter Lokasi Berdasarkan Gambar:
                    "country": "Indonesia",
                    "city": location_param,  # Mengambil input dari kolom lokasi di Streamlit
                    
                    # Tambahan agar hasil lebih akurat
                    "locationQuery": location_param,
                    "exportPlaceUrls": True,
                }

                # Menggunakan ID unik aktor sesuai link yang kamu berikan
                run = client.actor("2Mdma1N6Fd0y3QEjR").call(run_input=run_input)
                
                # Mengambil Data
                dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
                
                if dataset_items:
                    df = pd.DataFrame(dataset_items)
                    
                    # Ambil kolom spesifik sesuai permintaanmu
                    # Nama Usaha: 'title'
                    # Kategori: 'categoryName'
                    # Alamat: 'address'
                    # Koordinat: biasanya ada di 'location' -> lat, lng
                    
                    if 'location' in df.columns:
                        df['Latitude'] = df['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
                        df['Longitude'] = df['location'].apply(lambda x: x.get('lng') if isinstance(x, dict) else None)

                    # Seleksi kolom akhir
                    cols_to_show = ['title', 'categoryName', 'address', 'Latitude', 'Longitude']
                    # Filter hanya kolom yang benar-benar ada di hasil scraping
                    df_display = df[[c for c in cols_to_show if c in df.columns]]
                    
                    st.success(f"Berhasil menarik {len(df_display)} data!")
                    st.dataframe(df_display, use_container_width=True)
                    
                    # Tombol Download
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download CSV", csv, f"maps_{location_param}.csv", "text/csv")
                else:
                    st.warning("Data tidak ditemukan. Tips: Masukkan nama kota saja di kolom lokasi (Contoh: 'Solok').")

        except Exception as e:
            st.error(f"Error: {e}")
