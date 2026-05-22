import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="IC Batam NBH ERP", layout="wide")

st.title("🔥 IC Batam - NBH Anti Fraud ERP System")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("nbh.db", check_same_thread=False)
c = conn.cursor()

# =========================
# TABLE NBH MASTER
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS nbh (
    id TEXT,
    toko TEXT,
    no_nrb TEXT,
    tgl_nrb TEXT,
    nama_barang TEXT,
    qty REAL,
    rph REAL,
    case_id TEXT
)
""")

# =========================
# TABLE BUKTI FOLLOW UP (WITH IMAGE)
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS bukti (
    id TEXT,
    case_id TEXT,
    toko TEXT,
    no_nrb TEXT,
    catatan TEXT,
    status TEXT,
    uploaded_by TEXT,
    created_at TEXT,
    foto BLOB
)
""")

conn.commit()

# =========================
# ROLE LOGIN (SIMPLE)
# =========================
role = st.sidebar.selectbox(
    "Login Role",
    ["Admin IC", "Tim Upload IC", "Toko"]
)

st.sidebar.divider()

# =========================
# LOAD DATA
# =========================
def load_nbh():
    return pd.read_sql("SELECT * FROM nbh", conn)

def load_bukti():
    return pd.read_sql("SELECT * FROM bukti", conn)

df = load_nbh()
df_bukti = load_bukti()

# =========================
# ADMIN IC
# =========================
if role == "Admin IC":

    st.subheader("📊 Dashboard Admin IC")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Case", df["case_id"].nunique() if not df.empty else 0)
    col2.metric("Total Toko", df["toko"].nunique() if not df.empty else 0)
    col3.metric("Total NRB", df["no_nrb"].nunique() if not df.empty else 0)

    st.divider()

    st.subheader("📥 Upload NBH CSV (PIPE | FORMAT)")

    file = st.file_uploader("Upload CSV NBH", type=["csv"])

    if file:

        data = pd.read_csv(file, sep="|", engine="python")

        if len(data.columns) == 1:
            data = data.iloc[:, 0].str.split("|", expand=True)

        data.columns = [
            "TOKO","NO_NRB","TGL_NRB","NO_BA","TGL_BA",
            "PLUIDM","PLUIGR","NAMA_BARANG","KET_RETUR",
            "QTY","RPH"
        ]

        for _, row in data.iterrows():

            case_id = f"{row['TOKO']}_{row['NO_NRB']}_{row['TGL_NRB']}"

            c.execute("""
            INSERT INTO nbh VALUES (?,?,?,?,?,?,?,?)
            """, (
                str(uuid.uuid4()),
                row["TOKO"],
                row["NO_NRB"],
                row["TGL_NRB"],
                row["NAMA_BARANG"],
                row["QTY"],
                row["RPH"],
                case_id
            ))

        conn.commit()
        st.success("✅ Upload NBH berhasil")

    st.subheader("📌 DATA NBH")
    st.dataframe(df, use_container_width=True)


# =========================
# TIM UPLOAD IC (UPLOAD BUKTI + FOTO)
# =========================
elif role == "Tim Upload IC":

    st.subheader("📷 Upload Bukti Follow Up IC")

    if df.empty:
        st.warning("Belum ada data NBH")
    else:

        case = st.selectbox("Pilih Case ID", df["case_id"].unique())

        catatan = st.text_area("Catatan Follow Up")
        status = st.selectbox("Status", ["BELUM FOLLOW UP", "SUDAH FOLLOW UP", "SELESAI"])

        foto = st.file_uploader("Upload Bukti Foto (WA Screenshot)", type=["png", "jpg", "jpeg"])

        if st.button("Simpan Bukti"):

            foto_bytes = None
            if foto is not None:
                foto_bytes = foto.read()

            c.execute("""
            INSERT INTO bukti VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                str(uuid.uuid4()),
                case,
                df[df["case_id"] == case]["toko"].values[0],
                df[df["case_id"] == case]["no_nrb"].values[0],
                catatan,
                status,
                "TIM_UPLOAD",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                foto_bytes
            ))

            conn.commit()
            st.success("✅ Bukti + Foto berhasil disimpan")

    st.subheader("📌 History Follow Up")
    st.dataframe(df_bukti, use_container_width=True)


# =========================
# TOKO PORTAL (VIEW + FOTO)
# =========================
elif role == "Toko":

    st.subheader("🏪 Portal Toko NBH (Read Only)")

    if df.empty:
        st.warning("Belum ada data NBH")
    else:

        toko = st.selectbox("Pilih Toko", df["toko"].unique())

        toko_data = df[df["toko"] == toko]

        st.subheader("📊 NBH Anda")
        st.dataframe(toko_data, use_container_width=True)

        st.subheader("📷 Bukti Follow Up IC")

        case_list = toko_data["case_id"].unique()
        bukti_toko = df_bukti[df_bukti["case_id"].isin(case_list)]

        if bukti_toko.empty:
            st.info("Belum ada bukti follow up")
        else:

            for _, row in bukti_toko.iterrows():

                st.write(f"📌 Case ID: {row['case_id']}")
                st.write(f"Status: {row['status']}")
                st.write(f"Catatan: {row['catatan']}")
                st.write(f"Tanggal: {row['created_at']}")

                if row["foto"] is not None:
                    try:
                        img = Image.open(BytesIO(row["foto"]))
                        st.image(img, caption="Bukti Follow Up IC", use_container_width=True)
                    except:
                        st.warning("⚠️ Gambar tidak bisa ditampilkan")

                st.divider()

# =========================
# CLOSE DB
# =========================
conn.close()
