import unittest
from skyflow.vault.controller._audit import Audit
from skyflow.vault.controller._bin_look_up import BinLookUp


class TestAudit(unittest.TestCase):
    def test_instantiation(self):
        a = Audit()
        self.assertIsNotNone(a)

    def test_list_returns_none(self):
        a = Audit()
        self.assertIsNone(a.list())


class TestBinLookUp(unittest.TestCase):
    def test_instantiation(self):
        b = BinLookUp()
        self.assertIsNotNone(b)

    def test_get_returns_none(self):
        b = BinLookUp()
        self.assertIsNone(b.get())


if __name__ == "__main__":
    unittest.main()
