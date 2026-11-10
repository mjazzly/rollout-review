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
    GREY, INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, colour, column, filter_in, header, lit, measure_colour, panel,
    proj_column, proj_measure, pt, table_height, table_width, textbox, value_is, wrapped_lines,
    BODY_END, GAP, HEADER_TITLE_H, HEADER_TITLE_Y, TEXT_INSET, body_top,
)

PAGE = "e5a1b3c7d9f2e4a6b8c0"

ROW1_Y = HEADER_TITLE_Y + HEADER_TITLE_H + GAP
ROW2_H = 46 + 133 + 4               # a subtitle row, then the retired table: two rows, one of two lines
ROW2_Y = BODY_END - ROW2_H
ROW1_H = ROW2_Y - GAP - ROW1_Y
COST_W = 24 + 90 + 130 + 130 + 100 + 4 * 12 + 12   # the cost table's columns
MAIN_PANEL = (16, ROW1_Y, 1248, ROW1_H)
COST_PANEL = (16, ROW2_Y, COST_W, ROW2_H)
RETIRED_PANEL = (16 + COST_W + GAP, ROW2_Y, 1248 - COST_W - GAP, ROW2_H)
LIVE = 21                           # live prompts at Week 24 (scripts/page4_figures.py)
LIVE_ITEMS = [f"LIB-{n:02d}" for n in range(1, 24) if n not in (12, 14)]   # retired or merged: LIB-12, LIB-14
PASSING = ("LIB-09", "LIB-13")      # passing on the smaller model (page4_figures.py)
COST_COLS = (90, 130, 130, 100)     # prompt, standard model, smaller model, cost index
TOKENS_W = 290
TOKENS_END = 4500                   # the most tokens on a passing prompt: 3,744 (LIB-09, standard)
INDEX_END = 2.5                     # the highest cost index is 2.07 (LIB-13)
RETIRED_CHART_W = 380              # 60 px a month: "Month 6" stays level (48 px slanted, round 7)
RETIRED_COLS = (60, 182)            # prompt ID, what happened
PASSES = (("Passes", MARINE), ("Does not pass", GREY))
TIERS = (("smaller", "Smaller model", MARINE), ("standard", "Standard model", GREY))   # Desktop's order: a to z


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
    """Round 9: a clustered column chart, one series, coloured by a measure (marine passes, grey not):
    the stacked column chart with a series drew no labels in rounds 7 and 8; clustered column
    charts drew theirs on pages 2 and 3."""
    m = "Smaller model cases share"
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_library_item", "item_id", active=True)]},
            "Y": {"projections": [proj_measure(m)]}},
            "sortDefinition": {"sort": [{"field": proj_measure(m)["field"], "direction": "Descending"}],
                               "isDefaultSort": False}},
        "objects": {
            # round 10: the colour from a measure did not take; one dataPoint per prompt, picked by its
            # ID, the selector the stage colours used (S3)
            "dataPoint": [{"properties": {"fill": colour(MARINE if i in PASSING else GREY)},
                           "selector": value_is("dim_library_item", "item_id", i)} for i in LIVE_ITEMS],
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
    """Round 9: columns, labelled above in full ("1,854"): as bars, two prompts drew 8 px bars whose
    labels touched the bar below."""
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_library_item", "item_id", active=True)]},
            "Series": {"projections": [proj_column("fact_test_run", "model_tier")]},
            "Y": {"projections": [proj_measure("Cost per use", "Median tokens per run")]}},
            "sortDefinition": {"sort": [{"field": column("dim_library_item", "item_id"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": value_is("fact_test_run", "model_tier", v)}
                          for v, _, c in TIERS],
            "labels": [{"properties": {"show": lit("true"), "labelDisplayUnits": lit("1D")}}],
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

    # ---- the cost of the passing prompts: one table (round 10)
    x, y, w, h = COST_PANEL
    pan, inner = "p4_cost_panel", w - 24
    p.add(pan, COST_PANEL, panel(), z=2000, row="bottom")
    p.add("p4_cost_title", (x + 12, y + 6, inner, 20), heading("Cost of the passing prompts"), on=pan, group="t")
    p.add("p4_cost_sub", (x + 12, y + 26, inner, 18), subtitle("Median tokens per run"), on=pan, group="t",
          kind="subtitle")
    cols = [(proj_column("dim_library_item", "item_id", display="Prompt"), COST_COLS[0]),
            (proj_measure("Standard model tokens", "Standard model"), COST_COLS[1]),
            (proj_measure("Smaller model tokens", "Smaller model"), COST_COLS[2]),
            (proj_measure("Cost index text", "Cost index"), COST_COLS[3])]
    p.add("p4_cost_table", (x + 12, y + 46, inner, h - 50), table(cols), on=pan, group="b",
          need_w=table_width(list(COST_COLS)), need_h=table_height([1, 1]), extra=passing_only("passesCost"))

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
        14: [("p4_cost_table", "Cost index text")],
        15: [("p4_retired_table", "item_id"), ("p4_retired_table", "Retired or merged change")],
    }
    return p


if __name__ == "__main__":
    build().write()
