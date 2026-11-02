import re


def extract_fields(text: str) -> dict:
    """
    Extract structured fields from Indian government documents.

    Extracts:
    - Applicant name
    - Date of birth
    - Father's name
    - Social category
    - Annual income
    - Address
    - Document identifier
    """

    fields = {}

    if not text:
        return fields

    # 1. Applicant Name
    name_match = re.search(
        r"(?:Applicant\s*Name|Candidate\s*Name|Student\s*Name|Name)"
        r"\s*[:\-.,]\s*([A-Za-z. ]+)",
        text,
        re.IGNORECASE
    )

    if name_match:
        value = name_match.group(1).strip()

        if (
            len(value) > 2
            and not any(
                keyword in value.lower()
                for keyword in [
                    "tehsildar",
                    "magistrate",
                    "officer",
                    "authority"
                ]
            )
        ):
            fields["name"] = value

    # 2. Date of Birth
    dob_match = re.search(
        r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)"
        r"\s*[:\-.,]?\s*"
        r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})",
        text,
        re.IGNORECASE
    )

    if dob_match:
        fields["date_of_birth"] = dob_match.group(1).strip()
        fields["dob"] = fields["date_of_birth"]

    # 3. Father's Name
    father_match = re.search(
        r"(?:Father['’]?s?\s*Name|Father|S/o|D/o|W/o)"
        r"\s*[:\-.,]\s*([A-Za-z. ]+)",
        text,
        re.IGNORECASE
    )

    if father_match:
        father_value = father_match.group(1).strip()

        if len(father_value) > 2:
            fields["father_name"] = father_value

    # 4. Social Category
    category_match = re.search(
        r"(?:Social\s*Category|Category|Caste\s*Community|Caste)"
        r"\s*[:\-.,]?\s*([A-Za-z0-9 /()]+)",
        text,
        re.IGNORECASE
    )

    if category_match:
        category_value = category_match.group(1).strip()

        category_patterns = {
            "OBC": r"\bOBC\b|OTHER BACKWARD CLASS",
            "SC": r"\bSC\b|SCHEDULED CASTE",
            "ST": r"\bST\b|SCHEDULED TRIBE",
            "EWS": r"\bEWS\b",
            "GENERAL": r"\bGENERAL\b"
        }

        for category, pattern in category_patterns.items():
            if re.search(
                pattern,
                category_value,
                re.IGNORECASE
            ):
                fields["category"] = category
                break
        # 4B. Caste Community
    community_match = re.search(
        r"Caste\s*Community\s*[:.,]?\s*([A-Za-z /-]+)",
        text,
        re.IGNORECASE
    )

    if community_match:
        community = community_match.group(1).strip()
        if community:
            fields["caste_community"] = community

    # 5. Annual Income
    income_match = re.search(
        r"(?:Certified\s*Annual\s*Income|"
        r"Annual\s*Family\s*Income|"
        r"Annual\s*Income|Income)"
        r"\s*[:\-.,]?\s*"
        r"(?:Rs\.?|₹|INR)?\s*"
        r"([0-9,]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )

    if income_match:
        fields["income"] = (
            income_match.group(1)
            .strip()
            .replace(",", "")
        )

    # 6. Address
    address_match = re.search(
        r"(?:Permanent\s*Residence|Permanent\s*Address|Address)"
        r"\s*[:\-.,]?\s*([^\n\r]+)",
        text,
        re.IGNORECASE
    )

    if address_match:
        fields["address"] = address_match.group(1).strip()

    # 7. Document Identifier
     # 7. Document Identifier
    doc_id_match = re.search(
        r"(?:Aadhaar\s*(?:Number|No\.?)|"
        r"(?:Certificate|Cerificate|Certficate)\s*"
        r"(?:No\.?|Number|Reference\s*No\.?)|"
        r"Roll\s*No\.?|Receipt\s*No\.?)"
        r"\s*[:\-]?\s*([A-Z0-9/\- ]{4,25})",
        text,
        re.IGNORECASE
    )

    if doc_id_match:
        fields["document_id"] = doc_id_match.group(1).strip()
        # 8. Roll Number
    roll_match = re.search(
        r"Roll\s*(?:Number|No\.?)\s*[:\-]?\s*([A-Z0-9/-]+)",
        text,
        re.IGNORECASE
    )

    if roll_match:
        fields["roll_number"] = roll_match.group(1).strip()

    # 9. Year of Passing
    year_match = re.search(
        r"(?:Year\s*of\s*Passing|Passing\s*Year)"
        r"\s*[:\-]?\s*((?:19|20)\d{2})",
        text,
        re.IGNORECASE
    )

    if year_match:
        fields["year_of_passing"] = year_match.group(1)

    # 10. Marks Obtained and Maximum Marks
    marks_match = re.search(
        r"(?:Total\s*Marks|Marks\s*Obtained)"
        r"\s*[:\-]?\s*(\d{1,4})\s*/\s*(\d{1,4})",
        text,
        re.IGNORECASE
    )

    if marks_match:
        obtained = int(marks_match.group(1))
        maximum = int(marks_match.group(2))

        if maximum > 0 and obtained <= maximum:
            fields["marks_obtained"] = obtained
            fields["maximum_marks"] = maximum

    # 11. Percentage
    percentage_match = re.search(
        r"(\d{1,3}(?:\.\d+)?)\s*%",
        text
    )

    if percentage_match:
        percentage = float(percentage_match.group(1))

        if 0 <= percentage <= 100:
            fields["percentage"] = percentage

    # 12. Result
    result_match = re.search(
        r"Result\s*[:\-]?\s*(PASSED|PASS|FAILED|FAIL)",
        text,
        re.IGNORECASE
    )

    if result_match:
        fields["result"] = result_match.group(1).upper()

    # 13. Institution
    institution_match = re.search(
        r"Institution\s*[:\-]\s*([^\n\r]+)",
        text,
        re.IGNORECASE
    )

    if institution_match:
        fields["institution"] = institution_match.group(1).strip()

    if doc_id_match:
        fields["document_id"] = doc_id_match.group(1).strip()

    return fields