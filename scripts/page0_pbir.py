#!/usr/bin/env python3
"""Write page 0 (Rollout review) into the Power BI project's report files (PBIR).

The page's visuals are written from the layout below, so the sizes add up and nothing
overlaps. The card, line chart, shape and navigator settings copy the ones Power BI
Desktop wrote on the PC (commit 22ebf37), so every property name is one Desktop uses.

Running it again replaces every visual on the page with the ones below.
Close Power BI Desktop on the PC before pulling the result, and open the .pbip after.

    python3 scripts/page0_pbir.py
"""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "report" / "Rollout review.Report" / "definition" / "pages"
PAGE = "93ede836331e460c840c"      # Rollout review
CHECKS = "771f458519e1ab215825"    # Checks, hidden
SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
          "visualContainer/2.14.0/schema.json")

MARINE, PALE, GREY = "#2C5F7C", "#CFE0EA", "#7E8E92"
INK, INK_SOFT, WHITE = "#172529", "#4F6166", "#FFFFFF"

# ---------------------------------------------------------------- layout (1280 x 720)
NAV = dict(x=16, y=8, w=1248, h=30)
TITLE = dict(x=16, y=40, w=1248, h=56)
HEADER_LINE = dict(x=16, y=96, w=1248, h=28)
TILE_Y, TILE_H, TILE_W = 132, 384, 300
TILE_XS = [16, 332, 648, 964]
# pieces inside a tile: (offset from tile top, height); x is tile x + 12, width 276
T_TEXT, T_CARD, T_LINE, T_RULE = (6, 66), (72, 182), (256, 74), (332, 52)
BOTTOM_Y, BOTTOM_H = 528, 184
SPLIT_BASE = dict(x=16, y=BOTTOM_Y, w=456, h=BOTTOM_H)
SPLIT_LATEST = dict(x=488, y=BOTTOM_Y, w=456, h=BOTTOM_H)
MOVED = dict(x=960, y=BOTTOM_Y, w=304, h=BOTTOM_H)

TILES = [
    ("Foundation", "Which uses matter most, and where do people get stuck?",
     "Requests matched to a tested prompt that already exists"),
    ("Execution", "Does it hold up in everyday use?", "Repeat use within 30 days"),
    ("Refinement", "What earns its place, and at what cost?",
     "Tested prompts that pass on the smaller model"),
    ("Scale", "Where has it changed the work?",
     "Share of people in the air against the baseline, in points"),
]
RULE = ("Working when the month's figure meets the threshold. "
        "Trend: against two check-ins earlier, flat within 1 point.")


# ---------------------------------------------------------------- expression helpers
def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def text(s: str) -> dict:
    return lit("'" + s.replace("'", "''") + "'")


def colour(hex_: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_}'")}}


def measure(name: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}}


def column(table: str, name: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def proj_measure(name: str, display: str | None = None) -> dict:
    p = {"field": measure(name), "queryRef": f"_Measures.{name}", "nativeQueryRef": display or name}
    if display:
        p["displayName"] = display
    return p


def proj_column(table: str, name: str, active: bool = False) -> dict:
    p = {"field": column(table, name), "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if active:
        p["active"] = True
    return p


def stage_is(stage: str) -> dict:
    return {"data": [{"scopeId": {"Comparison": {
        "ComparisonKind": 0,
        "Left": column("dim_checkpoint_source", "stage"),
        "Right": {"Literal": {"Value": f"'{stage}'"}}}}}]}


OFF = {"show": lit("false")}
ON = {"show": lit("true")}
WILDCARD = [{"dataViewWildcard": {"matchingOption": 0}}]


def field_id() -> str:
    return f"field-{uuid.uuid4()}"


# ---------------------------------------------------------------- visuals
class Page:
    def __init__(self) -> None:
        self.visuals: list[dict] = []

    def add(self, name: str, box: dict, visual: dict, z: int, **extra) -> None:
        tab = len(self.visuals) * 100
        self.visuals.append({
            "$schema": SCHEMA,
            "name": name,
            "position": {"x": box["x"], "y": box["y"], "z": z, "height": box["h"],
                         "width": box["w"], "tabOrder": tab},
            "visual": visual,
            **extra,
        })


def textbox(paragraphs: list[list[tuple[str, dict]]]) -> dict:
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": v, "textStyle": style} if style else {"value": v}
                          for v, style in para]} for para in paragraphs]}}]},
        "visualContainerObjects": {"background": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def shape_panel() -> dict:
    return {
        "visualType": "shape",
        "objects": {
            "shape": [{"properties": {"tileShape": text("rectangle"), "roundEdge": lit("8L")}}],
            "rotation": [{"properties": {"shapeAngle": lit("0L")}}],
            "outline": [{"properties": OFF}],
            "fill": [{"properties": {"fillColor": colour(WHITE)}, "selector": {"id": "default"}}],
        },
        "visualContainerObjects": {"border": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


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
            "label": [{"properties": {"fontSize": lit("10D"), "textWrap": lit("true")},
                       "selector": {"id": "default"}}],
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
            "dataPoint": [{"properties": {"fill": colour(MARINE)}}],
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


def stage_split(measure_name: str, title: str, subtitle: str, legend: bool) -> dict:
    team = column("dim_team", "team")
    return {
        "visualType": "hundredPercentStackedBarChart",
        "query": {
            "queryState": {
                "Category": {"projections": [proj_column("dim_team", "team", active=True)]},
                "Series": {"projections": [proj_column("dim_checkpoint_source", "stage")]},
                "Y": {"projections": [proj_measure(measure_name)]},
            },
            "sortDefinition": {"sort": [{"field": team, "direction": "Ascending"}],
                               "isDefaultSort": False},
        },
        "objects": {
            "dataPoint": [
                {"properties": {"fill": colour(c)}, "selector": stage_is(s)}
                for s, c in (("On the ground", GREY), ("At the gate", PALE), ("In the air", MARINE))
            ],
            "labels": [
                {"properties": {"show": lit("true"), "fontSize": lit("9D"), "labelPrecision": lit("0L")}},
                {"properties": {"color": colour(WHITE)}, "selector": stage_is("In the air")},
            ],
            "legend": [{"properties": {"show": lit("true"), "position": text("Top"),
                                       "fontSize": lit("9D")}}] if legend
            else [{"properties": OFF}],
            "categoryAxis": [{"properties": {"show": lit("true"), "fontSize": lit("9D")}}],
            "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
        },
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("true"), "text": text(title)}}],
            "subTitle": [{"properties": {"show": lit("true"), "text": text(subtitle),
                                         "fontSize": lit("9D"), "fontColor": colour(INK_SOFT)}}],
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
        "visualContainerObjects": {
            "title": [{"properties": {"show": lit("true"), "text": text("Moved up since the last count")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def navigator() -> dict:
    # as Desktop wrote it on the PC
    return {
        "visualType": "pageNavigator",
        "objects": {
            "text": [{"properties": {"fontSize": lit("10D")}, "selector": {"id": "default"}}],
            "shape": [{"properties": {"tileShape": text("rectangleRounded"),
                                      "rectangleRoundedCurve": lit("8L")},
                       "selector": {"id": "default"}}],
            "pages": [{"properties": {"showHiddenPages": lit("false")}}],
            "outline": [{"properties": OFF}],
        },
        "drillFilterOtherVisuals": True,
    }


def build() -> Page:
    p = Page()
    p.add("p0_navigator", NAV, navigator(), z=0)
    p.add("p0_title", TITLE, textbox([
        [("Rollout review", {"fontWeight": "bold", "fontSize": "18pt", "color": INK})],
        [("Read from the question log, the usage dashboards, the library's records, "
          "the run log and the check-in · ", {"fontSize": "10pt", "color": INK_SOFT}),
         ("Week 1 to Week 24, six check-ins", {"fontWeight": "bold", "fontSize": "10pt",
                                               "color": INK_SOFT})],
    ]), z=1000)
    header = {
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
    p.add("p0_header_line", HEADER_LINE, header, z=1000)

    for n, (stage, question, label) in enumerate(TILES):
        x = TILE_XS[n]
        key = stage.lower()
        inner = lambda off_h: dict(x=x + 12, y=TILE_Y + off_h[0], w=TILE_W - 24, h=off_h[1])
        p.add(f"p0_{key}_panel", dict(x=x, y=TILE_Y, w=TILE_W, h=TILE_H), shape_panel(), z=2000)
        p.add(f"p0_{key}_text", inner(T_TEXT), textbox([
            [(stage, {"fontWeight": "bold", "fontSize": "14pt", "color": INK})],
            [(question, {"fontSize": "10pt", "color": INK_SOFT})],
        ]), z=3000)
        p.add(f"p0_{key}_card", inner(T_CARD), tile_card(stage, label), z=3000)
        line, filters = sparkline(stage)
        p.add(f"p0_{key}_sparkline", inner(T_LINE), line, z=3000, filterConfig=filters)
        p.add(f"p0_{key}_rule", inner(T_RULE), textbox([
            [(RULE, {"fontSize": "8pt", "color": INK_SOFT})]]), z=3000)

    p.add("p0_split_baseline", SPLIT_BASE, stage_split(
        "Stage split baseline", "Where each team stood at its baseline",
        "Stage by source placement, each team at its own baseline month", legend=False), z=2000)
    p.add("p0_split_latest", SPLIT_LATEST, stage_split(
        "Stage split latest", "Where each team stands now, Month 6",
        "Stage by source placement, latest count", legend=True), z=2000)
    p.add("p0_moved_up", MOVED, moved_up_card(), z=2000)
    return p


def check(p: Page) -> None:
    """Every visual sits on the page, and nothing overlaps except a tile's pieces on its panel."""
    boxes = [(v["name"], v["position"]) for v in p.visuals]
    for name, b in boxes:
        assert b["x"] >= 0 and b["y"] >= 0, name
        assert b["x"] + b["width"] <= 1280 and b["y"] + b["height"] <= 720, f"{name} runs off the page"
    for i, (a, A) in enumerate(boxes):
        for b, B in boxes[i + 1:]:
            if a.endswith("_panel") and b.startswith(a[:-6]) or b.endswith("_panel") and a.startswith(b[:-6]):
                continue
            apart = (A["x"] + A["width"] <= B["x"] or B["x"] + B["width"] <= A["x"] or
                     A["y"] + A["height"] <= B["y"] or B["y"] + B["height"] <= A["y"])
            assert apart, f"{a} overlaps {b}"


def main() -> None:
    p = build()
    check(p)
    visuals = PAGES / PAGE / "visuals"
    if visuals.exists():
        shutil.rmtree(visuals)
    for v in p.visuals:
        folder = visuals / v["name"]
        folder.mkdir(parents=True)
        (folder / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n",
                                            encoding="utf-8")
    # keep the Checks page hidden, so the navigator does not list it
    checks = PAGES / CHECKS / "page.json"
    page = json.loads(checks.read_text(encoding="utf-8"))
    if page.get("visibility") != "HiddenInViewMode":
        page["visibility"] = "HiddenInViewMode"
        checks.write_text(json.dumps(page, indent=2) + "\n", encoding="utf-8")
    print(f"{len(p.visuals)} visuals written to page {PAGE}; nothing overlaps")


if __name__ == "__main__":
    main()
