
import re
from difflib import SequenceMatcher
from datetime import datetime


FIELDS_TO_COMPARE = [
    "name",
    "date_of_birth",
    "address"
]


def normalize_name(value):
    """Normalize names while preserving individual words."""
    value = str(value).lower().strip()
    value = re.sub(r"[^a-z\s]", " ", value)
    return " ".join(value.split())


def normalize_date(value):
    """Convert common date formats into YYYY-MM-DD."""
    value = str(value).strip()

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return value.lower()


def extract_pin_code(value):
    """Extract a six-digit Indian PIN code, if present."""
    match = re.search(r"\b\d{6}\b", str(value))
    return match.group() if match else None


def normalize_address(value):
    """Normalize common address abbreviations and punctuation."""
    value = str(value).lower()

    # Remove PIN codes; they are checked separately.
    value = re.sub(r"\b\d{6}\b", " ", value)

    replacements = {
        "street": "st",
        "road": "rd",
        "uttar pradesh": "up",
        "apartment": "apt",
        "district": "dist"
    }

    for old, new in replacements.items():
        value = re.sub(r"\b" + old + r"\b", new, value)

    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def calculate_similarity(value1, value2):
    """Calculate similarity between normalized values."""
    value1 = str(value1).lower().strip()
    value2 = str(value2).lower().strip()
    return SequenceMatcher(None, value1, value2).ratio()


def is_initial_name_match(name1, name2):
    """Check whether names may match through initials."""
    tokens1 = normalize_name(name1).split()
    tokens2 = normalize_name(name2).split()

    if len(tokens1) != len(tokens2) or not tokens1:
        return False

    for a, b in zip(tokens1, tokens2):
        if a == b:
            continue
        if len(a) == 1 and b.startswith(a):
            continue
        if len(b) == 1 and a.startswith(b):
            continue
        return False

    return True


def compare_documents(documents):
    """
    Compare extracted fields across documents.

    Reports possible mismatches for human verification.
    PIN codes are checked independently of address text.
    """
    findings = []

    for field in FIELDS_TO_COMPARE:
        values = []

        for document_name, data in documents.items():
            value = data.get(field)
            if value:
                values.append({
                    "document": document_name,
                    "value": value
                })

        if len(values) < 2:
            continue

        reference = values[0]

        for item in values[1:]:
            value1 = reference["value"]
            value2 = item["value"]

            # Check PIN codes independently of the address comparison.
            if field == "address":
                pin1 = extract_pin_code(value1)
                pin2 = extract_pin_code(value2)

                if pin1 and pin2 and pin1 != pin2:
                    findings.append({
                        "type": "cross_document_mismatch",
                        "field": "pin_code",
                        "severity": "warning",
                        "documents": [
                            reference["document"],
                            item["document"]
                        ],
                        "values": [pin1, pin2],
                        "explanation":
                            "Different PIN codes detected across "
                            "documents. Verify the original documents."
                    })

                elif bool(pin1) != bool(pin2):
                    findings.append({
                        "type": "incomplete_address",
                        "field": "address",
                        "severity": "warning",
                        "documents": [
                            reference["document"],
                            item["document"]
                        ],
                        "explanation":
                            "A PIN code is missing from one document. "
                            "Verify whether the address is complete."
                    })

                normalized1 = normalize_address(value1)
                normalized2 = normalize_address(value2)

            elif field == "name":
                normalized1 = normalize_name(value1)
                normalized2 = normalize_name(value2)

            elif field == "date_of_birth":
                normalized1 = normalize_date(value1)
                normalized2 = normalize_date(value2)

            else:
                normalized1 = str(value1).lower().strip()
                normalized2 = str(value2).lower().strip()

            # No further discrepancy for equivalent normalized values.
            if normalized1 == normalized2:
                continue

            # Names matching through initials need review, not a
            # definitive mismatch.
            if (
                field == "name"
                and is_initial_name_match(value1, value2)
            ):
                findings.append({
                    "type": "name_initial_match",
                    "field": field,
                    "severity": "info",
                    "documents": [
                        reference["document"],
                        item["document"]
                    ],
                    "values": [value1, value2],
                    "explanation":
                        "Names appear consistent through initials, "
                        "but full-name verification is recommended."
                })
                continue

            similarity = calculate_similarity(
                normalized1,
                normalized2
            )

            findings.append({
                "type": "cross_document_mismatch",
                "field": field,
                "severity": "warning",
                "documents": [
                    reference["document"],
                    item["document"]
                ],
                "values": [value1, value2],
                "similarity": round(similarity, 2),
                "explanation":
                    f"Possible {field} discrepancy detected. "
                    "Please verify the original documents."
            })

    return findings
