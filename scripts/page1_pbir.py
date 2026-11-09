#!/usr/bin/env python3
"""Write page 1 (Where people sit, FRAME-01) into the Power BI project's report files.

    python3 scripts/page1_pbir.py

Brief section 6, page 1: the nine checkpoints as a bar chart per team on one scale, with
a toggle between check-in and source placement; the gap per team; movement between the
two latest counts with seat arrivals apart; the largest group per team with its lever.
Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, OFF, STAGES, NO_FRAME, Page, colour, column, filter_in, lit, navigator,
    panel, proj_column, proj_measure, pt, set_page_order, text, textbox, value_is,
)

PAGE = "b7e4c2a91d3f5e6a8c10"
PAGE0 = "93ede836331e460c840c"

TEAMS = ("Consulting", "Finance", "Legal", "Operations", "People", "Technology")
CHECKPOINTS = ("No ticket", "Ticket held", "Checked in", "Through security", "Waiting to board",
               "Boarding", "Takeoff", "Above the clouds", "Frequent flyer")
STAGE_OF = {c: STAGES[i // 3][1] for i, c in enumerate(CHECKPOINTS)}   # 1-3 ground, 4-6 gate, 7-9 air
# One scale for all six teams and both placements: the largest bar at Month 6 is 174
# (Consulting, Takeoff, source placement), so every chart runs 0 to 180.
SCALE_END = 180

# ---------------------------------------------------------------- header strip
NAV = (16, 4, 1248, 32)
TITLE = (16, 36, 240, 34)
SOURCE = (16, 70, 972, 22)
TOGGLE = (1004, 36, 260, 56)

# ---------------------------------------------------------------- body
SPLIT = (16, 96, 1248, 345)            # panel: title row, then six team charts
CHART_W, CHART_H, CHART_GAP = 197, 283, 8
TABLES_Y, TABLES_H = 445, 271
GAP_PANEL = (16, TABLES_Y, 264, TABLES_H)
MOVE_PANEL = (296, TABLES_Y, 332, TABLES_H)
LARGEST_PANEL = (644, TABLES_Y, 620, TABLES_H)


def team_chart(team: str) -> dict:
    cp = column("dim_checkpoint", "checkpoint")
    return {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column("dim_checkpoint", "checkpoint", active=True)]},
                "Y": {"projections": [proj_measure("People at checkpoint")]},
            },
            "sortDefinition": {"sort": [{"field": cp, "direction": "Ascending"}], "isDefaultSort": False},
        },
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(STAGE_OF[c])},
                           "selector": value_is("dim_checkpoint", "checkpoint", c)} for c in CHECKPOINTS],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"),
                                          "end": lit(f"{SCALE_END}D"), "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def toggle() -> dict:
    # as Desktop wrote Branch review's month slicer: a dropdown, one value always picked
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [
            proj_column("placement_toggle", "placement", active=True)]}}},
        "objects": {
            "data": [{"properties": {"mode": text("Dropdown")}}],
            "selection": [{"properties": {"singleSelect": lit("true"), "strictSingleSelect": lit("true")}}],
            "general": [{"properties": {"filter": {"filter": {
                "Version": 2, "From": [{"Name": "f", "Entity": "placement_toggle", "Type": 0}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                                "Property": "placement"}}],
                    "Values": [[{"Literal": {"Value": "'Source'"}}]]}}}]}}}}],
            "header": [{"properties": {"text": text("Placement: Source or Check-in")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def table(columns: list[tuple[dict, int]]) -> dict:
    """columns: (projection, width in px). Sorted by team, no totals."""
    return {
        "visualType": "tableEx",
        "query": {
            "queryState": {"Values": {"projections": [c for c, _ in columns]}},
            "sortDefinition": {"sort": [{"field": column("dim_team", "team"), "direction": "Ascending"}]},
        },
        "objects": {
            "total": [{"properties": {"totals": lit("false")}}],
            "columnWidth": [{"properties": {"value": lit(f"{w}D")}, "selector": {"metadata": c["queryRef"]}}
                            for c, w in columns],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def title(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def team() -> dict:
    return proj_column("dim_team", "team", display="Team")


def build() -> Page:
    p = Page(PAGE, "Where people sit")
    p.add("p1_navigator", NAV, navigator(), z=0)
    p.add("p1_title", TITLE, textbox([[("Where people sit", pt(18, bold=True, color=INK))]]))
    p.add("p1_source", SOURCE, textbox([[
        ("Read from the check-in, the usage dashboards, the library's records and the question log · ",
         pt(10, color=INK_SOFT)),
        ("Month 6, the latest of six check-ins", pt(10, bold=True, color=INK_SOFT))]]))
    p.add("p1_toggle", TOGGLE, toggle())

    # the nine checkpoints, one chart per team, one scale
    x, y, w, h = SPLIT
    p.add("p1_split_panel", SPLIT, panel(), z=2000)
    legend_w = 282
    p.add("p1_split_title", (x + 12, y + 6, w - 24 - legend_w, 22),
          title("People at each checkpoint, by team, under the placement picked above · one scale for all six"),
          on="p1_split_panel", group="t")
    legend = []
    for n, (stage, hex_) in enumerate(STAGES):
        legend += [("■", pt(9, color=hex_)),
                   (f" {stage}" + ("   " if n < 2 else ""), pt(9, color=INK_SOFT))]
    p.add("p1_split_legend", (x + w - 12 - legend_w, y + 6, legend_w, 22), textbox([legend]),
          on="p1_split_panel", group="t")
    for i, t in enumerate(TEAMS):
        cx = x + 12 + i * (CHART_W + CHART_GAP)
        key = t.lower()
        p.add(f"p1_{key}_name", (cx, y + 38, CHART_W, 20), textbox([[(t, pt(10, bold=True, color=INK))]]),
              on="p1_split_panel", group="c", same="team name")
        p.add(f"p1_{key}_chart", (cx, y + 58, CHART_W, CHART_H), team_chart(t),
              on="p1_split_panel", group="c", same="team chart", categories=9,
              extra={"filterConfig": {"filters": [filter_in("dim_team", "team", [t], f"team{t}")]}})

    # the three tables: one top edge, one height
    tables = (
        ("p1_gap", GAP_PANEL, "The gap: check-in against source", [
            (team(), 84), (proj_measure("Gap higher", "Higher"), 50),
            (proj_measure("Gap level", "Level"), 50), (proj_measure("Gap lower", "Lower"), 50)]),
        ("p1_move", MOVE_PANEL, "Movement, Month 5 to Month 6", [
            (team(), 84), (proj_measure("Movement up", "Up"), 48), (proj_measure("Movement held", "Held"), 48),
            (proj_measure("Movement down", "Down"), 48),
            (proj_measure("Movement seats arrived", "Seats arrived, apart"), 70)]),
        ("p1_largest", LARGEST_PANEL, "Largest group per team, under the placement picked, and its lever", [
            (team(), 84), (proj_measure("Largest group", "Largest group"), 116),
            (proj_measure("Largest group people", "People"), 56),
            (proj_measure("Largest group lever", "Lever"), 330)]),
    )
    for key, box, heading, cols in tables:
        x, y, w, h = box
        pan = f"{key}_panel"
        p.add(pan, box, panel(), z=2000, row="tables")
        p.add(f"{key}_title", (x + 12, y + 6, w - 24, 22), title(heading), on=pan, group="t")
        p.add(f"{key}_table", (x + 12, y + 30, w - 24, h - 34), table(cols), on=pan, group="c")
    return p


if __name__ == "__main__":
    build().write()
    set_page_order([PAGE0, PAGE])
