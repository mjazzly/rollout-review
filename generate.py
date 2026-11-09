#!/usr/bin/env python3
"""DASH-02 Rollout review: seeded synthetic data generator.

Writes every table in section 3 of DASH-02-DESIGN.md to data/*.csv, plus the
derived table data/fact_placement.csv (section 5 source placement rules).

Everything is synthetic. Seed 42; rerun with `python3 generate.py` and the
output is byte-for-byte the same. The five planted storylines (design note
section 7) are planted by the team parameters below and named in README.md.

How it works, in one paragraph: each person gets a seat week (staggered by
team) and a behaviour mode that can change at each month boundary. Weekly
usage, library runs, questions and the check-in are generated from that mode.
The source placement is then computed from the written tables only, by
`place()`, so Power BI and check.py can read the same result from data/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT = Path(__file__).resolve().parent / "data"

N_WEEKS = 24
WEEKS_PER_MONTH = 4  # six check-in months of four weeks each
FIRST_WEEK = pd.Timestamp("2026-05-18")  # a Monday; week 24 starts 2026-10-26
REMINDER_WEEKS = frozenset(w for w in range(1, N_WEEKS + 1) if w % 4 == 1)  # 1, 5, 9, 13, 17, 21
CHECKIN_WEEKS = {m: m * WEEKS_PER_MONTH for m in range(1, 7)}  # check-in taken at the end of week 4m

CATEGORIES = ["Rules and allowed use", "Drafting", "Summarising", "Analysis",
              "Research", "Formatting", "Coding"]
LEVELS = ["Junior", "Mid", "Senior", "Lead"]
REGIONS = ["Americas", "Europe", "Asia Pacific"]

# ---------------------------------------------------------------------------
# dim_checkpoint: FRAME-01, word for word from design note section 4
# ---------------------------------------------------------------------------
CHECKPOINTS = [
    (1, "No ticket", "On the ground", "Has no AI they are allowed to use for work yet",
     "Access, and a reason to use AI in the first week"),
    (2, "Ticket held", "On the ground", "Is allowed to use AI for work, but has not tried it yet",
     "A first task done side by side with someone who already uses AI"),
    (3, "Checked in", "On the ground", "Tried AI once or twice, then stopped",
     "A second task that fits their actual week"),
    (4, "Through security", "At the gate", "Is still working out what AI is allowed for, or has just read the rules",
     "A worked example from their own role"),
    (5, "Waiting to board", "At the gate", "Uses AI only in the weeks a reminder goes out",
     "One recurring task tied to a day of the week"),
    (6, "Boarding", "At the gate", "Has used AI once on real work that went to someone else",
     "Make that recurring task part of their routine"),
    (7, "Takeoff", "In the air", "Uses AI every week on one task, for a month or more",
     "A second task, and a place to share what works"),
    (8, "Above the clouds", "In the air", "Uses AI on several tasks and shares what works",
     "Ask them to show their team"),
    (9, "Frequent flyer", "In the air",
     "AI is part of how they work every week, and colleagues come to them with questions",
     "Give them a prompt to look after in the library, and point new starters their way"),
]
STAGE_OF = {cp: stage for cp, _, stage, _, _ in CHECKPOINTS}

# ---------------------------------------------------------------------------
# The check-in: FRAME-01's live form on the Frames page, word for word.
# Stage keys: "air", "gate", "ground"; q1 "No, or not yet" ends the form at No ticket.
# ---------------------------------------------------------------------------
Q_OPTIONS = {
    "q1_access": {"air": "Yes, and I know what I may use it for",
                  "gate": "Yes, but I am unsure what is allowed"},
    "q2_last_use": {"air": "This week", "gate": "Some weeks ago", "ground": "Only to try it out"},
    "q3_trigger": {"air": "Habit, it is part of how I work", "gate": "A reminder, or a task that needs it",
                   "ground": "I have not found the moment yet"},
    "q4_used_on": {"air": "Work that goes to someone else", "gate": "Small tasks and drafts I mostly rewrite",
                   "ground": "Nothing yet"},
    "q5_if_gone": {"air": "I would lose time every week", "gate": "A little", "ground": "Nothing"},
}
Q1_NO = "No, or not yet"
STAGE_KEY = {"On the ground": "ground", "At the gate": "gate", "In the air": "air"}

# ---------------------------------------------------------------------------
# Teams. Each parameter is what plants a storyline (design note section 7).
#   modes0: share of each starting behaviour once the seat lands
#   up:     chance per month boundary of stepping up one rung
#   lib:    share of active people who use the library at all; share of runs via library
# ---------------------------------------------------------------------------
MODES = ["none", "trial", "rules", "reminder", "sporadic", "weekly", "power", "lapsed"]
TEAMS = {
    # 5. Consulting: broad, steady adoption, highest library share, the benchmark
    "Consulting": dict(headcount=300, seat_week=2, no_seat=0.02,
                       modes0=dict(none=.12, trial=.10, rules=.04, reminder=.04, sporadic=.38, weekly=.32),
                       up=dict(wake=.15, retry=.15, rules=.25, reminder=.25, sw=.30, down=.03, lapse=.02),
                       lib_user=.85, lib_share=.62),
    # 2. Finance: many active only in reminder weeks, who place themselves at Takeoff
    "Finance": dict(headcount=200, seat_week=3, no_seat=0.03,
                    modes0=dict(none=.12, trial=.06, rules=.05, reminder=.62, sporadic=.10, weekly=.05),
                    up=dict(wake=.10, retry=.05, rules=.10, reminder=.03, sw=.10, down=.04, lapse=.03),
                    wake_to="reminder", lib_user=.30, lib_share=.25),
    # 3. Operations: repeat Summarising questions until the week-12 library item, then a jump
    "Operations": dict(headcount=250, seat_week=5, no_seat=0.03,
                       modes0=dict(none=.30, trial=.10, rules=.05, reminder=.20, sporadic=.30, weekly=.05),
                       up=dict(wake=.05, retry=.05, rules=.08, reminder=.05, sw=.08, down=.03, lapse=.03),
                       up_after_item=dict(wake=.35, retry=.30, rules=.30, reminder=.50, sw=.40, down=.02, lapse=.01),
                       lib_user=.25, lib_user_after_item=.85, lib_share=.15, lib_share_after_item=.45),
    # 1. Legal: seats first, most never try it
    "Legal": dict(headcount=120, seat_week=1, no_seat=0.0,
                  modes0=dict(none=.74, trial=.09, rules=.08, reminder=.02, sporadic=.04, weekly=.03),
                  up=dict(wake=.015, retry=.02, rules=.05, reminder=.05, sw=.05, down=.05, lapse=.05),
                  lib_user=.40, lib_share=.30),
    # People: in between, no planted story
    "People": dict(headcount=130, seat_week=9, no_seat=0.08,
                   modes0=dict(none=.28, trial=.12, rules=.08, reminder=.10, sporadic=.30, weekly=.12),
                   up=dict(wake=.10, retry=.10, rules=.15, reminder=.15, sw=.18, down=.04, lapse=.03),
                   lib_user=.50, lib_share=.30),
    # 4. Technology: good adoption; the Refinement story lives in its library items
    "Technology": dict(headcount=200, seat_week=4, no_seat=0.02,
                       modes0=dict(none=.12, trial=.10, rules=.04, reminder=.05, sporadic=.40, weekly=.29),
                       up=dict(wake=.12, retry=.12, rules=.20, reminder=.20, sw=.25, down=.04, lapse=.03),
                       lib_user=.60, lib_share=.40),
}
OPS_ITEM_WEEK = 12
OPS_CATEGORY = "Summarising"
OPS_REGULARS = 10  # Operations people who keep asking the Summarising question until LIB-16 exists
# Share of Rules and allowed use questions kept, by check-in month: high early, low by month 6
RULES_KEEP_BY_MONTH = {1: 1.0, 2: 0.9, 3: 0.65, 4: 0.5, 5: 0.35, 6: 0.3}

# Library items: (item_id, item_name, category, owner_team, published_week, answer_key_first, spread)
# spread: list of (team, first_week) where a second team starts running it.
ITEMS = [
    ("LIB-01", "Proposal outline from a brief", "Drafting", "Consulting", 3, True, [("Technology", 7)]),
    ("LIB-02", "Interview notes to key points", "Summarising", "Consulting", 4, True, []),
    ("LIB-03", "Market scan in five questions", "Research", "Consulting", 5, True, [("Finance", 15)]),
    ("LIB-04", "Slide text tightener", "Formatting", "Consulting", 7, False, []),
    ("LIB-05", "Workplan from meeting notes", "Analysis", "Consulting", 9, True, []),
    ("LIB-06", "Client question log tidy", "Formatting", "Consulting", 11, True, []),
    ("LIB-07", "What may I use it for: quick check", "Rules and allowed use", "Consulting", 6, True, []),
    ("LIB-08", "Findings memo first draft", "Drafting", "Consulting", 14, False, []),
    ("LIB-09", "Code review checklist", "Coding", "Technology", 4, True, []),
    ("LIB-10", "Error log explainer", "Coding", "Technology", 5, True, [("Operations", 14)]),
    ("LIB-11", "Test case writer", "Coding", "Technology", 6, True, []),
    ("LIB-12", "Release note drafter", "Drafting", "Technology", 8, False, []),
    ("LIB-13", "Query explainer", "Analysis", "Technology", 9, True, []),
    ("LIB-14", "Ticket summary", "Summarising", "Technology", 10, False, []),
    ("LIB-15", "Rota change notice", "Drafting", "Operations", 7, False, []),
    ("LIB-16", "Shift handover summary", "Summarising", "Operations", OPS_ITEM_WEEK, True, [("People", 18)]),
    ("LIB-17", "Supplier email reply", "Drafting", "Operations", 15, True, []),
    ("LIB-18", "Variance commentary draft", "Analysis", "Finance", 6, True, []),
    ("LIB-19", "Month-end checklist", "Formatting", "Finance", 14, False, []),
    ("LIB-20", "Policy question check", "Rules and allowed use", "Legal", 5, True, []),
    ("LIB-21", "Clause comparison table", "Analysis", "Legal", 13, True, []),
    ("LIB-22", "Job advert first draft", "Drafting", "People", 11, True, []),
    ("LIB-23", "Survey comments themes", "Summarising", "People", 16, False, []),
]
# 4. Technology: two pass on the smaller model at half the tokens; one retired, one merged in month 5
SMALLER_PASS = {"LIB-09": 0.50, "LIB-13": 0.50}  # tokens on the smaller tier, as a share of standard
RETIRED = {"LIB-12": 18}                          # item -> status_week
MERGED = {"LIB-14": (19, "LIB-10")}                # item -> (status_week, merged_into_item_id)
# Owners who answer colleagues' questions (the Frequent flyer candidates), by item
HELPER_ITEMS = {"LIB-01", "LIB-02", "LIB-05", "LIB-07", "LIB-09", "LIB-11", "LIB-16"}
# Items owned by the same person as an earlier item (some owners look after two)
SECOND_ITEM_OF = {"LIB-06": "LIB-02", "LIB-13": "LIB-11"}

LIMITS = {
    "Rules and allowed use": "Points to the policy text; does not give a ruling on a new case",
    "Drafting": "First draft only; the sender checks every fact and name",
    "Summarising": "Works on notes under 3,000 words; flags anything it could not place",
    "Analysis": "Explains the figures it is given; does not fetch or recompute them",
    "Research": "Public sources only; every claim carries its source line",
    "Formatting": "Changes layout and wording, never the figures",
    "Coding": "Suggests changes; a person runs the tests before merging",
}


def week_start(w: int) -> pd.Timestamp:
    return FIRST_WEEK + pd.Timedelta(weeks=w - 1)


def month_of(w: int) -> int:
    return (w - 1) // WEEKS_PER_MONTH + 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build(rng: np.random.Generator) -> dict[str, pd.DataFrame]:
    weeks = range(1, N_WEEKS + 1)

    # dim_week -----------------------------------------------------------
    dim_week = pd.DataFrame({
        "week_start": [week_start(w).date() for w in weeks],
        "month": [week_start(w).strftime("%Y-%m") for w in weeks],
        "checkin_month": [month_of(w) for w in weeks],
        "reminder_week": [w in REMINDER_WEEKS for w in weeks],
    })

    # dim_person ---------------------------------------------------------
    teams_list = [t for t, p in TEAMS.items() for _ in range(p["headcount"])]
    n = len(teams_list)
    order = rng.permutation(n)
    person_team = [teams_list[i] for i in order]
    pid = [f"P{i + 1:04d}" for i in range(n)]
    level = rng.choice(LEVELS, size=n, p=[.35, .35, .20, .10])
    region_p = {"Consulting": [.40, .35, .25], "Finance": [.30, .40, .30], "Operations": [.25, .30, .45],
                "Legal": [.35, .45, .20], "People": [.30, .35, .35], "Technology": [.30, .25, .45]}
    region = [rng.choice(REGIONS, p=region_p[t]) for t in person_team]
    start_days = rng.integers(0, (pd.Timestamp("2026-04-30") - pd.Timestamp("2014-01-06")).days, size=n)
    start_date = [(pd.Timestamp("2014-01-06") + pd.Timedelta(days=int(d))).date() for d in start_days]
    seat = []
    for t in person_team:
        p = TEAMS[t]
        if rng.random() < p["no_seat"]:
            seat.append(None)
        else:  # each team's wave lands over two weeks; Legal all in week 1
            seat.append(p["seat_week"] + (0 if t == "Legal" else int(rng.random() < .35)))
    dim_person = pd.DataFrame({"person_id": pid, "team": person_team, "level": level, "region": region,
                               "start_date": start_date, "seat_assigned_week": seat})
    seat_wk = dict(zip(pid, seat))
    team_of = dict(zip(pid, person_team))
    by_team = {t: [p for p in pid if team_of[p] == t] for t in TEAMS}

    # dim_library_item: owners first, because owners behave as power users ----
    owner_of: dict[str, str] = {}
    taken: set[str] = set()
    for item_id, _, _, team, pub, _, _ in ITEMS:
        if item_id in SECOND_ITEM_OF:
            owner_of[item_id] = owner_of[SECOND_ITEM_OF[item_id]]
            continue
        pool = [p for p in by_team[team] if seat_wk[p] is not None and seat_wk[p] <= pub - 1
                and p not in taken and dim_person.loc[int(p[1:]) - 1, "level"] in ("Mid", "Senior", "Lead")]
        if not pool:  # Operations and People get seats later; owners there are early in the wave
            pool = [p for p in by_team[team] if seat_wk[p] is not None and p not in taken]
        owner = pool[int(rng.integers(len(pool)))]
        owner_of[item_id] = owner
        taken.add(owner)
    item_rows = []
    for item_id, name, cat, team, pub, akf, _ in ITEMS:
        status, status_week, merged_into = "active", None, None
        if item_id in RETIRED:
            status, status_week = "retired", RETIRED[item_id]
        if item_id in MERGED:
            status, (status_week, merged_into) = "merged", MERGED[item_id]
        version = 2 if item_id in SMALLER_PASS or rng.random() < .35 else 1
        item_rows.append(dict(item_id=item_id, item_name=name, category=cat, owner_person_id=owner_of[item_id],
                              owner_team=team, version=version, limits=LIMITS[cat], answer_key_first=akf,
                              status=status, merged_into_item_id=merged_into, published_week=pub,
                              status_week=status_week))
    dim_library_item = pd.DataFrame(item_rows)
    item_info = {r["item_id"]: r for r in item_rows}
    spread = {i[0]: i[6] for i in ITEMS}
    owners = set(owner_of.values())
    owner_first_pub = {}
    for it, o in owner_of.items():
        owner_first_pub[o] = min(owner_first_pub.get(o, 99), item_info[it]["published_week"])
    helpers = {owner_of[i] for i in HELPER_ITEMS}
    helper_from = {owner_of[i]: item_info[i]["published_week"] for i in HELPER_ITEMS}

    def item_live(it: str, w: int) -> bool:
        r = item_info[it]
        return r["published_week"] <= w and (r["status_week"] is None or w < r["status_week"])

    avail_cache: dict[tuple[str, int], list[str]] = {}

    def items_for(team: str, w: int) -> list[str]:
        if (team, w) in avail_cache:
            return avail_cache[(team, w)]
        out = []
        for it, r in item_info.items():
            if not item_live(it, w):
                continue
            if r["owner_team"] == team or any(t == team and w >= s for t, s in spread[it]):
                out.append(it)
        avail_cache[(team, w)] = out
        return out

    # Behaviour modes per person per week ---------------------------------
    mode = {p: ["noseat"] * (N_WEEKS + 1) for p in pid}  # index 0 unused
    lib_user = {}
    for p in pid:
        t = team_of[p]
        tp = TEAMS[t]
        sw = seat_wk[p]
        lib_user[p] = rng.random() < tp["lib_user"]
        if sw is None:
            continue
        if p in owners:
            cur = "power"
        else:
            m0 = tp["modes0"]
            cur = str(rng.choice(list(m0), p=np.array(list(m0.values())) / sum(m0.values())))
        trial_left = int(rng.integers(1, 3)) if cur == "trial" else 0
        for w in range(sw, N_WEEKS + 1):
            if w > sw and w % 4 == 1 and p not in owners:  # month boundary: weeks 5, 9, 13, 17, 21
                after = t == "Operations" and w > OPS_ITEM_WEEK
                if after and w == 13:
                    lib_user[p] = rng.random() < tp["lib_user_after_item"]
                up = tp["up_after_item"] if after and w == 13 else tp["up"]
                r = rng.random()
                if cur == "none" and r < up["wake"]:
                    cur = tp.get("wake_to", "trial" if rng.random() < .4 else "sporadic")
                    trial_left = int(rng.integers(1, 3)) if cur == "trial" else 0
                elif cur in ("lapsed_trial", "lapsed") and r < up["retry"]:
                    cur = "sporadic"
                elif cur == "rules" and r < up["rules"]:
                    cur = "sporadic"
                elif cur == "reminder" and r < up["reminder"]:
                    cur = "sporadic"
                elif cur == "sporadic":
                    if r < up["sw"]:
                        cur = "weekly"
                    elif r > 1 - up["lapse"]:
                        cur = "lapsed"
                elif cur == "weekly" and r < up["down"]:
                    cur = "sporadic"
            mode[p][w] = cur
            if cur == "trial":
                # the trial uses up its one or two weeks, then the person stops
                if trial_left > 0:
                    mode[p][w] = "trial_on"
                    trial_left -= 1
                else:
                    cur = "lapsed_trial"
                    mode[p][w] = cur

    # fact_training: sessions per team, shown items, attendees --------------
    train_rows = []
    sid = 0
    forced: dict[tuple[str, int], str] = {}
    session_weeks = {"Consulting": [4, 9, 15, 20], "Technology": [6, 11, 17], "Operations": [8, 13, 19],
                     "Finance": [7, 16], "Legal": [3, 14], "People": [12, 19]}
    run_after_training = {"Consulting": .55, "Technology": .45, "Operations": .40, "Finance": .20,
                          "Legal": .12, "People": .30}
    for t, wks in session_weeks.items():
        for w in wks:
            avail = items_for(t, w)
            if not avail:
                continue
            sid += 1
            shown = avail[int(rng.integers(len(avail)))] if not (t == "Operations" and w == 13) else "LIB-16"
            seated = [p for p in by_team[t] if seat_wk[p] is not None and seat_wk[p] <= w]
            k = min(len(seated), int(rng.integers(18, 36)))
            att = rng.choice(seated, size=k, replace=False)
            for p in sorted(att):
                train_rows.append(dict(session_id=f"S{sid:02d}", person_id=p, team=t,
                                       session_week=week_start(w).date(), item_id_shown=shown))
                if mode[p][w] not in ("none",) and rng.random() < run_after_training[t]:
                    fw = w + int(rng.random() < .4)
                    if fw <= N_WEEKS and item_live(shown, fw):
                        forced[(p, fw)] = shown
    fact_training = pd.DataFrame(train_rows)

    # fact_usage_week and person-level library runs ------------------------
    usage_rows, lib_rows = [], []
    fav: dict[str, list[str]] = {}

    def lib_share(t: str, w: int) -> float:
        tp = TEAMS[t]
        if t == "Operations" and w >= OPS_ITEM_WEEK:
            return tp["lib_share_after_item"]
        return tp["lib_share"]

    for p in pid:
        sw = seat_wk[p]
        if sw is None:
            continue
        t = team_of[p]
        for w in range(sw, N_WEEKS + 1):
            md = mode[p][w]
            days = 0
            if md == "trial_on":
                days = int(rng.integers(2, 4))
            elif md == "rules":
                days = int(rng.integers(2, 3)) if rng.random() < .10 else (1 if rng.random() < .15 else 0)
            elif md == "reminder":
                if w in REMINDER_WEEKS:
                    days = int(rng.integers(2, 4)) if rng.random() < .88 else 0
                else:
                    days = 1 if rng.random() < .06 else 0
            elif md == "sporadic":
                days = int(rng.integers(2, 4)) if rng.random() < .42 else (1 if rng.random() < .2 else 0)
            elif md == "weekly":
                days = int(rng.integers(2, 5)) if rng.random() < .93 else (1 if rng.random() < .5 else 0)
            elif md == "power":
                days = int(rng.integers(3, 6)) if rng.random() < .97 else 2
            elif md in ("lapsed", "lapsed_trial", "none"):
                days = 1 if (md != "none" and rng.random() < .02) else 0
            forced_item = forced.get((p, w))
            if forced_item and days == 0:
                days = 1
            sessions = int(days * rng.integers(1, 4)) if days else 0
            runs = int(sessions * rng.integers(1, 4)) if sessions else 0
            lib_runs: dict[str, int] = {}
            if runs:
                avail = items_for(t, w)
                use_lib = (md == "power") or (lib_user[p] and md in ("sporadic", "weekly", "trial_on")
                                              and rng.random() < .80)
                if t == "Operations" and w >= OPS_ITEM_WEEK and "LIB-16" in avail and use_lib:
                    fav.setdefault(p, [])
                    if "LIB-16" not in fav[p] and rng.random() < .8:
                        fav[p].insert(0, "LIB-16")
                if use_lib and avail:
                    f = [i for i in fav.get(p, []) if i in avail]
                    want = int(rng.integers(2, 5)) if md == "power" else (2 if rng.random() < .15 else 1)
                    if md == "power":
                        own = [i for i, o in owner_of.items() if o == p and i in avail]
                        f = list(dict.fromkeys(own + f))
                    while len(f) < min(want, len(avail)):
                        cand = [i for i in avail if i not in f]
                        f.append(cand[int(rng.integers(len(cand)))])
                    fav[p] = f
                    chosen = f[:min(want, runs)]
                    total_lib = max(len(chosen), int(round(runs * min(.95, lib_share(t, w) * rng.uniform(.7, 1.3)))))
                    total_lib = min(total_lib, runs)
                    split = rng.multinomial(total_lib - len(chosen), [1 / len(chosen)] * len(chosen)) + 1 \
                        if total_lib >= len(chosen) else np.ones(len(chosen), dtype=int)
                    for it, k in zip(chosen, split):
                        if k > 0:
                            lib_runs[it] = lib_runs.get(it, 0) + int(k)
                if forced_item and forced_item in avail:
                    lib_runs[forced_item] = lib_runs.get(forced_item, 0) + 1
                    runs = max(runs, sum(lib_runs.values()))
            usage_rows.append(dict(person_id=p, week_start=week_start(w).date(), days_active=days,
                                   sessions=max(sessions, 1 if runs else 0), runs_total=runs,
                                   runs_via_library=sum(lib_runs.values())))
            for it, k in lib_runs.items():
                lib_rows.append(dict(item_id=it, person_id=p, week_start=week_start(w).date(), runs=k))
    fact_usage_week = pd.DataFrame(usage_rows)
    fact_library_run_person = pd.DataFrame(lib_rows).sort_values(["item_id", "week_start", "person_id"])
    lr = fact_library_run_person.assign(team=fact_library_run_person["person_id"].map(team_of))
    fact_library_run = (lr.groupby(["item_id", "team", "week_start"], as_index=False)
                          .agg(runs=("runs", "sum"), distinct_users=("person_id", "nunique")))

    # fact_question --------------------------------------------------------
    q_rate = {"none": .004, "noseat": 0, "trial_on": .05, "lapsed_trial": .006, "lapsed": .008, "rules": .30,
              "reminder": .015, "sporadic": .035, "weekly": .040, "power": .015}
    cat_w = {"Consulting": [.06, .26, .18, .20, .18, .08, .04], "Finance": [.10, .18, .14, .32, .08, .14, .04],
             "Operations": [.08, .20, .30, .16, .06, .14, .06], "Legal": [.30, .26, .16, .12, .10, .04, .02],
             "People": [.12, .30, .22, .10, .08, .14, .04], "Technology": [.05, .12, .10, .16, .08, .06, .43]}
    q_rows = []

    def add_q(p: str, w: int, cat: str) -> None:
        q_rows.append(dict(person_id=p, week=w, category=cat,
                           question_date=(week_start(w) + pd.Timedelta(days=int(rng.integers(0, 5)))).date()))

    for p in pid:
        if seat_wk[p] is None:
            continue
        t = team_of[p]
        for w in range(seat_wk[p], N_WEEKS + 1):
            md = mode[p][w]
            if rng.random() < q_rate.get(md, 0):
                if md == "rules":
                    cat = "Rules and allowed use"
                else:
                    wts = np.array(cat_w[t], dtype=float)
                    if t == "Operations":
                        wts[CATEGORIES.index(OPS_CATEGORY)] = 0  # Operations' Summarising volume is planted below
                    cat = str(rng.choice(CATEGORIES, p=wts / wts.sum()))
                add_q(p, w, cat)
    # 3. Operations: Summarising questions run hot until LIB-16 (week 12), then fall away
    ops_seated = [p for p in by_team["Operations"] if seat_wk[p] is not None]
    ops_regulars = sorted(rng.choice([p for p in ops_seated if p not in owners], size=OPS_REGULARS, replace=False))
    for w in range(TEAMS["Operations"]["seat_week"], N_WEEKS + 1):
        k = rng.poisson(3.2 if w < OPS_ITEM_WEEK else (1.2 if w == OPS_ITEM_WEEK else 0.12))
        for _ in range(k):
            cand = [p for p in ops_seated if seat_wk[p] <= w]
            if w < OPS_ITEM_WEEK:  # the same people keep coming back with the same request
                cand = [p for p in ops_regulars if seat_wk[p] <= w]
            add_q(cand[int(rng.integers(len(cand)))], w, OPS_CATEGORY)

    qdf = pd.DataFrame(q_rows).sort_values(["question_date", "person_id"]).reset_index(drop=True)
    actions, linked, answered_by, difficulty = [], [], [], []
    for _, r in qdf.iterrows():
        w, cat, t = r["week"], r["category"], team_of[r["person_id"]]
        live = [i for i, info in item_info.items() if info["category"] == cat and item_live(i, w)]
        own_team_live = [i for i in live if item_info[i]["owner_team"] == t]
        d = int(rng.choice([1, 2, 3], p=[.45, .40, .15]))
        if live:
            a = str(rng.choice(["answered", "pointed to library", "new prompt written", "escalated"],
                               p=[.28, .58, .04, .10] if d < 3 else [.40, .30, .05, .25]))
        else:
            a = str(rng.choice(["answered", "new prompt written", "escalated"],
                               p=[.65, .17, .18] if d < 3 else [.45, .15, .40]))
        link = None
        if a == "pointed to library":
            link = (own_team_live or live)[int(rng.integers(len(own_team_live or live)))]
        elif a == "new prompt written":
            later = [i for i, info in item_info.items() if info["category"] == cat
                     and w <= info["published_week"] <= w + 4]
            link = later[0] if later else None
        by = None
        if a in ("answered", "pointed to library"):
            team_helpers = [h for h in sorted(helpers) if team_of[h] == t and helper_from[h] <= w
                            and h != r["person_id"]]
            if team_helpers and rng.random() < .62:
                by = team_helpers[int(rng.integers(len(team_helpers)))]
        actions.append(a); linked.append(link); answered_by.append(by); difficulty.append(d)
    qdf["difficulty"], qdf["action_taken"] = difficulty, actions
    qdf["linked_item_id"], qdf["answered_by_person_id"] = linked, answered_by
    qdf["team"] = qdf["person_id"].map(team_of)
    # Rules and allowed use questions fall month on month as people learn what is allowed.
    # A separate stream (also seeded from 42) thins them, so no other table moves.
    keep = RULES_KEEP_BY_MONTH
    thin = np.random.default_rng([SEED, 1]).random(len(qdf))
    month = qdf["week"].map(month_of)
    drop = (qdf["category"] == "Rules and allowed use") & (thin >= month.map(keep))
    qdf = qdf[~drop].reset_index(drop=True)
    qdf["question_id"] = [f"Q{i + 1:05d}" for i in range(len(qdf))]
    # Repeat flag (section 8): same person, same category, within 30 days of their earlier question
    qdf["_d"] = pd.to_datetime(qdf["question_date"])
    prev = qdf.groupby(["person_id", "category"])["_d"].shift(1)
    qdf["repeat_flag"] = ((qdf["_d"] - prev).dt.days <= 30).fillna(False).astype(bool)
    fact_question = qdf[["question_id", "question_date", "person_id", "team", "category", "difficulty",
                         "action_taken", "linked_item_id", "answered_by_person_id", "repeat_flag"]]

    # fact_test_run --------------------------------------------------------
    tr_rows = []
    rid = 0
    for r in item_rows:
        it, pub = r["item_id"], r["published_week"]
        cases = int(rng.integers(5, 13))
        base_in, base_out = int(rng.integers(1400, 4200)), int(rng.integers(350, 1300))
        for v in range(1, r["version"] + 1):
            w = pub if v == 1 else min(N_WEEKS, pub + int(rng.integers(3, 8)))
            latest = v == r["version"]
            for tier in ("standard", "smaller"):
                if tier == "standard":
                    ok = cases if (latest and (it in SMALLER_PASS or rng.random() < .86)) \
                        or (not latest and rng.random() < .6) \
                        else cases - int(rng.integers(1, 3))
                    f_tok = 1.0
                else:
                    if it in SMALLER_PASS:  # half the tokens on every smaller run; the latest version passes
                        ok = cases if latest else cases - int(rng.integers(1, 3))
                        f_tok = SMALLER_PASS[it]
                    else:
                        ok, f_tok = cases - int(rng.integers(1, 4)), float(rng.uniform(.85, 1.05))
                for _ in range(int(rng.integers(1, 3))):  # one or two runs per version and tier
                    rid += 1
                    noise = rng.uniform(.92, 1.08)
                    tr_rows.append(dict(run_id=f"R{rid:04d}", item_id=it, version=v,
                                        run_date=(week_start(w) + pd.Timedelta(days=int(rng.integers(0, 5)))).date(),
                                        model_tier=tier, cases_total=cases, cases_matched=max(0, ok),
                                        tokens_in=int(base_in * f_tok * noise), tokens_out=int(base_out * f_tok * noise)))
    fact_test_run = pd.DataFrame(tr_rows).sort_values(["run_date", "item_id", "version", "model_tier"],
                                                      kind="stable").reset_index(drop=True)
    fact_test_run["run_id"] = [f"R{i + 1:04d}" for i in range(len(fact_test_run))]

    # fact_checkin: the live FRAME-01 form, answered by everyone each month -------
    self_cp_of = {"noseat": 1, "none": 2, "trial_on": 3, "lapsed_trial": 3, "lapsed": 3, "rules": 4,
                  "reminder": 5, "sporadic": 6, "weekly": 7, "power": 8}
    ci_rows = []
    for m, W in CHECKIN_WEEKS.items():
        for p in pid:
            md = mode[p][W]
            t = team_of[p]
            cp = self_cp_of[md]
            if md == "power" and p in helpers and helper_from[p] <= W:
                cp = 9
            if md == "sporadic" and not lib_user[p]:
                cp = 5 if rng.random() < .5 else 6
            if cp > 1:
                if t == "Finance" and md == "reminder":
                    cp = 7 if rng.random() < .78 else int(rng.choice([5, 6]))
                else:
                    r = rng.random()
                    cp = cp + 1 if r < .13 else cp - 1 if r < .21 else cp
                    cp = int(min(9, max(2, cp)))
            ci_rows.append(dict(person_id=p, checkin_month=m, **answers_for(cp, rng), checkpoint_id=cp))
    fact_checkin = pd.DataFrame(ci_rows)

    # Remaining dimensions -------------------------------------------------
    dim_team = pd.DataFrame({"team": list(TEAMS), "headcount": [TEAMS[t]["headcount"] for t in TEAMS]})
    dim_checkpoint = pd.DataFrame(CHECKPOINTS, columns=["checkpoint_id", "checkpoint", "stage", "how_you_tell", "lever"])
    dim_category = pd.DataFrame({"category": CATEGORIES})

    # Week columns are written as the week's week_start date, so they join to dim_week
    def as_week(v):
        return None if v is None or pd.isna(v) else week_start(int(v)).date()
    dim_person["seat_assigned_week"] = dim_person["seat_assigned_week"].map(as_week)
    for c in ("published_week", "status_week"):
        dim_library_item[c] = dim_library_item[c].map(as_week)

    return dict(dim_person=dim_person, dim_team=dim_team, dim_week=dim_week, dim_checkpoint=dim_checkpoint,
                dim_library_item=dim_library_item, dim_category=dim_category,
                fact_question=fact_question, fact_usage_week=fact_usage_week, fact_library_run=fact_library_run,
                fact_library_run_person=fact_library_run_person, fact_test_run=fact_test_run,
                fact_checkin=fact_checkin, fact_training=fact_training)


def form_stage(ans: dict) -> str:
    """The live form's rule: most common stage over q1 to q5, a tie goes to the earlier stage."""
    votes = {"ground": 0, "gate": 0, "air": 0}
    for q, opts in Q_OPTIONS.items():
        for k, text in opts.items():
            if ans[q] == text:
                votes[k] += 1
    best = max(votes.values())
    return next(s for s in ("ground", "gate", "air") if votes[s] == best)


def answers_for(cp: int, rng: np.random.Generator) -> dict:
    """Check-in answers q1 to q5 that the live form would turn into checkpoint cp."""
    if cp == 1:
        return {"q1_access": Q1_NO, "q2_last_use": None, "q3_trigger": None, "q4_used_on": None, "q5_if_gone": None}
    target = STAGE_KEY[STAGE_OF[cp]]
    for _ in range(50):
        ans = {}
        for q, opts in Q_OPTIONS.items():
            keys = list(opts)
            if target in keys and rng.random() < .65:
                k = target
            else:
                k = keys[int(rng.integers(len(keys)))]
            ans[q] = opts[k]
        if form_stage(ans) == target:
            return ans
    # fallback, never reached at seed 42: every answer at the target stage where it exists
    return {q: opts.get(target, opts["gate"]) for q, opts in Q_OPTIONS.items()}


# ---------------------------------------------------------------------------
# Source placement (section 5), computed from the written tables only
# ---------------------------------------------------------------------------
def place(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per person per check-in month: check-in checkpoint, source checkpoint, gap.

    Rules from the top, first match wins, over the trailing eight weeks ending with
    the check-in week (weeks before week 1 count as inactive: nobody had a seat).
    The nine rules together cover everyone, so every row gets a placement.
    """
    wk_no = {pd.Timestamp(d): i + 1 for i, d in enumerate(sorted(pd.to_datetime(t["dim_week"]["week_start"])))}
    people = list(t["dim_person"]["person_id"])
    idx = {p: i for i, p in enumerate(people)}
    seat = pd.to_datetime(t["dim_person"]["seat_assigned_week"]).map(wk_no).to_numpy(dtype=float)

    u = t["fact_usage_week"]
    uw = pd.to_datetime(u["week_start"]).map(wk_no).to_numpy()
    ui = u["person_id"].map(idx).to_numpy()
    active = np.zeros((len(people), N_WEEKS + 1), dtype=bool)
    librun = np.zeros_like(active)
    active[ui, uw] = (u["days_active"] >= 2).to_numpy()
    librun[ui, uw] = (u["runs_via_library"] > 0).to_numpy()

    lp = t["fact_library_run_person"]
    lp_items: dict[tuple[int, int], set] = {}
    for p, d, it in zip(lp["person_id"], pd.to_datetime(lp["week_start"]), lp["item_id"]):
        lp_items.setdefault((idx[p], wk_no[d]), set()).add(it)

    li = t["dim_library_item"]
    owned = {}  # person index -> list of (published_week, end_week or None)
    for o, pub, sw in zip(li["owner_person_id"], pd.to_datetime(li["published_week"]),
                          pd.to_datetime(li["status_week"])):
        owned.setdefault(idx[o], []).append((wk_no[pub], None if pd.isna(sw) else wk_no[sw]))

    q = t["fact_question"]
    qd = pd.to_datetime(q["question_date"])
    answered = {}
    for p, d in zip(q["answered_by_person_id"], qd):
        if isinstance(p, str):
            answered.setdefault(idx[p], []).append(d)
    rules_q = {}
    for p, d, c in zip(q["person_id"], qd, q["category"]):
        if c == "Rules and allowed use":
            rules_q.setdefault(idx[p], []).append(d)

    ci = t["fact_checkin"].set_index(["person_id", "checkin_month"])["checkpoint_id"]
    rows = []
    for m in range(1, 7):
        W = CHECKIN_WEEKS[m]
        win = [w for w in range(W - 7, W + 1) if w >= 1]
        win_start = week_start(W - 7)
        checkin_date = week_start(W) + pd.Timedelta(days=6)
        d30 = checkin_date - pd.Timedelta(days=29)
        wk30 = [w for w in win if week_start(w) >= d30]  # weeks starting inside the 30 days: W-3 to W
        for p in people:
            i = idx[p]
            src = None
            if np.isnan(seat[i]) or seat[i] > W:
                src = 1
            else:
                owns = any(pub <= W and (end is None or W < end) for pub, end in owned.get(i, []))
                n_ans = sum(win_start <= d <= checkin_date for d in answered.get(i, []))
                aw = [bool(active[i, w]) for w in win]
                n_active = sum(aw)
                run = best = 0
                for a in aw:
                    run = run + 1 if a else 0
                    best = max(best, run)
                items = set().union(*[lp_items.get((i, w), set()) for w in win])
                lib_ever = bool(librun[i, 1:W + 1].any())
                ever = int(active[i, 1:W + 1].sum())
                rules_30 = any(d30 <= d <= checkin_date for d in rules_q.get(i, []))
                act_30 = int(sum(active[i, w] for w in wk30))
                if owns and n_ans >= 3:
                    src = 9
                elif n_active >= 6 and len(items) >= 2 and owns:
                    src = 8
                elif best >= 4:
                    src = 7
                elif lib_ever and best < 4:
                    src = 6
                elif rules_30 and act_30 < 2:
                    src = 4
                elif n_active >= 1 and best < 4:
                    src = 5
                elif ever >= 1 and n_active == 0:
                    src = 3
                elif ever == 0:
                    src = 2
                else:  # unreachable: the rules above cover every seat holder
                    raise AssertionError(f"no placement rule matched {p} in month {m}")
            cin = int(ci.loc[(p, m)])
            rows.append(dict(person_id=p, checkin_month=m, checkin_checkpoint_id=cin,
                             source_checkpoint_id=src, gap=cin - src))
    return pd.DataFrame(rows)


def write(tables: dict[str, pd.DataFrame]) -> None:
    OUT.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False, lineterminator="\n")


def main() -> None:
    rng = np.random.default_rng(SEED)
    tables = build(rng)
    tables["fact_placement"] = place(tables)
    write(tables)
    for name, df in tables.items():
        print(f"{name:26s} {len(df):>7,d} rows")


if __name__ == "__main__":
    main()
