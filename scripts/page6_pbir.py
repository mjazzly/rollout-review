#!/usr/bin/env python3
"""Write the Notes page (the last tab) into the Power BI project's report files.

    python3 scripts/page6_pbir.py

Round 7: everything the pages no longer say in their headers and panels: the sources per
page, what each measure means, the thresholds and how a stage reads, which controls drive
which panels, the shading rules, and that cost is shown in tokens. The definitions are the
measures.md definitions in plain words, without the source tables' column names.
Round 8: no scrollbars, and every line starts with its key term in bold: each entry is one
line (checked here with room to spare), the definitions full width and grouped by page, the
other three panels side by side under them.
"""
from __future__ import annotations

import math

from pbir import (
    INK, INK_SOFT, MARINE, Page, header, panel, pt, set_page_order, text_height, textbox, wrapped_lines,
    BODY_END, GAP, body_top,
)

PAGE = "a7c3e5f9b1d2c4e6f8a0"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", "d4e9f2a6b8c1d3e5f7a9",
         "e5a1b3c7d9f2e4a6b8c0", "f6b2c4d8e1a3f5b7c9d1", PAGE]
ONE_LINE_SPARE = 1.08     # an entry fits one line with 8% to spare

# (term, text) entries; (page name, None) starts a group
DEFINITIONS = [
    ("Rollout review", "The four stage figures are defined under their pages; moved up is under Where people sit."),
    ("Where people sit", None),
    ("People at each checkpoint", "People at each of the nine checkpoints in the month picked, by their own "
     "check-in answer or by what the sources show."),
    ("The gap", "Each person's check-in checkpoint against their source checkpoint: higher, level or lower."),
    ("Moved up, and movement", "People seated at both counts whose source checkpoint rose, held or fell since "
     "the previous count; seats arrived in the month are counted apart."),
    ("Largest group", "The checkpoint holding the most people in each team, with the lever written for it; a tie "
     "goes to the earlier checkpoint."),
    ("Foundation", None),
    ("Uses logged and ranked", "Questions in the question log, by use; matched means the asker was pointed to a "
     "tested prompt."),
    ("Requests matched to a tested prompt that already exists", "Questions answered by pointing the asker to a "
     "prompt in the library, over all questions logged."),
    ("Prompts tested against an answer key written first", "Prompts whose answer key was written before they "
     "were tested, over all prompts in the library."),
    ("Usage baseline by team", "The team's weekly active share, averaged over the four weeks from the week its "
     "seats arrived."),
    ("Execution", None),
    ("First use within two weeks of training", "Attendees who ran the prompt shown in their session that week or "
     "the next, over all attendees. Legal's 0.0% is real: one session, 19 attendees."),
    ("Repeat use within 30 days", "People active again within 30 days of their first active week, over people "
     "whose first active week began 30 days or more before the check-in."),
    ("Recurring questions covered by a tested prompt", "Recurring questions whose use had a live prompt the week "
     "they were asked, over all recurring questions."),
    ("Tested prompts passing their cases", "Live prompts whose latest standard-model run matched every test case, "
     "over all live prompts."),
    ("Refinement", None),
    ("Tested prompts that pass on a smaller model", "Live prompts whose latest smaller-model run matched every "
     "test case; each column shows its cases matched."),
    ("Cost per use and the cost index", "Median tokens per test run on each model; the cost index is the "
     "standard model's median over the smaller model's."),
    ("Prompts retired or merged", "Prompts retired or merged into another, counted in the check-in month of the "
     "change."),
    ("Scale", None),
    ("Share of people in the air against the baseline", "People the sources place at Takeoff or above, as a share "
     "of the team, at Month 6 against the team's baseline month; the change in points."),
    ("Impact in people's own words", "Month 6 answers to \"If AI disappeared from your work tomorrow, what would "
     "change?\", by team."),
    ("Uses taken up beyond the first team", "Prompts run by two or more teams; the week another team first ran "
     "each, and the runs by other teams."),
]

SOURCES = [
    ("Rollout review", "All the sources below"),
    ("Where people sit", "Check-in, usage, library, question log"),
    ("Foundation", "Question log, usage, library"),
    ("Execution", "Usage, question log, run log"),
    ("Refinement", "Run log, library"),
    ("Scale", "Question log, usage, check-in"),
]

THRESHOLDS = [
    ("Foundation", "Working at 40% or more"),
    ("Execution", "Working at 60% or more"),
    ("Refinement", "Working at 50% or more"),
    ("Scale", "Working at 10 points or more above baseline"),
    ("Trend", "Against two check-ins earlier; flat within 1 point"),
    ("Illustrative", "A programme sets its own thresholds"),
]

CONTROLS = [
    ("Placement", "Source or check-in: grid and largest group"),
    ("Month", "Sets every panel on Where people sit"),
    ("Team", "Sets Execution; none picked shows every team"),
    ("Passing", "Tested prompts passing ignores the team"),
    ("Shading", "Darker is more; marine at 60%, or 20 questions"),
    ("Cost", "In tokens; a programme applies its own price per model"),
]


def entries(items) -> dict:
    paras = []
    for name, text in items:
        if text is None:
            paras.append([(name, pt(9, bold=True, color=MARINE))])
        else:
            paras.append([(name + ". ", pt(9, bold=True, color=INK)), (text, pt(9, color=INK_SOFT))])
    return textbox(paras)


def notes_panel(p: Page, key: str, x: int, y: int, w: int, h: int | None, title: str, items, row=None) -> int:
    """A panel holding its text; every entry one line, starting with its term in bold."""
    body = entries(items)
    tw = w - 24
    for para in body["objects"]["general"][0]["properties"]["paragraphs"]:
        runs = [(r["value"], r.get("textStyle")) for r in para["textRuns"]]
        if wrapped_lines(runs, int(tw / ONE_LINE_SPARE)) > 1:
            raise SystemExit(f"Notes: '{runs[0][0]}' does not fit on one line in {tw} px with room to spare")
    text_h = math.ceil(text_height(body, tw)) + 1
    need = 6 + 20 + 10 + text_h + 4
    h = h or need
    if h < need:
        raise SystemExit(f"Notes: {key} needs {need} px, has {h}")
    pan = f"p6_{key}_panel"
    p.add(pan, (x, y, w, h), panel(), z=2000, row=row)
    p.add(f"p6_{key}_title", (x + 12, y + 6, tw, 20), textbox([[(title, pt(10, bold=True, color=INK))]]),
          on=pan, group="t")
    p.add(f"p6_{key}_text", (x + 12, y + 36, tw, text_h), body, on=pan, group="b")
    return y + h


def build() -> Page:
    p = Page(PAGE, "Notes")
    header(p, "p6", "Notes", None,
           "Read from the question log, the usage dashboards, the library's records, the run log and the check-in",
           "Week 1 to Week 24, six check-ins")
    y0 = body_top(p)
    y = notes_panel(p, "definitions", 16, y0, 1248, None, "What each measure means, by page", DEFINITIONS)
    y += GAP
    h = BODY_END - y
    w = (1248 - 2 * GAP) // 3
    for i, (key, title, items) in enumerate((("sources", "Read from, by page", SOURCES),
                                             ("thresholds", "Thresholds, and how a stage reads", THRESHOLDS),
                                             ("controls", "Controls, shading and cost", CONTROLS))):
        x = 16 + i * (w + GAP)
        notes_panel(p, key, x, y, w if i < 2 else 1264 - x, h, title, items, row="notes")
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
