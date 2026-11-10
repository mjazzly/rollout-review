#!/usr/bin/env python3
"""Write page 0 (Rollout review) into the Power BI project's report files.

    python3 scripts/page0_pbir.py

Every visual on the page is replaced. The checks in scripts/pbir.py run first and the
page is not written if any fails. Close Power BI Desktop on the PC before pulling.
"""
from __future__ import annotations

from pbir import (
    INK, INK_SOFT, OFF, STAGES, Page, caption, colour, column, filter_in, header, lit,
    measure_colour, panel, proj_column, proj_measure, pt, text,
    textbox, value_card, value_is, NO_FRAME,
)

PAGE = "93ede836331e460c840c"

# ---------------------------------------------------------------- header strip
# pbir.header(): the title with the sources at the right of its row (round 5, every page);
# page 0 has no question, so its header line card sits on the second line
HEADER_LINE = (16, 70, 1248, 24)        # card, 11, middle of the row

# ---------------------------------------------------------------- tiles
TILE_Y, TILE_W, TILE_H = 98, 300, 350
TILE_XS = (16, 332, 648, 964)
# Inside a tile, four groups 10 apart (2 above the sparkline, which pads itself):
#   a  stage name and question
#   b  the figure's caption, sitting on the figure
#   c  verdict, trend, threshold
#   d  sparkline, Month 2 to Month 6
# (offset from the tile top, height); x is tile x + 12, width 276
A_TEXT = (6, 62)
B_CAPTION = (78, 34)        # 9, grey, two lines; a one-line caption sits on the bottom
B_FIGURE = (112, 54)        # 28
C_VERDICT = (176, 24)       # 10, amber when Not yet working
C_TREND = (200, 24)         # 10
C_THRESHOLD = (224, 24)     # 9, grey
D_LINE = (250, 100)

# The rule line ("How to read a tile") moved to the Notes page in round 7.

# ---------------------------------------------------------------- bottom row
BOTTOM_Y, BOTTOM_H = 452, 242       # to BODY_END (694), above the sources line
SPLIT_BASE = (16, BOTTOM_Y, 456, BOTTOM_H)
SPLIT_LATEST = (488, BOTTOM_Y, 456, BOTTOM_H)
MOVED = (960, BOTTOM_Y, 304, BOTTOM_H)

TILES = (
    ("Foundation", "Which uses matter most, and where do people get stuck?",
     "Requests matched to a tested prompt that already exists"),
    ("Execution", "Does it hold up in everyday use?", "Repeat use within 30 days"),
    ("Refinement", "What earns its place, and at what cost?",
     "Tested prompts that pass on the smaller model"),
    ("Scale", "Where has it changed the work?",
     "Share of people in the air against the baseline, in points"),
)



# ---------------------------------------------------------------- visuals
def sparkline(stage: str) -> dict:
    return {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [proj_column("dim_month", "month_label", active=True)]},
            "Y": {"projections": [proj_measure(f"{stage} tile")]}}},
        "objects": {
            "categoryAxis": [{"properties": OFF}],
            "valueAxis": [{"properties": {"start": lit("0D"), "gridlineShow": lit("false"),
                                          "show": lit("false")}}],
            "legend": [{"properties": OFF}],
            "lineStyles": [{"properties": {"strokeWidth": lit("2D"), "showMarker": lit("true"),
                                           "markerSize": lit("3D")}}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def stage_split(measure_name: str) -> dict:
    # Identical but for the measure, so the two plots share width, height and order.
    return {
        "visualType": "hundredPercentStackedBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
                "Series": {"projections": [proj_column("dim_checkpoint_source", "stage")]},
                "Y": {"projections": [proj_measure(measure_name)]},
            },
            "sortDefinition": {"sort": [{"field": column("dim_team", "team"), "direction": "Ascending"}],
                               "isDefaultSort": False},
        },
        "objects": {
            "dataPoint": [{"properties": {"fill": colour(c)},
                           "selector": value_is("dim_checkpoint_source", "stage", s)}
                          for s, c in STAGES],
            "labels": [{"properties": OFF}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}], "subTitle": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def header_line() -> dict:
    # as Desktop wrote it on the PC, centred in its row
    return {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj_measure("Header line")]}}},
        "objects": {
            "value": [{"properties": {"fontSize": lit("11D")}, "selector": {"id": "default"}}],
            "label": [{"properties": OFF, "selector": {"metadata": "_Measures.Header line"}}],
            "layout": [{"properties": {"alignment": text("middle")}}],
            "fillCustom": [{"properties": OFF}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def panel_title(s: str) -> dict:
    return textbox([[(s, pt(10, bold=True, color=INK))]])


def build() -> Page:
    p = Page(PAGE, "Rollout review")
    header(p, "p0", "Rollout review", None,
           "Read from the question log, the usage dashboards, the library's records, the run log and the check-in",
           "Week 1 to Week 24, six check-ins")
    p.add("p0_header_line", HEADER_LINE, header_line())

    for x, (stage, question, label) in zip(TILE_XS, TILES):
        key = stage.lower()
        pan = f"p0_{key}_panel"

        def piece(name, off_h, visual, group, same, **kw):
            box = (x + 12, TILE_Y + off_h[0], TILE_W - 24, off_h[1])
            p.add(f"p0_{key}_{name}", box, visual, on=pan, group=group, same=same, **kw)

        p.add(pan, (x, TILE_Y, TILE_W, TILE_H), panel(), z=2000, same="tile")
        piece("text", A_TEXT, textbox([[(stage, pt(14, bold=True, color=INK))],
                                       [(question, pt(10, color=INK_SOFT))]]), "a", "tile text")
        piece("caption", B_CAPTION, caption(label, 9, TILE_W - 24, 2), "b", "tile caption")
        piece("figure", B_FIGURE, value_card(f"{stage} tile", 28, display=label), "b", "tile figure")
        piece("verdict", C_VERDICT,
              value_card(f"{stage} verdict", 10, measure_colour(f"{stage} verdict colour")),
              "c", "tile line")
        piece("trend", C_TREND, value_card(f"{stage} trend", 10), "c", "tile line")
        piece("threshold", C_THRESHOLD, value_card(f"{stage} threshold", 9, colour(INK_SOFT)),
              "c", "tile line")
        piece("sparkline", D_LINE, sparkline(stage), "d", "sparkline",
              extra={"filterConfig": {"filters": [
                  filter_in("dim_month", "month_label", ["Month 1"], f"notMonth1{stage}", negate=True)]}})

    # stage split: two panels, each a title then its chart; the shared legend at the top right of
    # the right one
    for pan, box, title, title_w, m in (
            ("p0_split_base_panel", SPLIT_BASE, "Stage by team, at its baseline month", 432, "Stage split baseline"),
            ("p0_split_latest_panel", SPLIT_LATEST, "Stage by team, Month 6", 160, "Stage split latest")):
        x, y, w, h = box
        p.add(pan, box, panel(), z=2000, row="bottom")
        p.add(f"{pan}_title", (x + 12, y + 6, title_w, 22), panel_title(title), on=pan, group="t")
        p.add(f"{pan}_chart", (x + 12, y + 30, w - 24, h - 34), stage_split(m), on=pan, group="c",
              same="stage chart", categories=6)
    legend = []
    for n, (stage, hex_) in enumerate(STAGES):
        legend += [("■", pt(9, color=hex_)),
                   (f" {stage}" + ("  " if n < 2 else ""), pt(9, color=INK_SOFT))]
    p.add("p0_split_legend", (SPLIT_LATEST[0] + 12 + 160, SPLIT_LATEST[1] + 6, 272, 22),
          textbox([legend]), on="p0_split_latest_panel", group="t", legend=True)
    p.awaiting["p0_split_latest_panel_chart"] = ("labels on the In the air share only: a hand reference "
                                                 "(BUILD-STEPS step 54)")

    # moved up: title; the count with its caption; seats arrived with its caption, apart
    x, y, w, h = MOVED
    inner = w - 24
    p.add("p0_moved_panel", MOVED, panel(), z=2000, row="bottom")
    p.add("p0_moved_title", (x + 12, y + 6, inner, 22), panel_title("Moved up since the last count"),
          on="p0_moved_panel", group="t")
    p.add("p0_moved_caption", (x + 12, y + 38, inner, 34),
          caption("People who moved up a checkpoint,\nMonth 5 to Month 6", 9, inner, 2),
          on="p0_moved_panel", group="b")
    p.add("p0_moved_figure", (x + 12, y + 72, inner, 62), value_card("Moved up since last count", 36),
          on="p0_moved_panel", group="b")
    p.add("p0_seats_caption", (x + 12, y + 144, inner, 18),
          caption("Seats arrived over the same month, counted apart", 9, inner, 1),
          on="p0_moved_panel", group="c")
    p.add("p0_seats_figure", (x + 12, y + 162, inner, 30), value_card("Seats arrived", 14),
          on="p0_moved_panel", group="c")
    return p


if __name__ == "__main__":
    build().write()
