#!/usr/bin/env python3
"""Write page 3 (Execution) into the Power BI project's report files.

    python3 scripts/page3_pbir.py

Brief section 6, page 3, "Does it hold up in everyday use?":
- first use within two weeks of training, with its count;
- repeat use within 30 days, by month (the page 0 Execution figure is Month 6);
- recurring questions covered by a tested prompt, with its count, beside a grid of
  recurring questions by use and month (where coverage came in shows as the grid emptying);
- tested prompts passing their cases, with its count, and the live prompts not passing
  at their latest run, by name (text, so a table).
A team slicer (all teams to start) lets CHECK.md question 12 (Operations) be read on the
page. Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, MARINE, MATRIX_COLUMN_PAD, OFF, NO_FRAME, Page, colour, column, filter_in,
    header, lit, measure_colour, panel, proj_column, proj_measure, pt, set_page_order, table_height,
    table_width, text, textbox, value_card,
)

PAGE = "d4e9f2a6b8c1d3e5f7a9"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", PAGE]

TEAM = (1148, 36, 116, 62)
ROW1_Y, ROW1_H = 102, 270
ROW2_Y, ROW2_H = 376, 340
FIRST_PANEL = (16, ROW1_Y, 412, ROW1_H)
REPEAT_PANEL = (444, ROW1_Y, 820, ROW1_H)
RECURRING_PANEL = (16, ROW2_Y, 814, ROW2_H)
PASSING_PANEL = (846, ROW2_Y, 418, ROW2_H)
FIGURE_W = 200
USE_COL, MONTH_COL = 150, 64        # grid column widths
NOT_PASSING_ROWS = 4                # live prompts not passing at Month 6 (scripts/page3_figures.py)
ITEM_COL, CASES_COL = 250, 100


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def team_slicer() -> dict:
    # as Branch review's branch slicer: a dropdown, one team or all of them
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj_column("dim_team", "team", active=True)]}}},
        "objects": {
            "data": [{"properties": {"mode": text("Dropdown")}}],
            "selection": [{"properties": {"strictSingleSelect": lit("false"), "selectAllCheckboxEnabled": lit("true"),
                                          "singleSelect": lit("true")}}],
            "header": [{"properties": {"text": text("Team")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def repeat_chart() -> dict:
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure("Execution tile", "Repeat use within 30 days")]}}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)}, "selector": {"metadata": "_Measures.Execution tile"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit("1D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def recurring_grid() -> dict:
    cell = "_Measures.Repeat-flagged questions"
    return {
        "visualType": "pivotTable",
        "query": {"queryState": {
            "Rows": {"projections": [proj_column("dim_category", "category", active=True, display="Use")]},
            "Columns": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Values": {"projections": [proj_measure("Repeat-flagged questions", "Recurring questions")]}}},
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
    cols = [(proj_column("dim_library_item", "item_name", display="Prompt"), ITEM_COL),
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


def figure_with_count(p: Page, key: str, pan: str, x: int, y: int, w: int, figure: str, count: str,
                      group: str = "b") -> None:
    p.add(f"p3_{key}_figure", (x, y, w, 62), value_card(figure, 36), on=pan, group=group, same="figure")
    p.add(f"p3_{key}_count", (x, y + 62, w, 24), value_card(count, 10, colour(INK_SOFT)),
          on=pan, group=group, same="count")


def build() -> Page:
    p = Page(PAGE, "Execution", number=3)
    header(p, "p3", "Execution", "Read from the usage dashboards, the question log and the run log",
           "Week 1 to Week 24", question="Does it hold up in everyday use?", right=TEAM[0] - 16)
    p.add("p3_team", TEAM, team_slicer())

    # ---- first use within two weeks of training
    x, y, w, h = FIRST_PANEL
    pan, inner = "p3_first_panel", w - 24
    p.add(pan, FIRST_PANEL, panel(), z=2000, row="top")
    p.add("p3_first_title", (x + 12, y + 6, inner, 20), heading("First use within two weeks of training"),
          on=pan, group="t")
    p.add("p3_first_sub", (x + 12, y + 26, inner, 18), subtitle("Every session, Week 1 to Week 24 · follows the team"),
          on=pan, group="t")
    figure_with_count(p, "first", pan, x + 12, y + 54, FIGURE_W, "First use within two weeks of training",
                      "First use count")

    # ---- repeat use within 30 days, by month
    x, y, w, h = REPEAT_PANEL
    pan, inner = "p3_repeat_panel", w - 24
    p.add(pan, REPEAT_PANEL, panel(), z=2000, row="top")
    p.add("p3_repeat_title", (x + 12, y + 6, inner, 20), heading("Repeat use within 30 days, by month"),
          on=pan, group="t")
    p.add("p3_repeat_sub", (x + 12, y + 26, inner, 18), subtitle(
        "People active again within 30 days of their first active week, read at each check-in · follows the team"),
        on=pan, group="t")
    p.add("p3_repeat_chart", (x + 12, y + 46, inner, h - 50), repeat_chart(), on=pan, group="c", categories=5,
          extra={"filterConfig": {"filters": [
              filter_in("dim_month", "month_label", ["Month 1"], "notMonth1", negate=True)]}})

    # ---- recurring questions covered, beside the grid of recurring questions
    x, y, w, h = RECURRING_PANEL
    pan, inner = "p3_recurring_panel", w - 24
    p.add(pan, RECURRING_PANEL, panel(), z=2000, row="bottom")
    p.add("p3_recurring_title", (x + 12, y + 6, inner, 20), heading("Recurring questions covered by a tested prompt"),
          on=pan, group="t")
    p.add("p3_recurring_sub", (x + 12, y + 26, inner, 18), subtitle(
        "Week 1 to Week 24 · the grid: recurring questions in each use, by month, darker for more · follows the team"),
        on=pan, group="t")
    figure_with_count(p, "recurring", pan, x + 12, y + 54, FIGURE_W, "Recurring questions covered by a tested prompt",
                      "Recurring covered count")
    gx = x + 12 + FIGURE_W + 16
    p.add("p3_recurring_grid", (gx, y + 54, x + w - 12 - gx, 250), recurring_grid(), on=pan, group="b",
          need_w=table_width([USE_COL] + [MONTH_COL] * 6, MATRIX_COLUMN_PAD), need_h=table_height([1] * 7))

    # ---- tested prompts passing, and the ones that are not
    x, y, w, h = PASSING_PANEL
    pan, inner = "p3_passing_panel", w - 24
    p.add(pan, PASSING_PANEL, panel(), z=2000, row="bottom")
    p.add("p3_passing_title", (x + 12, y + 6, inner, 20), heading("Tested prompts passing their cases"),
          on=pan, group="t")
    p.add("p3_passing_sub", (x + 12, y + 26, inner, 18), subtitle("Live prompts at Week 24, latest standard run"),
          on=pan, group="t")
    figure_with_count(p, "passing", pan, x + 12, y + 54, FIGURE_W, "Tested prompts passing their cases",
                      "Passing count")
    p.add("p3_not_passing_caption", (x + 12, y + 150, inner, 18), subtitle("Not passing at their latest run"),
          on=pan, group="c")
    need = table_height([1] * NOT_PASSING_ROWS)
    p.add("p3_not_passing", (x + 12, y + 168, inner, need), not_passing_table(), on=pan, group="c",
          need_w=table_width([ITEM_COL, CASES_COL]), need_h=need)

    p.answers = {
        10: [("p3_first_figure", "First use within two weeks of training"), ("p3_first_count", "First use count")],
        11: [("p3_recurring_figure", "Recurring questions covered by a tested prompt"),
             ("p3_recurring_count", "Recurring covered count")],
        12: [("p3_recurring_grid", "Repeat-flagged questions")],
    }
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
