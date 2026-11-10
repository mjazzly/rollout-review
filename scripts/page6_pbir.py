#!/usr/bin/env python3
"""Write the Notes page (the last tab) into the Power BI project's report files.

    python3 scripts/page6_pbir.py

Round 7: everything the pages no longer say in their headers and panels: the sources per
page, what each measure means, the thresholds and how a stage reads, which controls drive
which panels, the shading rules, and that cost is shown in tokens. The definitions are the
measures.md definitions in plain words, without the source tables' column names.
Round 8: every line starts with its key term in bold: each entry is one line (checked here with
room to spare). Round 9: no scrollbars: heights use the line spacing Desktop drew (NOTES_LINE_PX);
"Read from, by page" is gone (each page's foot says it); the page names sit in their own column
beside the definitions, line for line; thresholds and controls side by side under them.
"""
from __future__ import annotations

import math

from pbir import (
    INK, INK_SOFT, MARINE, NOTES_LINE_PX, Page, header, notes_height, panel, pt, set_page_order, textbox,
    wrapped_lines, BODY_END, GAP, body_top,
)

PAGE = "a7c3e5f9b1d2c4e6f8a0"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", "d4e9f2a6b8c1d3e5f7a9",
         "e5a1b3c7d9f2e4a6b8c0", "f6b2c4d8e1a3f5b7c9d1", PAGE]
ONE_LINE_SPARE = 1.08     # an entry fits one line with 8% to spare

PAGE_COL = 120            # the definitions' page names, in their own column

# page -> [(term, text)]
DEFINITIONS = [
    ("Rollout review", [
        ("Stage figures", "Each is defined under its page below; moved up is under Where people sit."),
    ]),
    ("Where people sit", [
        ("People at each checkpoint", "People at each of the nine checkpoints in the month picked, by their own "
         "check-in answer or by what the sources show."),
        ("The gap", "Each person's check-in checkpoint against their source checkpoint: higher, level or lower."),
        ("Moved up, and movement", "People seated at both counts whose source checkpoint rose, held or fell since "
         "the previous count; seats arrived are counted apart."),
        ("Largest group", "The checkpoint holding the most people in each team, with the lever written for it; a "
         "tie goes to the earlier checkpoint."),
    ]),
    ("Foundation", [
        ("Uses logged and ranked", "Questions in the question log, by use; matched means the asker was pointed to "
         "a tested prompt."),
        ("Requests matched to a tested prompt that already exists", "Questions answered by pointing the asker to a "
         "library prompt, over all questions."),
        ("Prompts tested against an answer key written first", "Prompts whose answer key was written before they "
         "were tested, over all prompts."),
        ("Usage baseline by team", "The team's weekly active share, averaged over the four weeks from the week its "
         "seats arrived."),
    ]),
    ("Execution", [
        ("First use within two weeks of training", "Attendees who ran the prompt shown that week or the next, over "
         "all attendees. Legal's 0.0% is real: one session, 19 attendees."),
        ("Repeat use within 30 days", "People active again within 30 days of their first active week, over people "
         "who began 30 days or more before the check-in."),
        ("Recurring questions covered by a tested prompt", "Recurring questions whose use had a live prompt the "
         "week they were asked, over all recurring questions."),
        ("Tested prompts passing their cases", "Live prompts whose latest standard-model run matched every test "
         "case, over all live prompts."),
    ]),
    ("Refinement", [
        ("Tested prompts that pass on a smaller model", "Live prompts whose latest smaller-model run matched every "
         "test case; each column shows its cases matched."),
        ("Cost per use and the cost index", "Median tokens per test run on each model; the index is the standard "
         "model's median over the smaller model's."),
        ("Prompts retired or merged", "Prompts retired or merged into another, counted in the check-in month of the "
         "change."),
    ]),
    ("Scale", [
        ("Share of people in the air against the baseline", "People the sources place at Takeoff or above, as a "
         "share of the team, Month 6 against its baseline month; the change in points."),
        ("Impact in people's own words", "Month 6 answers to \"If AI disappeared from your work tomorrow, what would "
         "change?\", by team."),
        ("Uses taken up beyond the first team", "Prompts run by two or more teams; the week another team first ran "
         "each, and the runs by other teams."),
    ]),
]

THRESHOLDS = [
    ("Foundation", "Working at 40% or more"),
    ("Execution", "Working at 60% or more"),
    ("Refinement", "Working at 50% or more"),
    ("Scale", "Working at 10 points or more above each team's baseline"),
    ("Trend", "The month against two check-ins earlier: up, down, or flat within 1 point"),
    ("Illustrative", "A programme sets its own thresholds; front-page lines run Month 2 to Month 6"),
]

CONTROLS = [
    ("Placement", "Source or check-in placement, for the grid and the largest group"),
    ("Month", "Sets every panel on Where people sit; Month 6 to start"),
    ("Team", "Sets every Execution panel but tested prompts passing; none picked shows every team"),
    ("Shading", "Darker is more: marine at 60% of a team, or at 20 recurring questions"),
    ("Sources", "Each page's foot names what it reads from"),
    ("Cost", "Shown in tokens; a programme applies its own price per model"),
]


def entries(items) -> dict:
    return textbox([[(name + ". ", pt(9, bold=True, color=INK)), (text, pt(9, color=INK_SOFT))]
                    for name, text in items])


def one_line(body: dict, width: int) -> None:
    for para in body["objects"]["general"][0]["properties"]["paragraphs"]:
        runs = [(r["value"], r.get("textStyle")) for r in para["textRuns"]]
        if wrapped_lines(runs, int(width / ONE_LINE_SPARE)) > 1:
            raise SystemExit(f"Notes: '{runs[0][0]}' does not fit on one line in {width} px with room to spare")


def notes_panel(p: Page, key: str, box, title: str, columns, row=None) -> None:
    """A panel holding its text: columns of one-line 9pt paragraphs, side by side, line for line."""
    x, y, w, h = box
    pan = f"p6_{key}_panel"
    p.add(pan, box, panel(), z=2000, row=row)
    p.add(f"p6_{key}_title", (x + 12, y + 6, w - 24, 20), textbox([[(title, pt(10, bold=True, color=INK))]]),
          on=pan, group="t")
    cx = x + 12
    for n, (cw, body) in enumerate(columns):
        cw = cw or x + w - 12 - cx
        one_line(body, cw)
        text_h = math.ceil(notes_height(body, cw))
        if y + 36 + text_h > y + h - 4:
            raise SystemExit(f"Notes: {key} needs {36 + text_h + 4} px, has {h}")
        p.add(f"p6_{key}_text{n}", (cx, y + 36, cw, text_h), body, on=pan, group="b", kind="notes")
        cx += cw


def build() -> Page:
    p = Page(PAGE, "Notes")
    header(p, "p6", "Notes", None,
           "Read from the question log, the usage dashboards, the library's records, the run log and the check-in",
           "Week 1 to Week 24, six check-ins")
    y0 = body_top(p)
    pages, terms = [], []
    for page, items in DEFINITIONS:
        for k, item in enumerate(items):
            pages.append([(page if k == 0 else "\u00a0", pt(9, bold=True, color=MARINE))])
            terms.append(item)
    defs_h = 36 + len(terms) * NOTES_LINE_PX + 4 + 4
    notes_panel(p, "definitions", (16, y0, 1248, defs_h), "What each measure means, by page",
                [(PAGE_COL, textbox(pages)), (0, entries(terms))])
    y = y0 + defs_h + GAP
    w = (1248 - GAP) // 2
    for i, (key, title, items) in enumerate((("thresholds", "Thresholds, and how a stage reads", THRESHOLDS),
                                             ("controls", "Controls, shading, sources and cost", CONTROLS))):
        x = 16 + i * (w + GAP)
        notes_panel(p, key, (x, y, w if i == 0 else 1264 - x, BODY_END - y), title, [(0, entries(items))],
                    row="notes")
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
