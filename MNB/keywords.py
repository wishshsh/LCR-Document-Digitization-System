# mnb/keywords.py
# ============================================================
# Keyword fallback lists used by classifier.py when the
# trained .pkl models are not available.
#
# Uses EXACT Philippine civil registry form headers:
#   Form 102 → "Municipal Form No. 102 / Certificate of Live Birth"
#   Form 103 → "Municipal Form No. 103 / Certificate of Death"
#   Form 97  → "Municipal Form No. 97  / Certificate of Marriage"
#
# NOTE: Form 90 is NOT classified here.
#   Form 90 has its own upload page (Application for Marriage License).
#   The SEX field on the uploaded birth cert determines routing:
#     Male   → GROOM slot in Form 90
#     Female → BRIDE slot in Form 90
# ============================================================

# ── PATH A: Certifications Page ──────────────────────────────
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
}

# ── PATH B: Form 90 Marriage License Page ────────────────────
# Used ONLY on the Marriage License upload page.
# Reads the SEX field from the uploaded PSA/NSO birth certificate.
#   Male   → GROOM (routed to Groom slot in Form 90)
#   Female → BRIDE (routed to Bride slot in Form 90)
SEX_KEYWORDS = {
    "GROOM": [
        "sex: male",
        "sex male",
        "2. sex: male",
        " male",
        "sex m",
    ],
    "BRIDE": [
        "sex: female",
        "sex female",
        "2. sex: female",
        " female",
        "sex f",
    ],
}
