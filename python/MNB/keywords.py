# mnb/keywords.py
# ============================================================
# Keyword fallback lists used by classifier.py when the
# trained .pkl models are not available.
#
# Uses EXACT Philippine civil registry form headers:
#   Form 102 → "Municipal Form No. 102 / Certificate of Live Birth"
#   Form 103 → "Municipal Form No. 103 / Certificate of Death"
#   Form 97  → "Municipal Form No. 97  / Certificate of Marriage"
#   Form 90  → "Application for Marriage License"
#   Form 54  → "Accountable Form No. 54 / Form No. 10
#               Marriage License and Fee Receipt of Two Pesos"
#
# Form 54 NER entities extracted after classification:
#   NAME_OF_GROOM      → name of groom (contracting party, male)
#   AGE_OF_GROOM       → age of groom in years (and months)
#   RESIDENCE_OF_GROOM → full address / residence of groom
#   NAME_OF_BRIDE      → name of bride (contracting party, female)
#   AGE_OF_BRIDE       → age of bride in years (and months)
#   RESIDENCE_OF_BRIDE → full address / residence of bride
#   DATE_OF_ISSUANCE   → date the marriage license was issued
# ============================================================

# ── PATH A: Certifications / Marriage License Page ───────────
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
        # Exact header variants
        "Application for Marriage License",
        "application for marriage license",
        # Field-level keywords
        "name of applicant",
        "date of birth of applicant",
        "place of birth of applicant",
        "citizenship",
        "residence of applicant",
        "citizenship of father",
        "citizenship of mother",
        "no. of previous marriages",
        "parental consent",
        "parental advice",
        "affidavit",
        "applicant",
        "marriage license application",
    ],

    "form54": [
        # Exact printed headers
        "Accountable Form No. 54",
        "Accountable Form No.54",
        "Form No. 10",
        "Form No.10",
        "Marriage License and Fee Receipt of Two Pesos",
        "Marriage License and Fee Receipt",
        "marriage license fee receipt",
        # Body text cues
        "may legally contract marriage",
        "having paid the license fee",
        "license fee of",
        "Articles 65 of Republic Act No. 386",
        "Republic Act No. 386",
        "one hundred and twenty days",
        "marriage license valid until",
        "marriage license valid",
        "notice & application",
        "notice and application",
        "Registration Officer",
        "Local Civil Registrar of",
        # Structural cues
        "this is to certify that",
        "aged",
        "years and",
    ],
}

# ── Form 54 NER entity slot names (used by bridge.py) ────────
# Extracted from Form 54 (Marriage License and Fee Receipt)
# after classification via classify_form_type() → 'form54'
FORM54_NER_ENTITIES = [
    "NAME_OF_GROOM",       # name of groom (contracting party, male)
    "AGE_OF_GROOM",        # age of groom in years (and months)
    "RESIDENCE_OF_GROOM",  # full address / residence of groom
    "NAME_OF_BRIDE",       # name of bride (contracting party, female)
    "AGE_OF_BRIDE",        # age of bride in years (and months)
    "RESIDENCE_OF_BRIDE",  # full address / residence of bride
    "DATE_OF_ISSUANCE",    # date the marriage license was issued
]
