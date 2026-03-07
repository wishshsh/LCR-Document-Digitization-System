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
#       ▼  spaCy NER  (model trained on labels defined HERE)
#   Extracted dict  {F102_CHILD_FIRST: "Juan", ...}
#       │
#       ▼  name_assembler.py  (uses NAME_GROUPS_* from here)
#   Assembled dict  {name_of_child: "Juan dela Cruz Santos", ...}
#       │
#       ▼  autofill.py  (uses OUTPUT_MAP_* from here)
#   Digital Form object  Form1A(name_of_child="Juan dela Cruz Santos")
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
#  Form 90  (Marriage License) — same fields for groom & bride
#    name_of_applicant          date_of_birth
#    age                        place_of_birth
#    sex                        citizenship
#    residence                  religion
#    name_of_father             father_citizenship
#    maiden_name_of_mother      mother_citizenship
#    mother_residence
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

# Ordered output fields as they appear on Form 1A
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
F103_SEX            = "F103_SEX"            # → sex
F103_AGE            = "F103_AGE"            # → age
F103_CIVIL_STATUS   = "F103_CIVIL_STATUS"   # → civil_status
F103_CITIZENSHIP    = "F103_CITIZENSHIP"    # → nationality
F103_DATE_OF_DEATH  = "F103_DATE_OF_DEATH"  # → date_of_death
F103_PLACE_OF_DEATH = "F103_PLACE_OF_DEATH" # → place_of_death
F103_CAUSE_IMMEDIATE= "F103_CAUSE_IMMEDIATE"# → cause_of_death
F103_CAUSE_ANTECEDENT="F103_CAUSE_ANTECEDENT"
F103_CAUSE_UNDERLYING="F103_CAUSE_UNDERLYING"
F103_RELIGION       = "F103_RELIGION"
F103_OCCUPATION     = "F103_OCCUPATION"
F103_RESIDENCE      = "F103_RESIDENCE"

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
# Form 97 has two columns: HUSBAND and WIFE.
# Both share the same field structure.

# — Event / registry ——————————————————————————————————————————
F97_REGISTRY_NO          = "F97_REGISTRY_NO"
F97_DATE_OF_REGISTRATION = "F97_DATE_OF_REGISTRATION"  # → date_of_registration
F97_DATE_OF_MARRIAGE     = "F97_DATE_OF_MARRIAGE"      # → date_of_marriage
F97_PLACE_OF_MARRIAGE    = "F97_PLACE_OF_MARRIAGE"     # → place_of_marriage

# — Husband name parts  (assembled → husband.name) ———————————
F97_HUSBAND_FIRST  = "F97_HUSBAND_FIRST"
F97_HUSBAND_MIDDLE = "F97_HUSBAND_MIDDLE"
F97_HUSBAND_LAST   = "F97_HUSBAND_LAST"

# — Husband details ———————————————————————————————————————————
F97_HUSBAND_DOB           = "F97_HUSBAND_DOB"
F97_HUSBAND_AGE           = "F97_HUSBAND_AGE"          # → husband.age
F97_HUSBAND_PLACE_BIRTH   = "F97_HUSBAND_PLACE_BIRTH"
F97_HUSBAND_SEX           = "F97_HUSBAND_SEX"
F97_HUSBAND_CITIZENSHIP   = "F97_HUSBAND_CITIZENSHIP"  # → husband.nationality
F97_HUSBAND_RESIDENCE     = "F97_HUSBAND_RESIDENCE"
F97_HUSBAND_RELIGION      = "F97_HUSBAND_RELIGION"
F97_HUSBAND_CIVIL_STATUS  = "F97_HUSBAND_CIVIL_STATUS"

# — Husband's father  (assembled → husband.name_of_father) ————
F97_HUSBAND_FATHER_FIRST       = "F97_HUSBAND_FATHER_FIRST"
F97_HUSBAND_FATHER_MIDDLE      = "F97_HUSBAND_FATHER_MIDDLE"
F97_HUSBAND_FATHER_LAST        = "F97_HUSBAND_FATHER_LAST"
F97_HUSBAND_FATHER_CITIZENSHIP = "F97_HUSBAND_FATHER_CITIZENSHIP"  # → husband.nationality_of_father

# — Husband's mother  (assembled → husband.name_of_mother) ————
F97_HUSBAND_MOTHER_FIRST       = "F97_HUSBAND_MOTHER_FIRST"
F97_HUSBAND_MOTHER_MIDDLE      = "F97_HUSBAND_MOTHER_MIDDLE"
F97_HUSBAND_MOTHER_LAST        = "F97_HUSBAND_MOTHER_LAST"
F97_HUSBAND_MOTHER_CITIZENSHIP = "F97_HUSBAND_MOTHER_CITIZENSHIP"  # → husband.nationality_of_mother

# — Wife name parts  (assembled → wife.name) —————————————————
F97_WIFE_FIRST  = "F97_WIFE_FIRST"
F97_WIFE_MIDDLE = "F97_WIFE_MIDDLE"
F97_WIFE_LAST   = "F97_WIFE_LAST"

# — Wife details ——————————————————————————————————————————————
F97_WIFE_DOB          = "F97_WIFE_DOB"
F97_WIFE_AGE          = "F97_WIFE_AGE"          # → wife.age
F97_WIFE_PLACE_BIRTH  = "F97_WIFE_PLACE_BIRTH"
F97_WIFE_SEX          = "F97_WIFE_SEX"
F97_WIFE_CITIZENSHIP  = "F97_WIFE_CITIZENSHIP"  # → wife.nationality
F97_WIFE_RESIDENCE    = "F97_WIFE_RESIDENCE"
F97_WIFE_RELIGION     = "F97_WIFE_RELIGION"
F97_WIFE_CIVIL_STATUS = "F97_WIFE_CIVIL_STATUS"

# — Wife's father  (assembled → wife.name_of_father) —————————
F97_WIFE_FATHER_FIRST       = "F97_WIFE_FATHER_FIRST"
F97_WIFE_FATHER_MIDDLE      = "F97_WIFE_FATHER_MIDDLE"
F97_WIFE_FATHER_LAST        = "F97_WIFE_FATHER_LAST"
F97_WIFE_FATHER_CITIZENSHIP = "F97_WIFE_FATHER_CITIZENSHIP"  # → wife.nationality_of_father

# — Wife's mother  (assembled → wife.name_of_mother) —————————
F97_WIFE_MOTHER_FIRST       = "F97_WIFE_MOTHER_FIRST"
F97_WIFE_MOTHER_MIDDLE      = "F97_WIFE_MOTHER_MIDDLE"
F97_WIFE_MOTHER_LAST        = "F97_WIFE_MOTHER_LAST"
F97_WIFE_MOTHER_CITIZENSHIP = "F97_WIFE_MOTHER_CITIZENSHIP"  # → wife.nationality_of_mother

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

# NER label → SpouseOutput field name
OUTPUT_MAP_3A_HUSBAND = {
    # name               ← assembled
    F97_HUSBAND_AGE:                 "age",
    F97_HUSBAND_CITIZENSHIP:         "nationality",
    # name_of_father     ← assembled
    F97_HUSBAND_FATHER_CITIZENSHIP:  "nationality_of_father",
    # name_of_mother     ← assembled
    F97_HUSBAND_MOTHER_CITIZENSHIP:  "nationality_of_mother",
}
OUTPUT_MAP_3A_WIFE = {
    # name               ← assembled
    F97_WIFE_AGE:                    "age",
    F97_WIFE_CITIZENSHIP:            "nationality",
    # name_of_father     ← assembled
    F97_WIFE_FATHER_CITIZENSHIP:     "nationality_of_father",
    # name_of_mother     ← assembled
    F97_WIFE_MOTHER_CITIZENSHIP:     "nationality_of_mother",
}
OUTPUT_MAP_3A_EVENT = {
    F97_REGISTRY_NO:          "registry_number",
    F97_DATE_OF_REGISTRATION: "date_of_registration",
    F97_DATE_OF_MARRIAGE:     "date_of_marriage",
    F97_PLACE_OF_MARRIAGE:    "place_of_marriage",
}

# Fields per spouse on Form 3A (in order)
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
# BIRTH CERTIFICATE  →  FORM 90   Marriage License
# ═════════════════════════════════════════════════════════════
# Source: individual birth certificates of groom and bride.
# NER extracts generic F90_APPLICANT_* labels for each.

# — Applicant name parts  (assembled → name_of_applicant) ————
F90_APPLICANT_FIRST  = "F90_APPLICANT_FIRST"
F90_APPLICANT_MIDDLE = "F90_APPLICANT_MIDDLE"
F90_APPLICANT_LAST   = "F90_APPLICANT_LAST"

# — Applicant details —————————————————————————————————————————
F90_DATE_OF_BIRTH  = "F90_DATE_OF_BIRTH"   # → date_of_birth
F90_AGE            = "F90_AGE"             # → age
F90_PLACE_OF_BIRTH = "F90_PLACE_OF_BIRTH"  # → place_of_birth
F90_SEX            = "F90_SEX"             # → sex
F90_CITIZENSHIP    = "F90_CITIZENSHIP"     # → citizenship
F90_RESIDENCE      = "F90_RESIDENCE"       # → residence
F90_RELIGION       = "F90_RELIGION"        # → religion

# — Father  (assembled → name_of_father) ——————————————————————
F90_FATHER_FIRST       = "F90_FATHER_FIRST"
F90_FATHER_LAST        = "F90_FATHER_LAST"
F90_FATHER_CITIZENSHIP = "F90_FATHER_CITIZENSHIP"   # → father_citizenship

# — Mother  (assembled → maiden_name_of_mother) ——————————————
F90_MOTHER_FIRST       = "F90_MOTHER_FIRST"
F90_MOTHER_LAST        = "F90_MOTHER_LAST"
F90_MOTHER_CITIZENSHIP = "F90_MOTHER_CITIZENSHIP"   # → mother_citizenship
F90_MOTHER_RESIDENCE   = "F90_MOTHER_RESIDENCE"     # → mother_residence

FORM_90_LABELS = [
    F90_APPLICANT_FIRST, F90_APPLICANT_MIDDLE, F90_APPLICANT_LAST,
    F90_DATE_OF_BIRTH, F90_AGE, F90_PLACE_OF_BIRTH,
    F90_SEX, F90_CITIZENSHIP, F90_RESIDENCE, F90_RELIGION,
    F90_FATHER_FIRST, F90_FATHER_LAST, F90_FATHER_CITIZENSHIP,
    F90_MOTHER_FIRST, F90_MOTHER_LAST, F90_MOTHER_CITIZENSHIP,
    F90_MOTHER_RESIDENCE,
]

# middle_label=None → join only first+last for father/mother on Form 90
NAME_GROUPS_90 = [
    (F90_APPLICANT_FIRST, F90_APPLICANT_MIDDLE, F90_APPLICANT_LAST, "name_of_applicant"),
    (F90_FATHER_FIRST,    None,                 F90_FATHER_LAST,    "name_of_father"),
    (F90_MOTHER_FIRST,    None,                 F90_MOTHER_LAST,    "maiden_name_of_mother"),
]

OUTPUT_MAP_90 = {
    # name_of_applicant      ← assembled
    F90_DATE_OF_BIRTH:       "date_of_birth",
    F90_AGE:                 "age",
    F90_PLACE_OF_BIRTH:      "place_of_birth",
    F90_SEX:                 "sex",
    F90_CITIZENSHIP:         "citizenship",
    F90_RESIDENCE:           "residence",
    F90_RELIGION:            "religion",
    # name_of_father         ← assembled
    F90_FATHER_CITIZENSHIP:  "father_citizenship",
    # maiden_name_of_mother  ← assembled
    F90_MOTHER_CITIZENSHIP:  "mother_citizenship",
    F90_MOTHER_RESIDENCE:    "mother_residence",
}

OUTPUT_FIELDS_90 = [
    "name_of_applicant", "date_of_birth", "age", "place_of_birth",
    "sex", "citizenship", "residence", "religion",
    "name_of_father", "father_citizenship",
    "maiden_name_of_mother", "mother_citizenship", "mother_residence",
]


# ═════════════════════════════════════════════════════════════
# ALL LABELS — registered with spaCy NER at model init
# ═════════════════════════════════════════════════════════════
ALL_LABELS = FORM_102_LABELS + FORM_103_LABELS + FORM_97_LABELS + FORM_90_LABELS
