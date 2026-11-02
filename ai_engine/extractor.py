
import re


def extract_fields(text):
    """
    Extract basic fields from document text.
    Returns structured information.
    """

    fields = {}

    # Extract name
    name_match = re.search(
        r"Name\s*[:\-]\s*([A-Za-z ]+)",
        text,
        re.IGNORECASE
    )

    if name_match:
        fields["name"] = name_match.group(1).strip()

    # Extract date of birth
    dob_match = re.search(
        r"(?:DOB|Date of Birth)\s*[:\-]\s*([\d/-]+)",
        text,
        re.IGNORECASE
    )

    if dob_match:
        fields["date_of_birth"] = dob_match.group(1).strip()

    # Extract address
    address_match = re.search(
        r"Address\s*[:\-]\s*(.+)",
        text,
        re.IGNORECASE
    )

    if address_match:
        fields["address"] = address_match.group(1).strip()

    return fields
