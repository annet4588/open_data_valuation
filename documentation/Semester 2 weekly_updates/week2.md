## Week 1 (12 January)
**Focus:** Second Iteration: Scoring logic refinement, weighting behaviour, value tagging rules, and user guidance improvements.

---

### Highlights
- Refined the **two-step scoring model**, clearly separating:
-- **Star ratings (required)** — intrinsic dataset quality and value
-- **Weights (optional)** — user-defined prioritisation

- Implemented **safe weighting logic**
-- Weights only take effect when at least one slider is changed
-- Default weights no longer alter results
-- Weight sliders are disabled for dimensions rated 0 stars

- Improved **Value Tags** logic
-- Tags are now shown only when weights are **meaningfully applied**
-- Tags represent the dataset's **highest-priority value** dimension(s) based on weighted scores
-- **Star-only** assessments display **rating tables** without tags to avoid misinterpretation

- Enhanced **valuation results** and **visualisations**:
-- Results **dynamically switch** between star-based and weighted views
-- Ranking and charts **update consistently** with weighting behaviour

- Strengthened **session state management**:
-- Prevented users progressing without interacting with star ratings
-- Ensured **consistent behaviour** across reruns and user interactions

- Added **user guidance** and rewrote **tooltips** in clear, non-technical language:
-- Adjusted in-tool instructions
-- Developed a structured **Full User Guide** explaining stars, weights, and tags
-- Clarified **when and why** users should apply weights

---

**Outcome:**  
- Implroved clarity, transparency, and robustness of the valuation process.
- Reduced risk of accidental prioritisation or misleading results.
- Prepare the tool for the next round of stakeholder testing, with clearer guidance for both **Data Users** and **Data Providers**.
- Established a stronger foundation for future enhancements, including dataset comparison and policy-driven tagging.

---