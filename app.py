import streamlit as st
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="MTP Dashboard System", layout="wide")

# 1. DATABASE KREDENSIAL (Sesuai Permintaan)
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
    st.session_state.uploaded_data = None  # Untuk menyimpan data CSV Admin
if "ic_uploads" not in st.session_state:
    st.session_state.ic_uploads = []  # Untuk menyimpan data bukti foto dari IC

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
                    df = pd.read_csv(uploaded_file)
                    
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
            
            # Menampilkan data CSV yang ada
            if st.session_state.uploaded_data is not None:
                st.subheader("Data Saat Ini")
                st.dataframe(st.session_state.uploaded_data)
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
        
        # Ambil list NBH dari data admin jika ada, kalau tidak pakai manual text input
        st.subheader("Input Bukti Kerja")
        if st.session_state.uploaded_data is not None and 'NBH' in st.session_state.uploaded_data.columns:
            nbh_options = st.session_state.uploaded_data['NBH'].unique().tolist()
            nbh_choice = st.selectbox("Pilih NBH", nbh_options)
        else:
            nbh_choice = st.text_input("Masukkan/Pilih NBH (Ketik Manual karena CSV Admin Kosong)")
            
        img_file = st.file_uploader("Upload Bukti Foto", type=["jpg", "jpeg", "png"])
        
        if st.button("Submit Upload", type="primary"):
            if nbh_choice and img_file:
                # Simpan data ke session state dengan primary status "Selesai" sesuai request
                st.session_state.ic_uploads.append({
                    "nbh": nbh_choice,
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
        
        tab1, tab2 = st.tabs(["📊 Data NBH", "💬 Bukti Chat"])
        
        with tab1:
            st.header("Melihat Data NBH & Progress")
            if st.session_state.uploaded_data is not None:
                st.dataframe(st.session_state.uploaded_data)
            else:
                st.info("Belum ada data NBH utama dari Admin.")
                
            st.subheader("Status Foto dari IC")
            if st.session_state.ic_uploads:
                # Menampilkan rangkuman status foto untuk toko
                toko_view = [{"NBH": x["nbh"], "Status Dokumen": x["status"]} for x in st.session_state.ic_uploads]
                st.table(toko_view)
            else:
                st.info("Belum ada update bukti fisik dari IC.")
                
        with tab2:
            st.header("Bukti Chat")
            st.info("Fitur tampilan bukti chat. (Bisa disesuaikan dengan kebutuhan integrasi masa depan)")
            # Simulasi atau integrasi file chat di sini
            st.text_area("Catatan/Pesan Toko ke Tim IC", placeholder="Tulis pesan atau pantau log chat di sini...")
