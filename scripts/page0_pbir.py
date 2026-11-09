#!/usr/bin/env python3
"""Write page 0 (Rollout review) into the Power BI project's report files.

    python3 scripts/page0_pbir.py

Every visual on the page is replaced. The checks in scripts/pbir.py run first and the
page is not written if any fails. Close Power BI Desktop on the PC before pulling.
"""
from __future__ import annotations

from pbir import (
    OFF, WILDCARD, Page, colour, column, field_id, INK_SOFT, lit,
    measure, navigator, panel, proj_column, proj_measure, text, textbox,
)

PAGE = "93ede836331e460c840c"

# ---------------------------------------------------------------- layout, 1280 by 720
NAV = (16, 6, 1248, 30)
TITLE = (16, 38, 1248, 56)
HEADER_LINE = (16, 94, 1248, 28)

TILE_Y, TILE_W, TILE_H = 128, 300, 338
TILE_XS = (16, 332, 648, 964)
# inside a tile: (offset from the tile top, height); x is tile x + 12, width 276
IN_TEXT = (6, 64)      # stage name, 14 bold; question, 10 (one or two lines)
IN_LABEL = (70, 40)    # the figure's label, 10, up to two lines; fixed so figures align
IN_CARD = (110, 124)   # figure 28, then verdict, trend, threshold
IN_LINE = (234, 100)   # sparkline, months 2 to 6

RULE = (16, 470, 1248, 24)

SPLIT_HEAD = (16, 500, 520, 26)
SPLIT_LEGEND = (536, 500, 408, 26)
SPLIT_BASE = (16, 528, 456, 184)
SPLIT_LATEST = (488, 528, 456, 184)
MOVED_PANEL = (960, 500, 304, 212)

TILES = (
    ("Foundation", "Which uses matter most, and where do people get stuck?",
     "Requests matched to a tested prompt that already exists"),
    ("Execution", "Does it hold up in everyday use?", "Repeat use within 30 days"),
    ("Refinement", "What earns its place, and at what cost?",
     "Tested prompts that pass on the smaller model"),
    ("Scale", "Where has it changed the work?",
     "Share of people in the air against the baseline, in points"),
)
RULE_TEXT = ("How to read a tile: Working when the month's figure meets the threshold. "
             "Trend: against two check-ins earlier, flat within 1 point. "
             "The line runs from Month 2 to Month 6.")

BOLD = {"fontWeight": "bold"}


def pt(n: int, bold: bool = False) -> dict:
    return {"fontSize": f"{n}pt", **(BOLD if bold else {})}


# ---------------------------------------------------------------- visuals
def tile_card(stage: str, label: str) -> dict:
    tile = f"{stage} tile"
    meta = f"_Measures.{tile}"
    ids = {k: field_id() for k in ("verdict", "trend", "threshold")}

    def ref(kind: str, order: int) -> dict:
        return {"properties": {"value": {"expr": measure(f"{stage} {kind}")}},
                "selector": {"data": WILDCARD, "metadata": meta, "id": ids[kind], "order": order}}

    return {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj_measure(tile, label)]}}},
        "objects": {
            "referenceLabel": [ref("verdict", 0), ref("trend", 1), ref("threshold", 2)],
            "value": [{"properties": {"fontSize": lit("28D")}, "selector": {"id": "default"}}],
            # the label is a text box above the card, so all four figures share one line
            "label": [{"properties": OFF, "selector": {"metadata": meta}}],
            "divider": [{"properties": OFF, "selector": {"id": "default"}}],
            "referenceLabelTitle": [{"properties": OFF, "selector": {"metadata": meta}}],
            "referenceLabelValue": [
                {"properties": {"valueFontSize": lit("10D")}, "selector": {"metadata": meta}},
                {"properties": {"valueBold": lit("true"), "valueFontSize": lit("10D")},
                 "selector": {"metadata": meta, "id": ids["verdict"]}},
                {"properties": {"valueFontColor": {"solid": {"color": {"expr": measure(f"{stage} verdict colour")}}}},
                 "selector": {"data": WILDCARD, "metadata": meta, "id": ids["verdict"]}},
                {"properties": {"valueFontSize": lit("10D")},
                 "selector": {"metadata": meta, "id": ids["trend"]}},
                {"properties": {"valueFontSize": lit("9D"), "valueFontColor": colour(INK_SOFT)},
                 "selector": {"metadata": meta, "id": ids["threshold"]}},
            ],
            "fillCustom": [{"properties": OFF}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def sparkline(stage: str) -> tuple[dict, dict]:
    visual = {
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
        "visualContainerObjects": {"title": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }
    filters = {"filters": [{
        "name": f"notMonth1{stage}",
        "field": column("dim_month", "month_label"),
        "type": "Categorical",
        "filter": {"Version": 2, "From": [{"Name": "d", "Entity": "dim_month", "Type": 0}],
                   "Where": [{"Condition": {"Not": {"Expression": {"In": {
                       "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                                   "Property": "month_label"}}],
                       "Values": [[{"Literal": {"Value": "'Month 1'"}}]]}}}}}]},
        "objects": {"general": [{"properties": {"isInvertedSelectionMode": lit("true")}}]},
    }]}
    return visual, filters


def stage_split(measure_name: str, title: str) -> dict:
    # Identical but for the measure and title, so the two plots share width, height and order.
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
            "labels": [{"properties": {"show": lit("true"), "labelPrecision": lit("0L")}}],
            "legend": [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("true"), "text": text(title)}}],
            "subTitle": [{"properties": OFF}],
        },
        "drillFilterOtherVisuals": True,
    }


def moved_up_card() -> dict:
    main = "Moved up since last count"
    meta = f"_Measures.{main}"
    return {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [
            proj_measure(main, "People who moved up a checkpoint, Month 5 to Month 6")]}}},
        "objects": {
            "referenceLabel": [{"properties": {"value": {"expr": measure("Seats arrived")}},
                                "selector": {"data": WILDCARD, "metadata": meta,
                                             "id": field_id(), "order": 0}}],
            "value": [{"properties": {"fontSize": lit("36D")}, "selector": {"id": "default"}}],
            "label": [{"properties": {"fontSize": lit("10D"), "textWrap": lit("true")},
                       "selector": {"id": "default"}}],
            "referenceLabelValue": [{"properties": {"valueFontSize": lit("14D")},
                                     "selector": {"metadata": meta}}],
            "fillCustom": [{"properties": OFF}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def header_line() -> dict:
    # as Desktop wrote it on the PC
    return {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj_measure("Header line")]}}},
        "objects": {
            "value": [{"properties": {"fontSize": lit("11D")}, "selector": {"id": "default"}}],
            "label": [{"properties": OFF, "selector": {"metadata": "_Measures.Header line"}}],
            "fillCustom": [{"properties": OFF}],
        },
        "visualContainerObjects": {"title": [{"properties": OFF}],
                                   "background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def build() -> Page:
    p = Page(PAGE)
    p.add("p0_navigator", NAV, navigator(), z=0)
    p.add("p0_title", TITLE, textbox([
        [("Rollout review", pt(18, bold=True))],
        [("Read from the question log, the usage dashboards, the library's records, "
          "the run log and the check-in · ", pt(10)),
         ("Week 1 to Week 24, six check-ins", pt(10, bold=True))],
    ]))
    p.add("p0_header_line", HEADER_LINE, header_line())

    for x, (stage, question, label) in zip(TILE_XS, TILES):
        key = stage.lower()
        pan = f"p0_{key}_panel"

        def inner(off_h):
            return (x + 12, TILE_Y + off_h[0], TILE_W - 24, off_h[1])

        p.add(pan, (x, TILE_Y, TILE_W, TILE_H), panel(), z=2000, same="tile")
        p.add(f"p0_{key}_text", inner(IN_TEXT), textbox([
            [(stage, pt(14, bold=True))], [(question, pt(10))]]), on=pan, same="tile text")
        p.add(f"p0_{key}_label", inner(IN_LABEL), textbox([[(label, pt(10))]]),
              on=pan, same="tile label")
        p.add(f"p0_{key}_card", inner(IN_CARD), tile_card(stage, label), on=pan, same="tile card")
        line, filters = sparkline(stage)
        p.add(f"p0_{key}_sparkline", inner(IN_LINE), line, on=pan, same="sparkline",
              extra={"filterConfig": filters})

    p.add("p0_rule", RULE, textbox([[(RULE_TEXT, pt(9))]]))

    p.add("p0_split_head", SPLIT_HEAD, textbox([[
        ("Stage split by team, by source placement", pt(12, bold=True))]]))
    p.add("p0_split_legend", SPLIT_LEGEND, textbox([[
        ("■", pt(12)), (" On the ground     ", pt(10)),
        ("■", pt(12)), (" At the gate     ", pt(10)),
        ("■", pt(12)), (" In the air", pt(10))]]))
    p.add("p0_split_baseline", SPLIT_BASE,
          stage_split("Stage split baseline", "At each team's baseline month"),
          z=2000, same="stage chart", categories=6)
    p.add("p0_split_latest", SPLIT_LATEST,
          stage_split("Stage split latest", "Latest count, Month 6"),
          z=2000, same="stage chart", categories=6)

    mx, my, mw, mh = MOVED_PANEL
    p.add("p0_moved_panel", MOVED_PANEL, panel(), z=2000)
    p.add("p0_moved_title", (mx + 12, my + 6, mw - 24, 30), textbox([[
        ("Moved up since the last count", pt(12, bold=True))]]), on="p0_moved_panel")
    p.add("p0_moved_card", (mx + 12, my + 38, mw - 24, mh - 44), moved_up_card(),
          on="p0_moved_panel")
    return p


if __name__ == "__main__":
    build().write()
