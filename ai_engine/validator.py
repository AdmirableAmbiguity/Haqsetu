
from datetime import datetime


def validate_fields(document_name, fields):
    """
    Validate extracted fields for a document.

    Returns a list of findings.
    """
    findings = []

    # 1. Check whether applicant name was extracted
    if not fields.get("name"):
        findings.append({
            "type": "missing_field",
            "field": "name",
            "document": document_name,
            "severity": "warning",
            "explanation": "Applicant name could not be extracted. Manual verification is recommended."
        })

    # 2. Validate date of birth
    dob = fields.get("date_of_birth") or fields.get("dob")

    if dob:
        valid_date = False

        for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                datetime.strptime(dob, date_format)
                valid_date = True
                break
            except ValueError:
                continue

        if not valid_date:
            findings.append({
                "type": "invalid_date",
                "field": "date_of_birth",
                "document": document_name,
                "severity": "warning",
                "explanation": "Date of birth has an unsupported or invalid format."
            })

    # 3. Validate annual income
    income = fields.get("income")

    if income is not None:
        try:
            if float(income) < 0:
                raise ValueError
        except (ValueError, TypeError):
            findings.append({
                "type": "invalid_income",
                "field": "income",
                "document": document_name,
                "severity": "error",
                "explanation": "Annual income must be a valid non-negative number."
            })

    # 4. Validate marks
    obtained = fields.get("marks_obtained")
    maximum = fields.get("maximum_marks")

    if obtained is not None and maximum is not None:
        try:
            if (
                float(maximum) <= 0
                or float(obtained) < 0
                or float(obtained) > float(maximum)
            ):
                raise ValueError
        except (ValueError, TypeError):
            findings.append({
                "type": "invalid_marks",
                "field": "marks",
                "document": document_name,
                "severity": "error",
                "explanation": "Marks obtained must be between zero and maximum marks."
            })

    # 5. Validate percentage
    percentage = fields.get("percentage")

    if percentage is not None:
        try:
            if not 0 <= float(percentage) <= 100:
                raise ValueError
        except (ValueError, TypeError):
            findings.append({
                "type": "invalid_percentage",
                "field": "percentage",
                "document": document_name,
                "severity": "error",
                "explanation": "Percentage must be between 0 and 100."
            })

    # 6. Check certificate number
    if document_name in ("certificate", "income_proof"):
        if not fields.get("document_id"):
            findings.append({
                "type": "missing_document_identifier",
                "field": "document_id",
                "document": document_name,
                "severity": "warning",
                "explanation": "Certificate identifier could not be extracted. Manual verification is recommended."
            })

    return findings
