# Data dictionary: Rollout review (DASH-02)

Every table in `data/`, its grain, the live system that would supply it, and every column. Everything is synthetic, written by `generate.py` (seed 42), except `dim_threshold`, which is written by hand. To swap in a live backend, replace a CSV with an export that has the same columns.

Conventions across all tables:

- Dates are ISO `YYYY-MM-DD`. A **week** is identified by its `week_start` date, a Monday. Every column ending in `_week` holds a `week_start` date and joins to `dim_week.week_start`.
- The period is 24 weeks, from 2026-05-18 to the week starting 2026-10-26. A **check-in month** is a block of four weeks (1 to 6). Each check-in is taken at the end of the block's fourth week.
- Booleans are written `True` or `False`. An empty cell means null.
- `person_id` is `P0001` to `P1200`. People have no names; per section 12 of the design note, team is the lowest grain shown.
- No currency anywhere. Cost is measured in tokens.

| Table | Kind | Grain | Rows | Live source |
|---|---|---|---:|---|
| fact_question | fact | question | 778 | Office hours or help channel log |
| fact_usage_week | fact | person, week | 24,419 | Platform admin export |
| fact_library_run | fact | item, team, week | 408 | Library run log |
| fact_library_run_person | fact | item, person, week | 7,319 | Library run log |
| fact_test_run | fact | test run | 89 | Test harness output |
| fact_checkin | fact | person, month | 7,200 | Check-in form |
| fact_training | fact | session, attendee | 391 | Training register |
| fact_placement | fact, **derived** | person, check-in month | 7,200 | Derived by `generate.py` from the tables above (section 5 rules) |
| dim_person | dimension | person | 1,200 | HR roster plus licence admin |
| dim_team | dimension | team | 6 | HR roster |
| dim_week | dimension | week | 24 | Calendar plus comms plan |
| dim_checkpoint | dimension | checkpoint | 9 | FRAME-01, copied word for word |
| dim_library_item | dimension | library item | 23 | The library's records: owner, version, limits and test result |
| dim_category | dimension | category | 7 | Analyst's category list |
| dim_threshold | dimension | stage tile | 4 | The programme's own targets (illustrative here, from measures.md) |

---

## Facts

### fact_question

The question log: one row per question asked, who asked, what the request really was, how hard it was, and what was done.
**Grain:** question. **Live source:** office hours or help channel log.

| Column | Type | Description |
|---|---|---|
| question_id | text | `Q00001` onward, in date order. Key. |
| question_date | date | Day the question was asked. |
| person_id | text | Who asked. Joins to dim_person. |
| team | text | The asker's team, as logged. Joins to dim_team. |
| category | text | What the request really was. Joins to dim_category. |
| difficulty | integer | 1 to 3, where 3 is hardest. |
| action_taken | text | One of `answered`, `pointed to library`, `new prompt written`, `escalated`. |
| linked_item_id | text, nullable | For `pointed to library`, the item pointed to. For `new prompt written`, the first item in the same category published within four weeks of the question, if there is one. Otherwise empty. |
| answered_by_person_id | text, nullable | The colleague who answered, when a colleague did. Empty when the office hours host answered or the question was escalated. |
| repeat_flag | boolean | True when the same person asked an earlier question in the same category within 30 days (section 8). |

### fact_usage_week

The usage dashboards: the figures the tools themselves report.
**Grain:** person, week. There is one row for every seat holder for every week from their `seat_assigned_week` on, including weeks with no use. People without a seat have no rows. **Live source:** platform admin export.

| Column | Type | Description |
|---|---|---|
| person_id | text | Joins to dim_person. |
| week_start | date | Joins to dim_week. |
| days_active | integer | Days in the week with any use, 0 to 5. A week counts as an **active week** when this is 2 or more. |
| sessions | integer | Sessions started in the week. |
| runs_total | integer | Prompts run in the week. |
| runs_via_library | integer | Of runs_total, the runs made from a library item. Always no more than runs_total. |

### fact_library_run

The library's records, use side.
**Grain:** item, team, week. A row exists only where the item had runs. **Live source:** library run log.

| Column | Type | Description |
|---|---|---|
| item_id | text | Joins to dim_library_item. |
| team | text | The running people's team. Joins to dim_team. |
| week_start | date | Joins to dim_week. |
| runs | integer | Runs of the item by that team in that week. |
| distinct_users | integer | People in that team who ran the item that week. |

This table is the exact roll-up of fact_library_run_person. It is still written out because it is the table the design note names.

### fact_library_run_person

The library's records, use side, per person. Two things read person-level item runs: the Above the clouds rule ("runs across 2 or more library items") and Execution's first measure ("a run on the shown item within 14 days").
**Grain:** item, person, week. **Live source:** library run log, which records who ran each item.

| Column | Type | Description |
|---|---|---|
| item_id | text | Joins to dim_library_item. |
| person_id | text | Joins to dim_person. |
| week_start | date | Joins to dim_week. |
| runs | integer | Runs of the item by the person in the week. Summed across items, this equals fact_usage_week.runs_via_library for the same person and week. |

### fact_test_run

The run log: what each test run cost and what it matched.
**Grain:** test run. **Live source:** test harness output.

| Column | Type | Description |
|---|---|---|
| run_id | text | `R0001` onward, in date order. Key. |
| item_id | text | Joins to dim_library_item. |
| version | integer | The item version tested. |
| run_date | date | Day of the run. |
| model_tier | text | `standard` or `smaller`. |
| cases_total | integer | Test cases in the answer key. |
| cases_matched | integer | Cases whose output matched the key. A run is **passing** when this equals cases_total. |
| tokens_in | integer | Input tokens for the run. |
| tokens_out | integer | Output tokens for the run. **Tokens per run** is tokens_in plus tokens_out. |

### fact_checkin

The check-in (FRAME-01): five questions about stage, then one about checkpoint. Answer text is copied word for word from the live form on the Frames page.
**Grain:** person, check-in month. Every person answers all six check-ins. **Live source:** check-in form.

| Column | Type | Description |
|---|---|---|
| person_id | text | Joins to dim_person. |
| checkin_month | integer | 1 to 6. Joins to dim_week.checkin_month. |
| q1_access | text | "Can you use AI for your work today?" One of `Yes, and I know what I may use it for` (air), `Yes, but I am unsure what is allowed` (gate), `No, or not yet` (ends the form at No ticket). |
| q2_last_use | text, nullable | "When did you last use AI on real work?" One of `This week` (air), `Some weeks ago` (gate), `Only to try it out` (ground). Empty when q1 is `No, or not yet`. |
| q3_trigger | text, nullable | "What gets you to open it?" One of `Habit, it is part of how I work` (air), `A reminder, or a task that needs it` (gate), `I have not found the moment yet` (ground). Empty when q1 is `No, or not yet`. |
| q4_used_on | text, nullable | "What do you use AI on?" One of `Work that goes to someone else` (air), `Small tasks and drafts I mostly rewrite` (gate), `Nothing yet` (ground). Empty when q1 is `No, or not yet`. |
| q5_if_gone | text, nullable | "If AI disappeared from your work tomorrow, what would change?" One of `I would lose time every week` (air), `A little` (gate), `Nothing` (ground). Empty when q1 is `No, or not yet`. This is the Scale page's "impact in people's own words". |
| checkpoint_id | integer | The sixth question, "Which sounds most like you?". The value is 1 when q1 is `No, or not yet`. Otherwise it is a checkpoint inside the stage that q1 to q5 select under the form's rule: the most common stage wins, and a tie goes to the earlier stage. Joins to dim_checkpoint. |

### fact_training

Needed for Execution's first measure.
**Grain:** session, attendee. **Live source:** training register.

| Column | Type | Description |
|---|---|---|
| session_id | text | `S01` onward. |
| person_id | text | Attendee. Joins to dim_person. |
| team | text | Team the session was run for. Joins to dim_team. |
| session_week | date | `week_start` of the session's week. Joins to dim_week. |
| item_id_shown | text | The library item shown in the session. Joins to dim_library_item. |

### fact_placement (derived)

**Derived, not a source.** `place()` in `generate.py` computes it from fact_usage_week, fact_library_run_person, fact_question, dim_person, dim_library_item, dim_week and fact_checkin, using the section 5 source placement rules as written in `measures.md`. Power BI reads this table instead of recomputing trailing windows in DAX. `check.py` can recompute it from the same CSVs.
**Grain:** person, check-in month.

| Column | Type | Description |
|---|---|---|
| person_id | text | Joins to dim_person. |
| checkin_month | integer | 1 to 6. |
| checkin_checkpoint_id | integer | The person's own placement: fact_checkin.checkpoint_id. Joins to dim_checkpoint. |
| source_checkpoint_id | integer | The placement the sources give, from the first rule that matches. The rules place every person, so this is never empty. Joins to dim_checkpoint. |
| gap | integer | checkin_checkpoint_id minus source_checkpoint_id. Above 0 means the person places themselves higher than the sources do. |

---

## Dimensions

### dim_person

**Grain:** person. **Live source:** HR roster plus licence admin.

| Column | Type | Description |
|---|---|---|
| person_id | text | Key. |
| team | text | Joins to dim_team. |
| level | text | `Junior`, `Mid`, `Senior` or `Lead`. |
| region | text | `Americas`, `Europe` or `Asia Pacific`. |
| start_date | date | Joining date. Everyone joined before the period starts. |
| seat_assigned_week | date, nullable | `week_start` of the week their seat on the assistant platform was assigned. Empty means no seat in the period. Seats are staggered by team: Legal in week 1, Consulting from week 2, Finance from week 3, Technology from week 4, Operations from week 5, People from week 9. |

### dim_team

**Grain:** team. **Live source:** HR roster.

| Column | Type | Description |
|---|---|---|
| team | text | `Consulting`, `Finance`, `Operations`, `Legal`, `People`, `Technology`. Key. |
| headcount | integer | 300, 200, 250, 120, 130 and 200, for 1,200 in total. |

### dim_week

**Grain:** week. **Live source:** calendar plus comms plan.

| Column | Type | Description |
|---|---|---|
| week_start | date | Monday. Key. |
| month | text | Calendar month of week_start, as `YYYY-MM`. |
| checkin_month | integer | The four-week check-in month the week falls in, 1 to 6. Weeks 1 to 4 are month 1, and so on. |
| reminder_week | boolean | True in the weeks a reminder goes out: every fourth week, starting with week 1 (weeks 1, 5, 9, 13, 17, 21). |

### dim_checkpoint

**Grain:** checkpoint. **Live source:** FRAME-01. Copied word for word from section 4 of the design note.

| Column | Type | Description |
|---|---|---|
| checkpoint_id | integer | 1 to 9. Key. |
| checkpoint | text | No ticket, Ticket held, Checked in, Through security, Waiting to board, Boarding, Takeoff, Above the clouds, Frequent flyer. |
| stage | text | On the ground (1 to 3), At the gate (4 to 6), In the air (7 to 9). |
| how_you_tell | text | FRAME-01's "How you tell" line. |
| lever | text | FRAME-01's "The lever" line. |

### dim_library_item

**Grain:** library item. **Live source:** the library's records: owner, version, limits and test result.

| Column | Type | Description |
|---|---|---|
| item_id | text | `LIB-01` to `LIB-23`. Key. |
| item_name | text | Short generic name of the tested prompt. |
| category | text | Joins to dim_category. |
| owner_person_id | text | The person who looks after the item. Joins to dim_person. |
| owner_team | text | The owner's team. Joins to dim_team. |
| version | integer | Current version. |
| limits | text | What the item must not be used for. |
| answer_key_first | boolean | True when the answer key was written before the prompt. |
| status | text | `active`, `retired` or `merged`. |
| merged_into_item_id | text, nullable | For `merged`, the item it was merged into. |
| published_week | date | `week_start` of the week it was published. |
| status_week | date, nullable | `week_start` of the week it was retired or merged. Empty while active. |

An item is **live** in a week when published_week is on or before that week and, if status_week is set, the week is before status_week.

### dim_category

**Grain:** category. **Live source:** analyst's category list.

| Column | Type | Description |
|---|---|---|
| category | text | `Rules and allowed use`, `Drafting`, `Summarising`, `Analysis`, `Research`, `Formatting`, `Coding`. Key. |

### dim_threshold

The thresholds the four stage tiles on page 0 are judged against. They are the illustrative programme targets from measures.md ("Stage tiles"): a real programme sets its own, and these are here so the tiles can carry a verdict on the synthetic data. Power BI reads the threshold from this table, so each tile prints its threshold from data rather than a typed label.
**Grain:** stage tile. **Live source:** the programme's own targets. Written by hand, not by `generate.py`, so rerunning the generator leaves it as it is.

| Column | Type | Description |
|---|---|---|
| stage | text | `Foundation`, `Execution`, `Refinement`, `Scale`: the FRAME-04 stage the tile answers. Key. |
| threshold | decimal | The tile's threshold, in the unit of the tile's own figure. A share for Foundation (0.4, that is 40%), Execution (0.6, 60%) and Refinement (0.5, 50%). Percentage points above baseline for Scale (10). A tile's verdict is Working when its figure meets this value. |
