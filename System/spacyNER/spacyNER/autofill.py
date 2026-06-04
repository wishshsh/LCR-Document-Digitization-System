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
# Marriage License page:
#   fill_form_90(groom_ocr, bride_ocr) → Form90
#     MNB classify_sex() has already routed each cert before this.
# =============================================================

from spacyNER.extractor import CivilRegistryNER
from spacyNER.models import (
    Form1A, Form2A, Form3A, Form90,
    SpouseOutput, ApplicantOutput,
)
from spacyNER.labels import (
    # Form 102 — Birth Certificate
    F102_CHILD_FIRST, F102_CHILD_MIDDLE, F102_CHILD_LAST,
    F102_SEX, F102_DATE_OF_BIRTH, F102_PLACE_OF_BIRTH,
    F102_TYPE_OF_BIRTH, F102_BIRTH_ORDER,
    F102_MOTHER_FIRST, F102_MOTHER_MIDDLE, F102_MOTHER_LAST,
    F102_MOTHER_CITIZENSHIP, F102_MOTHER_RELIGION, F102_MOTHER_RESIDENCE,
    F102_FATHER_FIRST, F102_FATHER_MIDDLE, F102_FATHER_LAST,
    F102_FATHER_CITIZENSHIP, F102_FATHER_RELIGION, F102_FATHER_RESIDENCE,
    F102_MARRIAGE_DATE, F102_MARRIAGE_PLACE,
    F102_REGISTRY_NO, F102_DATE_OF_REGISTRATION,
    # Form 103 — Death Certificate
    F103_DECEASED_FIRST, F103_DECEASED_MIDDLE, F103_DECEASED_LAST,
    F103_SEX, F103_RELIGION, F103_AGE,
    F103_PLACE_OF_DEATH, F103_DATE_OF_DEATH,
    F103_CITIZENSHIP, F103_RESIDENCE, F103_CIVIL_STATUS, F103_OCCUPATION,
    F103_CAUSE_IMMEDIATE, F103_CAUSE_ANTECEDENT, F103_CAUSE_UNDERLYING,
    F103_REGISTRY_NO, F103_DATE_OF_REGISTRATION,
    # Form 97 — Marriage Certificate
    F97_HUSBAND_FIRST, F97_HUSBAND_MIDDLE, F97_HUSBAND_LAST,
    F97_HUSBAND_DOB, F97_HUSBAND_AGE,
    F97_HUSBAND_PLACE_BIRTH, F97_HUSBAND_SEX, F97_HUSBAND_CITIZENSHIP,
    F97_HUSBAND_RESIDENCE, F97_HUSBAND_RELIGION, F97_HUSBAND_CIVIL_STATUS,
    F97_HUSBAND_FATHER_FIRST, F97_HUSBAND_FATHER_MIDDLE, F97_HUSBAND_FATHER_LAST,
    F97_HUSBAND_FATHER_CITIZENSHIP,
    F97_HUSBAND_MOTHER_FIRST, F97_HUSBAND_MOTHER_MIDDLE, F97_HUSBAND_MOTHER_LAST,
    F97_HUSBAND_MOTHER_CITIZENSHIP,
    F97_WIFE_FIRST, F97_WIFE_MIDDLE, F97_WIFE_LAST,
    F97_WIFE_DOB, F97_WIFE_AGE,
    F97_WIFE_PLACE_BIRTH, F97_WIFE_SEX, F97_WIFE_CITIZENSHIP,
    F97_WIFE_RESIDENCE, F97_WIFE_RELIGION, F97_WIFE_CIVIL_STATUS,
    F97_WIFE_FATHER_FIRST, F97_WIFE_FATHER_MIDDLE, F97_WIFE_FATHER_LAST,
    F97_WIFE_FATHER_CITIZENSHIP,
    F97_WIFE_MOTHER_FIRST, F97_WIFE_MOTHER_MIDDLE, F97_WIFE_MOTHER_LAST,
    F97_WIFE_MOTHER_CITIZENSHIP,
    F97_PLACE_OF_MARRIAGE, F97_DATE_OF_MARRIAGE,
    F97_REGISTRY_NO, F97_DATE_OF_REGISTRATION,
    # Form 90 — Marriage License (shared)
    F90_REGISTRY_NO, F90_DATE_OF_REGISTRATION,
    # Form 90 — Groom (Male birth cert)
    F90_GROOM_FIRST, F90_GROOM_MIDDLE, F90_GROOM_LAST,
    F90_GROOM_DATE_OF_BIRTH, F90_GROOM_AGE, F90_GROOM_PLACE_OF_BIRTH,
    F90_GROOM_SEX, F90_GROOM_CITIZENSHIP, F90_GROOM_RESIDENCE, F90_GROOM_RELIGION,
    F90_GROOM_FATHER_FIRST, F90_GROOM_FATHER_MIDDLE, F90_GROOM_FATHER_LAST,
    F90_GROOM_FATHER_CITIZENSHIP,
    F90_GROOM_MOTHER_FIRST, F90_GROOM_MOTHER_MIDDLE, F90_GROOM_MOTHER_LAST,
    F90_GROOM_MOTHER_CITIZENSHIP, F90_GROOM_MOTHER_RESIDENCE,
    # Form 90 — Bride (Female birth cert)
    F90_BRIDE_FIRST, F90_BRIDE_MIDDLE, F90_BRIDE_LAST,
    F90_BRIDE_DATE_OF_BIRTH, F90_BRIDE_AGE, F90_BRIDE_PLACE_OF_BIRTH,
    F90_BRIDE_SEX, F90_BRIDE_CITIZENSHIP, F90_BRIDE_RESIDENCE, F90_BRIDE_RELIGION,
    F90_BRIDE_FATHER_FIRST, F90_BRIDE_FATHER_MIDDLE, F90_BRIDE_FATHER_LAST,
    F90_BRIDE_FATHER_CITIZENSHIP,
    F90_BRIDE_MOTHER_FIRST, F90_BRIDE_MOTHER_MIDDLE, F90_BRIDE_MOTHER_LAST,
    F90_BRIDE_MOTHER_CITIZENSHIP, F90_BRIDE_MOTHER_RESIDENCE,
)


def _set(obj, field: str, data: dict, label: str) -> None:
    """Set obj.field = data[label] if the label exists and is not None."""
    v = data.get(label)
    if v is not None:
        setattr(obj, field, v)


class AutoFillEngine:

    def __init__(self, extractor: CivilRegistryNER):
        self.extractor = extractor

    # ── Form 1A (from Form 102 — Certificate of Live Birth) ───
    def fill_form_1a(self, ocr_text: str) -> Form1A:
        data = self.extractor.extract_form_102(ocr_text)
        form = Form1A()

        # Child
        _set(form, "child_first",          data, F102_CHILD_FIRST)
        _set(form, "child_middle",         data, F102_CHILD_MIDDLE)
        _set(form, "child_last",           data, F102_CHILD_LAST)
        _set(form, "sex",                  data, F102_SEX)
        _set(form, "date_of_birth",        data, F102_DATE_OF_BIRTH)
        _set(form, "place_of_birth",       data, F102_PLACE_OF_BIRTH)
        _set(form, "type_of_birth",        data, F102_TYPE_OF_BIRTH)
        _set(form, "birth_order",          data, F102_BIRTH_ORDER)

        # Mother
        _set(form, "mother_first",         data, F102_MOTHER_FIRST)
        _set(form, "mother_middle",        data, F102_MOTHER_MIDDLE)
        _set(form, "mother_last",          data, F102_MOTHER_LAST)
        _set(form, "mother_citizenship",   data, F102_MOTHER_CITIZENSHIP)
        _set(form, "mother_religion",      data, F102_MOTHER_RELIGION)
        _set(form, "mother_residence",     data, F102_MOTHER_RESIDENCE)

        # Father
        _set(form, "father_first",         data, F102_FATHER_FIRST)
        _set(form, "father_middle",        data, F102_FATHER_MIDDLE)
        _set(form, "father_last",          data, F102_FATHER_LAST)
        _set(form, "father_citizenship",   data, F102_FATHER_CITIZENSHIP)
        _set(form, "father_religion",      data, F102_FATHER_RELIGION)
        _set(form, "father_residence",     data, F102_FATHER_RESIDENCE)

        # Parents' marriage
        _set(form, "marriage_date",        data, F102_MARRIAGE_DATE)
        _set(form, "marriage_place",       data, F102_MARRIAGE_PLACE)

        # Registry
        _set(form, "registry_no",          data, F102_REGISTRY_NO)
        _set(form, "date_of_registration", data, F102_DATE_OF_REGISTRATION)

        return form

    # ── Form 2A (from Form 103 — Certificate of Death) ────────
    def fill_form_2a(self, ocr_text: str) -> Form2A:
        data = self.extractor.extract_form_103(ocr_text)
        form = Form2A()

        # Deceased
        _set(form, "deceased_first",       data, F103_DECEASED_FIRST)
        _set(form, "deceased_middle",      data, F103_DECEASED_MIDDLE)
        _set(form, "deceased_last",        data, F103_DECEASED_LAST)
        _set(form, "sex",                  data, F103_SEX)
        _set(form, "religion",             data, F103_RELIGION)
        _set(form, "age",                  data, F103_AGE)
        _set(form, "place_of_death",       data, F103_PLACE_OF_DEATH)
        _set(form, "date_of_death",        data, F103_DATE_OF_DEATH)
        _set(form, "citizenship",          data, F103_CITIZENSHIP)
        _set(form, "residence",            data, F103_RESIDENCE)
        _set(form, "civil_status",         data, F103_CIVIL_STATUS)
        _set(form, "occupation",           data, F103_OCCUPATION)

        # Causes
        _set(form, "cause_immediate",      data, F103_CAUSE_IMMEDIATE)
        _set(form, "cause_antecedent",     data, F103_CAUSE_ANTECEDENT)
        _set(form, "cause_underlying",     data, F103_CAUSE_UNDERLYING)

        # Registry
        _set(form, "registry_no",          data, F103_REGISTRY_NO)
        _set(form, "date_of_registration", data, F103_DATE_OF_REGISTRATION)

        return form

    # ── Form 3A (from Form 97 — Certificate of Marriage) ──────
    def fill_form_3a(self, ocr_text: str) -> Form3A:
        data    = self.extractor.extract_form_97(ocr_text)
        husband = SpouseOutput()
        wife    = SpouseOutput()
        form    = Form3A(husband=husband, wife=wife)

        # Husband
        _set(husband, "first",              data, F97_HUSBAND_FIRST)
        _set(husband, "middle",             data, F97_HUSBAND_MIDDLE)
        _set(husband, "last",               data, F97_HUSBAND_LAST)
        _set(husband, "date_of_birth",      data, F97_HUSBAND_DOB)
        _set(husband, "age",                data, F97_HUSBAND_AGE)
        _set(husband, "place_of_birth",     data, F97_HUSBAND_PLACE_BIRTH)
        _set(husband, "sex",                data, F97_HUSBAND_SEX)
        _set(husband, "citizenship",        data, F97_HUSBAND_CITIZENSHIP)
        _set(husband, "residence",          data, F97_HUSBAND_RESIDENCE)
        _set(husband, "religion",           data, F97_HUSBAND_RELIGION)
        _set(husband, "civil_status",       data, F97_HUSBAND_CIVIL_STATUS)
        _set(husband, "father_first",       data, F97_HUSBAND_FATHER_FIRST)
        _set(husband, "father_middle",      data, F97_HUSBAND_FATHER_MIDDLE)
        _set(husband, "father_last",        data, F97_HUSBAND_FATHER_LAST)
        _set(husband, "father_citizenship", data, F97_HUSBAND_FATHER_CITIZENSHIP)
        _set(husband, "mother_first",       data, F97_HUSBAND_MOTHER_FIRST)
        _set(husband, "mother_middle",      data, F97_HUSBAND_MOTHER_MIDDLE)
        _set(husband, "mother_last",        data, F97_HUSBAND_MOTHER_LAST)
        _set(husband, "mother_citizenship", data, F97_HUSBAND_MOTHER_CITIZENSHIP)

        # Wife
        _set(wife, "first",                 data, F97_WIFE_FIRST)
        _set(wife, "middle",                data, F97_WIFE_MIDDLE)
        _set(wife, "last",                  data, F97_WIFE_LAST)
        _set(wife, "date_of_birth",         data, F97_WIFE_DOB)
        _set(wife, "age",                   data, F97_WIFE_AGE)
        _set(wife, "place_of_birth",        data, F97_WIFE_PLACE_BIRTH)
        _set(wife, "sex",                   data, F97_WIFE_SEX)
        _set(wife, "citizenship",           data, F97_WIFE_CITIZENSHIP)
        _set(wife, "residence",             data, F97_WIFE_RESIDENCE)
        _set(wife, "religion",              data, F97_WIFE_RELIGION)
        _set(wife, "civil_status",          data, F97_WIFE_CIVIL_STATUS)
        _set(wife, "father_first",          data, F97_WIFE_FATHER_FIRST)
        _set(wife, "father_middle",         data, F97_WIFE_FATHER_MIDDLE)
        _set(wife, "father_last",           data, F97_WIFE_FATHER_LAST)
        _set(wife, "father_citizenship",    data, F97_WIFE_FATHER_CITIZENSHIP)
        _set(wife, "mother_first",          data, F97_WIFE_MOTHER_FIRST)
        _set(wife, "mother_middle",         data, F97_WIFE_MOTHER_MIDDLE)
        _set(wife, "mother_last",           data, F97_WIFE_MOTHER_LAST)
        _set(wife, "mother_citizenship",    data, F97_WIFE_MOTHER_CITIZENSHIP)

        # Shared event + registry
        _set(form, "place_of_marriage",    data, F97_PLACE_OF_MARRIAGE)
        _set(form, "date_of_marriage",     data, F97_DATE_OF_MARRIAGE)
        _set(form, "registry_no",          data, F97_REGISTRY_NO)
        _set(form, "date_of_registration", data, F97_DATE_OF_REGISTRATION)

        return form

    # ── Form 90 (Marriage License) ─────────────────────────────
    def fill_form_90(self, groom_ocr: str, bride_ocr: str) -> Form90:
        """
        groom_ocr = OCR from Male birth cert  → F90_GROOM_* labels
        bride_ocr = OCR from Female birth cert → F90_BRIDE_* labels
        MNB classify_sex() should have already confirmed which is which.
        """
        groom_data = self.extractor.extract_form_90_groom(groom_ocr)
        bride_data = self.extractor.extract_form_90_bride(bride_ocr)

        groom = ApplicantOutput()
        bride = ApplicantOutput()
        form  = Form90(groom=groom, bride=bride)

        # Shared registry (taken from groom cert)
        _set(form, "registry_no",               groom_data, F90_REGISTRY_NO)
        _set(form, "date_of_registration",       groom_data, F90_DATE_OF_REGISTRATION)

        # Groom
        _set(groom, "first",                    groom_data, F90_GROOM_FIRST)
        _set(groom, "middle",                   groom_data, F90_GROOM_MIDDLE)
        _set(groom, "last",                     groom_data, F90_GROOM_LAST)
        _set(groom, "date_of_birth",            groom_data, F90_GROOM_DATE_OF_BIRTH)
        _set(groom, "age",                      groom_data, F90_GROOM_AGE)
        _set(groom, "place_of_birth",           groom_data, F90_GROOM_PLACE_OF_BIRTH)
        _set(groom, "sex",                      groom_data, F90_GROOM_SEX)
        _set(groom, "citizenship",              groom_data, F90_GROOM_CITIZENSHIP)
        _set(groom, "residence",                groom_data, F90_GROOM_RESIDENCE)
        _set(groom, "religion",                 groom_data, F90_GROOM_RELIGION)
        _set(groom, "father_first",             groom_data, F90_GROOM_FATHER_FIRST)
        _set(groom, "father_middle",            groom_data, F90_GROOM_FATHER_MIDDLE)
        _set(groom, "father_last",              groom_data, F90_GROOM_FATHER_LAST)
        _set(groom, "father_citizenship",       groom_data, F90_GROOM_FATHER_CITIZENSHIP)
        _set(groom, "mother_first",             groom_data, F90_GROOM_MOTHER_FIRST)
        _set(groom, "mother_middle",            groom_data, F90_GROOM_MOTHER_MIDDLE)
        _set(groom, "mother_last",              groom_data, F90_GROOM_MOTHER_LAST)
        _set(groom, "mother_citizenship",       groom_data, F90_GROOM_MOTHER_CITIZENSHIP)
        _set(groom, "mother_residence",         groom_data, F90_GROOM_MOTHER_RESIDENCE)

        # Bride
        _set(bride, "first",                    bride_data, F90_BRIDE_FIRST)
        _set(bride, "middle",                   bride_data, F90_BRIDE_MIDDLE)
        _set(bride, "last",                     bride_data, F90_BRIDE_LAST)
        _set(bride, "date_of_birth",            bride_data, F90_BRIDE_DATE_OF_BIRTH)
        _set(bride, "age",                      bride_data, F90_BRIDE_AGE)
        _set(bride, "place_of_birth",           bride_data, F90_BRIDE_PLACE_OF_BIRTH)
        _set(bride, "sex",                      bride_data, F90_BRIDE_SEX)
        _set(bride, "citizenship",              bride_data, F90_BRIDE_CITIZENSHIP)
        _set(bride, "residence",                bride_data, F90_BRIDE_RESIDENCE)
        _set(bride, "religion",                 bride_data, F90_BRIDE_RELIGION)
        _set(bride, "father_first",             bride_data, F90_BRIDE_FATHER_FIRST)
        _set(bride, "father_middle",            bride_data, F90_BRIDE_FATHER_MIDDLE)
        _set(bride, "father_last",              bride_data, F90_BRIDE_FATHER_LAST)
        _set(bride, "father_citizenship",       bride_data, F90_BRIDE_FATHER_CITIZENSHIP)
        _set(bride, "mother_first",             bride_data, F90_BRIDE_MOTHER_FIRST)
        _set(bride, "mother_middle",            bride_data, F90_BRIDE_MOTHER_MIDDLE)
        _set(bride, "mother_last",              bride_data, F90_BRIDE_MOTHER_LAST)
        _set(bride, "mother_citizenship",       bride_data, F90_BRIDE_MOTHER_CITIZENSHIP)
        _set(bride, "mother_residence",         bride_data, F90_BRIDE_MOTHER_RESIDENCE)

        return form

    # ── Utility ────────────────────────────────────────────────
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
