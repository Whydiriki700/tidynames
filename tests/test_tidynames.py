import os, sys, tempfile, unittest
sys.path.insert(0, ".")
from tidynames.core import apply_plan, build_plan, find_collisions, slugify, undo

class SlugTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Foto Liburan 2026!"), "foto-liburan-2026")
        self.assertEqual(slugify("IMG_0001 final FINAL"), "img-0001-final-final")

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        for name in ("Foto A.jpg", "Foto B.jpg", "catatan.txt"):
            with open(os.path.join(self.tmp.name, name), "w") as handle:
                handle.write("x")
    def tearDown(self):
        self.tmp.cleanup()
    def test_slug_plan(self):
        plan = build_plan(self.tmp.name, slug=True)
        mapping = {p["old"]: p["new"] for p in plan}
        self.assertEqual(mapping["Foto A.jpg"], "foto-a.jpg")
        self.assertNotIn("catatan.txt", mapping)
    def test_number_prefix(self):
        plan = build_plan(self.tmp.name, number=True, start=5)
        self.assertTrue(all(p["new"].split("-")[0].isdigit() for p in plan))
        self.assertTrue(plan[0]["new"].startswith("005-"))
    def test_apply_and_undo(self):
        plan = build_plan(self.tmp.name, slug=True)
        safe = [p for p in plan if p not in find_collisions(self.tmp.name, plan)]
        done = apply_plan(self.tmp.name, safe)
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, "foto-a.jpg")))
        restored = undo(self.tmp.name)
        self.assertEqual(len(restored), len(done))
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, "Foto A.jpg")))
    def test_collision_detected(self):
        with open(os.path.join(self.tmp.name, "foto-a.jpg"), "w") as handle:
            handle.write("y")
        plan = build_plan(self.tmp.name, slug=True)
        collisions = find_collisions(self.tmp.name, plan)
        self.assertTrue(any(c["old"] == "Foto A.jpg" for c in collisions))

if __name__ == "__main__":
    unittest.main()
