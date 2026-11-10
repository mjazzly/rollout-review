#!/usr/bin/env python3
"""Write page 5 (Scale) into the Power BI project's report files.

    python3 scripts/page5_pbir.py

Brief section 6, page 5, "Where has it changed the work?":
- impact in people's own words: the Month 6 check-in answers to "If AI disappeared from
  your work tomorrow, what would change?", per team, counts on the bars;
- share of people in the air against the baseline: each team at its baseline month (named
  beside the team) and at Month 6, and the change in points;
- uses taken up beyond the first team: the count, and the prompts by name with the team
  that took each up and the week it started (text, so a table).
No slicer: the page reads Month 6 and Week 1 to Week 24.
"""
from __future__ import annotations

from pbir import (
    AMBER, GREY, INK, INK_SOFT, MARINE, OFF, PALE, NO_FRAME, Page, colour, column, header, lit,
    panel, proj_column, proj_measure, pt, set_page_order, table_height, table_width, textbox, value_card,
)

PAGE = "f6b2c4d8e1a3f5b7c9d1"
ORDER = ["93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10", "c3f8d1e5a7b9c2d4e6f8", "d4e9f2a6b8c1d3e5f7a9",
         "e5a1b3c7d9f2e4a6b8c0", PAGE]

ROW1_Y, ROW1_H = 102, 380
IMPACT_PANEL = (16, ROW1_Y, 616, ROW1_H)
AIR_PANEL = (648, ROW1_Y, 616, ROW1_H)
TAKEN_PANEL = (16, 486, 1248, 230)
AIR_CHART_W = 368
FIGURE_W = 180
TAKEN_COLS = (56, 240, 110, 110, 80)   # ID, prompt, made by, taken up by, from
IMPACT_MIN_SHARE = 17 / 120            # the thinnest segment: Legal, "I would lose time every week"
AIR_MAX, POINTS_MAX = 0.603, 17.6      # Consulting at Month 6; Operations' change (scripts/page5_figures.py)


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def legend(items) -> dict:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("  " if n < len(items) - 1 else ""), pt(9, color=INK_SOFT))]
    return textbox([runs])


def by_team(chart: str, measures, category=("dim_team", "team"), end=1.0, inner_padding=None) -> dict:
    """Bars per team. measures: (measure, display, colour)."""
    axis = {"show": lit("true")}
    if inner_padding is not None:
        axis["innerPadding"] = lit(f"{inner_padding}L")
    return {
        "visualType": chart,
        "query": {"queryState": {
            "Category": {"projections": [proj_column(*category, active=True)]},
            "Y": {"projections": [proj_measure(m, d) for m, d, _ in measures]}},
            "sortDefinition": {"sort": [{"field": column(*category), "direction": "Ascending"}], "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": {"metadata": f"_Measures.{m}"}}
                          for m, _, c in measures],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": axis}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{end}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def build() -> Page:
    p = Page(PAGE, "Scale", number=5)
    header(p, "p5", "Scale", "Read from the question log, the usage dashboards and the check-in",
           "Week 1 to Week 24", question="Where has it changed the work?")

    # ---- impact in people's own words
    x, y, w, h = IMPACT_PANEL
    pan, inner = "p5_impact_panel", w - 24
    p.add(pan, IMPACT_PANEL, panel(), z=2000, row="top")
    p.add("p5_impact_title", (x + 12, y + 6, inner, 20), heading("Impact in people's own words"), on=pan, group="t")
    p.add("p5_impact_sub", (x + 12, y + 26, 260, 18), subtitle("Month 6: if AI disappeared tomorrow?"),
          on=pan, group="t")
    p.add("p5_impact_legend", (x + 12 + 260, y + 26, inner - 260, 18), legend((
        ("I would lose time every week", MARINE), ("A little", PALE), ("Nothing", GREY))),
        on=pan, group="t", legend=True)
    impact = (("Impact lose time share", "I would lose time every week", MARINE),
              ("Impact a little share", "A little", PALE), ("Impact nothing share", "Nothing", GREY))
    p.add("p5_impact_chart", (x + 12, y + 46, inner, h - 50), by_team("barChart", impact),
          on=pan, group="c", categories=6, label_min_share=IMPACT_MIN_SHARE)

    # ---- share in the air: baseline against Month 6, and the change in points
    x, y, w, h = AIR_PANEL
    pan, inner = "p5_air_panel", w - 24
    p.add(pan, AIR_PANEL, panel(), z=2000, row="top")
    p.add("p5_air_title", (x + 12, y + 6, inner, 20), heading("Share of people in the air against the baseline"),
          on=pan, group="t")
    p.add("p5_air_sub", (x + 12, y + 26, AIR_CHART_W, 18),
          subtitle("Each team at its baseline month (by its name) and at Month 6"), on=pan, group="t")
    px = x + 12 + AIR_CHART_W + 16
    p.add("p5_points_name", (px, y + 26, x + w - 12 - px, 18), subtitle("Change, in points"), on=pan, group="t")
    air = (("Share of people in the air baseline", "Baseline", GREY),
           ("Share of people in the air latest", "Month 6", MARINE))
    chart_h = h - 50 - 20
    p.add("p5_air_chart", (x + 12, y + 46, AIR_CHART_W, chart_h),
          by_team("clusteredBarChart", air, ("dim_team", "team_baseline_label"), 0.8, inner_padding=10),
          on=pan, group="c", categories=6, series=2, max_value=AIR_MAX)
    p.add("p5_air_legend", (x + 12, y + 46 + chart_h, AIR_CHART_W, 20),
          legend((("Baseline", GREY), ("Month 6", MARINE))), on=pan, group="c", legend=True)
    p.add("p5_points_chart", (px, y + 46, x + w - 12 - px, h - 50),
          by_team("clusteredBarChart", (("Air change points", "Change, in points", MARINE),), end=22),
          on=pan, group="c", categories=6, max_value=POINTS_MAX)

    # ---- uses taken up beyond the first team
    x, y, w, h = TAKEN_PANEL
    pan, inner = "p5_taken_panel", w - 24
    p.add(pan, TAKEN_PANEL, panel(), z=2000)
    p.add("p5_taken_title", (x + 12, y + 6, inner, 20), heading("Uses taken up beyond the first team"),
          on=pan, group="t")
    p.add("p5_taken_sub", (x + 12, y + 26, inner, 18),
          subtitle("Prompts with runs from two or more teams, Week 1 to Week 24, and the team that took each up"),
          on=pan, group="t")
    p.add("p5_taken_figure", (x + 12, y + 54, FIGURE_W, 62), value_card("Uses taken up beyond the first team", 36),
          on=pan, group="b", same="figure")
    p.add("p5_taken_count", (x + 12, y + 116, FIGURE_W, 24), value_card("Uses taken up count", 10, colour(INK_SOFT)),
          on=pan, group="b", same="count")
    tx = x + 12 + FIGURE_W + 16
    cols = [(proj_column("dim_library_item", "item_id", display="ID"), TAKEN_COLS[0]),
            (proj_column("dim_library_item", "item_name", display="Prompt"), TAKEN_COLS[1]),
            (proj_column("dim_library_item", "owner_team", display="Made by"), TAKEN_COLS[2]),
            (proj_measure("Second team", "Taken up by"), TAKEN_COLS[3]),
            (proj_measure("Second team from", "From"), TAKEN_COLS[4])]
    p.add("p5_taken_table", (tx, y + 46, table_width(list(TAKEN_COLS)), h - 50), {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [c for c, _ in cols]}}},
        "objects": {
            "total": [{"properties": {"totals": lit("false")}}],
            "columnWidth": [{"properties": {"value": lit(f"{wd}D")}, "selector": {"metadata": c["queryRef"]}}
                            for c, wd in cols],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }, on=pan, group="b", need_w=table_width(list(TAKEN_COLS)), need_h=table_height([1] * 4))

    p.answers = {
        16: [("p5_taken_table", "item_id"), ("p5_taken_table", "Second team"), ("p5_taken_table", "Second team from")],
        17: [("p5_air_chart", "Share of people in the air latest"), ("p5_air_chart", "Share of people in the air baseline"),
             ("p5_points_chart", "Air change points")],
        18: [("p5_impact_chart", "Impact lose time share")],
    }
    return p


if __name__ == "__main__":
    build().write()
    set_page_order(ORDER)
