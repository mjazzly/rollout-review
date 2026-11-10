#!/usr/bin/env python3
"""The figures page 5 (Scale) should show, read from the CSVs.

    python3 scripts/page5_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import Q, connect  # noqa: E402

c = connect()
for n, (page, question, sql, fmt) in enumerate(Q, 1):
    if page == 5:
        print(f"Q{n}: {fmt(c.execute(sql).fetchall())}")

print("\nImpact in people's own words, Month 6 (lose time every week / a little / nothing)")
for team, lose, little, nothing in c.execute("""
    SELECT p.team, count(*) FILTER (WHERE q5_if_gone = 'I would lose time every week'),
           count(*) FILTER (WHERE q5_if_gone = 'A little'), count(*) FILTER (WHERE q5_if_gone = 'Nothing')
    FROM fact_checkin k JOIN dim_person p USING (person_id) WHERE k.checkin_month = 6 GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"  {team}: {lose} / {little} / {nothing}")

print("\nShare of people in the air: baseline month, baseline, Month 6, change in points")
for team, bm, base, latest in c.execute("""
    WITH size AS (SELECT team, count(*) AS n FROM dim_person GROUP BY 1),
    air AS (SELECT p.team, f.checkin_month AS m, count(*) FILTER (WHERE f.source_checkpoint_id >= 7) AS a
            FROM fact_placement f JOIN dim_person p USING (person_id) GROUP BY 1, 2)
    SELECT t.team, t.base_m, b.a * 1.0 / s.n, l.a * 1.0 / s.n FROM tb t JOIN size s USING (team)
    JOIN air b ON b.team = t.team AND b.m = t.base_m JOIN air l ON l.team = t.team AND l.m = 6
    ORDER BY 1""").fetchall():
    print(f"  {team} (Month {bm}): {100 * base:.1f}% -> {100 * latest:.1f}%, {100 * (latest - base):+.1f} points")

print("\nUses taken up beyond the first team")
for item, name, owner, team2, wk in c.execute("""
    WITH r AS (SELECT item_id, team, min(week_start) AS w FROM fact_library_run GROUP BY 1, 2),
    o AS (SELECT r.item_id, i.item_name, i.owner_team,
                 arg_min(r.team, r.w) FILTER (WHERE r.team <> i.owner_team) AS t2,
                 min(r.w) FILTER (WHERE r.team <> i.owner_team) AS w2
          FROM r JOIN dim_library_item i USING (item_id) GROUP BY 1, 2, 3)
    SELECT o.item_id, o.item_name, o.owner_team, o.t2, k.week_no FROM o JOIN wk k ON k.week_start = o.w2
    ORDER BY 1""").fetchall():
    print(f"  {item} {name} (made by {owner}): taken up by {team2} from Week {wk}")

print("\nRuns by other teams, per prompt taken up (round 8 column)")
for item, runs in c.execute("""
    SELECT r.item_id, sum(r.runs) FILTER (WHERE r.team <> i.owner_team) FROM fact_library_run r
    JOIN dim_library_item i USING (item_id) GROUP BY 1 HAVING count(DISTINCT r.team) >= 2 ORDER BY 1""").fetchall():
    print(f"  {item}: {runs:,}")
