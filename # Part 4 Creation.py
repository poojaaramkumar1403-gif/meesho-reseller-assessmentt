# Part 4 Creation

# 1. part4_agent/agent_spec.md
agent_spec_md = """# Meesho Reseller Alert Intelligence Agent Specification

## 1. Executive Goal
Keep Meesho category managers informed of any category whose month-on-month revenue moves beyond the 8% threshold, with a human approving every message before it goes out.

---

## 2. System Architecture & Components

### A. Goal
Automate the monthly monitoring of category sales velocity across Meesho's reseller ecosystem, flag significant movements (|MoM| > 8.0%), apply caps to prevent notification fatigue, enforce strict PII/data-integrity guardrails, and generate human-reviewable draft alerts.

### B. Tools (Concrete Python Functions)
1. `validate_feed(csv_path: str) -> tuple[bool, list[str]]`: Validates input CSV integrity (Part 2).
2. `mom_growth(previous: float, current: float) -> float`: Computes percentage growth rounded to 2 decimal places (Part 2).
3. `is_flagged(mom_pct: float, threshold: float = 8.0) -> str`: Classifies movements into `"flagged"`, `"not_flagged"`, or `"escalate_exact_boundary"` (Part 2).
4. `draft_category_message(...)`: Fills deterministic prompt-pack templates to draft stakeholder alerts (Part 3).

### C. Memory & State
* **Persistent Baseline State**: Historical category revenue totals from the prior month (stored in `monthly_category_revenue.csv`).
* **Active Execution State**:
  * `validation_status`: `"valid"` or `"invalid"`
  * `validation_errors`: List of validation error strings
  * `flagged_categories`: List of category objects exceeding threshold
  * `suppressed_categories`: List of category names suppressed due to the 3-message cap
  * `escalated_categories`: List of category names on the exact 8.0% threshold boundary

### D. Planner (Ordered Subtasks 1–8)
1. **Load & Validate Feed**: Load current month revenue CSV and execute `validate_feed`.
2. **Hard Stop Check**: If `validate_feed` returns `False`, trigger `action_taken = "hard_stop"`, populate `validation_errors`, log error, and stop execution immediately.
3. **Compute MoM Growth**: If valid, pair each category with its previous month revenue baseline and calculate `mom_growth(prev, curr)`.
4. **Evaluate Thresholds**: Run `is_flagged(mom_pct, threshold=8.0)` for every category.
5. **Sort Flagged Movements**: Filter categories where `is_flagged == "flagged"` and sort descending by magnitude (`abs(mom_pct)`).
6. **Draft Top 3 Messages (Capped)**: Select at most the top 3 flagged categories by magnitude and generate narrative drafts (`drafted = true`).
7. **Handle Overflow & Exact Boundaries**:
   * **7a (Suppressed Categories)**: Move remaining flagged categories beyond the top 3 cap into `suppressed_categories` (`drafted = false`), logging them as "suppressed, review manually".
   * **7b (Exact Boundary Escalation)**: Move any category with `is_flagged == "escalate_exact_boundary"` into `escalated_categories` without drafting, routing to human ops for manual review.
8. **Emit JSON Payload**: Output a single standardized JSON payload containing the complete execution trace and set `action_taken = "drafted_and_held_for_approval"`.

### E. Feedback Loop (Human-in-the-Loop Guardrail)
No drafted message is ever sent automatically over SMTP, Slack, or WhatsApp. Every generated draft is marked as `drafted_and_held_for_approval` in the JSON output, requiring explicit human category manager review and approval prior to distribution.

---

## 3. Guardrails & Safety Controls

| Guardrail Type | Mechanism | Operational Enforcement |
| :--- | :--- | :--- |
| **Input Guardrail** | `validate_feed` | Halts execution on missing categories, non-numeric revenue, or negative values. |
| **Action Guardrail** | Draft-and-Hold Pattern | Zero auto-sending; all outputs are queued for human approval. |
| **Output Guardrail** | Template Determinism & Masking | All narrative numbers must trace verbatim to SQL/Engine outputs; raw reseller names masked via `alias_for`. |

---

## 4. System Stopping Conditions
* **Success Stopping Condition**: Valid CSV feed processed, MoM computed for all categories, top 3 flagged messages drafted, overflow suppressed, and JSON emitted with `action_taken = "drafted_and_held_for_approval"`.
* **Error Stopping Condition**: Input CSV fails `validate_feed`. Execution immediately terminates with `action_taken = "hard_stop"`, `validation_status = "invalid"`, and zero MoM or narrative calculations attempted.

---

## 5. Agent-Level Given-When-Then Specifications

### Spec 1: Significant Expansion Flagging
* **GIVEN** April→May Ethnic Wear revenue moves from INR 104,520.77 to INR 185,107.61
* **WHEN** the agent processes the May execution run
* **THEN** it computes MoM growth of 77.1%, sets `is_flagged = "flagged"`, and drafts a stakeholder alert.

### Spec 2: Minor Movement Non-Flagging
* **GIVEN** May→June Beauty & Personal Care revenue moves from INR 35,542.11 to INR 37,559.07
* **WHEN** the agent processes the June execution run
* **THEN** it computes MoM growth of 5.67%, sets `is_flagged = "not_flagged"`, and excludes it from `flagged_categories` and `suppressed_categories`.

### Spec 3: Exact Threshold Boundary Escalation
* **GIVEN** a synthetic category revenue moving from INR 100,000.00 to INR 108,000.00 (exact 8.0% boundary)
* **WHEN** evaluated by the agent
* **THEN** `is_flagged` returns `"escalate_exact_boundary"`, no draft message is created, and the category is placed in `escalated_categories` for human review.

### Spec 4: Corrupted Feed Hard Stop
* **GIVEN** an input CSV containing negative revenue or missing category fields
* **WHEN** `validate_feed` executes
* **THEN** the agent immediately triggers a Hard Stop (`action_taken = "hard_stop"`), returns `validation_status = "invalid"`, outputs the exact 3 validation error messages, and leaves all category lists empty.
"""

with open(f"{repo_dir}/part4_agent/agent_spec.md", "w") as f:
    f.write(agent_spec_md)

# 2. part4_agent/mock_agent_runner.py
mock_agent_runner_py = '''import csv
import json
import os
import sys

# Ensure part2_engine and part3_narrative are importable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from part2_engine.growth_engine import mom_growth, is_flagged, validate_feed
from part3_narrative.masking import alias_for, assert_no_raw_names_leak

def load_revenue_dict(csv_path: str, target_month: str = None) -> dict:
    \"\"\"Reads a validated monthly_category_revenue CSV and returns {category: revenue}.\"\"\"
    revenue_map = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = row["month"].strip()
            if target_month is None or m.lower() == target_month.lower():
                cat = row["category"].strip()
                rev = float(row["revenue"].strip())
                revenue_map[cat] = rev
    return revenue_map

def draft_category_message(category: str, current_month: str, prev_month: str, prev_rev: float, curr_rev: float, mom_pct: float) -> str:
    \"\"\"Offline template fill function for generating deterministic category updates.\"\"\"
    direction = "increased" if mom_pct > 0 else "decreased"
    msg = (
        f"Alert for {category} in {current_month}: Revenue {direction} by {mom_pct}% MoM "
        f"(from INR {prev_rev:.2f} in {prev_month} to INR {curr_rev:.2f} in {current_month}). "
        f"[Context: {category} {current_month} vs {prev_month} | Insight: [FACT] MoM movement of {mom_pct}% | "
        f"Implication: [HYPOTHESIS] Audit regional catalog inventory and seller engagement.]"
    )
    return msg

def run(current_month: str, previous_month_csv: str, current_month_csv: str, prev_month_name: str = None) -> dict:
    \"\"\"Executes the complete 8-subtask Agent monitoring pipeline.
    
    Returns structured JSON output matching spec 4.3.
    \"\"\"
    # Subtask 1: Load and validate current month feed
    valid, errors = validate_feed(current_month_csv)
    
    # Subtask 2: Hard Stop if invalid
    if not valid:
        return {
            "run_month": current_month,
            "validation_status": "invalid",
            "validation_errors": errors,
            "flagged_categories": [],
            "suppressed_categories": [],
            "escalated_categories": [],
            "action_taken": "hard_stop"
        }
    
    # Automatically infer previous month name if not provided
    month_order = ["April", "May", "June", "July"]
    if prev_month_name is None:
        if current_month in month_order and month_order.index(current_month) > 0:
            prev_month_name = month_order[month_order.index(current_month) - 1]
        else:
            prev_month_name = "Previous Month"
            
    # Load revenue data dictionaries
    prev_revenues = load_revenue_dict(previous_month_csv, target_month=prev_month_name)
    curr_revenues = load_revenue_dict(current_month_csv, target_month=current_month)
    
    flagged_candidates = []
    escalated_categories = []
    
    # Subtasks 3 & 4: Compute MoM growth and evaluate is_flagged for each category
    all_categories = sorted(list(curr_revenues.keys()))
    for cat in all_categories:
        curr_rev = curr_revenues[cat]
        prev_rev = prev_revenues.get(cat, 0.0)
        
        growth = mom_growth(prev_rev, curr_rev)
        status = is_flagged(growth, threshold=8.0)
        
        if status == "flagged":
            flagged_candidates.append({
                "category": cat,
                "mom_pct": growth,
                "previous_revenue": prev_rev,
                "current_revenue": curr_rev,
                "abs_mom": abs(growth)
            })
        elif status == "escalate_exact_boundary":
            # Subtask 7b: Exact boundary escalation
            escalated_categories.append(cat)
            
    # Subtask 5: Sort flagged categories by abs(mom_pct) descending
    flagged_candidates.sort(key=lambda x: x["abs_mom"], reverse=True)
    
    # Subtask 6 & 7: Apply top-3 cap, draft messages, and track suppressed
    flagged_categories_out = []
    suppressed_categories_out = []
    
    for idx, item in enumerate(flagged_candidates):
        if idx < 3:
            # Top 3: Draft message
            msg = draft_category_message(
                category=item["category"],
                current_month=current_month,
                prev_month=prev_month_name,
                prev_rev=item["previous_revenue"],
                curr_rev=item["current_revenue"],
                mom_pct=item["mom_pct"]
            )
            flagged_categories_out.append({
                "category": item["category"],
                "mom_pct": item["mom_pct"],
                "previous_revenue": item["previous_revenue"],
                "current_revenue": item["current_revenue"],
                "drafted": True,
                "message": msg
            })
        else:
            # Beyond top 3 cap: Suppress
            suppressed_categories_out.append(item["category"])
            
    # Subtask 8: Emit structured JSON output object
    output = {
        "run_month": current_month,
        "validation_status": "valid",
        "validation_errors": [],
        "flagged_categories": flagged_categories_out,
        "suppressed_categories": sorted(suppressed_categories_out),
        "escalated_categories": sorted(escalated_categories),
        "action_taken": "drafted_and_held_for_approval"
    }
    return output

if __name__ == "__main__":
    # Test runner on May and June scenarios
    p1_output = os.path.join(BASE_DIR, "part1_sql", "output", "monthly_category_revenue.csv")
    corrupted = os.path.join(BASE_DIR, "part2_engine", "fixtures", "corrupted_feed.csv")
    
    print("--- May Run (April -> May) ---")
    may_res = run("May", p1_output, p1_output, prev_month_name="April")
    print(json.dumps(may_res, indent=2))
    
    print("\n--- June Run (May -> June) ---")
    june_res = run("June", p1_output, p1_output, prev_month_name="May")
    print(json.dumps(june_res, indent=2))
    
    print("\n--- Corrupted Feed Run ---")
    corrupt_res = run("July", p1_output, corrupted)
    print(json.dumps(corrupt_res, indent=2))
'''

with open(f"{repo_dir}/part4_agent/mock_agent_runner.py", "w") as f:
    f.write(mock_agent_runner_py)

print("Part 4 code & spec created.")