import unittest
import io
from skyflow.vault.detect._deidentify_text_response import DeidentifyTextResponse
from skyflow.vault.detect._reidentify_text_response import ReidentifyTextResponse
from skyflow.vault.detect._entity_info import EntityInfo
from skyflow.vault.detect._file_input import FileInput
from skyflow.vault.detect._text_index import TextIndex
from skyflow.vault.detect._date_transformation import DateTransformation
from skyflow.vault.detect._transformations import Transformations
from skyflow.vault.detect._file import File
from skyflow.utils.enums import DetectEntities


class TestTextIndex(unittest.TestCase):
    def test_repr(self):
        t = TextIndex(start=0, end=4)
        self.assertIn("TextIndex", repr(t))
        self.assertIn("0", repr(t))

    def test_str(self):
        t = TextIndex(start=0, end=4)
        self.assertEqual(str(t), repr(t))

    def test_attributes(self):
        t = TextIndex(start=5, end=10)
        self.assertEqual(t.start, 5)
        self.assertEqual(t.end, 10)


class TestEntityInfo(unittest.TestCase):
    def setUp(self):
        self.text_index = TextIndex(0, 4)
        self.processed_index = TextIndex(0, 8)

    def test_repr(self):
        e = EntityInfo(
            token="TOKEN_1", value="John",
            text_index=self.text_index,
            processed_index=self.processed_index,
            entity="NAME", scores={"confidence": 0.9}
        )
        self.assertIn("EntityInfo", repr(e))
        self.assertIn("John", repr(e))

    def test_str(self):
        e = EntityInfo(
            token="TOKEN_1", value="John",
            text_index=self.text_index,
            processed_index=self.processed_index,
            entity="NAME", scores={}
        )
        self.assertEqual(str(e), repr(e))

    def test_attributes(self):
        e = EntityInfo(
            token="T", value="v",
            text_index=self.text_index,
            processed_index=self.processed_index,
            entity="EMAIL", scores={"s": 1.0}
        )
        self.assertEqual(e.token, "T")
        self.assertEqual(e.entity, "EMAIL")


class TestDeidentifyTextResponse(unittest.TestCase):
    def test_repr(self):
        r = DeidentifyTextResponse(
            processed_text="[TOKEN_1]", entities=[], word_count=1, char_count=9
        )
        self.assertIn("DeidentifyTextResponse", repr(r))

    def test_str(self):
        r = DeidentifyTextResponse(
            processed_text="[TOKEN_1]", entities=[], word_count=1, char_count=9
        )
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = DeidentifyTextResponse(
            processed_text="text", entities=[], word_count=1, char_count=4
        )
        self.assertIsNone(r.errors)


class TestReidentifyTextResponse(unittest.TestCase):
    def test_repr(self):
        r = ReidentifyTextResponse(processed_text="John lives in NYC")
        self.assertIn("ReidentifyTextResponse", repr(r))

    def test_str(self):
        r = ReidentifyTextResponse(processed_text="John")
        self.assertEqual(str(r), repr(r))

    def test_defaults(self):
        r = ReidentifyTextResponse(processed_text="text")
        self.assertIsNone(r.errors)


class TestFileInput(unittest.TestCase):
    def test_repr_with_file(self):
        bio = io.BytesIO(b"data")
        bio.name = "test.txt"
        fi = FileInput(file=bio)
        self.assertIn("FileInput", repr(fi))

    def test_str(self):
        fi = FileInput(file_path="/some/path.pdf")
        self.assertEqual(str(fi), repr(fi))

    def test_repr_no_file(self):
        fi = FileInput()
        self.assertIn("FileInput", repr(fi))
        self.assertIsNone(fi.file)
        self.assertIsNone(fi.file_path)


class TestDateTransformation(unittest.TestCase):
    def test_instantiation(self):
        dt = DateTransformation(
            max_days=30, min_days=1,
            entities=[DetectEntities.DATE]
        )
        self.assertEqual(dt.max, 30)
        self.assertEqual(dt.min, 1)
        self.assertEqual(dt.entities, [DetectEntities.DATE])


class TestTransformations(unittest.TestCase):
    def test_instantiation(self):
        dt = DateTransformation(max_days=30, min_days=1, entities=[DetectEntities.DATE])
        t = Transformations(shift_dates=dt)
        self.assertEqual(t.shift_dates, dt)


class TestFile(unittest.TestCase):
    def test_properties_with_file(self):
        bio = io.BytesIO(b"hello")
        bio.name = "test.txt"
        f = File(file=bio)
        self.assertEqual(f.name, "test.txt")
        self.assertEqual(f.size, 5)
        self.assertIsNotNone(f.type)
        self.assertIsNotNone(f.last_modified)

    def test_properties_without_file(self):
        f = File()
        self.assertIsNone(f.name)
        self.assertIsNone(f.size)
        self.assertIsNone(f.type)
        self.assertIsNone(f.last_modified)

    def test_seek_without_file(self):
        f = File()
        result = f.seek(0)
        self.assertIsNone(result)

    def test_read_without_file(self):
        f = File()
        result = f.read()
        self.assertIsNone(result)

    def test_seek_with_file(self):
        bio = io.BytesIO(b"hello")
        bio.name = "t.txt"
        f = File(file=bio)
        f.seek(0)
        self.assertEqual(f.read(), b"hello")

    def test_repr(self):
        bio = io.BytesIO(b"hi")
        bio.name = "t.txt"
        f = File(file=bio)
        self.assertIn("File", repr(f))


if __name__ == "__main__":
    unittest.main()
