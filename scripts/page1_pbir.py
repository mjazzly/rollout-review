#!/usr/bin/env python3
"""Write page 1 (Where people sit, FRAME-01) into the Power BI project's report files.

    python3 scripts/page1_pbir.py

Round 3 (Megat, 10 Nov 2026), nothing on the page scrolls:
- top, full width: a matrix, teams by the nine checkpoints under their stage names, counts
  shaded by the team's share at each checkpoint; follows the placement toggle and month;
- bottom row, one top edge and height: the gap (higher, level, lower per team), movement
  (up and down per team, seats arrived apart), and the largest group with its lever.
A month slicer (Month 6 to start) lets CHECK.md question 6 (Month 3 to Month 4) be read
on the page. Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    AMBER, GREY, INK, INK_SOFT, MARINE, MATRIX_COLUMN_PAD, OFF, PALE, NO_FRAME, Page, caption,
    colour, column, header, lit, measure_colour, panel, proj_column, proj_measure, pt,
    set_page_order, table_height, table_width, text, textbox, value_card, wrapped_lines,
)

PAGE = "b7e4c2a91d3f5e6a8c10"
PAGE0 = "93ede836331e460c840c"

TEAMS = ("Consulting", "Finance", "Legal", "Operations", "People", "Technology")
STAGE_NAMES = ("On the ground", "At the gate", "In the air")

# ---------------------------------------------------------------- header strip
# pbir.header(): title, sources at the right of its row (left of the slicers), and the
# month note on the second line; the slicers span both header lines
TOGGLE = (944, 36, 188, 62)
MONTH = (1148, 36, 116, 62)

# ---------------------------------------------------------------- body
MATRIX_PANEL = (16, 102, 1248, 280)
TEAM_COL, CP_COL = 120, 116            # matrix column widths: team, then each checkpoint
BOTTOM_Y, BOTTOM_H = 386, 330
GAP_PANEL = (16, BOTTOM_Y, 352, BOTTOM_H)
MOVE_PANEL = (384, BOTTOM_Y, 274, BOTTOM_H)
LARGEST_PANEL = (674, BOTTOM_Y, 590, BOTTOM_H)
LARGEST_COLS = (90, 136, 292)          # team (no name breaks); largest group with its people; lever

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
    cell = "_Measures.People at checkpoint"
    return {
        "visualType": "pivotTable",
        "query": {
            "queryState": {
                "Rows": {"projections": [proj_column("dim_team", "team", active=True, display="Team")]},
                "Columns": {"projections": [proj_column("dim_checkpoint", "checkpoint", active=True)]},
                "Values": {"projections": [proj_measure("People at checkpoint")]},
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
            "labels": [{"properties": {"show": lit("true")}}],
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


def slicer(table: str, col: str, start: str, header: str, buttons: bool) -> dict:
    objects = {
        "data": [{"properties": {"mode": text("Basic" if buttons else "Dropdown")}}],
        "selection": [{"properties": {"singleSelect": lit("true"), "strictSingleSelect": lit("true")}}],
        "general": [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "f", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": col}}],
                "Values": [[{"Literal": {"Value": f"'{start}'"}}]]}}}]}}}}],
        "header": [{"properties": {"text": text(header)}}],
    }
    if buttons:
        objects["general"][0]["properties"]["orientation"] = lit("1D")   # horizontal: two buttons
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj_column(table, col, active=True)]}}},
        "objects": objects,
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


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def build() -> Page:
    p = Page(PAGE, "Where people sit", number=1)
    header(p, "p1", "Where people sit",
           "Read from the check-in, the usage dashboards, the library's records and the question log",
           "Week 1 to Week 24", question="Month 6 shown; pick another month at the top right",
           right=TOGGLE[0] - 16)
    p.add("p1_toggle", TOGGLE, slicer("placement_toggle", "placement", "Source", "Placement", buttons=True))
    p.add("p1_month", MONTH, slicer("dim_month", "month_label", "Month 6", "Month", buttons=False))
    p.awaiting["p1_toggle"] = ("the selected button in marine with white text: a Button slicer formatted "
                               "by hand (BUILD-STEPS section G, step 54)")

    # ---- the matrix: teams by checkpoints, stage names over their three checkpoints
    x, y, w, h = MATRIX_PANEL
    pan = "p1_matrix_panel"
    p.add(pan, MATRIX_PANEL, panel(), z=2000)
    p.add("p1_matrix_title", (x + 12, y + 6, w - 24, 20), heading_with_note(
        "People at each checkpoint, by team",
        "follows the placement toggle and the month · each cell is shaded by the team's share at that "
        "checkpoint, white at none to marine at 60% or more"), on=pan, group="t")
    for k, stage in enumerate(STAGE_NAMES):
        p.add(f"p1_stage_{k + 1}", (x + 12 + TEAM_COL + k * 3 * CP_COL, y + 36, 3 * CP_COL, 20),
              heading(stage), on=pan, group="m", same="stage name")
    p.add("p1_matrix", (x + 12, y + 56, w - 24, 220), matrix(), on=pan, group="m",
          need_w=table_width([TEAM_COL] + [CP_COL] * 9, MATRIX_COLUMN_PAD),
          need_h=table_height([1] * 6))

    # ---- the gap: title; subtitle and legend on one row; the chart
    x, y, w, h = GAP_PANEL
    pan, inner = "p1_gap_panel", w - 24
    p.add(pan, GAP_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_gap_title", (x + 12, y + 6, inner, 20), heading("The gap: check-in against source"),
          on=pan, group="t")
    p.add("p1_gap_sub", (x + 12, y + 26, 150, 18), subtitle("Month only, not the toggle"),
          on=pan, group="t")
    p.add("p1_gap_legend", (x + 12 + 150, y + 26, inner - 150, 18),
          legend((("Higher", AMBER), ("Level", PALE), ("Lower", GREY))), on=pan, group="t", legend=True)
    p.add("p1_gap_chart", (x + 12, y + 46, inner, h - 50), gap_chart(), on=pan, group="c", categories=6,
          label_min_share=GAP_MIN_SHARE)

    # ---- movement: title; subtitle and legend; the chart; seats arrived apart, at the bottom
    x, y, w, h = MOVE_PANEL
    pan, inner = "p1_move_panel", w - 24
    p.add(pan, MOVE_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_move_title", (x + 12, y + 6, inner, 20), heading("Movement since the previous count"),
          on=pan, group="t")
    p.add("p1_move_sub", (x + 12, y + 26, 150, 18), subtitle("Month only, not the toggle"),
          on=pan, group="t")
    p.add("p1_move_legend", (x + 12 + 150, y + 26, inner - 150, 18), legend((("Up", MARINE), ("Down", GREY))),
          on=pan, group="t", legend=True)
    chart_h = h - 6 - 38 - 2 - 10 - 23 - 4
    p.add("p1_move_chart", (x + 12, y + 46, inner, chart_h), movement_chart(), on=pan, group="c",
          categories=6, series=2)
    sy = y + 46 + chart_h + 10
    p.add("p1_seats_caption", (x + 12, sy, 150, 23),
          textbox([[("Seats arrived, all teams:", pt(9, color=INK_SOFT))]]), on=pan, group="s")
    p.add("p1_seats_figure", (x + 12 + 150, sy, 40, 23), value_card("Seats arrived", 10),
          on=pan, group="s")

    # ---- largest group and its lever: text, so a table
    x, y, w, h = LARGEST_PANEL
    pan, inner = "p1_largest_panel", w - 24
    p.add(pan, LARGEST_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_largest_title", (x + 12, y + 6, inner, 20),
          heading_with_note("Largest group per team, and its lever", "follows the placement toggle and the month"),
          on=pan, group="t")
    team_w, group_w, lever_w = LARGEST_COLS
    lines = [max(wrapped_lines([(g, pt(10))], group_w + 4), wrapped_lines([(l, pt(10))], lever_w + 4))
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
        6: [("p1_move_chart", "Movement up"), ("p1_seats_figure", "Seats arrived")],
    }
    return p


if __name__ == "__main__":
    build().write()
    set_page_order([PAGE0, PAGE])
