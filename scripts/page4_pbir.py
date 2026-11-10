#!/usr/bin/env python3
"""Write page 4 (Refinement) into the Power BI project's report files.

    python3 scripts/page4_pbir.py

Brief section 6, page 4, "What earns its place, and at what cost?":
- tested prompts that pass on a smaller model: the count, the front page's share in words,
  and the prompts by name (text, so a table);
- prompts retired or merged by month, and what happened to each (a table: text);
- cost per use: median tokens per run by prompt, standard beside smaller, and under it the
  cost index (standard over smaller) by prompt, labelled.
No slicer: the page reads Week 1 to Week 24, and the share at Week 24.
"""
from __future__ import annotations

from pbir import (
    GREY, INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, colour, column, header, lit, panel,
    proj_column, proj_measure, pt, set_page_order, table_height, table_width, textbox, value_card,
    value_is, wrapped_lines, TEXT_INSET,
)

PAGE = "e5a1b3c7d9f2e4a6b8c0"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", "d4e9f2a6b8c1d3e5f7a9", PAGE]

ROW1_Y, ROW1_H = 102, 208
SMALLER_PANEL = (16, ROW1_Y, 600, ROW1_H)
RETIRED_PANEL = (632, ROW1_Y, 632, ROW1_H)
COST_PANEL = (16, 314, 1248, 402)
FIGURE_W = 180
SMALLER_COLS = (56, 180, 96)        # prompt ID, prompt, cases on the smaller model
RETIRED_CHART_W = 330
RETIRED_COLS = (56, 170)            # prompt ID, what happened
ITEMS = 23                          # library items with test runs (scripts/page4_figures.py)
INDEX_END = 2.5                     # the highest cost index is 2.07 (LIB-13)


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def legend(items) -> dict:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("  " if n < len(items) - 1 else ""), pt(9, color=INK_SOFT))]
    return textbox([runs])


def table(cols: list[tuple[dict, int]]) -> dict:
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


def columns(measure_name: str, category: tuple[str, str], end: float | None, series_field=None,
            series=None, labels=True, axis=True) -> dict:
    q = {"Category": {"projections": [proj_column(*category, active=True)]},
         "Y": {"projections": [proj_measure(measure_name)]}}
    if series_field:
        q["Series"] = {"projections": [proj_column(*series_field)]}
    value_axis = {"show": lit("false"), "start": lit("0D"), "gridlineShow": lit("false")}
    if end:
        value_axis["end"] = lit(f"{end}D")
    objects = {
        "labels": [{"properties": {"show": lit("true" if labels else "false")}}],
        "legend": [{"properties": OFF}],
        "categoryAxis": [{"properties": {"show": lit("true" if axis else "false")}}],
        "valueAxis": [{"properties": value_axis}],
    }
    if series:
        objects["dataPoint"] = [{"properties": {"fill": colour(c)}, "selector": value_is(*series_field, v)}
                                for v, c in series]
    else:
        objects["dataPoint"] = [{"properties": {"fill": colour(MARINE)},
                                 "selector": {"metadata": f"_Measures.{measure_name}"}}]
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": q,
                  "sortDefinition": {"sort": [{"field": proj_column(*category)["field"], "direction": "Ascending"}],
                                     "isDefaultSort": False}},
        "objects": objects,
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def build() -> Page:
    p = Page(PAGE, "Refinement", number=4)
    header(p, "p4", "Refinement", "Read from the run log and the library's records", "Week 1 to Week 24",
           question="What earns its place, and at what cost?")

    # ---- passing on the smaller model
    x, y, w, h = SMALLER_PANEL
    pan, inner = "p4_smaller_panel", w - 24
    p.add(pan, SMALLER_PANEL, panel(), z=2000, row="top")
    p.add("p4_smaller_title", (x + 12, y + 6, inner, 20), heading("Tested prompts that pass on a smaller model"),
          on=pan, group="t")
    p.add("p4_smaller_sub", (x + 12, y + 26, inner, 18), subtitle("Latest smaller-model run, every library item"),
          on=pan, group="t")
    p.add("p4_smaller_figure", (x + 12, y + 54, FIGURE_W, 62),
          value_card("Tested prompts that pass on a smaller model", 36), on=pan, group="b", same="figure")
    p.add("p4_smaller_count", (x + 12, y + 116, FIGURE_W, 24), value_card("Smaller model share line", 10, colour(INK_SOFT)),
          on=pan, group="b", same="count")
    tx = x + 12 + FIGURE_W + 16
    cols = [(proj_column("dim_library_item", "item_id", display="ID"), SMALLER_COLS[0]),
            (proj_column("dim_library_item", "item_name", display="Prompt"), SMALLER_COLS[1]),
            (proj_measure("Smaller model cases when passing", "Smaller model"), SMALLER_COLS[2])]
    p.add("p4_smaller_table", (tx, y + 46, x + w - 12 - tx, h - 50), table(cols), on=pan, group="b",
          need_w=table_width(list(SMALLER_COLS)), need_h=table_height([1, 1]))

    # ---- retired or merged
    x, y, w, h = RETIRED_PANEL
    pan, inner = "p4_retired_panel", w - 24
    p.add(pan, RETIRED_PANEL, panel(), z=2000, row="top")
    p.add("p4_retired_title", (x + 12, y + 6, inner, 20), heading("Prompts retired or merged"), on=pan, group="t")
    p.add("p4_retired_sub", (x + 12, y + 26, inner, 18), subtitle("Counted in the check-in month of the change"),
          on=pan, group="t")
    p.add("p4_retired_chart", (x + 12, y + 46, RETIRED_CHART_W, h - 50),
          columns("Prompts retired or merged", ("dim_month", "month_label"), 3),
          on=pan, group="b", categories=6, max_value=2, longest_category="Month 6", longest_label="2")
    tx = x + 12 + RETIRED_CHART_W + 16
    changes = ["Retired in Month 5", "Merged into LIB-10 in Month 5"]
    lines = [wrapped_lines([(c, pt(10))], RETIRED_COLS[1] + 2 * TEXT_INSET) for c in changes]
    cols = [(proj_column("dim_library_item", "item_id", display="ID"), RETIRED_COLS[0]),
            (proj_measure("Retired or merged change", "What happened"), RETIRED_COLS[1])]
    p.add("p4_retired_table", (tx, y + 46, x + w - 12 - tx, h - 50), table(cols), on=pan, group="b",
          need_w=table_width(list(RETIRED_COLS)), need_h=table_height(lines))

    # ---- cost per use, then the cost index, by prompt (one axis of prompt IDs, under the index)
    x, y, w, h = COST_PANEL
    pan, inner = "p4_cost_panel", w - 24
    p.add(pan, COST_PANEL, panel(), z=2000)
    p.add("p4_cost_title", (x + 12, y + 6, inner, 20), heading("Cost per use"), on=pan, group="t")
    p.add("p4_cost_sub", (x + 12, y + 26, inner - 220, 18), subtitle(
        "Median tokens per run, by prompt, on the standard model and on the smaller model"), on=pan, group="t")
    p.add("p4_cost_legend", (x + 12 + inner - 220, y + 26, 220, 18),
          legend((("Standard model", GREY), ("Smaller model", MARINE))), on=pan, group="t", legend=True)
    p.add("p4_tokens_chart", (x + 12, y + 46, inner, 180),
          columns("Cost per use", ("dim_library_item", "item_id"), None, ("fact_test_run", "model_tier"),
                  (("standard", GREY), ("smaller", MARINE)), labels=False, axis=False),
          on=pan, group="c1", categories=ITEMS, series=2)
    p.add("p4_index_name", (x + 12, y + 236, inner, 20),
          heading("Cost index: standard over smaller, by prompt"), on=pan, group="c2")
    p.add("p4_index_chart", (x + 12, y + 256, inner, 142),
          columns("Cost index", ("dim_library_item", "item_id"), INDEX_END),
          on=pan, group="c2", categories=ITEMS, max_value=2.07, longest_category="LIB-23", longest_label="2.07")

    p.answers = {
        13: [("p4_smaller_table", "item_id"), ("p4_smaller_table", "Smaller model cases when passing"),
             ("p4_smaller_figure", "Tested prompts that pass on a smaller model")],
        14: [("p4_index_chart", "Cost index")],
        15: [("p4_retired_table", "item_id"), ("p4_retired_table", "Retired or merged change")],
    }
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
