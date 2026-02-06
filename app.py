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

## Debug checks (confirms Supabase secrets are loaded at runtime)
# st.write("Supabase URL loaded:", bool(st.secrets.get("SUPABASE_URL")))
# st.write("Supabase key loaded:", bool(st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")))


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
    "Use this tool to assess the economic, social, and environmental value of open datasets."
)
# Instructions
st.info(
    """
    Takes less than **5 minutes** to complete
    """
)
# -----------------------------
# Session state show_guide initialisation
# -----------------------------
# This session keeps the guide open while user interacting with the app
if "show_guide" not in st.session_state:
    st.session_state["show_guide"] = False
    
if st.button("Read the full guide"):
    st.session_state["show_guide"] = True

# Sidebar appears on click and displays the guide
if st.session_state["show_guide"]:
    with st.sidebar:
        st.markdown("# Full User Guide")

        if st.button("Close guide"):
            st.session_state["show_guide"] = False
            st.rerun()

        st.markdown(
            """
### What this tool does
This tool helps you understand the value of an open dataset for decision-making.  

---

# How star ratings and weights work together

### Star ratings (required)
- Stars show **how strong** the dataset is in each area (0-5).
- They reflect the **quality** or **usefulness** of the data and never change.

### Weights (optional)
- Weights let you highlight what **matters most** for your use case.
- They do not change star ratings — they only **affect ranking** and **value tags**.

---

# Important things to know about weights
- Weights only apply if you **change at least one** slider
- If all weights **stay at 1**, results remain **star-based**
- You **cannot apply** weights to dimensions rated **0 stars**

This keeps results clear and avoids accidental prioritisation.

---

# What happens when weights are applied?
When you change one or more weights:

- Scores are calculated using **stars × weight**
- Higher weighted scores **appear higher** in the results
- A **high-star** dimension can **move down** if its weight is **low**

Value tags are created based on these weighted scores.

---

# When should I use weights?
Use weights if you want the results to reflect:

- Policy or organisational priorities
- A specific type of value
- Where the dataset matters most for decision-making

Leave weights unchanged for a neutral, balanced view.

---

# Value tags
- Value tags appear **only when you apply weights**
- They **highlight** the dataset's **main priority value**, based on what you chose to emphasise
- If you **don't apply** weights, **no value** tags are shown

Value tags are designed to help users quickly see **where a dataset delivers the most value for decision-making**.

---
# Evidence base    
This tool operationalises NatureScot's national research framework by adapting it for **open data valuation** and aligning it with **FAIR principles**.    
[NatureScot Research Report 1382 - Understanding the need and value of land cover and habitat data](https://www.nature.scot/doc/naturescot-research-report-1382-understanding-need-and-value-land-cover-and-habitat-data)  

"""
        )    
        
# -----------------------------
# Instructions
# -----------------------------
st.markdown(
    """    
    <h2 style='text-align: center; '>Instructions:</h2>
    """,
    unsafe_allow_html=True
)

with st.expander(
    "ℹ️ **How to use this Tool** —  Click to see how it works  👆", expanded=False
):
    st.markdown(
        """
**Step 1 — Upload a dataset**  
Upload a CSV/XLSX/XLS file. A preview and a data quality overview will be shown.

**Step 2 — Choose a use case**  
Select the **option** that best matches how the dataset will be used.

**Step 3 — Rate each value dimension (0-5 stars)**  
Give a rating for each dimension (Economic, Social, Environmental, Cultural, Policy Alignment, Data Quality).  
Use **Reset** to clear a single dimension or **Update Scores** to reset all.

**Step 4 — Optional: Apply weights**  
Tick **Apply custom weights** if some dimensions matter more than others for your use case.  
Weights range from **0.0 (less important)** to **1.0 (normal importance)**.  
If you **don't change** any weight, results stay **star-based**.

**Step 5 — View Results**  
Click **Calculate Scores** to see the overall value score and breakdown.  
Click **Show graphs** to explore the results visually.

**Value Tags**  
Value tags appear **only when weights are applied**.  
They show which dimension matters most to your use case.

**Remember:**  
Stars show how **good** the data is.  
Weights show **what matters most**. 
"""
    )

if "ratings_nonce" not in st.session_state:
    st.session_state["ratings_nonce"] = 0

# -----------------------------
# Session state initialisation
# -----------------------------
# Tracks if the user confirmed the star ratings
if "scores_confirmed" not in st.session_state:
    st.session_state["scores_confirmed"] = False
    
# Tracks if the user has interacted with at least one star rating
if "ratings_touched" not in st.session_state:
    st.session_state["ratings_touched"] = False

# Indicates if the user clicked "Calculate Scores"
if "calculate_scores" not in st.session_state:
    st.session_state["calculate_scores"] = False
    
# Track if the user changed at least one weight
if "weights_touched" not in st.session_state:
    st.session_state["weights_touched"] = False

# Unique identifier for the current valuation run   
if "submit_id" not in st.session_state:
    st.session_state["submit_id"] = None

# Prevent duplicate db inserts when Streamlit reruns
if "saved_submit_id" not in st.session_state:
    st.session_state["saved_submit_id"] = None
    
# Holds the most recent calculated valuation payload
# Allows results to be re calculated, and only saved the user clicks "Save Results"    
if "latest_payload" not in st.session_state:
    st.session_state["latest_payload"] = None

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
    "Statutory Requirements: Regulatory Compliance Monitoring",
    "Impact Assessment",
    "Service Planning & Improvement",
    "Management and monitoring",
]

# Tooltips Star rating
tooltips = {
    "Economic": (
        "☆ None (0) = No economic benefit from use  \n"  
        "⭐⭐⭐⭐⭐ (5) = Strong cost savings, efficiency gains, or avoided cost"
        ),
    "Social": (
        "☆ None (0) = No social benefit from use  \n" 
        "⭐⭐⭐⭐⭐ (5) = Improves wellbeing, access, or public outcomes through use of the data"
        ),
    "Environmental": (
        "☆ None (0) = No practical environmental application  \n"
        "⭐⭐⭐⭐⭐ (5) = Enables environmental performance improvement or risk mitigation"
        ) ,
    "Cultural": (
        "☆ None (0) = No cultural or heritage benefit from use  \n"
        "⭐⭐⭐⭐⭐ (5) = Supports cultural heritage, identity, or place-based outcomes"
        ) ,
    "Policy Alignment": (
        "☆ None (0) = Not used in policy or statutory contexts  \n"
        "⭐⭐⭐⭐⭐ (5) = Critical for policy development, delivery, or regulatory decision-making"
        )  ,
    "Data Quality": (
        "☆ None (0) = Data quality prevents effective use  \n"
        "⭐⭐⭐⭐⭐ (5) = FAIR-aligned, findable, accessible, interoperable and reusable data"
        ) ,
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
    st.session_state["ratings_touched"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["weights_touched"] = False

    st.session_state["selected_use_case"] = None
    st.session_state["apply_weights"] = False
    st.session_state["submit_id"] = None
    st.session_state["saved_submit_id"] = None
    st.session_state["latest_payload"] = None

    # Force remount star widgets (clear UI)
    st.session_state["ratings_nonce"] += 1

    # Clear old rating/weight keys
    for k in list(st.session_state.keys()):
        if k.startswith("rating_") or k.startswith("weight_"):
            del st.session_state[k]

# Rating key
def rating_key(dataset_sig: str, use_case: str, dim: str) -> str:
    n_all = st.session_state["ratings_nonce"]
    n_dim = st.session_state["dim_nonce"].get(dim, 0)
    return f"rating_{n_all}_{n_dim}_{dataset_sig}_{use_case}_{dim}".replace(
        " ", "_"
    ).lower()

# Initialise per dimension nonce to allow reset each dimension individually
if "dim_nonce" not in st.session_state:
    st.session_state["dim_nonce"] = {d: 0 for d in value_dimensions}

# Reset one dimension
def reset_one_dimension(dim: str):
    st.session_state["scores_confirmed"] = False
    st.session_state["ratings_touched"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["weights_touched"] = False
    st.session_state["saved_submit_id"] = None
    st.session_state["dim_nonce"][dim] = st.session_state["dim_nonce"].get(dim, 0) + 1

# Reset Rating
def reset_ratings_only():
    st.session_state["scores_confirmed"] = False
    st.session_state["ratings_touched"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["weights_touched"] = False
    st.session_state["saved_submit_id"] = None
    # Force remount star widgets (clear UI)
    st.session_state["ratings_nonce"] += 1

    # Clear old rating/weight keys
    for k in list(st.session_state.keys()):
        if k.startswith("rating_") or k.startswith("weight_"):
            del st.session_state[k]
            
# Reset Use Case
def reset_on_use_case_change():
    st.session_state["scores_confirmed"] = False
    st.session_state["ratings_touched"] = False
    st.session_state["calculate_scores"] = False
    st.session_state["weights_touched"] = False
    st.session_state["saved_submit_id"] = None
    st.session_state["latest_payload"] = None
    st.session_state["submit_id"] = None
    st.session_state["ratings_nonce"] +=1 # remount star widget - so previous rating don't appear
    
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
    key="dataset_uploader",  # file uploader key
    on_change=reset_dependent_state,  # added the helper function on change
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
df_preview.index = df.index + 1
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
st.info("Select the **Use Case** that best reflects how this dataset is primarily used.")

# User's selected use case using session_state key
selected_use_case = st.selectbox(
    "",
    use_cases,
    index=None,
    placeholder="Select Use Case...",
    key="selected_use_case",  
    on_change=reset_on_use_case_change,
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

# Add a button to update scores
st.info(
        """
        Select a **star rating (0-5)** for each value dimension below.

        Use **Reset** to clear a single dimension.  
        Use **Update Scores** to reset all star ratings to zero.
        """
)

# st.caption("Click **Update Scores** to reset all star ratings to zero")
st.button("Update Scores", on_click=reset_ratings_only)

dataset_sig = st.session_state["dataset_sig"]

for dim in value_dimensions:
    st.markdown(f"**{dim}**")
    
    # Updated tooltip with expander sections explaining how to assess each dimension
    st.caption(tooltips.get(dim, ""))
    with st.expander("How to assess this dimension"):
        if dim == "Economic":
            st.write("""
                **Consider:**
                • Cost savings
                • Efficiency gains
                • Avoided data collection costs

                **Example:** Does this data reduce staff time or external spend?  
                **Learn more:**
                [NatureScot Report/Components of the framework](https://www.nature.scot/doc/naturescot-research-report-1382-understanding-need-and-value-land-cover-and-habitat-data#components-of-the-framework)
            """
            )
        elif dim == "Social":
            st.write("""
                **Consider:**
                • Public wellbeing
                • Access to services
                • Community outcomes

                **Example:** Does this help people access support?
            """)

        elif dim == "Environmental":
            st.write("""
                **Consider:**
                • Risk monitoring
                • Habitat protection
                • Climate impacts

                **Example:** Does this support environmental management?
            """)

        elif dim == "Cultural":
            st.write("""
                **Consider:**
                • Heritage protection
                • Place identity
                • Cultural records

                **Example:** Does this preserve local history?
            """)

        elif dim == "Policy Alignment":
            st.write("""
                **Consider:**
                • Legal reporting
                • Statutory duties
                • Strategy support

                **Example:** Is this required for compliance?
            """)

        elif dim == "Data Quality":
            st.write("""
                **Consider:**
                • Accuracy and completeness
                • Clear Metadata 
                • FAIR principles
                • Licensing and ownership
                • Easy to find on official data platforms  
                
                **Example:** Can someone outside your team easily find, understand, and reuse this dataset?     

                **Guidance:** 
                [The Government Data Quality Framework (GOV.UK)](https://www.gov.uk/government/publications/the-government-data-quality-framework/the-government-data-quality-framework/)  
                **Learn more:**
                [FAIR Principals (GO-FAIR)](https://www.go-fair.org/fair-principles/)
            """
            )
            
    col_star, col_btn = st.columns([9, 1], vertical_alignment="center")

    with col_star:
        k = rating_key(dataset_sig, selected_use_case,dim) # unique key for this rating
        prev_key = f"prev_{k}" # stores the previous value of this rating
        
        # Display the widget
        val = st_star_rating(
            label="",
            maxValue=5,
            defaultValue=0,
            key=k,
        )
        scores[dim] = val # saves the selected rating for this dimension
        
        # Mark as touched if user changed this rating
        prev = st.session_state.get(prev_key, val)
        
        # Check if the rating chnaged since the last run
        if val !=prev:
            st.session_state["ratings_touched"] = True
        
        # Save the current rating value for the next time
        st.session_state[prev_key] = val

    with col_btn:
        st.button(
            "Reset",
            key=f"reset_{dataset_sig}_{selected_use_case}_{dim}".replace(
                " ", "_"
            ).lower(),
            on_click=reset_one_dimension,
            args=(dim,),
        )


# Add a button to confirm scores
if not st.session_state["ratings_touched"]:
    st.info("Select at least one rating (0-5) before confirming.")
    
st.button(
    "Confirm Scores",
    disabled=not st.session_state["ratings_touched"], # button disabled till at least one star rating clicked
    on_click=lambda: st.session_state.__setitem__("scores_confirmed", True),
)
if not st.session_state["scores_confirmed"]:
    st.warning("Please rate the dimensions and click **Confirm Scores** to continue.")
    st.stop()

# -----------------------------
# 4. OPTIONAL WEIGHTING
# -----------------------------
if st.session_state["scores_confirmed"]:
    st.header("4. Optional: Apply Weights to Dimensions")
    
    st.info(
        """
        **Optional step** — leave unchecked to continue with equal weighting across all dimensions.
       
        When you're finished scoring, click **Calculate Scores** to proceed.
        """
    )   
    apply_weights = st.checkbox(
        "Apply custom weights?", key="apply_weights" 
    )  # widget key
    st.caption(
       "Weights are only applied if you change at least one slider."
    )
    if apply_weights:
        weights = {}
        for dim in value_dimensions:
            stars = int(scores.get(dim, 0) or 0) # get star rating 
            
            w_key = f"weight_{dataset_sig}_{selected_use_case}_{dim}".replace(" ", "_").lower()
            prev_key = f"prev_{w_key}"
            
            w = st.slider(
                f"{dim} Weight (0.0 - 1.0)",
                0.0,
                1.0,
                1.0,  # Important: default = netral 
                step=0.1,
                key=w_key,
                disabled=(stars == 0), # disables 0 star rating 
            )
            weights[dim] = w
            
            # Deteck user interaction
            prev = st.session_state.get(prev_key, w)
            if w !=prev:
                st.session_state["weights_touched"] = True
            st.session_state[prev_key] = w
    else:
        weights = {dim: 1.0 for dim in value_dimensions}
        st.session_state["weights_touched"] = False

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
    
    # Build weights default 1.0
    weights={
        dim: float(
            st.session_state.get(
                f"weight_{dataset_sig}_{selected_use_case}_{dim}".replace(" ", "_").lower(), 
                1.0,
            )
        )
        for dim in value_dimensions
    }
    
    # Only treat weights as "applied" if the user actually changed something
    weights_meaningful = any(weights[d] !=1.0 for d in value_dimensions)
    apply_effective_weights = apply_weights and weights_meaningful

    # -----------------------------
    # CASE A: No WEIGHTS, STAR only results
    # -----------------------------
    if not apply_effective_weights:
        total_stars = sum(scores.values())
        max_possible = len(value_dimensions) * 5
        final_score_percent = round((total_stars / max_possible) * 100, 2)

        max_score = max(scores.values())
        top_dim = [dim for dim, val in scores.items() if val == max_score]
        top_dim_str = ", ".join(top_dim)

        # Payload
        payload = {
            "submit_id": st.session_state["submit_id"],
            "dataset_sig": st.session_state["dataset_sig"],
            "use_case": st.session_state["selected_use_case"],
            "apply_weights": False,
            "stars": {d: int(scores[d] or 0) for d in value_dimensions},
            "weights": {d: 1.0 for d in value_dimensions},
            "final_score_percent": float(final_score_percent),
            "tags":[],
        }
        
        # Store payload so it can be saved only when the user clicks "save results"
        st.session_state["latest_payload"] = payload

        st.markdown(
            f"""
            **Valuation Score (Star-Based):** {final_score_percent}%  
            **Top Score Dimension(s):** {top_dim_str}  
            **Use Case:** {selected_use_case}
            """
        )

        # Star only breakdown
        star_df = pd.DataFrame(
            {
                "Dimension": value_dimensions,
                "Stars (0-5)": [int(scores[d] or 0) for d in value_dimensions],
            }
        )

        st.dataframe(star_df, width="stretch")

    # -----------------------------
    # CASE B: WEIGHTS applied
    # -----------------------------
    else:
        # apply_weights = True
        # weights_meaningful = True
        # weights dict with default 1.0 exist

        # Calculated weighted score for each dimension (stars * weight)
        weighted_scores = {
            dim: (scores[dim] or 0) * weights[dim] for dim in value_dimensions
        }
        # -----------------------------
        # Compute value tags for saving
        # -----------------------------
        # Tags represent the highest priority dimensions 
        # based on weighted scores
        top_dimensions =[]
        
        if apply_effective_weights and st.session_state["weights_touched"]:
            if weighted_scores:
                top_score = max(weighted_scores.values())
                
                if top_score > 0:
                    top_dimensions=[
                        dim for dim, val in weighted_scores.items()
                        if val == top_score
                    ]
        # -----------------------------            
        # Continue with overall score calculations
        # -----------------------------
        total_score = sum(weighted_scores.values())
        max_possible = sum(5 * weights[dim] for dim in value_dimensions)
        
        #Prevent division by 0
        if max_possible == 0:
            st.warning("All weights are set to 0, weighted score cannot be calculated."
                       "Increase at least one weight above 0 to continue.")
            st.stop()
            
        final_score_percent = round((total_score / max_possible) * 100, 2)
        
        # Top dimensions for display
        max_score = max(weighted_scores.values())
        top_dim = [dim for dim, val in weighted_scores.items() if val == max_score]
        top_dim_str = ", ".join(top_dim)

        # Payload with weights
        payload = {
            "submit_id": st.session_state["submit_id"],
            "dataset_sig": st.session_state["dataset_sig"],
            "use_case": st.session_state["selected_use_case"],
            "apply_weights": True,
            "stars": {d: int(scores[d] or 0) for d in value_dimensions},
            "weights": weights,
            "final_score_percent": float(final_score_percent),
            "tags": top_dimensions,
        }
        
        # Store payload
        st.session_state["latest_payload"] = payload

        st.markdown(
            f"""
            **Weighted Valuation Score:** {final_score_percent}%  
            **Top Score Dimension(s):** {top_dim_str}  
            **Use Case:** {selected_use_case}
            """
        )

        weighted_df = pd.DataFrame(
            {
                "Dimension": value_dimensions,
                "Stars (0-5)": [int(scores[d] or 0) for d in value_dimensions],
                "Weights": [weights[d] for d in value_dimensions],
                "Weighted Score": [
                    round(weighted_scores[d], 2) for d in value_dimensions
                ],
            }
        )
        st.dataframe(weighted_df, width="stretch")

    # Save results to database only if the user clicks "Save Results"
    # Prevents duplicate saves on reruns and ensure re calculations don't overwrite stored results
    st.divider()
    # Check if the current valuation has been saved
    already_saved =(
    st.session_state.get("latest_payload") is not None
    and st.session_state.get("saved_submit_id") 
    == st.session_state.get("latest_payload", {}).get("submit_id")
    )
    
    # Display message depending on status: success message - if results saved; guidance message - if not saved yet
    if already_saved:
        st.success("Results saved successfully!")
    else:
        st.info("When you're happy with the results, click **Save Results** to store them.")
    
    # Button before save "Save Results" and after - "Saved"
    button_label = "Saved" if already_saved else "Save Results"
    if st.button(button_label, disabled=already_saved):
        payload = st.session_state.get("latest_payload")
        if not payload:
            st.warning("No results to save yet.")
        else:
            payload["created_at"] = datetime.now(timezone.utc).isoformat()
            try:
                save_valuation(payload)
                st.session_state["saved_submit_id"] = payload["submit_id"]
                st.success("Results saved successfully!")
                st.rerun() #refresh UI to get button disabled
            except Exception as e:
                st.error(f"Couldn't save results to the database: {e}")   
                      
    st.info("Click **Show graph** to see how star rating and weights affect scores and priorities.")
    # Show graphs
    if st.button("Show graphs"):
        st.subheader("Visualisation of Scores")

        if apply_effective_weights:
            # Weighted chart
            df_plot = pd.DataFrame(
                {
                    "Dimension": value_dimensions,
                    "Score": [
                        round(weighted_scores[dim], 2) for dim in value_dimensions
                    ],
                }
            )
            chart_title = "Weighted Value Dimension Scores"
            y_axis_label = "Weighted Score"
        else:
            # Non-Weighted chart
            df_plot = pd.DataFrame(
                {
                    "Dimension": value_dimensions,
                    "Score": [
                        round(float(scores.get(dim, 0) or 0), 2) for dim in value_dimensions
                    ],
                }
            )

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
            text="Score",
        )
        # Format text on bars (always 2 decimals, placed outside the bar)
        fig.update_traces(texttemplate="%{y: .2f}", textfont_size=16)

        fig.update_layout(yaxis_title=y_axis_label)

        plotly_config = {
            "displayModeBar": False,
            "responsive": True,
            "scrollZoom": False,
            "doubleClick": False,
        }
        st.plotly_chart(fig, config=plotly_config)

        # -----------------------------
        # Build rating table
        # -----------------------------
        rating_rows = []

        for dim in value_dimensions:
            stars = int(scores.get(dim, 0) or 0)

            # Base row
            row = {"Dimension": dim, "Stars (0-5)": stars, "Stars": star_string(stars)}

            # Apply weighted score if chosen
            if apply_weights:
                w = float(weights.get(dim, 1.0))  # fallback
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
            sort_col = "Weighted Score" if apply_effective_weights else "Stars (0-5)"
            rating_df = rating_df.sort_values(by=sort_col, ascending=False)

            # -----------------------------
            # Display summary
            # -----------------------------
            st.markdown("## ⭐ Value Rating Summary")
            for _, row in rating_df.iterrows():
                if apply_effective_weights:
                    st.markdown(f"**{row['Dimension']}**: {row['Stars']} ")
                else:
                    st.markdown(f"**{row['Dimension']}**:{row['Stars']}")

            # -----------------------------
            # Tags - prioritised value dimentions
            #
            # Tags shown ONLY when weights are applied            
            # If no weights - no tags shown, only the rating table / summary displayed
            # -----------------------------
            
            if apply_effective_weights and st.session_state["weights_touched"]:
                    
                if top_dimensions:
                    tags_html = "".join(f'<div class="oval-tag"> {dim}</div>' for dim in top_dimensions)
                    st.markdown(
                       f'## 🏷️ Tags <div class="tag-container">{tags_html}</div>',
                       unsafe_allow_html=True,
                    )
                else:
                    st.info("No tags to show (all weighted scores are 0).")
            else:
                st.info("Tags are shown when you apply weights.")

            
            
