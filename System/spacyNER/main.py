# ============================================================
# main.py
# ------------------------------------------------------------
# Entry point — run the full pipeline with sample form texts.
#
# How to run:
#   python main.py
#
# For real scanned forms:
#   from spacyNER.ocr import scan_form
#   text = scan_form("path/to/form_102.jpg")
# ============================================================

from spacyNER.extractor import CivilRegistryNER
from spacyNER.autofill  import AutoFillEngine

MODEL_PATH = "en_core_web_sm"
# After fine-tuning:
# MODEL_PATH = "./models/civil_registry_model/model-best"

extractor = CivilRegistryNER(model_path=MODEL_PATH)
filler    = AutoFillEngine(extractor)

print("=" * 65)
print("   CIVIL REGISTRY NER — AUTO-FILL PIPELINE")
print("=" * 65)


# ──────────────────────────────────────────────────────────
# CERTIFICATIONS PAGE — Form 102 (Certificate of Live Birth)
# ──────────────────────────────────────────────────────────
FORM_102_OCR = """
Registry No.: 2024-001
Province: Metro Manila
City/Municipality: Makati City

1. NAME (First): Juan  (Middle): dela Cruz  (Last): Santos
2. SEX: Male
3. DATE OF BIRTH: March 15, 1990
4. PLACE OF BIRTH: Ospital ng Makati, Makati City, Metro Manila
5a. TYPE OF BIRTH: Single
5c. BIRTH ORDER: First

MOTHER:
7. MAIDEN NAME (First): Maria  (Middle): Reyes  (Last): dela Cruz
8. CITIZENSHIP: Filipino
9. RELIGION/RELIGIOUS SECT: Roman Catholic
13. RESIDENCE: 123 Rizal Street, Barangay San Antonio, Makati City

FATHER:
14. NAME (First): Pedro  (Middle): Cruz  (Last): Santos
15. CITIZENSHIP: Filipino
16. RELIGION/RELIGIOUS SECT: Roman Catholic
19. RESIDENCE: 123 Rizal Street, Barangay San Antonio, Makati City

MARRIAGE OF PARENTS:
20a. DATE: June 10, 1985
20b. PLACE: Manila City, Metro Manila, Philippines
"""

# ──────────────────────────────────────────────────────────
# CERTIFICATIONS PAGE — Form 103 (Certificate of Death)
# ──────────────────────────────────────────────────────────
FORM_103_OCR = """
Registry No.: 2024-045
Province: Metro Manila
City/Municipality: Quezon City

1. NAME (First): Carlos  (Middle): Reyes  (Last): Mendoza
2. SEX: Male
3. RELIGION: Roman Catholic
4. AGE: 65
5. PLACE OF DEATH: Quezon City Medical Center, Quezon City, Metro Manila
6. DATE OF DEATH: September 2, 2020
7. CITIZENSHIP: Filipino
8. RESIDENCE: 45 Mabini Street, Quezon City, Metro Manila
9. CIVIL STATUS: Married
10. OCCUPATION: Retired Teacher

17. CAUSES OF DEATH:
Immediate cause: Cardiac Arrest
Antecedent cause: Hypertensive Cardiovascular Disease
Underlying cause: Hypertension
"""

# ──────────────────────────────────────────────────────────
# CERTIFICATIONS PAGE — Form 97 (Certificate of Marriage)
# ──────────────────────────────────────────────────────────
FORM_97_OCR = """
Registry No.: 2024-088
Province: Metro Manila
City/Municipality: Makati City

HUSBAND:
1. NAME (First): Jose  (Middle): Cruz  (Last): Ramos
2a. DATE OF BIRTH: June 10, 1994
2b. AGE: 28
3. PLACE OF BIRTH: Manila, Metro Manila, Philippines
4a. SEX: Male
4b. CITIZENSHIP: Filipino
5. RESIDENCE: 123 Rizal Street, Makati City, Metro Manila
6. RELIGION/RELIGIOUS SECT: Roman Catholic
7. CIVIL STATUS: Single
8. NAME OF FATHER (First): Roberto  (Middle): Santos  (Last): Ramos
9. CITIZENSHIP: Filipino
10. NAME OF MOTHER (First): Conchita  (Middle): Dela  (Last): Rosa
11. CITIZENSHIP: Filipino

WIFE:
1. NAME (First): Elena  (Middle): Bautista  (Last): Torres
2a. DATE OF BIRTH: April 20, 1997
2b. AGE: 25
3. PLACE OF BIRTH: Cebu City, Cebu, Philippines
4a. SEX: Female
4b. CITIZENSHIP: Filipino
5. RESIDENCE: 456 Mabini Avenue, Cebu City, Cebu
6. RELIGION/RELIGIOUS SECT: Roman Catholic
7. CIVIL STATUS: Single
8. NAME OF FATHER (First): Ernesto  (Middle): Lim  (Last): Torres
9. CITIZENSHIP: Filipino
10. NAME OF MOTHER (First): Felicitas  (Middle): Cruz  (Last): Bautista
11. CITIZENSHIP: Filipino

15. PLACE OF MARRIAGE: Makati City Hall, Makati City, Metro Manila
16. DATE OF MARRIAGE: February 14, 2022
"""

# ──────────────────────────────────────────────────────────
# MARRIAGE LICENSE PAGE — Groom's Birth Certificate (Male/PSA)
# MNB classify_sex() → "GROOM"  (SEX: Male)
# Uses F90_GROOM_* labels
# ──────────────────────────────────────────────────────────
FORM_90_GROOM_OCR = """
Municipal Form No. 102 Certificate of Live Birth
PSA Registry No.: 2024-BC-001
Date of Registration: January 10, 2024

GROOM
Groom (First): Jose  Groom (Middle): Santos  Groom (Last): Ramos
Groom Date of Birth: March 15, 1995
Groom Age: 29
Groom Place of Birth: Manila
Groom Sex: Male
Groom Citizenship: Filipino
Groom Residence: 123 Rizal Street Makati City

Groom Father (First): Pedro  Groom Father (Middle): dela Cruz  Groom Father (Last): Villanueva
Groom Father Citizenship: Filipino

Groom Mother (First): Lourdes  Groom Mother (Middle): Reyes  Groom Mother (Last): Bautista
Groom Mother Citizenship: Filipino
"""

# ──────────────────────────────────────────────────────────
# MARRIAGE LICENSE PAGE — Bride's Birth Certificate (Female/NSO)
# MNB classify_sex() → "BRIDE"  (SEX: Female)
# Uses F90_BRIDE_* labels
# ──────────────────────────────────────────────────────────
FORM_90_BRIDE_OCR = """
Municipal Form No. 102 Certificate of Live Birth
NSO Registry No.: 2024-BC-002
Date of Registration: January 10, 2024

BRIDE
Bride (First): Maria  Bride (Middle): Garcia  Bride (Last): Torres
Bride Date of Birth: August 3, 1998
Bride Age: 26
Bride Place of Birth: Quezon City
Bride Sex: Female
Bride Citizenship: Filipino
Bride Residence: 456 Mabini Avenue Quezon City

Bride Father (First): Eduardo  Bride Father (Middle): Mendoza  Bride Father (Last): Aquino
Bride Father Citizenship: Filipino

Bride Mother (First): Gloria  Bride Mother (Middle): Santos  Bride Mother (Last): Lopez
Bride Mother Citizenship: Filipino
"""


# ──────────────────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────────────────
def print_form(title: str, source: str, form_object):
    result = filler.to_dict(form_object)
    print(f"\n{'═' * 65}")
    print(f"  📋 {title}")
    print(f"     Source: {source}")
    print(f"{'═' * 65}")
    if not result:
        print("  ⚠️  No fields extracted.")
        print("  → Add annotated training data and fine-tune the model.")
        return
    for field_name, value in result.items():
        label = field_name.replace("_", " ").title()
        print(f"  {label:<45} {value}")


# ──────────────────────────────────────────────────────────
# RUN PIPELINE
# ──────────────────────────────────────────────────────────

# ── Certifications Page ────────────────────────────────────

form_1a = filler.fill_form_1a(FORM_102_OCR)
print_form("FORM 1A — Birth Certificate", "Form 102 (Certificate of Live Birth)", form_1a)
print("\n  ✏️  NAME ASSEMBLY:")
print(f"     Name of Child  → {form_1a.name_of_child!r}")
print(f"     Name of Mother → {form_1a.name_of_mother!r}")
print(f"     Name of Father → {form_1a.name_of_father!r}")

form_2a = filler.fill_form_2a(FORM_103_OCR)
print_form("FORM 2A — Death Certificate", "Form 103 (Certificate of Death)", form_2a)
print("\n  ✏️  NAME ASSEMBLY:")
print(f"     Name of Deceased → {form_2a.name_of_deceased!r}")

form_3a = filler.fill_form_3a(FORM_97_OCR)
print_form("FORM 3A — Marriage Certificate", "Form 97 (Certificate of Marriage)", form_3a)
print("\n  ✏️  NAME ASSEMBLY:")
print(f"     Husband Name         → {form_3a.husband.name!r}")
print(f"     Husband Father Name  → {form_3a.husband.name_of_father!r}")
print(f"     Husband Mother Name  → {form_3a.husband.name_of_mother!r}")
print(f"     Wife Name            → {form_3a.wife.name!r}")
print(f"     Wife Father Name     → {form_3a.wife.name_of_father!r}")
print(f"     Wife Mother Name     → {form_3a.wife.name_of_mother!r}")

# ── Marriage License Page ──────────────────────────────────
# MNB has already classified:
#   FORM_90_GROOM_OCR → classify_sex() → "GROOM" (Male)
#   FORM_90_BRIDE_OCR → classify_sex() → "BRIDE" (Female)

form_90 = filler.fill_form_90(FORM_90_GROOM_OCR, FORM_90_BRIDE_OCR)
print_form("FORM 90 — Application for Marriage License",
           "Marriage License Page (Groom + Bride Birth Certs)", form_90)
print("\n  ✏️  NAME ASSEMBLY:")
print(f"     Groom Name              → {form_90.groom.name_of_applicant!r}")
print(f"     Groom Father Name       → {form_90.groom.name_of_father!r}")
print(f"     Groom Mother Name       → {form_90.groom.maiden_name_of_mother!r}")
print(f"     Bride Name              → {form_90.bride.name_of_applicant!r}")
print(f"     Bride Father Name       → {form_90.bride.name_of_father!r}")
print(f"     Bride Mother Name       → {form_90.bride.maiden_name_of_mother!r}")


print("\n" + "=" * 65)
print("  ✅ Pipeline complete!")
print("=" * 65)
print()
print("  CERTIFICATIONS PAGE → MNB classifies form type → SpaCy NER")
print("  MARRIAGE LICENSE PAGE → MNB classify_sex() routes groom/bride → SpaCy NER")
print()
print("  NEXT STEPS:")
print("  1. Add annotated examples → training/prepare_data.py")
print("  2. Run: python training/prepare_data.py")
print("  3. Run: python training/train.py")
print("  4. Set MODEL_PATH = './models/civil_registry_model/model-best'")
