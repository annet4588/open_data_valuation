import streamlit as st
import pandas as pd
from src.dataset_quality import DatasetQualityValuator
import plotly.express as px
from pathlib import Path
import hashlib

# Path to style.css file
css_path = Path(__file__).parent / "style.css"
# Chart colour scheme
PASTEL_COLORS = px.colors.qualitative.Pastel

# -----------------------------
# Streamlit setup
# -----------------------------
st.set_page_config(page_title="Open Data Valuation Tool", layout="centered")
# Load CSS from file
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
st.title("Open Data Valuation Tool")
st.markdown(
    "Use this Tool to assess the value of open datasets based on strategic dimentions."
)
# -----------------------------
# Session state initialisation
# -----------------------------
if "scores_confirmed" not in st.session_state:
    st.session_state["scores_confirmed"] = False
    
if "calculate_scores" not in st.session_state:
    st.session_state["calculate_scores"] = False

    

# Value Dimentions
value_dimensions = [
    "Economic",
    "Social",
    "Environmental",
    "Cultural",
    "Policy Alignment",
    "Data Quality",
]

# All Use Cases
use_cases = [
    "Planning & Development",
    "Policy Monitoring & Reporting",
    "Public Engagement & Awareness",
    "Regulatory Compliance Monitoring",
    "Water Quality Risk Assessment",
    "Environmental Impact Assessment",
    "Service Planning & Improvement",
    "Biodiversity & Habitat Protection",
    "Climate Resilience & Adaptation"
]

# Tooltips
tooltips = {
    "Economic": "1 - No Economic Benefit; 5 - Enables Cost Savings",
    "Social": "1 - Little or No Impact on Public Engagement; 5 - Widely used for Inclusion, Transparency, Public Engagement.",
    "Environmental": "1 - No environmental relevance or support; 5 - Essential for monitoring, conservation, or environmental planning.",
    "Cultural": "1 - Not relevant to cultural or heritage aspects; 5 - Actively supports cultural preservation or heritage value.",
    "Policy Alignment": "1 - Not linked to any relevant policy or directive; 5 - Strongly aligned with current policy goals or legislations.",
    "Data Quality": "1 - Outdated, incomplete, or poorly documented data; 5 - High-quality, Structured Data with Strong Metadata and accesibility.",
}

# -----------------------------
# Helpers
# -----------------------------
# Signature for uploaded dataset, if different content with same name/size
def file_signature(uploaded_file) -> str:
    data = uploaded_file.getvalue()
    h = hashlib.md5(data).hexdigest()
    return f"{uploaded_file.name}-{uploaded_file.size}-{h}"

# Called when dataset_uploader changes
def reset_dependent_state():
    st.session_state["scores_confirmed"] = False
    st.session_state["calculate_scores"] = False
    
    st.session_state["selected_use_case"] = None
    st.session_state["apply_weight"] = False
    
    # Clear old rating/weight keys
    for k in list(st.session_state.keys()):
        if k.startswith("rating_") or k.startswith("weight_"):
            del st.session_state[k]
    
    
# -----------------------------
# 1. SELECT DATASET
# -----------------------------
st.header("1. Select Dataset")
# File uploader
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file", 
    type=["csv", "xlsx", "xls"],
    key="dataset_uploader", # file uploader key
    on_change=reset_dependent_state # added the helper function on change
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
        df_preview = df.copy()
        df_preview.index = df.index+1
        st.dataframe(df_preview.head(), width="stretch")

        # Evaluate dataset quality
        st.subheader("Data Quality Overview:")
        dq = DatasetQualityValuator(df)
        quality = dq.score()
        st.json(quality)

        # -----------------------------
        # 2. SELECT USE CASE
        # -----------------------------
        st.header("2. Select Use Case")
 
        # User's selected use case using session_state key
        selected_use_case = st.selectbox(
            "Choose a Use Case", 
            use_cases, 
            index=None, 
            placeholder="Select Use Case...",
            key="selected_use_case" # widget key
        )
        
        # Show selected use case
        st.write(f"Selected Use Case: **{selected_use_case}**")
        
        if selected_use_case is None:
            st.warning("You have to Select a Use Case to proceed.")
        
        
        # # For Future Development - addition Use Cases
        # st.header("2a. Additional Use Case")
        # add_second_use_case = st.selectbox("Would you like to choose a second Use Case?")
        # if add_second_use_case:
        #     second_use_case = st.selectbox("Select a second Use Case", use_cases, key="second_use_case")

        # -----------------------------
        # 3. SCORE VALUE DIMENSIONS
        # -----------------------------
        if st.session_state["selected_use_case"]:
            st.header("3. Score Value Dimentions")

            for dim in value_dimensions:
                st.markdown(f"**{dim}**")
                st.caption(tooltips.get(dim, ""))
                
                st.session_state["scores"][dim]= st.slider(
                    "Score (1 = Low, 5 = High)", 
                    1, 
                    5, 
                    st.session_state["scores"].get(dim, 3),
                    key=f"score_{dim}")
                
            # Read scores from session_state
            scores = st.session_state["scores"]
            
            # Add a button to confirm scores
            if st.button("Confirm Scores"):
                st.session_state["scores_confirmed"] = True               
                
            if st.session_state["scores_confirmed"]:                  
                # -----------------------------
                # 4. OPTIONAL WEIGHTING 
                # -----------------------------  
                st.header("4. Optional: Apply Weights to Dimensions")
                apply_weights = st.checkbox(
                    "Apply custom weights?", 
                    key="apply_weights") # widget key
                
                if apply_weights:
                    for dim in value_dimensions:
                        st.session_state["weights"][dim] = st.slider(
                            f"{dim} Weight (0.0 - 1.0)", 
                            0.0, 
                            1.0, 
                            st.session_state["weights"].get(dim, 0.5),
                            step=0.1,
                            key=f"weight_{dim}")
                        
                    weights = st.session_state["weights"]
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
            
            # -----------------------------
            # 5. CALCULATE AND DISPLAY RESULTS
            # -----------------------------        
            if st.session_state["calculate_scores"] and st.session_state["scores_confirmed"]:
                # 5. CALCULATE AND DISPLAY RESULTS
                st.header("5. Valuation Score Summary")
               
                apply_weights = st.session_state.get("apply_weights", False)
                weights = st.session_state.get(
                    "weights", 
                    {dim: 1.0 for dim in value_dimensions})
                
                if apply_weights:
                    # Calculate weighed scores
                    weighted_scores = {dim: scores[dim] * weights[dim] for dim in value_dimensions}
                    total_score = sum(weighted_scores.values())
                    max_possible = sum(5* weights[dim]for dim in value_dimensions)
                    final_score_percent = round((total_score/max_possible) * 100, 2) if max_possible else 0.0
                    
                    # Find highest scoring diamentions
                    max_score = max(weighted_scores.values()) if weighted_scores else 0
                    top_dim = [dim for dim, val in weighted_scores.items() if val == max_score]
                    top_dim_str = ", ".join(top_dim)
                    
                    st.markdown(
                        f"""
                        **Weighted Valuation Score:** {final_score_percent}%\n  
                        **Top Score Dimension:** {top_dim_str} value\n
                        **Use Case:** {selected_use_case}
                        """
                    )
                    
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
                    final_score_percent = round((total_score / max_possible) * 100, 2) if max_possible else 0.0
                    
                    # Find highest scoring diamentions
                    max_score = max(scores.values()) if scores else 0
                    top_dim = [dim for dim, val in scores.items() if val == max_score]
                    top_dim_str = ", ".join(top_dim)
                    
                    st.markdown(
                        f"""
                        **Weighted Valuation Score**  
                        {final_score_percent}%  
                        Top Score Dimension: {top_dim_str} value\n
                        Use Case: {selected_use_case}
                        """
                    )
                    
                    # Show breakdown
                    st.dataframe(pd.DataFrame({
                        "Dimension": value_dimensions,
                        "Score": [scores[dim] for dim in value_dimensions]
                    }))
                # Show graphs
                if(st.button("Show graphs")):
                    st.subheader("Visualisation of Scores")
                    
                    if apply_weights:
                        weights = st.session_state.get("weights", {dim: 1.0 for dim in value_dimensions})
                        # Weighted chart
                        df_plot = pd.DataFrame({
                            "Dimension": value_dimensions,
                            "Score": [round(scores[dim] * weights[dim], 2) for dim in value_dimensions]
                        })
                        chart_title = "Weighted Value Dimension Scores"
                        y_axis_label = "Weighted Score"
                    else:
                        # Non-Weighted chart
                        df_plot = pd.DataFrame({
                            "Dimension": value_dimensions,
                            "Score": [round(scores[dim], 2) for dim in value_dimensions]
                        })
                        
                        chart_title = "Value Dimension Scores"
                        y_axis_label = "Score (1-5)"
                    
                    # Create a Bar chart
                    fig = px.bar(
                        df_plot,
                        x="Dimension",
                        y="Score",
                        title=chart_title,
                        color="Dimension", 
                        color_discrete_sequence=PASTEL_COLORS,
                        text="Score"
                    )
                    # Format text on bars (always 2 decimals, placed outside the bar)
                    fig.update_traces(
                        texttemplate='%{y: .2f}', 
                        textfont_size=16)
                    
                    fig.update_layout(yaxis_title=y_axis_label)
        
                    plotly_config ={
                        "displayModeBar": False,
                        "responsive": True,
                        "scrollZoom": False,
                        "doubleClick": False,
                    }
                    st.plotly_chart(
                        fig, 
                        config=plotly_config)
                    
                    # Star rating function
                    def star_rating(score, max_stars=5):
                        filled = int(round(score))
                        empty = max_stars - filled

                        return "⭐" * filled + "☆" * empty
                    
                    # Build rating table
                    rating = []
                    for dim in value_dimensions:
                        score = scores[dim]
                        stars = star_rating(score)
                        rating.append([dim, round(score, 2), stars])
                    rating.sort(key=lambda x: x[1], reverse=True)

                    rating_df = pd.DataFrame(
                        rating,
                        columns=["Dimension", "Score", "Stars"]
                    )
                    
                    # Display
                    st.markdown("## ⭐ Value Rating Summary")

                    for i, row in rating_df.iterrows():
                        st.markdown(
                            f"<b>{row['Dimension']}</b>: {row['Stars']}",
                            unsafe_allow_html=True
                        )
            
        
        
    except Exception as e:
        st.error(f"Failed to reaf file: {e}")
else:
    st.info("Upload a CSV/XLSX/XLS file to begin.")
