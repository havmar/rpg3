"""Contract suite for engine.py: the model, not the sessions that built it."""

import json
import random
import unittest

import engine


def stock_delver(**over):
    d = {
        "name": "Testfell",
        "stats": {"edge": 2, "iron": 2, "vim": 2, "nerve": 2, "craft": 2},
        "knack": "none",
        "weapon": {"name": "pick-hammer", "dmg": "1d8", "acc": 0},
        "armor": {"name": "quilted delver's coat", "guard": 1, "soak": 1},
        "hp": 14, "grit": 3,
        "light": 10, "supply": 3, "salvage": [], "alive": True,
    }
    d.update(over)
    return d


HOUND = {"name": "glasshound", "hp": 6, "atk": 3, "guard": 12, "soak": 0,
         "dmg": "1d6", "traits": ["swift"], "menace": 2, "dread": 0}
BRUTE = {"name": "glazier's remnant", "hp": 18, "atk": 5, "guard": 13, "soak": 2,
         "dmg": "2d6", "traits": ["relentless"], "menace": 5, "dread": 2}


def run_to_end(delver, enemies, stance, seed, choice="fight_on"):
    state, result = engine.start_fight(delver, enemies, stance, seed)
    if result is None:
        result = engine.resume_fight(state, choice)
    return result


class TestSeedsAndDice(unittest.TestCase):
    def test_child_seed_stable_and_distinct(self):
        self.assertEqual(engine.child_seed("a", 1), engine.child_seed("a", 1))
        self.assertNotEqual(engine.child_seed("a", 1), engine.child_seed("a", 2))
        self.assertNotEqual(engine.child_seed("a", 1), engine.child_seed("a/1"))

    def test_dice_bounds(self):
        rng = random.Random(7)
        for _ in range(200):
            self.assertTrue(3 <= engine.roll_dice("2d6+1", rng) <= 13)
        self.assertEqual(engine.max_dice("2d6+1"), 13)
        with self.assertRaises(ValueError):
            engine.roll_dice("d6", rng)
        with self.assertRaises(ValueError):
            engine.max_dice("2d6+1d4")

    def test_rng_for_deterministic(self):
        self.assertEqual(engine.rng_for("x", 1).random(), engine.rng_for("x", 1).random())


class TestDelverMath(unittest.TestCase):
    def test_derived(self):
        d = stock_delver()
        self.assertEqual(engine.hp_max(d), 14)
        self.assertEqual(engine.grit_max(d), 3)
        self.assertEqual(engine.attack_bonus(d), 4)
        self.assertEqual(engine.guard(d), 11)
        self.assertEqual(engine.soak(d), 1)

    def test_knacks(self):
        self.assertEqual(engine.grit_max(stock_delver(knack="archivist")), 4)
        self.assertEqual(engine.attack_bonus(stock_delver(knack="cutter")), 5)
        self.assertEqual(engine.light_max(stock_delver(knack="lamplighter")), 12)
        self.assertEqual(engine.nerve_bonus(stock_delver(knack="salvage-priest")), 6)

    def test_heavy_armor_attack_penalty(self):
        d = stock_delver(armor={"name": "plate", "guard": 2, "soak": 3, "heavy": True})
        self.assertEqual(engine.attack_bonus(d), 3)


class TestFight(unittest.TestCase):
    def test_deterministic(self):
        a = run_to_end(stock_delver(), [HOUND, HOUND], "measure", 11)
        b = run_to_end(stock_delver(), [HOUND, HOUND], "measure", 11)
        self.assertEqual(a["events"], b["events"])
        self.assertEqual(a["outcome"], b["outcome"])

    def test_outcomes_and_state_bounds(self):
        for seed in range(30):
            r = run_to_end(stock_delver(), [HOUND, BRUTE], "measure", seed)
            self.assertIn(r["outcome"], ("victory", "retreated", "down"))
            self.assertTrue(0 <= r["hp"] <= 14)
            self.assertTrue(0 <= r["grit"] <= 3)
            if r["outcome"] == "victory":
                self.assertEqual(len(r["kills"]), 2)

    def find_pausing_seed(self):
        for seed in range(200):
            state, result = engine.start_fight(stock_delver(), [BRUTE], "measure", seed)
            if result is None:
                return seed, state
        self.fail("no seed pauses vs the brute; pause heuristic is broken")

    def test_pause_serializes_and_resumes_deterministically(self):
        seed, state = self.find_pausing_seed()
        blob = json.dumps(state)
        r1 = engine.resume_fight(json.loads(blob), "fight_on")
        r2 = engine.resume_fight(json.loads(blob), "fight_on")
        self.assertEqual(r1["events"], r2["events"])

    def test_pause_options_and_withdraw(self):
        seed, state = self.find_pausing_seed()
        opts = engine.pause_options(state)
        self.assertIn("fight_on", opts)
        self.assertIn("withdraw", opts)
        for stance in engine.STANCES:
            if stance != state["stance"]:
                self.assertIn(stance, opts)
        r = engine.resume_fight(json.loads(json.dumps(state)), "withdraw")
        self.assertIn(r["outcome"], ("retreated", "down"))

    def test_bad_resume_choice_raises(self):
        seed, state = self.find_pausing_seed()
        with self.assertRaises(ValueError):
            engine.resume_fight(state, "surrender")

    def test_pauses_at_most_once(self):
        # resuming with fight_on must run to an outcome, never re-pause
        seed, state = self.find_pausing_seed()
        r = engine.resume_fight(state, "fight_on")
        self.assertIn(r["outcome"], ("victory", "retreated", "down"))

    def test_unknown_stance_raises(self):
        with self.assertRaises(ValueError):
            engine.start_fight(stock_delver(), [HOUND], "berserk", 1)


class TestStrange(unittest.TestCase):
    def test_unknown_effect_raises(self):
        with self.assertRaises(ValueError):
            engine.apply_strange(stock_delver(), {}, "free_lunch", random.Random(1))

    def test_oil_seep(self):
        d = stock_delver()
        engine.apply_strange(d, {}, "oil_seep", random.Random(1))
        self.assertEqual(d["light"], 12)

    def test_kind_stranger_caps_at_max(self):
        d = stock_delver(hp=14)
        engine.apply_strange(d, {}, "kind_stranger", random.Random(1))
        self.assertEqual(d["hp"], 14)

    def test_old_stairs_sets_flag(self):
        exp = {}
        engine.apply_strange(stock_delver(), exp, "old_stairs", random.Random(1))
        self.assertTrue(exp["free_delve"])


if __name__ == "__main__":
    unittest.main()
