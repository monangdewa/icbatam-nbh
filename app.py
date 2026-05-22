import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import datetime

st.set_page_config(page_title="IC Batam NBH ERP", layout="wide")

st.title("🔥 IC Batam - NBH Anti Fraud ERP System")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("nbh.db", check_same_thread=False)
c = conn.cursor()

# TABLE NBH
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

# TABLE BUKTI FOLLOW UP
c.execute("""
CREATE TABLE IF NOT EXISTS bukti (
    id TEXT,
    case_id TEXT,
    toko TEXT,
    no_nrb TEXT,
    catatan TEXT,
    status TEXT,
    uploaded_by TEXT,
    created_at TEXT
)
""")

conn.commit()

# =========================
# ROLE LOGIN SIMPLE
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
# ADMIN DASHBOARD
# =========================
if role == "Admin IC":

    st.subheader("📊 Dashboard Admin IC")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Case", df["case_id"].nunique() if not df.empty else 0)
    col2.metric("Total Toko", df["toko"].nunique() if not df.empty else 0)
    col3.metric("Total NRB", df["no_nrb"].nunique() if not df.empty else 0)

    st.divider()

    st.subheader("📥 Upload NBH (CSV PIPE |)")

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
        st.success("✅ Data NBH berhasil diupload")

    st.subheader("📌 Data NBH")
    st.dataframe(df, use_container_width=True)


# =========================
# TIM UPLOAD IC
# =========================
elif role == "Tim Upload IC":

    st.subheader("📷 Upload Bukti Follow Up")

    if df.empty:
        st.warning("Belum ada data NBH")
    else:

        case = st.selectbox("Pilih Case ID", df["case_id"].unique())

        catatan = st.text_area("Catatan Follow Up")
        status = st.selectbox("Status", ["BELUM", "SUDAH FOLLOW UP", "SELESAI"])

        if st.button("Upload Bukti"):

            c.execute("""
            INSERT INTO bukti VALUES (?,?,?,?,?,?,?,?)
            """, (
                str(uuid.uuid4()),
                case,
                df[df["case_id"] == case]["toko"].values[0],
                df[df["case_id"] == case]["no_nrb"].values[0],
                catatan,
                status,
                "TIM_UPLOAD",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            st.success("✅ Bukti berhasil disimpan")

    st.subheader("📌 History Follow Up")
    st.dataframe(df_bukti, use_container_width=True)


# =========================
# TOKO PORTAL
# =========================
elif role == "Toko":

    st.subheader("🏪 Portal Toko NBH (Read Only)")

    if df.empty:
        st.warning("Belum ada data")
    else:

        toko = st.selectbox("Pilih Toko", df["toko"].unique())

        toko_data = df[df["toko"] == toko]

        st.subheader("📊 NBH Anda")
        st.dataframe(toko_data, use_container_width=True)

        st.subheader("📷 Bukti Follow Up")

        case_list = toko_data["case_id"].unique()
        bukti_toko = df_bukti[df_bukti["case_id"].isin(case_list)]

        st.dataframe(bukti_toko, use_container_width=True)

# =========================
# CLOSE DB
# =========================
conn.close()
