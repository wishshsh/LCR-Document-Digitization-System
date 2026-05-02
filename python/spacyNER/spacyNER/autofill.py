# =============================================================
# spacyNER/autofill.py
# =============================================================
# Maps extracted NER dicts → populated Form dataclasses.
#
# Certifications page:
#   fill_form_1a(text)  → Form1A  (from Form 102 OCR)
#   fill_form_2a(text)  → Form2A  (from Form 103 OCR)
#   fill_form_3a(text)  → Form3A  (from Form 97 OCR)
#
# Marriage License Receipt:
#   fill_form_90(text)  → Form54
#     Reads the Marriage License and Fee Receipt document (Form 90 /
#     Accountable Form No. 54 / Form No. 10) directly.
#     Extracts: name_of_groom, age_of_groom, residence_of_groom,
#               name_of_bride,  age_of_bride,  residence_of_bride,
#               date_of_issuance
# =============================================================

from spacyNER.extractor import CivilRegistryNER
from spacyNER.models    import (
    Form1A, Form2A, Form3A, Form54,
    SpouseOutput,
)
from spacyNER.labels import (
    OUTPUT_MAP_1A,
    OUTPUT_MAP_2A,
    OUTPUT_MAP_3A_HUSBAND,
    OUTPUT_MAP_3A_WIFE,
    OUTPUT_MAP_3A_EVENT,
    OUTPUT_MAP_90,
)


class AutoFillEngine:

    def __init__(self, extractor: CivilRegistryNER):
        self.extractor = extractor

    # ── Form 1A ───────────────────────────────────────────────
    def fill_form_1a(self, ocr_text: str) -> Form1A:
        """OCR text from Form 102 → Form1A object."""
        data = self.extractor.extract_form_102(ocr_text)
        form = Form1A()
        for label, field_name in OUTPUT_MAP_1A.items():
            v = data.get(label)
            if v: setattr(form, field_name, v)
        if data.get("name_of_child"):   form.name_of_child  = data["name_of_child"]
        if data.get("name_of_mother"):  form.name_of_mother = data["name_of_mother"]
        if data.get("name_of_father"):  form.name_of_father = data["name_of_father"]
        return form

    # ── Form 2A ───────────────────────────────────────────────
    def fill_form_2a(self, ocr_text: str) -> Form2A:
        """OCR text from Form 103 → Form2A object."""
        data = self.extractor.extract_form_103(ocr_text)
        form = Form2A()
        for label, field_name in OUTPUT_MAP_2A.items():
            v = data.get(label)
            if v: setattr(form, field_name, v)
        if data.get("name_of_deceased"):
            form.name_of_deceased = data["name_of_deceased"]
        return form

    # ── Form 3A ───────────────────────────────────────────────
    def fill_form_3a(self, ocr_text: str) -> Form3A:
        """OCR text from Form 97 → Form3A object."""
        data    = self.extractor.extract_form_97(ocr_text)
        husband = SpouseOutput()
        wife    = SpouseOutput()
        form    = Form3A(husband=husband, wife=wife)

        for label, field_name in OUTPUT_MAP_3A_HUSBAND.items():
            v = data.get(label)
            if v: setattr(husband, field_name, v)
        for label, field_name in OUTPUT_MAP_3A_WIFE.items():
            v = data.get(label)
            if v: setattr(wife, field_name, v)
        for label, field_name in OUTPUT_MAP_3A_EVENT.items():
            v = data.get(label)
            if v: setattr(form, field_name, v)

        if data.get("husband_name"):           husband.name           = data["husband_name"]
        if data.get("husband_name_of_father"): husband.name_of_father = data["husband_name_of_father"]
        if data.get("husband_name_of_mother"): husband.name_of_mother = data["husband_name_of_mother"]
        if data.get("wife_name"):              wife.name              = data["wife_name"]
        if data.get("wife_name_of_father"):    wife.name_of_father    = data["wife_name_of_father"]
        if data.get("wife_name_of_mother"):    wife.name_of_mother    = data["wife_name_of_mother"]
        return form

    # ── Form 54 (Form 90) ─────────────────────────────────────
    def fill_form_90(self, ocr_text: str) -> Form54:
        """
        OCR text from the Marriage License and Fee Receipt
        (Form 90 / Accountable Form No. 54 / Form No. 10) → Form54 object.

        Required output fields:
          name_of_groom    age_of_groom    residence_of_groom
          name_of_bride    age_of_bride    residence_of_bride
          date_of_issuance
        """
        data = self.extractor.extract_form_90(ocr_text)
        form = Form54()
        for label, field_name in OUTPUT_MAP_90.items():
            v = data.get(label)
            if v: setattr(form, field_name, v)
        # Assembled names
        if data.get("name_of_groom"): form.name_of_groom = data["name_of_groom"]
        if data.get("name_of_bride"): form.name_of_bride = data["name_of_bride"]
        return form

    # ── Utility ───────────────────────────────────────────────
    def to_dict(self, form_obj) -> dict:
        """Flatten any Form object to a non-None, non-nested dict."""
        if form_obj is None or not hasattr(form_obj, "to_dict"):
            return {}
        raw  = form_obj.to_dict()
        flat = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    if sv is not None:
                        flat[f"{k}_{sk}"] = sv
            elif v is not None:
                flat[k] = v
        return flat
