import unittest

from splot import (
    ProfileError,
    SchemaValidationError,
    SplotError,
    SplotProfileError,
    SplotRegistryError,
    SplotValidationError,
)
from splot.registry import FunctionRegistry
from splot.schemas import validate_decision_report_data


class ErrorTests(unittest.TestCase):
    def test_public_errors_share_base_classes(self):
        self.assertTrue(issubclass(ProfileError, SplotProfileError))
        self.assertTrue(issubclass(SchemaValidationError, SplotValidationError))
        self.assertTrue(issubclass(SplotRegistryError, SplotError))

    def test_registry_and_schema_raise_typed_errors(self):
        with self.assertRaises(SplotRegistryError):
            FunctionRegistry().get("missing.provider")
        with self.assertRaises(SchemaValidationError):
            validate_decision_report_data({})


if __name__ == "__main__":
    unittest.main()
