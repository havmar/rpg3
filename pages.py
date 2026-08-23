"""UNDERSTORY ui/ page writers. Engine-written pages are rewritten whole on
every save; the DM-authored pages (ui/scene.md, ui/chronicle.md) are never
touched here — `sheet` only commits them. Git is best-effort, never fatal.
"""

import os
import subprocess

import engine

UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")


def _write(name, text):
    os.makedirs(UI_DIR, exist_ok=True)
    with open(os.path.join(UI_DIR, name), "w", encoding="utf-8") as f:
        f.write(text)


def _bar(cur, top, width=20):
    filled = 0 if top <= 0 else max(0, min(width, round(width * cur / top)))
    return "[" + "#" * filled + "-" * (width - filled) + "] %d/%d" % (cur, top)


def write_delver(save):
    d = save["delver"]
    exp = save["expedition"]
    lines = []
    lines.append("=" * 52)
    lines.append("  %s -- %s of Wake%s" % (d["name"], d["background"],
                                           "" if d["alive"] else "  (DECEASED)"))
    lines.append("=" * 52)
    lines.append("")
    lines.append("  HP    " + _bar(d["hp"], engine.hp_max(d)))
    lines.append("  GRIT  " + _bar(d["grit"], engine.grit_max(d), width=8))
    lines.append("  LIGHT " + _bar(d["light"], engine.light_max(d), width=12))
    lines.append("  SUPPLY %d" % d["supply"])
    lines.append("")
    lines.append("  " + "  ".join("%s %d" % (s.upper(), d["stats"][s]) for s in engine.STATS))
    lines.append("")
    lines.append("  attack %+d   guard %d   soak %d" % (engine.attack_bonus(d), engine.guard(d), engine.soak(d)))
    lines.append("  weapon: %s (%s, acc %+d)" % (d["weapon"]["name"], d["weapon"]["dmg"], d["weapon"]["acc"]))
    lines.append("  armor:  %s (guard +%d, soak %d)%s" % (d["armor"]["name"], d["armor"]["guard"],
                                                          d["armor"]["soak"],
                                                          " [heavy]" if d["armor"].get("heavy") else ""))
    lines.append("  knack:  %s -- %s" % (d["knack"], d["knack_text"]))
    lines.append("")
    if exp["active"]:
        lines.append("  ON EXPEDITION -- depth %d" % exp["depth"])
    else:
        lines.append("  IN WAKE -- day %d" % save["wake"]["day"])
    lines.append("  chits banked: %d" % save["wake"]["chits"])
    if d["salvage"]:
        lines.append("  carrying:")
        for item in d["salvage"]:
            lines.append("    - %s (worth %d)" % (item["name"], item["value"]))
    lines.append("")
    _write("delver.txt", "\n".join(lines) + "\n")


def write_map(save):
    exp = save["expedition"]
    lines = ["THE DESCENT", "===========", ""]
    lines.append("  WAKE  (the mouth)" + ("" if exp["active"] else "   <-- you are here"))
    if exp["active"] and not exp["sites"]:
        lines.append("   |   <-- you are here, at the threshold")
    depth_seen = 0
    for site in exp["sites"] if exp["active"] else []:
        depth_seen = max(depth_seen, site["depth"])
        marker = "   <-- you are here" if site["depth"] == exp["depth"] and site is exp["sites"][-1] else ""
        lines.append("   |")
        lines.append("  d%-2d %-12s %s%s" % (site["depth"], "[" + site["kind"] + "]", site["name"], marker))
    if not exp["active"]:
        lines.append("   |")
        lines.append("  (the Understory waits)")
    lines.append("")
    _write("map.txt", "\n".join(lines) + "\n")


def write_history(save):
    lines = ["# The story so far", ""]
    if not save["history"]:
        lines.append("*Nothing yet. Wake watches the mouth and waits.*")
    for entry in save["history"]:
        lines.append("- " + entry)
    lines.append("")
    _write("history.md", "\n".join(lines) + "\n")


def write_fight(save):
    lf = save.get("last_fight")
    if not lf:
        return
    head = "LAST FIGHT -- %s (depth %d) -- %s" % (lf["site"], lf["depth"], lf["outcome"].upper())
    short = [head, "=" * len(head), ""]
    short += engine.fight_summary(lf["events"])
    _write("fight.txt", "\n".join(short) + "\n")
    full = [head, "=" * len(head), "", "(every roll; the short log is fight.txt)", ""]
    full += [("* " if imp else "  ") + text for imp, text in lf["events"]]
    _write("fight_full.txt", "\n".join(full) + "\n")


def write_pages(save):
    write_delver(save)
    write_map(save)
    write_history(save)
    write_fight(save)


def sheet_commit(message):
    """Commit every existing ui/ page. Best-effort; never raises."""
    try:
        root = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(["git", "add", "ui"], cwd=root, capture_output=True, timeout=30)
        done = subprocess.run(["git", "commit", "-m", message], cwd=root,
                              capture_output=True, timeout=30, text=True)
        if done.returncode == 0:
            return "committed: " + message
        return "nothing new to commit"
    except Exception as exc:  # git trouble must never kill the table
        return "git trouble (ignored): %s" % exc
