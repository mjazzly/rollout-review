#!/usr/bin/env python3
"""The figures page 4 (Refinement) should show, read from the CSVs.

    python3 scripts/page4_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import Q, connect  # noqa: E402

c = connect()
for n, (page, question, sql, fmt) in enumerate(Q, 1):
    if page == 4:
        print(f"Q{n}: {fmt(c.execute(sql).fetchall())}")

print("\nCost per use (median tokens per run) and cost index, by prompt")
print("| Prompt | Standard | Smaller | Cost index |\n|---|---:|---:|---:|")
for item, std, sml in c.execute("""
    SELECT item_id, median(tokens_in + tokens_out) FILTER (WHERE model_tier = 'standard'),
           median(tokens_in + tokens_out) FILTER (WHERE model_tier = 'smaller')
    FROM fact_test_run GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"| {item} | {std:,.0f} | {sml:,.0f} | {std / sml:.2f} |")

print("\nPrompts retired or merged, by check-in month of the change")
for m, item, status, into in c.execute("""
    SELECT w.checkin_month, i.item_id, i.status, i.merged_into_item_id
    FROM dim_library_item i JOIN dim_week w ON w.week_start = i.status_week
    WHERE i.status IN ('retired', 'merged') ORDER BY 1, 2""").fetchall():
    print(f"  Month {m}: {item} {status}" + (f" into {into}" if into else ""))

print("\nLive prompts at Week 24, cases matched on the latest smaller-model run (round 7 main chart)")
for item, m, t in c.execute("""
    WITH c6 AS (SELECT w FROM cw WHERE m = 6),
    live AS (SELECT i.* FROM dim_library_item i, c6
             WHERE i.published_week <= c6.w AND (i.status_week IS NULL OR i.status_week > c6.w)),
    lr AS (SELECT item_id, cases_matched, cases_total,
                  row_number() OVER (PARTITION BY item_id ORDER BY run_date DESC, run_id DESC) AS rk
           FROM fact_test_run WHERE model_tier = 'smaller')
    SELECT l.item_id, lr.cases_matched, lr.cases_total FROM live l JOIN lr ON lr.item_id = l.item_id AND rk = 1
    ORDER BY lr.cases_matched * 1.0 / lr.cases_total DESC, 1""").fetchall():
    print(f"  {item}: {100 * m / t:.1f}% ({m} of {t})" + ("  passes" if m == t else ""))
