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
7. page 1's standing rules: nothing scrolls (tables and matrices sized to their columns
   and rows, bar charts to their bars, text boxes to their text); a data label never
   touches a bar (clustered bars at least LABEL_H thick, stacked segments at least
   LABEL_MIN_PX wide, a fixed value axis LABEL_ROOM past the longest bar); a legend shows
   every entry on one line; a table holds text only (charts first); every CHECK.md
   question for the page names the visual and field it is read from, shown without
   hovering (Page.answers);
8. page 2's standing rules: no more than two lines of text (a title and one grey subtitle)
   before the first visual in a panel, a caption sitting on its visual aside; no working
   terms from the notes (WORKING_TERMS) anywhere on a page; every number shown in one of
   NUMBER_FORMATS (counts whole, percentages one decimal, points one decimal with a sign);
9. page 3's standing rules: no blank row or column in a grid (its value measure is
   blank for Power BI's blank member); no subtitle or legend cut off (text is measured
   with TEXT_INSET each side); the gap rule holds for boxed visuals too: the tab bar,
   slicers and panels never touch (ROW_GAP down, COL_GAP across);
10. page 4's standing rules (round 7): the header is the title and the question only; the
   sources and period are one grey line at the foot of every page; a panel subtitle is at
   most SUBTITLE_WORDS words and never a "follows" note; a legend sits at the top right of its
   panel; no text is cut (a card's longest text fits its width);
11. round 8 (every page): one gap, GAP = 16 px, between all panels, between the header and
   the first row, and as the outer margin on all four sides (_grid16); a panel's size fits its
   content: under every piece, and right of it, the empty band is at most FIT_SHARE of the
   panel (a table counts by the rows and columns it shows) (_fit); a table's column headers sit
   on one line; a column chart's axis names stay level (a slot needs the name plus 18 px);
12. round 9 (every page): a button's height holds its label (BUTTON_MIN_H a row; Desktop lays
   more than three buttons out in rows of three unless told one row), and its width holds its
   longest label; every chart's labels are written on (labels.show) unless the page names it as
   unlabelled, and no labels on a stacked column chart with a series (they did not draw, rounds
   7 and 8); a stacked segment holds its label (AXIS_CHROME, LABEL_ROOM_PX); in a figure band
   the title sits FIGURE_TITLE_GAP right of the figure's text, and the figure lines up with the
   text of a table under it;
13. round 10: no button label, dropdown text or figure is cut: a button is its label plus
   BUTTON_TEXT_PAD wide, a dropdown its text plus DROPDOWN_PAD, and a figure box holds the
   widest value its measure can show ("100.0%" for a share) plus FIGURE_BOX_PAD;
14. every format setting name is in SEEN (Desktop wrote it in Megat's own files, or a
   screenshot confirmed it) or in UNCONFIRMED (from the published schema, or a pattern
   Megat gave). Each push lists the unconfirmed names it used.
"""
from __future__ import annotations

import json
import math
import re
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
INSET_TYPES = {"lineChart", "clusteredBarChart", "hundredPercentStackedBarChart", "tableEx",
               "pivotTable", "barChart", "clusteredColumnChart", "columnChart"}
COLUMN_TYPES = {"clusteredColumnChart", "columnChart"}   # categories run across: the per-bar check uses width
BOXED = {"shape", "pageNavigator", "slicer", "advancedSlicerVisual"}   # visuals drawn as a box

# Page 2 standing rules (10 Nov 2026)
WORKING_TERMS = ("headline", "FRAME-", "storyline", "helper", "measures.md", "CHECK.md", "DASH-",
                 "follows the", "How to read",
                 "repeat-flagged", "repeat_flag", "Foundation tile", "Execution tile",
                 "Refinement tile", "Scale tile", "scratch")
NUMBER_FORMATS = {"#,0": "count", "0.0%": "percentage", "+0.0;-0.0;0.0": "points",
                  "0.00": "ratio"}   # the cost index, two decimals as CHECK.md reads it

# Text measured on the page 0 screenshots (10 Nov 2026): a 10pt line of 44 to 45
# characters filled a 276 px text box, so about 0.62 px per character per point, with
# almost no inner padding; lines are about 1.73 x the point size apart.
CHAR_W, BOLD_W, LINE_H, TEXT_PAD, TEXT_INSET = 0.62, 1.08, 1.73, 2, 6
# TEXT_INSET was 2; page 1 round 4 cut "Month only, not the toggle" (est. 145 px) in a 150 px
# box, so a box keeps 6 px clear each side.

# ------------------------------------------------------------------ setting names
# (visual type or "container", object) -> property names, each written by Desktop in:
#   RR  rollout-review, commit 22ebf37 (page 0 built by hand)
#   BR  ~/Code/data-answers/dashboard/report/Branch review.Report
#   S3  confirmed by Megat on the page 0 round 3 screenshot (10 Nov 2026)
#   P1  confirmed on the page 1 round 2 screenshots (10 Nov 2026)
#   H1  Megat's hand reference on the page 1 gap chart (commit d1878b6)
#   H2  Megat's button slicer on page 1 (commit 1141219): no colour settings, so the
#       marine selected state with white text is the button slicer's own default
#   H3  Megat's hand reference on the page 1 gap chart: overflow text (commit 0df130b)
#   TH  theme.json, Megat's theme file: visualStyles border show, color, radius; background color
#   R7  confirmed on the round 7 screenshots (10 Nov 2026): the slicer and button slicer headers
#       turned off with header.show
#   R9  confirmed on the round 9 screenshots (10 Nov 2026): the button slicer's one-row layout
#       (layout.rowCount, layout.columnCount) and the tab bar's text.verticalAlignment
#   R8  confirmed on the round 8 screenshots (10 Nov 2026): labels.color on one bar chart series
#       (the gap's Level and the impact's A little read dark)
SEEN: dict[tuple[str, str], set[str]] = {
    ("container", "title"): {"show", "text"},                        # RR, BR
    ("container", "subTitle"): {"show"},                             # BR
    ("container", "background"): {"show", "color"},                  # RR, BR; color TH
    ("container", "border"): {"show", "color", "radius"},            # RR; color, radius TH
    ("container", "visualHeader"): {"show"},                         # BR
    ("textbox", "general"): {"paragraphs"},                          # RR, BR
    ("shape", "shape"): {"tileShape", "roundEdge"},                  # RR
    ("shape", "rotation"): {"shapeAngle"},                           # RR
    ("shape", "outline"): {"show"},                                  # RR
    ("shape", "fill"): {"fillColor"},                                # RR
    ("pageNavigator", "text"): {"fontSize", "verticalAlignment"},    # RR; verticalAlignment R9
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
    ("hundredPercentStackedBarChart", "labels"): {"show"},          # H1: Megat's hand reference, d1878b6
    ("barChart", "labels"): {"show", "labelOverflow", "color"},      # H3: Megat's hand reference, 0df130b; color R8
    ("lineClusteredColumnComboChart", "categoryAxis"): {"showAxisTitle"},  # BR
    ("lineClusteredColumnComboChart", "legend"): {"show"},           # BR
    ("lineClusteredColumnComboChart", "dataPoint"): {"fill", "fillTransparency"},  # BR
    ("slicer", "data"): {"mode"},                                    # BR
    ("slicer", "selection"): {"singleSelect", "strictSingleSelect", "selectAllCheckboxEnabled"},  # BR
    ("slicer", "header"): {"text", "show"},                          # BR; show R7
    ("advancedSlicerVisual", "data"): set(),                         # H2: Megat's button slicer, 1141219
    ("advancedSlicerVisual", "selection"): {"singleSelect", "strictSingleSelect"},  # H2
    ("advancedSlicerVisual", "general"): {"filter"},                 # H2
    ("advancedSlicerVisual", "header"): {"show"},                    # R7
    ("advancedSlicerVisual", "layout"): {"rowCount", "columnCount"}, # R9
    ("tableEx", "total"): {"totals"},                                # BR
    ("tableEx", "columnWidth"): {"value"},                           # BR
    ("tableEx", "values"): {"backColor", "fontColor"},               # BR
    ("pivotTable", "subTotals"): {"rowSubtotals", "columnSubtotals"},  # P1: page 1 round 2 screenshot
    ("pivotTable", "values"): {"backColor", "fontColor"},            # P1
    ("pivotTable", "columnWidth"): {"value"},                        # P1
    ("slicer", "general"): {"filter", "orientation"},                # BR; orientation P1
}
TEXT_STYLE_SEEN = {"fontWeight", "fontSize", "color"}                # RR, BR; color S3

# Not yet in Megat's files or confirmed on screen. Listed with every push.
UNCONFIRMED: dict[tuple[str, str], set[str]] = {
    # Round 10, the Month dropdown's values: text at body size, and no frame of its own (the box is
    # the container's border, rounded as the buttons are). Neither is in Megat's files or the
    # published schema; each is the format pane's own wording (Values: text size, border).
    ("slicer", "items"): {"textSize", "outline"},
}
UNCONFIRMED_VALUES: list[str] = [
    "items.outline 'None' on the Month dropdown",
]
CORNER = 4   # one corner radius: panels, the tab bar, and every visual box (theme.json border radius)

# Written as true, but a screenshot showed they did not take. Not set true again until a
# hand reference shows the right form. Page 1 round 2: data labels on the 100% stacked gap chart.
DID_NOT_TAKE: dict[tuple[str, str], set[str]] = {}
# (Round 2's labels.show on the 100% stacked gap chart did not show; Megat's hand
# reference, d1878b6, wrote the same setting, so it is confirmed. The one other
# difference in that file: Desktop dropped "isDefaultSort": false from the sort.)
TEXT_STYLE_UNCONFIRMED: set[str] = set()

# Microsoft's axis, legend, label and data colour objects are shared by the cartesian
# charts, so a name seen on one of them counts for the others. Each use is listed.
CARTESIAN = {"lineChart", "clusteredBarChart", "hundredPercentStackedBarChart", "columnChart",
             "lineClusteredColumnComboChart", "barChart", "clusteredColumnChart"}
FAMILY_OBJECTS = {"categoryAxis", "valueAxis", "legend", "labels", "dataPoint"}
SUBTITLE_WORDS = 8

# Smallest sizes Desktop drew on page 0. A line chart at 276 by 67 and 276 by 74 did not
# draw; at 276 by 100 it did. Bars: the round 2 screenshot scrolled with bars 26.5 px
# apart; round 3 drew six bars in 206 px with the title off. So 27 px per bar, plus 40 px
# with the chart title off or 76 px with it on.
MIN_SIZE = {
    "lineChart": dict(w=200, h=100),
    "hundredPercentStackedBarChart": dict(w=240, h=150),   # drew at 432 wide; 240 untested
    "clusteredBarChart": dict(w=150, h=150),
    "barChart": dict(w=240, h=150),
    "clusteredColumnChart": dict(w=200, h=120),
}
BAR_PER_CATEGORY = 27
BAR_CHROME = {True: 76, False: 40}

# Tables and matrices must show every row and column without a scrollbar. Page 1 round 2
# screenshots: a one-line row is 25 px, a two-line row 42 (17 a line), a header with the
# sort arrow 48, and the bottom 18 px of the box is kept clear (the matrix clipped its
# last row there). Columns adding to 560 px in a 592 px table still scrolled sideways, so
# each column takes about 12 px more than its width, plus 12.
TABLE_ROW, TABLE_LINE, TABLE_HEADER, TABLE_BOTTOM = 25, 17, 48, 18
COLUMN_PAD, TABLE_EDGE = 12, 12
TABLE_SLACK = 24   # kept for the round 1 calls; table_width() is the rule now


def table_height(row_lines: list[int], header: int = TABLE_HEADER) -> int:
    """Height a table needs to show every row: row_lines is the lines each row wraps to."""
    return header + sum(TABLE_ROW + (n - 1) * TABLE_LINE for n in row_lines) + TABLE_BOTTOM


def table_width(widths: list[int], pad: int = COLUMN_PAD) -> int:
    """Width a table needs so it does not scroll sideways. A matrix pads less: 120 + 9 x 116
    in 1224 px showed no scrollbar (page 1 round 2), so 4 a column."""
    return sum(widths) + pad * len(widths) + TABLE_EDGE


MATRIX_COLUMN_PAD = 4


# Data labels (page 1 round 2): on clustered bars thinner than a label, the label of the
# lower bar sat on the bar above. A 9pt label is about 14 px tall; a two-digit label needs
# a segment about 16 px wide. Category names take about 70 px left of a bar chart's plot.
LABEL_H, LABEL_MIN_PX, AXIS_LABEL_W, DEFAULT_INNER_PADDING, LABEL_ROOM = 14, 24, 70, 20, 1.15
# LABEL_MIN_PX was 16; page 1 round 4: two-digit labels dropped from segments of 16 and 20 px
# and showed in 25 px, so a stacked segment needs 24 px for its label.
# With labelOverflow on (H3), Legal's 10 showed in a 20.6 px segment and Finance's 13 did not
# in 16 px (page 1 round 6), so an overflowing label needs 20 px.
LABEL_MIN_PX_OVERFLOW = 20
AXIS_CHROME = 105      # a bar chart's width less its plot: team names and margins (round 8 screenshots)
LABEL_ROOM_PX = 7      # a label inside a stacked segment needs its width and this much
CATEGORY_ROOM = 18     # a column chart's axis name stays level when its slot is this much wider
LEGEND_SAFETY = 1.05   # a legend's text, estimated, fits its box with this much to spare (and TEXT_INSET)


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
    """A white panel with rounded corners: an empty text box whose own box is drawn, white, with
    the theme's corner radius (round 7: a rectangle shape did not round its corners; the
    slicer boxes, drawn by their container, did)."""
    return {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": "\u00a0"}]}]}}]},
        "visualContainerObjects": {
            "title": [{"properties": OFF}],
            "background": [{"properties": {"show": lit("true"), "color": colour(WHITE)}}],
            "border": [{"properties": {"show": lit("true"), "color": colour(WHITE), "radius": lit(f"{CORNER}D")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def navigator() -> dict:
    """The page navigator, as Desktop wrote it on the PC."""
    return {
        "visualType": "pageNavigator",
        "objects": {
            "text": [{"properties": {"fontSize": lit("10D"), "verticalAlignment": text("middle")},
                      "selector": {"id": "default"}}],
            "shape": [{"properties": {"tileShape": text("rectangleRounded"),
                                      "rectangleRoundedCurve": lit(f"{CORNER}L")},
                       "selector": {"id": "default"}}],
            "pages": [{"properties": {"showHiddenPages": lit("false")}}],
            "outline": [{"properties": OFF}],
        },
        "drillFilterOtherVisuals": True,
    }


def text_width(runs: list[tuple[str, dict]]) -> float:
    """Estimated width of one line of text runs."""
    w = 0.0
    for value, style in runs:
        size = _run_size(style)
        w += len(value) * CHAR_W * size * (BOLD_W if (style or {}).get("fontWeight") == "bold" else 1)
    return w


# Round 8: one gap of GAP px between all panels, between the header and the first row, and as
# the outer margin on every side.
GAP = MARGIN = 16
# Round 9: the tab bar 40 px tall (Megat); the question beside the title on the title row, so the
# taller bar costs the body nothing.
HEADER_NAV = (MARGIN, MARGIN, PAGE_W - 2 * MARGIN, 40)
HEADER_TITLE_Y, HEADER_TITLE_H = 72, 34       # GAP below the tab bar
QUESTION_DY, QUESTION_H = 8, 23               # the question, 12pt, its baseline on the title's
CONTROL_Y, CONTROL_H = 72, 40                 # controls: the title row, at its right (round 7 clipped at 30)
BUTTON_MIN_H = 36                             # a button row: 30 px clipped (round 7), 20 px drew blank (round 8)
BUTTON_TEXT_PAD = 36                          # round 9: "Consulting" (62 px est.) cut in a 90 px button, "Check-in" (50) whole
DROPDOWN_PAD = 48                             # a dropdown: its text, the arrow and margins
LINE_GREY = "#C9D1D4"                         # the buttons' own outline, unpicked
BUTTON_DEFAULT_COLUMNS = 3                    # round 8: six buttons in a 432 by 40 box drew as two rows of three
FOOTER_H = 18
FOOTER_Y = PAGE_H - MARGIN - FOOTER_H         # 686: the sources and period, one grey line
BODY_END = FOOTER_Y - ROW_GAP                 # 682: panels end here
FIT_SHARE = 0.2                               # at most a fifth of a panel left empty under or beside a piece


def body_top(p: "Page") -> int:
    """The first row's top: GAP under the lowest piece of the header (title, question, controls)."""
    panels = {v.on for v in p.visuals if v.on}
    return max(v.bottom for v in p.visuals if v.on is None and v.vt != "pageNavigator"
               and v.name not in panels and not v.name.endswith("_footer")) + GAP


def header(p: "Page", prefix: str, title: str, question: str | None, sources: str, period: str) -> None:
    """Every page: the tab bar; the title, and its question beside it (round 7: no other text in the
    header; round 9: one row); the sources and period as one grey line at the foot."""
    p.add(f"{prefix}_navigator", HEADER_NAV, navigator(), z=0)
    t_runs = [(title, pt(18, bold=True, color=INK))]
    tw = int(text_width(t_runs) * 1.1) + 12
    p.add(f"{prefix}_title", (16, HEADER_TITLE_Y, tw, HEADER_TITLE_H), textbox([t_runs]))
    if question:
        q_runs = [(question, pt(12, color=INK_SOFT))]
        p.add(f"{prefix}_question", (16 + tw + 4, HEADER_TITLE_Y + QUESTION_DY, int(text_width(q_runs) * 1.1) + 12,
                                     QUESTION_H), textbox([q_runs]))
    p.add(f"{prefix}_footer", (16, FOOTER_Y, 1248, FOOTER_H), textbox([[
        (sources + " · ", pt(9, color=INK_SOFT)), (period, pt(9, color=INK_SOFT))]]))


def button_slicer(table: str, col: str, display: str, start: str | None = None, strict: bool = True,
                  buttons: int = 2) -> dict:
    """A row of buttons, as Megat's placement toggle (H2, commit 1141219): no header, no box, the
    picked button marine with white text. Round 8: every control is one of these (the dropdown
    drew a box of its own); strict means one button is always picked, else none picked is all."""
    general = {}
    if start:
        general["filter"] = {"filter": {
            "Version": 2, "From": [{"Name": "b", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": col}}],
                "Values": [[{"Literal": {"Value": "'" + start.replace("'", "''") + "'"}}]]}}}]}}
    objects = {
        "data": [{"properties": {}}],
        "header": [{"properties": OFF}],
        "selection": [{"properties": {"singleSelect": lit("true"),
                                      "strictSingleSelect": lit("true" if strict else "false")}}],
    }
    if general:
        objects["general"] = [{"properties": general}]
    if buttons > BUTTON_DEFAULT_COLUMNS:
        objects["layout"] = [{"properties": {"rowCount": lit("1L"), "columnCount": lit(f"{buttons}L")}}]
    return {
        "visualType": "advancedSlicerVisual",
        "query": {"queryState": {"Values": {"projections": [proj_column(table, col, display=display)]}}},
        "objects": objects,
        "visualContainerObjects": {"background": [{"properties": OFF}], "border": [{"properties": OFF}],
                                   "title": [{"properties": OFF}]},
        "drillFilterOtherVisuals": True,
    }


def dropdown(table: str, col: str, start: str) -> dict:
    """Round 10: the Month control as a dropdown showing the picked month in full. Its box is the
    container's: white, a light grey border, the 4 px corner the buttons have; the values at body
    size (10pt) with no frame of their own; no header."""
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj_column(table, col, active=True)]}}},
        "objects": {
            "data": [{"properties": {"mode": text("Dropdown")}}],
            "selection": [{"properties": {"singleSelect": lit("true"), "strictSingleSelect": lit("true")}}],
            "header": [{"properties": OFF}],
            "items": [{"properties": {"textSize": lit("10D"), "outline": text("None")}}],
            "general": [{"properties": {"filter": {"filter": {
                "Version": 2, "From": [{"Name": "d", "Entity": table, "Type": 0}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": col}}],
                    "Values": [[{"Literal": {"Value": "'" + start.replace("'", "''") + "'"}}]]}}}]}}}}],
        },
        "visualContainerObjects": {
            "title": [{"properties": OFF}],
            "background": [{"properties": {"show": lit("true"), "color": colour(WHITE)}}],
            "border": [{"properties": {"show": lit("true"), "color": colour(LINE_GREY), "radius": lit(f"{CORNER}D")}}],
        },
        "drillFilterOtherVisuals": True,
    }


def figure_width(longest: str) -> int:
    """A 24pt figure's width: 17.8 px a character, measured on the round 8 screenshots ("44.5%" 88 px,
    "89.4%" 87, "4" 18)."""
    return round(len(longest) * FIGURE_CHAR_PX)


def figure_band(p: "Page", key: str, pan: str, x: int, y: int, w: int, figure: str, title: str,
                count: str | None = None, sub: str | None = None, longest: str = "", group: str = "t",
                over_table: bool = False, widest: str = "100.0%") -> int:
    """Every panel led by a figure: the figure at the top left; the panel's title FIGURE_TITLE_GAP right
    of the figure's text, whatever its width, with the count (or a grey line) under the title.
    Over a table, the figure moves in by TABLE_TEXT_INSET so it lines up with the table's text
    (round 9). Returns the band's bottom edge."""
    fx = x + PANEL_PAD_X + (TABLE_TEXT_INSET if over_table else 0)
    # round 10: the box holds the widest value the figure can show ("100.0%" for a share) with
    # FIGURE_BOX_PAD to spare ("44.5%" was cut with 17 px); the title sits FIGURE_TITLE_GAP right of
    # that widest value, over the box's empty end
    fw = figure_width(widest) + FIGURE_BOX_PAD
    tx = fx + figure_width(widest) + FIGURE_TITLE_GAP
    tw = x + w - PANEL_PAD_X - tx
    t_vis = textbox([[(title, pt(10, bold=True, color=INK))]])
    th = math.ceil(text_height(t_vis, tw))
    p.add(f"{key}_figure", (fx, y + PANEL_PAD_TOP, fw, FIGURE_H), value_card(figure, FIGURE_PT),
          on=pan, group=group, longest_value=widest, kind="band figure")
    p.add(f"{key}_title", (tx, y + PANEL_PAD_TOP, tw, th), t_vis, on=pan, group=group, z=3100)
    if count:
        p.add(f"{key}_count", (tx, y + PANEL_PAD_TOP + th, tw, 24), value_card(count, 10, colour(INK_SOFT)),
              on=pan, group=group, longest_value="", z=3100)
        below = th + 24
    else:
        s_vis = textbox([[(sub or "", pt(9, color=INK_SOFT))]])
        sh = math.ceil(text_height(s_vis, tw))
        p.add(f"{key}_sub", (tx, y + PANEL_PAD_TOP + th, tw, sh), s_vis, on=pan, group=group, kind="subtitle", z=3100)
        below = th + sh
    return y + PANEL_PAD_TOP + max(FIGURE_H, below)


FIGURE_CHAR_PX = 17.8          # a 24pt figure, a character (round 8 screenshots)
FIGURE_TITLE_GAP = 16          # the title sits this far right of the figure's widest text (Megat, round 9)
FIGURE_BOX_PAD = 28            # a figure box holds its widest text with this to spare (round 9: 17 px cut it)
TABLE_TEXT_INSET = 23          # a table's or matrix's text starts this far in from its box (round 8)
FIGURE_H, FIGURE_PT = 48, 24   # the figure in a band: 24pt (28pt drew in 54 px on page 0)


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


NOTES_LINE_PX = 18   # a 9pt line, one paragraph each: 17.0 px on the round 8 Notes screenshot (15.6 estimated)


def notes_height(visual: dict, width: int) -> float:
    """Height of a text box of one-line 9pt paragraphs, as Desktop spaces them (round 8 Notes)."""
    lines = 0
    for para in visual["objects"]["general"][0]["properties"]["paragraphs"]:
        lines += wrapped_lines([(r["value"], r.get("textStyle")) for r in para["textRuns"]], width)
    return lines * NOTES_LINE_PX + 4


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
    need_w: int = 0                      # a table's width need (table_width), so it does not scroll
    need_h: int = 0                      # a table's header and rows (table_height)
    series: int = 1                      # bars side by side in each category (clustered)
    label_min_share: float = 0.0         # stacked: the thinnest labelled segment, as a share of its bar
    max_value: float = 0.0               # the longest bar, when the value axis end is fixed
    legend: bool = False                 # a legend text box: every entry on one line, top right of its panel
    kind: str | None = None              # "subtitle": at most SUBTITLE_WORDS words
    longest_value: str = ""              # a card showing text: its longest text, which must fit
    longest_category: str = ""           # column charts: the longest axis label, kept on one line
    longest_label: str = ""              # column charts: the longest data label, kept inside its column
    buttons: int = 0                     # a button slicer: how many buttons it draws
    longest_button: str = ""             # a button slicer: its longest label
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
    number: int | None = None            # page number in CHECK.md
    answers: dict = field(default_factory=dict)   # CHECK.md question -> [(visual, field shown)]
    awaiting: dict = field(default_factory=dict)  # visual -> the hand reference it waits for
    unlabelled: dict = field(default_factory=dict)  # chart -> why it has no data labels (sparklines)
    too_thin: dict = field(default_factory=dict)    # chart -> the labels Desktop cannot fit, told to Megat
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
                band = {f"{v.name[:-7]}_{k}" for v in (a, b) if v.kind == "band figure" for k in ("title", "count", "sub")}
                if a.name in band or b.name in band:
                    continue   # a figure band: the figure box's empty end runs under its title and count   # a figure band: the figure box's empty end runs under its title
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
            if v.categories and v.vt in COLUMN_TYPES:
                if (w - 20) / v.categories < BAR_PER_CATEGORY:
                    problems.append(f"{v.name}: {v.categories} columns do not fit across {w} px")
            elif v.categories:
                need = v.categories * BAR_PER_CATEGORY + BAR_CHROME[title_on(v.visual)]
                if h < need:
                    problems.append(f"{v.name}: {v.categories} bars need {need} px, it is {h}")
        for v in vs:
            if v.need_w and v.box[2] < v.need_w:
                problems.append(f"{v.name}: columns need {v.need_w} px, it is {v.box[2]}")
            if v.need_h and v.box[3] < v.need_h:
                problems.append(f"{v.name}: rows need {v.need_h} px, it is {v.box[3]}")
        problems += self._labels()
        problems += self._tables_hold_text()
        problems += self._answers()
        problems += self._panel_text()
        problems += self._words()
        problems += self._formats()
        problems += self._grids()
        problems += self._round7()
        problems += self._spacing()
        problems += self._grid16()
        problems += self._fit()
        problems += self._headers()
        problems += self._buttons()
        problems += self._labels_present()
        problems += self._bands()
        problems += self._text_fit()
        # 7 setting names
        problems += [f"{v.name}: {p}" for v in vs for p in unseen(v.visual)]
        return problems

    def _labels(self) -> list[str]:
        out = []
        for v in self.visuals:
            objs = v.visual.get("objects", {})
            labels_on = any(it.get("properties", {}).get("show") == lit("true") for it in objs.get("labels", []))
            if v.categories and labels_on and v.vt not in COLUMN_TYPES:
                per_cat = (v.box[3] - BAR_CHROME[title_on(v.visual)]) / v.categories
                if v.vt == "clusteredBarChart":
                    pad = DEFAULT_INNER_PADDING
                    for it in objs.get("categoryAxis", []):
                        val = it.get("properties", {}).get("innerPadding")
                        if val:
                            pad = float(val["expr"]["Literal"]["Value"].rstrip("LD"))
                    thick = per_cat * (1 - pad / 100) / v.series
                    if thick < LABEL_H:
                        out.append(f"{v.name}: bars {thick:.1f} px thick, a label needs {LABEL_H}")
                overflow = any(it.get("properties", {}).get("labelOverflow") == lit("true")
                               for it in objs.get("labels", []))
                need_px = LABEL_MIN_PX_OVERFLOW if overflow else LABEL_MIN_PX
                if v.label_min_share and v.name not in self.awaiting:
                    # round 9: the plot is the chart less AXIS_CHROME (page 0: 432 px chart, 327 px of bar);
                    # a label needs its own width and LABEL_ROOM_PX ("7.5%" did not show in 24.5 px,
                    # "9.2%" did in 30; "10" did in 20.6 px)
                    seg = (v.box[2] - AXIS_CHROME) * v.label_min_share
                    if v.longest_label:
                        need_px = text_width([(v.longest_label, pt(9))]) + LABEL_ROOM_PX
                    if seg < need_px:
                        out.append(f"{v.name}: thinnest segment {seg:.1f} px, its label needs {need_px:.1f}")
            if v.categories and v.vt in COLUMN_TYPES:
                # Round 7: "Month 1" slanted in 48 px slots (page 4) and stayed level in 61 px slots
                # (page 2), so a slot holds its name plus CATEGORY_ROOM.
                per_cat = (v.box[2] - 20) / v.categories
                if v.longest_category and text_width([(v.longest_category, pt(9))]) + CATEGORY_ROOM > per_cat:
                    out.append(f"{v.name}: '{v.longest_category}' needs {CATEGORY_ROOM} px more than its "
                               f"{per_cat:.0f} px slot to stay level")
                if labels_on and v.longest_label:
                    # a label above a column may be wider than the column, not wider than its slot
                    slot = per_cat / v.series
                    if text_width([(v.longest_label, pt(9))]) + 8 > slot:
                        out.append(f"{v.name}: label '{v.longest_label}' is wider than its slot ({slot:.0f} px)")
            for it in objs.get("valueAxis", []):
                end = it.get("properties", {}).get("end")
                if end and v.max_value:
                    e = float(end["expr"]["Literal"]["Value"].rstrip("LD"))
                    if e < LABEL_ROOM * v.max_value:
                        out.append(f"{v.name}: axis ends at {e}, under {LABEL_ROOM} x the longest bar {v.max_value}")
            if v.legend:
                for para in v.visual["objects"]["general"][0]["properties"]["paragraphs"]:
                    runs = [(r["value"], r.get("textStyle")) for r in para["textRuns"]]
                    if wrapped_lines(runs, int((v.box[2] - 2 * TEXT_INSET) / LEGEND_SAFETY) + 2 * TEXT_INSET) > 1:
                        out.append(f"{v.name}: legend does not fit on one line with room to spare")
        return out

    def _panel_text(self) -> list[str]:
        """At most two lines of text (title, subtitle) above the first visual in a panel."""
        out = []
        for pname in {v.on for v in self.visuals if v.on}:
            members = [v for v in self.visuals if v.on == pname]
            charts = [v for v in members if v.vt != "textbox"]
            if not charts:
                continue
            first = min(v.top for v in charts)
            rows: dict[int, int] = {}
            for t in members:
                if t.vt != "textbox" or t.bottom > first:
                    continue
                sits_on = any(c.top == t.bottom and _overlap_x(c, t) for c in charts)
                if sits_on:
                    continue   # a caption on its visual
                paras = [pa for pa in t.visual["objects"]["general"][0]["properties"]["paragraphs"]
                         if "".join(r["value"] for r in pa["textRuns"]).strip("\u00a0 ")]
                rows[t.top] = max(rows.get(t.top, 0), len(paras))
            if sum(rows.values()) > 2:
                out.append(f"{pname}: {sum(rows.values())} lines of text before its first visual, not 2")
        return out

    def _words(self) -> list[str]:
        out = []
        for v in self.visuals:
            texts = []
            if v.vt == "textbox":
                for pa in v.visual["objects"]["general"][0]["properties"]["paragraphs"]:
                    texts += [r["value"] for r in pa["textRuns"]]
            for role in v.visual.get("query", {}).get("queryState", {}).values():
                texts += [pr.get("displayName", "") for pr in role["projections"]]
            for objs in (v.visual.get("objects", {}), v.visual.get("visualContainerObjects", {})):
                for it in objs.get("header", []) + objs.get("title", []):
                    t = it.get("properties", {}).get("text")
                    if t:
                        texts.append(t["expr"]["Literal"]["Value"])
            for t in texts:
                for w in WORKING_TERMS:
                    if w.lower() in t.lower():
                        out.append(f"{v.name}: working term '{w}' in \"{t[:50]}\"")
        return out

    def _formats(self) -> list[str]:
        out = []
        fmts = model_formats()
        for v in self.visuals:
            for role in v.visual.get("query", {}).get("queryState", {}).values():
                for pr in role["projections"]:
                    f = pr["field"]
                    if "Measure" not in f:
                        continue
                    name = f["Measure"]["Property"]
                    fmt = fmts.get(("Measure", name))
                    if fmt not in NUMBER_FORMATS and fmt not in ("text", "dynamic"):
                        out.append(f"{v.name}: {name} is formatted '{fmt}', not a count, percentage or points")
        return out

    def panels(self) -> set[str]:
        return {v.on for v in self.visuals if v.on}

    def _round7(self) -> list[str]:
        out = []
        panels = self.panels()
        if not any(v.name.endswith("_footer") and v.top == FOOTER_Y for v in self.visuals):
            out.append("no sources line at the foot of the page")
        for v in self.visuals:
            if v.on is None and v.name not in panels and v.vt not in ("pageNavigator",) \
                    and not v.name.endswith(("_footer", "_title", "_question", "_header_line")) \
                    and v.vt not in ("slicer", "advancedSlicerVisual") and v.bottom > BODY_END:
                out.append(f"{v.name} runs into the foot of the page")
            if v.on in panels and v.bottom > BODY_END:
                out.append(f"{v.name} runs into the foot of the page")
            if v.kind == "subtitle":
                words = " ".join(r["value"] for pa in v.visual["objects"]["general"][0]["properties"]["paragraphs"]
                                 for r in pa["textRuns"]).split()
                if len(words) > SUBTITLE_WORDS:
                    out.append(f"{v.name}: subtitle has {len(words)} words, more than {SUBTITLE_WORDS}")
            if v.legend and v.on:
                p = self.get(v.on)
                if v.right != p.right - PANEL_PAD_X:
                    out.append(f"{v.name}: a legend sits at the top right of its panel")
                firsts = [c.top for c in self.visuals if c.on == v.on and c.vt not in ("textbox", "cardVisual")]
                if firsts and v.top >= min(firsts):
                    out.append(f"{v.name}: a legend sits above its chart, in the panel's top rows")
            if v.longest_value and v.vt == "cardVisual":
                size = float(v.visual["objects"]["value"][0]["properties"]["fontSize"]["expr"]["Literal"]["Value"].rstrip("D"))
                if text_width([(v.longest_value, pt(int(size)))]) + 2 * TEXT_INSET > v.box[2]:
                    out.append(f"{v.name}: '{v.longest_value}' is cut at {v.box[2]} px")
        for p in panels:
            if self.get(p).bottom > BODY_END:
                out.append(f"{p} runs into the foot of the page")
        return out

    def _grids(self) -> list[str]:
        """A grid's value measure is blank for Power BI's blank row and column member."""
        out = []
        bodies = measure_bodies()
        for v in self.visuals:
            if v.vt != "pivotTable":
                continue
            qs = v.visual["query"]["queryState"]
            fields = [pr["field"]["Column"] for role in ("Rows", "Columns") for pr in qs.get(role, {}).get("projections", [])]
            for pr in qs["Values"]["projections"]:
                body = bodies.get(pr["field"]["Measure"]["Property"], "")
                for f in fields:
                    guard = f"ISBLANK ( SELECTEDVALUE ( {f['Expression']['SourceRef']['Entity']}[{f['Property']}] ) )"
                    if guard not in body:
                        out.append(f"{v.name}: {pr['field']['Measure']['Property']} does not blank the empty "
                                   f"{f['Property']} member, so the grid can show a blank row")
        return out

    def _tables_hold_text(self) -> list[str]:
        out = []
        kinds = model_fields()
        for v in self.visuals:
            if v.vt != "tableEx":
                continue
            for role in v.visual["query"]["queryState"].values():
                for pr in role["projections"]:
                    f = pr["field"]
                    key = ("Measure" if "Measure" in f else "Column",
                           next(iter(f.values()))["Property"])
                    if kinds.get(key) != "text":
                        out.append(f"{v.name}: {key[1]} is not text; a table holds text only, numbers go in charts")
        return out

    def _answers(self) -> list[str]:
        out = []
        if self.number is None:
            return out
        wanted = check_questions(self.number)
        if set(wanted) != set(self.answers):
            out.append(f"CHECK.md questions for page {self.number} are {sorted(wanted)}; "
                       f"the page answers {sorted(self.answers)}")
        for q, reads in self.answers.items():
            for name, prop in reads:
                v = next((x for x in self.visuals if x.name == name), None)
                if v is None:
                    out.append(f"question {q}: no visual {name}")
                    continue
                props = [next(iter(pr["field"].values()))["Property"]
                         for role in v.visual.get("query", {}).get("queryState", {}).values()
                         for pr in role["projections"]]
                if prop not in props:
                    out.append(f"question {q}: {name} does not show {prop}")
                if v.categories and name not in self.awaiting and not any(
                        it.get("properties", {}).get("show") == lit("true")
                                            for it in v.visual.get("objects", {}).get("labels", [])):
                    out.append(f"question {q}: {name} has no data labels, so the figure needs a hover")
        return out

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
                inset = all(v.vt in INSET_TYPES for v in g2 if v.top == top2)
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
        return out

    def _grid16(self) -> list[str]:
        """Round 8: one gap, GAP px, between panels (down and across), between the header and the
        first row, between the tab bar and the controls, and the outer margin on all sides."""
        out = []
        vs = self.visuals
        names = self.panels()
        panels = [v for v in vs if v.name in names]
        controls = [v for v in vs if v.on is None and v.vt in ("slicer", "advancedSlicerVisual")]
        nav = [v for v in vs if v.vt == "pageNavigator"]
        footer = [v for v in vs if v.name.endswith("_footer")]
        if min(v.left for v in vs) != MARGIN or max(v.right for v in vs) != PAGE_W - MARGIN:
            out.append(f"the page's left and right margins are not {MARGIN} px")
        for v in vs:
            if v.left < MARGIN or v.right > PAGE_W - MARGIN:
                out.append(f"{v.name} is inside the {MARGIN} px margin")
        if not nav or nav[0].top != MARGIN:
            out.append(f"the tab bar is not {MARGIN} px from the top")
        if not footer or footer[0].bottom != PAGE_H - MARGIN:
            out.append(f"the sources line is not {MARGIN} px from the bottom")
        if panels:
            first = min(p.top for p in panels)
            if first != body_top(self):
                out.append(f"the first row is {first - body_top(self) + GAP} px under the header, not {GAP}")
            if max(p.bottom for p in panels) != BODY_END:
                out.append(f"the last row ends at {max(p.bottom for p in panels)}, not {BODY_END}: "
                           "an empty band at the foot of the page")
        for c in controls:
            if nav and c.top - nav[0].bottom != GAP:
                out.append(f"{c.name} is {c.top - nav[0].bottom} px under the tab bar, not {GAP}")
        boxes = panels + controls
        for a in boxes:
            below = [b for b in panels if b is not a and _overlap_x(a, b) and b.top >= a.bottom]
            if below and a in panels and min(b.top for b in below) - a.bottom != GAP:
                out.append(f"{a.name}: {min(b.top for b in below) - a.bottom} px to the panel below, not {GAP}")
            right = [b for b in boxes if b is not a and a.top < b.bottom and b.top < a.bottom and b.left >= a.right]
            if right and min(b.left for b in right) - a.right != GAP:
                out.append(f"{a.name}: {min(b.left for b in right) - a.right} px to the box at its right, not {GAP}")
        return out

    def _fit(self) -> list[str]:
        """Round 8: a panel's size fits its content. Under every piece (over its width) and right of
        it (over its height), the empty band is at most FIT_SHARE of the panel. A table or grid
        counts by the rows and columns it shows (need_h, need_w), not by its box."""
        out = []
        for pname in sorted(self.panels()):
            p = self.get(pname)
            members = [v for v in self.visuals if v.on == pname]

            def low(u):
                return u.top + u.need_h if u.need_h else u.bottom

            def far(u):
                return u.left + u.need_w if u.need_w else u.right
            worst_v = max(p.bottom - max(low(u) for u in members if _overlap_x(u, v)) for v in members)
            worst_h = max(p.right - max(far(u) for u in members if u.top < v.bottom and v.top < u.bottom)
                          for v in members)
            if worst_v > FIT_SHARE * p.box[3]:
                out.append(f"{pname}: {worst_v} px empty under its content, more than a fifth of its {p.box[3]} px")
            if worst_h > FIT_SHARE * p.box[2]:
                out.append(f"{pname}: {worst_h} px empty beside its content, more than a fifth of its {p.box[2]} px")
        return out

    def _headers(self) -> list[str]:
        """Round 8: a table's column headers sit on one line (page 3's "Cases matched" wrapped in 90 px)."""
        out = []
        for v in self.visuals:
            if v.vt != "tableEx":
                continue
            widths = {it["selector"]["metadata"]: float(it["properties"]["value"]["expr"]["Literal"]["Value"].rstrip("D"))
                      for it in v.visual["objects"].get("columnWidth", [])}
            for pr in v.visual["query"]["queryState"]["Values"]["projections"]:
                head = pr.get("displayName", pr["nativeQueryRef"])
                wd = widths.get(pr["queryRef"])
                if wd and text_width([(head, pt(10))]) + 2 * TEXT_INSET > wd:
                    out.append(f"{v.name}: header '{head}' does not sit on one line in {wd:.0f} px")
        return out

    def _buttons(self) -> list[str]:
        """Round 9: a button's height holds its label, and its width its longest label. Desktop lays more
        than BUTTON_DEFAULT_COLUMNS buttons out in rows of three unless the layout says one row."""
        out = []
        for v in self.visuals:
            if v.vt != "advancedSlicerVisual":
                continue
            if not v.buttons or not v.longest_button:
                out.append(f"{v.name}: a button slicer needs its button count and longest label for the check")
                continue
            layout = (v.visual["objects"].get("layout") or [{"properties": {}}])[0]["properties"]
            rows = 1 if layout.get("rowCount") == lit("1L") else math.ceil(v.buttons / min(v.buttons, BUTTON_DEFAULT_COLUMNS))
            cols = math.ceil(v.buttons / rows)
            if v.box[3] / rows < BUTTON_MIN_H:
                out.append(f"{v.name}: {rows} rows of buttons, {v.box[3] / rows:.0f} px each; a label needs {BUTTON_MIN_H}")
            if v.box[2] / cols < text_width([(v.longest_button, pt(10))]) + BUTTON_TEXT_PAD:
                out.append(f"{v.name}: '{v.longest_button}' is cut in a {v.box[2] / cols:.0f} px button")
        for v in self.visuals:
            if v.vt == "slicer" and v.on is None:
                if not v.longest_button:
                    out.append(f"{v.name}: a dropdown needs its longest value for the check")
                elif v.box[2] < text_width([(v.longest_button, pt(10))]) + DROPDOWN_PAD:
                    out.append(f"{v.name}: '{v.longest_button}' is cut in a {v.box[2]} px dropdown")
                if v.box[3] < BUTTON_MIN_H:
                    out.append(f"{v.name}: {v.box[3]} px is lower than a button row")
        return out

    def _labels_present(self) -> list[str]:
        """Round 9: every chart's data labels are written on, unless the page says why not; no labels on a
        stacked column chart with a series, which drew none (rounds 7 and 8)."""
        out = []
        charts = CARTESIAN | {"hundredPercentStackedBarChart"}
        for v in self.visuals:
            if v.vt not in charts:
                continue
            objs = v.visual.get("objects", {})
            on = any(it.get("properties", {}).get("show") == lit("true") and "selector" not in it
                     for it in objs.get("labels", []))
            if not on and v.name not in self.unlabelled:
                out.append(f"{v.name}: no data labels written, and the page does not say why")
            series = v.visual.get("query", {}).get("queryState", {}).get("Series")
            if on and v.vt == "columnChart" and series:
                out.append(f"{v.name}: labels on a stacked column chart with a series did not draw (rounds 7, 8)")
        return out

    def _bands(self) -> list[str]:
        """Round 9: in a figure band the title sits FIGURE_TITLE_GAP right of the figure's text."""
        out = []
        for v in self.visuals:
            if v.kind != "band figure":
                continue
            t = self.get(v.name[: -len("_figure")] + "_title")
            gap = t.left - (v.left + figure_width(v.longest_value))
            if gap != FIGURE_TITLE_GAP:
                out.append(f"{t.name}: {gap} px right of the figure's widest text, not {FIGURE_TITLE_GAP}")
            if v.box[2] < figure_width(v.longest_value) + FIGURE_BOX_PAD:
                out.append(f"{v.name}: '{v.longest_value}' would be cut in {v.box[2]} px")
            if "%" in v.longest_value and v.longest_value != "100.0%":
                out.append(f"{v.name}: a share's box must hold '100.0%', not only '{v.longest_value}'")
        return out

    def _text_fit(self) -> list[str]:
        out = []
        panels = self.panels()
        need = {v.name: (notes_height(v.visual, v.box[2]) if v.kind == "notes" else text_height(v.visual, v.box[2]))
                for v in self.visuals if v.vt == "textbox" and v.name not in panels}
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
        if any(v.vt == "shape" for v in self.visuals):
            print("  Unconfirmed values: " + "; ".join(UNCONFIRMED_VALUES))
        for name, note in self.awaiting.items():
            print(f"  Waiting for a hand reference: {name}: {note}")
        for name, note in self.too_thin.items():
            print(f"  Too thin for a label: {name}: {note}")
        if any(v.vt == "slicer" and "items" in v.visual["objects"] for v in self.visuals):
            print("  Unconfirmed values: " + "; ".join(UNCONFIRMED_VALUES))


def model_fields() -> dict[tuple[str, str], str]:
    """("Measure" or "Column", name) -> "text" or "number", read from the model's TMDL files:
    a measure with no format string, or a column of data type string, is text."""
    return {k: ("text" if v == "text" else "number") for k, v in model_formats().items()}


def model_formats() -> dict[tuple[str, str], str]:
    """("Measure" or "Column", name) -> the format string, "text", "dynamic" (a dynamic
    format string) or "column" (a non-text column)."""
    out: dict[tuple[str, str], str] = {}
    tables = PAGES.parent.parent.parent / "Rollout review.SemanticModel" / "definition" / "tables"
    for f in tables.glob("*.tmdl"):
        lines = f.read_text(encoding="utf-8-sig").splitlines()
        cur = None
        for line in lines:
            m = re.match(r"\t(measure|column) ('(?:[^']|'')*'|[^ =]+)", line)
            if m:
                name = m.group(2)
                name = name[1:-1].replace("''", "'") if name.startswith("'") else name
                cur = ("Measure" if m.group(1) == "measure" else "Column", name)
                out[cur] = "text" if cur[0] == "Measure" else "column"
            elif re.match(r"\t[^\t]", line):
                cur = None
            elif cur and line.strip().startswith("formatString:") and cur[0] == "Measure":
                out[cur] = line.strip().split(":", 1)[1].strip()
            elif cur and line.strip().startswith("formatStringDefinition") and cur[0] == "Measure":
                out[cur] = "dynamic"
            elif cur and line.strip() == "dataType: string":
                out[cur] = "text"
    return out


def measure_bodies() -> dict[str, str]:
    """Measure name -> DAX body, from measures.dax (the one written source)."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import dax_to_tmdl
    return {o.name: "\n".join(o.body) for o in dax_to_tmdl.parse()}


def check_questions(page: int) -> list[int]:
    """CHECK.md question numbers whose page column is this page."""
    out = []
    for line in (ROOT / "CHECK.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|", line)
        if m and int(m.group(2)) == page:
            out.append(int(m.group(1)))
    return out


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
            for p, val in it.get("properties", {}).items():
                if p in DID_NOT_TAKE.get((vt, obj), set()) and val == lit("true"):
                    out.append(f"setting {obj}.{p} true on {vt} did not take on screen; needs a hand reference")
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
