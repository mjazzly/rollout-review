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

## Next

- E. Pull the measures, reopen the project, refresh, import the theme, and read a few figures off a scratch page against CHECK.md before any page is built
- F. Page 0, then pages 1 to 5, one page at a time, a screenshot per page
