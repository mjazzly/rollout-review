#!/usr/bin/env python3
"""Write page 1 (Where people sit, FRAME-01) into the Power BI project's report files.

    python3 scripts/page1_pbir.py

Round 3 (Megat, 10 Nov 2026), nothing on the page scrolls:
- top, full width: a matrix, teams by the nine checkpoints under their stage names, counts
  shaded by the team's share at each checkpoint; follows the placement toggle and month;
- bottom row, one top edge and height: the gap (higher, level, lower per team), movement
  (up and down per team, seats arrived apart), and the largest group with its lever.
A row of month buttons (Month 6 to start) lets CHECK.md question 6 (Month 3 to Month 4) be read
on the page. Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    AMBER, GREY, INK, INK_SOFT, MARINE, MATRIX_COLUMN_PAD, OFF, PALE, NO_FRAME, Page, caption,
    colour, column, header, lit, measure_colour, panel, proj_column, proj_measure, pt, button_slicer,
    BODY_END, CONTROL_H, CONTROL_Y, GAP, MARGIN, PAGE_W,
    set_page_order, table_height, table_width, text, textbox, value_card, wrapped_lines, TEXT_INSET,
)

PAGE = "b7e4c2a91d3f5e6a8c10"
PAGE0 = "93ede836331e460c840c"

TEAMS = ("Consulting", "Finance", "Legal", "Operations", "People", "Technology")
STAGE_NAMES = ("On the ground", "At the gate", "In the air")

# ---------------------------------------------------------------- header strip
# Round 8: both controls are rows of buttons, 40 px tall (30 clipped the toggle); the month's
# six buttons at the right, the placement toggle GAP to their left.
MONTH_BUTTON_W = 72
MONTH = (PAGE_W - MARGIN - 6 * MONTH_BUTTON_W, CONTROL_Y, 6 * MONTH_BUTTON_W, CONTROL_H)
TOGGLE = (MONTH[0] - GAP - 180, CONTROL_Y, 180, CONTROL_H)

# ---------------------------------------------------------------- body
BODY_Y = CONTROL_Y + CONTROL_H + GAP
TEAM_COL, CP_COL = 120, 116            # matrix column widths: team, then each checkpoint
# Round 9: the stage names on the title's row, each over its three checkpoints from the second
# (so the title, "People at each checkpoint", ends before the first); the matrix right under them.
MATRIX_H = 28 + 216 + 4
MATRIX_PANEL = (16, BODY_Y, 1248, MATRIX_H)
BOTTOM_Y = MATRIX_PANEL[1] + MATRIX_PANEL[3] + GAP
BOTTOM_H = BODY_END - BOTTOM_Y
# Round 7: the gap is 422 wide so Finance's 13 gets 20 px of bar (it overflows its segment).
# Round 8: movement narrows to 210 and the lever table widens to 140 for the largest group, so
# only Legal's lever wraps and the table fits the shorter row.
GAP_PANEL = (16, BOTTOM_Y, 422, BOTTOM_H)
MOVE_PANEL = (GAP_PANEL[0] + GAP_PANEL[2] + GAP, BOTTOM_Y, 210, BOTTOM_H)
LARGEST_PANEL = (MOVE_PANEL[0] + MOVE_PANEL[2] + GAP, BOTTOM_Y, 1264 - (MOVE_PANEL[0] + MOVE_PANEL[2] + GAP), BOTTOM_H)
LARGEST_COLS = (80, 140, 292)          # team; largest group with its people; lever

# The thinnest gap segment at Month 6: Finance, lower, 13 of 200 (scripts/page1_figures.py)
GAP_MIN_SHARE = 13 / 200
# The largest group and its lever at Month 6, under either placement (page1_figures.py);
# the table is sized for these to wrap
LARGEST = {
    "Consulting": ("Takeoff, 174", "A second task, and a place to share what works"),
    "Finance": ("Waiting to board, 112", "One recurring task tied to a day of the week"),
    "Legal": ("Ticket held, 84", "A first task done side by side with someone who already uses AI"),
    "Operations": ("Boarding, 95", "Make that recurring task part of their routine"),
    "People": ("Takeoff, 37", "A second task, and a place to share what works"),
    "Technology": ("Takeoff, 101", "A second task, and a place to share what works"),
}


def sort_by_team() -> dict:
    return {"sort": [{"field": column("dim_team", "team"), "direction": "Ascending"}], "isDefaultSort": False}


def series_colour(measure_name: str, hex_: str) -> dict:
    # Branch review's pattern: one dataPoint per measure, picked by its queryRef
    return {"properties": {"fill": colour(hex_)}, "selector": {"metadata": f"_Measures.{measure_name}"}}


def matrix() -> dict:
    cell = "_Measures.People at checkpoint in grid"
    return {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": {"projections": [proj_column("dim_team", "team", active=True, display="Team")]},
                "Columns": {"projections": [proj_column("dim_checkpoint", "checkpoint", active=True)]},
                "Values": {"projections": [proj_measure("People at checkpoint in grid", "People")]},
            },
            "sortDefinition": sort_by_team(),
        },
        "objects": {
            "subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}],
            "values": [{"properties": {"backColor": measure_colour("Checkpoint shade"),
                                       "fontColor": measure_colour("Checkpoint text colour")},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": cell}}],
            "columnWidth": [
                {"properties": {"value": lit(f"{TEAM_COL}D")}, "selector": {"metadata": "dim_team.team"}},
                {"properties": {"value": lit(f"{CP_COL}D")}, "selector": {"metadata": cell}},
            ],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def gap_chart() -> dict:
    # Round 4: a stacked bar of each team's shares (higher, level, lower add to 1, so every
    # bar runs full width and Finance's 13 has room), labelled with the counts: the share
    # measures carry a dynamic format string that shows the count (measures.dax).
    series = (("Gap higher share", "Higher", AMBER), ("Gap level share", "Level", PALE),
              ("Gap lower share", "Lower", GREY))
    return {
        "visualType": "barChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
                "Y": {"projections": [proj_measure(m, d) for m, d, _ in series]},
            },
            "sortDefinition": sort_by_team(),
        },
        "objects": {
            "dataPoint": [series_colour(m, c) for m, _, c in series],
            # round 8: dark labels on the pale Level segment, white (the default) on the others
            "labels": [{"properties": {"show": lit("true"), "labelOverflow": lit("true")}},
                       {"properties": {"color": colour(INK)}, "selector": {"metadata": "_Measures.Gap level share"}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit("1D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}], "subTitle": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def movement_chart() -> dict:
    series = (("Movement up", "Up", MARINE), ("Movement down", "Down", GREY))
    return {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
                "Y": {"projections": [proj_measure(m, d) for m, d, _ in series]},
            },
            "sortDefinition": sort_by_team(),
        },
        "objects": {
            "dataPoint": [series_colour(m, c) for m, _, c in series],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            # thicker bars: 10% between teams, so each bar is taller than its label
            "categoryAxis": [{"properties": {"show": lit("true"), "innerPadding": lit("10L")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}], "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def legend(items: tuple[tuple[str, str], ...]) -> dict:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("  " if n < len(items) - 1 else ""),
                                            pt(9, color=INK_SOFT))]
    return textbox([runs])


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def heading_with_note(s: str, note: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK)), (" · " + note, pt(9, color=INK_SOFT))]])


def subtitle(s: str) -> dict:  # noqa: D401
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def build() -> Page:
    p = Page(PAGE, "Where people sit", number=1)
    header(p, "p1", "Where people sit", None,
           "Read from the check-in, the usage dashboards, the library's records and the question log",
           "Week 1 to Week 24, six check-ins")
    p.add("p1_toggle", TOGGLE, button_slicer("placement_toggle", "placement", "Placement", "Source"),
          buttons=2, longest_button="Check-in")
    p.add("p1_month", MONTH, button_slicer("dim_month", "month_label", "Month", "Month 6", buttons=6),
          buttons=6, longest_button="Month 6")

    # ---- the matrix: teams by checkpoints, stage names over their three checkpoints
    x, y, w, h = MATRIX_PANEL
    pan = "p1_matrix_panel"
    p.add(pan, MATRIX_PANEL, panel(), z=2000)
    p.add("p1_matrix_title", (x + 12, y + 6, TEAM_COL + CP_COL, 20), heading("People at each checkpoint"),
          on=pan, group="t")
    for k, stage in enumerate(STAGE_NAMES):
        p.add(f"p1_stage_{k + 1}", (x + 12 + TEAM_COL + k * 3 * CP_COL + CP_COL, y + 6, 2 * CP_COL, 20),
              heading(stage), on=pan, group="t", same="stage name")
    p.add("p1_matrix", (x + 12, y + 28, w - 24, h - 32), matrix(), on=pan, group="m",
          need_w=table_width([TEAM_COL] + [CP_COL] * 9, MATRIX_COLUMN_PAD),
          need_h=table_height([1] * 6))

    # ---- the gap: title; subtitle, legend top right; the chart
    x, y, w, h = GAP_PANEL
    pan, inner = "p1_gap_panel", w - 24
    p.add(pan, GAP_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_gap_title", (x + 12, y + 6, inner, 20), heading("The gap: check-in against source"),
          on=pan, group="t")
    p.add("p1_gap_sub", (x + 12, y + 26, inner - 170, 18), subtitle("People, the month picked"),
          on=pan, group="t", kind="subtitle")
    p.add("p1_gap_legend", (x + 12 + inner - 170, y + 26, 170, 18),
          legend((("Higher", AMBER), ("Level", PALE), ("Lower", GREY))), on=pan, group="t", legend=True)
    p.add("p1_gap_chart", (x + 12, y + 46, inner, h - 50), gap_chart(), on=pan, group="c", categories=6,
          label_min_share=GAP_MIN_SHARE, longest_label="13")

    # ---- movement: title; subtitle, legend top right; the chart; under it seats arrived, apart
    x, y, w, h = MOVE_PANEL
    pan, inner = "p1_move_panel", w - 24
    p.add(pan, MOVE_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_move_title", (x + 12, y + 6, inner, 20), heading("Movement since last count"),
          on=pan, group="t")
    # round 8: seats arrived on the subtitle row, so the bars keep room for their labels
    p.add("p1_seats_line", (x + 12, y + 26, inner - 90, 20), value_card("Seats arrived line", 9, colour(INK_SOFT)),
          on=pan, group="t", longest_value="0 seats arrived")
    p.add("p1_move_legend", (x + 12 + inner - 90, y + 26, 90, 18), legend((("Up", MARINE), ("Down", GREY))),
          on=pan, group="t", legend=True)
    p.add("p1_move_chart", (x + 12, y + 48, inner, h - 52), movement_chart(), on=pan, group="c",
          categories=6, series=2)

    # ---- largest group and its lever: text, so a table
    x, y, w, h = LARGEST_PANEL
    pan, inner = "p1_largest_panel", w - 24
    p.add(pan, LARGEST_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_largest_title", (x + 12, y + 6, inner, 20), heading("Largest group per team, and its lever"),
          on=pan, group="t")
    team_w, group_w, lever_w = LARGEST_COLS
    # a table cell's text area is its column width (wrapped_lines takes off TEXT_INSET each side)
    lines = [max(wrapped_lines([(g, pt(10))], group_w + 2 * TEXT_INSET),
                 wrapped_lines([(l, pt(10))], lever_w + 2 * TEXT_INSET))
             for g, l in LARGEST.values()]
    cols = [(proj_column("dim_team", "team", display="Team"), team_w),
            (proj_measure("Largest group with people", "Largest group"), group_w),
            (proj_measure("Largest group lever", "Lever"), lever_w)]
    p.add("p1_largest_table", (x + 12, y + 28, inner, h - 32), {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [c for c, _ in cols]}},
                  "sortDefinition": sort_by_team()},
        "objects": {
            "total": [{"properties": {"totals": lit("false")}}],
            "columnWidth": [{"properties": {"value": lit(f"{wd}D")}, "selector": {"metadata": c["queryRef"]}}
                            for c, wd in cols],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }, on=pan, group="c", need_w=table_width(list(LARGEST_COLS)), need_h=table_height(lines))

    p.answers = {
        4: [("p1_gap_chart", "Gap higher share"), ("p1_gap_chart", "Gap level share"),
            ("p1_gap_chart", "Gap lower share")],
        5: [("p1_largest_table", "Largest group with people"), ("p1_largest_table", "Largest group lever")],
        6: [("p1_move_chart", "Movement up"), ("p1_seats_line", "Seats arrived line")],
    }
    return p


if __name__ == "__main__":
    build().write()
    set_page_order([PAGE0, PAGE])
