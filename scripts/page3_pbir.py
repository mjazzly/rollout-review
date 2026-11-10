#!/usr/bin/env python3
"""Write page 3 (Execution) into the Power BI project's report files.

    python3 scripts/page3_pbir.py

Brief section 6, page 3, "Does it hold up in everyday use?":
- first use within two weeks of training: the figure, its count, and a bar per team;
- repeat use within 30 days: one figure (Month 6) and a small line by month (round 7);
- recurring questions covered by a tested prompt: the figure, its count, and a grid of
  recurring questions in each use by month;
- tested prompts passing their cases: the figure, its count, and the live prompts not
  passing at their latest run, by name (text, so a table).
A row of team buttons (none picked: all teams) lets CHECK.md question 12 (Operations) be read.
Legal's 0.0% first use is real: one Legal session (week of 17 Aug 2026), 19 attendees, none ran
the item they were shown within two weeks.
Round 8: every panel is led by its figure (pbir.figure_band) with its visual under it, on one
grid: a left column 634 px wide (first use, repeat use) and a right one 598 px wide (recurring,
passing), so no panel is taller or wider than its content.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, MARINE, MATRIX_COLUMN_PAD, OFF, NO_FRAME, Page, body_top, button_slicer, colour, column,
    figure_band, filter_in, header, lit, measure_colour, panel, proj_column, proj_measure, pt,
    table_height, table_width, textbox, wrapped_lines,
    BODY_END, CONTROL_H, CONTROL_Y, GAP, HEADER_SECOND_H, HEADER_SECOND_Y, MARGIN, PAGE_W, TEXT_INSET,
)

PAGE = "d4e9f2a6b8c1d3e5f7a9"

TEAM_BUTTON_W = 90
TEAM = (PAGE_W - MARGIN - 6 * TEAM_BUTTON_W, CONTROL_Y, 6 * TEAM_BUTTON_W, CONTROL_H)
BODY_Y = HEADER_SECOND_Y + HEADER_SECOND_H + GAP
USE_COL, MONTH_COL = 150, 64        # grid column widths
LEFT_W = 1248 - GAP - (table_width([USE_COL] + [MONTH_COL] * 6, MATRIX_COLUMN_PAD) + 24)
RIGHT_X = 16 + LEFT_W + GAP
RIGHT_W = 1264 - RIGHT_X
BAND = 6 + 48 + 2                   # the figure band, then a chart (which pads its own top)
ROW_B_H = BAND + table_height([1] * 4) + 7        # four prompts not passing
ROW_A_H = BODY_END - BODY_Y - GAP - ROW_B_H
ROW_B_Y = BODY_Y + ROW_A_H + GAP
FIRST_PANEL = (16, BODY_Y, LEFT_W, ROW_A_H)
RECURRING_PANEL = (RIGHT_X, BODY_Y, RIGHT_W, ROW_A_H)
REPEAT_PANEL = (16, ROW_B_Y, LEFT_W, ROW_B_H)
PASSING_PANEL = (RIGHT_X, ROW_B_Y, RIGHT_W, ROW_B_H)
NOT_PASSING = ("Market scan in five questions", "Shift handover summary", "What may I use it for: quick check",
               "Workplan from meeting notes")   # scripts/page3_figures.py; the longest sets the rows
CASES_COL = 150
ITEM_COL = RIGHT_W - 24 - table_width([0, CASES_COL])
FIRST_USE_MAX = 0.585               # the highest team: Operations, 58.5% (scripts/page3_figures.py)


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def team_columns(measure_name: str) -> dict:
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
            "Y": {"projections": [proj_measure(measure_name)]}},
            "sortDefinition": {"sort": [{"field": column("dim_team", "team"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)}, "selector": {"metadata": f"_Measures.{measure_name}"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit("0.7D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def repeat_line() -> dict:
    return {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure("Execution tile", "Repeat use within 30 days")]}}},
        "objects": {
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            # 0.5 to 1: the line sits in the chart's upper half, not pressed to its top
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0.5D"), "end": lit("1D"),
                                          "gridlineShow": lit("false")}}],
            "legend": [{"properties": OFF}],
            "labels": [{"properties": {"show": lit("true")}}],
            "lineStyles": [{"properties": {"strokeWidth": lit("2D"), "showMarker": lit("true"),
                                           "markerSize": lit("3D")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def recurring_grid() -> dict:
    cell = "_Measures.Recurring questions in grid"
    return {
        "visualType": "pivotTable",
        "query": {"queryState": {
            "Rows": {"projections": [proj_column("dim_category", "category", active=True, display="Use")]},
            "Columns": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Values": {"projections": [proj_measure("Recurring questions in grid", "Recurring questions")]}}},
        "objects": {
            "subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}],
            "values": [{"properties": {"backColor": measure_colour("Recurring shade"),
                                       "fontColor": measure_colour("Recurring text colour")},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": cell}}],
            "columnWidth": [
                {"properties": {"value": lit(f"{USE_COL}D")}, "selector": {"metadata": "dim_category.category"}},
                {"properties": {"value": lit(f"{MONTH_COL}D")}, "selector": {"metadata": cell}},
            ],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def not_passing_table() -> dict:
    cols = [(proj_column("dim_library_item", "item_name", display="Not passing at the latest run"), ITEM_COL),
            (proj_measure("Cases matched when not passing", "Cases matched"), CASES_COL)]
    return {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [c for c, _ in cols]}}},
        "objects": {
            "total": [{"properties": {"totals": lit("false")}}],
            "columnWidth": [{"properties": {"value": lit(f"{wd}D")}, "selector": {"metadata": c["queryRef"]}}
                            for c, wd in cols],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def figure_panel(p: Page, key: str, box, figure: str, count: str | None = None, sub: str | None = None,
                 longest: str = "", row: str | None = None):
    x, y, w, h = box
    pan = f"p3_{key}_panel"
    p.add(pan, box, panel(), z=2000, row=row)
    band = figure_band(p, f"p3_{key}", pan, x, y, w, figure, figure, count=count, sub=sub, longest=longest)
    return pan, x, y, w, h, band


def build() -> Page:
    p = Page(PAGE, "Execution", number=3)
    header(p, "p3", "Execution", "Does it hold up in everyday use?",
           "Read from the usage dashboards, the question log and the run log", "Week 1 to Week 24")
    p.add("p3_team", TEAM, button_slicer("dim_team", "team", "Team", None, strict=False))
    assert body_top(p) == BODY_Y

    # ---- first use: the figure and its count, a column per team under them
    pan, x, y, w, h, band = figure_panel(p, "first", FIRST_PANEL, "First use within two weeks of training",
                                         count="First use count", longest="44.5%", row="a")
    p.add("p3_first_by_team", (x + 12, band + 2, w - 24, y + h - 4 - band - 2),
          team_columns("First use within two weeks of training"), on=pan, group="c", categories=6,
          max_value=FIRST_USE_MAX, longest_category="Technology", longest_label="58.5%")

    # ---- recurring questions covered: the figure and its count, the grid under them
    pan, x, y, w, h, band = figure_panel(p, "recurring", RECURRING_PANEL, "Recurring questions covered by a tested prompt",
                                         count="Recurring covered count", longest="89.4%", row="a")
    p.add("p3_recurring_grid", (x + 12, band + 2, w - 24, y + h - 4 - band - 2), recurring_grid(), on=pan, group="c",
          need_w=table_width([USE_COL] + [MONTH_COL] * 6, MATRIX_COLUMN_PAD), need_h=table_height([1] * 7))

    # ---- repeat use: the figure, and a line by month under it
    pan, x, y, w, h, band = figure_panel(p, "repeat", REPEAT_PANEL, "Repeat use within 30 days",
                                         sub="Read at each check-in", longest="83.6%", row="b")
    p.add("p3_repeat_line", (x + 12, band + 2, w - 24, y + h - 4 - band - 2), repeat_line(), on=pan, group="c",
          extra={"filterConfig": {"filters": [filter_in("dim_month", "month_label", ["Month 1"], "notMonth1", negate=True)]}})

    # ---- tested prompts passing: the figure and its count, the ones not passing under them
    pan, x, y, w, h, band = figure_panel(p, "passing", PASSING_PANEL, "Tested prompts passing their cases",
                                         count="Passing count", longest="81.0%", row="b")
    lines = [max(wrapped_lines([(n, pt(10))], ITEM_COL + 2 * TEXT_INSET),
                 wrapped_lines([("11 of 12 cases", pt(10))], CASES_COL + 2 * TEXT_INSET)) for n in NOT_PASSING]
    p.add("p3_not_passing", (x + 12, band + 2, w - 24, y + h - 4 - band - 2), not_passing_table(), on=pan, group="c",
          need_w=table_width([ITEM_COL, CASES_COL]), need_h=table_height(lines))

    p.answers = {
        10: [("p3_first_figure", "First use within two weeks of training"), ("p3_first_count", "First use count")],
        11: [("p3_recurring_figure", "Recurring questions covered by a tested prompt"),
             ("p3_recurring_count", "Recurring covered count")],
        12: [("p3_recurring_grid", "Recurring questions in grid")],
    }
    return p


if __name__ == "__main__":
    build().write()
