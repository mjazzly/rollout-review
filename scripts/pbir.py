"""Shared pieces for writing report pages into the Power BI project (PBIR) from the Mac.

Each page has its own script (scripts/page0_pbir.py, ...). The page script lays its
visuals out and calls write_page(), which refuses to write anything unless the checks
below pass:

1. every visual sits inside the 1280 by 720 page;
2. nothing overlaps, except a panel and the pieces placed on it;
3. repeated elements share one exact size (visuals given the same `same` key);
4. no chart is smaller than Desktop can draw (MIN_SIZE below);
5. every format setting name is in SEEN (Desktop wrote it in Megat's own files) or in
   UNCONFIRMED (from the published schema, or a pattern Megat gave). Each push lists the
   unconfirmed names it used; a name whose screenshot shows it did not take is then
   read from one visual Megat formats by hand.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "report" / "Rollout review.Report" / "definition" / "pages"
CHECKS_PAGE = "771f458519e1ab215825"
SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
          "visualContainer/2.14.0/schema.json")
PAGE_W, PAGE_H = 1280, 720

MARINE, MARINE_DEEP, PALE, GREY = "#2C5F7C", "#214A62", "#CFE0EA", "#7E8E92"
INK, INK_SOFT, WHITE, AMBER = "#172529", "#4F6166", "#FFFFFF", "#B07E23"

# ------------------------------------------------------------------ setting names seen
# (visual type or "container", object) -> property names, each written by Desktop in:
#   RR  rollout-review, commit 22ebf37 (page 0 built by hand)
#   BR  ~/Code/data-answers/dashboard/report/Branch review.Report
SEEN: dict[tuple[str, str], set[str]] = {
    ("container", "title"): {"show", "text"},                        # RR, BR
    ("container", "subTitle"): {"show"},                             # BR
    ("container", "background"): {"show"},                           # RR, BR
    ("container", "border"): {"show"},                               # RR
    ("container", "visualHeader"): {"show"},                         # BR
    ("textbox", "general"): {"paragraphs"},                          # RR, BR
    ("shape", "shape"): {"tileShape", "roundEdge"},                  # RR
    ("shape", "rotation"): {"shapeAngle"},                           # RR
    ("shape", "outline"): {"show"},                                  # RR
    ("shape", "fill"): {"fillColor"},                                # RR
    ("pageNavigator", "text"): {"fontSize"},                         # RR
    ("pageNavigator", "shape"): {"tileShape", "rectangleRoundedCurve"},  # RR
    ("pageNavigator", "pages"): {"showHiddenPages"},                 # RR
    ("pageNavigator", "outline"): {"show"},                          # RR
    ("cardVisual", "value"): {"fontSize", "fontColor", "labelDisplayUnits", "labelPrecision"},  # RR, BR
    ("cardVisual", "label"): {"show", "fontSize", "textWrap"},       # RR
    ("cardVisual", "divider"): {"show"},                             # BR
    ("cardVisual", "fillCustom"): {"show"},                          # RR
    ("cardVisual", "outline"): {"show", "weight"},                   # BR
    ("cardVisual", "padding"): {"paddingIndividual", "leftMargin"},  # BR
    ("cardVisual", "layout"): {"alignment", "backgroundShow", "backgroundFillColor"},  # BR
    ("cardVisual", "referenceLabel"): {"value"},                     # RR
    ("cardVisual", "referenceLabelLayout"): {"position"},            # BR
    ("cardVisual", "referenceLabelTitle"): {"show"},                 # RR
    ("cardVisual", "referenceLabelValue"): {"valueBold", "valueFontColor", "valueFontSize"},  # RR
    ("cardVisual", "smallMultiplesHeader"): {"fontSize"},            # RR
    ("lineChart", "valueAxis"): {"show", "start", "gridlineShow"},   # RR
    ("lineChart", "lineStyles"): {"strokeWidth", "showMarker", "markerSize"},  # RR
    ("clusteredBarChart", "categoryAxis"): {"show", "innerPadding"},  # BR
    ("clusteredBarChart", "labels"): {"show", "labelDisplayUnits", "labelPrecision"},  # BR
    ("clusteredBarChart", "valueAxis"): {"show", "start", "end"},    # BR
    ("lineClusteredColumnComboChart", "categoryAxis"): {"showAxisTitle"},  # BR
    ("lineClusteredColumnComboChart", "legend"): {"show"},           # BR
    ("lineClusteredColumnComboChart", "dataPoint"): {"fill", "fillTransparency"},  # BR
}
TEXT_STYLE_SEEN = {"fontWeight", "fontSize"}                         # RR, BR

# Not yet in Megat's files. Listed with every push until a screenshot shows them working.
UNCONFIRMED: dict[tuple[str, str], set[str]] = {
    # Megat's pattern (10 Nov 2026) names dataPoint.fill; the selector picks each stage by
    # value (scopeId), since a metadata selector names the stage field, not one stage.
    ("hundredPercentStackedBarChart", "dataPoint"): {"fill"},
}
TEXT_STYLE_UNCONFIRMED = {"color"}                                    # Megat's pattern

# Microsoft's axis, legend and label objects are shared by the cartesian charts, so a
# name seen on one of them counts for the others. Each use is listed by used_by_family().
CARTESIAN = {"lineChart", "clusteredBarChart", "hundredPercentStackedBarChart",
             "lineClusteredColumnComboChart"}
FAMILY_OBJECTS = {"categoryAxis", "valueAxis", "legend", "labels"}

# Smallest sizes Desktop is known to draw on this page set. A line chart at 276 by 67
# (axis on) and 276 by 74 (axes off) did not draw on page 0; 100 is the floor until a
# screenshot shows a line drawing smaller.
MIN_SIZE = {
    "lineChart": dict(w=200, h=100),
    "hundredPercentStackedBarChart": dict(w=300, h=150),
}
# Page 0 round 2 screenshot: six bars in a 184-high chart with its title on scrolled,
# showing four bars 26.5 px apart, the plot starting about 60 px below the chart top and
# ending about 18 px above its bottom. So: 27 px per bar, plus 76 px with the title on,
# or 40 px with the title off (an estimate until a screenshot shows it).
BAR_PER_CATEGORY = 27
BAR_CHROME = {True: 76, False: 40}


# ------------------------------------------------------------------ expression helpers
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


OFF = {"show": lit("false")}
ON = {"show": lit("true")}
WILDCARD = [{"dataViewWildcard": {"matchingOption": 0}}]


def field_id() -> str:
    return f"field-{uuid.uuid4()}"


def textbox(paragraphs: list[list[tuple[str, dict]]]) -> dict:
    """paragraphs: a list of paragraphs, each a list of (text, textStyle) runs."""
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": v, "textStyle": style} if style else {"value": v}
                          for v, style in para]} for para in paragraphs]}}]},
        "visualContainerObjects": {"background": [{"properties": OFF}],
                                   "title": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def panel() -> dict:
    """A white rounded panel (a rectangle shape), as Desktop wrote it on the PC."""
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


def navigator() -> dict:
    """The page navigator, as Desktop wrote it on the PC."""
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


# ------------------------------------------------------------------ page
@dataclass
class Visual:
    name: str
    box: tuple[int, int, int, int]       # x, y, w, h
    visual: dict
    z: int = 3000
    on: str | None = None                # the panel this visual sits on
    same: str | None = None              # repeated elements with the same key share one size
    categories: int = 0                  # bars in a bar chart, for the per-bar check
    extra: dict = field(default_factory=dict)


@dataclass
class Page:
    id: str
    visuals: list[Visual] = field(default_factory=list)

    def add(self, name, box, visual, **kw) -> Visual:
        v = Visual(name, tuple(box), visual, **kw)
        self.visuals.append(v)
        return v

    # -------------------------------------------------------------- checks
    def check(self) -> list[str]:
        problems = []
        names = [v.name for v in self.visuals]
        if len(set(names)) != len(names):
            problems.append("two visuals share a name")
        for v in self.visuals:
            x, y, w, h = v.box
            if x < 0 or y < 0 or x + w > PAGE_W or y + h > PAGE_H:
                problems.append(f"{v.name} is not inside {PAGE_W} by {PAGE_H}: {v.box}")
        for i, a in enumerate(self.visuals):
            for b in self.visuals[i + 1:]:
                if a.on == b.name or b.on == a.name:
                    continue
                ax, ay, aw, ah = a.box
                bx, by, bw, bh = b.box
                if not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay):
                    problems.append(f"{a.name} overlaps {b.name}")
        for v in self.visuals:
            if v.on:
                p = next((q for q in self.visuals if q.name == v.on), None)
                if p is None:
                    problems.append(f"{v.name} sits on {v.on}, which is not on the page")
                    continue
                px, py, pw, ph = p.box
                x, y, w, h = v.box
                if x < px or y < py or x + w > px + pw or y + h > py + ph:
                    problems.append(f"{v.name} runs outside its panel {p.name}")
        sizes: dict[str, set] = {}
        for v in self.visuals:
            if v.same:
                sizes.setdefault(v.same, set()).add(v.box[2:])
        for key, s in sizes.items():
            if len(s) > 1:
                problems.append(f"repeated '{key}' pieces differ in size: {sorted(s)}")
        for v in self.visuals:
            vt = v.visual["visualType"]
            w, h = v.box[2:]
            m = MIN_SIZE.get(vt)
            if m and (w < m["w"] or h < m["h"]):
                problems.append(f"{v.name} ({vt}) is {w} by {h}, below {m['w']} by {m['h']}")
            if v.categories and (h - BAR_CHROME[title_on(v.visual)]) / v.categories < BAR_PER_CATEGORY:
                problems.append(f"{v.name}: {v.categories} bars do not fit without a scrollbar")
        problems += [f"{v.name}: {p}" for v in self.visuals for p in unseen(v.visual)]
        return problems

    # -------------------------------------------------------------- write
    def write(self) -> None:
        problems = self.check()
        if problems:
            raise SystemExit("Page not written:\n  " + "\n  ".join(problems))
        visuals = PAGES / self.id / "visuals"
        if visuals.exists():
            shutil.rmtree(visuals)
        for n, v in enumerate(self.visuals):
            x, y, w, h = v.box
            doc = {"$schema": SCHEMA, "name": v.name,
                   "position": {"x": x, "y": y, "z": v.z, "height": h, "width": w,
                                "tabOrder": n * 100},
                   "visual": v.visual, **v.extra}
            folder = visuals / v.name
            folder.mkdir(parents=True)
            (folder / "visual.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
        hide_checks_page()
        print(f"{len(self.visuals)} visuals written to page {self.id}. Checks passed: inside "
              f"{PAGE_W} by {PAGE_H}, no overlaps, repeated sizes equal, chart sizes, setting names.")
        fam = used_by_family(self)
        if fam:
            print("Names used through the cartesian family:\n  " + "\n  ".join(fam))
        unc = used_unconfirmed(self)
        if unc:
            print("Unconfirmed names used (not yet in Megat's files):\n  " + "\n  ".join(unc))


def title_on(visual: dict) -> bool:
    for it in visual.get("visualContainerObjects", {}).get("title", []):
        if it.get("properties", {}).get("show") == lit("false"):
            return False
    return True


def _allowed(vt: str, obj: str) -> set[str]:
    names = set(SEEN.get((vt, obj), set())) | UNCONFIRMED.get((vt, obj), set())
    if vt in CARTESIAN and obj in FAMILY_OBJECTS:
        for other in CARTESIAN:
            names |= SEEN.get((other, obj), set())
    return names


def unseen(visual: dict) -> list[str]:
    vt = visual["visualType"]
    out = []
    for obj, items in visual.get("objects", {}).items():
        for it in items:
            for p in it.get("properties", {}):
                if p not in _allowed(vt, obj):
                    out.append(f"setting {obj}.{p} on {vt} has not been seen in Desktop's files")
    for obj, items in visual.get("visualContainerObjects", {}).items():
        for it in items:
            for p in it.get("properties", {}):
                if p not in SEEN.get(("container", obj), set()):
                    out.append(f"container setting {obj}.{p} has not been seen in Desktop's files")
    if vt == "textbox":
        for para in visual["objects"]["general"][0]["properties"]["paragraphs"]:
            for run in para["textRuns"]:
                for k in run.get("textStyle", {}):
                    if k not in TEXT_STYLE_SEEN | TEXT_STYLE_UNCONFIRMED:
                        out.append(f"text style {k} has not been seen in Desktop's files")
    return out


def used_unconfirmed(page: Page) -> list[str]:
    out = set()
    for v in page.visuals:
        vt = v.visual["visualType"]
        for obj, items in v.visual.get("objects", {}).items():
            for it in items:
                for p in it.get("properties", {}):
                    if p in UNCONFIRMED.get((vt, obj), set()) and p not in SEEN.get((vt, obj), set()):
                        out.add(f"{vt}: {obj}.{p}")
        if vt == "textbox":
            for para in v.visual["objects"]["general"][0]["properties"]["paragraphs"]:
                for run in para["textRuns"]:
                    for k in run.get("textStyle", {}):
                        if k in TEXT_STYLE_UNCONFIRMED:
                            out.add(f"textbox: textStyle.{k}")
    return sorted(out)


def used_by_family(page: Page) -> list[str]:
    out = set()
    for v in page.visuals:
        vt = v.visual["visualType"]
        for obj, items in v.visual.get("objects", {}).items():
            own = SEEN.get((vt, obj), set()) | UNCONFIRMED.get((vt, obj), set())
            for it in items:
                for p in it.get("properties", {}):
                    if p not in own:
                        out.add(f"{vt}: {obj}.{p}")
    return sorted(out)


def hide_checks_page() -> None:
    path = PAGES / CHECKS_PAGE / "page.json"
    page = json.loads(path.read_text(encoding="utf-8"))
    if page.get("visibility") != "HiddenInViewMode":
        page["visibility"] = "HiddenInViewMode"
        path.write_text(json.dumps(page, indent=2) + "\n", encoding="utf-8")
