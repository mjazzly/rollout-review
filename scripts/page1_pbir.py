#!/usr/bin/env python3
"""Write page 1 (Where people sit, FRAME-01) into the Power BI project's report files.

    python3 scripts/page1_pbir.py

Round 2 design (Megat, 10 Nov 2026), nothing on the page scrolls:
- top, full width: a matrix, teams by the nine checkpoints under their stage names, counts
  shaded by the team's share at each checkpoint; follows the placement toggle;
- bottom row, one top edge and height: the gap (higher, level, lower per team), movement
  (up and down per team, seats arrived apart), and the largest group with its lever.
A month slicer (Month 6 to start) lets CHECK.md question 6 (Month 3 to Month 4) be read
on the page. Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    AMBER, GREY, INK, INK_SOFT, MARINE, OFF, PALE, NO_FRAME, Page, caption, colour, column,
    lit, measure_colour, navigator, panel, proj_column, proj_measure, pt, set_page_order,
    table_height, text, textbox, value_card, wrapped_lines, MATRIX_HEADER, TABLE_SLACK,
)

PAGE = "b7e4c2a91d3f5e6a8c10"
PAGE0 = "93ede836331e460c840c"

TEAMS = ("Consulting", "Finance", "Legal", "Operations", "People", "Technology")
STAGE_NAMES = ("On the ground", "At the gate", "In the air")

# ---------------------------------------------------------------- header strip
NAV = (16, 4, 1248, 32)
TITLE = (16, 36, 240, 34)
SOURCE = (16, 70, 836, 22)
TOGGLE = (868, 36, 248, 56)
MONTH = (1132, 36, 132, 56)

# ---------------------------------------------------------------- body
MATRIX_PANEL = (16, 96, 1248, 288)
TEAM_COL, CP_COL = 120, 116            # matrix column widths: team, then each checkpoint
BOTTOM_Y, BOTTOM_H = 388, 328
GAP_PANEL = (16, BOTTOM_Y, 300, BOTTOM_H)
MOVE_PANEL = (332, BOTTOM_Y, 300, BOTTOM_H)
LARGEST_PANEL = (648, BOTTOM_Y, 616, BOTTOM_H)
LARGEST_COLS = (("Team", 84), ("Largest group", 120), ("People", 60), ("Lever", 304))

# The levers of the checkpoints that are a team's largest group at Month 6, under either
# placement (scripts/page1_figures.py); the table is sized for them to wrap
LEVERS = {
    "Consulting": "A second task, and a place to share what works",
    "Finance": "One recurring task tied to a day of the week",
    "Legal": "A first task done side by side with someone who already uses AI",
    "Operations": "Make that recurring task part of their routine",
    "People": "A second task, and a place to share what works",
    "Technology": "A second task, and a place to share what works",
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
    series = (("Gap higher", "Higher", AMBER), ("Gap level", "Level", PALE), ("Gap lower", "Lower", GREY))
    return {
        "visualType": "hundredPercentStackedBarChart",
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
            "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
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
            "categoryAxis": [{"properties": {"show": lit("true")}}],
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


def legend(items: tuple[tuple[str, str], ...]) -> list:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("   " if n < len(items) - 1 else ""),
                                            pt(9, color=INK_SOFT))]
    return [runs]


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def build() -> Page:
    p = Page(PAGE, "Where people sit")
    p.add("p1_navigator", NAV, navigator(), z=0)
    p.add("p1_title", TITLE, textbox([[("Where people sit", pt(18, bold=True, color=INK))]]))
    p.add("p1_source", SOURCE, textbox([[
        ("Read from the check-in, the usage dashboards, the library's records and the question log · ",
         pt(10, color=INK_SOFT)),
        ("the month picked, Month 6 to start", pt(10, bold=True, color=INK_SOFT))]]))
    p.add("p1_toggle", TOGGLE, slicer("placement_toggle", "placement", "Source", "Placement", buttons=True))
    p.add("p1_month", MONTH, slicer("dim_month", "month_label", "Month 6", "Month", buttons=False))

    # ---- the matrix: teams by checkpoints, stage names over their three checkpoints
    x, y, w, h = MATRIX_PANEL
    pan = "p1_matrix_panel"
    p.add(pan, MATRIX_PANEL, panel(), z=2000)
    p.add("p1_matrix_title", (x + 12, y + 6, w - 24, 20), heading("People at each checkpoint, by team"),
          on=pan, group="t")
    p.add("p1_matrix_sub", (x + 12, y + 26, w - 24, 18), subtitle(
        "Follows the placement toggle and the month · each cell is shaded by the team's share at that "
        "checkpoint, white at none to marine at 60% or more"), on=pan, group="t")
    for k, stage in enumerate(STAGE_NAMES):
        p.add(f"p1_stage_{k + 1}", (x + 12 + TEAM_COL + k * 3 * CP_COL, y + 54, 3 * CP_COL, 20),
              heading(stage), on=pan, group="m", same="stage name")
    p.add("p1_matrix", (x + 12, y + 74, w - 24, 210), matrix(), on=pan, group="m",
          need_w=TEAM_COL + 9 * CP_COL + TABLE_SLACK, need_h=MATRIX_HEADER + 6 * 26)

    # ---- the gap
    x, y, w, h = GAP_PANEL
    pan, inner = "p1_gap_panel", w - 24
    p.add(pan, GAP_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_gap_title", (x + 12, y + 6, inner, 20), heading("The gap: check-in against source"),
          on=pan, group="t")
    p.add("p1_gap_sub", (x + 12, y + 26, inner, 18), subtitle("Follows the month, not the toggle"),
          on=pan, group="t")
    p.add("p1_gap_legend", (x + 12, y + 54, inner, 20),
          textbox(legend((("Higher", AMBER), ("Level", PALE), ("Lower", GREY)))), on=pan, group="c")
    p.add("p1_gap_chart", (x + 12, y + 74, inner, 246), gap_chart(), on=pan, group="c", categories=6)

    # ---- movement, with seats arrived apart
    x, y, w, h = MOVE_PANEL
    pan, inner = "p1_move_panel", w - 24
    p.add(pan, MOVE_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_move_title", (x + 12, y + 6, inner, 20), heading("Movement since the previous count"),
          on=pan, group="t")
    p.add("p1_move_sub", (x + 12, y + 26, 196, 18), subtitle("Follows the month, not the toggle"),
          on=pan, group="t")
    p.add("p1_move_legend", (x + 12 + 196, y + 26, 80, 18),
          textbox(legend((("Up", MARINE), ("Down", GREY)))), on=pan, group="t")
    p.add("p1_move_chart", (x + 12, y + 46, inner, 224), movement_chart(), on=pan, group="c", categories=6)
    p.add("p1_seats_caption", (x + 12, y + 280, inner, 18),
          caption("Seats arrived, all teams, counted apart", 9, inner, 1), on=pan, group="s")
    p.add("p1_seats_figure", (x + 12, y + 298, inner, 26), value_card("Seats arrived", 12),
          on=pan, group="s")

    # ---- largest group and its lever
    x, y, w, h = LARGEST_PANEL
    pan, inner = "p1_largest_panel", w - 24
    p.add(pan, LARGEST_PANEL, panel(), z=2000, row="bottom")
    p.add("p1_largest_title", (x + 12, y + 6, inner, 20), heading("Largest group per team, and its lever"),
          on=pan, group="t")
    p.add("p1_largest_sub", (x + 12, y + 26, inner, 18), subtitle("Follows the placement toggle and the month"),
          on=pan, group="t")
    widths = dict(LARGEST_COLS)
    lever_lines = [wrapped_lines([(LEVERS[t], pt(10))], widths["Lever"] - 10) for t in TEAMS]
    cols = [(proj_column("dim_team", "team", display="Team"), widths["Team"]),
            (proj_measure("Largest group", "Largest group"), widths["Largest group"]),
            (proj_measure("Largest group people", "People"), widths["People"]),
            (proj_measure("Largest group lever", "Lever"), widths["Lever"])]
    p.add("p1_largest_table", (x + 12, y + 46, inner, 278), {
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
    }, on=pan, group="c", need_w=sum(widths.values()) + TABLE_SLACK, need_h=table_height(lever_lines))
    return p


if __name__ == "__main__":
    build().write()
    set_page_order([PAGE0, PAGE])
