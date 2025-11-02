import streamlit as st
import pandas as pd
from src.dataset_quality import DatasetQualityValuator

# Streamlit setup
st.set_page_config(page_title="Open Data Valuation Tool", layout="wide")
st.title("Open Data Valuation Dashboard")
st.markdown(
    "Use this Tool to assess the value of open datasets based on strategic dimentions."
)

# Value Dimentions
value_dimensions = [
    "Economic",
    "Social",
    "Environmental",
    "Cultural",
    "Policy Alignment",
    "Data Quality",
]

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
        use_cases = [
            "Planning & Development",
            "Policy Monitoring & Reporting",
            "Public Engagement & Awareness",
            "Regulatory Compliance Monitoring",
            "Water Quality Risk Assessment",
        ]
        # User's selected use case
        selected_use_case = st.selectbox(
            "Choose a Use Case", use_cases, index=None, placeholder="Select Use Case..."
        )
        # Show selected use case
        st.write("Selected Use Case: ", selected_use_case)
        
        # # For Future Development - addition Use Cases
        # st.header("2a. Additional Use Case")
        # add_second_use_case = st.selectbox("Would you like to choose a second Use Case?")
        # if add_second_use_case:
        #     second_use_case = st.selectbox("Select a second Use Case", use_cases, key="second_use_case")

        # 3. SCORE VALUE DIMENTIONS
        if selected_use_case !=None:
            st.header("3. Score Value Dimentions")
            # Initialise scores
            scores = {}

            # Tooltips
            tooltips = {
                "Economic": "1 - No Economic Benefit; 5 - Enables Cost Savings",
                "Social": "1 - Little or No Impact on Public Engagement; 5 - Widely used for Inclusion, Transparency, Public Engagement.",
                "Environmental": "1 - No environmental relevance or support; 5 - Essential for monitoring, conservation, or environmental planning.",
                "Cultural": "1 - Not relevant to cultural or heritage aspects; 5 - Actively supports cultural preservation or heritage value.",
                "Policy Alignment": "1 - Not linked to any relevant policy or directive; 5 - Strongly aligned with current policy goals or legislations.",
                "Data Quality": "1 - Outdated, incomplete, or poorly documented data; 5 - High-quality, Structured Data with Strong Metadata and accesibility.",
            }

            for dim in value_dimensions:
                st.markdown(f"{dim} Score")
                st.caption(tooltips.get(dim, ""))
                scores[dim] = st.slider("Score (1 = Low, 5 = High)", 1, 5, 3, key=dim)
            
            # Add a button to confirm scores
            if st.button("Confirm Scores"):
                st.session_state["scores_confirmed"] = True               
                
            if st.session_state.get("scores_confirmed"):                  
                # 4. OPTIONAL WEIGHTING    
                st.header("4. Optional: Apply Weights to Dimensions")
                apply_weights = st.checkbox("Apply custom weights?")
                weights = {}
                
                if apply_weights:
                    for dim in value_dimensions:
                        weights[dim] = st.slider(f"{dim} Weight (0.0 - 1.0)", 0.0, 1.0, 0.5, key=f"weight_{dim}")
                else:
                    weights = {dim: 1.0 for dim in value_dimensions}
                
                # Add button Calculate Scores
                if st.button("Calculate Scores"):
                    st.session_state["calculate_scores"] = True
                    
            else:
                # If user click Calculate button without Confirming
                if st.button("Calculate Scores"):
                   st.warning("Please confirm your scores before proceeding")
                   st.session_state["calculate_scores"] = False
                        
            # Show Results    
            if st.session_state.get("calculate_scores") and st.session_state.get("scores_confirmed"):
                # 5. CALCULATE AND DISPLAY RESULTS
                st.header("5. Valuation Score Summary")
                
                if apply_weights:
                    # Calculate weighed scores
                    weighted_scores = {dim: scores[dim] * weights[dim] for dim in value_dimensions}
                    total_score = sum(weighted_scores.values())
                    max_possible = sum([5* weights[dim]for dim in value_dimensions])
                    final_score_percent = round((total_score/max_possible) * 100, 2)
                    
                    st.metric("Weighted Valuation Score", f"{final_score_percent}%")
                    
                    # Show breakdown
                    st.dataframe(pd.DataFrame({
                        "Dimension": value_dimensions,
                        "Score": [scores[dim] for dim in value_dimensions],
                        "Weight": [weights[dim] for dim in value_dimensions],
                        "Weighted Score": [weighted_scores[dim] for dim in value_dimensions]
                    }))
                
                else:
                    # Calculate Scores without applied weights
                    total_score = sum(scores.values())
                    max_possible = len(value_dimensions) * 5
                    final_score_percent = round((total_score / max_possible) * 100, 2)
                    
                    st.metric("Valuation Scores no added weights", f"{final_score_percent}%")
                    
                    # Show breakdown
                    st.dataframe(pd.DataFrame({
                        "Dimension": value_dimensions,
                        "Score": [scores[dim] for dim in value_dimensions]
                    }))
                
        else: 
            st.warning("You have to Select a Use Case to proceed.")
        
    except Exception as e:
        st.error(f"Failed to reaf file: {e}")
else:
    st.info("Upload a CSV/XLSX/XLS file to begin.")
