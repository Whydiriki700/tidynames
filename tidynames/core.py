"""Rename planning: nothing on disk changes until apply_plan runs.

A plan is a list of {old, new} names inside one folder. Collisions (two
files wanting the same new name, or a target that already exists and is
not itself being renamed away) are reported and those entries are dropped
from the plan, never forced.
"""
import json
import os
import re
import unicodedata
from datetime import datetime

UNDO_NAME = "tidynames-undo.json"


def slugify(stem):
    text = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "file"


def build_plan(folder, slug=False, prefix="", date_prefix=False, number=False,
               start=1, replace=None):
    names = sorted(n for n in os.listdir(folder)
                   if os.path.isfile(os.path.join(folder, n)) and n != UNDO_NAME)
    plan = []
    for idx, name in enumerate(names):
        stem, ext = os.path.splitext(name)
        new_stem = stem
        if replace:
            new_stem = new_stem.replace(replace[0], replace[1])
        if slug:
            new_stem = slugify(new_stem)
        head = ""
        if date_prefix:
            stamp = os.path.getmtime(os.path.join(folder, name))
            head += datetime.fromtimestamp(stamp).strftime("%Y%m%d") + "-"
        if prefix:
            head += prefix
        if number:
            head += f"{start + idx:03d}-"
        new_name = head + new_stem + ext.lower() if slug else head + new_stem + ext
        if new_name != name:
            plan.append({"old": name, "new": new_name})
    return plan


def find_collisions(folder, plan):
    targets = {}
    collisions = []
    planned_away = {entry["old"] for entry in plan}
    for entry in plan:
        target = entry["new"]
        if target in targets:
            collisions.append(entry)
            continue
        targets[target] = entry
        if os.path.exists(os.path.join(folder, target)) and target not in planned_away:
            collisions.append(entry)
    return collisions


def apply_plan(folder, plan):
    done = []
    for entry in plan:
        os.rename(os.path.join(folder, entry["old"]),
                  os.path.join(folder, entry["new"]))
        done.append(entry)
    if done:
        with open(os.path.join(folder, UNDO_NAME), "w", encoding="utf-8") as handle:
            json.dump(done, handle, indent=2)
    return done


def undo(folder):
    path = os.path.join(folder, UNDO_NAME)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        entries = json.load(handle)
    restored = []
    for entry in reversed(entries):
        os.rename(os.path.join(folder, entry["new"]),
                  os.path.join(folder, entry["old"]))
        restored.append(entry)
    os.remove(path)
    return restored
