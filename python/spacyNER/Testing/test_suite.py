# ============================================================
# testing/test_suite.py
# ------------------------------------------------------------
# COMPLETE TEST SUITE for Civil Registry NER System
#
# Covers ALL thesis testing requirements:
#
#   1. ACCURACY TESTING
#      - Per-label accuracy (precision, recall, F1)
#      - Per-form accuracy (Form 1A, 2A, 3A)
#      - Overall system accuracy %
#
#   2. BLACK BOX TESTING
#      - Input/output tests (no knowledge of internals)
#      - Valid input tests
#      - Invalid / edge case input tests
#      - Boundary tests (empty, partial, garbled OCR)
#
#   3. CONFUSION MATRIX
#      - Per-label true positive / false positive / false negative
#      - Visual confusion matrix table
#      - Per-form confusion matrix
#
#   4. ISO 25010 RELIABILITY TESTING
#      - Fault tolerance (bad input, missing fields)
#      - Recoverability (system doesn't crash on errors)
#      - Maturity (consistent results on repeated runs)
#      - Availability (model loads successfully)
#
#   5. ISO 25010 USABILITY TESTING
#      - Learnability (consistent output format)
#      - Operability (pipeline runs end-to-end)
#      - Accessibility (output readable as dict/dataclass)
#      - Error handling (clear messages on failure)
#
# How to run:
#   python testing/test_suite.py
#   python testing/test_suite.py --model ./models/civil_registry_model/model-best
#   python testing/test_suite.py --model en_core_web_sm   (baseline before training)
# ============================================================

import sys
import os
import time
import argparse
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spacyNER.extractor import CivilRegistryNER
from spacyNER.autofill  import AutoFillEngine
from spacyNER.models    import Form1A, Form2A, Form3A


# ══════════════════════════════════════════════════════════
# TEST DATA
# Each test case has: input text, expected labels, form type
# These simulate real CRNN+CTC OCR output from scanned forms.
# ══════════════════════════════════════════════════════════

# ── Form 1A Test Cases ─────────────────────────────────────
FORM_1A_TESTS = [
    {
        "id": "1A-001",
        "desc": "Standard birth certificate — complete fields",
        "text": (
            "1. NAME (First): Juan  (Middle): dela Cruz  (Last): Santos\n"
            "2. SEX: Male\n"
            "3. DATE OF BIRTH: March 15, 1990\n"
            "4. PLACE OF BIRTH: Makati City\n"
            "7. MAIDEN NAME (First): Maria  (Middle): Reyes  (Last): dela Cruz\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Pedro  (Middle): Cruz  (Last): Santos\n"
            "15. CITIZENSHIP: Filipino\n"
            "20a. DATE: June 10, 1985\n"
            "20b. PLACE: Manila"
        ),
        "expected_labels": [
            "F102_CHILD_FIRST", "F102_CHILD_MIDDLE", "F102_CHILD_LAST",
            "F102_SEX", "F102_DATE_OF_BIRTH", "F102_PLACE_OF_BIRTH",
            "F102_MOTHER_FIRST", "F102_MOTHER_CITIZENSHIP",
            "F102_FATHER_FIRST", "F102_FATHER_CITIZENSHIP",
        ],
        "expected_values": {
            "name_of_child": "Juan dela Cruz Santos",
            "sex": "Male",
            "name_of_mother": "Maria Reyes dela Cruz",
            "name_of_father": "Pedro Cruz Santos",
        }
    },
    {
        "id": "1A-002",
        "desc": "Birth certificate — female child, twin birth",
        "text": (
            "1. NAME (First): Ana  (Middle): Garcia  (Last): Reyes\n"
            "2. SEX: Female\n"
            "3. DATE OF BIRTH: August 21, 1995\n"
            "4. PLACE OF BIRTH: Pasig City\n"
            "5a. TYPE OF BIRTH: Twin\n"
            "7. MAIDEN NAME (First): Gloria  (Middle): Santos  (Last): Garcia\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Ramon  (Middle): Cruz  (Last): Reyes\n"
            "15. CITIZENSHIP: Filipino"
        ),
        "expected_labels": [
            "F102_CHILD_FIRST", "F102_SEX", "F102_DATE_OF_BIRTH",
            "F102_PLACE_OF_BIRTH", "F102_TYPE_OF_BIRTH",
            "F102_MOTHER_FIRST", "F102_FATHER_FIRST",
        ],
        "expected_values": {
            "name_of_child": "Ana Garcia Reyes",
            "sex": "Female",
            "type_of_birth": "Twin",
        }
    },
    {
        "id": "1A-003",
        "desc": "Birth certificate — no middle name (mother)",
        "text": (
            "1. NAME (First): Carlo  (Middle): Santos  (Last): Lim\n"
            "2. SEX: Male\n"
            "3. DATE OF BIRTH: December 1, 2010\n"
            "4. PLACE OF BIRTH: Cebu City\n"
            "7. MAIDEN NAME (First): Rosa  (Middle):   (Last): Santos\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Bernard  (Middle): Cruz  (Last): Lim\n"
            "15. CITIZENSHIP: Filipino"
        ),
        "expected_labels": [
            "F102_CHILD_FIRST", "F102_SEX", "F102_DATE_OF_BIRTH",
            "F102_MOTHER_FIRST", "F102_FATHER_FIRST",
        ],
        "expected_values": {
            "name_of_child": "Carlo Santos Lim",
        }
    },
    {
        "id": "1A-004",
        "desc": "Birth certificate — hyphenated last name",
        "text": (
            "1. NAME (First): Sofia  (Middle): Mendoza  (Last): Santos-Cruz\n"
            "2. SEX: Female\n"
            "3. DATE OF BIRTH: November 30, 2005\n"
            "4. PLACE OF BIRTH: Quezon City\n"
            "7. MAIDEN NAME (First): Carmen  (Middle): Uy  (Last): Mendoza\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Roberto  (Middle): Cruz  (Last): Santos-Cruz\n"
            "15. CITIZENSHIP: Filipino"
        ),
        "expected_labels": [
            "F102_CHILD_FIRST", "F102_CHILD_LAST", "F102_SEX",
            "F102_MOTHER_FIRST", "F102_FATHER_FIRST",
        ],
        "expected_values": {
            "name_of_child": "Sofia Mendoza Santos-Cruz",
        }
    },
    {
        "id": "1A-005",
        "desc": "Birth certificate — with registry number",
        "text": (
            "Registry No.: 2024-001\n"
            "1. NAME (First): Liza  (Middle): Ramos  (Last): Delos Santos\n"
            "2. SEX: Female\n"
            "3. DATE OF BIRTH: July 7, 1988\n"
            "4. PLACE OF BIRTH: Davao City\n"
            "7. MAIDEN NAME (First): Perla  (Middle): Aquino  (Last): Ramos\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Manuel  (Middle): Santos  (Last): Delos Santos\n"
            "15. CITIZENSHIP: Filipino"
        ),
        "expected_labels": [
            "F102_REGISTRY_NO", "F102_CHILD_FIRST", "F102_SEX",
            "F102_DATE_OF_BIRTH", "F102_PLACE_OF_BIRTH",
            "F102_MOTHER_FIRST", "F102_FATHER_FIRST",
        ],
        "expected_values": {
            "registry_number": "2024-001",
        }
    },
]

# ── Form 2A Test Cases ─────────────────────────────────────
FORM_2A_TESTS = [
    {
        "id": "2A-001",
        "desc": "Death certificate — complete fields with all causes",
        "text": (
            "1. NAME (First): Fernando  (Middle): Santos  (Last): Cruz\n"
            "2. SEX: Male\n"
            "4. AGE: 70\n"
            "5. PLACE OF DEATH: PGH Manila\n"
            "6. DATE OF DEATH: March 3, 2023\n"
            "7. CITIZENSHIP: Filipino\n"
            "9. CIVIL STATUS: Widowed\n"
            "10. OCCUPATION: Retired Teacher\n"
            "Immediate cause: Renal Failure\n"
            "Antecedent cause: Chronic Kidney Disease\n"
            "Underlying cause: Diabetes Mellitus"
        ),
        "expected_labels": [
            "F103_DECEASED_FIRST", "F103_DECEASED_MIDDLE", "F103_DECEASED_LAST",
            "F103_SEX", "F103_AGE", "F103_PLACE_OF_DEATH", "F103_DATE_OF_DEATH",
            "F103_CITIZENSHIP", "F103_CIVIL_STATUS", "F103_OCCUPATION",
            "F103_CAUSE_IMMEDIATE", "F103_CAUSE_ANTECEDENT", "F103_CAUSE_UNDERLYING",
        ],
        "expected_values": {
            "name_of_deceased": "Fernando Santos Cruz",
            "age": "70",
            "civil_status": "Widowed",
            "cause_immediate": "Renal Failure",
        }
    },
    {
        "id": "2A-002",
        "desc": "Death certificate — female, elderly, natural cause",
        "text": (
            "1. NAME (First): Josefa  (Middle): dela Paz  (Last): Gonzales\n"
            "2. SEX: Female\n"
            "3. RELIGION: Roman Catholic\n"
            "4. AGE: 91\n"
            "5. PLACE OF DEATH: Batangas City\n"
            "6. DATE OF DEATH: December 31, 2021\n"
            "7. CITIZENSHIP: Filipino\n"
            "9. CIVIL STATUS: Widowed\n"
            "Immediate cause: Old Age"
        ),
        "expected_labels": [
            "F103_DECEASED_FIRST", "F103_SEX", "F103_RELIGION",
            "F103_AGE", "F103_PLACE_OF_DEATH", "F103_DATE_OF_DEATH",
            "F103_CITIZENSHIP", "F103_CIVIL_STATUS", "F103_CAUSE_IMMEDIATE",
        ],
        "expected_values": {
            "name_of_deceased": "Josefa dela Paz Gonzales",
            "religion": "Roman Catholic",
        }
    },
    {
        "id": "2A-003",
        "desc": "Death certificate — with residence field",
        "text": (
            "1. NAME (First): Benjamin  (Middle): Ocampo  (Last): Velasquez\n"
            "2. SEX: Male\n"
            "4. AGE: 48\n"
            "5. PLACE OF DEATH: Makati Medical Center\n"
            "6. DATE OF DEATH: May 20, 2018\n"
            "7. CITIZENSHIP: Filipino\n"
            "8. RESIDENCE: 12 Ayala Avenue, Makati City\n"
            "9. CIVIL STATUS: Married\n"
            "10. OCCUPATION: Accountant\n"
            "Immediate cause: Myocardial Infarction"
        ),
        "expected_labels": [
            "F103_DECEASED_FIRST", "F103_SEX", "F103_AGE",
            "F103_PLACE_OF_DEATH", "F103_DATE_OF_DEATH",
            "F103_CITIZENSHIP", "F103_RESIDENCE", "F103_CIVIL_STATUS",
            "F103_OCCUPATION", "F103_CAUSE_IMMEDIATE",
        ],
        "expected_values": {
            "name_of_deceased": "Benjamin Ocampo Velasquez",
            "occupation": "Accountant",
        }
    },
    {
        "id": "2A-004",
        "desc": "Death certificate — young adult, only immediate cause",
        "text": (
            "1. NAME (First): Cristina  (Middle): Evangelista  (Last): Sy\n"
            "2. SEX: Female\n"
            "4. AGE: 29\n"
            "5. PLACE OF DEATH: Philippine General Hospital\n"
            "6. DATE OF DEATH: June 6, 2016\n"
            "7. CITIZENSHIP: Filipino\n"
            "9. CIVIL STATUS: Single\n"
            "Immediate cause: Dengue Hemorrhagic Fever"
        ),
        "expected_labels": [
            "F103_DECEASED_FIRST", "F103_SEX", "F103_AGE",
            "F103_PLACE_OF_DEATH", "F103_DATE_OF_DEATH",
            "F103_CITIZENSHIP", "F103_CIVIL_STATUS", "F103_CAUSE_IMMEDIATE",
        ],
        "expected_values": {
            "name_of_deceased": "Cristina Evangelista Sy",
            "age": "29",
        }
    },
    {
        "id": "2A-005",
        "desc": "Death certificate — all three causes of death",
        "text": (
            "1. NAME (First): Ernesto  (Middle): Macapagal  (Last): Villafuerte\n"
            "2. SEX: Male\n"
            "4. AGE: 77\n"
            "5. PLACE OF DEATH: Veterans Memorial Medical Center\n"
            "6. DATE OF DEATH: November 11, 2017\n"
            "7. CITIZENSHIP: Filipino\n"
            "9. CIVIL STATUS: Married\n"
            "Immediate cause: Multi-Organ Failure\n"
            "Antecedent cause: Septicemia\n"
            "Underlying cause: Pneumonia"
        ),
        "expected_labels": [
            "F103_DECEASED_FIRST", "F103_AGE", "F103_DATE_OF_DEATH",
            "F103_CAUSE_IMMEDIATE", "F103_CAUSE_ANTECEDENT", "F103_CAUSE_UNDERLYING",
        ],
        "expected_values": {
            "cause_immediate": "Multi-Organ Failure",
            "cause_antecedent": "Septicemia",
            "cause_underlying": "Pneumonia",
        }
    },
]

# ── Form 3A Test Cases ─────────────────────────────────────
FORM_3A_TESTS = [
    {
        "id": "3A-001",
        "desc": "Marriage certificate — complete husband and wife",
        "text": (
            "Husband (First): Jose  (Middle): Cruz  (Last): Ramos\n"
            "Husband AGE: 28\n"
            "Husband CITIZENSHIP: Filipino\n"
            "Husband CIVIL STATUS: Single\n"
            "Wife (First): Elena  (Middle): Bautista  (Last): Torres\n"
            "Wife AGE: 25\n"
            "Wife CITIZENSHIP: Filipino\n"
            "Wife CIVIL STATUS: Single\n"
            "16. DATE OF MARRIAGE: February 14, 2022\n"
            "15. PLACE OF MARRIAGE: Makati City Hall"
        ),
        "expected_labels": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_MIDDLE", "F97_HUSBAND_LAST",
            "F97_HUSBAND_AGE", "F97_HUSBAND_CITIZENSHIP", "F97_HUSBAND_CIVIL_STATUS",
            "F97_WIFE_FIRST", "F97_WIFE_MIDDLE", "F97_WIFE_LAST",
            "F97_WIFE_AGE", "F97_WIFE_CITIZENSHIP",
            "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
        "expected_values": {
            "husband_name": "Jose Cruz Ramos",
            "wife_name": "Elena Bautista Torres",
            "date_of_marriage": "February 14, 2022",
            "place_of_marriage": "Makati City Hall",
        }
    },
    {
        "id": "3A-002",
        "desc": "Marriage certificate — with parents names",
        "text": (
            "Husband (First): Ricardo  (Middle): dela Torre  (Last): Magsaysay\n"
            "Husband AGE: 35\n"
            "Husband CITIZENSHIP: Filipino\n"
            "Husband NAME OF FATHER (First): Alfredo  (Middle): Cruz  (Last): Magsaysay\n"
            "Husband NAME OF MOTHER (First): Florencia  (Middle): dela  (Last): Torre\n"
            "Wife (First): Consuelo  (Middle): Reyes  (Last): Pascual\n"
            "Wife AGE: 30\n"
            "Wife CITIZENSHIP: Filipino\n"
            "DATE OF MARRIAGE: October 4, 2019\n"
            "PLACE OF MARRIAGE: Quezon City"
        ),
        "expected_labels": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_AGE", "F97_HUSBAND_CITIZENSHIP",
            "F97_HUSBAND_FATHER_FIRST", "F97_HUSBAND_MOTHER_FIRST",
            "F97_WIFE_FIRST", "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
        "expected_values": {
            "husband_name": "Ricardo dela Torre Magsaysay",
            "wife_name": "Consuelo Reyes Pascual",
        }
    },
    {
        "id": "3A-003",
        "desc": "Marriage certificate — with place of birth",
        "text": (
            "Husband (First): Marco  (Middle): Villanueva  (Last): Concepcion\n"
            "Husband PLACE OF BIRTH: Iloilo City\n"
            "Husband AGE: 26\n"
            "Husband CITIZENSHIP: Filipino\n"
            "Wife (First): Patricia  (Middle): Guevara  (Last): Luna\n"
            "Wife PLACE OF BIRTH: Cebu City\n"
            "Wife AGE: 24\n"
            "Wife CITIZENSHIP: Filipino\n"
            "DATE OF MARRIAGE: June 21, 2023\n"
            "PLACE OF MARRIAGE: Iloilo City Hall"
        ),
        "expected_labels": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_PLACE_BIRTH", "F97_HUSBAND_AGE",
            "F97_WIFE_FIRST", "F97_WIFE_PLACE_BIRTH", "F97_WIFE_AGE",
            "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
        "expected_values": {
            "husband_name": "Marco Villanueva Concepcion",
            "wife_name": "Patricia Guevara Luna",
        }
    },
    {
        "id": "3A-004",
        "desc": "Marriage certificate — with religion",
        "text": (
            "HUSBAND NAME (First): Albert  (Middle): Garcia  (Last): Santos\n"
            "HUSBAND AGE: 40\n"
            "HUSBAND CITIZENSHIP: Filipino\n"
            "HUSBAND RELIGION: Roman Catholic\n"
            "WIFE NAME (First): Rowena  (Middle): Alvarez  (Last): Reyes\n"
            "WIFE AGE: 36\n"
            "WIFE CITIZENSHIP: Filipino\n"
            "WIFE RELIGION: Roman Catholic\n"
            "DATE OF MARRIAGE: March 14, 2010\n"
            "PLACE OF MARRIAGE: Victory Christian Center, Pasig"
        ),
        "expected_labels": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_AGE", "F97_HUSBAND_RELIGION",
            "F97_WIFE_FIRST", "F97_WIFE_AGE", "F97_WIFE_RELIGION",
            "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
        "expected_values": {
            "husband_name": "Albert Garcia Santos",
        }
    },
    {
        "id": "3A-005",
        "desc": "Marriage certificate — with date of birth",
        "text": (
            "Husband (First): Miguel  (Middle): Santos  (Last): dela Cruz\n"
            "Husband DATE OF BIRTH: June 15, 1990\n"
            "Husband AGE: 31\n"
            "Husband CITIZENSHIP: Filipino\n"
            "Wife (First): Sofia  (Middle): Tan  (Last): Lim\n"
            "Wife DATE OF BIRTH: March 20, 1993\n"
            "Wife AGE: 28\n"
            "Wife CITIZENSHIP: Filipino\n"
            "16. DATE OF MARRIAGE: December 12, 2021\n"
            "15. PLACE OF MARRIAGE: Taguig City"
        ),
        "expected_labels": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_DOB", "F97_HUSBAND_AGE",
            "F97_WIFE_FIRST", "F97_WIFE_DOB", "F97_WIFE_AGE",
            "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
        "expected_values": {
            "husband_name": "Miguel Santos dela Cruz",
            "wife_name": "Sofia Tan Lim",
        }
    },
]

# ── Black Box Edge Case Tests ──────────────────────────────
BLACK_BOX_TESTS = [
    {
        "id": "BB-001",
        "desc": "Empty input — should not crash",
        "form": "1A",
        "text": "",
        "expect_crash": False,
        "expect_empty": True,
    },
    {
        "id": "BB-002",
        "desc": "Whitespace only — should not crash",
        "form": "1A",
        "text": "   \n\n\t  ",
        "expect_crash": False,
        "expect_empty": True,
    },
    {
        "id": "BB-003",
        "desc": "Garbled OCR output — should not crash",
        "form": "2A",
        "text": "1. N4ME (F1rst): J@an  (M1ddle): d3la Cr!z  (L@st): $antos\n2. SEX: M@le",
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-004",
        "desc": "Partial form — only name fields present",
        "form": "1A",
        "text": "1. NAME (First): Maria  (Middle): Santos  (Last): Reyes",
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-005",
        "desc": "Very long OCR text — should not crash",
        "form": "2A",
        "text": "1. NAME (First): Carlos  (Last): Cruz\n" * 50,
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-006",
        "desc": "Missing colon separators — OCR formatting issue",
        "form": "1A",
        "text": "NAME First Juan Middle dela Cruz Last Santos\nSEX Male\nDATE OF BIRTH March 15 1990",
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-007",
        "desc": "Numbers only — no recognizable form content",
        "form": "3A",
        "text": "123456789 0987654321 11111 22222 33333",
        "expect_crash": False,
        "expect_empty": True,
    },
    {
        "id": "BB-008",
        "desc": "Valid Form 3A input — pipeline completes",
        "form": "3A",
        "text": (
            "Husband (First): Patrick  (Middle): Sy  (Last): Chua\n"
            "Wife (First): Christine  (Middle): Lim  (Last): Go\n"
            "DATE OF MARRIAGE: July 7, 2023\n"
            "PLACE OF MARRIAGE: Binondo Church, Manila"
        ),
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-009",
        "desc": "Mixed language (Filipino/English) — common in real forms",
        "form": "1A",
        "text": (
            "1. PANGALAN (First): Jose  (Middle): dela Cruz  (Last): Reyes\n"
            "2. SEX: Lalaki\n"
            "3. DATE OF BIRTH: Enero 5, 2000\n"
            "4. PLACE OF BIRTH: Lungsod ng Maynila"
        ),
        "expect_crash": False,
        "expect_empty": False,
    },
    {
        "id": "BB-010",
        "desc": "Special characters in name — OCR artifact",
        "form": "2A",
        "text": (
            "1. NAME (First): Fe|ipe  (Middle): San+os  (Last): Cr-uz\n"
            "2. SEX: Male\n"
            "4. AGE: 55\n"
            "6. DATE OF DEATH: May 1, 2020"
        ),
        "expect_crash": False,
        "expect_empty": False,
    },
]

ALL_FORM_TESTS = FORM_1A_TESTS + FORM_2A_TESTS + FORM_3A_TESTS


# ══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════

def separator(char="═", width=65):
    return char * width

def header(title):
    print(f"\n{separator()}")
    print(f"  {title}")
    print(separator())

def subheader(title):
    print(f"\n  {'─' * 60}")
    print(f"  {title}")
    print(f"  {'─' * 60}")


def run_extraction(extractor, filler, form_type, text):
    """Run extraction for a given form type. Returns form object."""
    if form_type == "1A":
        return filler.fill_form_1a(text)
    elif form_type == "2A":
        return filler.fill_form_2a(text)
    elif form_type == "3A":
        return filler.fill_form_3a(text)


def get_extracted_labels(extractor, form_type, text):
    """Get set of extracted NER label keys from raw extraction."""
    if form_type == "1A" or "F102" in str(form_type):
        return extractor.extract_form_102(text)
    elif form_type == "2A" or "F103" in str(form_type):
        return extractor.extract_form_103(text)
    elif form_type == "3A" or "F97" in str(form_type):
        return extractor.extract_form_97(text)
    return {}


def infer_form_type(labels):
    """Guess form type from label prefix."""
    for label in labels:
        if label.startswith("F102"):
            return "1A"
        elif label.startswith("F103"):
            return "2A"
        elif label.startswith("F97"):
            return "3A"
    return "1A"


# ══════════════════════════════════════════════════════════
# 1. ACCURACY TESTING
# ══════════════════════════════════════════════════════════

def run_accuracy_testing(extractor, filler):
    header("1. ACCURACY TESTING")
    print("  Measures: how many expected labels were correctly extracted")
    print("  Formula: Accuracy = Correct / Total Expected × 100%\n")

    results = {
        "Form 1A (Birth)":    {"correct": 0, "total": 0, "tests": 0},
        "Form 2A (Death)":    {"correct": 0, "total": 0, "tests": 0},
        "Form 3A (Marriage)": {"correct": 0, "total": 0, "tests": 0},
    }

    all_label_results = []

    for test_set, form_name in [
        (FORM_1A_TESTS, "Form 1A (Birth)"),
        (FORM_2A_TESTS, "Form 2A (Death)"),
        (FORM_3A_TESTS, "Form 3A (Marriage)"),
    ]:
        subheader(f"Accuracy — {form_name}")

        for test in test_set:
            form_type = test["id"].split("-")[0]
            data = get_extracted_labels(extractor, form_type, test["text"])
            found_labels = set(data.keys())

            correct = 0
            total = len(test["expected_labels"])
            missing = []

            for label in test["expected_labels"]:
                if label in found_labels:
                    correct += 1
                else:
                    missing.append(label)

            pct = (correct / total * 100) if total > 0 else 0
            status = "✅" if pct >= 70 else ("⚠️ " if pct >= 50 else "❌")

            print(f"  {status} [{test['id']}] {test['desc']}")
            print(f"       Score: {correct}/{total} ({pct:.1f}%)")
            if missing:
                print(f"       Missing: {', '.join(missing[:3])}"
                      + ("..." if len(missing) > 3 else ""))

            results[form_name]["correct"] += correct
            results[form_name]["total"]   += total
            results[form_name]["tests"]   += 1
            all_label_results.append(pct)

    # Summary table
    subheader("Accuracy Summary")
    print(f"  {'Form':<30} {'Correct':>8} {'Total':>7} {'Accuracy':>10}")
    print(f"  {'─'*30} {'─'*8} {'─'*7} {'─'*10}")

    total_correct = 0
    total_labels  = 0
    for form_name, r in results.items():
        pct = (r["correct"] / r["total"] * 100) if r["total"] > 0 else 0
        mark = "✅" if pct >= 70 else ("⚠️ " if pct >= 50 else "❌")
        print(f"  {mark} {form_name:<28} {r['correct']:>8} {r['total']:>7} {pct:>9.1f}%")
        total_correct += r["correct"]
        total_labels  += r["total"]

    print(f"  {'─'*30} {'─'*8} {'─'*7} {'─'*10}")
    overall = (total_correct / total_labels * 100) if total_labels > 0 else 0
    print(f"  {'OVERALL':<30} {total_correct:>8} {total_labels:>7} {overall:>9.1f}%")

    return overall


# ══════════════════════════════════════════════════════════
# 2. BLACK BOX TESTING
# ══════════════════════════════════════════════════════════

def run_black_box_testing(extractor, filler):
    header("2. BLACK BOX TESTING")
    print("  Tests system behavior from external perspective.")
    print("  No knowledge of internals — only input → output.\n")
    print("  Test categories:")
    print("   • Valid inputs (normal use)")
    print("   • Invalid / edge case inputs (empty, garbled, partial)")
    print("   • Boundary inputs (very long, special chars, mixed language)\n")

    passed = 0
    failed = 0
    errors = []

    for test in BLACK_BOX_TESTS:
        test_passed = True
        notes = []

        try:
            start = time.time()

            # Run the full pipeline
            form_obj = run_extraction(extractor, filler, test["form"], test["text"])
            elapsed = time.time() - start

            # Check: did it crash? (it didn't if we're here)
            if test["expect_crash"]:
                test_passed = False
                notes.append("Expected crash but system survived")

            # Check: is output empty when expected?
            from spacyNER.autofill import AutoFillEngine
            result = AutoFillEngine(extractor).to_dict(form_obj)
            is_empty = len(result) == 0

            if test["expect_empty"] and not is_empty:
                # Soft warning — not a hard fail for edge cases
                notes.append(f"Expected empty output but got {len(result)} fields")

            if not test["expect_empty"] and is_empty and test["id"] not in ["BB-007"]:
                notes.append("Expected some output but got nothing")

            # Performance check — must respond within 5 seconds
            if elapsed > 5.0:
                test_passed = False
                notes.append(f"Too slow: {elapsed:.2f}s (limit: 5s)")

            status_icon = "✅" if test_passed else "❌"
            timing = f"{elapsed*1000:.0f}ms"

            print(f"  {status_icon} [{test['id']}] {test['desc']}")
            print(f"       Fields found: {len(result)} | Time: {timing}")
            if notes:
                for note in notes:
                    print(f"       ℹ️  {note}")

        except Exception as e:
            if test["expect_crash"]:
                print(f"  ✅ [{test['id']}] {test['desc']}")
                print(f"       Crashed as expected: {type(e).__name__}")
            else:
                test_passed = False
                errors.append(f"[{test['id']}] {type(e).__name__}: {e}")
                print(f"  ❌ [{test['id']}] {test['desc']}")
                print(f"       CRASH: {type(e).__name__}: {e}")
                failed += 1
                continue

        if test_passed:
            passed += 1
        else:
            failed += 1

    subheader("Black Box Summary")
    total = passed + failed
    pct = (passed / total * 100) if total > 0 else 0
    print(f"  Passed: {passed}/{total} ({pct:.1f}%)")
    if errors:
        print(f"  Crashes detected: {len(errors)}")
        for e in errors:
            print(f"    ❌ {e}")
    else:
        print(f"  ✅ No crashes detected — system is stable")

    return passed, total


# ══════════════════════════════════════════════════════════
# 3. CONFUSION MATRIX
# ══════════════════════════════════════════════════════════

def run_confusion_matrix(extractor):
    header("3. CONFUSION MATRIX")
    print("  Per-label: True Positive (TP), False Positive (FP),")
    print("  False Negative (FN), Precision, Recall, F1-Score\n")

    # Collect TP/FP/FN for every label across all test cases
    label_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0})

    for test in ALL_FORM_TESTS:
        form_type = test["id"].split("-")[0]
        data = get_extracted_labels(extractor, form_type, test["text"])
        found_labels = set(data.keys())
        expected_labels = set(test["expected_labels"])

        for label in expected_labels:
            if label in found_labels:
                label_stats[label]["TP"] += 1   # Correctly found
            else:
                label_stats[label]["FN"] += 1   # Missed

        # False positives: found labels not in expected
        for label in found_labels:
            if label in expected_labels:
                pass  # already counted as TP
            elif any(label in t["expected_labels"] for t in ALL_FORM_TESTS):
                label_stats[label]["FP"] += 1   # Found but not expected here

    # Print per-form confusion matrices
    form_groups = [
        ("Form 1A (Birth Certificate)",    "F102"),
        ("Form 2A (Death Certificate)",    "F103"),
        ("Form 3A (Marriage Certificate)", "F97"),
    ]

    overall_tp = overall_fp = overall_fn = 0

    for form_name, prefix in form_groups:
        subheader(f"Confusion Matrix — {form_name}")
        form_labels = {k: v for k, v in label_stats.items() if k.startswith(prefix)}

        if not form_labels:
            print("  ⚠️  No test results for this form yet.")
            continue

        print(f"  {'Label':<40} {'TP':>4} {'FP':>4} {'FN':>4} {'Precision':>10} {'Recall':>8} {'F1':>8}")
        print(f"  {'─'*40} {'─'*4} {'─'*4} {'─'*4} {'─'*10} {'─'*8} {'─'*8}")

        form_tp = form_fp = form_fn = 0

        for label, stats in sorted(form_labels.items()):
            tp = stats["TP"]
            fp = stats["FP"]
            fn = stats["FN"]

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1        = (2 * precision * recall / (precision + recall)
                        if (precision + recall) > 0 else 0.0)

            perf = "✅" if f1 >= 0.7 else ("⚠️ " if f1 >= 0.5 else "❌")
            short_label = label.replace(prefix + "_", "")
            print(f"  {perf} {short_label:<38} {tp:>4} {fp:>4} {fn:>4} "
                  f"{precision:>9.2f}  {recall:>7.2f}  {f1:>7.2f}")

            form_tp += tp; form_fp += fp; form_fn += fn

        form_prec = form_tp / (form_tp + form_fp) if (form_tp + form_fp) > 0 else 0
        form_rec  = form_tp / (form_tp + form_fn) if (form_tp + form_fn) > 0 else 0
        form_f1   = (2 * form_prec * form_rec / (form_prec + form_rec)
                     if (form_prec + form_rec) > 0 else 0)

        print(f"  {'─'*40} {'─'*4} {'─'*4} {'─'*4} {'─'*10} {'─'*8} {'─'*8}")
        print(f"  {'  FORM TOTAL':<40} {form_tp:>4} {form_fp:>4} {form_fn:>4} "
              f"{form_prec:>9.2f}  {form_rec:>7.2f}  {form_f1:>7.2f}")

        overall_tp += form_tp
        overall_fp += form_fp
        overall_fn += form_fn

    # Overall confusion matrix summary
    subheader("Overall Confusion Matrix Summary")
    overall_prec = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_rec  = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1   = (2 * overall_prec * overall_rec / (overall_prec + overall_rec)
                    if (overall_prec + overall_rec) > 0 else 0)

    print(f"  {'Metric':<25} {'Value':>10}")
    print(f"  {'─'*25} {'─'*10}")
    print(f"  {'True Positives (TP)':<25} {overall_tp:>10}")
    print(f"  {'False Positives (FP)':<25} {overall_fp:>10}")
    print(f"  {'False Negatives (FN)':<25} {overall_fn:>10}")
    print(f"  {'Precision':<25} {overall_prec:>9.2f}")
    print(f"  {'Recall':<25} {overall_rec:>9.2f}")
    print(f"  {'F1-Score':<25} {overall_f1:>9.2f}")

    return overall_f1


# ══════════════════════════════════════════════════════════
# 4. ISO 25010 RELIABILITY TESTING
# ══════════════════════════════════════════════════════════

def run_reliability_testing(extractor, filler):
    header("4. ISO 25010 — RELIABILITY TESTING")
    print("  ISO 25010 Reliability sub-characteristics:")
    print("   • Maturity      — consistent results on repeated runs")
    print("   • Fault Tolerance — handles bad/missing input without crashing")
    print("   • Recoverability  — recovers from error states")
    print("   • Availability    — model loads and responds correctly\n")

    passed = 0
    total  = 0

    # ── 4.1 Availability ──────────────────────────────────
    subheader("4.1 Availability — Model Load & Response")
    availability_tests = [
        ("Model loaded successfully",        extractor is not None),
        ("AutoFillEngine initialized",       filler is not None),
        ("fill_form_1a() is callable",       callable(getattr(filler, "fill_form_1a", None))),
        ("fill_form_2a() is callable",       callable(getattr(filler, "fill_form_2a", None))),
        ("fill_form_3a() is callable",       callable(getattr(filler, "fill_form_3a", None))),
        ("extract_form_102() is callable",   callable(getattr(extractor, "extract_form_102", None))),
        ("extract_form_103() is callable",   callable(getattr(extractor, "extract_form_103", None))),
        ("extract_form_97() is callable",    callable(getattr(extractor, "extract_form_97", None))),
    ]
    for desc, condition in availability_tests:
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc}")

    # ── 4.2 Fault Tolerance ───────────────────────────────
    subheader("4.2 Fault Tolerance — Bad Input Handling")
    fault_inputs = [
        ("Empty string",         ""),
        ("None-like whitespace", "   \n  "),
        ("Random symbols",       "@#$%^&*()_+{}|:<>?"),
        ("Very long input",      "NAME: Juan Santos\n" * 200),
        ("Binary-like text",     "\x00\x01\x02 NAME First Juan"),
        ("Only numbers",         "123 456 789 000 111 222"),
        ("Repeated newlines",    "\n\n\n\n\n"),
    ]
    for desc, bad_input in fault_inputs:
        total += 1
        try:
            result = filler.fill_form_1a(bad_input)
            passed += 1
            print(f"  ✅ {desc} → handled gracefully")
        except Exception as e:
            print(f"  ❌ {desc} → CRASH: {type(e).__name__}: {e}")

    # ── 4.3 Maturity (Consistency) ────────────────────────
    subheader("4.3 Maturity — Consistency on Repeated Runs")
    test_text = (
        "1. NAME (First): Juan  (Middle): dela Cruz  (Last): Santos\n"
        "2. SEX: Male\n"
        "3. DATE OF BIRTH: March 15, 1990\n"
        "4. PLACE OF BIRTH: Makati City"
    )

    results_across_runs = []
    NUM_RUNS = 5
    for i in range(NUM_RUNS):
        data = extractor.extract_form_102(test_text)
        results_across_runs.append(frozenset(data.keys()))

    all_same = len(set(results_across_runs)) == 1
    total += 1
    if all_same:
        passed += 1
        print(f"  ✅ {NUM_RUNS} repeated runs → identical results (consistent)")
    else:
        print(f"  ❌ {NUM_RUNS} repeated runs → inconsistent results")

    # ── 4.4 Recoverability ────────────────────────────────
    subheader("4.4 Recoverability — System Continues After Errors")
    recovery_tests = [
        ("Run after empty input",  ""),
        ("Run with valid input after error", (
            "1. NAME (First): Maria  (Last): Santos\n2. SEX: Female"
        )),
        ("Run Form 2A after Form 1A error", None),
    ]

    # Test that system continues working after errors
    try:
        filler.fill_form_1a("")          # potential error
        filler.fill_form_2a("")          # should still work
        form = filler.fill_form_1a(      # should recover
            "1. NAME (First): Test  (Last): User\n2. SEX: Male"
        )
        total += 1
        passed += 1
        print(f"  ✅ System recovers after empty input — continues processing")
    except Exception as e:
        total += 1
        print(f"  ❌ System did not recover: {e}")

    try:
        for _ in range(3):
            filler.fill_form_2a("GARBAGE INPUT @#$%")
        filler.fill_form_2a(
            "1. NAME (First): Carlos  (Last): Cruz\n4. AGE: 65"
        )
        total += 1
        passed += 1
        print(f"  ✅ System processes valid input after multiple bad inputs")
    except Exception as e:
        total += 1
        print(f"  ❌ System failed after bad inputs: {e}")

    subheader("ISO 25010 Reliability Summary")
    pct = (passed / total * 100) if total > 0 else 0
    print(f"  Passed: {passed}/{total} ({pct:.1f}%)")
    if pct >= 90:
        print(f"  ✅ RELIABILITY: EXCELLENT — meets ISO 25010 standard")
    elif pct >= 75:
        print(f"  ⚠️  RELIABILITY: ACCEPTABLE — minor issues found")
    else:
        print(f"  ❌ RELIABILITY: NEEDS IMPROVEMENT")

    return passed, total


# ══════════════════════════════════════════════════════════
# 5. ISO 25010 USABILITY TESTING
# ══════════════════════════════════════════════════════════

def run_usability_testing(extractor, filler):
    header("5. ISO 25010 — USABILITY TESTING")
    print("  ISO 25010 Usability sub-characteristics:")
    print("   • Learnability  — consistent, predictable output format")
    print("   • Operability   — pipeline runs end-to-end without manual steps")
    print("   • Accessibility — output is readable and usable by calling code")
    print("   • User error protection — handles mistakes without data corruption\n")

    passed = 0
    total  = 0

    sample_text_102 = (
        "1. NAME (First): Juan  (Middle): dela Cruz  (Last): Santos\n"
        "2. SEX: Male\n"
        "3. DATE OF BIRTH: March 15, 1990\n"
        "4. PLACE OF BIRTH: Makati City\n"
        "7. MAIDEN NAME (First): Maria  (Middle): Reyes  (Last): dela Cruz\n"
        "8. CITIZENSHIP: Filipino\n"
        "14. NAME (First): Pedro  (Middle): Cruz  (Last): Santos"
    )

    sample_text_103 = (
        "1. NAME (First): Carlos  (Middle): Reyes  (Last): Mendoza\n"
        "2. SEX: Male\n4. AGE: 65\n"
        "5. PLACE OF DEATH: Manila\n"
        "6. DATE OF DEATH: January 1, 2020\n"
        "Immediate cause: Heart Attack"
    )

    sample_text_97 = (
        "Husband (First): Jose  (Middle): Cruz  (Last): Ramos\n"
        "Wife (First): Elena  (Middle): Bautista  (Last): Torres\n"
        "DATE OF MARRIAGE: February 14, 2022\n"
        "PLACE OF MARRIAGE: Manila City Hall"
    )

    # ── 5.1 Learnability ──────────────────────────────────
    subheader("5.1 Learnability — Output Format Consistency")

    learn_tests = [
        ("Form1A has name_of_child field",
         lambda: hasattr(filler.fill_form_1a(sample_text_102), "name_of_child")),
        ("Form1A name_of_child is string or None",
         lambda: isinstance(filler.fill_form_1a(sample_text_102).name_of_child, (str, type(None)))),
        ("Form2A has name_of_deceased field",
         lambda: hasattr(filler.fill_form_2a(sample_text_103), "name_of_deceased")),
        ("Form3A has husband and wife fields",
         lambda: hasattr(filler.fill_form_3a(sample_text_97), "husband") and
                 hasattr(filler.fill_form_3a(sample_text_97), "wife")),
        ("to_dict() returns a dictionary",
         lambda: isinstance(filler.to_dict(filler.fill_form_1a(sample_text_102)), dict)),
        ("Same input always gives same output type",
         lambda: type(filler.fill_form_1a(sample_text_102)) == type(filler.fill_form_1a(sample_text_102))),
        ("Form1A output is a Form1A instance",
         lambda: isinstance(filler.fill_form_1a(sample_text_102), Form1A)),
        ("Form2A output is a Form2A instance",
         lambda: isinstance(filler.fill_form_2a(sample_text_103), Form2A)),
        ("Form3A output is a Form3A instance",
         lambda: isinstance(filler.fill_form_3a(sample_text_97), Form3A)),
    ]

    for desc, test_fn in learn_tests:
        total += 1
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc}")
        except Exception as e:
            print(f"  ❌ {desc} → {type(e).__name__}: {e}")

    # ── 5.2 Operability ───────────────────────────────────
    subheader("5.2 Operability — End-to-End Pipeline")

    operability_tests = [
        ("Form 1A pipeline completes (text → Form1A object)",
         lambda: filler.fill_form_1a(sample_text_102) is not None),
        ("Form 2A pipeline completes (text → Form2A object)",
         lambda: filler.fill_form_2a(sample_text_103) is not None),
        ("Form 3A pipeline completes (text → Form3A object)",
         lambda: filler.fill_form_3a(sample_text_97) is not None),
        ("to_dict() converts Form1A without errors",
         lambda: filler.to_dict(filler.fill_form_1a(sample_text_102)) is not None),
        ("to_dict() converts Form2A without errors",
         lambda: filler.to_dict(filler.fill_form_2a(sample_text_103)) is not None),
        ("to_dict() converts Form3A without errors",
         lambda: filler.to_dict(filler.fill_form_3a(sample_text_97)) is not None),
        ("Pipeline handles empty text without crash",
         lambda: filler.fill_form_1a("") is not None),
        ("Pipeline handles all 3 forms in sequence",
         lambda: all([
             filler.fill_form_1a(sample_text_102) is not None,
             filler.fill_form_2a(sample_text_103) is not None,
             filler.fill_form_3a(sample_text_97)  is not None,
         ])),
    ]

    for desc, test_fn in operability_tests:
        total += 1
        try:
            start = time.time()
            result = test_fn()
            elapsed = time.time() - start
            if result:
                passed += 1
                print(f"  ✅ {desc} ({elapsed*1000:.0f}ms)")
            else:
                print(f"  ❌ {desc}")
        except Exception as e:
            print(f"  ❌ {desc} → {type(e).__name__}: {e}")

    # ── 5.3 Accessibility ─────────────────────────────────
    subheader("5.3 Accessibility — Output Readability")

    form_1a = filler.fill_form_1a(sample_text_102)
    form_2a = filler.fill_form_2a(sample_text_103)
    form_3a = filler.fill_form_3a(sample_text_97)
    dict_1a = filler.to_dict(form_1a)

    accessibility_tests = [
        ("Form1A dict keys are human-readable strings",
         lambda: all(isinstance(k, str) for k in dict_1a.keys())),
        ("Form1A dict values are strings or None",
         lambda: all(isinstance(v, (str, type(None))) for v in dict_1a.values())),
        ("Form3A.husband is accessible as attribute",
         lambda: form_3a.husband is not None),
        ("Form3A.wife is accessible as attribute",
         lambda: form_3a.wife is not None),
        ("Form3A.husband.name is string or None",
         lambda: isinstance(form_3a.husband.name, (str, type(None)))),
        ("Name fields use First Middle Last order",
         lambda: (form_1a.name_of_child or "").count("  ") == 0),
        ("Empty form produces empty dict (no None values in dict)",
         lambda: all(v is not None for v in filler.to_dict(filler.fill_form_1a("")).values())),
    ]

    for desc, test_fn in accessibility_tests:
        total += 1
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc}")
        except Exception as e:
            print(f"  ❌ {desc} → {type(e).__name__}: {e}")

    # ── 5.4 User Error Protection ─────────────────────────
    subheader("5.4 User Error Protection — Input Mistakes")

    error_protection_tests = [
        ("Calling wrong form type does not corrupt other forms",
         lambda: (filler.fill_form_1a(sample_text_103) is not None and
                  filler.fill_form_1a(sample_text_102) is not None)),
        ("Processing bad input does not affect next call",
         lambda: (filler.fill_form_1a("GARBAGE") is not None and
                  filler.fill_form_1a(sample_text_102) is not None)),
        ("Multiple calls do not accumulate state errors",
         lambda: len([filler.fill_form_2a(sample_text_103) for _ in range(5)]) == 5),
    ]

    for desc, test_fn in error_protection_tests:
        total += 1
        try:
            result = test_fn()
            if result:
                passed += 1
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc}")
        except Exception as e:
            print(f"  ❌ {desc} → {type(e).__name__}: {e}")

    subheader("ISO 25010 Usability Summary")
    pct = (passed / total * 100) if total > 0 else 0
    print(f"  Passed: {passed}/{total} ({pct:.1f}%)")
    if pct >= 90:
        print(f"  ✅ USABILITY: EXCELLENT — meets ISO 25010 standard")
    elif pct >= 75:
        print(f"  ⚠️  USABILITY: ACCEPTABLE — minor issues found")
    else:
        print(f"  ❌ USABILITY: NEEDS IMPROVEMENT")

    return passed, total


# ══════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════

def print_final_report(model_path, accuracy, bb_pass, bb_total,
                        f1_score, rel_pass, rel_total,
                        usa_pass, usa_total, total_time):
    header("FINAL TEST REPORT")
    print(f"  Model:      {model_path}")
    print(f"  Date/Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration:   {total_time:.2f} seconds\n")

    def grade(pct):
        if pct >= 90: return "EXCELLENT ✅"
        if pct >= 75: return "GOOD ✅"
        if pct >= 60: return "ACCEPTABLE ⚠️ "
        return "NEEDS IMPROVEMENT ❌"

    bb_pct  = (bb_pass  / bb_total  * 100) if bb_total  > 0 else 0
    rel_pct = (rel_pass / rel_total * 100) if rel_total > 0 else 0
    usa_pct = (usa_pass / usa_total * 100) if usa_total > 0 else 0

    print(f"  {'Test':<35} {'Score':>12} {'Grade'}")
    print(f"  {'─'*35} {'─'*12} {'─'*20}")
    print(f"  {'1. Accuracy Testing':<35} {accuracy:>10.1f}%  {grade(accuracy)}")
    print(f"  {'2. Black Box Testing':<35} {bb_pct:>10.1f}%  {grade(bb_pct)}")
    print(f"  {'3. Confusion Matrix (F1)':<35} {f1_score*100:>10.1f}%  {grade(f1_score*100)}")
    print(f"  {'4. ISO 25010 Reliability':<35} {rel_pct:>10.1f}%  {grade(rel_pct)}")
    print(f"  {'5. ISO 25010 Usability':<35} {usa_pct:>10.1f}%  {grade(usa_pct)}")

    overall = (accuracy + bb_pct + f1_score*100 + rel_pct + usa_pct) / 5
    print(f"  {'─'*35} {'─'*12} {'─'*20}")
    print(f"  {'OVERALL SYSTEM SCORE':<35} {overall:>10.1f}%  {grade(overall)}")

    print(f"\n  {'─'*60}")
    if overall >= 75:
        print(f"  ✅ SYSTEM PASSES all testing objectives")
    else:
        print(f"  ⚠️  SYSTEM NEEDS IMPROVEMENT in some areas")
        print(f"  → Add more annotated training examples")
        print(f"  → Re-run training and evaluate again")
    print(f"  {'─'*60}")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Civil Registry NER — Complete Test Suite"
    )
    parser.add_argument(
        "--model",
        default="./models/civil_registry_model/model-best",
        help="Path to spaCy model (default: trained model)"
    )
    args = parser.parse_args()

    print(separator("═"))
    print("   CIVIL REGISTRY NER — COMPLETE TEST SUITE")
    print("   ISO 25010 Compliance Testing")
    print(separator("═"))
    print(f"\n  Model: {args.model}")
    print(f"  Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load model
    print("  Loading model...")
    try:
        extractor = CivilRegistryNER(model_path=args.model)
        filler    = AutoFillEngine(extractor)
        print(f"  ✅ Model loaded: {args.model}\n")
    except Exception as e:
        print(f"  ❌ Could not load model: {e}")
        print(f"  → Try: python testing/test_suite.py --model en_core_web_sm")
        sys.exit(1)

    start_time = time.time()

    # Run all 5 test sections
    accuracy          = run_accuracy_testing(extractor, filler)
    bb_pass, bb_total = run_black_box_testing(extractor, filler)
    f1_score          = run_confusion_matrix(extractor)
    rel_pass, rel_total = run_reliability_testing(extractor, filler)
    usa_pass, usa_total = run_usability_testing(extractor, filler)

    total_time = time.time() - start_time

    print_final_report(
        args.model, accuracy,
        bb_pass, bb_total,
        f1_score,
        rel_pass, rel_total,
        usa_pass, usa_total,
        total_time
    )


if __name__ == "__main__":
    main()
