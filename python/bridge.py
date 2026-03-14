# bridge.py
# ============================================================
# BRIDGE — connects the three algorithms
#
#   CRNN+CTC  (Irish)     →  field dict from field_extractor.py
#   MNB       (Princess)  →  classifies form type
#   spacyNER  (Shane)     →  extracts + assembles fields
#
# DROP THIS FILE in the ROOT of your project:
#
#   LCR-Document-Digitization-System/
#   ├── CRNN+CTC/
#   ├── MNB/
#   ├── spacyNER/
#   ├── bridge.py          ← HERE
#   └── pipeline.py
#
# NOTE: nationality = citizenship (same field, different label per form)
#       The _get() helper handles both names automatically.
# ============================================================

import sys
import os
from pathlib import Path

# ── Make all three algorithm folders importable ──────────────
_ROOT = Path(__file__).resolve().parent

for folder in ["CRNN+CTC", "MNB", "spacyNER"]:
    p = str(_ROOT / folder)
    if p not in sys.path:
        sys.path.insert(0, p)

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Imports ──────────────────────────────────────────────────
from spacyNER.extractor import CivilRegistryNER
from spacyNER.autofill  import AutoFillEngine
from MNB.classifier     import MNBClassifier

# ── Default paths ────────────────────────────────────────────
NER_MODEL_PATH = str(_ROOT / "spacyNER" / "models" / "civil_registry_model" / "model-best")
MNB_MODEL_DIR  = str(_ROOT / "MNB" / "models")


# ════════════════════════════════════════════════════════════
# HELPER — nationality/citizenship alias
# Tries multiple key names, returns first non-empty value.
# nationality = citizenship — same field, different label per form.
# ════════════════════════════════════════════════════════════

def _get(f: dict, *keys, default='') -> str:
    for k in keys:
        v = f.get(k, '')
        if v and str(v).strip():
            return str(v).strip()
    return default


# ════════════════════════════════════════════════════════════
# CRNN FIELD DICT → TEXT CONVERTERS
# Turns Irish's field dict into readable text that NER can read.
# Handles both old field names and new dynamic_field_extractor names.
# ════════════════════════════════════════════════════════════

def crnn_birth_to_text(f: dict) -> str:
    """Form 102 → Form 1A text.
    Fields needed:
      Registry Number, Date of Registration,
      Name of Child, Sex, Date of Birth, Place of Birth,
      Name of Mother, Nationality/Citizenship of Mother,
      Name of Father, Nationality/Citizenship of Father,
      Date of Marriage of Parents, Place of Marriage of Parents
    """
    return (
        f"Registry No.: {_get(f, 'registry_number', 'registry_no')}\n"
        f"Date of Registration: {_get(f, 'date_of_registration')}\n"
        f"1. NAME (First): {_get(f, 'child_first_name')}  "
        f"(Middle): {_get(f, 'child_middle_name')}  "
        f"(Last): {_get(f, 'child_last_name')}\n"
        f"2. SEX: {_get(f, 'sex')}\n"
        f"3. DATE OF BIRTH: {_get(f, 'dob_month')} {_get(f, 'dob_day')}, {_get(f, 'dob_year')}\n"
        f"4. PLACE OF BIRTH: {_get(f, 'place_birth_hospital')} "
        f"{_get(f, 'place_birth_city')} {_get(f, 'place_birth_province')}\n"
        f"MOTHER:\n"
        f"7. MAIDEN NAME (First): {_get(f, 'mother_first_name')}  "
        f"(Middle): {_get(f, 'mother_middle_name')}  "
        f"(Last): {_get(f, 'mother_last_name')}\n"
        f"8. CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'nationality_of_mother', 'mother_citizenship', 'mother_nationality')}\n"
        f"FATHER:\n"
        f"14. NAME (First): {_get(f, 'father_first_name')}  "
        f"(Middle): {_get(f, 'father_middle_name')}  "
        f"(Last): {_get(f, 'father_last_name')}\n"
        f"15. CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'nationality_of_father', 'father_citizenship', 'father_nationality')}\n"
        f"MARRIAGE OF PARENTS:\n"
        f"20a. DATE: {_get(f, 'parents_marriage_month')} "
        f"{_get(f, 'parents_marriage_day')}, {_get(f, 'parents_marriage_year')}\n"
        f"20b. PLACE: {_get(f, 'parents_marriage_city')} "
        f"{_get(f, 'parents_marriage_province')}\n"
    )


def crnn_death_to_text(f: dict) -> str:
    """Form 103 → Form 2A text.
    Fields needed:
      Registry Number, Date of Registration,
      Name of Deceased, Sex, Age, Civil Status,
      Nationality/Citizenship, Date of Death, Place of Death,
      Cause of Death
    """
    return (
        f"Registry No.: {_get(f, 'registry_number', 'registry_no')}\n"
        f"Date of Registration: {_get(f, 'date_of_registration')}\n"
        f"1. NAME (First): {_get(f, 'deceased_first_name')}  "
        f"(Middle): {_get(f, 'deceased_middle_name')}  "
        f"(Last): {_get(f, 'deceased_last_name')}\n"
        f"2. SEX: {_get(f, 'sex')}\n"
        f"4. AGE: {_get(f, 'age', 'age_years')}\n"
        f"9. CIVIL STATUS: {_get(f, 'civil_status')}\n"
        f"7. CITIZENSHIP/NATIONALITY: {_get(f, 'nationality', 'citizenship')}\n"
        f"6. DATE OF DEATH: {_get(f, 'dod_month')} {_get(f, 'dod_day')}, {_get(f, 'dod_year')}\n"
        f"5. PLACE OF DEATH: {_get(f, 'place_death_hospital')} "
        f"{_get(f, 'place_death_city')} {_get(f, 'place_death_province')}\n"
        f"17. CAUSE OF DEATH: {_get(f, 'cause_of_death', 'cause_immediate')}\n"
        f"Antecedent cause: {_get(f, 'cause_antecedent')}\n"
        f"Underlying cause: {_get(f, 'cause_underlying')}\n"
    )


def crnn_marriage_to_text(f: dict) -> str:
    """Form 97 → Form 3A text.
    Fields needed (both husband and wife):
      Name, Age, Nationality/Citizenship,
      Name of Mother, Nationality/Citizenship of Mother,
      Name of Father, Nationality/Citizenship of Father,
      Registry Number, Date of Registration,
      Date of Marriage, Place of Marriage
    """
    return (
        f"Registry No.: {_get(f, 'registry_number', 'registry_no')}\n"
        f"Date of Registration: {_get(f, 'date_of_registration')}\n"
        f"HUSBAND:\n"
        f"1. NAME (First): {_get(f, 'husband_first_name')}  "
        f"(Middle): {_get(f, 'husband_middle_name')}  "
        f"(Last): {_get(f, 'husband_last_name')}\n"
        f"2b. AGE: {_get(f, 'husband_age')}\n"
        f"4b. CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'husband_nationality', 'husband_citizenship')}\n"
        f"8. NAME OF FATHER (First): {_get(f, 'husband_father_first')}  "
        f"(Middle): {_get(f, 'husband_father_middle')}  "
        f"(Last): {_get(f, 'husband_father_last')}\n"
        f"8b. FATHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'husband_father_nationality', 'husband_father_citizenship')}\n"
        f"10. NAME OF MOTHER (First): {_get(f, 'husband_mother_first')}  "
        f"(Middle): {_get(f, 'husband_mother_middle')}  "
        f"(Last): {_get(f, 'husband_mother_last')}\n"
        f"10b. MOTHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'husband_mother_nationality', 'husband_mother_citizenship')}\n"
        f"WIFE:\n"
        f"1. NAME (First): {_get(f, 'wife_first_name')}  "
        f"(Middle): {_get(f, 'wife_middle_name')}  "
        f"(Last): {_get(f, 'wife_last_name')}\n"
        f"2b. AGE: {_get(f, 'wife_age')}\n"
        f"4b. CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'wife_nationality', 'wife_citizenship')}\n"
        f"8. NAME OF FATHER (First): {_get(f, 'wife_father_first')}  "
        f"(Middle): {_get(f, 'wife_father_middle')}  "
        f"(Last): {_get(f, 'wife_father_last')}\n"
        f"8b. FATHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'wife_father_nationality', 'wife_father_citizenship')}\n"
        f"10. NAME OF MOTHER (First): {_get(f, 'wife_mother_first')}  "
        f"(Middle): {_get(f, 'wife_mother_middle')}  "
        f"(Last): {_get(f, 'wife_mother_last')}\n"
        f"10b. MOTHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'wife_mother_nationality', 'wife_mother_citizenship')}\n"
        f"15. PLACE OF MARRIAGE: "
        f"{_get(f, 'place_marriage_city')} {_get(f, 'place_marriage_province')}\n"
        f"16. DATE OF MARRIAGE: {_get(f, 'date_marriage_month')} "
        f"{_get(f, 'date_marriage_day')}, {_get(f, 'date_marriage_year')}\n"
    )


def crnn_birth_to_form90_text(f: dict, role: str = 'groom') -> str:
    """Birth cert of groom or bride → Form 90 text.
    Fields needed:
      Name, Date of Birth, Place of Birth, Sex,
      Citizenship/Nationality,
      Name of Father, Citizenship of Father,
      Name of Mother, Citizenship of Mother
    role: 'groom' or 'bride'
    """
    return (
        f"{role.upper()}:\n"
        f"1. NAME (First): {_get(f, 'first_name', 'child_first_name')}  "
        f"(Middle): {_get(f, 'middle_name', 'child_middle_name')}  "
        f"(Last): {_get(f, 'last_name', 'child_last_name')}\n"
        f"2. DATE OF BIRTH: {_get(f, 'dob_month')} {_get(f, 'dob_day')}, {_get(f, 'dob_year')}\n"
        f"3. PLACE OF BIRTH: {_get(f, 'place_birth_hospital')} "
        f"{_get(f, 'place_birth_city')} {_get(f, 'place_birth_province')}\n"
        f"4. SEX: {_get(f, 'sex')}\n"
        f"5. CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'citizenship', 'nationality', 'nationality_of_mother', 'mother_citizenship')}\n"
        f"NAME OF FATHER (First): {_get(f, 'father_first_name')}  "
        f"(Middle): {_get(f, 'father_middle_name')}  "
        f"(Last): {_get(f, 'father_last_name')}\n"
        f"FATHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'father_citizenship', 'father_nationality')}\n"
        f"NAME OF MOTHER (First): {_get(f, 'mother_first_name')}  "
        f"(Middle): {_get(f, 'mother_middle_name')}  "
        f"(Last): {_get(f, 'mother_last_name')}\n"
        f"MOTHER CITIZENSHIP/NATIONALITY: "
        f"{_get(f, 'mother_citizenship', 'mother_nationality')}\n"
    )


# ── Auto-detect form type from CRNN field keys ───────────────
_BIRTH_KEYS    = {'child_first_name', 'mother_first_name', 'dob_day',
                  'registry_number', 'nationality_of_mother'}
_DEATH_KEYS    = {'deceased_first_name', 'cause_of_death', 'dod_day',
                  'cause_immediate', 'nationality'}
_MARRIAGE_KEYS = {'husband_first_name', 'wife_first_name', 'date_marriage_day',
                  'husband_nationality', 'wife_nationality'}

_CONVERTERS = {
    'birth':    crnn_birth_to_text,
    'death':    crnn_death_to_text,
    'marriage': crnn_marriage_to_text,
}

def _detect_form_type(fields: dict) -> str:
    keys = set(fields.keys())
    if keys & _BIRTH_KEYS:    return 'birth'
    if keys & _DEATH_KEYS:    return 'death'
    if keys & _MARRIAGE_KEYS: return 'marriage'
    return 'birth'


# ════════════════════════════════════════════════════════════
# BRIDGE CLASS
# ════════════════════════════════════════════════════════════

class CivilRegistryBridge:
    """
    The single connection point between the three algorithms.

    Usage:
        from bridge import CivilRegistryBridge

        bridge = CivilRegistryBridge()

        # Path A — birth / death / marriage cert
        form = bridge.process(crnn_fields, form_hint="birth")
        print(form.to_dict())

        # Path B — Form 90 (two birth certs)
        form90 = bridge.process_marriage_license(
            groom_crnn_fields,
            bride_crnn_fields
        )
    """

    def __init__(self,
                 ner_model_path: str = NER_MODEL_PATH,
                 mnb_model_dir:  str = MNB_MODEL_DIR):

        # Princess's MNB classifier
        self.mnb = MNBClassifier(model_dir=mnb_model_dir)

        # Shane's NER extractor
        self.extractor = CivilRegistryNER(model_path=ner_model_path)
        self.filler    = AutoFillEngine(self.extractor)

    # ── Path A — single cert (birth / death / marriage) ──────
    def process(self, crnn_fields: dict, form_hint: str = None):
        """
        Parameters
        ----------
        crnn_fields : dict
            Output from Irish's run_crnn_ocr() / dynamic_field_extractor

        form_hint : str, optional
            'birth' | 'death' | 'marriage'
            Auto-detected from field keys if not given.

        Returns
        -------
        Form1A | Form2A | Form3A  with all fields populated
        """
        form_type = form_hint or _detect_form_type(crnn_fields)
        ocr_text  = _CONVERTERS.get(form_type, crnn_birth_to_text)(crnn_fields)
        mnb_label = self.mnb.classify_form_type(ocr_text)
        print(f"  [Bridge] hint={form_type!r}  MNB={mnb_label}  NER→running...")

        if form_type == 'birth':
            return self.filler.fill_form_1a(ocr_text)
        elif form_type == 'death':
            return self.filler.fill_form_2a(ocr_text)
        elif form_type == 'marriage':
            return self.filler.fill_form_3a(ocr_text)
        else:
            return self.filler.fill_form_1a(ocr_text)

    # ── Path B — Form 90 (two birth certs) ───────────────────
    def process_marriage_license(self,
                                  groom_crnn_fields: dict,
                                  bride_crnn_fields:  dict):
        """
        Parameters
        ----------
        groom_crnn_fields : dict   CRNN output for groom's birth cert
        bride_crnn_fields : dict   CRNN output for bride's birth cert

        Returns
        -------
        Form90  with groom.* and bride.* fields populated
        """
        groom_text = crnn_birth_to_form90_text(groom_crnn_fields, role='groom')
        bride_text = crnn_birth_to_form90_text(bride_crnn_fields, role='bride')

        groom_sex = self.mnb.classify_sex(groom_text)
        bride_sex  = self.mnb.classify_sex(bride_text)
        print(f"  [Bridge] Form90  groom_sex={groom_sex}  bride_sex={bride_sex}")

        return self.filler.fill_form_90(groom_text, bride_text)


# ── Quick test — run: python bridge.py ───────────────────────
if __name__ == "__main__":

    SAMPLE_BIRTH = {
        "registry_number":           "2024-001",
        "date_of_registration":      "June 12, 1998",
        "child_first_name":          "TASLIAH",
        "child_middle_name":         "ABOBACAR",
        "child_last_name":           "GOMONSANG",
        "sex":                       "FEMALE",
        "dob_day":                   "12",
        "dob_month":                 "JUNE",
        "dob_year":                  "1998",
        "place_birth_hospital":      "CAMP JAS BLISS",
        "place_birth_city":          "MALABANG",
        "place_birth_province":      "LANAO DEL SUR",
        "mother_first_name":         "H. ASLIAH",
        "mother_middle_name":        "SANTICAN",
        "mother_last_name":          "ABOBACAR",
        "nationality_of_mother":     "FILIPINO",   # nationality = citizenship
        "father_first_name":         "H. NAEEF",
        "father_middle_name":        "MUDAG",
        "father_last_name":          "GOMONSANG",
        "nationality_of_father":     "FILIPINO",   # nationality = citizenship
        "parents_marriage_month":    "JANUARY",
        "parents_marriage_day":      "5",
        "parents_marriage_year":     "1990",
        "parents_marriage_city":     "CAMP JAS BLISS MALABANG",
        "parents_marriage_province": "LANAO DEL SUR",
    }

    print("=" * 55)
    print("  BRIDGE TEST")
    print("=" * 55)

    bridge = CivilRegistryBridge()
    form   = bridge.process(SAMPLE_BIRTH, form_hint="birth")

    print(f"\n  name_of_child  → {form.name_of_child!r}")
    print(f"  name_of_mother → {form.name_of_mother!r}")
    print(f"  name_of_father → {form.name_of_father!r}")
    print(f"  date_of_birth  → {form.date_of_birth!r}")
    print("\n  Full result:")
    for k, v in form.to_dict().items():
        if v:
            print(f"    {k:<35} {v}")
