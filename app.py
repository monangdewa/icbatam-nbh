import streamlit as st
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="MTP Dashboard System", layout="wide")

# 1. DATABASE KREDENSIAL
CREDENTIALS = {
    "Admin": {"user": "MTP", "pwd": "1712"},
    "IC Upload": {"user": "ICBTM", "pwd": "@ICBTM"},
    "Toko": {"user": "BTMJUARA", "pwd": "BTMJUARA"}
}

# 2. INISIALISASI SESSION STATE (Penyimpanan Data Sementara)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None  # Menyimpan dataframe CSV
if "ic_uploads" not in st.session_state:
    st.session_state.ic_uploads = []  # Menyimpan data bukti foto dari IC

# 3. FUNGSI LOGOUT
def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ==========================================
# HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 MTP System Login")
    st.subheader("Silakan pilih jenis login dan masukkan akun Anda")
    
    # Form Login
    role_choice = st.selectbox("Jenis Login", ["Admin", "IC Upload", "Toko"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login", type="primary"):
        target = CREDENTIALS[role_choice]
        if username == target["user"] and password == target["pwd"]:
            st.session_state.logged_in = True
            st.session_state.role = role_choice
            st.success(f"Login berhasil sebagai {role_choice}!")
            st.rerun()
        else:
            st.error("Username atau Password salah. Silakan coba lagi.")

# ==========================================
# HALAMAN DASHBOARD (JIKA SUDAH LOGIN)
# ==========================================
else:
    # Sidebar untuk Navigasi & Logout
    st.sidebar.title(f"👤 {st.session_state.role}")
    st.sidebar.write("Selamat Datang!")
    if st.sidebar.button("Log Out", type="secondary"):
        logout()

    # --- DASHBOARD ADMIN ---
    if st.session_state.role == "Admin":
        st.title("🖥️ Dashboard Admin")
        
        tab1, tab2 = st.tabs(["📁 Upload & Kelola CSV", "📸 Cek & Edit Bukti Foto IC"])
        
        with tab1:
            st.header("Upload Data CSV")
            
            # Pilihan hapus data sebelumnya
            delete_previous = st.radio("Hapus data sebelumnya sebelum upload baru?", ("Tidak", "YA"))
            
            uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
            
            if uploaded_file is not None:
                if st.button("Proses File CSV"):
                    try:
                        # Menggunakan sep='|' karena file CSV menggunakan pemisah tanda pipa
                        df = pd.read_csv(uploaded_file, sep='|')
                        
                        if delete_previous == "YA":
                            st.session_state.uploaded_data = df
                            st.warning("Data sebelumnya telah dihapus dan digantikan data baru.")
                        else:
                            if st.session_state.uploaded_data is not None:
                                st.session_state.uploaded_data = pd.concat([st.session_state.uploaded_data, df], ignore_index=True)
                                st.success("Data baru berhasil ditambahkan ke data lama.")
                            else:
                                st.session_state.uploaded_data = df
                                st.success("Data berhasil diupload.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal membaca file. Pastikan format benar. Error: {e}")
            
            # Menampilkan data CSV yang ada dengan Fitur Filter Toko
            if st.session_state.uploaded_data is not None:
                st.write("---")
                st.subheader("🔍 Filter & Tampilkan Data Saat Ini")
                
                # Mengambil nama kolom pertama secara otomatis (kolom TOKO)
                nama_kolom_toko = st.session_state.uploaded_data.columns[0]
                
                # Mengambil daftar kode toko yang unik untuk dijadikan pilihan filter
                list_toko = sorted(st.session_state.uploaded_data[nama_kolom_toko].dropna().unique().tolist())
                
                # Input Filter Multi-select untuk Admin
                toko_terpilih = st.multiselect("Pilih Toko yang Ingin Ditampilkan:", options=list_toko, default=list_toko)
                
                # Menyaring data berdasarkan toko yang dipilih
                df_filtered = st.session_state.uploaded_data[st.session_state.uploaded_data[nama_kolom_toko].isin(toko_terpilih)]
                
                # Menampilkan tabel hasil filter
                st.dataframe(df_filtered, use_container_width=True)
            else:
                st.info("Belum ada data CSV yang diupload.")

        with tab2:
            st.header("Bukti Foto dari IC")
            if not st.session_state.ic_uploads:
                st.info("Belum ada bukti foto yang diupload oleh IC.")
            else:
                for idx, item in enumerate(st.session_state.ic_uploads):
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**NBH:** {item['nbh']}")
                            st.write(f"**Status:** {item['status']}")
                            st.image(item['image'], caption=f"Foto untuk NBH: {item['nbh']}", width=300)
                        with col2:
                            new_nbh = st.text_input(f"Edit NBH ({idx})", value=item['nbh'], key=f"admin_edit_{idx}")
                            if st.button(f"Simpan Perubahan ({idx})", key=f"admin_save_{idx}"):
                                st.session_state.ic_uploads[idx]['nbh'] = new_nbh
                                st.success("Data NBH berhasil diperbarui!")
                                st.rerun()
                                
                            if st.button(f"Hapus Foto ({idx})", key=f"admin_del_{idx}"):
                                st.session_state.ic_uploads.pop(idx)
                                st.error("Foto berhasil dihapus.")
                                st.rerun()

    # --- DASHBOARD IC UPLOAD ---
    elif st.session_state.role == "IC Upload":
        st.title("📤 Dashboard IC Upload")
        
        st.subheader("Input Bukti Kerja")
        
        # Mengecek apakah data CSV sudah ada untuk mengambil NBH secara otomatis
        if st.session_state.uploaded_data is not None:
            # Mencari kolom NBH atau menggunakan kolom indeks ke-1 jika nama kolom persisnya berbeda
            kolom_nbh = [col for col in st.session_state.uploaded_data.columns if 'NBH' in col]
            if kolom_nbh:
                nbh_options = st.session_state.uploaded_data[kolom_nbh[0]].dropna().unique().tolist()
                nbh_choice = st.selectbox("Pilih NBH", nbh_options)
            else:
                nbh_choice = st.text_input("Masukkan NBH (Ketik Manual)")
        else:
            nbh_choice = st.text_input("Masukkan NBH (Ketik Manual karena CSV Admin Kosong)")
            
        img_file = st.file_uploader("Upload Bukti Foto", type=["jpg", "jpeg", "png"])
        
        if st.button("Submit Upload", type="primary"):
            if nbh_choice and img_file:
                # Simpan data ke session state dengan primary status "Selesai"
                st.session_state.ic_uploads.append({
                    "nbh": str(nbh_choice),
                    "image": img_file,
                    "status": "Selesai"
                })
                st.success("Bukti berhasil diupload dengan status: Selesai!")
                st.rerun()
            else:
                st.error("Mohon isi NBH dan upload foto terlebih dahulu.")
                
        # Kelola foto yang sudah diupload oleh IC sendiri
        st.write("---")
        st.subheader("Riwayat Upload Anda")
        if not st.session_state.ic_uploads:
            st.info("Anda belum mengupload foto apapun.")
        else:
            for idx, item in enumerate(st.session_state.ic_uploads):
                with st.container(border=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**NBH:** {item['nbh']} | **Status:** {item['status']}")
                        st.image(item['image'], width=200)
                    with col2:
                        edit_nbh_ic = st.text_input(f"Ubah NBH", value=item['nbh'], key=f"ic_edit_{idx}")
                        if st.button(f"Update NBH", key=f"ic_save_{idx}"):
                            st.session_state.ic_uploads[idx]['nbh'] = edit_nbh_ic
                            st.success("NBH diperbarui.")
                            st.rerun()
                        if st.button(f"Hapus", key=f"ic_del_{idx}"):
                            st.session_state.ic_uploads.pop(idx)
                            st.warning("Data dihapus.")
                            st.rerun()

    # --- DASHBOARD TOKO ---
    elif st.session_state.role == "Toko":
        st.title("🏪 Dashboard Toko")
        
        # Fitur Input Mandiri untuk Toko memasukkan Kodenya sendiri
        st.subheader("Pengaturan Akses Toko")
        kode_toko_anda = st.text_input("Masukkan Kode Toko Anda untuk Filter Data (Contoh: TWSU, T2SU, TAPK):", value="TWSU").strip().upper()
        
        tab1, tab2 = st.tabs(["📊 Data NBH", "💬 Bukti Chat"])
        
        with tab1:
            st.header(f"Melihat Data NBH - Toko {kode_toko_anda}")
            
            if st.session_state.uploaded_data is not None:
                nama_kolom_toko = st.session_state.uploaded_data.columns[0]
                
                # Memfilter data utama: Hanya menampilkan baris yang kolom TOKO-nya cocok dengan input toko
                data_toko_ini = st.session_state.uploaded_data[st.session_state.uploaded_data[nama_kolom_toko].astype(str).str.strip().str.upper() == kode_toko_anda]
                
                if not data_toko_ini.empty:
                    st.dataframe(data_toko_ini, use_container_width=True)
                else:
                    st.warning(f"Tidak ada data NBH yang ditemukan di CSV untuk kode toko '{kode_toko_anda}'.")
            else:
                st.info("Belum ada data NBH utama dari Admin.")
                
            st.write("---")
            st.subheader("Status Foto dari IC")
            if st.session_state.ic_uploads:
                # Menampilkan status dokumen IC yang ada
                toko_view = [{"NBH": x["nbh"], "Status Dokumen": x["status"]} for x in st.session_state.ic_uploads]
                st.table(toko_view)
            else:
                st.info("Belum ada update bukti fisik dari IC.")
                
        with tab2:
            st.header("Bukti Chat")
            st.info("Fitur tampilan bukti chat toko.")
            st.text_area("Catatan/Pesan Toko ke Tim IC", placeholder="Tulis pesan atau pantau log chat di sini...")
