# mnb/keywords.py
# ============================================================
# Keyword fallback lists used by classifier.py when the
# trained .pkl models are not available.
# ============================================================

FORM_KEYWORDS = {
    "form1a": [
        "child", "date of birth", "place of birth",
        "birth certificate", "mother", "father",
        "infant", "newborn", "bc registry",
        "type of birth", "birth order",
    ],
    "form2a": [
        "deceased", "date of death", "place of death",
        "cause of death", "death certificate",
        "burial", "died", "immediate cause",
        "antecedent cause", "underlying cause",
    ],
    "form3a": [
        "husband", "wife", "date of marriage",
        "place of marriage", "marriage certificate",
        "solemnizing officer", "witnesses",
        "contracting parties", "mc registry",
    ],
    "form90": [
        "marriage license application", "applicant",
        "parental consent", "Form 90",
        "application for marriage license",
        "co-applicant", "civil status",
    ],
}

SEX_KEYWORDS = {
    "GROOM": ["sex: male", "sex male", "2. sex: male", " male"],
    "BRIDE": ["sex: female", "sex female", "2. sex: female", " female"],
}
