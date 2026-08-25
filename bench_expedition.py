"""Bench: whole-career sim over the full loop (delve, fight, camp, surface).

Two batch policies, both cruder than any player on purpose. Both fight in
measure, answer a pause with withdraw below 35% hp else fight_on, camp when
hurt below half with supply in hand, and train on a fixed stat rotation
between expeditions. They differ on when to climb out:

- **ramp** (the plan-0001 policy, kept as the baseline): surface at a
  ramping depth target -- expedition n aims for depth n+1 -- or when hp
  drops below 40% or the light will not cover the climb.
- **satchel** (plan 0003): surface when the satchel is full or hp drops
  below 40%, plus the same light guard. This is the policy the carry limit
  is supposed to make viable: bag full, go home, get paid.

Sims understate the player.

    python bench_expedition.py [--careers 300] [--expeditions 10]
"""

import argparse

import content
import engine

POLICIES = ("ramp", "satchel")
TRAIN_ROTATION = ["edge", "vim", "iron", "nerve", "craft"]


def fresh_save(world_seed):
    cat = content.load_catalog()
    return cat, content.new_save(cat, world_seed)


def _time_to_climb(save, policy):
    d = save["delver"]
    exp = save["expedition"]
    hpm = engine.hp_max(d)
    climb_cost = (exp["depth"] + 2) // 3
    if d["hp"] < 0.4 * hpm or d["light"] <= climb_cost + 1:
        return True
    if policy == "satchel":
        return len(d["salvage"]) >= engine.satchel_cap(d)
    return exp["depth"] >= min(save["wake"]["expeditions"] + 2, content.DEPTH_MAX)


def run_career(world_seed, max_expeditions, policy):
    cat, save = fresh_save(world_seed)
    d = save["delver"]
    depths, banked, uptake = [], [], []
    while save["wake"]["expeditions"] < max_expeditions and d["alive"]:
        # one expedition
        while d["alive"]:
            exp = save["expedition"]
            if exp["pending_site"] and exp["pending_site"].get("enemies"):
                paused, _ = content.start_pending_fight(cat, save, "measure")
                if paused:
                    frac = exp["paused_fight"]["delver"]["hp"] / engine.hp_max(d)
                    content.resume_paused_fight(cat, save,
                                                "withdraw" if frac < 0.35 else "fight_on")
                continue
            if not d["alive"]:
                break
            if exp["active"] and _time_to_climb(save, policy):
                depths.append(exp["depth"])
                carried = list(d["salvage"])
                wanted = save["wake"]["commission"]["item"]
                before = save["wake"]["chits"]
                content.do_surface(cat, save)
                banked.append(save["wake"]["chits"] - before)
                if len(carried) >= 3:
                    uptake.append(any(i["name"] == wanted for i in carried))
                break
            if exp["active"] and d["hp"] < 0.5 * engine.hp_max(d) and d["supply"] > 0:
                content.do_camp(cat, save)
                continue
            content.advance_delve(cat, save, content._evt_rng(save))
        # spend between expeditions
        if d["alive"]:
            for stat in TRAIN_ROTATION:
                cost = content.TRAIN_COST_PER_LEVEL * (d["stats"][stat] + 1)
                if d["stats"][stat] < content.STAT_CAP and save["wake"]["chits"] >= cost:
                    content.do_train(save, stat)
                    break
    return {
        "died": not d["alive"],
        "died_on_day_one": not d["alive"] and save["wake"]["day"] == 1,
        "expeditions": save["wake"]["expeditions"],
        "banked": banked,
        "banked_total": sum(banked),
        "uptake": uptake,
        "max_depth": max(depths) if depths else save["expedition"]["depth"],
        "death_depth": save["expedition"]["depth"] if not d["alive"] else None,
    }


def _median(values):
    if not values:
        return 0
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


UPGRADE_BAR = 20  # a cullet-studded jack, the first upgrade worth wanting


def bench_policy(careers, max_expeditions, policy):
    results = [run_career(seed, max_expeditions, policy) for seed in range(careers)]
    died = [r for r in results if r["died"]]
    day_one = [r for r in results if r["died_on_day_one"]]
    per_expedition = [b for r in results for b in r["banked"]]
    uptake = [u for r in results for u in r["uptake"]]
    print("-- policy: %s --" % policy)
    print("died: %d (%.0f%%)   of those, on day 1: %d (%.0f%% of all careers)"
          % (len(died), 100.0 * len(died) / careers, len(day_one), 100.0 * len(day_one) / careers))
    if died:
        print("mean expeditions before death: %.1f" % (sum(r["expeditions"] for r in died) / len(died)))
        hist = {}
        for r in died:
            hist[r["death_depth"]] = hist.get(r["death_depth"], 0) + 1
        print("death depth histogram: " + "  ".join("d%d:%d" % (k, hist[k]) for k in sorted(hist)))
    print("mean max depth reached: %.1f" % (sum(r["max_depth"] for r in results) / len(results)))
    print("chits banked: mean %.0f per career, median %.0f per career, median %.0f per expedition"
          % (sum(r["banked_total"] for r in results) / len(results),
             _median([r["banked_total"] for r in results]), _median(per_expedition)))
    print("careers banking at least one upgrade (%d chits): %.0f%%"
          % (UPGRADE_BAR, 100.0 * sum(r["banked_total"] >= UPGRADE_BAR for r in results) / careers))
    if uptake:
        print("commission uptake: %.0f%% of surfacings carrying 3+ items filled the order (%d samples)"
              % (100.0 * sum(uptake) / len(uptake), len(uptake)))
    else:
        print("commission uptake: no surfacing carried 3+ items")


def bench(careers, max_expeditions):
    print("careers: %d per policy (cap %d expeditions each)" % (careers, max_expeditions))
    for policy in POLICIES:
        bench_policy(careers, max_expeditions, policy)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--careers", type=int, default=300)
    p.add_argument("--expeditions", type=int, default=10)
    args = p.parse_args()
    bench(args.careers, args.expeditions)
