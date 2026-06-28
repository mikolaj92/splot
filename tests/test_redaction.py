import unittest

from splot.redaction import REDACTED, redact_value


class RedactionTests(unittest.TestCase):
    def test_default_and_explicit_paths_are_redacted_without_mutating_input(self):
        original = {
            "payload": {"secret": "s1", "visible": "ok"},
            "items": [{"metadata": {"api_key": "k1", "note": "n1"}}, {"metadata": {"token": "t1"}}],
        }

        redacted = redact_value(original, ["payload.visible", "items.*.metadata.note"])

        self.assertEqual(redacted["payload"]["secret"], REDACTED)
        self.assertEqual(redacted["payload"]["visible"], REDACTED)
        self.assertEqual(redacted["items"][0]["metadata"]["api_key"], REDACTED)
        self.assertEqual(redacted["items"][0]["metadata"]["note"], REDACTED)
        self.assertEqual(original["payload"]["secret"], "s1")


if __name__ == "__main__":
    unittest.main()
