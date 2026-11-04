"""Synthetic score mechanics; real saved-vector evidence is evaluated separately."""
import unittest
from services.worker.search_relevance import selected_indices, validate_space, EMBEDDING_SPACE


class RelevanceTests(unittest.TestCase):
    def test_floor_band_and_inclusive_boundary(self):
        self.assertEqual(selected_indices([.74, .62, .61, .24, .23]), (0, 1))
        self.assertEqual(selected_indices([.24, .239]), (0,))
        self.assertEqual(selected_indices([.23, .0, -.3]), ())
        self.assertEqual(selected_indices([]), ())

    def test_invalid_scores_fail_closed(self):
        for scores in ([float('nan')], [float('inf')], [True], [1.01], [-1.01],
                       [.3, .4], [0.] * 101, '0.5'):
            with self.subTest(scores=str(scores)), self.assertRaises(ValueError):
                selected_indices(scores)

    def test_equal_scores_are_retained_without_inventing_confidence(self):
        self.assertEqual(selected_indices([.6, .6, .6]), (0, 1, 2))

    def test_profile_is_bound_to_the_calibrated_embedding_space(self):
        validate_space(*EMBEDDING_SPACE)
        for space in [('different', EMBEDDING_SPACE[1], 512),
                      (EMBEDDING_SPACE[0], 'different', 512),
                      (*EMBEDDING_SPACE[:2], 256)]:
            with self.assertRaises(ValueError):
                validate_space(*space)


if __name__ == '__main__':
    unittest.main()
