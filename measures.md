# Measures: Rollout review (DASH-02)

Each measure has one definition, written once here and carried word for word into the DAX measure description. That way the page, the check and the repo agree. The definitions use the column names in `DICTIONARY.md`. Section numbers refer to `DASH-02-DESIGN.md`.

## Shared terms

| Term | Definition |
|---|---|
| Active week | A week in which the person's days_active is 2 or more. |
| Check-in week | The fourth and last week of a check-in month. The check-in date is the last day of that week. |
| Trailing eight weeks | The check-in week and the seven weeks before it. Weeks before the period count as inactive, because nobody had a seat then. |
| Ever | From the first week of the period up to and including the check-in week. |
| Live item | A library item whose published_week is on or before the week and whose status_week, if set, is after the week. |
| Owns a library item | Is the owner_person_id of at least one item that is live in the check-in week. |
| Tokens per run | tokens_in plus tokens_out for one test run. |
| Latest run | For an item and model tier, the test run with the latest run_date on or before the date in question. A tie goes to the higher run_id. |
| Team's seats arrive | The earliest seat_assigned_week among the team's people. |

## Supporting measures (section 8)

| Measure | Definition |
|---|---|
| Assigned seats | People whose seat_assigned_week is on or before the week. |
| Weekly active share | People with days_active of 2 or more in the week, over assigned seats. |
| Library share | runs_via_library over runs_total. |
| Repeat flag | A question from the same person in the same category within 30 days of an earlier question by that person. |
| Passing | A test run where cases_matched equals cases_total. |
| Cost index | Median tokens per run on the standard tier over median tokens per run on the smaller tier, per item. |
| Baseline month | The first check-in month. |
| Moved up | People who held a seat at both the latest count and the previous count, and whose source checkpoint_id at the latest count is higher than at the previous count. |
| Seats arrived | People with no seat at the previous count and a seat at the latest count. Always shown beside Moved up and never added into it. |

A person **holds a seat at a count** when their seat_assigned_week is on or before that check-in week.

## Source placement rules (section 5)

Each person is evaluated at every check-in month over the trailing eight weeks, unless a rule says otherwise. The rules are tried from the top, and the first one that matches wins. Together they place every person, and the result is `fact_placement.source_checkpoint_id`.

| Order | Checkpoint | Rule |
|---|---|---|
| 1 | Frequent flyer (9) | Owns a library item, and is answered_by_person_id on 3 or more questions in the trailing eight weeks. |
| 2 | Above the clouds (8) | Has 6 or more active weeks in the trailing eight, has runs on 2 or more distinct library items in fact_library_run_person in the trailing eight weeks, and owns a library item. |
| 3 | Takeoff (7) | Has 4 or more consecutive active weeks in the trailing eight. |
| 4 | Boarding (6) | Has runs_via_library above 0 in at least one week ever, and fewer than 4 consecutive active weeks in the trailing eight. |
| 5 | Through security (4) | Asked a question in the Rules and allowed use category in the trailing 30 days (the check-in date and the 29 days before it), and has fewer than 2 active weeks among the weeks starting in those 30 days. |
| 6 | Waiting to board (5) | Has at least one active week in the trailing eight, and fewer than 4 of them consecutive. |
| 7 | Checked in (3) | Has at least one active week ever, and none in the trailing eight. |
| 8 | Ticket held (2) | Has a seat assigned on or before the check-in week, and no active week ever. |
| 9 | No ticket (1) | Has no seat assigned on or before the check-in week. Every rule above needs a seat, so testing this one first gives the same result. |
| | Gap | Check-in checkpoint_id minus source checkpoint_id, for the same person and check-in month. |

Notes on how the rules read against FRAME-01's page wording:

- **Checked in is wider than the page wording.** The page says "Tried AI once or twice, then stopped". The rule also covers people who used AI for several weeks and then stopped, because FRAME-01 has no separate checkpoint for a lapsed user.
- **Waiting to board is wider than "only in the weeks a reminder goes out".** It covers anyone who uses AI now and then, has no library run and has never kept it up for four weeks running. The live check-in words this checkpoint as "I mostly use AI when a reminder or a task pushes me". People whose active weeks are all reminder weeks remain a subset, which `dim_week.reminder_week` can still show.
- **Takeoff reads from usage alone**, as FRAME-01 says the usage dashboards separate it. A library run is not required.

## Page 0: Rollout review (front, sponsor)

| Measure | Definition |
|---|---|
| Headcount | People in dim_person. |
| Seats assigned | Assigned seats in the selected week. |
| Seats active this week | People with an assigned seat and days_active of 2 or more in the selected week. |
| Stage split | Share of people in each stage (On the ground, At the gate, In the air) by source placement, for the latest check-in month and the baseline month. |
| Moved up since last count | Moved up, counted between the latest check-in month and the one before it, shown with Seats arrived for the same two counts beside it. |

### Stage tiles

Each tile shows one headline figure for the latest check-in month, a 24-week sparkline, and its verdict rule printed underneath.

**Verdict rule (all four tiles).** The verdict is Working when the figure for the check-in month meets the tile's threshold and is higher than the figure for two check-in months earlier. Otherwise it is Not yet working.

**The thresholds are illustrative programme targets.** A real programme sets its own; these are here so the tiles can carry a verdict on the synthetic data.

| Tile | Headline measure | Definition | Threshold |
|---|---|---|---|
| Foundation | Requests matched to a tested prompt that already exists | Questions asked in the check-in month with action_taken of pointed to library, over all questions asked in the check-in month. | 40% |
| Execution | Repeat use within 30 days | People with another active week starting within 30 days after their first active week, over people whose first active week starts at least 30 days before the check-in date. | 60% |
| Refinement | Tested prompts that pass on the smaller model | Items live in the check-in week whose latest smaller-tier run on or before the check-in date is passing, over all items live in the check-in week. | 50% |
| Scale | Share of people in the air against the baseline | Share of people with a source checkpoint_id of 7, 8 or 9 in the check-in month, minus the same share in the baseline month, in percentage points. | 10 points above baseline |

## Page 1: Where people sit (FRAME-01)

| Measure | Definition |
|---|---|
| People at checkpoint | People at each checkpoint, per team and check-in month, by check-in placement or by source placement as the page toggle selects. |
| Gap: higher | People whose check-in checkpoint_id is higher than their source checkpoint_id in the check-in month. |
| Gap: level | People whose check-in checkpoint_id equals their source checkpoint_id in the check-in month. |
| Gap: lower | People whose check-in checkpoint_id is lower than their source checkpoint_id in the check-in month. |
| Movement: up | Moved up, per team. |
| Movement: held | People who held a seat at both counts and whose source checkpoint_id at the latest count equals the previous count. |
| Movement: down | People who held a seat at both counts and whose source checkpoint_id at the latest count is lower than at the previous count. |
| Movement: seats arrived | Seats arrived, per team, shown apart from up, held and down. |
| Largest group | Per team, the checkpoint with the most people under the placement the page toggle selects, for the check-in month, shown with its lever from dim_checkpoint. A tie goes to the lower checkpoint_id. |

## Page 2: Foundation. Which uses matter most, and where do people get stuck?

| Measure | Definition |
|---|---|
| Uses logged and ranked | Questions in each category, ranked from most to fewest. |
| Prompts tested against an answer key written first | Library items with answer_key_first true, over all library items. |
| Requests matched to a tested prompt that already exists | Questions with action_taken of pointed to library, over all questions. |
| Usage baseline by team | Weekly active share per team, averaged over the four weeks starting with the week the team's seats arrive. |

## Page 3: Execution. Does it hold up in everyday use?

| Measure | Definition |
|---|---|
| First use within two weeks of training | Training attendees with a run of the item shown in their session in the session week or the week after, over all training attendees. |
| Repeat use within 30 days | People with another active week starting within 30 days after their first active week, over people whose first active week starts at least 30 days before the end of the period. |
| Recurring questions covered by a tested prompt | Questions with repeat_flag true whose category had a live library item in the week they were asked, over all questions with repeat_flag true. |
| Tested prompts passing their cases | Live library items whose latest standard-tier run is passing, over all live library items. |

## Page 4: Refinement. What earns its place, and at what cost?

| Measure | Definition |
|---|---|
| Tested prompts that pass on a smaller model | Library items whose latest smaller-tier run is passing. |
| Cost per use | Median tokens per run, per item and model tier. |
| Cost index | Median tokens per run on the standard tier over median tokens per run on the smaller tier, per item. |
| Prompts retired or merged | Library items with status retired or merged, counted by the check-in month of their status_week, with merged_into_item_id shown for merged items. |

## Page 5: Scale. Where has it changed the work?

| Measure | Definition |
|---|---|
| Impact in people's own words | Check-in responses per team for each answer to q5_if_gone, for the check-in month. |
| Uses taken up beyond the first team | Library items with runs in fact_library_run from 2 or more teams. |
| Week the second team started | Per library item, the earliest week_start in fact_library_run with runs from a team other than the owner_team. |
| Share of people in the air | People with a source checkpoint_id of 7, 8 or 9, over all people in the team, per team, for the latest check-in month and the baseline month. |
