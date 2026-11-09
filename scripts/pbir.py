"""Shared pieces for writing report pages into the Power BI project (PBIR) from the Mac.

Each page has its own script (scripts/page0_pbir.py, ...). The page script lays its
visuals out and calls Page.write(), which refuses to write anything unless every check
below passes:

1. every visual sits inside the 1280 by 720 page;
2. nothing overlaps, except a panel and the pieces placed on it;
3. repeated elements share one exact size (visuals given the same `same` key);
4. no chart is smaller than Desktop can draw (MIN_SIZE, BAR_PER_CATEGORY);
5. spacing: inside a panel, text and visuals are grouped (`group` key); the first group
   sits PANEL_PAD_TOP below the panel top and PANEL_PAD_X in from its left; groups are
   GROUP_GAP apart (less CHART_INSET above a chart or table, which pads itself); pieces of
   one group stacked one on another touch (CAPTION_GAP), so a caption sits on the number
   or chart it labels; panels in one `row` share one top edge and height, COL_GAP apart;
   page rows are ROW_GAP apart, or touch inside the header strip;
6. text fits: each text box is tall enough for its text as Desktop wraps it (estimated
   from the page 0 screenshots), and no more than TEXT_SNUG taller, so a text box does
   not add hidden space (boxes of one `same` set are sized to the tallest of the set);
7. every format setting name is in SEEN (Desktop wrote it in Megat's own files, or a
   screenshot confirmed it) or in UNCONFIRMED (from the published schema, or a pattern
   Megat gave). Each push lists the unconfirmed names it used.
"""
from __future__ import annotations

import json
import math
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "report" / "Rollout review.Report" / "definition" / "pages"
CHECKS_PAGE = "771f458519e1ab215825"
SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
          "visualContainer/2.14.0/schema.json")
PAGE_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
               "page/2.1.0/schema.json")
PAGE_W, PAGE_H = 1280, 720

MARINE, MARINE_DEEP, PALE, GREY = "#2C5F7C", "#214A62", "#CFE0EA", "#7E8E92"
INK, INK_SOFT, WHITE, AMBER = "#172529", "#4F6166", "#FFFFFF", "#B07E23"
STAGES = (("On the ground", GREY), ("At the gate", PALE), ("In the air", MARINE))

# ------------------------------------------------------------------ spacing (every page)
PANEL_PAD_X = 12     # pieces sit this far in from a panel's left edge
PANEL_PAD_TOP = 6    # the first group sits this far below a panel's top edge
GROUP_GAP = 10       # between groups inside a panel
CHART_INSET = 8      # a chart or table pads its own top, so the gap above it is 10 - 8 = 2
CAPTION_GAP = 0      # a caption sits directly on the number or chart it labels
COL_GAP = 16         # between panels side by side in a row
ROW_GAP = 4          # between rows on the page (the header strip's pieces touch)
TEXT_SNUG = 6        # a text box is at most this much taller than its text
INSET_TYPES = {"lineChart", "clusteredBarChart", "hundredPercentStackedBarChart", "tableEx"}

# Text measured on the page 0 screenshots (10 Nov 2026): a 10pt line of 44 to 45
# characters filled a 276 px text box, so about 0.62 px per character per point, with
# almost no inner padding; lines are about 1.73 x the point size apart.
CHAR_W, BOLD_W, LINE_H, TEXT_PAD, TEXT_INSET = 0.62, 1.08, 1.73, 2, 2

# ------------------------------------------------------------------ setting names
# (visual type or "container", object) -> property names, each written by Desktop in:
#   RR  rollout-review, commit 22ebf37 (page 0 built by hand)
#   BR  ~/Code/data-answers/dashboard/report/Branch review.Report
#   S3  confirmed by Megat on the page 0 round 3 screenshot (10 Nov 2026)
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
    ("hundredPercentStackedBarChart", "dataPoint"): {"fill"},        # S3 (selector by value)
    ("lineClusteredColumnComboChart", "categoryAxis"): {"showAxisTitle"},  # BR
    ("lineClusteredColumnComboChart", "legend"): {"show"},           # BR
    ("lineClusteredColumnComboChart", "dataPoint"): {"fill", "fillTransparency"},  # BR
    ("slicer", "data"): {"mode"},                                    # BR
    ("slicer", "selection"): {"singleSelect", "strictSingleSelect", "selectAllCheckboxEnabled"},  # BR
    ("slicer", "general"): {"filter"},                               # BR
    ("slicer", "header"): {"text"},                                  # BR
    ("tableEx", "total"): {"totals"},                                # BR
    ("tableEx", "columnWidth"): {"value"},                           # BR
    ("tableEx", "values"): {"backColor", "fontColor"},               # BR
}
TEXT_STYLE_SEEN = {"fontWeight", "fontSize", "color"}                # RR, BR; color S3

# Not yet in Megat's files or confirmed on screen. Listed with every push.
UNCONFIRMED: dict[tuple[str, str], set[str]] = {}
TEXT_STYLE_UNCONFIRMED: set[str] = set()

# Microsoft's axis, legend, label and data colour objects are shared by the cartesian
# charts, so a name seen on one of them counts for the others. Each use is listed.
CARTESIAN = {"lineChart", "clusteredBarChart", "hundredPercentStackedBarChart",
             "lineClusteredColumnComboChart"}
FAMILY_OBJECTS = {"categoryAxis", "valueAxis", "legend", "labels", "dataPoint"}

# Smallest sizes Desktop drew on page 0. A line chart at 276 by 67 and 276 by 74 did not
# draw; at 276 by 100 it did. Bars: the round 2 screenshot scrolled with bars 26.5 px
# apart; round 3 drew six bars in 206 px with the title off. So 27 px per bar, plus 40 px
# with the chart title off or 76 px with it on.
MIN_SIZE = {
    "lineChart": dict(w=200, h=100),
    "hundredPercentStackedBarChart": dict(w=300, h=150),
    "clusteredBarChart": dict(w=150, h=150),
}
BAR_PER_CATEGORY = 27
BAR_CHROME = {True: 76, False: 40}


# ------------------------------------------------------------------ expression helpers
def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def text(s: str) -> dict:
    return lit("'" + s.replace("'", "''") + "'")


def colour(hex_: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_}'")}}


def measure_colour(name: str) -> dict:
    return {"solid": {"color": {"expr": measure(name)}}}


def measure(name: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}}


def column(table: str, name: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def proj_measure(name: str, display: str | None = None) -> dict:
    p = {"field": measure(name), "queryRef": f"_Measures.{name}", "nativeQueryRef": display or name}
    if display:
        p["displayName"] = display
    return p


def proj_column(table: str, name: str, active: bool = False, display: str | None = None) -> dict:
    p = {"field": column(table, name), "queryRef": f"{table}.{name}",
         "nativeQueryRef": display or name}
    if display:
        p["displayName"] = display
    if active:
        p["active"] = True
    return p


def value_is(table: str, col: str, value: str) -> dict:
    """Selector for one value of a column (one series, or one category)."""
    return {"data": [{"scopeId": {"Comparison": {
        "ComparisonKind": 0, "Left": column(table, col),
        "Right": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}}}]}


def filter_in(table: str, col: str, values: list[str], name: str, negate: bool = False) -> dict:
    cond = {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                               "Property": col}}],
                   "Values": [[{"Literal": {"Value": "'" + v.replace("'", "''") + "'"}}] for v in values]}}
    f = {"name": name, "field": column(table, col), "type": "Categorical",
         "filter": {"Version": 2, "From": [{"Name": "d", "Entity": table, "Type": 0}],
                    "Where": [{"Condition": {"Not": {"Expression": cond}} if negate else cond}]}}
    if negate:
        f["objects"] = {"general": [{"properties": {"isInvertedSelectionMode": lit("true")}}]}
    return f


OFF = {"show": lit("false")}
ON = {"show": lit("true")}
WILDCARD = [{"dataViewWildcard": {"matchingOption": 0}}]
NO_FRAME = {"title": [{"properties": OFF}], "background": [{"properties": OFF}]}


def field_id() -> str:
    return f"field-{uuid.uuid4()}"


def pt(n: int, bold: bool = False, color: str | None = None) -> dict:
    s = {"fontSize": f"{n}pt"}
    if bold:
        s["fontWeight"] = "bold"
    if color:
        s["color"] = color
    return s


# ------------------------------------------------------------------ visuals
def textbox(paragraphs: list[list[tuple[str, dict]]]) -> dict:
    """paragraphs: a list of paragraphs, each a list of (text, textStyle) runs."""
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [
            {"textRuns": [{"value": v, "textStyle": style} if style else {"value": v}
                          for v, style in para]} for para in paragraphs]}}]},
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


def caption(label: str, size: int, width: int, lines: int, color: str = INK_SOFT) -> dict:
    """A caption that sits on the bottom of its box: blank lines go above a shorter label,
    so the label always touches the number under it."""
    style = pt(size, color=color)
    paras = [[(part, style)] for part in label.split("\n")]   # "\n" forces a line break
    used = sum(wrapped_lines(para, width) for para in paras)
    blank = [[("\u00a0", style)] for _ in range(max(0, lines - used))]
    return textbox(blank + paras)


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


def value_card(measure_name: str, size: int, color: dict | None = None,
               display: str | None = None) -> dict:
    """A card showing one value and nothing else: no label, no divider, no left padding,
    the value in the middle of the box. Its caption is a text box above it."""
    meta = f"_Measures.{measure_name}"
    value = {"fontSize": lit(f"{size}D")}
    if color:
        value["fontColor"] = color
    return {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj_measure(measure_name, display)]}}},
        "objects": {
            "value": [{"properties": value, "selector": {"id": "default"}}],
            "label": [{"properties": OFF, "selector": {"metadata": meta}}],
            "divider": [{"properties": OFF, "selector": {"id": "default"}}],
            "padding": [{"properties": {"paddingIndividual": lit("true"), "leftMargin": lit("0L")},
                         "selector": {"id": "default"}}],
            "layout": [{"properties": {"alignment": text("middle")}}],
            "fillCustom": [{"properties": OFF}],
        },
        "visualContainerObjects": NO_FRAME,
        "drillFilterOtherVisuals": True,
    }


# ------------------------------------------------------------------ text estimate
def _run_size(style: dict | None) -> float:
    return float((style or {}).get("fontSize", "10pt").rstrip("pt"))


def wrapped_lines(runs: list[tuple[str, dict]], width: int) -> int:
    """Lines a paragraph takes when Desktop wraps it at word boundaries."""
    inner = width - 2 * TEXT_INSET
    chars = []
    for value, style in runs:
        w = CHAR_W * _run_size(style) * (BOLD_W if (style or {}).get("fontWeight") == "bold" else 1)
        chars += [(ch, w) for ch in value.replace("\u00a0", " ")]
    lines, x, spaces, word = 1, 0.0, 0.0, 0.0

    def place(x, lines):
        if x > 0 and x + spaces + word > inner:
            return word, lines + 1
        return x + spaces + word, lines

    for ch, w in chars:
        if ch == " ":
            if word:
                x, lines = place(x, lines)
                spaces, word = 0.0, 0.0
            spaces += w
        else:
            word += w
    if word:
        x, lines = place(x, lines)
    return lines


def text_height(visual: dict, width: int) -> float:
    total = 0.0
    for para in visual["objects"]["general"][0]["properties"]["paragraphs"]:
        runs = [(r["value"], r.get("textStyle")) for r in para["textRuns"]]
        size = max(_run_size(s) for _, s in runs)
        total += wrapped_lines(runs, width) * LINE_H * size
    return total + TEXT_PAD


# ------------------------------------------------------------------ page
@dataclass
class Visual:
    name: str
    box: tuple[int, int, int, int]       # x, y, w, h
    visual: dict
    z: int = 3000
    on: str | None = None                # the panel this visual sits on
    group: str | None = None             # pieces that read together, inside a panel
    same: str | None = None              # repeated elements with the same key share one size
    row: str | None = None               # panels that share one top edge and height
    categories: int = 0                  # bars in a bar chart, for the per-bar check
    extra: dict = field(default_factory=dict)

    @property
    def vt(self) -> str:
        return self.visual["visualType"]

    @property
    def top(self) -> int:
        return self.box[1]

    @property
    def bottom(self) -> int:
        return self.box[1] + self.box[3]

    @property
    def left(self) -> int:
        return self.box[0]

    @property
    def right(self) -> int:
        return self.box[0] + self.box[2]


def _overlap_x(a: Visual, b: Visual) -> bool:
    return a.left < b.right and b.left < a.right


@dataclass
class Page:
    id: str
    display_name: str
    visuals: list[Visual] = field(default_factory=list)

    def add(self, name, box, visual, **kw) -> Visual:
        v = Visual(name, tuple(box), visual, **kw)
        self.visuals.append(v)
        return v

    def get(self, name: str) -> Visual:
        return next(v for v in self.visuals if v.name == name)

    # -------------------------------------------------------------- checks
    def check(self) -> list[str]:
        problems: list[str] = []
        vs = self.visuals
        names = [v.name for v in vs]
        if len(set(names)) != len(names):
            problems.append("two visuals share a name")
        # 1 inside the page
        for v in vs:
            if v.left < 0 or v.top < 0 or v.right > PAGE_W or v.bottom > PAGE_H:
                problems.append(f"{v.name} is not inside {PAGE_W} by {PAGE_H}: {v.box}")
        # 2 no overlaps
        for i, a in enumerate(vs):
            for b in vs[i + 1:]:
                if a.on == b.name or b.on == a.name:
                    continue
                if _overlap_x(a, b) and a.top < b.bottom and b.top < a.bottom:
                    problems.append(f"{a.name} overlaps {b.name}")
        # 3 repeated sizes
        sizes: dict[str, set] = {}
        for v in vs:
            if v.same:
                sizes.setdefault(v.same, set()).add(v.box[2:])
        for key, s in sizes.items():
            if len(s) > 1:
                problems.append(f"repeated '{key}' pieces differ in size: {sorted(s)}")
        # 4 chart sizes
        for v in vs:
            w, h = v.box[2:]
            m = MIN_SIZE.get(v.vt)
            if m and (w < m["w"] or h < m["h"]):
                problems.append(f"{v.name} ({v.vt}) is {w} by {h}, below {m['w']} by {m['h']}")
            if v.categories:
                need = v.categories * BAR_PER_CATEGORY + BAR_CHROME[title_on(v.visual)]
                if h < need:
                    problems.append(f"{v.name}: {v.categories} bars need {need} px, it is {h}")
        problems += self._spacing()
        problems += self._text_fit()
        # 7 setting names
        problems += [f"{v.name}: {p}" for v in vs for p in unseen(v.visual)]
        return problems

    def _spacing(self) -> list[str]:
        out = []
        vs = self.visuals
        panels = {v.on for v in vs if v.on}
        for pname in panels:
            p = self.get(pname)
            members = [v for v in vs if v.on == pname]
            for v in members:
                if v.left < p.left or v.top < p.top or v.right > p.right or v.bottom > p.bottom:
                    out.append(f"{v.name} runs outside its panel {pname}")
            if min(v.left for v in members) != p.left + PANEL_PAD_X:
                out.append(f"{pname}: pieces start {min(v.left for v in members) - p.left} px in, "
                           f"not {PANEL_PAD_X}")
            groups: dict[str, list[Visual]] = {}
            for v in members:
                groups.setdefault(v.group or v.name, []).append(v)
            ordered = sorted(groups.values(), key=lambda g: min(v.top for v in g))
            first = min(v.top for v in ordered[0])
            if first - p.top != PANEL_PAD_TOP:
                out.append(f"{pname}: first group is {first - p.top} px below the top, not {PANEL_PAD_TOP}")
            for g1, g2 in zip(ordered, ordered[1:]):
                top2 = min(v.top for v in g2)
                gap = top2 - max(v.bottom for v in g1)
                inset = any(v.vt in INSET_TYPES for v in g2 if v.top == top2)
                want = GROUP_GAP - CHART_INSET if inset else GROUP_GAP
                if gap != want:
                    out.append(f"{pname}: gap above {g2[0].group or g2[0].name} is {gap}, not {want}")
            for g in groups.values():
                for a in g:
                    below = [b for b in g if b is not a and b.top >= a.bottom and _overlap_x(a, b)]
                    if below:
                        b = min(below, key=lambda b: b.top)
                        if b.top - a.bottom != CAPTION_GAP:
                            out.append(f"{a.name} and {b.name} are one group but {b.top - a.bottom} px apart")
        rows: dict[str, list[Visual]] = {}
        for v in vs:
            if v.row:
                rows.setdefault(v.row, []).append(v)
        for key, r in rows.items():
            if len({(v.top, v.box[3]) for v in r}) > 1:
                out.append(f"row '{key}': panels do not share one top edge and height")
            r = sorted(r, key=lambda v: v.left)
            for a, b in zip(r, r[1:]):
                if b.left - a.right != COL_GAP:
                    out.append(f"row '{key}': {a.name} to {b.name} is {b.left - a.right} px, not {COL_GAP}")
        page_level = [v for v in vs if not v.on]
        for a in page_level:
            below = [b for b in page_level if b.top >= a.bottom and _overlap_x(a, b)]
            if below:
                gap = min(b.top for b in below) - a.bottom
                if gap not in (0, ROW_GAP):
                    out.append(f"{a.name}: {gap} px to the row below, not 0 or {ROW_GAP}")
        return out

    def _text_fit(self) -> list[str]:
        out = []
        need = {v.name: text_height(v.visual, v.box[2]) for v in self.visuals if v.vt == "textbox"}
        tallest: dict[str, float] = {}
        for v in self.visuals:
            if v.name in need and v.same:
                tallest[v.same] = max(tallest.get(v.same, 0), need[v.name])
        for v in self.visuals:
            if v.name not in need:
                continue
            h = v.box[3]
            if need[v.name] > h:
                out.append(f"{v.name}: text needs {need[v.name]:.0f} px, the box is {h}")
            ref = tallest.get(v.same, need[v.name]) if v.same else need[v.name]
            if h - ref > TEXT_SNUG:
                out.append(f"{v.name}: box is {h - ref:.0f} px taller than its text")
        return out

    # -------------------------------------------------------------- write
    def write(self) -> None:
        problems = self.check()
        if problems:
            raise SystemExit("Page not written:\n  " + "\n  ".join(problems))
        folder = PAGES / self.id
        folder.mkdir(parents=True, exist_ok=True)
        page_json = {"$schema": PAGE_SCHEMA, "name": self.id, "displayName": self.display_name,
                     "displayOption": "FitToPage", "height": PAGE_H, "width": PAGE_W}
        (folder / "page.json").write_text(json.dumps(page_json, indent=2) + "\n", encoding="utf-8")
        visuals = folder / "visuals"
        if visuals.exists():
            shutil.rmtree(visuals)
        for n, v in enumerate(self.visuals):
            x, y, w, h = v.box
            doc = {"$schema": SCHEMA, "name": v.name,
                   "position": {"x": x, "y": y, "z": v.z, "height": h, "width": w,
                                "tabOrder": n * 100},
                   "visual": v.visual, **v.extra}
            (visuals / v.name).mkdir(parents=True)
            (visuals / v.name / "visual.json").write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        hide_checks_page()
        print(f"{self.display_name}: {len(self.visuals)} visuals written. Checks passed: inside "
              f"{PAGE_W} by {PAGE_H}, no overlaps, repeated sizes, chart sizes, spacing, "
              f"text fit, setting names.")
        fam = used_by_family(self)
        if fam:
            print("  Names used through the cartesian family:\n    " + "\n    ".join(fam))
        unc = used_unconfirmed(self)
        print("  Unconfirmed names: " + (", ".join(unc) if unc else "none"))


def set_page_order(order: list[str]) -> None:
    """Pages in this order, then any others (the hidden Checks page last)."""
    path = PAGES / "pages.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    rest = [p for p in meta["pageOrder"] if p not in order]
    meta["pageOrder"] = order + rest
    meta["activePageName"] = order[0]
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


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
        for obj, items in v.visual.get("objects", {}).items():
            for it in items:
                for p in it.get("properties", {}):
                    if p in UNCONFIRMED.get((v.vt, obj), set()) and p not in SEEN.get((v.vt, obj), set()):
                        out.add(f"{v.vt}: {obj}.{p}")
        if v.vt == "textbox":
            for para in v.visual["objects"]["general"][0]["properties"]["paragraphs"]:
                for run in para["textRuns"]:
                    for k in run.get("textStyle", {}):
                        if k in TEXT_STYLE_UNCONFIRMED:
                            out.add(f"textbox: textStyle.{k}")
    return sorted(out)


def used_by_family(page: Page) -> list[str]:
    out = set()
    for v in page.visuals:
        for obj, items in v.visual.get("objects", {}).items():
            own = SEEN.get((v.vt, obj), set()) | UNCONFIRMED.get((v.vt, obj), set())
            for it in items:
                for p in it.get("properties", {}):
                    if p not in own:
                        out.add(f"{v.vt}: {obj}.{p}")
    return sorted(out)


def hide_checks_page() -> None:
    path = PAGES / CHECKS_PAGE / "page.json"
    page = json.loads(path.read_text(encoding="utf-8"))
    if page.get("visibility") != "HiddenInViewMode":
        page["visibility"] = "HiddenInViewMode"
        path.write_text(json.dumps(page, indent=2) + "\n", encoding="utf-8")
