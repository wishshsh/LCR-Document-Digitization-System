# =============================================================
# spacyNER/models.py
# =============================================================
# Dataclasses for the four digital output forms.
# Field names EXACTLY match OUTPUT_FIELDS_* in labels.py.
#
# Imported by:
#   autofill.py   — instantiates and populates these classes
#   test_suite.py — checks attribute names and types
# =============================================================

from dataclasses import dataclass, field, asdict
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Form 1A — Certificate of Live Birth
# Output fields (Form 1A layout):
#   Registry Number · Date of Registration
#   Name of Child · Sex · Date of Birth · Place of Birth
#   Name of Mother · Nationality of Mother
#   Name of Father · Nationality of Father
#   Date of Marriage of Parents · Place of Marriage of Parents
# ─────────────────────────────────────────────────────────────
@dataclass
class Form1A:
    registry_number:               Optional[str] = None
    date_of_registration:          Optional[str] = None
    name_of_child:                 Optional[str] = None  # assembled First+Middle+Last
    sex:                           Optional[str] = None
    date_of_birth:                 Optional[str] = None
    place_of_birth:                Optional[str] = None
    name_of_mother:                Optional[str] = None  # assembled First+Middle+Last
    nationality_of_mother:         Optional[str] = None  # from F102_MOTHER_CITIZENSHIP
    name_of_father:                Optional[str] = None  # assembled First+Middle+Last
    nationality_of_father:         Optional[str] = None  # from F102_FATHER_CITIZENSHIP
    date_of_marriage_of_parents:   Optional[str] = None
    place_of_marriage_of_parents:  Optional[str] = None
    # supplementary
    type_of_birth:                 Optional[str] = None
    birth_order:                   Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# ─────────────────────────────────────────────────────────────
# Form 2A — Certificate of Death
# Output fields (Form 2A layout):
#   Registry Number · Date of Registration
#   Name of Deceased · Sex · Age · Civil Status
#   Nationality · Date of Death · Place of Death · Cause of Death
# ─────────────────────────────────────────────────────────────
@dataclass
class Form2A:
    registry_number:       Optional[str] = None
    date_of_registration:  Optional[str] = None
    name_of_deceased:      Optional[str] = None  # assembled First+Middle+Last
    sex:                   Optional[str] = None
    age:                   Optional[str] = None
    civil_status:          Optional[str] = None
    nationality:           Optional[str] = None  # from F103_CITIZENSHIP
    date_of_death:         Optional[str] = None
    place_of_death:        Optional[str] = None
    cause_of_death:        Optional[str] = None  # from F103_CAUSE_IMMEDIATE
    # supplementary
    cause_antecedent:      Optional[str] = None
    cause_underlying:      Optional[str] = None
    religion:              Optional[str] = None
    occupation:            Optional[str] = None
    residence:             Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# ─────────────────────────────────────────────────────────────
# SpouseOutput — reused for husband and wife in Form 3A
# Output fields per spouse (Form 3A layout):
#   Name · Age · Nationality
#   Name of Mother · Nationality of Mother
#   Name of Father · Nationality of Father
# ─────────────────────────────────────────────────────────────
@dataclass
class SpouseOutput:
    name:                  Optional[str] = None  # assembled First+Middle+Last
    age:                   Optional[str] = None
    nationality:           Optional[str] = None  # from F97_*_CITIZENSHIP
    name_of_mother:        Optional[str] = None  # assembled
    nationality_of_mother: Optional[str] = None
    name_of_father:        Optional[str] = None  # assembled
    nationality_of_father: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# ─────────────────────────────────────────────────────────────
# Form 3A — Certificate of Marriage
# Shared event fields:
#   Date of Registration · Date of Marriage · Place of Marriage
# ─────────────────────────────────────────────────────────────
@dataclass
class Form3A:
    husband:              SpouseOutput = field(default_factory=SpouseOutput)
    wife:                 SpouseOutput = field(default_factory=SpouseOutput)
    registry_number:      Optional[str] = None
    date_of_registration: Optional[str] = None
    date_of_marriage:     Optional[str] = None
    place_of_marriage:    Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "husband":              self.husband.to_dict(),
            "wife":                 self.wife.to_dict(),
            "registry_number":      self.registry_number,
            "date_of_registration": self.date_of_registration,
            "date_of_marriage":     self.date_of_marriage,
            "place_of_marriage":    self.place_of_marriage,
        }


# ─────────────────────────────────────────────────────────────
# Form 54 — Marriage License and Fee Receipt
# (Accountable Form No. 54 / Form No. 10 / Form 90)
#
# Extracted from the issued Marriage License document.
# Required output fields:
#   name_of_groom    age_of_groom    residence_of_groom
#   name_of_bride    age_of_bride    residence_of_bride
#   date_of_issuance
# ─────────────────────────────────────────────────────────────
@dataclass
class Form54:
    registry_number:     Optional[str] = None
    date_of_registration: Optional[str] = None
    name_of_groom:       Optional[str] = None  # assembled First+Middle+Last
    age_of_groom:        Optional[str] = None
    residence_of_groom:  Optional[str] = None
    name_of_bride:       Optional[str] = None  # assembled First+Middle+Last
    age_of_bride:        Optional[str] = None
    residence_of_bride:  Optional[str] = None
    date_of_issuance:    Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


# Keep Form90 as an alias so existing imports don't break
Form90 = Form54
