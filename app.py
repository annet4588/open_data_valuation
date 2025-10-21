import streamlit as st
import pandas as pd
from src.dataset_quality import DatasetQualityValuator

# Streamlit setup
st.set_page_config(page_title="Open Data Valuation", layout="wide")
st.title("Open Data Valuation Dashboard")

# File uploader
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file", type=["csv", "xlsx", "xls"]
)

# File handler
if uploaded_file:
    name = uploaded_file.name.lower()

    try:
        # Read file
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        elif name.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type")
            st.stop()

        # Show Preview
        st.subheader("Data Preview")
        st.dataframe(df.head(), width="stretch")
        
        # Evaluate dataset quality 
        dq = DatasetQualityValuator(df)
        quality = dq.score()
        st.json(quality)
        
    except Exception as e:
        st.error(f"Failed to reaf file: {e}")
else:
    st.info("Upload a CSV/XLSX/XLS file to begin.")
