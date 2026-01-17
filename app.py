from src.storage import save_valuation
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from src.dataset_quality import DatasetQualityValuator
import plotly.express as px
from pathlib import Path
import hashlib
from streamlit_star_rating import st_star_rating
import uuid


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
# Instructions
with st.expander("ℹ️ **How to use this Tool** —  Click to see how it works  👆", expanded = False):
    st.markdown("""
**Step 1 — Upload a dataset**  
Upload a CSV/XLSX/XLS file. A preview and a data quality overview will be shown.

**Step 2 — Choose a use case**  
Select the use case that best matches how the dataset will be used.

**Step 3 — Rate each value dimension (0–5 stars)**  
Give a rating for each dimension (Economic, Social, Environmental, Cultural, Policy Alignment, Data Quality).  
Use **Reset** to clear a single dimension or **Update Scores** to reset all.

**Step 4 — Optional: Apply weights**  
Tick **Apply custom weights** if some dimensions matter more than others for your use case.  
Weights range from **0.0 (not important)** to **1.0 (very important)**.

**Step 5 — Calculate scores**  
Click **Calculate Scores** to see the final valuation score and the top dimension(s).  
Click **Show graphs** to view charts and a value rating summary.

**How “Top dimension(s)” works**  
- If weights are OFF: top dimensions are those with the highest star rating.  
- If weights are ON: top dimensions are those with the highest **(stars × weight)** score.
""")

if "ratings_nonce" not in st.session_state:
    st.session_state["ratings_nonce"] = 0
       
# -----------------------------
# Session state initialisation
# -----------------------------
if "scores_confirmed" not in st.session_state:
    st.session_state["scores_confirmed"] = False
    
if "calculate_scores" not in st.session_state:
    st.session_state["calculate_scores"] = False

# Prevent duplicate db inserts when Streamlit reruns
if "saved_submit_id" not in st.session_state:
    st.session_state["saved_submit_id"] = None

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

# Tooltips Star rating
tooltips = {
    "Economic": "☆ None (0) = No economic impact · ⭐⭐⭐⭐⭐ (5) = Enables cost savings",
    "Social": "☆ None (0) = No public engagement impact · ⭐⭐⭐⭐⭐ (5) = High public value",
    "Environmental": "☆ None (0) = No environmental relevance · ⭐⭐⭐⭐⭐ (5) = Essential for monitoring",
    "Cultural": "☆ None (0) = No cultural relevance · ⭐⭐⭐⭐⭐ (5) = Supports heritage value",
    "Policy Alignment": "☆ None (0) = No policy alignment · ⭐⭐⭐⭐⭐ (5) = Strong policy alignment",
    "Data Quality": "☆ None (0) = Poor or unusable data · ⭐⭐⭐⭐⭐ (5) = High-quality Metadata and accesibility",
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
    st.session_state["apply_weights"] = False
    
    # Force remount star widgets (clear UI)
    st.session_state["ratings_nonce"] +=1
    
    # Clear old rating/weight keys
    for k in list(st.session_state.keys()):
        if k.startswith("rating_") or k.startswith("weight_"):
            del st.session_state[k]
# Rating key
def rating_key(dataset_sig: str, use_case: str, dim: str) -> str:
    n_all = st.session_state["ratings_nonce"]
    n_dim = st.session_state["dim_nonce"].get(dim, 0)
    return(
        f"rating_{n_all}_{n_dim}_{dataset_sig}_{use_case}_{dim}"
        .replace(" ", "_")
        .lower()
    )
# Initialise per dimension nonce to allow reset each dimension individually
if "dim_nonce" not in st.session_state:
    st.session_state["dim_nonce"] = {d: 0 for d in value_dimensions}
    
# Reset one dimension
def reset_one_dimension(dim: str):
    st.session_state["scores_confirmed"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["dim_nonce"][dim] = st.session_state["dim_nonce"].get(dim, 0) + 1
    
# Reset Rating
def reset_ratings_only():
    st.session_state["scores_confirmed"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["ratings_nonce"] +=1 # remount star components to defaultValue 0
    
def star_string(score: float, max_stars: int = 5) -> str:
    s = int(round(score))
    s = max(0, min(max_stars, s))
    return "⭐" * s + "☆" * (max_stars - s)
    
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

if not uploaded_file:
    st.info("Upload a CSV/XLSX/XLS file to begin.")
    st.stop()

# Autoreset when dataset changes and store it
sig = file_signature(uploaded_file)
st.session_state["dataset_sig"] = sig

# Read file
name = uploaded_file.name.lower()
try:

    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    elif name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file type")
        st.stop()
except Exception as e:
    st.error(f"Failed to reaf file: {e}")
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
    st.stop()


# # For Future Development - addition Use Cases
# st.header("2a. Additional Use Case")
# add_second_use_case = st.selectbox("Would you like to choose a second Use Case?")
# if add_second_use_case:
#     second_use_case = st.selectbox("Select a second Use Case", use_cases, key="second_use_case")

# -----------------------------
# 3. SCORE VALUE DIMENSIONS
# -----------------------------
st.header("3. Score Value Dimensions")

scores = {}

#Add a button to update scores
st.info("Select a star rating (0-5) for each value dimension below.")
st.caption("Click **Update Scores** to reset all star ratings to zero")
st.button("Update Scores", on_click=reset_ratings_only)

dataset_sig = st.session_state["dataset_sig"]

for dim in value_dimensions:
    st.markdown(f"**{dim}**")
    st.caption(tooltips.get(dim, ""))

    col_star, col_btn = st.columns([9, 1], vertical_alignment="center")

    with col_star:
        scores[dim] = st_star_rating(
            label="",
            maxValue=5,
            defaultValue=0,
            key=rating_key(dataset_sig, selected_use_case, dim),
        )

    with col_btn:
        st.button(
            "Reset",
            key=f"reset_{dataset_sig}_{selected_use_case}_{dim}".replace(" ", "_").lower(),
            on_click=reset_one_dimension,
            args=(dim,),
        )


# Add a button to confirm scores
st.button("Confirm Scores", on_click=lambda: st.session_state.__setitem__("scores_confirmed", True))             
    
                  
# -----------------------------
# 4. OPTIONAL WEIGHTING 
# -----------------------------  
if st.session_state["scores_confirmed"]:
    st.header("4. Optional: Apply Weights to Dimensions")
    
    apply_weights = st.checkbox(
        "Apply custom weights?", 
        key="apply_weights") # widget key
    
    if apply_weights:
        weights = {}
        for dim in value_dimensions:
            weights[dim] = st.slider(
                f"{dim} Weight (0.0 - 1.0)", 
                0.0, 
                1.0, 
                0.5, # default value
                step=0.1,
                key=f"weight_{dataset_sig}_{dim}".replace(" ", "_").lower()
            )
    else:
        weights = {dim: 1.0 for dim in value_dimensions}
    
    # Add button Calculate Scores
    if st.button("Calculate Scores"):
        st.session_state["calculate_scores"] = True
        st.session_state["submit_id"] = str(uuid.uuid4())
        
else:
    # If user click Calculate button without Confirming
    st.info("Click **Confirm Scores** to proceed to weighting and results.")
    st.stop()

# -----------------------------
# 5. CALCULATE AND DISPLAY RESULTS
# -----------------------------        
if st.session_state.get("calculate_scores"):
    st.header("5. Valuation Score Summary")
    
    apply_weights = st.session_state.get("apply_weights", False)
    
    # -----------------------------
    # CASE A: No WEIGHTS, STAR only results
    # -----------------------------    
    if not apply_weights:
        total_stars= sum(scores.values())
        max_possible=len(value_dimensions)*5
        final_score_percent=round((total_stars/max_possible)*100, 2)
        
        max_score=max(scores.values())
        top_dim=[dim for dim, val in scores.items() if val ==max_score]
        top_dim_str=", ".join(top_dim)
        
        # Payload
        payload = {
            "submit_id": st.session_state["submit_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_sig": st.session_state["dataset_sig"],
            "use_case": st.session_state["selected_use_case"],
            "apply_weights": False,
            "stars": {d: int(scores[d] or 0) for d in value_dimensions},
            "weights": {d: 1.0 for d in value_dimensions},
            "final_score_percent": float(final_score_percent)
        }
        # Track last saved submittion to prevent duplicate writes
        if payload["submit_id"] and payload["submit_id"] != st.session_state["saved_submit_id"]:
            try:
                save_valuation(payload)
                st.session_state["saved_submit_id"] = payload["submit_id"]
                st.success("Results saved successfully!")
            except Exception as e:
                st.error(f"Couldn't save results to the database: {e}")
        st.markdown(
            f"""
            **Valuation Score (Star-Based):** {final_score_percent}%  
            **Top Score Dimension(s):** {top_dim_str}  
            **Use Case:** {selected_use_case}
            """
        )
        
        # Star only breakdown
        star_df=pd.DataFrame({
            "Dimension": value_dimensions,
            "Stars (0-5)": [int(scores[d] or 0) for d in value_dimensions]
        })
        
        st.dataframe(star_df, width="stretch")
        
    # -----------------------------
    # CASE B: WEIGHTS applied
    # -----------------------------  
    else:
        weights = {
           dim: st.session_state.get(
               f"weight_{dataset_sig}_{dim}".replace(" ", "_").lower(), 0.5
           )
           for dim in value_dimensions
        }
       
        # Calculated scores and weights
        weighted_scores={
            dim: (scores[dim] or 0) * weights[dim]
            for dim in value_dimensions
        }
        
        total_score = sum(weighted_scores.values())
        max_possible = sum(5 * weights[dim] for dim in value_dimensions)
        final_score_percent = round((total_score / max_possible) * 100, 2)

        max_score = max(weighted_scores.values())
        top_dim = [dim for dim, val in weighted_scores.items() if val == max_score]
        top_dim_str = ", ".join(top_dim)
        
        # Payload with weights
        payload = {
            "submit_id": st.session_state["submit_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_sig": st.session_state["dataset_sig"],
            "use_case": st.session_state["selected_use_case"],
            "apply_weights": True,
            "stars": {d: int(scores[d] or 0) for d in value_dimensions},
            "weights": weights,
            "final_score_percent": float(final_score_percent),
        }
        # Track last saved submittion to prevent duplicate writes
        if payload["submit_id"] and payload["submit_id"] != st.session_state["saved_submit_id"]:
            try:               
                save_valuation(payload)
                st.session_state["saved_submit_id"] = payload["submit_id"]
                st.success("Results saved successfully!")
            except Exception as e:
                st.error(f"Couldn't save results to the database: {e}")
        
        
        st.markdown(
            f"""
            **Weighted Valuation Score:** {final_score_percent}%  
            **Top Score Dimension(s):** {top_dim_str}  
            **Use Case:** {selected_use_case}
            """
        )
        
        weighted_df = pd.DataFrame({
            "Dimension": value_dimensions,
            "Stars (0-5)": [int(scores[d] or 0) for d in value_dimensions],
            "Weights": [weights[d] for d in value_dimensions],
            "Weighted Score": [round(weighted_scores[d],2) for d in value_dimensions],
        })
        st.dataframe(weighted_df, width="stretch")
   
    # Show graphs
    if(st.button("Show graphs")):
        st.subheader("Visualisation of Scores")
        
        if apply_weights:
            # Weighted chart
            df_plot = pd.DataFrame({
                "Dimension": value_dimensions,
                "Score": [round(weighted_scores[dim], 2) for dim in value_dimensions]
            })
            chart_title = "Weighted Value Dimension Scores"
            y_axis_label = "Weighted Score"
        else:
            # Non-Weighted chart
            df_plot = pd.DataFrame({
                "Dimension": value_dimensions,
                "Score": [round(float(scores[dim] or 0), 2) for dim in value_dimensions]
            })
            
            chart_title = "Value Dimension Scores"
            y_axis_label = "Score (0-5 Stars)"
        
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
            config=plotly_config
            )
        
        # -----------------------------
        # Build rating table
        # -----------------------------   
        rating_rows = []
        
        for dim in value_dimensions:
            stars = int(scores[dim] or 0)
            
            # Base row
            row = {
                "Dimension": dim,
                "Stars (0-5)": stars,
                "Stars": star_string(stars)
            }
            
            # Apply weighted score if chosen
            if apply_weights:
                w = float(weights.get(dim, 0.5)) # fallback
                row["Weight"] = w
                row["Weighted Score"] = round(stars * w, 2)
                
            rating_rows.append(row)
           
        rating_df = pd.DataFrame(rating_rows)
        
        # Check if empty
        if rating_df.empty:
            st.warning("No rating data available.")
        else:
            # ----------------------------- 
            # Sort table for display            
            # ----------------------------- 
            sort_col = "Weighted Score" if apply_weights else "Stars (0-5)"
            rating_df = rating_df.sort_values(by=sort_col, ascending=False)
            
            # ----------------------------- 
            # Display summary
            # ----------------------------- 
            st.markdown("## ⭐ Value Rating Summary")
            for _, row in rating_df.iterrows():
                if apply_weights:
                    st.markdown(
                        f"**{row['Dimension']}**: {row['Stars']} "                   
                        )
                else:
                    st.markdown(f"**{row['Dimension']}**:{row['Stars']}")
                    
            # -----------------------------         
            # Tags - top dimention(s)
            # no weights - top by Stars
            # weights - top by weited score (stars * weight)
            # ----------------------------- 
            score_col = "Weighted Score" if apply_weights else "Stars (0-5)"            
            top_score = rating_df[score_col].max()
            top_dimensions = []
            # Do not display tags if the score is 0
            if top_score > 0:
               top_dimensions = rating_df[rating_df[score_col] == top_score]["Dimension"].tolist()
            

            tags_html = "".join(
                f'<div class="oval-tag"> {dim}</div>' 
                for dim in top_dimensions
                )
            st.markdown(
            f'## 🏷️ Tags <div class="tag-container">{tags_html}</div>',
            unsafe_allow_html=True
            )


            
        
             