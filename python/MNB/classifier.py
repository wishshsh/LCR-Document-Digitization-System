# mnb/classifier.py
# ============================================================
# MNB CLASSIFIER — wraps the trained DocumentClassifier
#
# Identifies which form was uploaded:
#   form102  → Form 102 (Certificate of Live Birth)
#   form103  → Form 103 (Certificate of Death)
#   form97   → Form 97  (Certificate of Marriage)
#   form90   → Form 90 / Accountable Form No. 54 / Form No. 10
#              (Marriage License and Fee Receipt of Two Pesos)
#
# Files needed:
#   form_classifier.py     ← training + DocumentClassifier
#   models/mnb_classifier.pkl
#   models/tfidf_vectorizer.pkl
#   models/mnb_metadata.json
# ============================================================

import sys
import os

_mnb_dir = os.path.dirname(os.path.abspath(__file__))
if _mnb_dir not in sys.path:
    sys.path.insert(0, _mnb_dir)

_root_dir = os.path.dirname(_mnb_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from form_classifier import DocumentClassifier
    _HAVE_DOC_CLASSIFIER = True
except ImportError:
    _HAVE_DOC_CLASSIFIER = False


# ── Keyword fallback (used if .pkl files not found) ────────
# Uses exact Philippine civil registry form headers
_FORM_KEYWORDS = {
    "form102": [
        "Municipal Form No. 102",
        "Municipal Form No.102",
        "Certificate of Live Birth",
        "live birth",
        "name of child",
        "date of birth",
        "place of birth",
        "birth certificate",
        "mother", "father",
        "infant", "newborn",
        "attendant at birth",
    ],
    "form103": [
        "Municipal Form No. 103",
        "Municipal Form No.103",
        "Certificate of Death",
        "death certificate",
        "name of deceased",
        "date of death",
        "place of death",
        "cause of death",
        "burial", "deceased",
        "immediate cause",
    ],
    "form97": [
        "Municipal Form No. 97",
        "Municipal Form No.97",
        "Certificate of Marriage",
        "marriage certificate",
        "name of husband",
        "name of wife",
        "date of marriage",
        "place of marriage",
        "solemnizing officer",
        "contracting parties",
        "witnesses",
    ],
    "form90": [
        "Accountable Form No. 54",
        "Accountable Form No.54",
        "Form No. 10",
        "Form No.10",
        "Marriage License and Fee Receipt",
        "Marriage License and Fee Receipt of Two Pesos",
        "fee receipt of two pesos",
        "marriage license",
        "may legally contract marriage",
        "license fee",
        "republic act no. 386",
        "articles 65",
        "registration officer",
        "marriage license valid until",
    ],
}

def _keyword_classify_form(text: str) -> str:
    """Keyword fallback for form classification."""
    t = text.lower()
    scores = {k: sum(1 for kw in v if kw.lower() in t) for k, v in _FORM_KEYWORDS.items()}
    return max(scores, key=scores.get)


# ── Form code → NER hint map ──────────────────────────────
_FORM_CODE_TO_HINT = {
    "form102": "birth",
    "form103": "death",
    "form97":  "marriage",
    "form90":  "marriage_license",
}


class MNBClassifier:
    """
    MNB Classifier for the Civil Registry Digitization System.

    Classifies any uploaded civil registry document:
        mnb = MNBClassifier()
        form_code = mnb.classify_form_type(ocr_text)
        # → 'form102' | 'form103' | 'form97' | 'form90'

        hint = mnb.get_ner_hint(ocr_text)
        # → 'birth' | 'death' | 'marriage' | 'marriage_license'

        result = mnb.classify_full(ocr_text)
        # → {'label': 'Form 90 - Marriage License and Fee Receipt',
        #    'form_code': 'form90', 'confidence': 0.97, 'probabilities': {...}}
    """

    def __init__(self, model_dir: str = "models"):
        self._doc_clf = None
        if _HAVE_DOC_CLASSIFIER:
            try:
                self._doc_clf = DocumentClassifier(model_dir=model_dir)
                print(f"  [MNB] Loaded DocumentClassifier from {model_dir}/")
            except FileNotFoundError as e:
                print(f"  [MNB] {e}")
                print("  [MNB] Using keyword fallback — run: python mnb/form_classifier.py")
        else:
            print("  [MNB] form_classifier.py not found — using keyword fallback")

    def classify_form_type(self, ocr_text: str) -> str:
        """
        Identify which form was uploaded.
        Returns: 'form102' | 'form103' | 'form97' | 'form90'
        """
        if self._doc_clf is not None:
            return self._doc_clf.predict(ocr_text)["form_code"]
        return _keyword_classify_form(ocr_text)

    def classify_full(self, ocr_text: str) -> dict:
        """
        Full result with label and confidence scores.
        Returns:
            {
                'label':         'Form 90 - Marriage License and Fee Receipt',
                'form_code':     'form90',
                'confidence':    0.97,
                'probabilities': { ... }
            }
        """
        if self._doc_clf is not None:
            return self._doc_clf.predict(ocr_text)
        winner = _keyword_classify_form(ocr_text)
        return {
            "label":         winner,
            "form_code":     winner,
            "confidence":    1.0,
            "probabilities": {k: (1.0 if k == winner else 0.0) for k in _FORM_KEYWORDS},
        }

    def get_ner_hint(self, ocr_text: str) -> str:
        """
        Returns NER hint string for bridge.py:
        'birth' | 'death' | 'marriage' | 'marriage_license'
        """
        code = self.classify_form_type(ocr_text)
        return _FORM_CODE_TO_HINT.get(code, "birth")


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    mnb = MNBClassifier()

    print("\n  ── Form Classification Tests ──")
    cert_tests = [
        (
            "Municipal Form No. 102 Certificate of Live Birth "
            "Name of child Maria Santos Date of birth 01/15/1990 "
            "Place of birth Brgy. San Jose Tarlac City "
            "Name of mother Lani Santos Name of father Jose Santos "
            "Sex Female birth certificate infant",
            "form102"
        ),
        (
            "Municipal Form No.102 Certificate of Live Birth "
            "PSA Child Juan Dela Cruz born 03/22/1985 Capas Tarlac "
            "mother Rosa father Pedro Sex Male",
            "form102"
        ),
        (
            "Municipal Form No. 103 Certificate of Death "
            "Name of deceased Pedro Reyes Date of death 03/22/2020 "
            "Cause of death Cardiac Arrest death certificate burial",
            "form103"
        ),
        (
            "Municipal Form No.103 Certificate of Death "
            "Deceased Ana Torres died 07/04/2000 Pneumonia burial permit",
            "form103"
        ),
        (
            "Municipal Form No. 97 Certificate of Marriage "
            "Name of husband Carlos Bautista Name of wife Ana Torres "
            "Date of marriage 07/04/2005 solemnizing officer witnesses",
            "form97"
        ),
        (
            "Municipal Form No.97 Certificate of Marriage "
            "Husband Jose Santos wife Maria Reyes married 11/30/1995 "
            "contracting parties",
            "form97"
        ),
        (
            "Accountable Form No. 54 Form No. 10 "
            "Marriage License and Fee Receipt of Two Pesos "
            "Erastus Noel T. Delizo aged 42 years may legally contract marriage "
            "with Maria Fatima A. Villena aged 30 years license fee "
            "Republic Act No. 386 Registration Officer",
            "form90"
        ),
        (
            "Form No. 10 Marriage License and Fee Receipt "
            "may legally contract marriage license fee Articles 65 "
            "marriage license valid until local civil registrar",
            "form90"
        ),
    ]

    for text, expected in cert_tests:
        result = mnb.classify_full(text)
        mark = "✅" if result["form_code"] == expected else "❌"
        print(f"  {mark}  Expected={expected:<8}  Got={result['form_code']:<8}  "
              f"Confidence={result['confidence']:.1%}  ({result['label']})")
