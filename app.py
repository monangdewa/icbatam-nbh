import streamlit as st
import pandas as pd
import uuid

st.set_page_config(page_title="IC Batam NBH Control System", layout="wide")

st.title("📊 IC Batam - NBH Control System")

# =========================
# UPLOAD CSV
# =========================
st.sidebar.header("📥 Upload CSV NBH")

file = st.sidebar.file_uploader("Upload file CSV", type=["csv"])

if file is not None:

    df = pd.read_csv(file, sep=None, engine="python")

    st.success("✅ File berhasil diupload")

    # =========================
    # CLEAN COLUMN
    # =========================
    df.columns = df.columns.str.strip()

    # =========================
    # FIX DATE FORMAT
    # =========================
    df["TGL_NRB"] = pd.to_datetime(
        df["TGL_NRB"],
        dayfirst=True,
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # =========================
    # CREATE SYSTEM_ID
    # =========================
    df["SYSTEM_ID"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # =========================
    # CREATE CASE_ID (KEY LOGIC)
    # =========================
    df["CASE_ID"] = (
        df["TOKO"].astype(str) + "_" +
        df["NO_NRB"].astype(str) + "_" +
        df["TGL_NRB"].astype(str)
    )

    # =========================
    # SHOW DATA CLEAN
    # =========================
    st.subheader("📌 Data NBH (Clean & Ready System)")

    st.dataframe(df, use_container_width=True)

    # =========================
    # KPI DASHBOARD
    # =========================
    st.subheader("📊 Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Case NBH", len(df))
    col2.metric("Total Toko", df["TOKO"].nunique())
    col3.metric("Total NRB", df["NO_NRB"].nunique())

    st.divider()

    # =========================
    # SEARCH SYSTEM
    # =========================
    st.subheader("🔍 Search Data NBH")

    toko = st.text_input("Cari TOKO")
    nrb = st.text_input("Cari NO_NRB")
    case = st.text_input("Cari CASE_ID")

    filtered = df.copy()

    if toko:
        filtered = filtered[filtered["TOKO"].astype(str).str.contains(toko, case=False)]

    if nrb:
        filtered = filtered[filtered["NO_NRB"].astype(str).str.contains(nrb, case=False)]

    if case:
        filtered = filtered[filtered["CASE_ID"].astype(str).str.contains(case, case=False)]

    st.dataframe(filtered, use_container_width=True)

else:
    st.info("📌 Silakan upload CSV NBH untuk mulai sistem")
