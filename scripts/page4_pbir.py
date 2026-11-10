#!/usr/bin/env python3
"""Write page 4 (Refinement) into the Power BI project's report files.

    python3 scripts/page4_pbir.py

Brief section 6, page 4, "What earns its place, and at what cost?" (round 7):
- main chart: the live prompts ranked by cases matched on their latest smaller-model run,
  the ones that pass (every case) in marine, the rest grey;
- under it, for the passing prompts only: median tokens per run on each model, and the cost
  index (standard over smaller). Below, not beside: 21 prompts need the full width for their
  names to sit under their columns;
- prompts retired or merged by month, and what happened to each (a table: text).
Round 8: each column is labelled with its cases matched, as "11 of 12" (a dynamic format string
on Smaller model cases share); the retired chart is wide enough for its month names to stay level.
"""
from __future__ import annotations

from pbir import (
    GREY, INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, colour, column, filter_in, header, lit, panel,
    proj_column, proj_measure, pt, table_height, table_width, textbox, value_is, wrapped_lines,
    BODY_END, GAP, HEADER_SECOND_H, HEADER_SECOND_Y, TEXT_INSET, body_top,
)

PAGE = "e5a1b3c7d9f2e4a6b8c0"

ROW1_Y = HEADER_SECOND_Y + HEADER_SECOND_H + GAP
ROW2_H = 46 + 150 + 4               # a subtitle row, then charts at Desktop's smallest bar chart (150)
ROW2_Y = BODY_END - ROW2_H
ROW1_H = ROW2_Y - GAP - ROW1_Y
COST_W = 550
MAIN_PANEL = (16, ROW1_Y, 1248, ROW1_H)
COST_PANEL = (16, ROW2_Y, COST_W, ROW2_H)
RETIRED_PANEL = (16 + COST_W + GAP, ROW2_Y, 1248 - COST_W - GAP, ROW2_H)
LIVE = 21                           # live prompts at Week 24 (scripts/page4_figures.py)
TOKENS_W = 290
TOKENS_END = 4500                   # the most tokens on a passing prompt: 3,744 (LIB-09, standard)
INDEX_END = 2.5                     # the highest cost index is 2.07 (LIB-13)
RETIRED_CHART_W = 380              # 60 px a month: "Month 6" stays level (48 px slanted, round 7)
RETIRED_COLS = (56, 170)            # prompt ID, what happened
PASSES = (("Passes", MARINE), ("Does not pass", GREY))
TIERS = (("standard", "Standard model", GREY), ("smaller", "Smaller model", MARINE))


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def legend(items) -> dict:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("  " if n < len(items) - 1 else ""), pt(9, color=INK_SOFT))]
    return textbox([runs])


def axis(end: float) -> dict:
    return {"show": lit("false"), "start": lit("0D"), "end": lit(f"{end}D"), "gridlineShow": lit("false")}


def ranked_live() -> dict:
    m = "Smaller model cases share"
    return {
        "visualType": "columnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_library_item", "item_id", active=True)]},
            "Series": {"projections": [proj_column("dim_library_item", "smaller_model_result")]},
            "Y": {"projections": [proj_measure(m)]}},
            "sortDefinition": {"sort": [{"field": proj_measure(m)["field"], "direction": "Descending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)},
                           "selector": value_is("dim_library_item", "smaller_model_result", v)} for v, c in PASSES],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": axis(1.2)}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def passing_only(name: str) -> dict:
    return {"filterConfig": {"filters": [filter_in("dim_library_item", "smaller_model_result", ["Passes"], name)]}}


def tokens_chart() -> dict:
    return {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_library_item", "item_id", active=True)]},
            "Series": {"projections": [proj_column("fact_test_run", "model_tier")]},
            "Y": {"projections": [proj_measure("Cost per use", "Median tokens per run")]}},
            "sortDefinition": {"sort": [{"field": column("dim_library_item", "item_id"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": value_is("fact_test_run", "model_tier", v)}
                          for v, _, c in TIERS],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": axis(TOKENS_END)}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def index_chart() -> dict:
    return {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_library_item", "item_id", active=True)]},
            "Y": {"projections": [proj_measure("Cost index")]}},
            "sortDefinition": {"sort": [{"field": column("dim_library_item", "item_id"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)}, "selector": {"metadata": "_Measures.Cost index"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": axis(INDEX_END)}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def months_chart() -> dict:
    m = "Prompts retired or merged"
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure(m)]}}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)}, "selector": {"metadata": f"_Measures.{m}"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": axis(3)}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def table(cols) -> dict:
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


def build() -> Page:
    p = Page(PAGE, "Refinement", number=4)
    header(p, "p4", "Refinement", "What earns its place, and at what cost?",
           "Read from the run log and the library's records", "Week 1 to Week 24")
    assert body_top(p) == ROW1_Y

    # ---- the main chart: live prompts ranked by cases matched on the smaller model
    x, y, w, h = MAIN_PANEL
    pan, inner = "p4_main_panel", w - 24
    p.add(pan, MAIN_PANEL, panel(), z=2000)
    p.add("p4_main_title", (x + 12, y + 6, inner, 20), heading("Tested prompts that pass on a smaller model"),
          on=pan, group="t")
    p.add("p4_main_sub", (x + 12, y + 26, inner - 170, 18), subtitle("Cases matched, latest smaller-model run, live prompts"),
          on=pan, group="t", kind="subtitle")
    p.add("p4_main_legend", (x + 12 + inner - 170, y + 26, 170, 18), legend(PASSES), on=pan, group="t", legend=True)
    p.add("p4_main_chart", (x + 12, y + 46, inner, h - 50), ranked_live(), on=pan, group="c",
          categories=LIVE, max_value=1.0, longest_category="LIB-23", longest_label="11 of 12")

    # ---- the cost of the passing prompts: tokens on each model, and the cost index
    x, y, w, h = COST_PANEL
    pan, inner = "p4_cost_panel", w - 24
    p.add(pan, COST_PANEL, panel(), z=2000, row="bottom")
    p.add("p4_cost_title", (x + 12, y + 6, inner - 220, 20), heading("Cost of the passing prompts"), on=pan, group="t")
    p.add("p4_cost_legend", (x + 12 + inner - 220, y + 6, 220, 20),
          legend(tuple((d, c) for _, d, c in TIERS)), on=pan, group="t", legend=True)
    p.add("p4_tokens_sub", (x + 12, y + 26, TOKENS_W, 18), subtitle("Median tokens per run"),
          on=pan, group="t", kind="subtitle")
    ix = x + 12 + TOKENS_W + 16
    p.add("p4_index_sub", (ix, y + 26, x + w - 12 - ix, 18), subtitle("Cost index, standard over smaller"),
          on=pan, group="t", kind="subtitle")
    p.add("p4_tokens_chart", (x + 12, y + 46, TOKENS_W, h - 50), tokens_chart(), on=pan, group="c",
          categories=2, series=2, max_value=3744, extra=passing_only("passesTokens"))
    p.add("p4_index_chart", (ix, y + 46, x + w - 12 - ix, h - 50), index_chart(), on=pan, group="c",
          categories=2, max_value=2.07, extra=passing_only("passesIndex"))

    # ---- retired or merged
    x, y, w, h = RETIRED_PANEL
    pan, inner = "p4_retired_panel", w - 24
    p.add(pan, RETIRED_PANEL, panel(), z=2000, row="bottom")
    p.add("p4_retired_title", (x + 12, y + 6, inner, 20), heading("Prompts retired or merged"), on=pan, group="t")
    p.add("p4_retired_sub", (x + 12, y + 26, inner, 18), subtitle("Counted in the check-in month of the change"),
          on=pan, group="t", kind="subtitle")
    p.add("p4_retired_chart", (x + 12, y + 46, RETIRED_CHART_W, h - 50), months_chart(),
          on=pan, group="b", categories=6, max_value=2, longest_category="Month 6", longest_label="2")
    tx = x + 12 + RETIRED_CHART_W + 16
    changes = ["Retired in Month 5", "Merged into LIB-10 in Month 5"]
    lines = [wrapped_lines([(c, pt(10))], RETIRED_COLS[1] + 2 * TEXT_INSET) for c in changes]
    cols = [(proj_column("dim_library_item", "item_id", display="ID"), RETIRED_COLS[0]),
            (proj_measure("Retired or merged change", "What happened"), RETIRED_COLS[1])]
    p.add("p4_retired_table", (tx, y + 46, x + w - 12 - tx, h - 50), table(cols), on=pan, group="b",
          need_w=table_width(list(RETIRED_COLS)), need_h=table_height(lines))

    p.answers = {
        13: [("p4_main_chart", "item_id"), ("p4_main_chart", "Smaller model cases share")],
        14: [("p4_index_chart", "Cost index")],
        15: [("p4_retired_table", "item_id"), ("p4_retired_table", "Retired or merged change")],
    }
    return p


if __name__ == "__main__":
    build().write()
