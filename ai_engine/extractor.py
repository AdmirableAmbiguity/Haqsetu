import re

def extract_fields(text: str) -> dict:
    """
    Extract structured fields from Indian government documents using robust regex patterns.
    """
    fields = {}
    if not text:
        return fields

    # 1. Applicant Name (handles 'Name:', 'Applicant Name:', 'Candidate Name:')
    name_match = re.search(
        r"(?:Applicant\s*Name|Candidate\s*Name|Student\s*Name|Name)\s*[:\-]\s*([A-Za-z. ]+)",
        text,
        re.IGNORECASE
    )
    if name_match:
        val = name_match.group(1).strip()
        if len(val) > 2 and not any(k in val.lower() for k in ["tehsildar", "magistrate", "officer", "authority"]):
            fields["name"] = val

    # 2. Date of Birth
    dob_match = re.search(
        r"(?:DOB|Date of Birth|Birth Date)\s*[:\-]\s*([\d]{1,2}[/\-.][\d]{1,2}[/\-.][\d]{2,4})",
        text,
        re.IGNORECASE
    )
    if dob_match:
        fields["date_of_birth"] = dob_match.group(1).strip()
        fields["dob"] = fields["date_of_birth"]

    # 3. Father's Name
    father_match = re.search(
        r"(?:Father['’]?s?\s*Name|Father|S/o|D/o|W/o)\s*[:\-]\s*([A-Za-z. ]+)",
        text,
        re.IGNORECASE
    )
    if father_match:
        fval = father_match.group(1).strip()
        if len(fval) > 2:
            fields["father_name"] = fval

    # 4. Social Category (OBC, SC, ST, EWS, General)
    cat_match = re.search(
        r"(?:Social\s*Category|Category|Caste\s*Community|Caste)\s*[:\-]\s*([A-Za-z0-9 /()]+)",
        text,
        re.IGNORECASE
    )
    if cat_match:
        cval = cat_match.group(1).strip()
        if any(c in cval.upper() for c in ["OBC", "SC", "ST", "EWS", "GENERAL"]):
            for c in ["OBC", "SC", "ST", "EWS", "GENERAL"]:
                if c in cval.upper():
                    fields["category"] = c
                    break
        else:
            fields["category"] = cval

    # 5. Annual Income
    inc_match = re.search(
        r"(?:Certified\s*Annual\s*Income|Annual\s*Family\s*Income|Annual\s*Income|Income)\s*[:\-]\s*(?:Rs\.?|₹|INR)?\s*([0-9,]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )
    if inc_match:
        fields["income"] = inc_match.group(1).strip().replace(",", "")

    # 6. Address
    address_match = re.search(
        r"(?:Permanent\s*Residence|Permanent\s*Address|Address)\s*[:\-]\s*([^\n\r]+)",
        text,
        re.IGNORECASE
    )
    if address_match:
        fields["address"] = address_match.group(1).strip()

    # 7. Document Identifier
    doc_id_match = re.search(
        r"(?:Aadhaar\s*Number|Aadhaar\s*No\.?|Certificate\s*No\.?|Certificate\s*Reference\s*No\.?|Roll\s*No\.?|Receipt\s*No\.?)\s*[:\-]?\s*([A-Z0-9/\- ]{4,25})",
        text,
        re.IGNORECASE
    )
    if doc_id_match:
        fields["document_id"] = doc_id_match.group(1).strip()

    return fields
