# =============================================================
# spacyNER/autofill.py
# =============================================================
# Maps extracted NER dicts → populated Form dataclasses.
#
# Imports from:
#   labels.py  — OUTPUT_MAP_1A / _2A / _3A_* / _90
#   models.py  — Form1A, Form2A, Form3A, Form90,
#                SpouseOutput, ApplicantOutput
#   extractor.py — CivilRegistryNER (provides extract_form_*())
#
# Flow for Form 1A:
#   extractor.extract_form_102(text)
#     → {F102_REGISTRY_NO: "2024-001",
#        name_of_child:    "Juan dela Cruz Santos", ...}
#   autofill.fill_form_1a(text)
#     → Form1A(registry_number="2024-001",
#              name_of_child="Juan dela Cruz Santos", ...)
#
# OUTPUT FIELD NAMES come from OUTPUT_MAP_* in labels.py and
# must match the attribute names in models.py exactly.
# =============================================================

from spacyNER.extractor import CivilRegistryNER
from spacyNER.models    import (
    Form1A, Form2A, Form3A, Form90,
    SpouseOutput, ApplicantOutput,
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
        """
        OCR text from Form 102  →  Form1A object.

        Populated output fields (Form 1A layout):
          Registry Number          Date of Registration
          Name of Child            Sex
          Date of Birth            Place of Birth
          Name of Mother           Nationality of Mother
          Name of Father           Nationality of Father
          Date of Marriage of Parents  Place of Marriage of Parents
        """
        data = self.extractor.extract_form_102(ocr_text)
        form = Form1A()
        # Direct-mapped fields (NER label → field name from OUTPUT_MAP_1A)
        for label, field_name in OUTPUT_MAP_1A.items():
            v = data.get(label)
            if v:
                setattr(form, field_name, v)
        # Assembled name fields (added by name_assembler, not in OUTPUT_MAP)
        if data.get("name_of_child"):
            form.name_of_child  = data["name_of_child"]
        if data.get("name_of_mother"):
            form.name_of_mother = data["name_of_mother"]
        if data.get("name_of_father"):
            form.name_of_father = data["name_of_father"]
        return form

    # ── Form 2A ───────────────────────────────────────────────
    def fill_form_2a(self, ocr_text: str) -> Form2A:
        """
        OCR text from Form 103  →  Form2A object.

        Populated output fields (Form 2A layout):
          Registry Number    Date of Registration
          Name of Deceased   Sex
          Age                Civil Status
          Nationality        Date of Death
          Place of Death     Cause of Death
        """
        data = self.extractor.extract_form_103(ocr_text)
        form = Form2A()
        for label, field_name in OUTPUT_MAP_2A.items():
            v = data.get(label)
            if v:
                setattr(form, field_name, v)
        if data.get("name_of_deceased"):
            form.name_of_deceased = data["name_of_deceased"]
        return form

    # ── Form 3A ───────────────────────────────────────────────
    def fill_form_3a(self, ocr_text: str) -> Form3A:
        """
        OCR text from Form 97  →  Form3A object.

        Populated output fields (Form 3A layout):
          For husband and wife:
            Name           Age            Nationality
            Name of Mother  Nationality of Mother
            Name of Father  Nationality of Father
          Shared:
            Date of Registration  Date of Marriage  Place of Marriage
        """
        data    = self.extractor.extract_form_97(ocr_text)
        husband = SpouseOutput()
        wife    = SpouseOutput()
        form    = Form3A(husband=husband, wife=wife)

        for label, field_name in OUTPUT_MAP_3A_HUSBAND.items():
            v = data.get(label)
            if v:
                setattr(husband, field_name, v)
        for label, field_name in OUTPUT_MAP_3A_WIFE.items():
            v = data.get(label)
            if v:
                setattr(wife, field_name, v)
        for label, field_name in OUTPUT_MAP_3A_EVENT.items():
            v = data.get(label)
            if v:
                setattr(form, field_name, v)

        if data.get("husband_name"):          husband.name           = data["husband_name"]
        if data.get("husband_name_of_father"):husband.name_of_father = data["husband_name_of_father"]
        if data.get("husband_name_of_mother"):husband.name_of_mother = data["husband_name_of_mother"]
        if data.get("wife_name"):             wife.name              = data["wife_name"]
        if data.get("wife_name_of_father"):   wife.name_of_father    = data["wife_name_of_father"]
        if data.get("wife_name_of_mother"):   wife.name_of_mother    = data["wife_name_of_mother"]
        return form

    # ── Form 90 ───────────────────────────────────────────────
    def fill_form_90(self, groom_ocr: str, bride_ocr: str) -> Form90:
        """
        Birth certificate OCR for groom + bride  →  Form90 object.

        Populated output fields per applicant (Form 90 layout):
          Name of Applicant  Date of Birth  Age  Place of Birth
          Sex                Citizenship    Residence  Religion
          Name of Father     Citizenship (Father)
          Maiden Name of Mother  Citizenship (Mother)  Residence (Mother)
        """
        return Form90(
            groom=self._fill_applicant(self.extractor.extract_form_90(groom_ocr)),
            bride=self._fill_applicant(self.extractor.extract_form_90(bride_ocr)),
        )

    def _fill_applicant(self, data: dict) -> ApplicantOutput:
        a = ApplicantOutput()
        for label, field_name in OUTPUT_MAP_90.items():
            v = data.get(label)
            if v:
                setattr(a, field_name, v)
        if data.get("name_of_applicant"):     a.name_of_applicant    = data["name_of_applicant"]
        if data.get("name_of_father"):        a.name_of_father       = data["name_of_father"]
        if data.get("maiden_name_of_mother"): a.maiden_name_of_mother= data["maiden_name_of_mother"]
        return a

    # ── Utility ───────────────────────────────────────────────
    def to_dict(self, form_obj) -> dict:
        """Flatten any Form object to a non-None, non-nested dict."""
        if form_obj is None:
            return {}
        if not hasattr(form_obj, "to_dict"):
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
