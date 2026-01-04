# Open Data Valuation Tool - Dissertation Project

## Overview
The **Open Data Valuation Tool** is an interactive web application developed as part of a dissertation project.  
It supports the systematic evaluation of open datasets by allowing users to score their value across multiple strategic dimensions, such as economic, social, environmental, and policy relevance.

The tool is implemented using **Python** and **Streamlit**, providing an accessible interface for non-technical users while maintaining a transparent and reproducible evaluation methodology.

---

## Background
This project addresses that gap by:
- Combining data quality assessment with user-defined value scoring
- Supporting different use cases that influence how value is perceived
- Providing a repeatable framework for qualitative and semi-quantitative evaluation

---

## Project Aim
Specific objectives include:
- Assessing datasets using clearly defined value dimensions
- Allowing users to apply star-based ratings (0–5)
- Supporting optional weighting of dimensions
- Providing transparent scoring summaries and visualisations
- Ensuring usability for policy, planning, and data governance contexts

---

## Methodology
The valuation methodology consists of the following steps:

1. **Dataset Upload**
   - Users upload a CSV or Excel dataset.
   - The dataset is previewed and assessed for basic quality indicators.

2. **Data Quality Assessment**
   - Automated checks evaluate completeness, structure, and usability.
   - Results are displayed as a structured summary.

3. **Use Case Selection**
   - Users select a predefined use case (e.g. planning, environmental monitoring).
   - This contextualises how value is interpreted.

4. **Value Dimension Scoring**
   - Datasets are scored across six dimensions:
     - Economic
     - Social
     - Environmental
     - Cultural
     - Policy Alignment
     - Data Quality
   - Each dimension is rated on a 0–5 star scale.

5. **Optional Weighting**
   - Users may apply custom weights to dimensions.
   - Both weighted and unweighted valuation results are supported.

6. **Results and Visualisation**
   - Final valuation scores are calculated.
   - Results are presented in tables and interactive charts.

---


## How to Run

### Local Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd open-data-valuation

2. (Optional) Create a virtual environment:
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

4. Run the Streamlit app
   streamlit run app.py

