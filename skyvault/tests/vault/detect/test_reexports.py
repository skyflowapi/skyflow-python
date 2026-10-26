import unittest


class TestDetectReexports(unittest.TestCase):
    def test_models_import_from_vault_detect(self):
        from skyflow.vault.detect import (
            DeidentifyStringRequest,
            DeidentifyFileRequest,
            GetRunRequest,
            ReidentifyStringRequest,
            ReidentifyFileRequest,
            CheckGuardrailsRequest,
            PollOptions,
            DetectConfiguration,
            Detect,
            Entity,
            RedactionLevel,
        )

        request = DeidentifyStringRequest(text="hello", configuration_id="cfg")
        self.assertEqual(request.text, "hello")
        self.assertIsNone(PollOptions().wait_time)

    def test_enums_import_from_utils_enums(self):
        from skyflow.utils.enums import (
            EntityType,
            DeidentificationType,
            ReturnEntitiesType,
            RedactionType,
            DataSourceType,
            FileDataFormat,
            DetectRunStatus,
            ObjectEntityType,
            ObjectDeidentificationType,
            OutputTranscriptionType,
            PdfProcessingMode,
            MaskingMethod,
            GuardrailsValidation,
        )

        self.assertEqual(EntityType.NAME.value, "NAME")
        self.assertEqual(FileDataFormat.PDF.value, "pdf")
        self.assertEqual(MaskingMethod.BLUR.value, "BLUR")

    def test_detect_accessor(self):
        from skyflow import Skyflow
        self.assertTrue(hasattr(Skyflow, "detect"))


if __name__ == "__main__":
    unittest.main()
