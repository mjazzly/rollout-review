# Rollout review

The data side of DASH-02, **Rollout review**, the second Power BI dashboard on the Dashboards page of [mjazzly.github.io](https://mjazzly.github.io/). It puts two frames from the Frames page into numbers:

- **FRAME-04, How to tell a rollout is working.** Four stages (Foundation, Execution, Refinement, Scale), with one question each and every measure read from a named source.
- **FRAME-01, The adoption flight.** Three stages and nine checkpoints. People place themselves in a check-in, the sources place them too, and the gap between the two is a finding.

It is written for the enablement lead of an AI adoption programme, who decides each week where enablement effort goes. The front page answers the programme sponsor's one question: is the rollout working?

## The data is synthetic

Every row in `data/` is made up. `generate.py` writes all of them from a fixed seed (42), so every rerun gives the same files byte for byte. The organisation is neutral: six generic teams, three regions, 1,200 people with no names, and "the assistant platform". Nothing is measured in currency.

The tables stand in for live systems: an office hours log, a platform admin export, a library run log, a test harness, a check-in form, a training register and an HR roster. [DICTIONARY.md](DICTIONARY.md) names the system behind each table. Swapping in a live backend means replacing a CSV with an export of the same columns.

## Planted storylines

Synthetic data with nothing in it gives pages with nothing to say, so the generator plants five storylines. They are planted, not found:

1. **Legal.** Seats arrive first, in week 1, but most people stay at Ticket held across all six counts. The problem is access and the first week.
2. **Finance.** The check-in places many people at Takeoff, while the sources place them at Waiting to board, active only in reminder weeks. The gap is the finding, and the problem is habit.
3. **Operations.** Repeat Summarising questions stop once a library item for that use is published in week 12, and people move up at the next count.
4. **Technology.** Two items pass on the smaller model at half the tokens. One item is retired and one merged in month 5.
5. **Consulting.** Broad, steady adoption with the highest library share, and the first item taken up by a second team. This is the benchmark team.

People sits in between, with no planted story.

One more pattern is planted across all teams: questions about Rules and allowed use fall month on month, from 52 in month 1 to 16 in month 6, so the ranked uses on the Foundation page change over the period.

## Rerun it

You need Python 3 with pandas, numpy and duckdb:

```bash
python3 -m pip install pandas numpy duckdb
```

Rewrite every table in `data/`:

```bash
python3 generate.py
```

Answer the 18 check questions from the CSVs:

```bash
python3 check.py
```

## Adopting this on live data

Every measure finds the latest check-in for itself: `Check-in month` is `MAX ( dim_month[checkin_month] )`, so with live exports a seventh month becomes the latest with no change to a measure. Three places name the period by hand and would change:

| Typed in | Where | What it would change to |
|---|---|---|
| The Month dropdown opens on `'Month 6'` | `scripts/page1_pbir.py` (the dropdown's saved filter) | The latest month: a calculated column on `dim_month` marking it (for example "Latest"), with the dropdown opening on that |
| `baseline_month` keeps a baseline only if it is Month 6 or earlier (`firstMonth <= 6`) | `measures.dax`, calculated column on `dim_team` | The cap read from the data: `firstMonth <= MAX ( dim_month[checkin_month] )` |
| Panel wording names Month 6 and Week 24: "Stage by team, Month 6", "Month 5 to Month 6", "Month 1 and Month 6" and that chart's Month 6 filter, "Month 6: if AI disappeared tomorrow?", the "Month 6" legend on Scale, "Week 1 to Week 24" in the footers, and Notes | The page scripts in `scripts/` | Measures that write the words from the latest month and week, and the Month 6 filter moved onto the latest-month column |

## What is here

| File | What it holds |
|---|---|
| `generate.py` | Seeded generator. Writes `data/*.csv`, including the derived `fact_placement` |
| `check.py` | Answers the check's 18 questions from the CSVs with DuckDB |
| `data/` | The fifteen CSVs |
| [DICTIONARY.md](DICTIONARY.md) | Every table and column, its grain and its live source |
| [measures.md](measures.md) | Every measure and placement rule, worded for the DAX descriptions |
| [CHECK.md](CHECK.md) | The questions, the expected answers and the match record |
| [DASH-02-DESIGN.md](DASH-02-DESIGN.md) | The design note |
| [PUBLISH.md](PUBLISH.md) | The Publish to web link |
| `get.cmd`, `send.cmd` | The PC's two scripts: bring the project up to date and open it; send a save from Desktop |
