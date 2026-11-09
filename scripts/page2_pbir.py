#!/usr/bin/env python3
"""Write page 2 (Foundation) into the Power BI project's report files.

    python3 scripts/page2_pbir.py

Brief section 6, page 2, "Which uses matter most, and where do people get stuck?":
- uses logged and ranked, Month 1 against Month 6 (two bar charts side by side on one
  scale, so the change is on the page without a slicer);
- requests matched to a tested prompt that already exists (the Foundation headline), whole
  period, with its count;
- prompts tested against an answer key written first, with its count;
- the usage baseline by team.
Every visual on the page is replaced; the checks in scripts/pbir.py run first.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, MARINE, OFF, NO_FRAME, Page, caption, colour, filter_in, lit, measure,
    navigator, panel, proj_column, proj_measure, pt, set_page_order, textbox, value_card,
)

PAGE = "c3f8d1e5a7b9c2d4e6f8"
PAGE0, PAGE1 = "93ede836331e460c840c", "b7e4c2a91d3f5e6a8c10"

# ---------------------------------------------------------------- header strip
NAV = (16, 4, 1248, 32)
TITLE = (16, 36, 1248, 34)
SOURCE = (16, 70, 1248, 22)

# ---------------------------------------------------------------- body
RANK_PANEL = (16, 96, 1248, 364)
RANK_CHART_W, RANK_CHART_H = 604, 304
RANK_END = 60          # one scale for both months: the longest bar is 52 (Month 1, Rules and allowed use)
BOTTOM_Y, BOTTOM_H = 464, 252
MATCHED_PANEL = (16, BOTTOM_Y, 300, BOTTOM_H)
KEY_PANEL = (332, BOTTOM_Y, 300, BOTTOM_H)
BASELINE_PANEL = (648, BOTTOM_Y, 616, BOTTOM_H)
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


def kpi(p: Page, key: str, box, title: str, note: str, label: str, figure: str, count: str) -> None:
    """A panel: title and note; the caption sitting on the figure; the count under it."""
    x, y, w, h = box
    pan, inner = f"p2_{key}_panel", w - 24
    p.add(pan, box, panel(), z=2000, row="bottom")
    p.add(f"p2_{key}_title", (x + 12, y + 6, inner, 20), heading(title), on=pan, group="t")
    p.add(f"p2_{key}_sub", (x + 12, y + 26, inner, 18), subtitle(note), on=pan, group="t")
    p.add(f"p2_{key}_caption", (x + 12, y + 54, inner, 34), caption(label, 9, inner, 2),
          on=pan, group="b", same="kpi caption")
    p.add(f"p2_{key}_figure", (x + 12, y + 88, inner, 62), value_card(figure, 36),
          on=pan, group="b", same="kpi figure")
    p.add(f"p2_{key}_count", (x + 12, y + 160, inner, 24), value_card(count, 10, colour(INK_SOFT)),
          on=pan, group="c", same="kpi count")


def build() -> Page:
    p = Page(PAGE, "Foundation", number=2)
    p.add("p2_navigator", NAV, navigator(), z=0)
    p.add("p2_title", TITLE, textbox([[
        ("Foundation", pt(18, bold=True, color=INK)),
        ("   Which uses matter most, and where do people get stuck?", pt(14, color=INK_SOFT))]]))
    p.add("p2_source", SOURCE, textbox([[
        ("Read from the question log, the usage dashboards and the library's records · ", pt(10, color=INK_SOFT)),
        ("Week 1 to Week 24; the ranking compares Month 1 with Month 6", pt(10, bold=True, color=INK_SOFT))]]))

    # ---- uses ranked, Month 1 against Month 6
    x, y, w, h = RANK_PANEL
    pan = "p2_rank_panel"
    p.add(pan, RANK_PANEL, panel(), z=2000)
    p.add("p2_rank_title", (x + 12, y + 6, w - 24, 20), heading_with_note(
        "Uses logged and ranked", "questions in each use, most first · Month 1 against Month 6, one scale"),
        on=pan, group="t")
    for i, (m, label) in enumerate((("Month 1", "Month 1, the first check-in"), ("Month 6", "Month 6, the latest"))):
        cx = x + 12 + i * (RANK_CHART_W + 16)
        key = m.replace(" ", "").lower()
        p.add(f"p2_rank_{key}_name", (cx, y + 36, RANK_CHART_W, 20), heading(label),
              on=pan, group="c", same="rank name")
        p.add(f"p2_rank_{key}", (cx, y + 56, RANK_CHART_W, RANK_CHART_H),
              bar_chart("Uses logged and ranked", ("dim_category", "category"), RANK_END, sort_by_value=True),
              on=pan, group="c", same="rank chart", categories=7, max_value=52,
              extra={"filterConfig": {"filters": [filter_in("dim_month", "month_label", [m], f"only{key}")]}})

    # ---- the headline and the answer key share
    kpi(p, "matched", MATCHED_PANEL, "The Foundation headline", "Whole period, Week 1 to Week 24",
        "Requests matched to a tested prompt that already exists",
        "Requests matched to a tested prompt that already exists", "Requests matched count")
    kpi(p, "key", KEY_PANEL, "Tested before going in the library", "All library items",
        "Prompts tested against an answer key written first",
        "Prompts tested against an answer key written first", "Answer key first count")

    # ---- usage baseline by team
    x, y, w, h = BASELINE_PANEL
    pan, inner = "p2_baseline_panel", w - 24
    p.add(pan, BASELINE_PANEL, panel(), z=2000, row="bottom")
    p.add("p2_baseline_title", (x + 12, y + 6, inner, 20), heading("Usage baseline by team"), on=pan, group="t")
    p.add("p2_baseline_sub", (x + 12, y + 26, inner, 18), subtitle(
        "Weekly active share over each team's first four weeks after its seats arrive"), on=pan, group="t")
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
