import os
import unittest
from unittest.mock import patch

from skyflow_flowvault.utils import _batching
from skyflow_flowvault.utils._batching import (
    resolve_batch_config,
    create_batches,
    DEFAULT_BATCH_SIZE,
    MAX_BATCH_SIZE,
    MAX_CONCURRENCY,
    INSERT_BATCH_SIZE_KEY,
    INSERT_CONCURRENCY_LIMIT_KEY,
)


def _with_settings(mapping):
    return patch.object(_batching, "_resolve_setting", lambda key: mapping.get(key))


class TestCreateBatches(unittest.TestCase):
    def test_contiguous_slices(self):
        self.assertEqual(create_batches([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])

    def test_single_batch_when_size_exceeds_count(self):
        self.assertEqual(create_batches([1, 2, 3], 10), [[1, 2, 3]])

    def test_empty(self):
        self.assertEqual(create_batches([], 5), [])


class TestResolveBatchConfig(unittest.TestCase):
    def test_defaults_when_unset(self):
        with _with_settings({}):
            batch_size, concurrency = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 500)
        self.assertEqual(batch_size, DEFAULT_BATCH_SIZE)
        self.assertEqual(concurrency, 1)

    def test_batch_size_capped_at_max(self):
        with _with_settings({INSERT_BATCH_SIZE_KEY: "5000"}):
            batch_size, _ = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 10)
        self.assertEqual(batch_size, MAX_BATCH_SIZE)

    def test_invalid_batch_size_falls_back(self):
        for raw in ("abc", "0", "-5"):
            with _with_settings({INSERT_BATCH_SIZE_KEY: raw}):
                batch_size, _ = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 10)
            self.assertEqual(batch_size, DEFAULT_BATCH_SIZE)

    def test_concurrency_capped_by_batch_count(self):
        with _with_settings({INSERT_BATCH_SIZE_KEY: "100", INSERT_CONCURRENCY_LIMIT_KEY: "10"}):
            batch_size, concurrency = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 500)
        self.assertEqual(batch_size, 100)
        self.assertEqual(concurrency, 5)  # 5 batches, so min(10, max, 5) = 5

    def test_concurrency_capped_at_max(self):
        with _with_settings({INSERT_BATCH_SIZE_KEY: "1", INSERT_CONCURRENCY_LIMIT_KEY: "999"}):
            _, concurrency = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 100)
        self.assertEqual(concurrency, MAX_CONCURRENCY)

    def test_invalid_concurrency_falls_back(self):
        with _with_settings({INSERT_CONCURRENCY_LIMIT_KEY: "abc"}):
            _, concurrency = resolve_batch_config(INSERT_BATCH_SIZE_KEY, INSERT_CONCURRENCY_LIMIT_KEY, 500)
        self.assertEqual(concurrency, 1)


class TestResolveSetting(unittest.TestCase):
    def test_reads_process_env_first(self):
        with patch.dict(os.environ, {INSERT_BATCH_SIZE_KEY: "77"}):
            self.assertEqual(_batching._resolve_setting(INSERT_BATCH_SIZE_KEY), "77")


if __name__ == "__main__":
    unittest.main()
