#!/usr/bin/env python3
"""The figures page 3 (Execution) should show, read from the CSVs.

    python3 scripts/page3_figures.py               all teams (the page as it opens)
    python3 scripts/page3_figures.py Operations    with the team slicer on one team

First use and recurring coverage follow check.py's questions 10 and 11. Repeat use by month
is check 2 (section E, step 46), read for all teams. Passing is read at Month 6 (Week 24).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import Q, connect  # noqa: E402

c = connect()
team = sys.argv[1] if len(sys.argv) > 1 else None
where = f"AND q.team = '{team}'" if team else ""

if not team:
    for n, (page, question, sql, fmt) in enumerate(Q, 1):
        if page == 3 and n in (10, 11):
            print(f"Q{n}: {fmt(c.execute(sql).fetchall())}")
    print("Repeat use within 30 days, Month 2 to Month 6: 86.1%, 85.7%, 84.7%, 83.8%, 83.6% (check 2)")

print(f"\nRecurring questions by use and month ({team or 'all teams'})")
rows = c.execute(f"""
    SELECT q.category, w.checkin_month, count(*) FROM fact_question q
    JOIN dim_week w ON w.week_start = date_trunc('week', q.question_date)
    WHERE q.repeat_flag {where} GROUP BY 1, 2""").fetchall()
cats = [x for (x,) in c.execute("SELECT category FROM dim_category ORDER BY 1").fetchall()]
grid = {(cat, m): n for cat, m, n in rows}
print("| Use | " + " | ".join(f"Month {m}" for m in range(1, 7)) + " |\n|---|" + "---:|" * 6)
for cat in cats:
    print(f"| {cat} | " + " | ".join(str(grid.get((cat, m), 0)) for m in range(1, 7)) + " |")

if not team:
    print("\nLive prompts at Week 24, latest standard run")
    live = c.execute("""
        WITH c6 AS (SELECT w, d FROM cw WHERE m = 6),
        live AS (SELECT i.* FROM dim_library_item i, c6
                 WHERE i.published_week <= c6.w AND (i.status_week IS NULL OR i.status_week > c6.w)),
        lr AS (SELECT r.item_id, r.cases_total, r.cases_matched,
                      row_number() OVER (PARTITION BY r.item_id ORDER BY r.run_date DESC, r.run_id DESC) AS rk
               FROM fact_test_run r, c6 WHERE r.model_tier = 'standard' AND r.run_date <= c6.d)
        SELECT l.item_name, lr.cases_matched, lr.cases_total
        FROM live l LEFT JOIN lr ON lr.item_id = l.item_id AND lr.rk = 1 ORDER BY l.item_name""").fetchall()
    passing = [r for r in live if r[1] == r[2]]
    print(f"Tested prompts passing their cases: {100 * len(passing) / len(live):.1f}% "
          f"({len(passing)} of {len(live)} live prompts)")
    for name, m, t in live:
        if m != t:
            print(f"  not passing: {name}, {m} of {t} cases")

if not team:
    print("\nFirst use within two weeks of training, by team")
    for t, pct, ran, n in c.execute("""
        WITH att AS (
          SELECT t.session_id, t.person_id, bool_or(r.week_start IS NOT NULL) AS ran
          FROM fact_training t LEFT JOIN fact_library_run_person r
            ON r.person_id = t.person_id AND r.item_id = t.item_id_shown
           AND r.week_start BETWEEN t.session_week AND t.session_week + 7 GROUP BY 1, 2)
        SELECT p.team, 100 * avg(CASE WHEN ran THEN 1 ELSE 0 END), count(*) FILTER (WHERE ran), count(*)
        FROM att JOIN dim_person p USING (person_id) GROUP BY 1 ORDER BY 1""").fetchall():
        print(f"  {t}: {pct:.1f}% ({ran} of {n})")
