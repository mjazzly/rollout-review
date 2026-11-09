#!/usr/bin/env python3
"""The figures page 1 (Where people sit) should show at Month 6, read from the CSVs.

    python3 scripts/page1_figures.py

Uses check.py's views (wk, cw, tb). Movement is Month 5 to Month 6, by source placement,
for people seated by the Month 5 check-in week; seats arrived are counted apart.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import connect  # noqa: E402

c = connect()
M = 6
checkpoints = c.execute("SELECT checkpoint_id, checkpoint FROM dim_checkpoint ORDER BY 1").fetchall()
teams = [t for (t,) in c.execute("SELECT team FROM dim_team ORDER BY 1").fetchall()]


def counts(col: str) -> dict:
    rows = c.execute(f"""
        SELECT p.team, f.{col}, count(*) FROM fact_placement f JOIN dim_person p USING (person_id)
        WHERE f.checkin_month = {M} GROUP BY 1, 2""").fetchall()
    return {(t, k): n for t, k, n in rows}


for title, col in (("Source placement (the default)", "source_checkpoint_id"),
                   ("Check-in placement", "checkin_checkpoint_id")):
    n = counts(col)
    print(f"\nPeople at each checkpoint, Month {M}, {title}")
    print("| Checkpoint | " + " | ".join(teams) + " |\n|---|" + "---:|" * len(teams))
    for k, name in checkpoints:
        print(f"| {k} {name} | " + " | ".join(str(n.get((t, k), 0)) for t in teams) + " |")
    biggest = {}
    for t in teams:
        k = max((n.get((t, k), 0), -k) for k, _ in checkpoints)
        biggest[t] = (dict(checkpoints)[-k[1]], k[0], -k[1])
    print(f"Largest group: " + "; ".join(f"{t} {b[0]} {b[1]}" for t, b in biggest.items()))
    print(f"Largest bar on the page: {max(n.values())}")

print(f"\nThe gap, Month {M} (check-in against source)")
print("| Team | Higher | Level | Lower |\n|---|---:|---:|---:|")
for t, h, l, lo in c.execute(f"""
        SELECT p.team, count(*) FILTER (WHERE gap > 0), count(*) FILTER (WHERE gap = 0),
               count(*) FILTER (WHERE gap < 0)
        FROM fact_placement f JOIN dim_person p USING (person_id) WHERE checkin_month = {M}
        GROUP BY 1 ORDER BY 1""").fetchall():
    print(f"| {t} | {h} | {l} | {lo} |")

print(f"\nMovement, Month {M - 1} to Month {M} (source placement)")
print("| Team | Up | Held | Down | Seats arrived |\n|---|---:|---:|---:|---:|")
for row in c.execute(f"""
        WITH s AS (
          SELECT p.team, p.seat_assigned_week AS seat, a.source_checkpoint_id AS prev,
                 b.source_checkpoint_id AS cur
          FROM dim_person p
          LEFT JOIN fact_placement a ON a.person_id = p.person_id AND a.checkin_month = {M - 1}
          LEFT JOIN fact_placement b ON b.person_id = p.person_id AND b.checkin_month = {M})
        SELECT team,
          count(*) FILTER (WHERE seat <= (SELECT w FROM cw WHERE m = {M - 1}) AND cur > prev),
          count(*) FILTER (WHERE seat <= (SELECT w FROM cw WHERE m = {M - 1}) AND cur = prev),
          count(*) FILTER (WHERE seat <= (SELECT w FROM cw WHERE m = {M - 1}) AND cur < prev),
          count(*) FILTER (WHERE (seat IS NULL OR seat > (SELECT w FROM cw WHERE m = {M - 1}))
                             AND seat <= (SELECT w FROM cw WHERE m = {M}))
        FROM s GROUP BY 1 ORDER BY 1""").fetchall():
    print("| " + " | ".join(str(x) for x in row) + " |")

print("\nLevers (dim_checkpoint)")
for k, name, lever in c.execute("SELECT checkpoint_id, checkpoint, lever FROM dim_checkpoint ORDER BY 1").fetchall():
    print(f"{k} {name}: {lever}")
