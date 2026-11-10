#!/usr/bin/env python3
"""Write page 2 (Foundation) into the Power BI project's report files.

    python3 scripts/page2_pbir.py

Brief section 6, page 2, "Which uses matter most, and where do people get stuck?":
- uses logged and ranked, Month 1 against Month 6 on one scale; each bar split into the
  questions matched to a tested prompt (marine) and not matched (amber), so demand without
  coverage shows (round 7; both months split, so one legend reads both);
- questions by month: Rules and allowed use (amber) against all other uses (marine), paired
  columns, its own panel (amber means a different thing there);
- requests matched to a tested prompt that already exists, with its count and its line by
  month; prompts tested against an answer key written first, with its count and one bar of
  the 16 written first and 7 not (round 8: no panel taller than its content);
- the usage baseline by team.
"""
from __future__ import annotations

from pbir import (
    AMBER, GREY, INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, body_top, colour, column, figure_band, filter_in,
    header, lit, panel, proj_column, proj_measure, pt, textbox, value_is,
    BODY_END, GAP, HEADER_SECOND_H, HEADER_SECOND_Y,
)

PAGE = "c3f8d1e5a7b9c2d4e6f8"

ROW1_Y = HEADER_SECOND_Y + HEADER_SECOND_H + GAP
ROW1_H = 48 + 7 * 27 + 40 + 4      # the title row, the month names and legend, seven bars
RANK_PANEL = (16, ROW1_Y, 820, ROW1_H)
MONTH_PANEL = (852, ROW1_Y, 412, ROW1_H)
ROW2_Y = ROW1_Y + ROW1_H + GAP
ROW2_H = BODY_END - ROW2_Y
MATCHED_PANEL = (16, ROW2_Y, 412, ROW2_H)     # wide enough for the measure's name on one line
KEY_PANEL = (444, ROW2_Y, 412, ROW2_H)
BASELINE_PANEL = (872, ROW2_Y, 392, ROW2_H)
RANK_END = 60          # one scale for both months: the longest bar is 52 (Month 1, Rules and allowed use)
MONTH_END = 125        # the highest column is 106 (all other uses, Month 5)
BASELINE_END = 0.6     # the highest baseline is 51.2% (Consulting, Technology)
MATCH = (("Matched to a tested prompt", MARINE), ("Not matched", AMBER))
MATCHED_END = 0.7      # the highest month is 57.2% (Month 4; scripts/page2_figures.py)
KEY_ITEMS = 23         # library items: 16 written first, 7 not


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def legend(items) -> dict:
    runs = []
    for n, (name, hex_) in enumerate(items):
        runs += [("■", pt(9, color=hex_)), (f" {name}" + ("  " if n < len(items) - 1 else ""), pt(9, color=INK_SOFT))]
    return textbox([runs])


def ranked(month: str) -> dict:
    """Questions in each use for one month, most first, split matched and not matched."""
    return {
        "visualType": "barChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_category", "category", active=True)]},
            "Series": {"projections": [proj_column("fact_question", "match_label")]},
            "Y": {"projections": [proj_measure("Uses logged and ranked")]}},
            "sortDefinition": {"sort": [{"field": proj_measure("Uses logged and ranked")["field"],
                                         "direction": "Descending"}], "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": value_is("fact_question", "match_label", v)}
                          for v, c in MATCH],
            "labels": [{"properties": {"show": lit("true"), "labelOverflow": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{RANK_END}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def by_month() -> dict:
    series = (("Rules questions", "Rules and allowed use", AMBER), ("Other questions", "All other uses", MARINE))
    return {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure(m, d) for m, d, _ in series]}}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": {"metadata": f"_Measures.{m}"}}
                          for m, _, c in series],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{MONTH_END}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def matched_line() -> dict:
    """Requests matched to a tested prompt, by check-in month (the front page tile's measure)."""
    return {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure("Foundation tile", "Requests matched")]}}},
        "objects": {
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{MATCHED_END}D"),
                                          "gridlineShow": lit("false")}}],
            "legend": [{"properties": OFF}],
            "labels": [{"properties": {"show": lit("true")}}],
            "lineStyles": [{"properties": {"strokeWidth": lit("2D"), "showMarker": lit("true"),
                                           "markerSize": lit("3D")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def key_bar() -> dict:
    """One bar: library items with the answer key written first, and not; each segment labelled
    with its count and what it is (dynamic format strings), so no legend is needed."""
    series = (("Answer key written first items", "Written first", MARINE), ("Answer key not first items", "Not first", GREY))
    return {
        "visualType": "barChart",
        "query": {"queryState": {"Y": {"projections": [proj_measure(m, d) for m, d, _ in series]}}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)}, "selector": {"metadata": f"_Measures.{m}"}}
                          for m, _, c in series],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("false"), "innerPadding": lit("40L")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{KEY_ITEMS}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def baseline_chart() -> dict:
    m = "Usage baseline by team"
    return {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
            "Y": {"projections": [proj_measure(m)]}},
            "sortDefinition": {"sort": [{"field": column("dim_team", "team"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)}, "selector": {"metadata": f"_Measures.{m}"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{BASELINE_END}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def build() -> Page:
    p = Page(PAGE, "Foundation", number=2)
    header(p, "p2", "Foundation", "Which uses matter most, and where do people get stuck?",
           "Read from the question log, the usage dashboards and the library's records", "Week 1 to Week 24")
    assert body_top(p) == ROW1_Y

    # ---- uses ranked, Month 1 and Month 6, matched or not
    x, y, w, h = RANK_PANEL
    pan, inner = "p2_rank_panel", w - 24
    p.add(pan, RANK_PANEL, panel(), z=2000, row="top")
    p.add("p2_rank_title", (x + 12, y + 6, inner, 20), heading("Uses logged and ranked, Month 1 and Month 6"),
          on=pan, group="t")
    p.add("p2_rank_legend", (x + 12 + inner - 270, y + 26, 270, 18), legend(MATCH), on=pan, group="t", legend=True)
    chart_w = (inner - 16) // 2
    for i, m in enumerate(("Month 1", "Month 6")):
        cx = x + 12 + i * (chart_w + 16)
        key = m.replace(" ", "").lower()
        p.add(f"p2_rank_{key}_name", (cx, y + 26, 70, 20), heading(m), on=pan, group="t", same="rank name")
        p.add(f"p2_rank_{key}", (cx, y + 48, chart_w, h - 52), ranked(m), on=pan, group="c", same="rank chart",
              categories=7, extra={"filterConfig": {"filters": [
                  filter_in("dim_month", "month_label", [m], f"only{key}")]}})

    # ---- by month: Rules and allowed use against all other uses
    x, y, w, h = MONTH_PANEL
    pan, inner = "p2_month_panel", w - 24
    p.add(pan, MONTH_PANEL, panel(), z=2000, row="top")
    p.add("p2_month_title", (x + 12, y + 6, inner, 20), heading("Questions by month"), on=pan, group="t")
    p.add("p2_month_legend", (x + 12 + inner - 262, y + 26, 262, 18),
          legend((("Rules and allowed use", AMBER), ("All other uses", MARINE))), on=pan, group="t", legend=True)
    p.add("p2_month_chart", (x + 12, y + 46, inner, h - 50), by_month(), on=pan, group="c",
          max_value=106, categories=6, series=2, longest_category="Month 6", longest_label="106")

    # ---- the two shares, each led by its figure: the line by month, and the 16 / 7 bar under them
    for key, box, m, count, longest, visual, kw in (
            ("matched", MATCHED_PANEL, "Requests matched to a tested prompt that already exists",
             "Requests matched count", "49.5%", matched_line(), {}),
            ("key", KEY_PANEL, "Prompts tested against an answer key written first",
             "Answer key first count", "69.6%", key_bar(), {})):
        x, y, w, h = box
        pan = f"p2_{key}_panel"
        p.add(pan, box, panel(), z=2000, row="bottom")
        band = figure_band(p, f"p2_{key}", pan, x, y, w, m, m, count=count, longest=longest)
        p.add(f"p2_{key}_chart", (x + 12, band + 2, w - 24, y + h - 4 - band - 2), visual, on=pan, group="c", **kw)

    # ---- usage baseline by team
    x, y, w, h = BASELINE_PANEL
    pan, inner = "p2_baseline_panel", w - 24
    p.add(pan, BASELINE_PANEL, panel(), z=2000, row="bottom")
    p.add("p2_baseline_title", (x + 12, y + 6, inner, 20), heading("Usage baseline by team"), on=pan, group="t")
    p.add("p2_baseline_sub", (x + 12, y + 26, inner, 18), subtitle("Weekly active share, first four weeks with seats"),
          on=pan, group="t", kind="subtitle")
    p.add("p2_baseline_chart", (x + 12, y + 46, inner, h - 50), baseline_chart(),
          on=pan, group="c", categories=6, max_value=0.512)

    p.answers = {
        7: [("p2_matched_figure", "Requests matched to a tested prompt that already exists"),
            ("p2_matched_count", "Requests matched count")],
        8: [("p2_rank_month1", "Uses logged and ranked"), ("p2_rank_month6", "Uses logged and ranked")],
        9: [("p2_baseline_chart", "Usage baseline by team")],
    }
    return p


if __name__ == "__main__":
    build().write()
