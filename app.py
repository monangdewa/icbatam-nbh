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
# TABLE NBH
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
# TABLE BUKTI (FINAL FIX)
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
# LOAD FUNCTIONS (REAL TIME SAFE)
# =========================
def load_nbh():
    df = pd.read_sql("SELECT * FROM nbh", conn)
    if not df.empty:
        df["case_id"] = df["case_id"].astype(str).str.strip()
    return df

def load_bukti():
    df = pd.read_sql("SELECT * FROM bukti", conn)
    if not df.empty:
        df["case_id"] = df["case_id"].astype(str).str.strip()
    return df

# =========================
# ROLE SYSTEM
# =========================
role = st.sidebar.selectbox(
    "Login Role",
    ["Admin IC", "Tim Upload IC", "Toko"]
)

st.sidebar.divider()

# =========================
# =========================
# ADMIN IC
# =========================
if role == "Admin IC":

    df = load_nbh()

    st.subheader("📊 Dashboard Admin IC")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Case", df["case_id"].nunique() if not df.empty else 0)
    col2.metric("Total Toko", df["toko"].nunique() if not df.empty else 0)
    col3.metric("Total NRB", df["no_nrb"].nunique() if not df.empty else 0)

    st.divider()

    st.subheader("📥 Upload NBH (PIPE | FORMAT)")

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

            case_id = f"{row['TOKO']}_{row['NO_NRB']}_{row['TGL_NRB']}".strip()

            c.execute("""
            INSERT INTO nbh VALUES (?,?,?,?,?,?,?,?)
            """, (
                str(uuid.uuid4()),
                row["TOKO"],
                row["NO_NRB"],
                row["TGL_NRB"],
                row["NAMA_BARANG"],
                float(row["QTY"]),
                float(row["RPH"]),
                case_id
            ))

        conn.commit()
        st.success("✅ NBH berhasil diupload")

    st.subheader("📌 DATA NBH")
    st.dataframe(df, use_container_width=True)


# =========================
# TIM UPLOAD IC (FIX FINAL AUTO STATUS)
# =========================
elif role == "Tim Upload IC":

    df = load_nbh()
    df_bukti = load_bukti()

    st.subheader("📷 Upload Bukti Follow Up (AUTO STATUS = SELESAI)")

    if df.empty:
        st.warning("Belum ada data NBH")
    else:

        case = st.selectbox("Pilih Case ID", df["case_id"].unique())

        catatan = st.text_area("Catatan Follow Up")

        foto = st.file_uploader("Upload Foto Bukti (WA Screenshot)", type=["png", "jpg", "jpeg"])

        if st.button("Simpan Bukti"):

            if foto is None:
                st.error("❌ Foto wajib diupload")
                st.stop()

            foto_bytes = foto.read()

            toko_val = df[df["case_id"] == case]["toko"].values[0]
            nrb_val = df[df["case_id"] == case]["no_nrb"].values[0]

            c.execute("""
            INSERT INTO bukti (
                id, case_id, toko, no_nrb, catatan, status,
                uploaded_by, created_at, foto
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                str(uuid.uuid4()),
                case.strip(),
                toko_val,
                nrb_val,
                catatan,
                "SELESAI",  # 🔥 AUTO STATUS FIX
                "TIM_UPLOAD",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                foto_bytes
            ))

            conn.commit()

            st.success("✅ Bukti berhasil diupload (Status: SELESAI)")
            st.rerun()

    st.subheader("📌 HISTORY FOLLOW UP (SELESAI)")

    df_bukti = df_bukti[df_bukti["status"] == "SELESAI"]

    st.dataframe(df_bukti, use_container_width=True)


# =========================
# TOKO PORTAL (VIEW + FOTO FIX)
# =========================
elif role == "Toko":

    df = load_nbh()
    df_bukti = load_bukti()

    st.subheader("🏪 Portal Toko NBH (Read Only)")

    if df.empty:
        st.warning("Belum ada data")
    else:

        toko = st.selectbox("Pilih Toko", df["toko"].unique())

        toko_data = df[df["toko"] == toko]

        st.subheader("📊 NBH Anda")
        st.dataframe(toko_data, use_container_width=True)

        st.subheader("📷 Bukti Follow Up IC")

        case_list = [str(x).strip() for x in toko_data["case_id"].unique()]

        bukti_toko = df_bukti[
            df_bukti["case_id"].astype(str).str.strip().isin(case_list)
        ]

        if bukti_toko.empty:
            st.info("Belum ada bukti follow up")
        else:

            for _, row in bukti_toko.iterrows():

                st.write(f"📌 Case ID: {row['case_id']}")
                st.write(f"Status: {row['status']}")
                st.write(f"Catatan: {row['catatan']}")
                st.write(f"Timestamp: {row['created_at']}")

                if row["foto"] is not None:
                    try:
                        img = Image.open(BytesIO(row["foto"]))
                        st.image(img, caption="Bukti Follow Up IC", use_container_width=True)
                    except:
                        st.warning("⚠️ Foto tidak bisa dibuka")

                st.divider()

# =========================
# CLOSE DB
# =========================
conn.close()
