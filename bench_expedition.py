"""Bench: whole-career sim over the full loop (delve, fight, camp, surface).

Batch policy (cruder than any player, on purpose): fight in measure, answer
a pause with withdraw below 35% hp else fight_on, camp when hurt below half
with supply in hand, surface at a ramping depth target (expedition n aims
for depth n+1) or when hp < 40% or light runs low, train on a fixed stat
rotation between expeditions. Sims understate the player.

    python bench_expedition.py [--careers 300] [--expeditions 10]
"""

import argparse

import content
import engine


def fresh_save(world_seed):
    cat = content.load_catalog()
    candidate = content.delver_candidates(cat, "Benchfell", world_seed)[0]
    return cat, {
        "version": engine.SAVE_VERSION, "world_seed": world_seed, "counter": 0,
        "delver": content.new_delver(candidate),
        "expedition": {"active": False, "depth": 0, "sites": [], "pending_site": None,
                       "paused_fight": None, "free_delve": False},
        "wake": {"chits": 0, "day": 1, "expeditions": 0},
        "history": [], "last_fight": None,
    }


TRAIN_ROTATION = ["edge", "vim", "iron", "nerve", "craft"]


def run_career(world_seed, max_expeditions):
    cat, save = fresh_save(world_seed)
    d = save["delver"]
    depths = []
    while save["wake"]["expeditions"] < max_expeditions and d["alive"]:
        # one expedition
        while d["alive"]:
            hpm = engine.hp_max(d)
            exp = save["expedition"]
            pending = exp["pending_site"] and exp["pending_site"].get("enemies")
            if pending:
                paused, _ = content.start_pending_fight(cat, save, "measure")
                if paused:
                    frac = save["expedition"]["paused_fight"]["delver"]["hp"] / hpm
                    content.resume_paused_fight(cat, save,
                                                "withdraw" if frac < 0.35 else "fight_on")
                continue
            if not d["alive"]:
                break
            climb_cost = (exp["depth"] + 2) // 3
            target = min(save["wake"]["expeditions"] + 2, content.DEPTH_MAX)
            if exp["active"] and (exp["depth"] >= target
                                  or d["hp"] < 0.4 * hpm or d["light"] <= climb_cost + 1):
                depths.append(exp["depth"])
                content.do_surface(cat, save)
                break
            if exp["active"] and d["hp"] < 0.5 * hpm and d["supply"] > 0:
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
        "expeditions": save["wake"]["expeditions"],
        "chits_banked_total": sum(int(h.split("banked ")[1].split(" chits")[0])
                                  for h in save["history"] if "banked" in h),
        "max_depth": max(depths) if depths else save["expedition"]["depth"],
        "death_depth": save["expedition"]["depth"] if not d["alive"] else None,
    }


def bench(careers, max_expeditions):
    results = [run_career(seed, max_expeditions) for seed in range(careers)]
    died = [r for r in results if r["died"]]
    survived = [r for r in results if not r["died"]]
    print("careers: %d (cap %d expeditions each)" % (careers, max_expeditions))
    print("died: %d (%.0f%%)   survived to cap: %d" % (len(died), 100.0 * len(died) / careers, len(survived)))
    if died:
        print("mean expeditions before death: %.1f" % (sum(r["expeditions"] for r in died) / len(died)))
        hist = {}
        for r in died:
            hist[r["death_depth"]] = hist.get(r["death_depth"], 0) + 1
        print("death depth histogram: " + "  ".join("d%d:%d" % (k, hist[k]) for k in sorted(hist)))
    print("mean max depth reached: %.1f" % (sum(r["max_depth"] for r in results) / len(results)))
    print("mean chits banked per career: %.0f" % (sum(r["chits_banked_total"] for r in results) / len(results)))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--careers", type=int, default=300)
    p.add_argument("--expeditions", type=int, default=10)
    args = p.parse_args()
    bench(args.careers, args.expeditions)
