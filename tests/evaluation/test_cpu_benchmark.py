"""Guard real-model export preparation without downloading models in unit tests."""

import math
import unittest
from scripts.benchmark_cpu import configure_storage, preflight, reduce_vector


class Tokenizer:
    def __call__(self, text, **kwargs):
        assert kwargs == {"truncation": False, "add_special_tokens": True}
        return {"input_ids": [0] + text.split() + [1]}


class CpuBenchmarkTests(unittest.TestCase):
    def test_c_drive_storage_is_rejected_before_creation(self):
        with self.assertRaises(ValueError):
            configure_storage("C:/gather-benchmark-must-not-create")

    def test_token_budget_counts_special_tokens_and_rejects_before_inference(self):
        self.assertEqual(preflight(Tokenizer(), ["one two"], 4), [4])
        with self.assertRaises(ValueError):
            preflight(Tokenizer(), ["one two"], 3)

    def test_preflight_rejects_empty_collection(self):
        with self.assertRaises(ValueError):
            preflight(Tokenizer(), [], 4)

    def test_reduced_dimensions_are_renormalized(self):
        self.assertEqual(reduce_vector([3.0, 4.0, 12.0], 2), [0.6, 0.8])
        self.assertAlmostEqual(sum(x*x for x in reduce_vector([3.0, 4.0, 12.0], 3)), 1)

    def test_invalid_vectors_cannot_be_exported(self):
        for vector, dimensions in (([0.0], 1), ([math.nan], 1), ([math.inf], 1), ([1.0], 2), ([1.0], 0)):
            with self.subTest(vector=vector, dimensions=dimensions), self.assertRaises(ValueError):
                reduce_vector(vector, dimensions)


if __name__ == "__main__":
    unittest.main()
