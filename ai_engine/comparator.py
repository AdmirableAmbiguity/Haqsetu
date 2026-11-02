
from difflib import SequenceMatcher


FIELDS_TO_COMPARE = [
    "name",
    "date_of_birth",
    "address"
]


def calculate_similarity(value1, value2):
    value1 = str(value1).lower().strip()
    value2 = str(value2).lower().strip()

    return SequenceMatcher(
        None,
        value1,
        value2
    ).ratio()


def compare_documents(documents):

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

            similarity = calculate_similarity(
                reference["value"],
                item["value"]
            )

            if similarity < 0.90:

                findings.append({
                    "type": "cross_document_mismatch",
                    "field": field,
                    "severity": "warning",
                    "documents": [
                        reference["document"],
                        item["document"]
                    ],
                    "values": [
                        reference["value"],
                        item["value"]
                    ],
                    "similarity": round(similarity, 2),
                    "explanation":
                        f"Possible {field} discrepancy detected."
                })

    return findings
