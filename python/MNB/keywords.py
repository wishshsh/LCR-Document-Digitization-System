# mnb/keywords.py
# ============================================================
# Keyword fallback lists used by classifier.py when the
# trained .pkl models are not available.
#
# Uses EXACT Philippine civil registry form headers:
#   Form 102 → "Municipal Form No. 102 / Certificate of Live Birth"
#   Form 103 → "Municipal Form No. 103 / Certificate of Death"
#   Form 97  → "Municipal Form No. 97  / Certificate of Marriage"
#   Form 90  → "Accountable Form No. 54 / Form No. 10 /
#               Marriage License and Fee Receipt of Two Pesos"
# ============================================================

# ── Certifications Page + Marriage License Page ───────────────
FORM_KEYWORDS = {

    "form102": [
        # Exact header variants
        "Municipal Form No. 102",
        "Municipal Form No.102",
        "Certificate of Live Birth",
        # Field-level keywords
        "name of child",
        "date of birth",
        "place of birth",
        "birth certificate",
        "name of mother",
        "name of father",
        "attendant at birth",
        "type of birth",
        "birth order",
        "legitimacy",
        "infant",
        "newborn",
        # PSA/NSO sealed copy keywords
        "PSA",
        "NSO",
        "bc registry",
    ],

    "form103": [
        # Exact header variants
        "Municipal Form No. 103",
        "Municipal Form No.103",
        "Certificate of Death",
        # Field-level keywords
        "name of deceased",
        "date of death",
        "place of death",
        "cause of death",
        "death certificate",
        "immediate cause",
        "antecedent cause",
        "underlying cause",
        "burial",
        "deceased",
        "died",
        "burial permit",
        "interment",
    ],

    "form97": [
        # Exact header variants
        "Municipal Form No. 97",
        "Municipal Form No.97",
        "Certificate of Marriage",
        # Field-level keywords
        "name of husband",
        "name of wife",
        "date of marriage",
        "place of marriage",
        "marriage certificate",
        "solemnizing officer",
        "contracting parties",
        "witnesses",
        "marriage license number",
        "mc registry",
        "nuptial",
        "wed",
    ],

    "form90": [
        # Exact header variants (Accountable Form No. 54 / Form No. 10)
        "Accountable Form No. 54",
        "Accountable Form No.54",
        "Form No. 10",
        "Form No.10",
        "Marriage License and Fee Receipt",
        "Marriage License and Fee Receipt of Two Pesos",
        "fee receipt of two pesos",
        # Field-level keywords
        "marriage license",
        "may legally contract marriage",
        "license fee",
        "republic act no. 386",
        "articles 65",
        "valid for no more than one hundred and twenty days",
        "contracting parties",
        "notice & application",
        "local civil registrar",
        "registration officer",
        "marriage license valid until",
    ],
}
