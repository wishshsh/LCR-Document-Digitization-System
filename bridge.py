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
NER_MODEL_PATH = str(_ROOT / "models" / "civil_registry_model" / "model-best")
MNB_MODEL_DIR  = str(_ROOT / "MNB" / "models")


# ════════════════════════════════════════════════════════════
# CRNN FIELD DICT → TEXT CONVERTERS
# Turns Irish's field dict into readable text that NER can read
# ════════════════════════════════════════════════════════════

def crnn_birth_to_text(f: dict) -> str:
    """Convert CRNN+CTC birth cert field dict → NER-ready text."""
    return (
        f"Registry No.: {f.get('registry_no', '')}\n"
        f"Province: {f.get('province', '')}\n"
        f"City/Municipality: {f.get('city_municipality', '')}\n"
        f"1. NAME (First): {f.get('child_first_name', '')}  "
        f"(Middle): {f.get('child_middle_name', '')}  "
        f"(Last): {f.get('child_last_name', '')}\n"
        f"2. SEX: {f.get('sex', '')}\n"
        f"3. DATE OF BIRTH: {f.get('dob_month', '')} {f.get('dob_day', '')}, {f.get('dob_year', '')}\n"
        f"4. PLACE OF BIRTH: {f.get('place_birth_hospital', '')} "
        f"{f.get('place_birth_city', '')} {f.get('place_birth_province', '')}\n"
        f"5a. TYPE OF BIRTH: {f.get('type_of_birth', '')}\n"
        f"MOTHER:\n"
        f"7. MAIDEN NAME (First): {f.get('mother_first_name', '')}  "
        f"(Middle): {f.get('mother_middle_name', '')}  "
        f"(Last): {f.get('mother_last_name', '')}\n"
        f"8. CITIZENSHIP: {f.get('mother_citizenship', '')}\n"
        f"9. RELIGION: {f.get('mother_religion', '')}\n"
        f"13. RESIDENCE: {f.get('mother_residence_house', '')} "
        f"{f.get('mother_residence_city', '')} {f.get('mother_residence_province', '')}\n"
        f"FATHER:\n"
        f"14. NAME (First): {f.get('father_first_name', '')}  "
        f"(Middle): {f.get('father_middle_name', '')}  "
        f"(Last): {f.get('father_last_name', '')}\n"
        f"15. CITIZENSHIP: {f.get('father_citizenship', '')}\n"
        f"16. RELIGION: {f.get('father_religion', '')}\n"
        f"19. RESIDENCE: {f.get('father_residence_house', '')} "
        f"{f.get('father_residence_city', '')} {f.get('father_residence_province', '')}\n"
        f"MARRIAGE OF PARENTS:\n"
        f"20a. DATE: {f.get('parents_marriage_month', '')} "
        f"{f.get('parents_marriage_day', '')}, {f.get('parents_marriage_year', '')}\n"
        f"20b. PLACE: {f.get('parents_marriage_city', '')} "
        f"{f.get('parents_marriage_province', '')}\n"
    )


def crnn_death_to_text(f: dict) -> str:
    """Convert CRNN+CTC death cert field dict → NER-ready text."""
    return (
        f"Registry No.: {f.get('registry_no', '')}\n"
        f"Province: {f.get('province', '')}\n"
        f"City/Municipality: {f.get('city_municipality', '')}\n"
        f"1. NAME (First): {f.get('deceased_first_name', '')}  "
        f"(Middle): {f.get('deceased_middle_name', '')}  "
        f"(Last): {f.get('deceased_last_name', '')}\n"
        f"2. SEX: {f.get('sex', '')}\n"
        f"3. RELIGION: {f.get('religion', '')}\n"
        f"4. AGE: {f.get('age_years', '')}\n"
        f"5. PLACE OF DEATH: {f.get('place_death_hospital', '')} "
        f"{f.get('place_death_city', '')} {f.get('place_death_province', '')}\n"
        f"6. DATE OF DEATH: {f.get('dod_month', '')} {f.get('dod_day', '')}, {f.get('dod_year', '')}\n"
        f"7. CITIZENSHIP: {f.get('citizenship', '')}\n"
        f"8. RESIDENCE: {f.get('residence_house', '')} "
        f"{f.get('residence_city', '')} {f.get('residence_province', '')}\n"
        f"9. CIVIL STATUS: {f.get('civil_status', '')}\n"
        f"10. OCCUPATION: {f.get('occupation', '')}\n"
        f"17. CAUSES OF DEATH:\n"
        f"Immediate cause: {f.get('cause_immediate', '')}\n"
        f"Antecedent cause: {f.get('cause_antecedent', '')}\n"
        f"Underlying cause: {f.get('cause_underlying', '')}\n"
    )


def crnn_marriage_to_text(f: dict) -> str:
    """Convert CRNN+CTC marriage cert field dict → NER-ready text."""
    return (
        f"Registry No.: {f.get('registry_no', '')}\n"
        f"Province: {f.get('province', '')}\n"
        f"City/Municipality: {f.get('city_municipality', '')}\n"
        f"HUSBAND:\n"
        f"1. NAME (First): {f.get('husband_first_name', '')}  "
        f"(Middle): {f.get('husband_middle_name', '')}  "
        f"(Last): {f.get('husband_last_name', '')}\n"
        f"2a. DATE OF BIRTH: {f.get('husband_dob_month', '')} "
        f"{f.get('husband_dob_day', '')}, {f.get('husband_dob_year', '')}\n"
        f"2b. AGE: {f.get('husband_age', '')}\n"
        f"3. PLACE OF BIRTH: {f.get('husband_place_birth_city', '')} "
        f"{f.get('husband_place_birth_province', '')}\n"
        f"4b. CITIZENSHIP: {f.get('husband_citizenship', '')}\n"
        f"5. RESIDENCE: {f.get('husband_residence', '')}\n"
        f"6. RELIGION: {f.get('husband_religion', '')}\n"
        f"7. CIVIL STATUS: {f.get('husband_civil_status', '')}\n"
        f"8. NAME OF FATHER (First): {f.get('husband_father_first', '')}  "
        f"(Middle): {f.get('husband_father_middle', '')}  "
        f"(Last): {f.get('husband_father_last', '')}\n"
        f"10. NAME OF MOTHER (First): {f.get('husband_mother_first', '')}  "
        f"(Middle): {f.get('husband_mother_middle', '')}  "
        f"(Last): {f.get('husband_mother_last', '')}\n"
        f"WIFE:\n"
        f"1. NAME (First): {f.get('wife_first_name', '')}  "
        f"(Middle): {f.get('wife_middle_name', '')}  "
        f"(Last): {f.get('wife_last_name', '')}\n"
        f"2a. DATE OF BIRTH: {f.get('wife_dob_month', '')} "
        f"{f.get('wife_dob_day', '')}, {f.get('wife_dob_year', '')}\n"
        f"2b. AGE: {f.get('wife_age', '')}\n"
        f"3. PLACE OF BIRTH: {f.get('wife_place_birth_city', '')} "
        f"{f.get('wife_place_birth_province', '')}\n"
        f"4b. CITIZENSHIP: {f.get('wife_citizenship', '')}\n"
        f"5. RESIDENCE: {f.get('wife_residence', '')}\n"
        f"6. RELIGION: {f.get('wife_religion', '')}\n"
        f"7. CIVIL STATUS: {f.get('wife_civil_status', '')}\n"
        f"8. NAME OF FATHER (First): {f.get('wife_father_first', '')}  "
        f"(Middle): {f.get('wife_father_middle', '')}  "
        f"(Last): {f.get('wife_father_last', '')}\n"
        f"10. NAME OF MOTHER (First): {f.get('wife_mother_first', '')}  "
        f"(Middle): {f.get('wife_mother_middle', '')}  "
        f"(Last): {f.get('wife_mother_last', '')}\n"
        f"15. PLACE OF MARRIAGE: {f.get('place_marriage_office', '')} "
        f"{f.get('place_marriage_city', '')} {f.get('place_marriage_province', '')}\n"
        f"16. DATE OF MARRIAGE: {f.get('date_marriage_month', '')} "
        f"{f.get('date_marriage_day', '')}, {f.get('date_marriage_year', '')}\n"
    )


# ── Auto-detect form type from CRNN field keys ───────────────
_BIRTH_KEYS    = {'child_first_name', 'mother_first_name', 'dob_day'}
_DEATH_KEYS    = {'deceased_first_name', 'cause_immediate', 'dod_day'}
_MARRIAGE_KEYS = {'husband_first_name', 'wife_first_name', 'date_marriage_day'}

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

    Nobody edits anyone else's code.

    Usage:
        from bridge import CivilRegistryBridge

        bridge = CivilRegistryBridge()

        # Path A — birth / death / marriage cert
        form = bridge.process(crnn_fields, form_hint="birth")
        print(form.name_of_child)
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
            Output from Irish's run_crnn_ocr() in field_extractor.py
            e.g. {"child_first_name": "Juan", "sex": "Male", ...}

        form_hint : str, optional
            'birth' | 'death' | 'marriage'
            Auto-detected from field keys if not given.

        Returns
        -------
        Form1A | Form2A | Form3A  with all fields populated
        """
        # 1 — detect form type
        form_type = form_hint or _detect_form_type(crnn_fields)

        # 2 — CRNN dict → plain text string
        ocr_text = _CONVERTERS.get(form_type, crnn_birth_to_text)(crnn_fields)

        # 3 — MNB confirms (logged as sanity check)
        mnb_label = self.mnb.classify_form_type(ocr_text)
        print(f"  [Bridge] hint={form_type!r}  MNB={mnb_label}  NER→running...")

        # 4 — spaCy NER fills the form
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
                                  bride_crnn_fields: dict):
        """
        Parameters
        ----------
        groom_crnn_fields : dict   Irish's CRNN output for groom birth cert
        bride_crnn_fields : dict   Irish's CRNN output for bride birth cert

        Returns
        -------
        Form90  with groom.* and bride.* fields populated
        """
        groom_text = crnn_birth_to_text(groom_crnn_fields)
        bride_text = crnn_birth_to_text(bride_crnn_fields)

        groom_sex = self.mnb.classify_sex(groom_text)
        bride_sex  = self.mnb.classify_sex(bride_text)
        print(f"  [Bridge] Form90  groom_sex={groom_sex}  bride_sex={bride_sex}")

        return self.filler.fill_form_90(groom_text, bride_text)


# ── Quick test — run: python bridge.py ───────────────────────
if __name__ == "__main__":

    SAMPLE_BIRTH = {
        "registry_no":        "2024-001",
        "province":           "Metro Manila",
        "city_municipality":  "Makati City",
        "child_first_name":   "Juan",
        "child_middle_name":  "dela Cruz",
        "child_last_name":    "Santos",
        "sex":                "Male",
        "dob_day":            "15",
        "dob_month":          "March",
        "dob_year":           "1990",
        "place_birth_city":   "Makati City",
        "mother_first_name":  "Maria",
        "mother_middle_name": "Reyes",
        "mother_last_name":   "dela Cruz",
        "mother_citizenship": "Filipino",
        "father_first_name":  "Pedro",
        "father_middle_name": "Cruz",
        "father_last_name":   "Santos",
        "father_citizenship": "Filipino",
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
