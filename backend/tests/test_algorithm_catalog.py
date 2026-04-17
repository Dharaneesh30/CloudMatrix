import unittest

from backend.core.algorithm_catalog import build_algorithm_catalog, summarize_evaluation_scheme


class AlgorithmCatalogTests(unittest.TestCase):
    def test_evaluation_scheme_totals(self):
        scheme = summarize_evaluation_scheme()
        self.assertEqual(int(scheme.get("total_marks", 0)), 60)
        marks = sum(int(item.get("marks", 0)) for item in scheme.get("evaluations", []))
        self.assertEqual(marks, 60)

    def test_required_concepts_present(self):
        concepts = build_algorithm_catalog()
        names = {item.get("concept") for item in concepts}
        required = {
            "Divide and Conquer",
            "Greedy Method",
            "Dynamic Programming",
            "Hashing",
            "Backtracking",
            "Branch and Bound",
            "Tree Algorithms",
        }
        self.assertTrue(required.issubset(names))

    def test_algorithms_have_complexity_fields(self):
        for concept in build_algorithm_catalog():
            algos = concept.get("algorithms", [])
            self.assertGreater(len(algos), 0)
            for algo in algos:
                self.assertTrue(str(algo.get("time_complexity", "")).strip())
                self.assertTrue(str(algo.get("space_complexity", "")).strip())


if __name__ == "__main__":
    unittest.main()
