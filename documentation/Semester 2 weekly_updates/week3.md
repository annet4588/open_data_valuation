## Week 3 (26 January)
**Focus:** Second Iteration: database integration, persistence of valuation results, and preparation for empirical testing.

---

### Highlights
- Integrated a **Supabase database** to enable persistent storage of valuation results:
-- Implemented secure saving of valuation payloads, including:
--- Star ratings
--- Applied weights (when used)
--- Final valuation score
--- Value tags (when weights are applied)
--- Use case metadata

- Refined **payload structure and submission flow**:
-- Ensured value tags are calculated **before saving** and correctly recorded in the database
-- Prevented duplicate inserts caused by Streamlit reruns

- Improved **Submission and state management**:
-- Added safeguards to ensure results are saved **only when explicitly submitted** (Save Results)
-- Disabled the **Save Results** button after succesful submission
-- Added user **confirmation notice** once results are stored

- Improved data integrity and ready for analysis:
-- Confirmed that tags are saved **only when weights are meaningfully applied**

- Conducted internal testing using example datasets to validate:
-- Database writes
-- Payload completeness
-- Consistency between UI output and stored records

---

**Outcome:**  
- Made a reliable data storage layer to support analysis
- Enabled systematic collection of stakeholder valuations for later comparison
- Prepared the tool for structered testing and response collection in the following weeks
- Transition from prototype to **reserach-ready tool**

---