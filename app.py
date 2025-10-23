import streamlit as st
import pandas as pd
from src.dataset_quality import DatasetQualityValuator

# Streamlit setup
st.set_page_config(page_title="Open Data Valuation Tool", layout="wide")
st.title("Open Data Valuation Dashboard")
st.markdown("Use this Tool to assess the value of open datasets based on strategic dimentions.")

# Value Dimentions
value_dimensions= ["Economic", "Social", "Environmental", "Cultural", "Policy Alignment", "Data Quality"]

# 1. SELECT DATASET
st.header("1. Select Dataset")
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
        st.subheader("Data Quality Overview:")
        dq = DatasetQualityValuator(df)
        quality = dq.score()
        st.json(quality)
        
        # 2. SELECT USE CASE
        st.header("2. Select Use Case") 
        # All Use Cases
        use_cases = ["Planning & Development", "Policy Monitoring & Reporting","Public Engagement & Awareness", "Regulatory Compliance Monitoring", "Water Quality Risk Assessment"]
        # User's selected use case
        selected_use_case = st.selectbox(
            "Choose a Use Case", 
            use_cases, 
            index=None, 
            placeholder="Select Use Case...")
        # Show selected use case
        st.write("Selected Use Case: ", selected_use_case)
        
    except Exception as e:
        st.error(f"Failed to reaf file: {e}")
else:
    st.info("Upload a CSV/XLSX/XLS file to begin.")
