#!/usr/bin/env python3
"""Write the Notes page (the last tab) into the Power BI project's report files.

    python3 scripts/page6_pbir.py

Round 7: everything the pages no longer say in their headers and panels: the sources per
page, what each measure means, the thresholds and how a stage reads, which controls drive
which panels, the shading rules, and that cost is shown in tokens. The definitions are the
measures.md definitions in plain words, without the source tables' column names.
"""
from __future__ import annotations

import math

from pbir import (
    INK, INK_SOFT, Page, header, panel, pt, set_page_order, text_height, textbox,
    BODY_END, HEADER_BODY_Y_NO_QUESTION,
)

PAGE = "a7c3e5f9b1d2c4e6f8a0"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", "d4e9f2a6b8c1d3e5f7a9",
         "e5a1b3c7d9f2e4a6b8c0", "f6b2c4d8e1a3f5b7c9d1", PAGE]

LEFT = (16, 760)
RIGHT = (792, 472)

DEFINITIONS = [
    ("Requests matched to a tested prompt that already exists",
     "Questions answered by pointing the asker to a prompt in the library, over all questions logged."),
    ("Repeat use within 30 days",
     "People active again within 30 days of their first active week, over people whose first active week "
     "began at least 30 days before the check-in."),
    ("Tested prompts that pass on a smaller model",
     "Prompts whose latest run on the smaller model matched every test case. The front page shows them as a "
     "share of the prompts live at the check-in."),
    ("Share of people in the air against the baseline",
     "People the sources place at Takeoff, Above the clouds or Frequent flyer, as a share of the team, at Month 6 "
     "against the team's baseline month: the first check-in after its seats arrived. The change is in points."),
    ("People at each checkpoint",
     "People at each of the nine checkpoints in the month picked, by their own check-in answer or by what the "
     "sources show."),
    ("The gap", "Each person's check-in checkpoint against their source checkpoint: higher, level or lower."),
    ("Moved up, and movement",
     "People seated at both counts whose source checkpoint rose, held or fell between the previous count and "
     "this one. Seats arrived over the same month are counted apart, never added in."),
    ("Largest group", "The checkpoint holding the most people in each team, with the lever written for it. "
     "A tie goes to the earlier checkpoint."),
    ("Uses logged and ranked",
     "Questions in the question log, by use. Matched means the asker was pointed to a tested prompt."),
    ("Prompts tested against an answer key written first",
     "Prompts whose answer key was written before they were tested, over all prompts in the library."),
    ("Usage baseline by team",
     "The team's weekly active share, averaged over the four weeks from the week its seats arrived."),
    ("First use within two weeks of training",
     "Attendees who ran the prompt shown in their session that week or the next, over all attendees."),
    ("Recurring questions covered by a tested prompt",
     "Questions marked as recurring whose use had a live prompt in the library the week they were asked, "
     "over all recurring questions."),
    ("Tested prompts passing their cases",
     "Prompts live at the check-in whose latest run on the standard model matched every test case, over all "
     "live prompts."),
    ("Cost per use and the cost index",
     "Median tokens per test run on each model. The cost index is the standard model's median over the "
     "smaller model's."),
    ("Prompts retired or merged",
     "Prompts retired or merged into another, counted in the check-in month of the change."),
    ("Impact in people's own words",
     "Answers at the Month 6 check-in to \"If AI disappeared from your work tomorrow, what would change?\", "
     "by team."),
    ("Uses taken up beyond the first team",
     "Prompts run by two or more teams, and the week a team other than the one that made it first ran each."),
]

SOURCES = [
    ("Rollout review", "the question log, the usage dashboards, the library's records, the run log and the check-in"),
    ("Where people sit", "the check-in, the usage dashboards, the library's records and the question log"),
    ("Foundation", "the question log, the usage dashboards and the library's records"),
    ("Execution", "the usage dashboards, the question log and the run log"),
    ("Refinement", "the run log and the library's records"),
    ("Scale", "the question log, the usage dashboards and the check-in"),
]

THRESHOLDS = [
    ("Foundation", "Working at 40% or more."),
    ("Execution", "Working at 60% or more."),
    ("Refinement", "Working at 50% or more."),
    ("Scale", "Working at 10 points or more above each team's baseline."),
    ("How a stage reads", "Working when the month's figure meets its threshold. The trend compares the month "
     "with two check-ins earlier: up, down, or flat within 1 point; no comparison before then. The front page "
     "lines run from Month 2 to Month 6. The thresholds are illustrative; a programme sets its own."),
]

CONTROLS = [
    ("Where people sit", "Placement switches People at each checkpoint and Largest group between source and "
     "check-in placement. Month sets every panel on the page."),
    ("Execution", "Team sets every panel except Tested prompts passing their cases."),
    ("Shading", "On Where people sit, a cell is the team's share at that checkpoint, white at none to marine at "
     "60% or more. On Execution, a cell is recurring questions, white at none to marine at 20 or more."),
    ("Cost", "Cost is shown in tokens. A programme would apply its own price per model."),
]


def entries(items: list[tuple[str, str]]) -> dict:
    return textbox([[(name + ". ", pt(9, bold=True, color=INK)), (text, pt(9, color=INK_SOFT))]
                     for name, text in items])


def notes_panel(p: Page, key: str, x: int, y: int, w: int, title: str, items) -> int:
    """A panel sized to its text; returns its bottom edge."""
    body = entries(items)
    text_h = math.ceil(text_height(body, w - 24)) + 1
    h = 6 + 20 + 10 + text_h + 4
    pan = f"p6_{key}_panel"
    p.add(pan, (x, y, w, h), panel(), z=2000)
    p.add(f"p6_{key}_title", (x + 12, y + 6, w - 24, 20), textbox([[(title, pt(10, bold=True, color=INK))]]),
          on=pan, group="t")
    p.add(f"p6_{key}_text", (x + 12, y + 36, w - 24, text_h), body, on=pan, group="b")
    return y + h


def build() -> Page:
    p = Page(PAGE, "Notes")
    header(p, "p6", "Notes", None, "Sources, definitions, thresholds and controls for the six pages",
           "Week 1 to Week 24, six check-ins")
    y0 = HEADER_BODY_Y_NO_QUESTION
    notes_panel(p, "definitions", LEFT[0], y0, LEFT[1], "What each measure means", DEFINITIONS)
    y = notes_panel(p, "sources", RIGHT[0], y0, RIGHT[1], "Read from, by page", SOURCES)
    y = notes_panel(p, "thresholds", RIGHT[0], y + 4, RIGHT[1], "Thresholds, and how a stage reads", THRESHOLDS)
    notes_panel(p, "controls", RIGHT[0], y + 4, RIGHT[1], "Controls, shading and cost", CONTROLS)
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
