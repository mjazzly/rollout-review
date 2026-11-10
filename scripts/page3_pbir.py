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
A team slicer (all teams to start) lets CHECK.md question 12 (Operations) be read on the page.
Legal's 0.0% first use is real: 19 Legal attendees, none ran the item they were shown.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, MARINE, MATRIX_COLUMN_PAD, OFF, NO_FRAME, Page, colour, column, filter_in,
    header, lit, measure_colour, panel, proj_column, proj_measure, pt, slim_slicer,
    table_height, table_width, textbox, value_card,
    BODY_END, CONTROL_H, CONTROL_Y, HEADER_BODY_Y,
)

PAGE = "d4e9f2a6b8c1d3e5f7a9"

TEAM = (1144, CONTROL_Y, 120, CONTROL_H)
ROW1_Y, ROW1_H = HEADER_BODY_Y, 252
ROW2_Y = ROW1_Y + ROW1_H + 4
ROW2_H = BODY_END - ROW2_Y
FIRST_PANEL = (16, ROW1_Y, 520, ROW1_H)
REPEAT_PANEL = (552, ROW1_Y, 712, ROW1_H)
RECURRING_PANEL = (16, ROW2_Y, 806, ROW2_H)
PASSING_PANEL = (838, ROW2_Y, 426, ROW2_H)
FIGURE_W = 180
USE_COL, MONTH_COL = 150, 64        # grid column widths
NOT_PASSING_ROWS = 4                # live prompts not passing at Month 6 (scripts/page3_figures.py)
ITEM_COL, CASES_COL = 250, 90
FIRST_USE_MAX = 0.585               # the highest team: Operations, 58.5% (scripts/page3_figures.py)


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def team_bars(measure_name: str) -> dict:
    return {
        "visualType": "clusteredBarChart",
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
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit("1D"),
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
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit("1D"),
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


def panel_top(p: Page, key: str, box, title: str, sub: str, row: str):
    x, y, w, h = box
    pan = f"p3_{key}_panel"
    p.add(pan, box, panel(), z=2000, row=row)
    p.add(f"p3_{key}_title", (x + 12, y + 6, w - 24, 20), heading(title), on=pan, group="t")
    p.add(f"p3_{key}_sub", (x + 12, y + 26, w - 24, 18), subtitle(sub), on=pan, group="t", kind="subtitle")
    return pan, x, y, w, h, w - 24


def figure_with_count(p: Page, key: str, pan: str, x: int, y: int, figure: str, count: str | None,
                      longest: str = "") -> None:
    p.add(f"p3_{key}_figure", (x, y, FIGURE_W, 62), value_card(figure, 36), on=pan, group="b", same="figure")
    if count:
        p.add(f"p3_{key}_count", (x, y + 62, FIGURE_W, 24), value_card(count, 10, colour(INK_SOFT)),
              on=pan, group="b", same="count", longest_value=longest)


def build() -> Page:
    p = Page(PAGE, "Execution", number=3)
    header(p, "p3", "Execution", "Does it hold up in everyday use?",
           "Read from the usage dashboards, the question log and the run log", "Week 1 to Week 24")
    p.add("p3_team", TEAM, slim_slicer("dim_team", "team", None, single=True, strict=False))

    # ---- first use: the figure and its count, a bar per team beside them
    pan, x, y, w, h, inner = panel_top(p, "first", FIRST_PANEL, "First use within two weeks of training",
                                       "Training sessions, Week 1 to Week 24", "top")
    figure_with_count(p, "first", pan, x + 12, y + 54, "First use within two weeks of training",
                      "First use count", "174 of 391 attendees")
    bx = x + 12 + FIGURE_W + 16
    p.add("p3_first_by_team", (bx, y + 46, x + w - 12 - bx, h - 50), team_bars("First use within two weeks of training"),
          on=pan, group="b", categories=6, max_value=FIRST_USE_MAX)

    # ---- repeat use: the Month 6 figure, and a small line by month beside it
    pan, x, y, w, h, inner = panel_top(p, "repeat", REPEAT_PANEL, "Repeat use within 30 days",
                                       "Read at each check-in", "top")
    figure_with_count(p, "repeat", pan, x + 12, y + 54, "Repeat use within 30 days", None)
    lx = x + 12 + FIGURE_W + 16
    p.add("p3_repeat_line", (lx, y + 46, x + w - 12 - lx, h - 50), repeat_line(), on=pan, group="b",
          extra={"filterConfig": {"filters": [filter_in("dim_month", "month_label", ["Month 1"], "notMonth1", negate=True)]}})

    # ---- recurring questions covered: the figure and its count, the grid beside them
    pan, x, y, w, h, inner = panel_top(p, "recurring", RECURRING_PANEL, "Recurring questions covered by a tested prompt",
                                       "Week 1 to Week 24", "bottom")
    figure_with_count(p, "recurring", pan, x + 12, y + 54, "Recurring questions covered by a tested prompt",
                      "Recurring covered count", "127 of 142 questions")
    gx = x + 12 + FIGURE_W + 16
    p.add("p3_recurring_grid_name", (gx, y + 54, x + w - 12 - gx, 20),
          heading("Recurring questions in each use, by month"), on=pan, group="b")
    p.add("p3_recurring_grid", (gx, y + 74, x + w - 12 - gx, 250), recurring_grid(), on=pan, group="b",
          need_w=table_width([USE_COL] + [MONTH_COL] * 6, MATRIX_COLUMN_PAD), need_h=table_height([1] * 7))

    # ---- tested prompts passing: the figure and its count, the ones not passing under them
    pan, x, y, w, h, inner = panel_top(p, "passing", PASSING_PANEL, "Tested prompts passing their cases",
                                       "Live prompts at Week 24, latest standard run", "bottom")
    figure_with_count(p, "passing", pan, x + 12, y + 54, "Tested prompts passing their cases", "Passing count",
                      "17 of 21 live prompts")
    need = table_height([1] * NOT_PASSING_ROWS)
    p.add("p3_not_passing", (x + 12, y + 142, inner, need), not_passing_table(), on=pan, group="c",
          need_w=table_width([ITEM_COL, CASES_COL]), need_h=need)

    p.answers = {
        10: [("p3_first_figure", "First use within two weeks of training"), ("p3_first_count", "First use count")],
        11: [("p3_recurring_figure", "Recurring questions covered by a tested prompt"),
             ("p3_recurring_count", "Recurring covered count")],
        12: [("p3_recurring_grid", "Recurring questions in grid")],
    }
    return p


if __name__ == "__main__":
    build().write()
