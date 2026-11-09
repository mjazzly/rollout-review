#!/usr/bin/env python3
"""The figures page 2 (Foundation) should show, read from the CSVs.

    python3 scripts/page2_figures.py

A question's month is the check-in month of the week it was asked in (as check.py).
Usage baselines are check 4's (section E, step 48), from check.py's question 9 rule.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import connect  # noqa: E402

c = connect()
rank = c.execute("""
    SELECT w.checkin_month AS m, q.category, count(*) AS n
    FROM fact_question q JOIN dim_week w ON w.week_start = date_trunc('week', q.question_date)
    WHERE w.checkin_month IN (1, 6) GROUP BY 1, 2 ORDER BY 1, 3 DESC, 2""").fetchall()
for m in (1, 6):
    rows = [(cat, n) for mm, cat, n in rank if mm == m]
    print(f"\nUses logged and ranked, Month {m} ({sum(n for _, n in rows)} questions)")
    for cat, n in rows:
        print(f"  {cat}: {n}")
print(f"Largest bar on either chart: {max(n for *_, n in rank)}")

print("\nQuestions by month: Rules and allowed use against all other uses")
for m, r, o in c.execute("""
    SELECT w.checkin_month, count(*) FILTER (WHERE category = 'Rules and allowed use'),
           count(*) FILTER (WHERE category <> 'Rules and allowed use')
    FROM fact_question q JOIN dim_week w ON w.week_start = date_trunc('week', q.question_date)
    GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"  Month {m}: {r} and {o}")

share, matched, total = c.execute("""
    SELECT avg(CASE WHEN action_taken = 'pointed to library' THEN 1 ELSE 0 END),
           count(*) FILTER (WHERE action_taken = 'pointed to library'), count(*) FROM fact_question""").fetchone()
print(f"\nRequests matched to a tested prompt that already exists: {100 * share:.1f}% ({matched} of {total} questions)")

items, akf = c.execute("SELECT count(*), count(*) FILTER (WHERE answer_key_first) FROM dim_library_item").fetchone()
print(f"Prompts tested against an answer key written first: {100 * akf / items:.1f}% ({akf} of {items} library items)")

print("\nUsage baseline by team")
for team, b in c.execute("""
    WITH first_seat AS (SELECT team, min(seat_assigned_week) AS s0 FROM dim_person GROUP BY 1),
    weeks AS (SELECT f.team, w.week_start FROM first_seat f
              JOIN dim_week w ON w.week_start BETWEEN f.s0 AND f.s0 + 21),
    share AS (
      SELECT k.team, k.week_start,
             count(*) FILTER (WHERE u.days_active >= 2) * 1.0
               / count(*) FILTER (WHERE p.seat_assigned_week <= k.week_start) AS s
      FROM weeks k JOIN dim_person p ON p.team = k.team
      LEFT JOIN fact_usage_week u ON u.person_id = p.person_id AND u.week_start = k.week_start
      GROUP BY 1, 2)
    SELECT team, avg(s) FROM share GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"  {team}: {100 * b:.1f}%")
