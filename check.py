#!/usr/bin/env python3
"""DASH-02 Rollout review: the recorded check.

Answers 18 questions, three per page (pages 0 to 5 in section 6 of the design
note), straight from data/*.csv with DuckDB. Each answer is printed the way the
Power BI visual shows it, so a match is a plain comparison:

- shares as percentages to one decimal place, e.g. 48.4%
- changes in a share as percentage points to one decimal place, e.g. +34.8 points
- counts as whole numbers; the cost index to two decimal places
- weeks as their week label, Week 1 to Week 24, e.g. Week 7 (no calendar date
  appears on any page)

Definitions follow measures.md word for word. Run: python3 check.py
(add --md to print the CHECK.md table rows instead).
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

DATA = Path(__file__).resolve().parent / "data"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for f in sorted(DATA.glob("*.csv")):
        con.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_csv_auto('{f.as_posix()}', header=true)")
    # Helpers: week numbers, and each check-in month's check-in week and check-in date
    con.execute("""CREATE VIEW wk AS
        SELECT week_start, checkin_month, row_number() OVER (ORDER BY week_start) AS week_no FROM dim_week""")
    con.execute("""CREATE VIEW cw AS
        SELECT checkin_month AS m, max(week_start) AS w, max(week_start) + 6 AS d FROM dim_week GROUP BY 1""")
    # Each team's baseline month: the first check-in month whose eight-week window starts on or
    # after the week the team's seats arrive (window of month m: weeks 4m-7 to 4m)
    con.execute("""CREATE VIEW tb AS
        SELECT p.team, CAST(ceil((min(k.week_no) + 7) / 4.0) AS INTEGER) AS base_m
        FROM dim_person p JOIN wk k ON k.week_start = p.seat_assigned_week GROUP BY 1""")
    return con


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def verdict(now: float, threshold: float) -> str:
    """Working when the figure meets the threshold; no trend condition (measures.md)."""
    return "Working" if now >= threshold else "Not yet working"


def trend(now: float, before: float | None) -> str:
    """Against two check-in months earlier; flat within 1 point (shares are fractions here)."""
    if before is None:
        return "No comparison yet"
    diff = 100 * (now - before)
    return "Flat" if abs(diff) <= 1 else "Up" if diff > 0 else "Down"


Q = []  # (page, question, sql, format(rows) -> str)


def q(page: int, question: str, sql: str):
    def deco(fmt):
        Q.append((page, question, sql.strip(), fmt))
        return fmt
    return deco


# ---------------------------------------------------------------- Page 0
@q(0, "In the last week of the period, how many seats were active, out of how many assigned?", """
SELECT count(*) FILTER (WHERE u.days_active >= 2) AS active,
       count(*)                                    AS assigned,
       max(k.week_no)                              AS week_no
FROM dim_person p
JOIN fact_usage_week u ON u.person_id = p.person_id AND u.week_start = (SELECT max(week_start) FROM dim_week)
JOIN wk k ON k.week_start = u.week_start
WHERE p.seat_assigned_week <= u.week_start
""")
def _(r): return f"{r[0][0]:,} of {r[0][1]:,} seats active (Week {r[0][2]})"


@q(0, "How many people moved up since the last count (month 5 to month 6), and how many seats arrived?", """
WITH s AS (
  SELECT p.seat_assigned_week AS seat, a.source_checkpoint_id AS prev, b.source_checkpoint_id AS cur
  FROM dim_person p
  JOIN fact_placement a ON a.person_id = p.person_id AND a.checkin_month = 5
  JOIN fact_placement b ON b.person_id = p.person_id AND b.checkin_month = 6)
SELECT count(*) FILTER (WHERE seat <= (SELECT w FROM cw WHERE m = 5) AND cur > prev) AS moved_up,
       count(*) FILTER (WHERE (seat IS NULL OR seat > (SELECT w FROM cw WHERE m = 5))
                          AND seat <= (SELECT w FROM cw WHERE m = 6))              AS seats_arrived
FROM s
""")
def _(r): return f"{r[0][0]} moved up; {r[0][1]} seats arrived"


@q(0, "What does the Refinement tile show for month 6, with its verdict and trend? (Technology storyline)", """
WITH live AS (
  SELECT cw.m, i.item_id FROM cw
  JOIN dim_library_item i ON i.published_week <= cw.w AND (i.status_week IS NULL OR i.status_week > cw.w)),
latest AS (
  SELECT cw.m, r.item_id, r.cases_matched = r.cases_total AS passing,
         row_number() OVER (PARTITION BY cw.m, r.item_id ORDER BY r.run_date DESC, r.run_id DESC) AS rn
  FROM cw JOIN fact_test_run r ON r.model_tier = 'smaller' AND r.run_date <= cw.d)
SELECT live.m, avg(CASE WHEN latest.passing THEN 1 ELSE 0 END) AS share
FROM live LEFT JOIN latest ON latest.m = live.m AND latest.item_id = live.item_id AND latest.rn = 1
WHERE live.m IN (4, 6) GROUP BY 1 ORDER BY 1
""")
def _(r):
    before, now = r[0][1], r[1][1]
    return f"{pct(now)}, {verdict(now, 0.50)} (threshold 50%); trend {trend(now, before)} (month 4 was {pct(before)})"


# ---------------------------------------------------------------- Page 1
@q(1, "In month 6, how many Finance people place themselves higher, level and lower than the sources do?", """
SELECT count(*) FILTER (WHERE f.gap > 0) AS higher,
       count(*) FILTER (WHERE f.gap = 0) AS level,
       count(*) FILTER (WHERE f.gap < 0) AS lower
FROM fact_placement f JOIN dim_person p USING (person_id)
WHERE p.team = 'Finance' AND f.checkin_month = 6
""")
def _(r): return f"Higher {r[0][0]}, level {r[0][1]}, lower {r[0][2]}"


@q(1, "In month 6, what is Legal's largest group by source placement, how many people are in it, and what is its lever?", """
SELECT c.checkpoint, count(*) AS people, c.lever
FROM fact_placement f JOIN dim_person p USING (person_id)
JOIN dim_checkpoint c ON c.checkpoint_id = f.source_checkpoint_id
WHERE p.team = 'Legal' AND f.checkin_month = 6
GROUP BY c.checkpoint_id, c.checkpoint, c.lever
ORDER BY people DESC, c.checkpoint_id LIMIT 1
""")
def _(r): return f"{r[0][0]}, {r[0][1]} people. Lever: {r[0][2]}"


@q(1, "How many Operations people moved up between month 3 and month 4, and how many Operations seats arrived?", """
WITH s AS (
  SELECT p.seat_assigned_week AS seat, a.source_checkpoint_id AS prev, b.source_checkpoint_id AS cur
  FROM dim_person p
  JOIN fact_placement a ON a.person_id = p.person_id AND a.checkin_month = 3
  JOIN fact_placement b ON b.person_id = p.person_id AND b.checkin_month = 4
  WHERE p.team = 'Operations')
SELECT count(*) FILTER (WHERE seat <= (SELECT w FROM cw WHERE m = 3) AND cur > prev) AS moved_up,
       count(*) FILTER (WHERE (seat IS NULL OR seat > (SELECT w FROM cw WHERE m = 3))
                          AND seat <= (SELECT w FROM cw WHERE m = 4))              AS seats_arrived
FROM s
""")
def _(r): return f"{r[0][0]} moved up; {r[0][1]} seats arrived"


# ---------------------------------------------------------------- Page 2
@q(2, "What share of requests were matched to a tested prompt that already exists?", """
SELECT avg(CASE WHEN action_taken = 'pointed to library' THEN 1 ELSE 0 END) AS share,
       count(*) FILTER (WHERE action_taken = 'pointed to library') AS matched, count(*) AS questions
FROM fact_question
""")
def _(r): return f"{pct(r[0][0])} ({r[0][1]} of {r[0][2]} questions)"


@q(2, "Which use led the ranking in month 1, and which in month 6?", """
WITH c AS (
  SELECT w.checkin_month AS m, q.category, count(*) AS questions,
         row_number() OVER (PARTITION BY w.checkin_month ORDER BY count(*) DESC, q.category) AS rk
  FROM fact_question q JOIN dim_week w ON w.week_start = date_trunc('week', q.question_date)
  WHERE w.checkin_month IN (1, 6) GROUP BY 1, 2)
SELECT m, category, questions FROM c WHERE rk = 1 ORDER BY m
""")
def _(r): return "; ".join(f"Month {m}: {c}, {n} questions" for m, c, n in r)


@q(2, "Which team had the lowest usage baseline, and what was it? (Legal storyline)", """
WITH first_seat AS (SELECT team, min(seat_assigned_week) AS s0 FROM dim_person GROUP BY 1),
weeks AS (
  SELECT f.team, w.week_start FROM first_seat f
  JOIN dim_week w ON w.week_start BETWEEN f.s0 AND f.s0 + 21),
share AS (
  SELECT k.team, k.week_start,
         count(*) FILTER (WHERE u.days_active >= 2) * 1.0
           / count(*) FILTER (WHERE p.seat_assigned_week <= k.week_start) AS s
  FROM weeks k JOIN dim_person p ON p.team = k.team
  LEFT JOIN fact_usage_week u ON u.person_id = p.person_id AND u.week_start = k.week_start
  GROUP BY 1, 2)
SELECT team, avg(s) AS baseline FROM share GROUP BY 1 ORDER BY baseline, team LIMIT 1
""")
def _(r): return f"{r[0][0]}, {pct(r[0][1])}"


# ---------------------------------------------------------------- Page 3
@q(3, "What share of training attendees ran the item they were shown within two weeks of the session?", """
WITH att AS (
  SELECT t.session_id, t.person_id,
         bool_or(r.week_start IS NOT NULL) AS ran
  FROM fact_training t
  LEFT JOIN fact_library_run_person r
    ON r.person_id = t.person_id AND r.item_id = t.item_id_shown
   AND r.week_start BETWEEN t.session_week AND t.session_week + 7
  GROUP BY 1, 2)
SELECT avg(CASE WHEN ran THEN 1 ELSE 0 END), count(*) FILTER (WHERE ran), count(*) FROM att
""")
def _(r): return f"{pct(r[0][0])} ({r[0][1]} of {r[0][2]} attendees)"


@q(3, "What share of recurring questions were covered by a tested prompt?", """
WITH rq AS (
  SELECT q.question_id,
         EXISTS (SELECT 1 FROM dim_library_item i
                 WHERE i.category = q.category
                   AND i.published_week <= date_trunc('week', q.question_date)
                   AND (i.status_week IS NULL OR i.status_week > date_trunc('week', q.question_date))) AS covered
  FROM fact_question q WHERE q.repeat_flag)
SELECT avg(CASE WHEN covered THEN 1 ELSE 0 END), count(*) FILTER (WHERE covered), count(*) FROM rq
""")
def _(r): return f"{pct(r[0][0])} ({r[0][1]} of {r[0][2]} repeat-flagged questions)"


@q(3, "How many repeat-flagged Summarising questions did Operations log in months 2 and 3, and in months 4 to 6? (Operations storyline)", """
SELECT count(*) FILTER (WHERE w.checkin_month <= 3) AS before_item,
       count(*) FILTER (WHERE w.checkin_month >= 4) AS after_item
FROM fact_question q JOIN dim_week w ON w.week_start = date_trunc('week', q.question_date)
WHERE q.team = 'Operations' AND q.category = 'Summarising' AND q.repeat_flag
""")
def _(r): return f"{r[0][0]} in months 2 and 3; {r[0][1]} in months 4 to 6"


# ---------------------------------------------------------------- Page 4
@q(4, "Which tested prompts pass on the smaller model? (Technology storyline)", """
WITH latest AS (
  SELECT item_id, cases_matched = cases_total AS passing,
         row_number() OVER (PARTITION BY item_id ORDER BY run_date DESC, run_id DESC) AS rn
  FROM fact_test_run WHERE model_tier = 'smaller')
SELECT string_agg(item_id, ', ' ORDER BY item_id), count(*) FROM latest WHERE rn = 1 AND passing
""")
def _(r): return f"{r[0][1]} items: {r[0][0]}"


@q(4, "What is the cost index for LIB-09 and LIB-13?", """
SELECT item_id,
       median(tokens_in + tokens_out) FILTER (WHERE model_tier = 'standard')
     / median(tokens_in + tokens_out) FILTER (WHERE model_tier = 'smaller') AS cost_index
FROM fact_test_run WHERE item_id IN ('LIB-09', 'LIB-13') GROUP BY 1 ORDER BY 1
""")
def _(r): return "; ".join(f"{i} {v:.2f}" for i, v in r)


@q(4, "Which prompts were retired or merged, and in which check-in month?", """
SELECT w.checkin_month, i.item_id, i.status, i.merged_into_item_id
FROM dim_library_item i JOIN dim_week w ON w.week_start = i.status_week
WHERE i.status IN ('retired', 'merged') ORDER BY 1, 2
""")
def _(r):
    return "; ".join(f"Month {m}: {i} {s}" + (f" into {into}" if into else "") for m, i, s, into in r)


# ---------------------------------------------------------------- Page 5
@q(5, "Which library item was the first taken up beyond its own team, by which team, and from which week? (Consulting storyline)", """
SELECT r.item_id, i.owner_team, r.team, min(k.week_no) AS first_week_no
FROM fact_library_run r JOIN dim_library_item i USING (item_id)
JOIN wk k ON k.week_start = r.week_start
WHERE r.team <> i.owner_team
GROUP BY 1, 2, 3 ORDER BY first_week_no, r.item_id LIMIT 1
""")
def _(r): return f"{r[0][0]} ({r[0][1]}), taken up by {r[0][2]} from Week {r[0][3]}"


@q(5, "What share of Consulting is in the air in month 6, against Consulting's baseline month?", """
SELECT f.checkin_month, avg(CASE WHEN f.source_checkpoint_id >= 7 THEN 1 ELSE 0 END) AS share
FROM fact_placement f JOIN dim_person p USING (person_id) JOIN tb ON tb.team = p.team
WHERE p.team = 'Consulting' AND (f.checkin_month = tb.base_m OR f.checkin_month = 6)
GROUP BY 1 ORDER BY 1
""")
def _(r):
    (bm, base), (_, now) = r[0], r[1]
    return f"{pct(now)} in month 6 against {pct(base)} in month {bm}, the baseline (+{100 * (now - base):.1f} points)"


@q(5, "In month 6, how many people in each team said that without AI they would lose time every week?", """
SELECT p.team, count(*) FILTER (WHERE c.q5_if_gone = 'I would lose time every week') AS people
FROM fact_checkin c JOIN dim_person p USING (person_id)
WHERE c.checkin_month = 6 GROUP BY 1 ORDER BY people DESC, p.team
""")
def _(r): return "; ".join(f"{t} {n}" for t, n in r)


def main() -> None:
    con = connect()
    md = "--md" in sys.argv
    for n, (page, question, sql, fmt) in enumerate(Q, 1):
        answer = fmt(con.execute(sql).fetchall())
        if md:
            print(f"| {n} | {page} | {question} | {answer} | |")
        else:
            print(f"Q{n:02d} · Page {page}\n{question}\n\n{sql}\n\n=> {answer}\n{'-' * 78}")


if __name__ == "__main__":
    main()
