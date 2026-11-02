
from ai_engine.ocr import extract_text


TEST_FILES = [
    "samples/test_files/aadhaar_card.png",
    "samples/test_files/caste_certificate.png",
    "samples/test_files/income_certificate.pdf",
    "samples/test_files/marksheet_class12.pdf"
]


def test_ocr():
    print("\n========== HAQSETU OCR TEST ==========\n")

    passed = 0
    failed = 0

    for file_path in TEST_FILES:
        print(f"\nTesting: {file_path}")

        try:
            text = extract_text(file_path)

            if not text.strip():
                print("RESULT: FAIL - No text extracted")
                failed += 1
                continue

            print("RESULT: PASS")
            print(f"Characters extracted: {len(text)}")
            print("Extracted preview:")
            print(text[:250].replace("\n", " "))

            passed += 1

        except Exception as error:
            print("RESULT: FAIL")
            print(f"Error: {error}")
            failed += 1

    print("\n========== TEST SUMMARY ==========")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")


if __name__ == "__main__":
    test_ocr()
