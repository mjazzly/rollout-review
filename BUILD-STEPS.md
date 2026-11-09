# Build steps: Rollout review in Power BI Desktop

The on-screen steps for `PBI-BRIEF.md` sections 2 to 6, on the PC over Remote Desktop. One action per step. When a step says "send a screenshot", stop there and wait for the reply before going on.

This first part covers the data load and the model that pages 0 to 5 all read (brief sections 2 and 3). It ends at the model view screenshot (step 31). Section D then saves it as a Power BI project; the measures (`measures.dax`) and the page steps follow.

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

The first build by hand (old steps 50 to 65) ran out of room: the sizes given were too small for the text, so the question ran into the card label, the reference labels were cut off and the sparkline was too short to draw. Page 0 is now written from the Mac by `scripts/page0_pbir.py`, straight into the project's report files, the way the measures are. The card, line chart, shape and navigator settings copy the ones Desktop wrote on the PC (commit 22ebf37), and the script checks that every visual sits on the page and that nothing overlaps.

Layout on the 1280 by 720 page, in pixels:

| Piece | x | y | w | h |
|---|---|---|---|---|
| Page navigator | 16 | 8 | 1248 | 30 |
| Title text box | 16 | 40 | 1248 | 56 |
| Header line card | 16 | 96 | 1248 | 28 |
| Tile panels (Foundation, Execution, Refinement, Scale) | 16, 332, 648, 964 | 132 | 300 | 384 |
| In each tile: stage and question | tile x + 12 | 138 | 276 | 66 |
| In each tile: card (figure, verdict, trend, threshold) | tile x + 12 | 204 | 276 | 182 |
| In each tile: sparkline, months 2 to 6 | tile x + 12 | 388 | 276 | 74 |
| In each tile: rule text, 8 | tile x + 12 | 464 | 276 | 52 |
| Stage split, baseline | 16 | 528 | 456 | 184 |
| Stage split, latest (legend on top) | 488 | 528 | 456 | 184 |
| Moved up since the last count | 960 | 528 | 304 | 184 |

The script also sets the Checks page to hidden, so the navigator does not list it. Two settings from the old steps are left at Desktop's default because their file names were not in Desktop's own files yet: the reference labels stack one under another rather than side by side, and the Seats arrived label keeps its measure name.

### On the PC

50. Close Power BI Desktop (save first if it asks). It does not notice files changing underneath it.
51. In PowerShell, in the rollout-review folder, `git pull`.
52. Open `report/Rollout review.pbip`. If Desktop reports a problem with a visual, send a screenshot of the message.
53. Send a screenshot of the whole page. It should read:
    - Header: `1,200 people · 1,167 seats assigned · 505 seats active in Week 24`
    - Foundation: 49.5%, **Working**, ↓ Down, Threshold 40%
    - Execution: 83.6%, **Working**, ↓ Down, Threshold 60%
    - Refinement: 9.5%, **Not yet working** in amber, → Flat, Threshold 50%
    - Scale: +10.1, **Working**, ↑ Up, Threshold 10 points above baseline
    - Moved up: 98, with Seats arrived 0 beside it
    - Two stage charts, six teams each, Consulting at the top
    - The navigator lists Rollout review only, not Checks

Fixes come back as a short list, made in the script and pulled again. Do not move or edit page 0's visuals on the PC until it is agreed: the next run of the script replaces the whole page. Once page 0 is agreed, it is committed from the PC (brief section 7, step 4).

---

## Next

- G. Page 1, Where people sit, then pages 2 to 5, one page at a time, a screenshot per page
