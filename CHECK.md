# The recorded check: Rollout review (DASH-02)

Eighteen questions, three per page (pages 0 to 5 in section 6 of `DASH-02-DESIGN.md`). `check.py` answers each one straight from `data/*.csv` with DuckDB and prints the question, the SQL and the answer. Each answer is then read off the matching Power BI visual and compared.

Answers are written the way the visual shows them, so a match is a plain comparison:

- Shares are percentages to one decimal place, for example 44.5%.
- A change in a share is in percentage points to one decimal place.
- Counts are whole numbers.
- The cost index is to two decimal places.
- Weeks are shown as their week_start date.

Definitions follow `measures.md`. Every page has at least one question on a planted storyline, and question 4 covers the Finance gap between check-in and source.

To reproduce the expected answers:

```bash
python3 check.py
```

| # | Page | Question | Expected answer | Matched |
|---:|---:|---|---|---|
| 1 | 0 | In the last week of the period, how many seats were active, out of how many assigned? | 505 of 1,167 seats active (week of 2026-10-26) | |
| 2 | 0 | How many people moved up since the last count (month 5 to month 6), and how many seats arrived? | 98 moved up; 0 seats arrived | |
| 3 | 0 | What does the Refinement tile show for month 6, and what is its verdict? (Technology storyline) | 9.5%, Not yet working (threshold 50%; month 4 was 8.7%) | |
| 4 | 1 | In month 6, how many Finance people place themselves higher, level and lower than the sources do? | Higher 111, level 76, lower 13 | |
| 5 | 1 | In month 6, what is Legal's largest group by source placement, how many people are in it, and what is its lever? | Ticket held, 84 people. Lever: A first task done side by side with someone who already uses AI | |
| 6 | 1 | How many Operations people moved up between month 3 and month 4, and how many Operations seats arrived? | 87 moved up; 0 seats arrived | |
| 7 | 2 | Which use comes up most often in the question log, and how many questions is that? | Rules and allowed use, 242 questions | |
| 8 | 2 | Which use led the ranking in month 1, and which in month 6? | Month 1: Rules and allowed use, 52 questions; Month 6: Analysis, 23 questions | |
| 9 | 2 | Which team had the lowest usage baseline, and what was it? (Legal storyline) | Legal, 11.9% | |
| 10 | 3 | What share of training attendees ran the item they were shown within two weeks of the session? | 44.5% (174 of 391 attendees) | |
| 11 | 3 | What share of recurring questions were covered by a tested prompt? | 89.4% (127 of 142 repeat-flagged questions) | |
| 12 | 3 | How many repeat-flagged Summarising questions did Operations log in months 2 and 3, and in months 4 to 6? (Operations storyline) | 16 in months 2 and 3; 0 in months 4 to 6 | |
| 13 | 4 | Which tested prompts pass on the smaller model? (Technology storyline) | 2 items: LIB-09, LIB-13 | |
| 14 | 4 | What is the cost index for LIB-09 and LIB-13? | LIB-09 2.02; LIB-13 2.07 | |
| 15 | 4 | Which prompts were retired or merged, and in which check-in month? | Month 5: LIB-12 retired; Month 5: LIB-14 merged into LIB-10 | |
| 16 | 5 | Which library item was the first taken up beyond its own team, by which team, and from which week? (Consulting storyline) | LIB-01 (Consulting), taken up by Technology from the week of 2026-06-29 | |
| 17 | 5 | What share of Consulting is in the air in month 6, against Consulting's baseline month? | 60.3% in month 6 against 47.0% in month 3, the baseline (+13.3 points) | |
| 18 | 5 | In month 6, how many people in each team said that without AI they would lose time every week? | Consulting 162; Technology 90; Finance 86; Operations 73; People 48; Legal 17 | |

**Match record:** __ of 18, checked against the Power BI build on ____.
