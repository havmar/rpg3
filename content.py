"""UNDERSTORY content layer: catalogs, validation, encounter/site generation.

Catalogs are versioned JSON under catalogs/. Every load validates; authored
censuses are pinned so silent content drift fails loudly. The engine stays
generic; everything that knows names lives here.
"""

import json
import os

import engine

CATALOG_VERSION = 1
CATALOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogs")

# pinned censuses: change these ON PURPOSE, in the same commit as the content
CENSUS = {
    "backgrounds": 6,
    "enemies": 10,
    "weapons": 6,
    "armors": 4,
    "salvage": 10,
    "strange": 10,
    "sites": 12,
    "marks": 10,
}

ALLOWED_TRAITS = {"swift", "lurker", "brittle", "relentless", "armored", "pack"}
SITE_KINDS = ("encounter", "salvage", "strange", "breather")
DEPTH_MAX = 6
# locality rule: generic templates may not name fixed places
FORBIDDEN_IN_TEMPLATES = ("Wake",)

SITE_KIND_WEIGHTS = [("encounter", 50), ("salvage", 25), ("strange", 15), ("breather", 10)]

_FIELDS = {
    "backgrounds": {"name", "blurb", "priorities", "knack", "knack_text", "weapon", "armor"},
    "enemies": {"name", "blurb", "hp", "atk", "guard", "soak", "dmg", "traits", "menace", "dread", "depth"},
    "weapons": {"name", "dmg", "acc", "value", "blurb"},
    "armors": {"name", "guard", "soak", "value", "heavy", "blurb"},
    "salvage": {"name", "value", "depth", "blurb"},
    "strange": {"name", "effect", "text"},
    "sites": {"name", "kind", "depth", "text"},
    "marks": {"name", "effect", "text"},
}

# a fight this hard leaves a mark; see engine.MARK_EFFECTS for what they do
MARK_BLOW = 6
MARK_HP_FRAC = 3  # ... or coming out at or under a third of your hp


class CatalogError(ValueError):
    pass


def _check_records(records, section):
    fields = _FIELDS[section]
    names = []
    for rec in records:
        missing = fields - set(rec)
        extra = set(rec) - fields
        if missing:
            raise CatalogError("%s %r missing fields %s" % (section, rec.get("name"), sorted(missing)))
        if extra:
            raise CatalogError("%s %r has unknown fields %s" % (section, rec.get("name"), sorted(extra)))
        names.append(rec["name"])
        for key in ("blurb", "text"):
            if key in rec:
                for word in FORBIDDEN_IN_TEMPLATES:
                    if word in rec[key]:
                        raise CatalogError("%s %r violates locality: names %r" % (section, rec["name"], word))
        if "depth" in rec:
            d = rec["depth"]
            if not (isinstance(d, list) and len(d) == 2 and 1 <= d[0] <= d[1] <= DEPTH_MAX):
                raise CatalogError("%s %r has bad depth band %r" % (section, rec["name"], d))
        if "dmg" in rec:
            try:
                engine.max_dice(rec["dmg"])
            except ValueError:
                raise CatalogError("%s %r has bad dice spec %r" % (section, rec["name"], rec["dmg"]))
    if len(set(names)) != len(names):
        raise CatalogError("%s has duplicate names" % section)
    if len(records) != CENSUS[section]:
        raise CatalogError("%s census is %d, pinned %d" % (section, len(records), CENSUS[section]))


def validate_catalog(cat):
    """Full lint of the merged catalog dict. Raises CatalogError."""
    for section in CENSUS:
        _check_records(cat[section], section)
    weapon_names = {w["name"] for w in cat["weapons"]}
    armor_names = {a["name"] for a in cat["armors"]}
    for b in cat["backgrounds"]:
        if sorted(b["priorities"]) != sorted(engine.STATS):
            raise CatalogError("background %r priorities not a permutation of stats" % b["name"])
        if b["weapon"] not in weapon_names or b["armor"] not in armor_names:
            raise CatalogError("background %r references unknown gear" % b["name"])
    for e in cat["enemies"]:
        if not set(e["traits"]) <= ALLOWED_TRAITS:
            raise CatalogError("enemy %r has unknown traits %s" % (e["name"], sorted(set(e["traits"]) - ALLOWED_TRAITS)))
        if e["menace"] < 1:
            raise CatalogError("enemy %r has menace < 1" % e["name"])
    for s in cat["strange"]:
        if s["effect"] not in engine.STRANGE_EFFECTS:
            raise CatalogError("strange %r has unknown effect %r" % (s["name"], s["effect"]))
    for m in cat["marks"]:
        if m["effect"] not in engine.MARK_EFFECTS:
            raise CatalogError("mark %r has unknown effect %r" % (m["name"], m["effect"]))
    for site in cat["sites"]:
        if site["kind"] not in SITE_KINDS:
            raise CatalogError("site %r has unknown kind %r" % (site["name"], site["kind"]))
    for kind in SITE_KINDS:
        for depth in range(1, DEPTH_MAX + 1):
            if not [s for s in cat["sites"] if s["kind"] == kind and s["depth"][0] <= depth <= s["depth"][1]]:
                raise CatalogError("no %s site template covers depth %d" % (kind, depth))
    for kind, section in (("encounter", "enemies"), ("salvage", "salvage")):
        for depth in range(1, DEPTH_MAX + 1):
            if not [r for r in cat[section] if r["depth"][0] <= depth <= r["depth"][1]]:
                raise CatalogError("no %s entry covers depth %d" % (section, depth))
    return cat


def load_catalog():
    """Load and validate all catalog files into one dict."""
    cat = {}
    for fname, sections in (
        ("backgrounds.json", ["backgrounds"]),
        ("enemies.json", ["enemies"]),
        ("gear.json", ["weapons", "armors"]),
        ("salvage.json", ["salvage"]),
        ("strange.json", ["strange"]),
        ("sites.json", ["sites"]),
        ("marks.json", ["marks"]),
    ):
        with open(os.path.join(CATALOG_DIR, fname), "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != CATALOG_VERSION:
            raise CatalogError("%s: version %r, expected %d" % (fname, data.get("version"), CATALOG_VERSION))
        for section in sections:
            cat[section] = data[section]
    return validate_catalog(cat)


def by_name(records, name):
    for rec in records:
        if rec["name"] == name:
            return rec
    raise KeyError(name)


# ------------------------------------------------------------- generators

def _eligible(records, depth):
    return [r for r in records if r["depth"][0] <= depth <= r["depth"][1]]


def build_encounter(cat, depth, rng):
    """Pick an enemy group for this depth. Returns list of enemy spec dicts."""
    pool = _eligible(cat["enemies"], depth)
    budget = max(1, 1 + depth + rng.randint(-1, 1))
    group = []
    while True:
        affordable = [e for e in pool if e["menace"] <= budget]
        if not affordable:
            break
        pick = rng.choice(affordable)
        count = (2 + (1 if rng.random() < 0.5 else 0)) if "pack" in pick["traits"] else 1
        count = min(count, max(1, budget // pick["menace"]))
        for _ in range(count):
            group.append(pick)
            budget -= pick["menace"]
    if not group:
        group.append(min(pool, key=lambda e: (e["menace"], e["name"])))
    return group


def roll_salvage(cat, depth, rng):
    return rng.choice(_eligible(cat["salvage"], depth))


def generate_site(cat, depth, rng):
    """One site at this depth: template + payload. Deterministic per rng."""
    total = sum(w for _, w in SITE_KIND_WEIGHTS)
    pick = rng.randint(1, total)
    for kind, weight in SITE_KIND_WEIGHTS:
        pick -= weight
        if pick <= 0:
            break
    template = rng.choice([s for s in cat["sites"] if s["kind"] == kind
                           and s["depth"][0] <= depth <= s["depth"][1]])
    site = {"depth": depth, "kind": kind, "name": template["name"], "text": template["text"]}
    if kind == "encounter":
        site["enemies"] = [e["name"] for e in build_encounter(cat, depth, rng)]
    elif kind == "salvage":
        items = [roll_salvage(cat, depth, rng)]
        if rng.random() < 0.4:
            items.append(roll_salvage(cat, depth, rng))
        site["salvage"] = [i["name"] for i in items]
    elif kind == "strange":
        strange = rng.choice(cat["strange"])
        site["strange"] = strange["name"]
        site["effect"] = strange["effect"]
        site["strange_text"] = strange["text"]
        if strange["effect"] in ("found_cache", "murmur_market"):
            site["salvage"] = [roll_salvage(cat, depth, rng)["name"]]
    return site


BASE_ARRAY = [3, 3, 2, 2, 2]


def delver_candidates(cat, name, world_seed):
    """Three seeded delver candidates for a name. Deterministic."""
    rng = engine.rng_for(world_seed, "delver", name)
    picks = rng.sample(sorted(cat["backgrounds"], key=lambda b: b["name"]), 3)
    candidates = []
    for bg in picks:
        stats = {}
        for stat, val in zip(bg["priorities"], BASE_ARRAY):
            stats[stat] = val
        bonus = rng.choice(sorted(engine.STATS))
        stats[bonus] += 1
        candidates.append({
            "name": name,
            "background": bg["name"],
            "blurb": bg["blurb"],
            "knack": bg["knack"],
            "knack_text": bg["knack_text"],
            "stats": stats,
            "weapon": dict(by_name(cat["weapons"], bg["weapon"])),
            "armor": dict(by_name(cat["armors"], bg["armor"])),
        })
    return candidates


# ---------------------------------------------------------- expedition flow
# Game-flow rules that need the catalogs live here so session.py stays a
# thin driver and engine.py stays generic.

SUPPLY_START = 3
TRAIN_COST_PER_LEVEL = 15
STAT_CAP = 6


def new_delver(candidate):
    d = dict(candidate)
    d["marks"] = []  # before the derived readers: they all consult it
    d["hp"] = engine.hp_max(d)
    d["grit"] = engine.grit_max(d)
    d["light"] = engine.light_max(d)
    d["supply"] = SUPPLY_START
    d["salvage"] = []
    d["alive"] = True
    return d


def _darkness(delver):
    return delver["light"] <= 0


def advance_delve(cat, save, rng):
    """One step deeper. Returns (site, lines). Mutates save."""
    delver = save["delver"]
    exp = save["expedition"]
    if exp["paused_fight"] or (exp["pending_site"] and exp["pending_site"].get("enemies")):
        raise ValueError("there is a fight in front of you; resolve it first")
    lines = []
    if not exp["active"]:
        exp["active"] = True
        exp["depth"] = 0
        exp["sites"] = []
        lines.append("You go down through the great mouth. The expedition begins.")
    if exp["depth"] >= DEPTH_MAX:
        lines.append("Below this the floor is one sealed pane, fathoms thick. "
                     "The Understory goes deeper; you, today, do not.")
    else:
        exp["depth"] += 1
    if exp.get("free_delve"):
        exp["free_delve"] = False
        cost = 0
        lines.append("The old stairs hold: no light spent.")
    else:
        cost = 1
    if engine.has_mark(delver, "light_leak"):
        cost += 1
        lines.append("Lamp-shy: the flame takes an extra measure on the way down.")
    delver["light"] = max(0, delver["light"] - cost)
    if _darkness(delver):
        lines.append("The lamp is dry. You move in the dark now.")
    site = generate_site(cat, exp["depth"], rng)
    exp["sites"].append({"depth": site["depth"], "kind": site["kind"], "name": site["name"]})
    if site["kind"] == "encounter":
        exp["pending_site"] = site
        lines.append("Something is here: " + ", ".join(site["enemies"]) + ".")
    elif site["kind"] == "salvage":
        for name in site["salvage"]:
            item = by_name(cat["salvage"], name)
            delver["salvage"].append({"name": item["name"], "value": item["value"]})
            lines.append("Salvage taken: %s (worth %d)." % (item["name"], item["value"]))
        exp["pending_site"] = None
    elif site["kind"] == "strange":
        lines.extend(engine.apply_strange(delver, exp, site["effect"], rng))
        for name in site.get("salvage", []):
            item = by_name(cat["salvage"], name)
            delver["salvage"].append({"name": item["name"], "value": item["value"]})
            lines.append("Salvage taken: %s (worth %d)." % (item["name"], item["value"]))
        exp["pending_site"] = None
    else:  # breather
        if engine.has_mark(delver, "breather_numb"):
            lines.append("A quiet room. You sit in it and get nothing back from it.")
        elif delver["grit"] < engine.grit_max(delver):
            delver["grit"] += 1
            lines.append("A moment of quiet; you gather yourself: +1 grit.")
        exp["pending_site"] = None
    return site, lines


def start_pending_fight(cat, save, stance):
    """Resolve (or pause) the pending encounter. Returns (paused, lines)."""
    exp = save["expedition"]
    site = exp["pending_site"]
    if not site or not site.get("enemies"):
        raise ValueError("no fight is pending")
    specs = [by_name(cat["enemies"], n) for n in site["enemies"]]
    seed = engine.child_seed(save["world_seed"], "fight", save["counter"])
    save["counter"] += 1
    state, result = engine.start_fight(save["delver"], specs, stance,
                                       seed, darkness=_darkness(save["delver"]))
    if result is None:
        exp["paused_fight"] = state
        return True, engine.fight_summary(state["events"])
    return False, apply_fight_result(cat, save, result)


def resume_paused_fight(cat, save, choice):
    exp = save["expedition"]
    if not exp["paused_fight"]:
        raise ValueError("no paused fight")
    result = engine.resume_fight(exp["paused_fight"], choice)
    exp["paused_fight"] = None
    return apply_fight_result(cat, save, result)


def apply_fight_result(cat, save, result):
    delver = save["delver"]
    exp = save["expedition"]
    site = exp["pending_site"]
    delver["hp"] = result["hp"]
    delver["grit"] = result["grit"]
    delver["light"] = result["light"]
    save["last_fight"] = {"outcome": result["outcome"], "site": site["name"],
                          "depth": exp["depth"], "events": result["events"]}
    lines = engine.fight_summary(result["events"])
    if result["outcome"] == "victory":
        exp["pending_site"] = None
        scrap = 2 * result["menace_defeated"]
        delver["salvage"].append({"name": "scrap glass and fittings", "value": scrap})
        lines.append("You strip the field: scrap worth %d." % scrap)
        rng = _evt_rng(save)
        if rng.random() < 0.7:
            item = roll_salvage(cat, exp["depth"], rng)
            delver["salvage"].append({"name": item["name"], "value": item["value"]})
            lines.append("Among the wreckage: %s (worth %d)." % (item["name"], item["value"]))
        save["history"].append("Day %d, depth %d: cleared %s (%s)."
                               % (save["wake"]["day"], exp["depth"], site["name"],
                                  ", ".join(site["enemies"])))
    elif result["outcome"] == "retreated":
        exp["pending_site"] = None
        exp["depth"] = max(0, exp["depth"] - 1)
        lines.append("You fall back to the previous gallery (depth %d)." % exp["depth"])
        save["history"].append("Day %d: retreated from %s at depth %d."
                               % (save["wake"]["day"], site["name"], exp["depth"] + 1))
    else:  # down
        delver["alive"] = False
        lines.append("The expedition ends here. The Understory keeps what it takes.")
        save["history"].append("Day %d: %s went down at depth %d, in %s. The Ledger remembers."
                               % (save["wake"]["day"], delver["name"], exp["depth"], site["name"]))
    lines.extend(gain_mark(cat, save, result))
    return lines


def gain_mark(cat, save, result):
    """A fight that nearly had you leaves something behind. Returns lines."""
    delver = save["delver"]
    if result["outcome"] not in ("victory", "retreated"):
        return []
    hard = (result["worst_blow"] >= MARK_BLOW
            or result["hp"] * MARK_HP_FRAC <= engine.hp_max(delver))
    if not hard or len(delver["marks"]) >= engine.MARK_CAP:
        return []
    held = {m["name"] for m in delver["marks"]}
    pool = [m for m in cat["marks"] if m["name"] not in held]
    rng = engine.rng_for(save["world_seed"], "mark", save["counter"])
    save["counter"] += 1
    mark = dict(rng.choice(pool))
    delver["marks"].append(mark)
    delver["hp"] = min(delver["hp"], engine.hp_max(delver))
    return ["You come away with something: %s -- %s" % (mark["name"], mark["text"])]


def do_camp(cat, save):
    delver = save["delver"]
    exp = save["expedition"]
    if not exp["active"]:
        raise ValueError("you camp in the deep, not in Wake")
    if exp["paused_fight"] or (exp["pending_site"] and exp["pending_site"].get("enemies")):
        raise ValueError("you cannot camp with something watching you; resolve the fight")
    if delver["supply"] < 1:
        raise ValueError("no supply left to camp on")
    rng = _evt_rng(save)
    delver["supply"] -= 1
    delver["light"] = max(0, delver["light"] - 1)
    heal = engine.camp_heal(delver, rng)
    delver["hp"] = min(engine.hp_max(delver), delver["hp"] + heal)
    lines = ["You camp cold behind a shard-wall: +%d hp, grit restored, -1 supply, -1 light." % heal]
    if delver["marks"]:
        mark = delver["marks"].pop()
        lines.append("Dressed and splinted by lamplight: %s is behind you." % mark["name"])
    delver["grit"] = engine.grit_max(delver)
    return lines


def do_surface(cat, save):
    delver = save["delver"]
    exp = save["expedition"]
    if not exp["active"]:
        raise ValueError("you are already in Wake")
    if exp["paused_fight"] or (exp["pending_site"] and exp["pending_site"].get("enemies")):
        raise ValueError("you cannot surface mid-fight; resolve it (or withdraw at the pause)")
    rng = _evt_rng(save)
    lines = []
    cost = (exp["depth"] + 2) // 3
    short = max(0, cost - delver["light"])
    delver["light"] = max(0, delver["light"] - cost)
    if short:
        dmg = sum(engine.roll_dice("1d6", rng) for _ in range(short))
        delver["hp"] = max(1, delver["hp"] - dmg)
        lines.append("The climb outruns the lamp: %d hp lost to the dark on the way up." % dmg)
    banked = 0
    bonus = 0
    for item in delver["salvage"]:
        banked += item["value"]
        if delver["knack"] == "glasspicker" and item["name"] != "scrap glass and fittings":
            bonus += 1
    banked += bonus
    delver["salvage"] = []
    save["wake"]["chits"] += banked
    save["wake"]["day"] += 1
    save["wake"]["expeditions"] += 1
    reached = exp["depth"]
    exp.update({"active": False, "depth": 0, "pending_site": None, "paused_fight": None,
                "free_delve": False})
    delver["hp"] = engine.hp_max(delver)
    delver["grit"] = engine.grit_max(delver)
    delver["light"] = engine.light_max(delver)
    delver["supply"] = SUPPLY_START
    if delver["marks"]:
        lines.append("A night above ground and a surgeon's hour: %s, all of it gone."
                     % ", ".join(m["name"] for m in delver["marks"]))
        delver["marks"] = []
    lines.append("You surface into the red light of the Ember. Banked %d chits (total %d)."
                 % (banked, save["wake"]["chits"]))
    lines.append("A day of rest in Wake: healed, refit, ready.")
    save["history"].append("Day %d: surfaced from depth %d, banked %d chits."
                           % (save["wake"]["day"], reached, banked))
    return lines


def do_train(save, stat):
    if stat not in engine.STATS:
        raise ValueError("no such stat; stats: %s" % ", ".join(engine.STATS))
    if save["expedition"]["active"]:
        raise ValueError("training happens in Wake")
    delver = save["delver"]
    new_val = delver["stats"][stat] + 1
    if new_val > STAT_CAP:
        raise ValueError("%s is at the cap (%d)" % (stat, STAT_CAP))
    cost = TRAIN_COST_PER_LEVEL * new_val
    if save["wake"]["chits"] < cost:
        raise ValueError("training %s to %d costs %d chits; you have %d"
                         % (stat, new_val, cost, save["wake"]["chits"]))
    save["wake"]["chits"] -= cost
    delver["stats"][stat] = new_val
    if stat == "vim":
        delver["hp"] = engine.hp_max(delver)
    if stat == "nerve":
        delver["grit"] = engine.grit_max(delver)
    save["history"].append("Day %d: trained %s to %d (%d chits)."
                           % (save["wake"]["day"], stat, new_val, cost))
    return ["%s rises to %d (-%d chits, %d left)." % (stat, new_val, cost, save["wake"]["chits"])]


def do_buy(cat, save, item_name):
    if save["expedition"]["active"]:
        raise ValueError("the outfitters are in Wake")
    delver = save["delver"]
    for section, slot in (("weapons", "weapon"), ("armors", "armor")):
        for rec in cat[section]:
            if rec["name"] == item_name:
                if save["wake"]["chits"] < rec["value"]:
                    raise ValueError("%s costs %d chits; you have %d"
                                     % (item_name, rec["value"], save["wake"]["chits"]))
                save["wake"]["chits"] -= rec["value"]
                delver[slot] = dict(rec)
                save["history"].append("Day %d: bought %s (%d chits)."
                                       % (save["wake"]["day"], item_name, rec["value"]))
                return ["%s is yours (-%d chits, %d left)." % (item_name, rec["value"], save["wake"]["chits"])]
    raise ValueError("no such item in the market: %r" % item_name)


def _evt_rng(save):
    rng = engine.rng_for(save["world_seed"], "evt", save["counter"])
    save["counter"] += 1
    return rng


# ------------------------------------------------------------------ eyeball

def main():
    import argparse
    p = argparse.ArgumentParser(description="content eyeball check: sample sites per depth")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--per-depth", type=int, default=3)
    args = p.parse_args()
    cat = load_catalog()
    print("catalog ok:", ", ".join("%s=%d" % (k, len(cat[k])) for k in sorted(CENSUS)))
    for depth in range(1, DEPTH_MAX + 1):
        for i in range(args.per_depth):
            rng = engine.rng_for(args.seed, "eyeball", depth, i)
            site = generate_site(cat, depth, rng)
            extra = site.get("enemies") or site.get("salvage") or site.get("strange") or ""
            print("d%d %-12s %-22s %s" % (depth, site["kind"], site["name"], extra))


if __name__ == "__main__":
    main()
