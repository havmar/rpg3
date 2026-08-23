"""Contract suite for content.py: catalogs, validation, generators, flow.

One broken world per validator clause: every lint gets exactly one test that
builds a catalog violating it and asserts rejection.
"""

import copy
import json
import os
import shutil
import tempfile
import unittest

import content
import engine


def cat():
    return copy.deepcopy(content.load_catalog())


class TestCatalogLoads(unittest.TestCase):
    def test_clean_load(self):
        c = content.load_catalog()
        for section, count in content.CENSUS.items():
            self.assertEqual(len(c[section]), count, section)

    def test_version_clause(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "catalogs")
            shutil.copytree(content.CATALOG_DIR, dst)
            path = os.path.join(dst, "gear.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["version"] = 99
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            old = content.CATALOG_DIR
            content.CATALOG_DIR = dst
            try:
                with self.assertRaises(content.CatalogError):
                    content.load_catalog()
            finally:
                content.CATALOG_DIR = old


class TestBrokenWorlds(unittest.TestCase):
    def assert_rejected(self, broken):
        with self.assertRaises(content.CatalogError):
            content.validate_catalog(broken)

    def test_missing_field(self):
        c = cat()
        del c["enemies"][0]["menace"]
        self.assert_rejected(c)

    def test_unknown_field(self):
        c = cat()
        c["salvage"][0]["loot_table"] = "x"
        self.assert_rejected(c)

    def test_duplicate_name(self):
        c = cat()
        c["weapons"][1]["name"] = c["weapons"][0]["name"]
        self.assert_rejected(c)

    def test_census_mismatch(self):
        c = cat()
        c["strange"].append(dict(c["strange"][0], name="a second seep"))
        self.assert_rejected(c)

    def test_bad_depth_band(self):
        c = cat()
        c["enemies"][0]["depth"] = [3, 2]
        self.assert_rejected(c)

    def test_bad_dice_spec(self):
        c = cat()
        c["enemies"][0]["dmg"] = "one sword"
        self.assert_rejected(c)

    def test_menace_below_one(self):
        c = cat()
        c["enemies"][0]["menace"] = 0
        self.assert_rejected(c)

    def test_unknown_trait(self):
        c = cat()
        c["enemies"][0]["traits"] = ["swift", "invisible"]
        self.assert_rejected(c)

    def test_unknown_strange_effect(self):
        c = cat()
        c["strange"][0]["effect"] = "free_lunch"
        self.assert_rejected(c)

    def test_unknown_site_kind(self):
        c = cat()
        c["sites"][0]["kind"] = "boss"
        self.assert_rejected(c)

    def test_locality_violation(self):
        c = cat()
        c["sites"][0]["text"] = "A tunnel that comes out behind Wake."
        self.assert_rejected(c)

    def test_site_coverage_gap(self):
        c = cat()
        for s in c["sites"]:
            if s["kind"] == "breather":
                s["depth"] = [1, 5]  # nobody covers depth 6
        self.assert_rejected(c)

    def test_enemy_coverage_gap(self):
        c = cat()
        for e in c["enemies"]:
            e["depth"] = [1, min(e["depth"][1], 5)]
        self.assert_rejected(c)

    def test_priorities_not_permutation(self):
        c = cat()
        c["backgrounds"][0]["priorities"] = ["edge"] * 5
        self.assert_rejected(c)

    def test_unknown_gear_reference(self):
        c = cat()
        c["backgrounds"][0]["weapon"] = "vorpal sword"
        self.assert_rejected(c)


class TestGenerators(unittest.TestCase):
    def setUp(self):
        self.cat = content.load_catalog()

    def test_encounters_deterministic_and_bounded(self):
        for depth in range(1, content.DEPTH_MAX + 1):
            g1 = content.build_encounter(self.cat, depth, engine.rng_for("t", depth))
            g2 = content.build_encounter(self.cat, depth, engine.rng_for("t", depth))
            self.assertEqual([e["name"] for e in g1], [e["name"] for e in g2])
            self.assertGreaterEqual(len(g1), 1)
            self.assertLessEqual(sum(e["menace"] for e in g1), 2 + 2 * depth + 1)
            for e in g1:
                self.assertTrue(e["depth"][0] <= depth <= e["depth"][1])

    def test_sites_deterministic_and_wellformed(self):
        for i in range(60):
            depth = 1 + i % content.DEPTH_MAX
            s1 = content.generate_site(self.cat, depth, engine.rng_for("s", i))
            s2 = content.generate_site(self.cat, depth, engine.rng_for("s", i))
            self.assertEqual(s1, s2)
            self.assertIn(s1["kind"], content.SITE_KINDS)
            if s1["kind"] == "encounter":
                self.assertTrue(s1["enemies"])

    def test_candidates(self):
        c1 = content.delver_candidates(self.cat, "Ashline", 42)
        c2 = content.delver_candidates(self.cat, "Ashline", 42)
        self.assertEqual(c1, c2)
        self.assertEqual(len({c["background"] for c in c1}), 3)
        for c in c1:
            self.assertEqual(sum(c["stats"].values()), sum(content.BASE_ARRAY) + 1)
        self.assertNotEqual(c1, content.delver_candidates(self.cat, "Ashline", 43))


class TestExpeditionFlow(unittest.TestCase):
    """Seeded integration career: the whole loop without a chat in sight."""

    def fresh_save(self, world_seed=1234):
        c = content.load_catalog()
        candidate = content.delver_candidates(c, "Testfell", world_seed)[0]
        return c, {
            "version": engine.SAVE_VERSION, "world_seed": world_seed, "counter": 0,
            "delver": content.new_delver(candidate),
            "expedition": {"active": False, "depth": 0, "sites": [], "pending_site": None,
                           "paused_fight": None, "free_delve": False},
            "wake": {"chits": 0, "day": 1, "expeditions": 0},
            "history": [], "last_fight": None,
        }

    def test_career_runs_and_save_roundtrips(self):
        c, save = self.fresh_save()
        for _ in range(8):
            if not save["delver"]["alive"]:
                break
            rng = content._evt_rng(save)
            content.advance_delve(c, save, rng)
            if save["expedition"]["pending_site"] and save["expedition"]["pending_site"].get("enemies"):
                paused, _ = content.start_pending_fight(c, save, "measure")
                if paused:
                    save = json.loads(json.dumps(save))  # pause survives the save file
                    content.resume_paused_fight(c, save, "fight_on")
            save = json.loads(json.dumps(save))
            d = save["delver"]
            self.assertTrue(0 <= d["hp"] <= engine.hp_max(d))
            self.assertGreaterEqual(d["light"], 0)
        if save["delver"]["alive"] and save["expedition"]["active"]:
            content.do_surface(c, save)
            self.assertFalse(save["expedition"]["active"])
            self.assertEqual(save["delver"]["salvage"], [])
            self.assertGreaterEqual(save["wake"]["chits"], 0)
        self.assertTrue(save["history"])

    def test_guards(self):
        c, save = self.fresh_save()
        with self.assertRaises(ValueError):
            content.do_camp(c, save)  # not underground
        with self.assertRaises(ValueError):
            content.do_surface(c, save)  # already in Wake
        with self.assertRaises(ValueError):
            content.start_pending_fight(c, save, "measure")  # nothing pending
        with self.assertRaises(ValueError):
            content.do_train(save, "luck")
        with self.assertRaises(ValueError):
            content.do_buy(c, save, "vorpal sword")

    def test_train_and_buy(self):
        c, save = self.fresh_save()
        save["wake"]["chits"] = 100
        stat = "edge"
        before = save["delver"]["stats"][stat]
        content.do_train(save, stat)
        self.assertEqual(save["delver"]["stats"][stat], before + 1)
        content.do_buy(c, save, "salvage axe")
        self.assertEqual(save["delver"]["weapon"]["name"], "salvage axe")
        self.assertLess(save["wake"]["chits"], 100)


if __name__ == "__main__":
    unittest.main()
