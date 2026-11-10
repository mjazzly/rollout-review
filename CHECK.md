# The recorded check: Rollout review (DASH-02)

> **Change note.** The expected answers to questions 1 and 16 were reworded from calendar dates to week numbers (Week 24, Week 7) before the Power BI build began, so that they read the way every page labels weeks. No calendar date appears on any page. This was not done to make a match. The figures behind them are unchanged.

Eighteen questions, three per page (pages 0 to 5 in section 6 of `DASH-02-DESIGN.md`). `check.py` answers each one straight from `data/*.csv` with DuckDB and prints the question, the SQL and the answer. Each answer is then read off the matching Power BI visual and compared.

Answers are written the way the visual shows them, so a match is a plain comparison:

- Shares are percentages to one decimal place, for example 44.5%.
- A change in a share is in percentage points to one decimal place.
- Counts are whole numbers.
- The cost index is to two decimal places.
- Weeks are shown as their week label, Week 1 to Week 24, as every page labels them.

Definitions follow `measures.md`. Every page has at least one question on a planted storyline, and question 4 covers the Finance gap between check-in and source.

To reproduce the expected answers:

```bash
python3 check.py
```

| # | Page | Question | Expected answer | Matched |
|---:|---:|---|---|---|
| 1 | 0 | In the last week of the period, how many seats were active, out of how many assigned? | 505 of 1,167 seats active (Week 24) | Yes. Rollout review, header line: 1,167 seats assigned, 505 seats active in Week 24 |
| 2 | 0 | How many people moved up since the last count (month 5 to month 6), and how many seats arrived? | 98 moved up; 0 seats arrived | Yes. Rollout review, Moved up since the last count: 98; seats arrived 0 |
| 3 | 0 | What does the Refinement tile show for month 6, with its verdict and trend? (Technology storyline) | 9.5%, Not yet working (threshold 50%); trend Flat (month 4 was 8.7%) | Yes. Rollout review, Refinement tile: 9.5%, Not yet working, Threshold 50%, → Flat. Month 4's 8.7% is behind the trend; the page does not print it |
| 4 | 1 | In month 6, how many Finance people place themselves higher, level and lower than the sources do? | Higher 111, level 76, lower 13 | Yes. Where people sit, Source, Month 6, the gap: Finance 111 / 76 / 13 |
| 5 | 1 | In month 6, what is Legal's largest group by source placement, how many people are in it, and what is its lever? | Ticket held, 84 people. Lever: A first task done side by side with someone who already uses AI | Yes. Where people sit, Source, Month 6, largest group: Legal, Ticket held, 84; A first task done side by side with someone who already uses AI |
| 6 | 1 | How many Operations people moved up between month 3 and month 4, and how many Operations seats arrived? | 87 moved up; 0 seats arrived | Yes. Where people sit, Check-in, Month 4: movement Operations 87 up; 0 seats arrived (all teams) |
| 7 | 2 | What share of requests were matched to a tested prompt that already exists? | 49.5% (385 of 778 questions) | Yes. Foundation: 49.5%, 385 of 778 questions |
| 8 | 2 | Which use led the ranking in month 1, and which in month 6? | Month 1: Rules and allowed use, 52 questions; Month 6: Analysis, 23 questions | Pending: read from the next Foundation screenshot (bar totals) |
| 9 | 2 | Which team had the lowest usage baseline, and what was it? (Legal storyline) | Legal, 11.9% | Yes. Foundation, usage baseline: Legal 11.9%, the lowest |
| 10 | 3 | What share of training attendees ran the item they were shown within two weeks of the session? | 44.5% (174 of 391 attendees) | Yes. Execution, all teams: 44.5%, 174 of 391 attendees |
| 11 | 3 | What share of recurring questions were covered by a tested prompt? | 89.4% (127 of 142 repeat-flagged questions) | Yes. Execution, all teams: 89.4%, 127 of 142 recurring questions |
| 12 | 3 | How many repeat-flagged Summarising questions did Operations log in months 2 and 3, and in months 4 to 6? (Operations storyline) | 16 in months 2 and 3; 0 in months 4 to 6 | Yes. Execution, Operations: Summarising 8 and 8 in Months 2 and 3 (16); 0, 0, 0 in Months 4 to 6 |
| 13 | 4 | Which tested prompts pass on the smaller model? (Technology storyline) | 2 items: LIB-09, LIB-13 | Yes. Refinement: LIB-09 (11 of 11) and LIB-13 (12 of 12) in marine |
| 14 | 4 | What is the cost index for LIB-09 and LIB-13? | LIB-09 2.02; LIB-13 2.07 | Yes. Refinement, cost table: LIB-09 2.02; LIB-13 2.07 |
| 15 | 4 | Which prompts were retired or merged, and in which check-in month? | Month 5: LIB-12 retired; Month 5: LIB-14 merged into LIB-10 | Yes. Refinement, retired or merged: LIB-12 Retired in Month 5; LIB-14 Merged into LIB-10 in Month 5 |
| 16 | 5 | Which library item was the first taken up beyond its own team, by which team, and from which week? (Consulting storyline) | LIB-01 (Consulting), taken up by Technology from Week 7 | Yes. Scale, taken-up table: LIB-01, made by Consulting, taken up by Technology from Week 7 |
| 17 | 5 | What share of Consulting is in the air in month 6, against Consulting's baseline month? | 60.3% in month 6 against 47.0% in month 3, the baseline (+13.3 points) | Yes. Scale: Consulting · Month 3 47.0%; Month 6 60.3% (+13.3) |
| 18 | 5 | In month 6, how many people in each team said that without AI they would lose time every week? | Consulting 162; Technology 90; Finance 86; Operations 73; People 48; Legal 17 | Yes. Scale, impact: Consulting 162, Finance 86, Legal 17, Operations 73, People 48, Technology 90 |

**Match record:** 17 of 18 read so far (question 8 pending), against the Power BI build at commit c2c9709, screenshots of 10 Nov 2026. Awaiting Megat's confirmation.
