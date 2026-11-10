#!/usr/bin/env python3
"""Write the objects in measures.dax into the Power BI project's model files (TMDL).

measures.dax stays the one written source. Every object in it (a line "Name =" at the
left margin, with the DAX below it) carries, in the comment lines directly above it:

    // Create as: ...          "calculated column on <table>" for a column; a measure otherwise
    // format: <string>        the format string; "text" or "none" for no format string
    // format expression: <DAX>  optional: a dynamic format string (the label a visual shows)
    // description: <text>     the Description, word for word

Measures go into _Measures; calculated columns into the table the Create as line names.
Running it again replaces the objects it wrote before (matched by name), so the model
follows measures.dax.

    python3 scripts/dax_to_tmdl.py --check       parse and list the objects, write nothing
    python3 scripts/dax_to_tmdl.py --write       write into report/Rollout review.SemanticModel
    add --tables <dir> to write into another tables folder (for a test copy)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAX = ROOT / "measures.dax"
TABLES = ROOT / "report" / "Rollout review.SemanticModel" / "definition" / "tables"
MEASURE_TABLE = "_Measures"

# Calculated columns need a data type in TMDL
COLUMN_TYPES = {
    "tokens_per_run": "int64",
    "seats_arrive_week": "dateTime",
    "passing": "boolean",
    "baseline_month": "int64",
    "status_month": "int64",
    "team_baseline_label": "string",
    "match_label": "string",
    "smaller_model_result": "string",
}

START = re.compile(r"^(?!VAR\b)([A-Za-z_][^=/]*?) =$")


@dataclass
class Obj:
    name: str
    kind: str  # "measure" or "column"
    table: str
    fmt: str | None
    fmt_expr: str | None
    description: str
    body: list[str]
    line: int


def parse() -> list[Obj]:
    lines = DAX.read_text(encoding="utf-8").splitlines()
    objs, problems = [], []
    i = 0
    while i < len(lines):
        m = START.match(lines[i])
        if not m:
            i += 1
            continue
        name, start = m.group(1).strip(), i
        # the comment run directly above
        j = i - 1
        run = []
        while j >= 0 and lines[j].startswith("//"):
            run.insert(0, lines[j])
            j -= 1
        # the body: up to a blank line (bodies have none inside)
        k = i + 1
        while k < len(lines) and lines[k].strip():
            k += 1
        body = lines[i + 1 : k]
        create = next((l for l in run if l.startswith("// Create as:")), "")
        fmt_line = next((l for l in run if l.startswith("// format:")), None)
        desc_line = next((l for l in run if l.startswith("// description:")), None)
        expr_line = next((l for l in run if l.startswith("// format expression:")), None)
        col = re.search(r"calculated column on (\w+)", create)
        if fmt_line is None:
            problems.append(f"line {start + 1}: {name}: no '// format:' line above it")
        if desc_line is None:
            problems.append(f"line {start + 1}: {name}: no '// description:' line above it")
        fmt = None
        if fmt_line is not None:
            fmt = fmt_line.split("format:", 1)[1].strip()
            fmt = None if fmt in ("text", "none") else fmt
        objs.append(Obj(
            name=name,
            kind="column" if col else "measure",
            table=col.group(1) if col else MEASURE_TABLE,
            fmt=fmt,
            fmt_expr=expr_line.split("format expression:", 1)[1].strip() if expr_line else None,
            description=desc_line.split("description:", 1)[1].strip() if desc_line else "",
            body=body,
            line=start + 1,
        ))
        i = k
    names = [o.name for o in objs]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        problems.append(f"names used twice: {sorted(dupes)}")
    for o in objs:
        if o.kind == "column" and o.name not in COLUMN_TYPES:
            problems.append(f"{o.name}: calculated column with no data type in COLUMN_TYPES")
    if problems:
        sys.exit("measures.dax problems:\n  " + "\n  ".join(problems))
    return objs


def quote(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return name
    return "'" + name.replace("'", "''") + "'"


def tmdl(o: Obj) -> list[str]:
    out = [f"\t/// {o.description}", f"\t{o.kind} {quote(o.name)} ="]
    out += ["\t\t\t" + l if l.strip() else "" for l in o.body]
    if o.kind == "column":
        out += [f"\t\tdataType: {COLUMN_TYPES[o.name]}", "\t\tisDataTypeInferred", "\t\tsummarizeBy: none"]
    if o.fmt and not o.fmt_expr:   # a dynamic format string replaces the static one
        out.append(f"\t\tformatString: {o.fmt}")
    if o.fmt_expr:
        out.append(f"\t\tformatStringDefinition = {o.fmt_expr}")
    out.append("")
    return out


def children(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Split a table file into its header (the table line and its properties) and its
    child blocks (each starting at a one-tab line, with any /// lines above it)."""
    starts = [i for i, l in enumerate(lines) if re.match(r"\t[^\t]", l) and not l.startswith("\t///")
              and re.match(r"\t(measure|column|partition|hierarchy|annotation|changedProperty)\b", l)]
    if not starts:
        return lines, []
    # pull leading /// lines into the block they describe
    starts = [next((j for j in range(s, -1, -1) if not lines[j - 1].startswith("\t///")), s) if s > 0 else s
              for s in starts]
    header = lines[: starts[0]]
    blocks = [lines[a:b] for a, b in zip(starts, starts[1:] + [len(lines)])]
    return header, blocks


def block_name(block: list[str]) -> tuple[str, str] | None:
    line = next(l for l in block if not l.startswith("\t///"))
    m = re.match(r"\t(measure|column) ('(?:[^']|'')*'|[^ =]+)", line)
    if not m:
        return None
    name = m.group(2)
    if name.startswith("'"):
        name = name[1:-1].replace("''", "'")
    return m.group(1), name


def write(objs: list[Obj]) -> None:
    if not TABLES.is_dir():
        sys.exit(f"No model folder at {TABLES}. Pull the project from the PC first.")
    by_table: dict[str, list[Obj]] = {}
    for o in objs:
        by_table.setdefault(o.table, []).append(o)
    for table, items in by_table.items():
        path = TABLES / f"{table}.tmdl"
        if not path.exists():
            sys.exit(f"No file for table {table}: {path}")
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        header, blocks = children(lines)
        ours = {(o.kind, o.name) for o in items}
        kept = [b for b in blocks if block_name(b) not in ours]
        if table == MEASURE_TABLE:
            # hide the placeholder column from Enter data, so the table shows as a measure table
            for b in kept:
                if block_name(b) == ("column", "Column1") and "\t\tisHidden" not in b:
                    head = next(i for i, l in enumerate(b) if l.startswith("\tcolumn"))
                    b.insert(head + 1, "\t\tisHidden")
        # new objects go before the first partition, after the existing columns and measures
        cut = next((i for i, b in enumerate(kept) if any(l.startswith("\tpartition") for l in b)), len(kept))
        new = [l for o in items for l in tmdl(o)]
        before = [l for b in kept[:cut] for l in b]
        if before and before[-1].strip():
            before.append("")
        text = header + before + new + [l for b in kept[cut:] for l in b]
        path.write_text("\n".join(text).rstrip("\n") + "\n", encoding="utf-8")
        print(f"{path.name}: {len(items)} objects written, "
              f"{len(blocks) - len(kept)} replaced")


def main() -> None:
    global TABLES
    if "--tables" in sys.argv:
        TABLES = Path(sys.argv[sys.argv.index("--tables") + 1])
    objs = parse()
    if "--write" in sys.argv:
        write(objs)
    else:
        for o in objs:
            print(f"{o.line:5}  {o.kind:7} {o.table:17} {o.fmt or '-':16} {o.name}")
        print(f"\n{sum(o.kind == 'measure' for o in objs)} measures, "
              f"{sum(o.kind == 'column' for o in objs)} calculated columns")


if __name__ == "__main__":
    main()
