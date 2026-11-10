"""Reporting regressions; no optimizer execution or campaign writes."""
import math
import unittest
from unittest.mock import Mock

from scripts.run_alns import iteration_throughput, plot_throughput


class ThroughputTests(unittest.TestCase):
    def test_pairs_are_time_weighted_and_ignore_allocated_budget(self):
        records = [dict(iterations=100, search_seconds=10, time_limit=1000),
                   dict(iterations=100, search_seconds=20, time_limit=2000)]
        result = iteration_throughput(records)
        self.assertAlmostEqual(result['iterations_per_search_second'], 200 / 30)
        self.assertEqual(result['throughput_runs'], 2)
        # Neither mean of per-run rates (7.5), nor budget-based rate (1/15).
        self.assertNotEqual(result['iterations_per_search_second'], 7.5)
        self.assertNotEqual(result['iterations_per_search_second'], 200 / 3000)

    def test_invalid_pairs_are_excluded_together(self):
        invalid = [None, 0, -1, math.nan, math.inf, True, '10']
        records = [dict(iterations=10, search_seconds=t) for t in invalid]
        records += [dict(iterations=i, search_seconds=5)
                    for i in [None, -1, math.nan, math.inf, True, '10', 1.5]]
        records += [{}, dict(iterations=999), dict(search_seconds=100)]
        records += [dict(iterations=100, search_seconds=10)]
        self.assertEqual(iteration_throughput(records),
                         dict(iterations_per_search_second=10, throughput_runs=1))

    def test_unavailable_and_zero_rates_are_distinct(self):
        self.assertEqual(iteration_throughput([{}]),
                         dict(iterations_per_search_second=None, throughput_runs=0))
        self.assertEqual(iteration_throughput([dict(iterations=0, search_seconds=5)]),
                         dict(iterations_per_search_second=0, throughput_runs=1))

    def test_plot_uses_measured_rate_and_explicit_label(self):
        axis = Mock()
        points = [dict(n=100, iterations_mean=999, time_limit=100,
                       iterations_per_search_second=20),
                  dict(n=200, iterations_per_search_second=None),
                  dict(n=300, iterations_per_search_second=0)]
        plot_throughput(axis, points)
        axis.plot.assert_called_once_with([100], [20], 'o')
        labels = axis.set.call_args.kwargs
        self.assertIn('measured search second', labels['ylabel'])
        self.assertIn('excludes construction/startup', labels['title'])
        self.assertEqual(labels['yscale'], 'log')


if __name__ == '__main__':
    unittest.main()
