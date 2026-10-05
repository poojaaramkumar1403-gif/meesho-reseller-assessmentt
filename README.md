# Write Part 1 README.md
part1_readme = """# Part 1: SQL Business Query Engine Output Documentation

## Overview
This directory contains the SQL query suite (`queries.sql`), python execution script (`queries.py`), and exported query result CSV files (`output/`).

## Query Summaries & Verification Results

### 1. Monthly Category Revenue (`output/monthly_category_revenue.csv`)
* **Total Rows**: Exactly 15 rows (5 categories across April, May, June 2026).
* **Columns**: `month`, `category`, `revenue`, `n_orders`
* **Grand Total Revenue**: **INR 1,262,066.92** across all 900 orders.

### 2. Region-Wise Revenue & Order Count (`output/region_revenue.csv`)
* **North**: INR 337,125.46 (231 orders)
* **West**: INR 333,106.33 (232 orders)
* **South**: INR 316,736.68 (216 orders)
* **East**: INR 275,098.45 (221 orders)
* **Sum**: Exactly matches Grand Total of **INR 1,262,066.92** across 900 orders.

### 3. Top Resellers by Total Spend (`output/top_resellers.csv`)
Query restricted to `total_spend > 50000`, ordered descending, limited to 5 rows:
1. `RS019` ("Mumbai Reseller 1"): INR 75,295.09
2. `RS022` ("Mumbai Reseller 4"): INR 73,882.33
3. `RS012` ("Hyderabad Reseller 6"): INR 69,936.46
4. `RS006` ("Lucknow Reseller 6"): INR 64,238.97
5. `RS005` ("Jaipur Reseller 5"): INR 61,825.02

### 4. Zero-Order Resellers & `COUNT(*)` Explanation (`output/zero_order_resellers.csv` & `output/count_demonstration.csv`)
* **Zero-Order Reseller**: Exactly one reseller (`RS024`, "Ahmedabad Reseller 6", Region: West) has placed zero orders.
* **Explanation of `COUNT(*)` vs `COUNT(order_id)`**:
  * In a `LEFT JOIN` between `resellers` and `orders`, unmatched resellers generate a single row with all `resellers` columns populated and all `orders` columns set to `NULL`.
  * `COUNT(*)` counts the total number of rows returned by the join group regardless of `NULL` values. Thus, for `RS024`, `COUNT(*)` evaluates to `1`.
  * `COUNT(order_id)` specifically evaluates non-NULL values in the `order_id` column. Because `order_id` is `NULL` for an unmatched row, `COUNT(order_id)` evaluates to `0`.
  * **Conclusion**: `COUNT(*)` cannot be used to detect zero-match `LEFT JOIN` rows because it falsely reports `1`. Production queries must evaluate `COUNT(order_id)` or check `WHERE order_id IS NULL`.

### 5. Average Order Value (AOV) for June Delivered Orders (`output/june_delivered_aov.csv`)
* Restricted to `month = 'June'` AND `status = 'Delivered'`.
* **June Delivered AOV**: **INR 1,267.69**.
"""

with open(f"{repo_dir}/part1_sql/output/README.md", "w") as f:
    f.write(part1_readme)

# Part 2 files creation
# 1. Fixture: corrupted_feed.csv
corrupted_feed_csv = """month,category,revenue,n_orders
July,Ethnic Wear,98450.00,61
July,Western Wear,-4200.00,38
July,,52310.00,45
July,Kids Wear,61200.50,50
July,Home & Kitchen,,42
July,Beauty & Personal Care,39870.25,44
"""
with open(f"{repo_dir}/part2_engine/fixtures/corrupted_feed.csv", "w") as f:
    f.write(corrupted_feed_csv.strip() + "\n")

# 2. part2_engine/growth_engine.py
growth_engine_py = '''import csv

def mom_growth(previous: float, current: float) -> float:
    \"\"\"Calculates Month-on-Month growth percentage rounded to 2 decimal places.\"\"\"
    if previous == 0:
        raise ValueError("Previous revenue cannot be zero for percentage growth calculation.")
    return round((current - previous) / previous * 100.0, 2)

def is_flagged(mom_pct: float, threshold: float = 8.0) -> str:
    \"\"\"Determines whether MoM percentage movement exceeds threshold or lands on boundary.\"\"\"
    abs_mom = abs(mom_pct)
    if abs_mom > threshold:
        return "flagged"
    elif abs_mom < threshold:
        return "not_flagged"
    else:
        return "escalate_exact_boundary"

def validate_feed(csv_path: str) -> tuple[bool, list[str]]:
    \"\"\"Validates a month,category,revenue,n_orders CSV feed.
    
    Checks every data row (line 2 onward, 1-indexed):
    1. Category not blank
    2. Revenue present, float-parseable, and non-negative
    \"\"\"
    errors = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return False, [f"File read error: {str(e)}"]

    if not lines:
        return False, ["Empty feed file"]

    # Parse CSV using standard csv reader to respect quotes if any
    reader = csv.reader(lines)
    header = next(reader, None)

    for idx, row in enumerate(reader, start=2):
        if not row or all(c.strip() == "" for c in row):
            continue  # skip completely empty lines if any
        
        # Ensure row has required length
        month = row[0].strip() if len(row) > 0 else ""
        category = row[1].strip() if len(row) > 1 else ""
        revenue_raw = row[2].strip() if len(row) > 2 else ""

        # Validation Rule 1: Category blank check
        if not category:
            errors.append(f"line {idx}: missing category (month={month})")
            continue  # as per test specification order

        # Validation Rule 2: Revenue blank check
        if not revenue_raw:
            errors.append(f"line {idx}: missing revenue (category={category})")
            continue

        # Validation Rule 3 & 4: Revenue numeric & non-negative check
        try:
            revenue_val = float(revenue_raw)
            if revenue_val < 0:
                errors.append(f"line {idx}: negative revenue ({revenue_raw}) for category={category}")
        except ValueError:
            errors.append(f"line {idx}: revenue not numeric: {revenue_raw!r}")

    if errors:
        return False, errors
    return True, []
'''

with open(f"{repo_dir}/part2_engine/growth_engine.py", "w") as f:
    f.write(growth_engine_py)

# 3. part2_engine/test_growth_engine.py
test_growth_engine_py = '''import unittest
import os
import sys

# Ensure part2_engine module importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from part2_engine.growth_engine import mom_growth, is_flagged, validate_feed

class TestGrowthEngine(unittest.TestCase):

    def test_given_when_then_case_1(self):
        # GIVEN April->May Ethnic Wear revenue moves from 104520.77 to 185107.61
        prev = 104520.77
        curr = 185107.61
        # WHEN mom_growth then is_flagged run
        growth = mom_growth(prev, curr)
        flag = is_flagged(growth)
        # THEN mom_growth returns 77.1 and is_flagged returns "flagged"
        self.assertEqual(growth, 77.1)
        self.assertEqual(flag, "flagged")

    def test_given_when_then_case_2(self):
        # GIVEN May->June Beauty & Personal Care revenue moves from 35542.11 to 37559.07
        prev = 35542.11
        curr = 37559.07
        # WHEN evaluated
        growth = mom_growth(prev, curr)
        flag = is_flagged(growth)
        # THEN mom_growth returns 5.67 and is_flagged returns "not_flagged"
        self.assertEqual(growth, 5.67)
        self.assertEqual(flag, "not_flagged")

    def test_given_when_then_case_3(self):
        # GIVEN synthetic pair previous=100000, current=108000
        prev = 100000.0
        curr = 108000.0
        # WHEN evaluated
        growth = mom_growth(prev, curr)
        flag = is_flagged(growth)
        # THEN mom_growth returns exactly 8.0 and is_flagged returns "escalate_exact_boundary"
        self.assertEqual(growth, 8.0)
        self.assertEqual(flag, "escalate_exact_boundary")

    def test_given_when_then_case_4(self):
        # GIVEN corrupted feed fixture
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "corrupted_feed.csv")
        # WHEN validate_feed runs on it
        valid, errors = validate_feed(fixture_path)
        # THEN returns (False, errors) with exactly 3 entries in exact order
        self.assertFalse(valid)
        self.assertEqual(len(errors), 3)
        expected_errors = [
            "line 3: negative revenue (-4200.00) for category=Western Wear",
            "line 4: missing category (month=July)",
            "line 6: missing revenue (category=Home & Kitchen)"
        ]
        # Note: line 3 raw revenue in fixture is -4200.00
        self.assertIn("line 3: negative revenue", errors[0])
        self.assertIn("line 4: missing category", errors[1])
        self.assertIn("line 6: missing revenue", errors[2])

    def test_valid_feed_monthly_category_revenue(self):
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "monthly_category_revenue.csv")
        valid, errors = validate_feed(fixture_path)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
'''

with open(f"{repo_dir}/part2_engine/test_growth_engine.py", "w") as f:
    f.write(test_growth_engine_py)

print("Part 2 code & tests created.")
