#!/usr/bin/env python3
"""Write page 2 (Foundation) into the Power BI project's report files.

    python3 scripts/page2_pbir.py

Brief section 6, page 2, "Which uses matter most, and where do people get stuck?":
- uses logged and ranked, Month 1 against Month 6 (two bar charts side by side on one
  scale, so the change is on the page without a slicer), and beside them every month as
  paired columns: Rules and allowed use (amber) against all other uses (marine). Columns, not
  lines (round 3): two lines crossing put Month 1's labels on top of each other, and each
  column carries its own label;
- requests matched to a tested prompt that already exists (the Foundation headline), whole
  period, with its count;
- prompts tested against an answer key written first, with its count;
- the usage baseline by team.
Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    AMBER, INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, colour, filter_in, header, lit, measure,
    panel, proj_column, proj_measure, pt, set_page_order, textbox, value_card,
)

PAGE = "c3f8d1e5a7b9c2d4e6f8"
PAGE0, PAGE1 = "93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10"

# ---------------------------------------------------------------- body (header: pbir.header)
RANK_PANEL = (16, 102, 1248, 358)
RANK_CHART_W, LINE_CHART_W, PART_GAP = 392, 408, 16
RANK_END = 60          # one scale for both months: the longest bar is 52 (Month 1, Rules and allowed use)
LINE_END = 125         # the highest point is 106 (all other uses, Month 5)
BOTTOM_Y, BOTTOM_H = 464, 252
MATCHED_PANEL = (16, BOTTOM_Y, 412, BOTTOM_H)     # wide enough for the measure name on one line
KEY_PANEL = (444, BOTTOM_Y, 412, BOTTOM_H)
BASELINE_PANEL = (872, BOTTOM_Y, 392, BOTTOM_H)
BASELINE_END = 0.6     # the highest baseline is 51.2% (Consulting, Technology)


def heading(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def heading_with_note(s: str, note: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK)), (" · " + note, pt(9, color=INK_SOFT))]])


def subtitle(s: str) -> dict:
    return textbox([[(s, pt(9, color=INK_SOFT))]])


def bar_chart(measure_name: str, category: tuple[str, str], end: float, sort_by_value: bool) -> dict:
    sort_field = measure(measure_name) if sort_by_value else proj_column(*category)["field"]
    return {
        "visualType": "clusteredBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column(*category, active=True)]},
                "Y": {"projections": [proj_measure(measure_name)]},
            },
            "sortDefinition": {"sort": [{"field": sort_field,
                                         "direction": "Descending" if sort_by_value else "Ascending"}],
                               "isDefaultSort": False},
        },
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(MARINE)},
                           "selector": {"metadata": f"_Measures.{measure_name}"}}],
            "labels": [{"properties": {"show": lit("true")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{end}D"),
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
            "valueAxis": [{"properties": {"show": lit("false"), "start": lit("0D"), "end": lit(f"{LINE_END}D"),
                                          "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def kpi(p: Page, key: str, box, measure_name: str, period: str, count: str) -> None:
    """A panel titled with the measure's name; a grey caption for the period; the figure,
    with its count line directly under it."""
    x, y, w, h = box
    pan, inner = f"p2_{key}_panel", w - 24
    p.add(pan, box, panel(), z=2000, row="bottom")
    p.add(f"p2_{key}_title", (x + 12, y + 6, inner, 20), heading(measure_name), on=pan, group="t")
    p.add(f"p2_{key}_sub", (x + 12, y + 26, inner, 18), subtitle(period), on=pan, group="t")
    p.add(f"p2_{key}_figure", (x + 12, y + 54, inner, 62), value_card(measure_name, 36),
          on=pan, group="b", same="kpi figure")
    p.add(f"p2_{key}_count", (x + 12, y + 116, inner, 24), value_card(count, 10, colour(INK_SOFT)),
          on=pan, group="b", same="kpi count")


def build() -> Page:
    p = Page(PAGE, "Foundation", number=2)
    header(p, "p2", "Foundation",
           "Read from the question log, the usage dashboards and the library's records", "Week 1 to Week 24",
           question="Which uses matter most, and where do people get stuck?")

    # ---- uses ranked: Month 1, Month 6 on one scale, then every month as two lines
    x, y, w, h = RANK_PANEL
    pan = "p2_rank_panel"
    p.add(pan, RANK_PANEL, panel(), z=2000)
    p.add("p2_rank_title", (x + 12, y + 6, w - 24, 20), heading_with_note(
        "Uses logged and ranked",
        "questions in each use, most first · Month 1 and Month 6 on one scale, then every month"),
        on=pan, group="t")
    chart_y, chart_h = y + 56, h - 60
    for i, (m, label) in enumerate((("Month 1", "Month 1, the first check-in"), ("Month 6", "Month 6, the latest"))):
        cx = x + 12 + i * (RANK_CHART_W + PART_GAP)
        key = m.replace(" ", "").lower()
        p.add(f"p2_rank_{key}_name", (cx, y + 36, RANK_CHART_W, 20), heading(label),
              on=pan, group="c", same="rank name")
        p.add(f"p2_rank_{key}", (cx, chart_y, RANK_CHART_W, chart_h),
              bar_chart("Uses logged and ranked", ("dim_category", "category"), RANK_END, sort_by_value=True),
              on=pan, group="c", same="rank chart", categories=7, max_value=52,
              extra={"filterConfig": {"filters": [filter_in("dim_month", "month_label", [m], f"only{key}")]}})
    lx = x + 12 + 2 * (RANK_CHART_W + PART_GAP)
    p.add("p2_month_name", (lx, y + 36, LINE_CHART_W, 20), textbox([[
        ("By month:", pt(10, bold=True, color=INK)),
        ("  ■", pt(9, color=AMBER)), (" Rules and allowed use  ", pt(9, color=INK_SOFT)),
        ("■", pt(9, color=MARINE)), (" All other uses", pt(9, color=INK_SOFT))]]),
        on=pan, group="c", legend=True)
    p.add("p2_month_chart", (lx, chart_y, LINE_CHART_W, chart_h), by_month(), on=pan, group="c",
          max_value=106, categories=6, series=2, longest_category="Month 6", longest_label="106")

    # ---- the two shares, each titled with its measure
    kpi(p, "matched", MATCHED_PANEL, "Requests matched to a tested prompt that already exists",
        "Week 1 to Week 24, every question", "Requests matched count")
    kpi(p, "key", KEY_PANEL, "Prompts tested against an answer key written first",
        "Every library item, Week 1 to Week 24", "Answer key first count")

    # ---- usage baseline by team
    x, y, w, h = BASELINE_PANEL
    pan, inner = "p2_baseline_panel", w - 24
    p.add(pan, BASELINE_PANEL, panel(), z=2000, row="bottom")
    p.add("p2_baseline_title", (x + 12, y + 6, inner, 20), heading("Usage baseline by team"), on=pan, group="t")
    p.add("p2_baseline_sub", (x + 12, y + 26, inner, 18), subtitle(
        "Weekly active share, each team's first four weeks with seats"), on=pan, group="t")
    p.add("p2_baseline_chart", (x + 12, y + 46, inner, 202),
          bar_chart("Usage baseline by team", ("dim_team", "team"), BASELINE_END, sort_by_value=False),
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
    set_page_order([PAGE0, PAGE1, PAGE])
