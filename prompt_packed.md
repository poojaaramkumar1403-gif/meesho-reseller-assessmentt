# Meesho Reseller Intelligence — Narrative Prompt Pack

This prompt pack turns flagged category metrics into executive updates without inventing figures.

---

## 1. Trigger
This prompt executes when a category's `is_flagged` status evaluates to `"flagged"` (i.e., $\vert{}MoM\%\vert{} > 8.0\%$).

---

## 2. Input List
The prompt template requires the following input variables:
- `{category}`: Name of the e-commerce category (e.g., `Ethnic Wear`).
- `{current_month}`: Current reporting month (e.g., `May`).
- `{prev_month}`: Immediately preceding month (e.g., `April`).
- `{previous_revenue}`: Formatted baseline revenue string (e.g., `₹1,04,520.77`).
- `{current_revenue}`: Formatted current revenue string (e.g., `₹1,85,107.61`).
- `{mom_pct}`: Month-over-Month percentage change string (e.g., `77.1%`).

---

## 3. Prompt Template
```text
You are an operations analyst at Meesho drafting an update for Category Managers and Regional Ops.

Generate an executive performance summary for {category} covering {current_month} vs. {prev_month}. 

Follow this strict structure:
1. Context: State the category, reporting period ({current_month} vs. {prev_month}), and baseline revenue ({previous_revenue}).
2. Insight: Explicitly state the exact percentage change ({mom_pct}) and new revenue figure ({current_revenue}). Label this sentence explicitly as [FACT].
3. Implication: Provide a concrete, actionable next step for regional field teams or category managers. Label any proposed drivers or causes explicitly as [HYPOTHESIS].

CRITICAL CONSTRAINTS:
- Do NOT invent or extrapolate any numeric values. Use ONLY the supplied placeholders.
- Do NOT alter raw category names.
- Do NOT auto-approve external distribution.