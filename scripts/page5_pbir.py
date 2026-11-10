#!/usr/bin/env python3
"""Write page 5 (Scale) into the Power BI project's report files.

    python3 scripts/page5_pbir.py

Brief section 6, page 5, "Where has it changed the work?":
- impact in people's own words: the Month 6 check-in answers to "If AI disappeared from
  your work tomorrow, what would change?", per team, counts on the segments;
- share of people in the air against the baseline: each team at its baseline month (named
  by the team) and at Month 6, the Month 6 bar labelled with its change in points (round 7:
  one chart, the change is the label);
- uses taken up beyond the first team: the count, and the prompts by name with the team that
  took each up, the week it started and the runs by other teams (text, so a table; round 8:
  the columns spread across the panel, under the figure band).
"""
from __future__ import annotations

from pbir import (
    GREY, INK, INK_SOFT, MARINE, OFF, PALE, NO_FRAME, Page, body_top, colour, column, figure_band, header, lit,
    panel, proj_column, proj_measure, pt, table_height, table_width, textbox,
    BODY_END, GAP, HEADER_SECOND_H, HEADER_SECOND_Y,
)

PAGE = "f6b2c4d8e1a3f5b7c9d1"

ROW2_H = 6 + 48 + 2 + table_height([1] * 4) + 4   # the figure band, then four prompts
ROW2_Y = BODY_END - ROW2_H
ROW1_Y = HEADER_SECOND_Y + HEADER_SECOND_H + GAP
ROW1_H = ROW2_Y - GAP - ROW1_Y
IMPACT_PANEL = (16, ROW1_Y, 616, ROW1_H)
AIR_PANEL = (648, ROW1_Y, 616, ROW1_H)
TAKEN_PANEL = (16, ROW2_Y, 1248, ROW2_H)
# ID, prompt, made by, taken up by, from, runs by other teams: spread over the panel's 1224 px
TAKEN_COLS = (100, 340, 170, 170, 140, 220)
IMPACT_MIN_SHARE = 17 / 120            # the thinnest segment: Legal, "I would lose time every week"
AIR_MAX = 0.603                        # Consulting at Month 6 (scripts/page5_figures.py)
IMPACT = (("Impact lose time share", "I would lose time every week", MARINE),
          ("Impact a little share", "A little", PALE), ("Impact nothing share", "Nothing", GREY))
AIR = (("Share of people in the air baseline", "Baseline month", GREY),
       ("Share in the air latest with change", "Month 6", MARINE))


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
            "labels": [{"properties": {"show": lit("true")}}] + [
                {"properties": {"color": colour(INK)}, "selector": {"metadata": f"_Measures.{m}"}}
                for m, _, c in measures if c == PALE],   # round 8: dark labels on the pale fill
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": axis}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{end}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def panel_top(p: Page, key: str, box, title: str, sub: str | None, legend_items=None, legend_w=0, row=None):
    x, y, w, h = box
    pan, inner = f"p5_{key}_panel", w - 24
    p.add(pan, box, panel(), z=2000, row=row)
    p.add(f"p5_{key}_title", (x + 12, y + 6, inner, 20), heading(title), on=pan, group="t")
    if sub:
        p.add(f"p5_{key}_sub", (x + 12, y + 26, inner - legend_w, 18), subtitle(sub), on=pan, group="t", kind="subtitle")
    if legend_items:
        p.add(f"p5_{key}_legend", (x + 12 + inner - legend_w, y + 26, legend_w, 18), legend(legend_items),
              on=pan, group="t", legend=True)
    return pan, x, y, w, h, inner


def build() -> Page:
    p = Page(PAGE, "Scale", number=5)
    header(p, "p5", "Scale", "Where has it changed the work?",
           "Read from the question log, the usage dashboards and the check-in", "Week 1 to Week 24")
    assert body_top(p) == ROW1_Y

    # ---- impact in people's own words
    pan, x, y, w, h, inner = panel_top(p, "impact", IMPACT_PANEL, "Impact in people's own words",
                                       "Month 6: if AI disappeared tomorrow?",
                                       tuple((d, c) for _, d, c in IMPACT), 330, "top")
    p.add("p5_impact_chart", (x + 12, y + 46, inner, h - 50), by_team("barChart", IMPACT),
          on=pan, group="c", categories=6, label_min_share=IMPACT_MIN_SHARE)

    # ---- share in the air: baseline against Month 6, the change in points on the Month 6 label
    pan, x, y, w, h, inner = panel_top(p, "air", AIR_PANEL, "Share of people in the air against the baseline",
                                       "Baseline month by each team, then Month 6",
                                       tuple((d, c) for _, d, c in AIR), 190, "top")
    p.add("p5_air_chart", (x + 12, y + 46, inner, h - 50),
          by_team("clusteredBarChart", AIR, ("dim_team", "team_baseline_label"), 0.8, inner_padding=10),
          on=pan, group="c", categories=6, series=2, max_value=AIR_MAX)

    # ---- uses taken up beyond the first team
    x, y, w, h = TAKEN_PANEL
    pan = "p5_taken_panel"
    p.add(pan, TAKEN_PANEL, panel(), z=2000)
    band = figure_band(p, "p5_taken", pan, x, y, w, "Uses taken up beyond the first team",
                       "Uses taken up beyond the first team", count="Uses taken up count", longest="4")
    cols = [(proj_column("dim_library_item", "item_id", display="ID"), TAKEN_COLS[0]),
            (proj_column("dim_library_item", "item_name", display="Prompt"), TAKEN_COLS[1]),
            (proj_column("dim_library_item", "owner_team", display="Made by"), TAKEN_COLS[2]),
            (proj_measure("Second team", "Taken up by"), TAKEN_COLS[3]),
            (proj_measure("Second team from", "From"), TAKEN_COLS[4]),
            (proj_measure("Runs by other teams", "Runs by other teams"), TAKEN_COLS[5])]
    p.add("p5_taken_table", (x + 12, band + 2, w - 24, y + h - 4 - band - 2), {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [c for c, _ in cols]}}},
        "objects": {
            "total": [{"properties": {"totals": lit("false")}}],
            "columnWidth": [{"properties": {"value": lit(f"{wd}D")}, "selector": {"metadata": c["queryRef"]}}
                            for c, wd in cols],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }, on=pan, group="c", need_w=table_width(list(TAKEN_COLS)), need_h=table_height([1] * 4))

    p.answers = {
        16: [("p5_taken_table", "item_id"), ("p5_taken_table", "Second team"), ("p5_taken_table", "Second team from"),
             ("p5_taken_table", "Runs by other teams")],
        17: [("p5_air_chart", "Share in the air latest with change"), ("p5_air_chart", "Share of people in the air baseline")],
        18: [("p5_impact_chart", "Impact lose time share")],
    }
    return p


if __name__ == "__main__":
    build().write()
