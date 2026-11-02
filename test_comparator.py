import unittest
from ai_engine.comparator import compare_documents


class TestDocumentComparator(unittest.TestCase):

    def test_equivalent_dates(self):
        documents = {
            "application": {"date_of_birth": "15/08/1990"},
            "identity": {"date_of_birth": "15-08-1990"}
        }

        self.assertEqual(compare_documents(documents), [])

    def test_different_names(self):
        documents = {
            "application": {"name": "Ravi Kumar"},
            "identity": {"name": "Rohit Kumar"}
        }

        findings = compare_documents(documents)

        self.assertTrue(any(
            f["type"] == "cross_document_mismatch"
            for f in findings
        ))

    def test_matching_initials(self):
        documents = {
            "application": {"name": "Ravi Kumar"},
            "identity": {"name": "R. Kumar"}
        }

        findings = compare_documents(documents)

        self.assertTrue(any(
            f["type"] == "name_initial_match"
            for f in findings
        ))

    def test_different_pin_codes(self):
        documents = {
            "application": {
                "address": "Lucknow, Uttar Pradesh - 226001"
            },
            "identity": {
                "address": "Lucknow, Uttar Pradesh - 226002"
            }
        }

        findings = compare_documents(documents)

        self.assertTrue(any(
            f.get("field") == "pin_code"
            and f["type"] == "cross_document_mismatch"
            for f in findings
        ))

    def test_missing_pin_code(self):
        documents = {
            "application": {
                "address": "Lucknow, Uttar Pradesh - 226001"
            },
            "identity": {
                "address": "Lucknow, Uttar Pradesh"
            }
        }

        findings = compare_documents(documents)

        self.assertTrue(any(
            f["type"] == "incomplete_address"
            for f in findings
        ))

    def test_different_address_and_pin_codes(self):
        documents = {
            "application": {
                "address": "123 Main Street, Lucknow - 226001"
            },
            "identity": {
                "address": "456 Park Road, Lucknow - 226002"
            }
        }

        findings = compare_documents(documents)

        self.assertTrue(any(
            f.get("field") == "pin_code"
            and f["type"] == "cross_document_mismatch"
            for f in findings
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)