"""Bench: single-fight outcome distributions by depth and stance.

A fresh stock delver against generated encounters. Fights that pause are
resumed with fight_on, so these are floor numbers: a real player answers
the pause better than "keep at it". Sims understate the player.

    python bench_combat.py [--runs 300]
"""

import argparse

import content
import engine
from test_engine import stock_delver


def bench(runs):
    cat = content.load_catalog()
    print("depth stance    victory retreat  down   avg_rounds avg_hp_lost pause%")
    for depth in range(1, content.DEPTH_MAX + 1):
        for stance in sorted(engine.STANCES):
            wins = flees = downs = rounds = hplost = paused = 0
            for i in range(runs):
                rng = engine.rng_for("bench", depth, stance, i)
                group = content.build_encounter(cat, depth, rng)
                delver = stock_delver()
                state, result = engine.start_fight(delver, group, stance,
                                                   engine.child_seed("benchfight", depth, stance, i))
                if result is None:
                    paused += 1
                    result = engine.resume_fight(state, "fight_on")
                wins += result["outcome"] == "victory"
                flees += result["outcome"] == "retreated"
                downs += result["outcome"] == "down"
                rounds += result["rounds"]
                hplost += delver["hp"] - result["hp"]
            print("  d%-3d %-9s %5.0f%%  %5.0f%%  %5.0f%%   %6.1f     %6.1f    %4.0f%%"
                  % (depth, stance, 100.0 * wins / runs, 100.0 * flees / runs,
                     100.0 * downs / runs, rounds / runs, hplost / runs, 100.0 * paused / runs))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=300)
    bench(p.parse_args().runs)
