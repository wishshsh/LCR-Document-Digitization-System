# =============================================================
# spacyNER/labels.py
# =============================================================
# SINGLE SOURCE OF TRUTH for every NER tag string and every
# output field name used across all four forms.
#
# Every other file imports from here — nothing is hardcoded
# anywhere else.
#
# ─────────────────────────────────────────────────────────────
# HOW THE PIPELINE CONNECTS
# ─────────────────────────────────────────────────────────────
#
#   Scanned Form Image
#       │
#       ▼  CRNN + CTC (OCR)
#   Raw OCR Text
#       │
#       ▼  MNB Classifier
#   Form Type Identified
#       │
#       ├─ Certifications Page → Form 102 / 103 / 97
#       │       ▼
#       │   spaCy NER → F102_* / F103_* / F97_* labels
#       │       ▼
#       │   name_assembler → assembled full names
#       │       ▼
#       │   autofill → Form1A / Form2A / Form3A objects
#       │
#       └─ Marriage License Receipt → Form 90 / Accountable Form No. 54
#               ▼
#           spaCy NER → F90_GROOM_* / F90_BRIDE_* labels
#               ▼
#           name_assembler → name_of_groom / name_of_bride
#               ▼
#           autofill → Form54(name_of_groom, age_of_groom, ...)
#
# ─────────────────────────────────────────────────────────────
# OUTPUT FIELDS — what gets printed on each digital form
# ─────────────────────────────────────────────────────────────
#
#  Form 1A  (Certificate of Live Birth)
#    registry_number            date_of_registration
#    name_of_child              sex
#    date_of_birth              place_of_birth
#    name_of_mother             nationality_of_mother
#    name_of_father             nationality_of_father
#    date_of_marriage_of_parents    place_of_marriage_of_parents
#
#  Form 2A  (Certificate of Death)
#    registry_number            date_of_registration
#    name_of_deceased           sex
#    age                        civil_status
#    nationality                date_of_death
#    place_of_death             cause_of_death
#
#  Form 3A  (Certificate of Marriage) — same fields for husband & wife
#    name                       age
#    nationality                name_of_mother
#    nationality_of_mother      name_of_father
#    nationality_of_father
#    date_of_registration       date_of_marriage    place_of_marriage
#
#  Form 54  (Marriage License and Fee Receipt / Form 90 / Accountable Form No. 54)
#    registry_number            date_of_registration
#    name_of_groom              age_of_groom         residence_of_groom
#    name_of_bride              age_of_bride         residence_of_bride
#    date_of_issuance
# =============================================================


# ═════════════════════════════════════════════════════════════
# FORM 102  →  FORM 1A   Certificate of Live Birth
# ═════════════════════════════════════════════════════════════

# — Registry ——————————————————————————————————————————————————
F102_REGISTRY_NO          = "F102_REGISTRY_NO"           # → registry_number
F102_DATE_OF_REGISTRATION = "F102_DATE_OF_REGISTRATION"  # → date_of_registration

# — Child name parts  (assembled → name_of_child) ————————————
F102_CHILD_FIRST  = "F102_CHILD_FIRST"
F102_CHILD_MIDDLE = "F102_CHILD_MIDDLE"
F102_CHILD_LAST   = "F102_CHILD_LAST"

# — Child details —————————————————————————————————————————————
F102_SEX            = "F102_SEX"            # → sex
F102_DATE_OF_BIRTH  = "F102_DATE_OF_BIRTH"  # → date_of_birth
F102_PLACE_OF_BIRTH = "F102_PLACE_OF_BIRTH" # → place_of_birth
F102_TYPE_OF_BIRTH  = "F102_TYPE_OF_BIRTH"  # supplementary
F102_BIRTH_ORDER    = "F102_BIRTH_ORDER"    # supplementary

# — Mother name parts  (assembled → name_of_mother) ——————————
F102_MOTHER_FIRST  = "F102_MOTHER_FIRST"
F102_MOTHER_MIDDLE = "F102_MOTHER_MIDDLE"
F102_MOTHER_LAST   = "F102_MOTHER_LAST"

# — Mother details ————————————————————————————————————————————
F102_MOTHER_CITIZENSHIP = "F102_MOTHER_CITIZENSHIP"  # → nationality_of_mother
F102_MOTHER_RELIGION    = "F102_MOTHER_RELIGION"
F102_MOTHER_RESIDENCE   = "F102_MOTHER_RESIDENCE"

# — Father name parts  (assembled → name_of_father) ——————————
F102_FATHER_FIRST  = "F102_FATHER_FIRST"
F102_FATHER_MIDDLE = "F102_FATHER_MIDDLE"
F102_FATHER_LAST   = "F102_FATHER_LAST"

# — Father details ————————————————————————————————————————————
F102_FATHER_CITIZENSHIP = "F102_FATHER_CITIZENSHIP"  # → nationality_of_father
F102_FATHER_RELIGION    = "F102_FATHER_RELIGION"
F102_FATHER_RESIDENCE   = "F102_FATHER_RESIDENCE"

# — Parents' marriage —————————————————————————————————————————
F102_MARRIAGE_DATE  = "F102_MARRIAGE_DATE"   # → date_of_marriage_of_parents
F102_MARRIAGE_PLACE = "F102_MARRIAGE_PLACE"  # → place_of_marriage_of_parents

FORM_102_LABELS = [
    F102_REGISTRY_NO, F102_DATE_OF_REGISTRATION,
    F102_CHILD_FIRST, F102_CHILD_MIDDLE, F102_CHILD_LAST,
    F102_SEX, F102_DATE_OF_BIRTH, F102_PLACE_OF_BIRTH,
    F102_TYPE_OF_BIRTH, F102_BIRTH_ORDER,
    F102_MOTHER_FIRST, F102_MOTHER_MIDDLE, F102_MOTHER_LAST,
    F102_MOTHER_CITIZENSHIP, F102_MOTHER_RELIGION, F102_MOTHER_RESIDENCE,
    F102_FATHER_FIRST, F102_FATHER_MIDDLE, F102_FATHER_LAST,
    F102_FATHER_CITIZENSHIP, F102_FATHER_RELIGION, F102_FATHER_RESIDENCE,
    F102_MARRIAGE_DATE, F102_MARRIAGE_PLACE,
]

# Used by name_assembler.py — (first_label, middle_label, last_label, output_field)
NAME_GROUPS_102 = [
    (F102_CHILD_FIRST,  F102_CHILD_MIDDLE,  F102_CHILD_LAST,  "name_of_child"),
    (F102_MOTHER_FIRST, F102_MOTHER_MIDDLE, F102_MOTHER_LAST, "name_of_mother"),
    (F102_FATHER_FIRST, F102_FATHER_MIDDLE, F102_FATHER_LAST, "name_of_father"),
]

# Used by autofill.py — NER label → Form 1A field name
OUTPUT_MAP_1A = {
    F102_REGISTRY_NO:          "registry_number",
    F102_DATE_OF_REGISTRATION: "date_of_registration",
    # name_of_child          ← assembled by name_assembler
    F102_SEX:                  "sex",
    F102_DATE_OF_BIRTH:        "date_of_birth",
    F102_PLACE_OF_BIRTH:       "place_of_birth",
    F102_TYPE_OF_BIRTH:        "type_of_birth",
    F102_BIRTH_ORDER:          "birth_order",
    # name_of_mother         ← assembled by name_assembler
    F102_MOTHER_CITIZENSHIP:   "nationality_of_mother",
    # name_of_father         ← assembled by name_assembler
    F102_FATHER_CITIZENSHIP:   "nationality_of_father",
    F102_MARRIAGE_DATE:        "date_of_marriage_of_parents",
    F102_MARRIAGE_PLACE:       "place_of_marriage_of_parents",
}

OUTPUT_FIELDS_1A = [
    "registry_number", "date_of_registration",
    "name_of_child", "sex", "date_of_birth", "place_of_birth",
    "name_of_mother", "nationality_of_mother",
    "name_of_father", "nationality_of_father",
    "date_of_marriage_of_parents", "place_of_marriage_of_parents",
]


# ═════════════════════════════════════════════════════════════
# FORM 103  →  FORM 2A   Certificate of Death
# ═════════════════════════════════════════════════════════════

# — Registry ——————————————————————————————————————————————————
F103_REGISTRY_NO          = "F103_REGISTRY_NO"           # → registry_number
F103_DATE_OF_REGISTRATION = "F103_DATE_OF_REGISTRATION"  # → date_of_registration

# — Deceased name parts  (assembled → name_of_deceased) ——————
F103_DECEASED_FIRST  = "F103_DECEASED_FIRST"
F103_DECEASED_MIDDLE = "F103_DECEASED_MIDDLE"
F103_DECEASED_LAST   = "F103_DECEASED_LAST"

# — Deceased details ——————————————————————————————————————————
F103_SEX             = "F103_SEX"            # → sex
F103_AGE             = "F103_AGE"            # → age
F103_CIVIL_STATUS    = "F103_CIVIL_STATUS"   # → civil_status
F103_CITIZENSHIP     = "F103_CITIZENSHIP"    # → nationality
F103_DATE_OF_DEATH   = "F103_DATE_OF_DEATH"  # → date_of_death
F103_PLACE_OF_DEATH  = "F103_PLACE_OF_DEATH" # → place_of_death
F103_CAUSE_IMMEDIATE = "F103_CAUSE_IMMEDIATE"# → cause_of_death
F103_CAUSE_ANTECEDENT= "F103_CAUSE_ANTECEDENT"
F103_CAUSE_UNDERLYING= "F103_CAUSE_UNDERLYING"
F103_RELIGION        = "F103_RELIGION"
F103_OCCUPATION      = "F103_OCCUPATION"
F103_RESIDENCE       = "F103_RESIDENCE"

FORM_103_LABELS = [
    F103_REGISTRY_NO, F103_DATE_OF_REGISTRATION,
    F103_DECEASED_FIRST, F103_DECEASED_MIDDLE, F103_DECEASED_LAST,
    F103_SEX, F103_AGE, F103_CIVIL_STATUS, F103_CITIZENSHIP,
    F103_DATE_OF_DEATH, F103_PLACE_OF_DEATH,
    F103_CAUSE_IMMEDIATE, F103_CAUSE_ANTECEDENT, F103_CAUSE_UNDERLYING,
    F103_RELIGION, F103_OCCUPATION, F103_RESIDENCE,
]

NAME_GROUPS_103 = [
    (F103_DECEASED_FIRST, F103_DECEASED_MIDDLE, F103_DECEASED_LAST, "name_of_deceased"),
]

OUTPUT_MAP_2A = {
    F103_REGISTRY_NO:          "registry_number",
    F103_DATE_OF_REGISTRATION: "date_of_registration",
    # name_of_deceased       ← assembled by name_assembler
    F103_SEX:                  "sex",
    F103_AGE:                  "age",
    F103_CIVIL_STATUS:         "civil_status",
    F103_CITIZENSHIP:          "nationality",
    F103_DATE_OF_DEATH:        "date_of_death",
    F103_PLACE_OF_DEATH:       "place_of_death",
    F103_CAUSE_IMMEDIATE:      "cause_of_death",
    F103_CAUSE_ANTECEDENT:     "cause_antecedent",
    F103_CAUSE_UNDERLYING:     "cause_underlying",
    F103_RELIGION:             "religion",
    F103_OCCUPATION:           "occupation",
    F103_RESIDENCE:            "residence",
}

OUTPUT_FIELDS_2A = [
    "registry_number", "date_of_registration",
    "name_of_deceased", "sex", "age", "civil_status",
    "nationality", "date_of_death", "place_of_death", "cause_of_death",
]


# ═════════════════════════════════════════════════════════════
# FORM 97  →  FORM 3A   Certificate of Marriage
# ═════════════════════════════════════════════════════════════

# — Event / registry ——————————————————————————————————————————
F97_REGISTRY_NO          = "F97_REGISTRY_NO"
F97_DATE_OF_REGISTRATION = "F97_DATE_OF_REGISTRATION"
F97_DATE_OF_MARRIAGE     = "F97_DATE_OF_MARRIAGE"
F97_PLACE_OF_MARRIAGE    = "F97_PLACE_OF_MARRIAGE"

# — Husband name parts  (assembled → husband.name) ———————————
F97_HUSBAND_FIRST  = "F97_HUSBAND_FIRST"
F97_HUSBAND_MIDDLE = "F97_HUSBAND_MIDDLE"
F97_HUSBAND_LAST   = "F97_HUSBAND_LAST"

# — Husband details ———————————————————————————————————————————
F97_HUSBAND_DOB           = "F97_HUSBAND_DOB"
F97_HUSBAND_AGE           = "F97_HUSBAND_AGE"
F97_HUSBAND_PLACE_BIRTH   = "F97_HUSBAND_PLACE_BIRTH"
F97_HUSBAND_SEX           = "F97_HUSBAND_SEX"
F97_HUSBAND_CITIZENSHIP   = "F97_HUSBAND_CITIZENSHIP"
F97_HUSBAND_RESIDENCE     = "F97_HUSBAND_RESIDENCE"
F97_HUSBAND_RELIGION      = "F97_HUSBAND_RELIGION"
F97_HUSBAND_CIVIL_STATUS  = "F97_HUSBAND_CIVIL_STATUS"

# — Husband's father ——————————————————————————————————————————
F97_HUSBAND_FATHER_FIRST       = "F97_HUSBAND_FATHER_FIRST"
F97_HUSBAND_FATHER_MIDDLE      = "F97_HUSBAND_FATHER_MIDDLE"
F97_HUSBAND_FATHER_LAST        = "F97_HUSBAND_FATHER_LAST"
F97_HUSBAND_FATHER_CITIZENSHIP = "F97_HUSBAND_FATHER_CITIZENSHIP"

# — Husband's mother ——————————————————————————————————————————
F97_HUSBAND_MOTHER_FIRST       = "F97_HUSBAND_MOTHER_FIRST"
F97_HUSBAND_MOTHER_MIDDLE      = "F97_HUSBAND_MOTHER_MIDDLE"
F97_HUSBAND_MOTHER_LAST        = "F97_HUSBAND_MOTHER_LAST"
F97_HUSBAND_MOTHER_CITIZENSHIP = "F97_HUSBAND_MOTHER_CITIZENSHIP"

# — Wife name parts  (assembled → wife.name) —————————————————
F97_WIFE_FIRST  = "F97_WIFE_FIRST"
F97_WIFE_MIDDLE = "F97_WIFE_MIDDLE"
F97_WIFE_LAST   = "F97_WIFE_LAST"

# — Wife details ——————————————————————————————————————————————
F97_WIFE_DOB          = "F97_WIFE_DOB"
F97_WIFE_AGE          = "F97_WIFE_AGE"
F97_WIFE_PLACE_BIRTH  = "F97_WIFE_PLACE_BIRTH"
F97_WIFE_SEX          = "F97_WIFE_SEX"
F97_WIFE_CITIZENSHIP  = "F97_WIFE_CITIZENSHIP"
F97_WIFE_RESIDENCE    = "F97_WIFE_RESIDENCE"
F97_WIFE_RELIGION     = "F97_WIFE_RELIGION"
F97_WIFE_CIVIL_STATUS = "F97_WIFE_CIVIL_STATUS"

# — Wife's father ————————————————————————————————————————————
F97_WIFE_FATHER_FIRST       = "F97_WIFE_FATHER_FIRST"
F97_WIFE_FATHER_MIDDLE      = "F97_WIFE_FATHER_MIDDLE"
F97_WIFE_FATHER_LAST        = "F97_WIFE_FATHER_LAST"
F97_WIFE_FATHER_CITIZENSHIP = "F97_WIFE_FATHER_CITIZENSHIP"

# — Wife's mother ————————————————————————————————————————————
F97_WIFE_MOTHER_FIRST       = "F97_WIFE_MOTHER_FIRST"
F97_WIFE_MOTHER_MIDDLE      = "F97_WIFE_MOTHER_MIDDLE"
F97_WIFE_MOTHER_LAST        = "F97_WIFE_MOTHER_LAST"
F97_WIFE_MOTHER_CITIZENSHIP = "F97_WIFE_MOTHER_CITIZENSHIP"

FORM_97_LABELS = [
    F97_REGISTRY_NO, F97_DATE_OF_REGISTRATION,
    F97_DATE_OF_MARRIAGE, F97_PLACE_OF_MARRIAGE,
    F97_HUSBAND_FIRST, F97_HUSBAND_MIDDLE, F97_HUSBAND_LAST,
    F97_HUSBAND_DOB, F97_HUSBAND_AGE, F97_HUSBAND_PLACE_BIRTH,
    F97_HUSBAND_SEX, F97_HUSBAND_CITIZENSHIP, F97_HUSBAND_RESIDENCE,
    F97_HUSBAND_RELIGION, F97_HUSBAND_CIVIL_STATUS,
    F97_HUSBAND_FATHER_FIRST, F97_HUSBAND_FATHER_MIDDLE, F97_HUSBAND_FATHER_LAST,
    F97_HUSBAND_FATHER_CITIZENSHIP,
    F97_HUSBAND_MOTHER_FIRST, F97_HUSBAND_MOTHER_MIDDLE, F97_HUSBAND_MOTHER_LAST,
    F97_HUSBAND_MOTHER_CITIZENSHIP,
    F97_WIFE_FIRST, F97_WIFE_MIDDLE, F97_WIFE_LAST,
    F97_WIFE_DOB, F97_WIFE_AGE, F97_WIFE_PLACE_BIRTH,
    F97_WIFE_SEX, F97_WIFE_CITIZENSHIP, F97_WIFE_RESIDENCE,
    F97_WIFE_RELIGION, F97_WIFE_CIVIL_STATUS,
    F97_WIFE_FATHER_FIRST, F97_WIFE_FATHER_MIDDLE, F97_WIFE_FATHER_LAST,
    F97_WIFE_FATHER_CITIZENSHIP,
    F97_WIFE_MOTHER_FIRST, F97_WIFE_MOTHER_MIDDLE, F97_WIFE_MOTHER_LAST,
    F97_WIFE_MOTHER_CITIZENSHIP,
]

NAME_GROUPS_97_HUSBAND = [
    (F97_HUSBAND_FIRST,        F97_HUSBAND_MIDDLE,        F97_HUSBAND_LAST,        "name"),
    (F97_HUSBAND_FATHER_FIRST, F97_HUSBAND_FATHER_MIDDLE, F97_HUSBAND_FATHER_LAST, "name_of_father"),
    (F97_HUSBAND_MOTHER_FIRST, F97_HUSBAND_MOTHER_MIDDLE, F97_HUSBAND_MOTHER_LAST, "name_of_mother"),
]
NAME_GROUPS_97_WIFE = [
    (F97_WIFE_FIRST,        F97_WIFE_MIDDLE,        F97_WIFE_LAST,        "name"),
    (F97_WIFE_FATHER_FIRST, F97_WIFE_FATHER_MIDDLE, F97_WIFE_FATHER_LAST, "name_of_father"),
    (F97_WIFE_MOTHER_FIRST, F97_WIFE_MOTHER_MIDDLE, F97_WIFE_MOTHER_LAST, "name_of_mother"),
]

OUTPUT_MAP_3A_HUSBAND = {
    F97_HUSBAND_AGE:                 "age",
    F97_HUSBAND_CITIZENSHIP:         "nationality",
    F97_HUSBAND_FATHER_CITIZENSHIP:  "nationality_of_father",
    F97_HUSBAND_MOTHER_CITIZENSHIP:  "nationality_of_mother",
}
OUTPUT_MAP_3A_WIFE = {
    F97_WIFE_AGE:                    "age",
    F97_WIFE_CITIZENSHIP:            "nationality",
    F97_WIFE_FATHER_CITIZENSHIP:     "nationality_of_father",
    F97_WIFE_MOTHER_CITIZENSHIP:     "nationality_of_mother",
}
OUTPUT_MAP_3A_EVENT = {
    F97_REGISTRY_NO:          "registry_number",
    F97_DATE_OF_REGISTRATION: "date_of_registration",
    F97_DATE_OF_MARRIAGE:     "date_of_marriage",
    F97_PLACE_OF_MARRIAGE:    "place_of_marriage",
}

OUTPUT_FIELDS_3A_SPOUSE = [
    "name", "age", "nationality",
    "name_of_mother", "nationality_of_mother",
    "name_of_father", "nationality_of_father",
]
OUTPUT_FIELDS_3A_EVENT = [
    "registry_number", "date_of_registration",
    "date_of_marriage", "place_of_marriage",
]


# ═════════════════════════════════════════════════════════════
# FORM 90 (Accountable Form No. 54 / Form No. 10)
# → FORM 54   Marriage License and Fee Receipt of Two Pesos
# ═════════════════════════════════════════════════════════════
# Source: Scanned Marriage License and Fee Receipt
# (the issued license document itself, NOT birth certificates)
#
# Required output fields for Form 54:
#   name_of_groom         age_of_groom         residence_of_groom
#   name_of_bride         age_of_bride         residence_of_bride
#   date_of_issuance
# ═════════════════════════════════════════════════════════════

# — Registry ——————————————————————————————————————————————————
F90_REGISTRY_NO          = "F90_REGISTRY_NO"           # → registry_number
F90_DATE_OF_REGISTRATION = "F90_DATE_OF_REGISTRATION"  # → date_of_registration

# — Groom name parts  (assembled → name_of_groom) —————————————
F90_GROOM_FIRST  = "F90_GROOM_FIRST"
F90_GROOM_MIDDLE = "F90_GROOM_MIDDLE"
F90_GROOM_LAST   = "F90_GROOM_LAST"

# — Groom details —————————————————————————————————————————————
F90_GROOM_AGE       = "F90_GROOM_AGE"       # → age_of_groom
F90_GROOM_RESIDENCE = "F90_GROOM_RESIDENCE" # → residence_of_groom

# — Bride name parts  (assembled → name_of_bride) —————————————
F90_BRIDE_FIRST  = "F90_BRIDE_FIRST"
F90_BRIDE_MIDDLE = "F90_BRIDE_MIDDLE"
F90_BRIDE_LAST   = "F90_BRIDE_LAST"

# — Bride details —————————————————————————————————————————————
F90_BRIDE_AGE       = "F90_BRIDE_AGE"       # → age_of_bride
F90_BRIDE_RESIDENCE = "F90_BRIDE_RESIDENCE" # → residence_of_bride

# — Issuance date —————————————————————————————————————————————
F90_DATE_OF_ISSUANCE = "F90_DATE_OF_ISSUANCE"  # → date_of_issuance

# ── Label list ────────────────────────────────────────────────
FORM_90_LABELS = [
    F90_REGISTRY_NO, F90_DATE_OF_REGISTRATION,
    F90_GROOM_FIRST, F90_GROOM_MIDDLE, F90_GROOM_LAST,
    F90_GROOM_AGE, F90_GROOM_RESIDENCE,
    F90_BRIDE_FIRST, F90_BRIDE_MIDDLE, F90_BRIDE_LAST,
    F90_BRIDE_AGE, F90_BRIDE_RESIDENCE,
    F90_DATE_OF_ISSUANCE,
]

# ── Name assembly groups ──────────────────────────────────────
# (first_label, middle_label, last_label, output_field)
NAME_GROUPS_90_GROOM = [
    (F90_GROOM_FIRST, F90_GROOM_MIDDLE, F90_GROOM_LAST, "name_of_groom"),
]

NAME_GROUPS_90_BRIDE = [
    (F90_BRIDE_FIRST, F90_BRIDE_MIDDLE, F90_BRIDE_LAST, "name_of_bride"),
]

# ── Output map ────────────────────────────────────────────────
OUTPUT_MAP_90 = {
    F90_REGISTRY_NO:          "registry_number",
    F90_DATE_OF_REGISTRATION: "date_of_registration",
    # name_of_groom           ← assembled by name_assembler
    F90_GROOM_AGE:            "age_of_groom",
    F90_GROOM_RESIDENCE:      "residence_of_groom",
    # name_of_bride           ← assembled by name_assembler
    F90_BRIDE_AGE:            "age_of_bride",
    F90_BRIDE_RESIDENCE:      "residence_of_bride",
    F90_DATE_OF_ISSUANCE:     "date_of_issuance",
}

OUTPUT_FIELDS_54 = [
    "registry_number", "date_of_registration",
    "name_of_groom", "age_of_groom", "residence_of_groom",
    "name_of_bride", "age_of_bride", "residence_of_bride",
    "date_of_issuance",
]


# ═════════════════════════════════════════════════════════════
# ALL LABELS — registered with spaCy NER at model init
# ═════════════════════════════════════════════════════════════
ALL_LABELS = FORM_102_LABELS + FORM_103_LABELS + FORM_97_LABELS + FORM_90_LABELS
