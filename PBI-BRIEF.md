# Power BI brief: Rollout review (DASH-02)

Read DASH-02-DESIGN.md, measures.md, DICTIONARY.md and CHECK.md before this file. This brief covers build order steps 4 to 6: the Power BI report on the Windows PC, the check against CHECK.md, and Publish to web. The site page entry (step 6, second half) is a separate session in the site folder.

## 1. How this build runs

- Claude Code runs on the Mac in this folder and writes everything: the DAX measures file, the theme file, the model's measures, and every report page, as the project's report files (one script per page under `scripts/`). It never touches the PC. (Changed on 10 Nov 2026, after page 0 built by hand ran out of room: pages are now written from the Mac, not built by hand.)
- Megat builds nothing and moves nothing by hand on the PC. His part for each page: close Power BI Desktop, `git pull`, open the .pbip, send a screenshot of the page, approve or list fixes.
- The PC has the repo cloned at `C:\repos\rollout-review` (clone it there if not yet; Git on the PC already carries the noreply identity from the data-answers build). The report is saved as a Power BI project, `report/Rollout review.pbip`, and committed from the PC on Megat's word. (Changed from a .pbix on 9 Nov 2026, after the model check, so the measures go into the model's text files from the Mac, as for Branch review.)
- Nothing is published until the check in section 8 is recorded.

## 2. Data load

- Get Data from the `data` folder: load all fifteen CSVs as separate queries, names as the file names without `.csv`.
- Set the folder path as a Power Query parameter `DataFolder` (default `C:\repos\rollout-review\data`) so the file opens on any machine by changing one value.
- Types: every `*_week`, `week_start`, `*_date` column as Date; every `*_id` as Text except `checkpoint_id`, `checkin_checkpoint_id`, `source_checkpoint_id` and `gap` as Whole Number; percentages and counts as Whole Number or Decimal as the dictionary says; booleans as True/False.
- Add to `dim_week` in Power Query: `week_no` (1 to 24, from the row order of `week_start`) and `week_label` = "Week " & week_no. Sort `week_label` by `week_no`. Every axis and slicer uses `week_label` or `checkin_month`; **no calendar date appears on any page**.
- Add a second copy of `dim_checkpoint` named `dim_checkpoint_source` (reference query) so `fact_placement` can relate to both the check-in checkpoint and the source checkpoint with active relationships.

## 3. Model

Star schema, single direction, one-to-many from dimension to fact:

| From | To |
|---|---|
| dim_person[person_id] | fact_usage_week, fact_checkin, fact_question, fact_library_run_person, fact_training, fact_placement |
| dim_team[team] | dim_person (and fact_library_run[team], fact_question[team]) |
| dim_week[week_start] | fact_usage_week, fact_library_run, fact_library_run_person, fact_training[session_week] |
| dim_checkpoint[checkpoint_id] | fact_checkin[checkpoint_id], fact_placement[checkin_checkpoint_id] |
| dim_checkpoint_source[checkpoint_id] | fact_placement[source_checkpoint_id] |
| dim_library_item[item_id] | fact_library_run, fact_library_run_person, fact_test_run, fact_question[linked_item_id], fact_training[item_id_shown] |
| dim_category[category] | fact_question, dim_library_item |

`checkin_month` is a column on `fact_checkin`, `fact_placement` and `dim_week`; add a small `dim_month` table (1 to 6) if a month slicer needs a single source. Mark `dim_week` as the date table only if a time-intelligence function needs it; the measures below do not.

## 4. Measures

- Claude Code writes `measures.dax`: one block per measure, in the order of measures.md, each with the measure name, the DAX, and a `// description:` line carrying the measures.md definition word for word. Claude Code writes each measure from `measures.dax` into the project's model files (TMDL) on the Mac, with its description and format string, pushes, and Megat pulls on the PC, where Power BI reloads the project. The page, the check and the repo then say the same words.
- Put all measures in a dedicated empty table `_Measures`.
- Headline measures for the four tiles, their thresholds, and the verdict and trend rules come from measures.md as amended (verdict from threshold alone; trend up, flat within 1 point, or down against two months earlier; "No comparison yet" where there is no earlier figure). Thresholds live in a small `dim_threshold` table (stage, threshold) loaded from a two-column CSV Claude Code adds to `data/`, so the tile prints the threshold from data rather than a typed label.
- Placement measures read `fact_placement`; they do not recompute trailing windows in DAX.
- Format strings: percentages one decimal place, points as "+0.0" with the sign, cost index two decimals, counts with thousands separator.

## 5. Theme and layout

- Reuse the Branch review theme file from the data-answers repo if one exists, so the two dashboards read as one set; otherwise Claude Code writes `theme.json` here with the same values. Palette: his marine blue as the main data colour, one amber accent used only for the "attention" state (a Not yet working verdict, the Finance gap, a team below baseline), neutral greys for context, white panels on a light page background.
- No coloured side-accent bars, no shadows, no template chrome. Every repeated element on a page shares one size; bars in a row of small multiples share one scale.
- Text is grouped, with visible space between groups, and a caption sits directly on the number or chart it labels, as a smaller grey line. The spacing is fixed in `scripts/pbir.py` (panel padding 12 across and 6 down, 10 between groups, 0 from a caption to its number, 16 between panels in a row, 4 between page rows) and checked on every page.
- From page 1 (10 Nov 2026), on every page: nothing scrolls; a data label never touches or overlaps a bar; a legend shows every entry in full; charts before tables, and a table only when its content is text; every CHECK.md question for the page is answerable from what is visible, without hovering. `scripts/pbir.py` checks each of these it can measure before a page is written.
- Page size 16:9. Each page has a header strip: page title, the frame question it answers (pages 2 to 5), "Read from" the source tables, and the period ("Week 1 to Week 24, six check-ins"). Body text and footnotes in the theme font; key words in the header bold.
- At most four visuals in the body of each page.
- Page navigation: a left or top button strip with the six page names, the current page highlighted, so a reader can step through at their own pace.

## 6. Pages

### Page 0: Rollout review (front, sponsor)
- Header line: Period, headcount, seats assigned, seats active in Week 24.
- Four tiles in one row, equal size, one per stage (Foundation, Execution, Refinement, Scale). Each tile: the stage name, its FRAME-04 question in one line, the headline figure large, verdict word, trend arrow beside it (up, flat, down, or "No comparison yet"), threshold printed small, and a 5-point sparkline across months 2 to 6. The rule, the same for all four, in one line under the tile row (approved on page 0, 10 Nov 2026).
- Stage split: one stacked bar per team, On the ground, At the gate, In the air by source placement, latest count beside the team's baseline count.
- Moved up since the last count: one number, with Seats arrived as a separate smaller number beside it, never summed.

### Page 1: Where people sit (FRAME-01)
- Nine checkpoints as small multiples, one bar chart per team, one scale, with a toggle (bookmark or slicer) between check-in placement and source placement.
- The gap per team: higher, level, lower as three counts.
- Movement between the two latest counts: up, held, down per team.
- Largest group per team with its lever text from `dim_checkpoint_source[lever]`.

### Page 2: Foundation
Read from the question log, the usage dashboards and the library's records.
- Uses ranked by how often they come up, with a month slicer so the month 1 against month 6 change is visible.
- Share of library items with answer_key_first true.
- Share of requests matched to a tested prompt that already exists (the Foundation headline).
- Usage baseline by team (team-relative, from measures.md).

### Page 3: Execution
Read from the usage dashboards, the question log and the run log.
- First use within two weeks of a training session.
- Repeat use within 30 days (the Execution headline), by month.
- Recurring questions covered by a tested prompt.
- Tested prompts passing their cases, by item.

### Page 4: Refinement
Read from the run log and the library's records.
- Tested prompts that pass on the smaller model (the Refinement headline).
- Cost per use: median tokens per run by item, standard beside smaller, and the cost index.
- Prompts retired or merged by month, with merged_into shown.

### Page 5: Scale
Read from the question log and the usage dashboards, with the check-in supplying people's own words.
- Impact in people's own words: check-in question 5 answers counted per team.
- Uses taken up beyond the first team: items with runs from two or more teams, and the week the second team started.
- Share of people In the air against the team's baseline month (the Scale headline), per team.

## 7. Build loop

1. Claude Code writes `measures.dax`, `theme.json`, `data/dim_threshold.csv`, and `BUILD-STEPS.md` (the data load and model steps, then one section per page).
2. Megat loads data and model on the PC, sends a screenshot of the model view. Claude Code checks relationships against section 3 before any measure is created.
3. Measures go from `measures.dax` into the model files (section 4). `measures.dax` stays the only source for measures.
4. Pages are written one at a time, in page order, by `scripts/pageN_pbir.py`. A page is fixed and approved before the next one starts.
5. Before every push the page script checks its own layout and refuses to write the page if any check fails: every visual inside 1280 by 720; nothing overlapping except a panel and the pieces on it; repeated elements sharing one exact size; no chart smaller than Desktop can draw; the spacing in section 5 (groups, captions, panels in a row sharing one top edge and height); every text box tall enough for its text and no taller than it needs; every format setting name known (step 6).
6. A format setting name is never guessed. It comes from Megat's own files (Desktop wrote it), from the published schema at the `$schema` URL in each visual.json, or from a pattern Megat gives. Anything not from his files is marked unconfirmed and listed with the push. Only when a screenshot shows an unconfirmed name did not take does Claude Code ask for one visual formatted by hand, and read the name from its file.
7. With every push, Claude Code gives the figures the page should show, from check.py or the CSVs, so the screen can be compared against them.
8. The project is committed and pushed after each approved page. The Checks page stays hidden until publish.

## 8. The check

- When all six pages are approved, Claude Code fills the "matched" column in CHECK.md from Megat's screenshots, question by question: for each of the eighteen questions, the figure read from the named page with the filter state the question implies (the whole period unless a month or team is named), as Yes with the figure, or No with what the visual showed. Megat confirms each row. Where a screenshot does not show the figure, Claude Code names the page and filter state to screenshot.
- Watch question 7: the whole-period share and the month 6 Foundation tile both round to 49.5%, so confirm the count (385 of 778) rather than the percentage alone.
- Any No is fixed in the measure or the visual, never in CHECK.md, and the check is rerun for that question.
- The final count (for example 18 of 18) is written at the top of CHECK.md and committed. That count is the figure the site page carries.

## 9. Publish

- Publish to My Workspace on the existing free licence, then File, Embed report, Publish to web, as for Branch review. Record the embed URL in a `PUBLISH.md` in the repo (URL only, no date).
- Open the public link in a private browser window and read every page once more before it goes anywhere.

## 10. After publish (separate session, site folder)

- Dashboards page entry for Rollout review beside Branch review: visual first, the supporting record (check count, repo link, the four source tables and FRAME-04) folded behind a button, the same pattern as Branch review.
- Cross-link from the Frames page (FRAME-04) to the dashboard, and from the dashboard entry back to Frames.
- The data tour gains a stop at this dashboard only when Megat says so.

## 11. Kept out

- Calendar dates on any visual or axis
- Any currency
- Person names or per-person views; team is the lowest grain shown
- A blended fluency or maturity score
- Screen recordings; the published report and the check record stand on their own
