# Build steps: Rollout review in Power BI Desktop

The on-screen steps for `PBI-BRIEF.md` sections 2 to 6, on the PC over Remote Desktop. One action per step. When a step says "send a screenshot", stop there and wait for the reply before going on.

This first part covers the data load and the model that pages 0 to 5 all read (brief sections 2 and 3). It ends at the model view screenshot (step 31). Section D then saves it as a Power BI project; the measures (`measures.dax`) and the page steps follow.

From page 0 on, pages are not built by hand. Each page is written from the Mac by its script (`scripts/pageN_pbir.py`), and the steps on the PC are the same every time: close Desktop, pull, open, screenshot, approve (section F onwards; brief section 7).

## What the model adds to the brief

Four things the brief's section 3 table does not list. Each one is there so a measure or slicer can work:

| Addition | Why |
|---|---|
| `dim_month` (checkin_month 1 to 6, with each month's check-in week and check-in date), related to `dim_week`, `fact_checkin` and `fact_placement` | One month slicer for every page (brief section 3 allows it). The check-in week and date are what "the check-in month" means in measures.md |
| `fact_question[question_week]` (the Monday of `question_date`), related to `dim_week` | So the month slicer on page 2 reaches the question log. check.py reads a question's month the same way |
| `dim_threshold` (from `data/dim_threshold.csv`) and `placement_toggle` (Check-in or Source) | Thresholds printed from data (brief section 4); the page 1 toggle |
| Two relationships from the brief left **inactive**: `dim_team` to `fact_question[team]`, and `dim_library_item` to `fact_question[linked_item_id]` | Power BI allows only one active filter path between two tables. Team already reaches the question log through `dim_person` (every question's team equals the asker's team; checked on the Mac), and category reaches it straight from `dim_category`. Both stay in the model as dashed lines so the model matches section 3 |

One type note: `reminder_week` ends in `_week` but is True/False, not a date (DICTIONARY.md), so it loads as True/False.

---

## A. Before you start

1. In Git Bash on the PC, bring the repo up to date: `cd /c/repos/rollout-review && git pull` (if the folder is not there yet: `git clone https://github.com/mjazzly/rollout-review.git /c/repos/rollout-review`).
2. Open Power BI Desktop and choose **Blank report**.
3. **File**, **Options and settings**, **Options**.
4. Under **CURRENT FILE**, **Data Load**: untick **Auto date/time**.
5. On the same page, under **Relationships**: untick **Autodetect new relationships after data is loaded** (and **Import relationships from data sources on first load** if it is ticked).
6. Click **OK**.

## B. Data load (Power Query)

7. **Home**, **Transform data**. The Power Query Editor opens.
8. **Home**, **Manage Parameters**, **New Parameter**. Name `DataFolder`, Type **Text**, Suggested Values **Any value**, Current Value `C:\repos\rollout-review\data`. Click **OK**.

**The query routine (steps 9 to 12).** Every query below is made the same way:

9. **Home**, **New Source**, **Blank Query**.
10. **Home**, **Advanced Editor**.
11. Select everything in the editor, paste the query's code from the list below, and click **Done**. The preview shows the table with no Error cells.
12. In **Query Settings** on the right, set **Name** to the query's name and press Enter.

Run steps 9 to 12 for each query, in this order. `LoadCsv` first, because every table query calls it.

### LoadCsv (a function: reads one CSV from DataFolder and turns empty cells into null)

```
(name as text) as table =>
let
    Source = Csv.Document(
        File.Contents(DataFolder & "\" & name & ".csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Nulls = Table.ReplaceValue(Promoted, "", null, Replacer.ReplaceValue, Table.ColumnNames(Promoted))
in
    Nulls
```

### dim_person

```
let
    Source = LoadCsv("dim_person"),
    Typed = Table.TransformColumnTypes(Source, {
        {"person_id", type text}, {"team", type text}, {"level", type text}, {"region", type text},
        {"start_date", type date}, {"seat_assigned_week", type date}
    }, "en-US")
in
    Typed
```

### dim_team

```
let
    Source = LoadCsv("dim_team"),
    Typed = Table.TransformColumnTypes(Source, {{"team", type text}, {"headcount", Int64.Type}}, "en-US")
in
    Typed
```

### dim_week (adds week_no 1 to 24 and week_label "Week 1" to "Week 24")

```
let
    Source = LoadCsv("dim_week"),
    Typed = Table.TransformColumnTypes(Source, {
        {"week_start", type date}, {"month", type text}, {"checkin_month", Int64.Type}, {"reminder_week", type logical}
    }, "en-US"),
    Sorted = Table.Sort(Typed, {{"week_start", Order.Ascending}}),
    WeekNo = Table.AddIndexColumn(Sorted, "week_no", 1, 1, Int64.Type),
    WeekLabel = Table.AddColumn(WeekNo, "week_label", each "Week " & Text.From([week_no]), type text)
in
    WeekLabel
```

### dim_month (built from dim_week: one row per check-in month)

```
let
    Source = dim_week,
    Grouped = Table.Group(Source, {"checkin_month"}, {{"checkin_week", each List.Max([week_start]), type date}}),
    CheckinDate = Table.AddColumn(Grouped, "checkin_date", each Date.AddDays([checkin_week], 6), type date),
    MonthLabel = Table.AddColumn(CheckinDate, "month_label", each "Month " & Text.From([checkin_month]), type text),
    Sorted = Table.Sort(MonthLabel, {{"checkin_month", Order.Ascending}})
in
    Sorted
```

### dim_checkpoint (adds stage_order 1 to 3, so the stages sort On the ground, At the gate, In the air)

```
let
    Source = LoadCsv("dim_checkpoint"),
    Typed = Table.TransformColumnTypes(Source, {
        {"checkpoint_id", Int64.Type}, {"checkpoint", type text}, {"stage", type text},
        {"how_you_tell", type text}, {"lever", type text}
    }, "en-US"),
    StageOrder = Table.AddColumn(Typed, "stage_order",
        each if [checkpoint_id] <= 3 then 1 else if [checkpoint_id] <= 6 then 2 else 3, Int64.Type)
in
    StageOrder
```

### dim_checkpoint_source (a reference to dim_checkpoint)

```
let
    Source = dim_checkpoint
in
    Source
```

### dim_library_item

```
let
    Source = LoadCsv("dim_library_item"),
    Typed = Table.TransformColumnTypes(Source, {
        {"item_id", type text}, {"item_name", type text}, {"category", type text},
        {"owner_person_id", type text}, {"owner_team", type text}, {"version", Int64.Type},
        {"limits", type text}, {"answer_key_first", type logical}, {"status", type text},
        {"merged_into_item_id", type text}, {"published_week", type date}, {"status_week", type date}
    }, "en-US")
in
    Typed
```

### dim_category

```
let
    Source = LoadCsv("dim_category"),
    Typed = Table.TransformColumnTypes(Source, {{"category", type text}}, "en-US")
in
    Typed
```

### dim_threshold

```
let
    Source = LoadCsv("dim_threshold"),
    Typed = Table.TransformColumnTypes(Source, {{"stage", type text}, {"threshold", type number}}, "en-US")
in
    Typed
```

### fact_question (adds question_week, the Monday of question_date)

```
let
    Source = LoadCsv("fact_question"),
    Typed = Table.TransformColumnTypes(Source, {
        {"question_id", type text}, {"question_date", type date}, {"person_id", type text},
        {"team", type text}, {"category", type text}, {"difficulty", Int64.Type},
        {"action_taken", type text}, {"linked_item_id", type text},
        {"answered_by_person_id", type text}, {"repeat_flag", type logical}
    }, "en-US"),
    QuestionWeek = Table.AddColumn(Typed, "question_week", each Date.StartOfWeek([question_date], Day.Monday), type date)
in
    QuestionWeek
```

### fact_usage_week

```
let
    Source = LoadCsv("fact_usage_week"),
    Typed = Table.TransformColumnTypes(Source, {
        {"person_id", type text}, {"week_start", type date}, {"days_active", Int64.Type},
        {"sessions", Int64.Type}, {"runs_total", Int64.Type}, {"runs_via_library", Int64.Type}
    }, "en-US")
in
    Typed
```

### fact_library_run

```
let
    Source = LoadCsv("fact_library_run"),
    Typed = Table.TransformColumnTypes(Source, {
        {"item_id", type text}, {"team", type text}, {"week_start", type date},
        {"runs", Int64.Type}, {"distinct_users", Int64.Type}
    }, "en-US")
in
    Typed
```

### fact_library_run_person

```
let
    Source = LoadCsv("fact_library_run_person"),
    Typed = Table.TransformColumnTypes(Source, {
        {"item_id", type text}, {"person_id", type text}, {"week_start", type date}, {"runs", Int64.Type}
    }, "en-US")
in
    Typed
```

### fact_test_run

```
let
    Source = LoadCsv("fact_test_run"),
    Typed = Table.TransformColumnTypes(Source, {
        {"run_id", type text}, {"item_id", type text}, {"version", Int64.Type}, {"run_date", type date},
        {"model_tier", type text}, {"cases_total", Int64.Type}, {"cases_matched", Int64.Type},
        {"tokens_in", Int64.Type}, {"tokens_out", Int64.Type}
    }, "en-US")
in
    Typed
```

### fact_checkin

```
let
    Source = LoadCsv("fact_checkin"),
    Typed = Table.TransformColumnTypes(Source, {
        {"person_id", type text}, {"checkin_month", Int64.Type}, {"q1_access", type text},
        {"q2_last_use", type text}, {"q3_trigger", type text}, {"q4_used_on", type text},
        {"q5_if_gone", type text}, {"checkpoint_id", Int64.Type}
    }, "en-US")
in
    Typed
```

### fact_training

```
let
    Source = LoadCsv("fact_training"),
    Typed = Table.TransformColumnTypes(Source, {
        {"session_id", type text}, {"person_id", type text}, {"team", type text},
        {"session_week", type date}, {"item_id_shown", type text}
    }, "en-US")
in
    Typed
```

### fact_placement

```
let
    Source = LoadCsv("fact_placement"),
    Typed = Table.TransformColumnTypes(Source, {
        {"person_id", type text}, {"checkin_month", Int64.Type}, {"checkin_checkpoint_id", Int64.Type},
        {"source_checkpoint_id", Int64.Type}, {"gap", Int64.Type}
    }, "en-US")
in
    Typed
```

When all eighteen are made (LoadCsv and seventeen tables), the Queries pane lists `DataFolder`, `LoadCsv` and the seventeen tables.

13. **Home**, **Close & Apply**. The data loads.
14. Open **Table view** (left rail). Click each table and check the row count at the bottom left against this list:

| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| dim_person | 1,200 | | fact_question | 778 |
| dim_team | 6 | | fact_usage_week | 24,419 |
| dim_week | 24 | | fact_library_run | 408 |
| dim_month | 6 | | fact_library_run_person | 7,319 |
| dim_checkpoint | 9 | | fact_test_run | 89 |
| dim_checkpoint_source | 9 | | fact_checkin | 7,200 |
| dim_library_item | 23 | | fact_training | 391 |
| dim_category | 7 | | fact_placement | 7,200 |
| dim_threshold | 4 | | | |

## C. Model

### Two tables made in Power BI

15. **Home**, **Enter data**. Leave the one empty column as it is, set **Name** to `_Measures`, and click **Load**. (Its column is hidden once the first measure is in, and the table then shows as a measure table.)
16. **Modeling**, **New table**. Paste this into the formula bar and press Enter:

```
placement_toggle =
DATATABLE ( "placement", STRING, { { "Check-in" }, { "Source" } } )
```

### Sort orders

In **Table view**, select the table, click the column header, then **Column tools**, **Sort by column**, and choose the sort column. One step each:

17. `dim_week[week_label]` sorted by `week_no`.
18. `dim_month[month_label]` sorted by `checkin_month`.
19. `dim_checkpoint[checkpoint]` sorted by `checkpoint_id`.
20. `dim_checkpoint[stage]` sorted by `stage_order`.
21. `dim_checkpoint_source[checkpoint]` sorted by `checkpoint_id`.
22. `dim_checkpoint_source[stage]` sorted by `stage_order`.

### Relationships

23. Open **Model view** (left rail).
24. **Home**, **Manage relationships**.

**The relationship routine (steps 25 to 27).** Every relationship below is made the same way:

25. Click **New relationship** (in recent versions, **+ New relationship**).
26. First table and column: the **From** in the list (the dimension, the one side). Second table and column: the **To** (the fact, the many side). Check that Power BI shows **Cardinality: One to many (1:\*)** and **Cross filter direction: Single**. Leave **Make this relationship active** ticked, except where the list says **inactive**: untick it for those two.
27. Click **Save** (or **OK**).

Run steps 25 to 27 for each row, in this order (R9 and R21 come after the paths they would duplicate, so Power BI accepts them as inactive):

| # | From (one) | To (many) | Active |
|---:|---|---|---|
| R1 | dim_person[person_id] | fact_usage_week[person_id] | yes |
| R2 | dim_person[person_id] | fact_checkin[person_id] | yes |
| R3 | dim_person[person_id] | fact_question[person_id] | yes |
| R4 | dim_person[person_id] | fact_library_run_person[person_id] | yes |
| R5 | dim_person[person_id] | fact_training[person_id] | yes |
| R6 | dim_person[person_id] | fact_placement[person_id] | yes |
| R7 | dim_team[team] | dim_person[team] | yes |
| R8 | dim_team[team] | fact_library_run[team] | yes |
| R9 | dim_team[team] | fact_question[team] | **inactive** |
| R10 | dim_week[week_start] | fact_usage_week[week_start] | yes |
| R11 | dim_week[week_start] | fact_library_run[week_start] | yes |
| R12 | dim_week[week_start] | fact_library_run_person[week_start] | yes |
| R13 | dim_week[week_start] | fact_training[session_week] | yes |
| R14 | dim_week[week_start] | fact_question[question_week] | yes |
| R15 | dim_checkpoint[checkpoint_id] | fact_checkin[checkpoint_id] | yes |
| R16 | dim_checkpoint[checkpoint_id] | fact_placement[checkin_checkpoint_id] | yes |
| R17 | dim_checkpoint_source[checkpoint_id] | fact_placement[source_checkpoint_id] | yes |
| R18 | dim_library_item[item_id] | fact_library_run[item_id] | yes |
| R19 | dim_library_item[item_id] | fact_library_run_person[item_id] | yes |
| R20 | dim_library_item[item_id] | fact_test_run[item_id] | yes |
| R21 | dim_library_item[item_id] | fact_question[linked_item_id] | **inactive** |
| R22 | dim_library_item[item_id] | fact_training[item_id_shown] | yes |
| R23 | dim_category[category] | fact_question[category] | yes |
| R24 | dim_category[category] | dim_library_item[category] | yes |
| R25 | dim_month[checkin_month] | dim_week[checkin_month] | yes |
| R26 | dim_month[checkin_month] | fact_checkin[checkin_month] | yes |
| R27 | dim_month[checkin_month] | fact_placement[checkin_month] | yes |

If Power BI refuses any row other than R9 and R21 as ambiguous, stop and send a screenshot of the message.

28. Close **Manage relationships**. The list there should show 27 relationships, 25 active and 2 inactive.

`dim_threshold`, `placement_toggle` and `_Measures` have no relationships; they sit apart in the model view on purpose.

### Save and check

29. **File**, **Save as**: `C:\repos\rollout-review\rollout-review.pbix`.
30. In **Model view**, right-click the canvas background and choose **Fit to screen** (or use the zoom slider at the bottom right) so all nineteen tables show, dragging any off-screen table into view.
31. Send two screenshots: the **model view** with every table and line visible, and the **Manage relationships** list (scroll it and send a second if it does not fit). Stop here.

Model checked on the Mac, 9 Nov 2026: 27 relationships, 25 active, R9 and R21 inactive, all many to one and single direction; nineteen tables. Then the build switched from a .pbix to a Power BI project (PBI-BRIEF.md section 1), so the measures go into the model's text files from the Mac.

---

## D. Save as a Power BI project

The .pbix from step 29 becomes a project in `report\`: one `.pbip` file and two folders beside it, `Rollout review.SemanticModel` (the model, as text) and `Rollout review.Report`. The repo's `.gitignore` keeps Power BI's local cache (which holds the loaded data) and the old .pbix out of git.

32. In PowerShell: `cd C:\repos\rollout-review`, then `git pull`. This brings the `.gitignore` the project needs; check that `dir -Force` lists `.gitignore`.
33. In Power BI Desktop, **File**, **Options and settings**, **Options**, **GLOBAL**, **Preview features**: if **Power BI Project (.pbip) save option** and **Store semantic model using TMDL format** are listed, tick both, click **OK** and restart Power BI Desktop, reopening `rollout-review.pbix`. If neither is listed, both are already standard (as on Branch review's 2.159); go on.
34. **File**, **Save as**, **Browse this device**. In the dialog, set **Save as type** to **Power BI project files (\*.pbip)**.
35. Go to `C:\repos\rollout-review`, make a new folder `report`, open it, set **File name** to `Rollout review`, and click **Save**. The title bar now reads **Rollout review**.
36. Close Power BI Desktop.
37. In PowerShell, check what git will take: `git status`. It should list `report/` and nothing ending in `.pbix` or `cache.abf`. Then: `git add report` and `git status` again: the new files are under `report/Rollout review.SemanticModel/` and `report/Rollout review.Report/`, with no `cache.abf` and no `localSettings.json`. If either shows, stop and send a screenshot.
38. `git commit -m "Power BI project: data load and model"`, then `git push`.
39. Tell me it is pushed. I pull on the Mac, check the model text (column types, sort orders, relationships), and write the measures and calculated columns into it with their descriptions and format strings. You then pull on the PC and reopen the project (section E, written once the measures are in).

`rollout-review.pbix` can be deleted once the project opens cleanly; git ignores it either way.

---

Pushed from the PC as `8dbed88`, 9 Nov 2026. Model text checked on the Mac: every column type as BUILD-STEPS section B sets it, the six sort orders in place, the 27 relationships with R9 and R21 inactive and none two-way, and no auto date/time tables.

---

## E. Measures in, theme, and a check on the screen

The 67 measures and 5 calculated columns from `measures.dax` are written into the model files by `scripts/dax_to_tmdl.py`, each with its description and format string. `_Measures` keeps its one empty column, now hidden, so the table shows as a measure table. Before any page is built, a scratch page reads a set of figures against the CSVs.

40. Close Power BI Desktop if it is open. In PowerShell: `git pull`.
41. Open `C:\repos\rollout-review\report\Rollout review.pbip`.
42. **Home**, **Refresh**. The calculated columns are worked out on refresh. If a message says a measure or column has an error, stop and send a screenshot.
43. In the **Data** pane, check:
    - `_Measures` sits at the top with the measure icon and holds 67 measures, with no warning triangle on any
    - `dim_team` has `seats_arrive_week` and `baseline_month`; `fact_test_run` has `tokens_per_run` and `passing`; `dim_library_item` has `status_month`
44. Import the theme: in Report view, the **View** ribbon (called **Design** in some versions), **Themes**, **Browse for themes** (or **Import theme**), and pick `C:\repos\rollout-review\theme.json`. The page background turns light grey.

### The scratch page

Report view, on the blank page that is already there. Each check is one Table visual: **Build a visual**, **Table**, then tick the fields listed, in order. A table with only measures shows one row. Turn the visual's **Totals** off (Format, Visual, Totals) where it has a row field.

45. **Check 1, page 0 and the shares.** A table with: `Seats assigned`, `Seats active this week`, `Moved up since last count`, `Seats arrived`, `Requests matched to a tested prompt that already exists`, `Requests matched count`, `First use within two weeks of training`, `Recurring questions covered by a tested prompt`, `Tested prompts that pass on a smaller model`. Expected:

    | Measure | Expected |
    |---|---|
    | Seats assigned | 1,167 |
    | Seats active this week | 505 |
    | Moved up since last count | 98 |
    | Seats arrived | 0 |
    | Requests matched to a tested prompt that already exists | 49.5% |
    | Requests matched count | 385 of 778 questions |
    | First use within two weeks of training | 44.5% |
    | Recurring questions covered by a tested prompt | 89.4% |
    | Tested prompts that pass on a smaller model | 2 |

46. **Check 2, the tiles by month.** A table with `dim_month[month_label]`, then `Foundation tile`, `Execution tile`, `Refinement tile`, `Scale tile`. Expected (blank means the cell is empty):

    | Month | Foundation | Execution | Refinement | Scale |
    |---|---:|---:|---:|---:|
    | Month 1 | 13.6% | blank | 0.0% | blank |
    | Month 2 | 53.9% | 86.1% | 0.0% | 0.0 |
    | Month 3 | 55.4% | 85.7% | 5.6% | 0.0 |
    | Month 4 | 57.2% | 84.7% | 8.7% | +4.9 |
    | Month 5 | 53.1% | 83.8% | 9.5% | +8.6 |
    | Month 6 | 49.5% | 83.6% | 9.5% | +10.1 |

    Scale reads 0.0 in months 2 and 3 by its definition: a team counts from its baseline month, where it is compared with itself.

47. **Check 3, verdicts, trends and thresholds** (month 6, nothing selected). A table with these twelve measures, in this order: `Foundation verdict`, `Foundation trend`, `Foundation threshold`, `Execution verdict`, `Execution trend`, `Execution threshold`, `Refinement verdict`, `Refinement trend`, `Refinement threshold`, `Scale verdict`, `Scale trend`, `Scale threshold`. Expected:

    | Tile | Verdict | Trend | Threshold |
    |---|---|---|---|
    | Foundation | Working | ↓ Down | Threshold 40% |
    | Execution | Working | ↓ Down | Threshold 60% |
    | Refinement | Not yet working | → Flat | Threshold 50% |
    | Scale | Working | ↑ Up | Threshold 10 points above baseline |

48. **Check 4, by team** (month 6, Source placement). A table with `dim_team[team]`, `baseline_month`, `Usage baseline by team`, `Share of people in the air latest`, `Share of people in the air baseline`, `Gap higher`, `Gap level`, `Gap lower`, `Largest group`, `Largest group people`. Expected:

    | Team | baseline_month | Usage baseline | In the air, latest | In the air, baseline | Higher | Level | Lower | Largest group | People |
    |---|---:|---:|---:|---:|---:|---:|---:|---|---:|
    | Consulting | 3 | 51.2% | 60.3% | 47.0% | 45 | 209 | 46 | Takeoff | 174 |
    | Finance | 3 | 27.9% | 13.0% | 9.5% | 111 | 76 | 13 | Waiting to board | 112 |
    | Legal | 2 | 11.9% | 7.5% | 6.7% | 19 | 91 | 10 | Ticket held | 84 |
    | Operations | 3 | 27.8% | 26.8% | 9.2% | 42 | 157 | 51 | Boarding | 95 |
    | People | 4 | 37.4% | 30.0% | 22.3% | 24 | 91 | 15 | Takeoff | 37 |
    | Technology | 3 | 51.2% | 52.0% | 42.5% | 29 | 141 | 30 | Takeoff | 101 |

49. Send a screenshot of the four tables (two if they do not fit). Any cell that differs, I fix in `measures.dax` and the model files, never in the expected figures. Do not save or commit yet.

All four checks matched on the PC, 9 Nov 2026 (check 3 once all twelve measures were in). The scratch page stays as a hidden page, **Checks**, for reading figures during the build, and is deleted before publish.

---

## F. Page 0: Rollout review (front, sponsor)

What the page holds (brief section 6): a header strip, four stage tiles in one row, the stage split by team, and the moved-up count.

**Approved by Megat on 10 Nov 2026, as pushed in round 4 (commit 821a169).** Rerunning `scripts/page0_pbir.py` reproduces it exactly; any later change to page 0 goes through a new round.

Page 0 is written by `scripts/page0_pbir.py`, using the shared checks in `scripts/pbir.py` (brief section 7, steps 5 and 6). `scripts/page0_figures.py` prints the stage split figures from the CSVs.

### Round 4 (10 Nov 2026): polish, from the round 3 screenshot

Round 3 confirmed `dataPoint.fill` (one entry per stage, picked by value) and `textStyle.color`; both are now in the confirmed list in `scripts/pbir.py`. The rule line under the tiles is approved.

| Fix asked | What changed |
|---|---|
| Navigator name at the bottom edge | Bar 26 to 32 high; at 32 (page 0 built by hand) the name read centred |
| Tile spacing: four groups, even gaps | Each tile is now (a) stage and question, (b) a 9pt grey caption sitting directly on the figure, (c) verdict, trend and threshold, (d) the sparkline, 10 px apart (2 above the sparkline, which pads itself). The figure, verdict, trend and threshold are each their own card with no label, divider or left padding, so the card's built-in gaps are gone. A one-line caption gets a blank line above it, so every caption touches its figure and the four figures share one line |
| Bottom panels: one top edge, one height | The two charts and Moved up are each a white panel, 240 high from y 476, with the title inside. Moved up is now caption-on-figure twice: the 98, then Seats arrived |
| Spacing as a standing rule | Constants in `scripts/pbir.py` (`PANEL_PAD_X` 12, `PANEL_PAD_TOP` 6, `GROUP_GAP` 10, `CHART_INSET` 8, `CAPTION_GAP` 0, `COL_GAP` 16, `ROW_GAP` 4, `TEXT_SNUG` 6), checked on every page with a text-fit estimate measured from the page 0 screenshots |

Not bold any more: the verdict is now a card value, and Desktop has not written a bold setting for a card value in Megat's files. It keeps its colour (amber when Not yet working).

Layout on the 1280 by 720 page, in pixels:

| Piece | x | y | w | h |
|---|---|---|---|---|
| Page navigator | 16 | 4 | 1248 | 32 |
| Title, header line (same row) | 16, 212 | 36 | 196, 1052 | 34 |
| "Read from" line | 16 | 70 | 1248 | 22 |
| Tile panels | 16, 332, 648, 964 | 96 | 300 | 350 |
| (a) stage and question | tile x + 12 | 102 | 276 | 62 |
| (b) caption, then figure | tile x + 12 | 174, 208 | 276 | 34, 54 |
| (c) verdict, trend, threshold | tile x + 12 | 272, 296, 320 | 276 | 24 each |
| (d) sparkline | tile x + 12 | 346 | 276 | 100 |
| Rule line | 16 | 450 | 1248 | 22 |
| Bottom panels: baseline, latest, moved up | 16, 488, 960 | 476 | 456, 456, 304 | 240 |

### Round 5 (10 Nov 2026): the shared header

Megat asked for one header on every page: the title; the sources and period in small grey text at the right of the title's row; the question on its own line below. Page 0 has no question, so its header line card sits on the second line, directly under the title (y 70, 24 high). The body moves down 2 px: tiles at y 98, the rule line at y 452, the bottom panels at y 478, 238 high (charts 204). Nothing else on page 0 changed. It needs approving again.

### On the PC (pages 0 and 1 together)

50. Close Power BI Desktop (save first if it asks).
51. In PowerShell, in the rollout-review folder: `git pull`.
52. Open `report/Rollout review.pbip`.
53. Send a screenshot of page 0, then click **Where people sit** in the navigator and send a screenshot of page 1. Then pick **Check-in** in the Placement toggle and send page 1 again.

### Figures page 0 should show

From check.py and the CSVs (the on-screen checks 1 to 4 in section E matched these):

| Piece | Should read |
|---|---|
| Header row | `Rollout review` then `1,200 people · 1,167 seats assigned · 505 seats active in Week 24` |
| Foundation | 49.5%, Working, ↓ Down, Threshold 40%; line 53.9%, 55.4%, 57.2%, 53.1%, 49.5% |
| Execution | 83.6%, Working, ↓ Down, Threshold 60%; line 86.1%, 85.7%, 84.7%, 83.8%, 83.6% |
| Refinement | 9.5%, Not yet working (amber), → Flat, Threshold 50%; line 0.0%, 5.6%, 8.7%, 9.5%, 9.5% |
| Scale | +10.1, Working, ↑ Up, Threshold 10 points above baseline; line 0.0, 0.0, +4.9, +8.6, +10.1 |
| Moved up | 98; Seats arrived 0 |
| Navigator | Rollout review, Where people sit (Checks is hidden) |

Stage split, by source placement (`python3 scripts/page0_figures.py`):

| Team | Baseline month | Baseline: ground, gate, air | Month 6: ground, gate, air |
|---|---:|---|---|
| Consulting | 3 | 12.0%, 41.0%, 47.0% | 9.0%, 30.7%, 60.3% |
| Finance | 3 | 16.5%, 74.0%, 9.5% | 17.0%, 70.0%, 13.0% |
| Legal | 2 | 71.7%, 21.7%, 6.7% | 79.2%, 13.3%, 7.5% |
| Operations | 3 | 30.4%, 60.4%, 9.2% | 22.8%, 50.4%, 26.8% |
| People | 4 | 33.8%, 43.8%, 22.3% | 37.7%, 32.3%, 30.0% |
| Technology | 3 | 20.0%, 37.5%, 42.5% | 19.5%, 28.5%, 52.0% |

---

## G. Page 1: Where people sit (FRAME-01)

Written by `scripts/page1_pbir.py`; figures from `python3 scripts/page1_figures.py` (add a month number, for example `4`, for the page with the month slicer moved).

### Round 3 (10 Nov 2026): fixes from the round 2 screenshots

Round 2 confirmed the matrix (totals off, cell shading, column widths, its Rows, Columns and Values roles) and the toggle as two buttons. Two settings did not take: data labels on the gap chart (a 100% stacked bar), and there is no setting yet for the selected button's colour. Both wait for a hand reference (step 54).

| Fix asked | What changed |
|---|---|
| Heat grid: all six rows | Matrix 220 high. Round 2 showed a 48 px header (with the sort arrow), 25 px rows and 18 px kept clear at the bottom, so six rows need 216 |
| Movement: labels on bars, legend cut | 10% between teams (`categoryAxis.innerPadding`, seen in Branch review), so each bar is 16 px, taller than its 14 px label; the legend has 104 px; Seats arrived sits on the legend row |
| Gap: counts on all three segments | Panel 300 to 352 wide, so Finance's 13 (the thinnest segment, 6.5% of its bar) gets 15 px of bar. Labels wait for the hand reference |
| Lever table: no sideways scrollbar | Three columns (team; largest group with its people, as "Ticket held, 84"; lever), sized to the round 2 measure: each column takes about 12 px more than its width. The lever column is 310, so a 46-character lever stays on one line |
| Toggle: selected in marine, white text | Waits for the hand reference: a Button slicer formatted by hand |
| Header line | "Month 6 shown; pick another month at the top right" |

The standing rules from page 1 are now in `scripts/pbir.py`: tables sized to columns and rows (`table_width`, `table_height`), bar thickness and segment width against a 14 px label, a fixed value axis 15% past the longest bar, legends on one line with 15% to spare, tables holding text only (read from the model's format strings), and each CHECK.md question for the page tied to the visual and field it is read from.

Layout: header as page 0, toggle x 944 (188 wide), month x 1148 (116). Matrix panel x 16, y 96, 1248 by 280. Bottom panels at y 380, 336 high: the gap x 16 (352), movement x 384 (274), largest group x 674 (590).

### Round 4 (10 Nov 2026): fixes from the round 3 screenshot

Megat's hand reference (commit d1878b6) turned the gap chart's labels on: Desktop wrote `labels.show` true, the same setting round 2 had written, so it is now confirmed for this chart type. The labels then showed percentages, so the chart is rebuilt to show counts:

| Fix asked | What changed |
|---|---|
| Gap labels as counts, not percentages | A plain stacked bar (`barChart`) of three helper share measures, `Gap higher share`, `Gap level share` and `Gap lower share`. They add to 1, so every bar runs full width and Finance's 13 has 16 px. Each carries a dynamic format string that prints its count, so the labels read 111 / 76 / 13. A custom label field would need a setting name not yet in Megat's files; the dynamic format string lives in `measures.dax` |
| Team column, no name breaks | 72 to 90 px; the lever column 310 to 292 (a 46-character lever still fits one line) |
| Toggle selected in marine, white text | Still waits for the hand reference (step 54) |
| Header | The shared header (section F, round 5), with the month note on the second line |
| Two lines before the first visual | The gap and movement panels put the subtitle and legend on one line ("Month only, not the toggle"); Seats arrived moves under the movement chart |

### Round 6 (10 Nov 2026): fixes from the round 5 screenshots, every page

| Fix asked | What changed |
|---|---|
| One corner style | Rounded, 4 px: `theme.json` border radius 8 to 4 (every visual box, slicers included), the tab bar's `rectangleRoundedCurve` 4, and every panel a rounded rectangle (`tileShape` 'rectangleRounded', `roundEdge` 4). The panels were sharp because `roundEdge` on a plain 'rectangle' does not round; 'rectangleRounded' is the navigator's value, so it is unconfirmed on a shape. If the panels stay sharp, the fallback is everything sharp |
| Slicers touch the tab bar and panels | Slicers start 4 px below the tab bar and end 4 px above the panels. The check now holds boxes (tab bar, slicers, panels) to 4 px down and 16 px across |
| Placement toggle clipped | Megat's button slicer (commit 1141219): no colour settings in its file, so marine and white is its default; 82 high, titled "Placement" through the field's display name, opening on Source. Page 1's body starts at y 126 under it |
| Gap: Finance's 13 and Legal's 10 unlabelled | Waits for the hand reference above (Overflow text). The check now needs 24 px for a label in a stacked segment |
| Subtitle cut, dark square before each legend | The subtitle had wrapped and its scrollbar was the square. Subtitles get their own line; legends sit under the chart; text boxes keep 6 px clear each side in the check (was 2) |
| Page 2: Month 1 labels collide, month names wrap | The by-month chart is paired columns (Rules and allowed use, amber; all other uses, marine): each count sits on its own column, and "Month 6" fits under its pair. The check now tests that a column's label and axis name fit |
| Page 3: blank first row, scrollbars in the grid | The blank row was Power BI's blank use: the cell measure added 0 for it. A new helper, `Recurring questions in grid`, is blank for the blank use and month; page 1's matrix uses `People at checkpoint in grid` the same way. The check now requires this guard on every grid |
| Page 3: empty first use panel | A bar per team beside the figure (it does not fit under it at this height): Consulting 57.3%, Finance 28.9%, Legal 0.0%, Operations 58.5%, People 21.3%, Technology 45.5% |

### On the PC (all six pages)

50. Close Power BI Desktop (save first if it asks).
51. In PowerShell, in the rollout-review folder: `git pull`.
52. Open `report/Rollout review.pbip` and go to **Where people sit**.
53. Send a screenshot of each of the six pages as they open, then Where people sit with the toggle on **Check-in** and the month on **Month 4**, and Execution with the team on **Operations**.
54. One hand reference on page 1, then save: **the gap chart**: **Format visual**, **Visual**, **Data labels**, **Options**, **Overflow text**: On. Nothing else. (Finance's 13 and Legal's 10 sit in segments of 16 and 20 px; round 4 showed a label needs about 24 px, so they need to overflow.)
55. Commit and push: `git add report`, `git commit -m "Page 1: gap labels overflow by hand"`, `git push`.

### Figures page 1 should show

As it opens (Source, Month 6). Matrix: count, with the team's share in brackets as a guide to the shading (the share is not on the page):

| Checkpoint | Consulting | Finance | Legal | Operations | People | Technology |
|---|---:|---:|---:|---:|---:|---:|
| No ticket | 2 | 3 | 0 | 6 | 10 | 12 |
| Ticket held | 15 | 14 | 84 (70%) | 40 | 28 (22%) | 20 |
| Checked in | 10 | 17 | 11 | 11 | 11 | 7 |
| Through security | 0 | 3 | 2 | 1 | 2 | 0 |
| Waiting to board | 11 | 112 (56%) | 9 | 30 | 21 | 12 |
| Boarding | 81 (27%) | 25 | 5 | 95 (38%) | 19 | 45 (22%) |
| Takeoff | 174 (58%) | 24 | 7 | 64 (26%) | 37 (28%) | 101 (50%) |
| Above the clouds | 3 | 2 | 2 | 2 | 2 | 1 |
| Frequent flyer | 4 | 0 | 0 | 1 | 0 | 2 |

| Team | Gap: Higher, Level, Lower | Movement: Up, Down | Largest group, people |
|---|---|---|---|
| Consulting | 45, 209, 46 | 33, 18 | Takeoff, 174 |
| Finance | 111, 76, 13 | 11, 13 | Waiting to board, 112 |
| Legal | 19, 91, 10 | 6, 4 | Ticket held, 84 |
| Operations | 42, 157, 51 | 18, 17 | Boarding, 95 |
| People | 24, 91, 15 | 15, 6 | Takeoff, 37 |
| Technology | 29, 141, 30 | 15, 9 | Takeoff, 101 |

Seats arrived: 0.

Toggle on **Check-in** (Month 6): the full matrix is printed by `python3 scripts/page1_figures.py`; the cells to look at are Consulting Checked in 30 and Above the clouds 24, Finance Takeoff 100, and the largest groups (Consulting Takeoff 156, Finance Takeoff 100, Legal Ticket held 74, Operations Boarding 75, People Takeoff 39, Technology Takeoff 80). Month on **Month 4** (Source): movement Up, Down: Consulting 33, 11; Finance 22, 10; Legal 7, 4; Operations 87, 12; People 37, 1; Technology 24, 12. Seats arrived 0.

### CHECK.md questions on page 1

| Q | Read from | Should read |
|---|---|---|
| 4 | The gap, Finance's bar (Month 6) | Higher 111, level 76, lower 13 |
| 5 | Largest group table, Legal row (Source, Month 6) | Ticket held, 84; "A first task done side by side with someone who already uses AI" |
| 6 | Movement, Operations, and Seats arrived (month on Month 4) | 87 moved up; 0 seats arrived |

---

## H. Page 2: Foundation

Written by `scripts/page2_pbir.py`; figures from `python3 scripts/page2_figures.py`. Header: "Foundation" with its question, "Which uses matter most, and where do people get stuck?"

| Piece | Built as | Period |
|---|---|---|
| Uses logged and ranked | Two bar charts side by side, Month 1 and Month 6, questions in each use, most first, one scale (0 to 60), counts on the bars. Two charts in place of a month slicer, so the change is on the page without a click | Month 1, Month 6 |
| The Foundation headline | Caption on the figure: Requests matched to a tested prompt that already exists, with the count under it ("385 of 778 questions", the helper `Requests matched count`) | whole period |
| Tested before going in the library | Prompts tested against an answer key written first, with "16 of 23 library items" under it (new helper `Answer key first count`) | all items |
| Usage baseline by team | One bar per team, A to Z, shares on the bars, scale 0 to 60% | each team's first four weeks |

No toggle or month slicer on this page. Layout: ranking panel x 16, y 96, 1248 by 364 (charts 604 by 304); bottom panels at y 464, 252 high: headline x 16 (300), answer key x 332 (300), baseline x 648 (616).

### Round 2 (10 Nov 2026)

- The shared header: "Foundation", then "Which uses matter most, and where do people get stuck?" on its own line; the sources at the right of the title's row.
- The top panel in three parts: Month 1 ranked and Month 6 ranked (392 wide each, one scale, 0 to 60), and every month as two lines, Rules and allowed use (amber) and all other uses (marine), counts on the points, scale 0 to 125. Helper measures `Rules questions` and `Other questions`.
- The two share panels (412 wide, so the measure's name fits one line) are titled with the measure's name, then a grey caption for the period, the figure, and its count line directly under it. "The Foundation headline" is gone.
- Baseline panel 392 wide.

### Figures page 2 should show

By month (the line chart): Rules and allowed use 52, 60, 56, 34, 24, 16; all other uses 36, 94, 101, 104, 106, 95.

| Use | Month 1 | Month 6 |
|---|---:|---:|
| Rules and allowed use | 52 | 16 |
| Drafting | 12 | 13 |
| Analysis | 9 | 23 |
| Summarising | 8 | 14 |
| Coding | 4 | 18 |
| Formatting | 2 | 18 |
| Research | 1 | 9 |
| All questions | 88 | 111 |

Month 1 ranks Rules and allowed use first; Month 6 ranks Analysis first, then Coding and Formatting tied on 18.

- Requests matched to a tested prompt that already exists: **49.5%**, "385 of 778 questions" (whole period; page 0's Month 6 figure is also 49.5%, so the count is the check)
- Prompts tested against an answer key written first: **69.6%**, "16 of 23 library items"
- Usage baseline by team: Consulting 51.2%, Finance 27.9%, Legal 11.9%, Operations 27.8%, People 37.4%, Technology 51.2%

### CHECK.md questions on page 2

| Q | Read from | Should read |
|---|---|---|
| 7 | Requests matched to a tested prompt that already exists, figure and count | 49.5% (385 of 778 questions) |
| 8 | The two ranking charts, top bar of each | Month 1: Rules and allowed use, 52; Month 6: Analysis, 23 |
| 9 | Usage baseline by team, shortest bar | Legal, 11.9% |

## I. Page 3: Execution

Written by `scripts/page3_pbir.py`; figures from `python3 scripts/page3_figures.py` (add a team, for example `Operations`, for the page with the team slicer moved). Header: "Execution", then "Does it hold up in everyday use?".

| Piece | Built as | Follows |
|---|---|---|
| Team | A dropdown at the top right, all teams to start. Added so CHECK.md question 12 (Operations) can be read on the page | |
| First use within two weeks of training | Figure with its count ("174 of 391 attendees", helper `First use count`) | team |
| Repeat use within 30 days, by month | Columns for Month 2 to Month 6, shares on the columns, scale 0 to 100% (Month 1 has no figure: nobody's first active week is 30 days old yet) | team |
| Recurring questions covered by a tested prompt | Figure with its count ("127 of 142 recurring questions", helper `Recurring covered count`), beside a grid: recurring questions in each use by month, shaded white to marine at 20 or more (helpers `Recurring shade`, `Recurring text colour`) | team |
| Tested prompts passing their cases | Figure with its count ("17 of 21 live prompts", helper `Passing count`), and under it the live prompts not passing at their latest run, by name, with cases matched (a table: text; helper `Cases matched when not passing`) | the whole library |

Layout: top row at y 102, 270 high: first use x 16 (412), repeat use x 444 (820). Bottom row at y 376, 340 high: recurring x 16 (814), passing x 846 (418).

### Figures page 3 should show

All teams (as it opens):

- First use within two weeks of training: **44.5%**, "174 of 391 attendees"
- Repeat use within 30 days: Month 2 86.1%, Month 3 85.7%, Month 4 84.7%, Month 5 83.8%, Month 6 83.6%
- Recurring questions covered by a tested prompt: **89.4%**, "127 of 142 recurring questions"
- Tested prompts passing their cases: **81.0%**, "17 of 21 live prompts". Not passing: Market scan in five questions, 8 of 9 cases; Shift handover summary, 9 of 10; What may I use it for: quick check, 11 of 12; Workplan from meeting notes, 8 of 9

Recurring questions grid, all teams:

| Use | Month 1 | Month 2 | Month 3 | Month 4 | Month 5 | Month 6 |
|---|---:|---:|---:|---:|---:|---:|
| Analysis | 0 | 1 | 0 | 0 | 0 | 0 |
| Coding | 0 | 0 | 1 | 0 | 0 | 0 |
| Drafting | 0 | 2 | 0 | 2 | 2 | 1 |
| Formatting | 0 | 1 | 1 | 1 | 0 | 1 |
| Research | 0 | 0 | 2 | 0 | 0 | 0 |
| Rules and allowed use | 15 | 36 | 25 | 17 | 12 | 5 |
| Summarising | 0 | 8 | 8 | 0 | 1 | 0 |

With the team on **Operations**, the Summarising row reads 0, 8, 8, 0, 0, 0.

### CHECK.md questions on page 3

| Q | Read from | Should read |
|---|---|---|
| 10 | First use within two weeks of training, figure and count | 44.5% (174 of 391 attendees) |
| 11 | Recurring questions covered by a tested prompt, figure and count | 89.4% (127 of 142 recurring questions) |
| 12 | The grid with the team on Operations, Summarising row | 8 + 8 = 16 in Months 2 and 3; 0 in Months 4 to 6 |

## J. Page 4: Refinement

Written by `scripts/page4_pbir.py`; figures from `python3 scripts/page4_figures.py`. Header: "Refinement", then "What earns its place, and at what cost?". No slicer.

| Piece | Built as |
|---|---|
| Tested prompts that pass on a smaller model | The count (2), the front page's share in words ("9.5% of live prompts at Week 24", helper `Smaller model share line`), and the prompts by name with their cases (a table: text; helper `Smaller model cases when passing`) |
| Prompts retired or merged | Columns by check-in month, counts on them, and beside them each change in words (a table: text; helper `Retired or merged change`) |
| Cost per use | Median tokens per run by prompt, standard (grey) beside smaller (marine), no labels; under it the cost index by prompt, labelled to two decimals (the one format outside counts, percentages and points, as CHECK.md reads it) |

Figures: passing on the smaller model **2** (LIB-09 Code review checklist, LIB-13 Query explainer); 9.5% of live prompts. Retired or merged: Month 5, 2 (LIB-12 retired; LIB-14 merged into LIB-10). Cost index: every prompt between 0.95 and 1.16 except LIB-09 **2.02** and LIB-13 **2.07** (the full list from `page4_figures.py`).

| Q | Read from | Should read |
|---|---|---|
| 13 | Passing on the smaller model, the table | LIB-09, LIB-13 |
| 14 | Cost index, the LIB-09 and LIB-13 columns | 2.02, 2.07 |
| 15 | Retired or merged, the table | LIB-12 retired in Month 5; LIB-14 merged into LIB-10 in Month 5 |

## K. Page 5: Scale

Written by `scripts/page5_pbir.py`; figures from `python3 scripts/page5_figures.py`. Header: "Scale", then "Where has it changed the work?". No slicer.

| Piece | Built as |
|---|---|
| Impact in people's own words | Month 6 answers to "If AI disappeared from your work tomorrow, what would change?", one bar per team split I would lose time every week (marine), A little (pale), Nothing (grey), counts on the segments (share measures with a dynamic format string, as the page 1 gap) |
| Share of people in the air against the baseline | Two bars per team, its baseline month (grey) and Month 6 (marine), the baseline month beside the team's name (new column `dim_team[team_baseline_label]`); beside them the change in points (helper `Air change points`) |
| Uses taken up beyond the first team | The count (4, "4 of 23 library items") and the prompts by name: who made each, who took it up, from which week (a table: text; helper `Second team from`) |

Figures: impact, lose time every week / a little / nothing: Consulting 162 / 74 / 62, Finance 86 / 67 / 44, Legal 17 / 28 / 75, Operations 73 / 106 / 65, People 48 / 37 / 35, Technology 90 / 52 / 46. In the air, baseline to Month 6: Consulting (Month 3) 47.0% to 60.3%, +13.3; Finance (Month 3) 9.5% to 13.0%, +3.5; Legal (Month 2) 6.7% to 7.5%, +0.8; Operations (Month 3) 9.2% to 26.8%, +17.6; People (Month 4) 22.3% to 30.0%, +7.7; Technology (Month 3) 42.5% to 52.0%, +9.5. Taken up: LIB-01 Proposal outline from a brief, made by Consulting, taken up by Technology from Week 7; LIB-03 Market scan in five questions, Consulting, Finance, Week 15; LIB-10 Error log explainer, Technology, Operations, Week 14; LIB-16 Shift handover summary, Operations, People, Week 18.

| Q | Read from | Should read |
|---|---|---|
| 16 | Uses taken up, the earliest week in the table | LIB-01 (Consulting), taken up by Technology from Week 7 |
| 17 | Share in the air, Consulting · Month 3, and the change | 47.0% at Month 3, 60.3% at Month 6, +13.3 points |
| 18 | Impact, the "I would lose time every week" segments | Consulting 162, Technology 90, Finance 86, Operations 73, People 48, Legal 17 |

## Next

- All six pages are written. Next: the CHECK.md match from the screenshots (brief section 8), then Publish to web
