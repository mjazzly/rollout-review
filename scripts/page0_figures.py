#!/usr/bin/env python3
"""The stage split figures page 0 should show, read from the CSVs (not from the model).

    python3 scripts/page0_figures.py

Each team's baseline month is the check-in month of its first seat week, as
dim_team[baseline_month]: ROUNDUP((week_no + 7) / 4). Stage is by source placement.
"""
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent.parent / "data"
c = duckdb.connect()
for t in ("dim_person", "dim_week", "fact_placement", "dim_checkpoint"):
    c.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('{DATA / (t + '.csv')}')")
c.execute("CREATE VIEW wk AS SELECT *, row_number() OVER (ORDER BY week_start) AS week_no FROM dim_week")
c.execute("""CREATE VIEW base AS SELECT p.team, ceil((min(w.week_no) + 7) / 4.0)::int AS bm
             FROM dim_person p JOIN wk w ON w.week_start = p.seat_assigned_week GROUP BY 1""")
SPLIT = """
WITH x AS (SELECT p.team, f.checkin_month AS m, k.stage
           FROM fact_placement f JOIN dim_person p USING (person_id)
           JOIN dim_checkpoint k ON k.checkpoint_id = f.source_checkpoint_id)
SELECT team, any_value(m) AS month,
       round(100 * avg((stage = 'On the ground')::int), 1),
       round(100 * avg((stage = 'At the gate')::int), 1),
       round(100 * avg((stage = 'In the air')::int), 1), count(*)
FROM x JOIN base USING (team) WHERE {cond} GROUP BY team ORDER BY team"""

for title, cond in (("At each team's baseline month", "m = bm"), ("Latest count, Month 6", "m = 6")):
    print(f"\n{title}\n| Team | Month | On the ground | At the gate | In the air | People |\n|---|---:|---:|---:|---:|---:|")
    for team, m, g, a, air, n in c.execute(SPLIT.format(cond=cond)).fetchall():
        print(f"| {team} | {m} | {g}% | {a}% | {air}% | {n} |")
