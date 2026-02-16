
## Week 5 (9 February)
**Focus:** Second Iteration: Enhancing user feedback mechanisms and strengthening evaluation readiness.

---

### Highlights
- Designed and implemented a new **Quick Feedback** section within the application to capture structured stakeholder input directly in the tool.

- Created a short **three-question survey** with an optional comment field to reduce reliance on email-based feedback and improve response consistency.

- Configured the feedback responses to be stored alongside valuation results in the database for future analysis.

- **Updated the database**: added additional fields for collecting feedback.

- Implemented session state control to insure feedback is linked to the correct valuation run and locked ```feedback_locked``` once the results are saved.

- Refined state management logic to prevent duplicate submissions and feedback resets appropriatly when triggered.

---

**Outcome:**
- Created a structured **Feedback mechanism** embedded within the user workflow.
- Improved data quality by standardising how stakeholder feedbak is collected.
- **Reduced time** for busy stakeholders being able to complete a quick 30 seconds survey rather than separate email communication.
- Improved the project evaluation framework in preparation for stakeholder testing in Week 6.

---
