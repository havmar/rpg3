"""UNDERSTORY session driver: a thin CLI over engine/content/pages.

All campaign state lives in save.json (untracked) between invocations. This
driver adds no game logic of its own; rules live in engine.py and
content.py, and the numbers live in the catalogs.

    python session.py new Ashline            # meet three candidates
    python session.py new Ashline --pick 2   # take one; the save begins
    python session.py delve                  # one step deeper
    python session.py fight --stance press   # resolve the pending fight
    python session.py fight --resume surge   # answer a mid-fight pause
    python session.py camp | surface | status | market | log
    python session.py train edge | buy "salvage axe"
    python session.py sheet -m "message"     # rewrite + commit ui/ pages
"""

import argparse
import json
import os
import sys

import content
import engine
import pages

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json")


def load_save():
    if not os.path.exists(SAVE_PATH):
        raise SystemExit("no save.json -- start with: python session.py new <Name>")
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        save = json.load(f)
    if save.get("version") != engine.SAVE_VERSION:
        raise SystemExit("save version %r != engine version %d -- no backcompat, ever: "
                         "delete save.json and raise a new delver"
                         % (save.get("version"), engine.SAVE_VERSION))
    return save


def write_save(save):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(save, f, indent=1)
    pages.write_pages(save)


def say(lines):
    for line in lines:
        print(line)


def require_alive(save):
    if not save["delver"]["alive"]:
        raise SystemExit("%s is dead. The Ledger remembers; the save is done. "
                         "Start anew: delete save.json, then session.py new <Name>"
                         % save["delver"]["name"])


# ------------------------------------------------------------------ commands

def cmd_new(cat, args):
    if os.path.exists(SAVE_PATH) and not args.force:
        raise SystemExit("save.json already exists; pass --force to abandon it")
    world_seed = args.seed if args.seed is not None else engine.child_seed(os.urandom(8).hex())
    candidates = content.delver_candidates(cat, args.name, world_seed)
    if args.pick is None:
        print("Three came to the mouth answering to %r (world seed %d):\n" % (args.name, world_seed))
        for i, c in enumerate(candidates, 1):
            stats = "  ".join("%s %d" % (s.upper(), c["stats"][s]) for s in engine.STATS)
            print("  %d) the %s -- %s" % (i, c["background"], c["blurb"]))
            print("     %s" % stats)
            print("     %s / %s; knack: %s" % (c["weapon"]["name"], c["armor"]["name"], c["knack_text"]))
            print()
        print("choose with: python session.py new %s --seed %d --pick N" % (args.name, world_seed))
        return
    candidate = candidates[args.pick - 1]
    save = {
        "version": engine.SAVE_VERSION,
        "world_seed": world_seed,
        "counter": 0,
        "delver": content.new_delver(candidate),
        "expedition": {"active": False, "depth": 0, "sites": [], "pending_site": None,
                       "paused_fight": None, "free_delve": False},
        "wake": {"chits": 0, "day": 1, "expeditions": 0},
        "history": ["Day 1: %s, %s, signed the delvers' book in Wake."
                    % (candidate["name"], candidate["background"])],
        "last_fight": None,
    }
    write_save(save)
    print("%s the %s stands at the mouth. (save.json written)"
          % (candidate["name"], candidate["background"]))


def cmd_status(cat, args):
    save = load_save()
    d = save["delver"]
    exp = save["expedition"]
    where = ("depth %d" % exp["depth"]) if exp["active"] else ("Wake, day %d" % save["wake"]["day"])
    print("%s the %s -- %s%s" % (d["name"], d["background"], where,
                                 "" if d["alive"] else " -- DEAD"))
    print("hp %d/%d  grit %d/%d  light %d  supply %d  chits %d"
          % (d["hp"], engine.hp_max(d), d["grit"], engine.grit_max(d),
             d["light"], d["supply"], save["wake"]["chits"]))
    if d["salvage"]:
        print("carrying: " + ", ".join("%s(%d)" % (i["name"], i["value"]) for i in d["salvage"]))
    for mark in d["marks"]:
        print("mark: %s -- %s" % (mark["name"], mark["text"]))
    if exp["paused_fight"]:
        print("A FIGHT HANGS PAUSED. Options:")
        for key, desc in sorted(engine.pause_options(exp["paused_fight"]).items()):
            print("  --resume %-9s %s" % (key, desc))
    elif exp["pending_site"] and exp["pending_site"].get("enemies"):
        print("A fight is pending at %s: %s" % (exp["pending_site"]["name"],
                                                ", ".join(exp["pending_site"]["enemies"])))


def cmd_delve(cat, args):
    save = load_save()
    require_alive(save)
    rng = content._evt_rng(save)
    site, lines = content.advance_delve(cat, save, rng)
    print("DEPTH %d -- %s [%s]" % (site["depth"], site["name"], site["kind"]))
    print(site["text"])
    if site["kind"] == "strange":
        print(site["strange_text"])
    say(lines)
    write_save(save)


def cmd_fight(cat, args):
    save = load_save()
    require_alive(save)
    if args.resume:
        say(content.resume_paused_fight(cat, save, args.resume))
    else:
        paused, lines = content.start_pending_fight(cat, save, args.stance)
        say(lines)
        if paused:
            print("")
            print("THE FIGHT PAUSES. Choose (session.py fight --resume <option>):")
            for key, desc in sorted(engine.pause_options(save["expedition"]["paused_fight"]).items()):
                print("  %-9s %s" % (key, desc))
    write_save(save)


def cmd_camp(cat, args):
    save = load_save()
    require_alive(save)
    say(content.do_camp(cat, save))
    write_save(save)


def cmd_surface(cat, args):
    save = load_save()
    require_alive(save)
    say(content.do_surface(cat, save))
    write_save(save)


def cmd_train(cat, args):
    save = load_save()
    require_alive(save)
    say(content.do_train(save, args.stat))
    write_save(save)


def cmd_buy(cat, args):
    save = load_save()
    require_alive(save)
    say(content.do_buy(cat, save, args.item))
    write_save(save)


def cmd_market(cat, args):
    save = load_save()
    print("THE OUTFITTERS' ROW, WAKE (chits: %d)" % save["wake"]["chits"])
    for w in cat["weapons"]:
        print("  %-22s %3d chits  (%s, acc %+d)  %s" % (w["name"], w["value"], w["dmg"], w["acc"], w["blurb"]))
    for a in cat["armors"]:
        print("  %-22s %3d chits  (guard +%d, soak %d%s)  %s"
              % (a["name"], a["value"], a["guard"], a["soak"], ", heavy" if a["heavy"] else "", a["blurb"]))
    print("training: raising a stat to N costs %d*N chits (cap %d)"
          % (content.TRAIN_COST_PER_LEVEL, content.STAT_CAP))


def cmd_log(cat, args):
    save = load_save()
    lf = save.get("last_fight")
    if not lf:
        print("no fight on record")
        return
    for imp, text, beat in lf["events"]:
        print(("* " if imp else "  ") + text + (("  [%s]" % beat) if beat else ""))


def cmd_sheet(cat, args):
    save = load_save()
    pages.write_pages(save)
    print(pages.sheet_commit(args.message or "table: %s, day %d"
                             % (save["delver"]["name"], save["wake"]["day"])))


def main(argv=None):
    cat = content.load_catalog()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="raise a delver (twice: once to see candidates, once with --pick)")
    s.add_argument("name")
    s.add_argument("--seed", type=int, default=None, help="world seed; keep it when picking")
    s.add_argument("--pick", type=int, choices=[1, 2, 3], default=None)
    s.add_argument("--force", action="store_true", help="abandon an existing save.json")
    s.set_defaults(fn=cmd_new)

    for name, fn, msg in (("status", cmd_status, "where things stand"),
                          ("delve", cmd_delve, "one step deeper (costs 1 light)"),
                          ("camp", cmd_camp, "heal and steady (1 supply, 1 light)"),
                          ("surface", cmd_surface, "climb out, bank salvage, rest in Wake"),
                          ("market", cmd_market, "what Wake sells"),
                          ("log", cmd_log, "print the full last-fight log")):
        s = sub.add_parser(name, help=msg)
        s.set_defaults(fn=fn)

    s = sub.add_parser("fight", help="resolve the pending encounter (autocombat, one pause)")
    s.add_argument("--stance", default="measure", choices=sorted(engine.STANCES))
    s.add_argument("--resume", default=None, help="answer a paused fight with an option key")
    s.set_defaults(fn=cmd_fight)

    s = sub.add_parser("train", help="raise a stat in Wake (costs chits)")
    s.add_argument("stat", choices=engine.STATS)
    s.set_defaults(fn=cmd_train)

    s = sub.add_parser("buy", help="buy gear in Wake")
    s.add_argument("item")
    s.set_defaults(fn=cmd_buy)

    s = sub.add_parser("sheet", help="rewrite ui/ pages and commit them (one commit per message)")
    s.add_argument("-m", "--message", default=None)
    s.set_defaults(fn=cmd_sheet)

    args = p.parse_args(argv)
    try:
        args.fn(cat, args)
    except ValueError as exc:
        raise SystemExit("cannot: %s" % exc)


if __name__ == "__main__":
    main()
