import unittest
from unittest.mock import patch

from common.vault.base_vault import VaultController, DEFAULT_INSERT_BATCH_SIZE, MAX_INSERT_BATCH_SIZE


class DummyVaultController(VaultController):
    def insert(self, request):
        raise NotImplementedError

    def get(self, request):
        raise NotImplementedError

    def update(self, request):
        raise NotImplementedError

    def delete(self, request):
        raise NotImplementedError

    def query(self, request):
        raise NotImplementedError

    def detokenize(self, request):
        raise NotImplementedError


class TestVaultControllerAbstractContract(unittest.TestCase):
    def test_cannot_instantiate_without_insert(self):
        class Incomplete(VaultController):
            pass

        with self.assertRaises(TypeError):
            Incomplete(vault_client=None)

    def test_cannot_instantiate_missing_any_single_method(self):
        """Java-interface-style: every one of the six operations is independently required --
        omitting any single one (not just insert) blocks instantiation."""
        for missing in ("insert", "get", "update", "delete", "query", "detokenize"):
            methods = {name: (lambda self, request: None) for name in
                       ("insert", "get", "update", "delete", "query", "detokenize") if name != missing}
            Incomplete = type("Incomplete", (VaultController,), methods)
            with self.assertRaises(TypeError, msg=f"missing only '{missing}' should still fail to instantiate"):
                Incomplete(vault_client=None)

    def test_concrete_subclass_instantiates(self):
        vault = DummyVaultController(vault_client=None)
        self.assertIsInstance(vault, VaultController)


class TestGetInsertBatchSize(unittest.TestCase):
    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {}, clear=True)
    def test_defaults_when_unset(self, _mock_find_dotenv):
        self.assertEqual(VaultController._get_insert_batch_size(), DEFAULT_INSERT_BATCH_SIZE)

    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": "25"}, clear=True)
    def test_valid_value_used(self, _mock_find_dotenv):
        self.assertEqual(VaultController._get_insert_batch_size(), 25)

    @patch("common.vault.base_vault.log_warn")
    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": "not-a-number"}, clear=True)
    def test_non_numeric_falls_back_to_default(self, _mock_find_dotenv, mock_log_warn):
        self.assertEqual(VaultController._get_insert_batch_size(), DEFAULT_INSERT_BATCH_SIZE)
        mock_log_warn.assert_called_once()

    @patch("common.vault.base_vault.log_warn")
    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": "0"}, clear=True)
    def test_zero_falls_back_to_default(self, _mock_find_dotenv, mock_log_warn):
        self.assertEqual(VaultController._get_insert_batch_size(), DEFAULT_INSERT_BATCH_SIZE)
        mock_log_warn.assert_called_once()

    @patch("common.vault.base_vault.log_warn")
    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": "-5"}, clear=True)
    def test_negative_falls_back_to_default(self, _mock_find_dotenv, mock_log_warn):
        self.assertEqual(VaultController._get_insert_batch_size(), DEFAULT_INSERT_BATCH_SIZE)
        mock_log_warn.assert_called_once()

    @patch("common.vault.base_vault.log_warn")
    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": "5000"}, clear=True)
    def test_over_max_clamps_to_max(self, _mock_find_dotenv, mock_log_warn):
        self.assertEqual(VaultController._get_insert_batch_size(), MAX_INSERT_BATCH_SIZE)
        mock_log_warn.assert_called_once()

    @patch("common.vault.base_vault.dotenv.find_dotenv", return_value=None)
    @patch.dict("os.environ", {"INSERT_BATCH_SIZE": str(MAX_INSERT_BATCH_SIZE)}, clear=True)
    def test_exactly_max_is_not_clamped_with_warning(self, _mock_find_dotenv):
        # boundary: exactly the max is valid, shouldn't warn
        self.assertEqual(VaultController._get_insert_batch_size(), MAX_INSERT_BATCH_SIZE)


class TestRunBatches(unittest.TestCase):
    def test_exact_division(self):
        items = list(range(10))
        seen_batches = []

        def send(batch, start):
            seen_batches.append((list(batch), start))
            return list(batch), []

        successes, errors = VaultController._run_batches(items, 5, send)
        self.assertEqual(seen_batches, [([0, 1, 2, 3, 4], 0), ([5, 6, 7, 8, 9], 5)])
        self.assertEqual(successes, items)
        self.assertEqual(errors, [])

    def test_remainder_batch(self):
        items = list(range(7))
        seen_batches = []

        def send(batch, start):
            seen_batches.append((list(batch), start))
            return [], []

        VaultController._run_batches(items, 3, send)
        self.assertEqual(seen_batches, [([0, 1, 2], 0), ([3, 4, 5], 3), ([6], 6)])

    def test_batch_size_larger_than_items_is_a_single_batch(self):
        items = [1, 2, 3]
        calls = []

        def send(batch, start):
            calls.append((list(batch), start))
            return list(batch), []

        VaultController._run_batches(items, 100, send)
        self.assertEqual(calls, [([1, 2, 3], 0)])

    def test_empty_items_makes_no_calls(self):
        calls = []

        def send(batch, start):
            calls.append(batch)
            return [], []

        successes, errors = VaultController._run_batches([], 5, send)
        self.assertEqual(calls, [])
        self.assertEqual(successes, [])
        self.assertEqual(errors, [])

    def test_results_aggregate_in_order_across_batches(self):
        items = list(range(6))

        def send(batch, start):
            # every batch reports its first item as a success, second as an error
            successes = [batch[0]]
            errors = [f"err-{batch[1]}"] if len(batch) > 1 else []
            return successes, errors

        successes, errors = VaultController._run_batches(items, 2, send)
        self.assertEqual(successes, [0, 2, 4])
        self.assertEqual(errors, ["err-1", "err-3", "err-5"])

    def test_a_failing_batch_does_not_abort_remaining_batches(self):
        items = list(range(4))
        calls = []

        def send(batch, start):
            calls.append(list(batch))
            if batch == [0, 1]:
                return [], ["batch-1-failed"]
            return list(batch), []

        successes, errors = VaultController._run_batches(items, 2, send)
        self.assertEqual(calls, [[0, 1], [2, 3]])  # second batch still ran
        self.assertEqual(successes, [2, 3])
        self.assertEqual(errors, ["batch-1-failed"])


if __name__ == "__main__":
    unittest.main()
