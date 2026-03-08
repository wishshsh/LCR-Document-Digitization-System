# mnb/classifier.py
# ============================================================
# MNB CLASSIFIER — wraps the trained DocumentClassifier
#
# Their trained model (form_classifier.py + pkl files)
# classifies ALL FOUR form types:
#   form1a  → Form 1A  (Birth Certificate)     ← from Form 102
#   form2a  → Form 2A  (Death Certificate)      ← from Form 103
#   form3a  → Form 3A  (Marriage Certificate)   ← from Form 97
#   form90  → Form 90  (Marriage License app)   ← birth cert source
#
# IMPORTANT: form90 IS the birth cert used as source for Form 90.
# The MNB_SEX classifier (GROOM/BRIDE) is a SEPARATE concern —
# it reads the SEX field of the birth cert text itself.
# It is NOT what this MNB does; see classify_sex() below.
#
# Files needed in mnb/ (or models/):
#   form_classifier.py     ← their training + DocumentClassifier
#   models/mnb_classifier.pkl
#   models/tfidf_vectorizer.pkl
#   models/mnb_metadata.json
# ============================================================

import sys
import os

# Allow importing form_classifier from the mnb/ folder
_mnb_dir = os.path.dirname(os.path.abspath(__file__))
if _mnb_dir not in sys.path:
    sys.path.insert(0, _mnb_dir)

# Also allow importing from project root (where models/ lives)
_root_dir = os.path.dirname(_mnb_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from form_classifier import DocumentClassifier
    _HAVE_DOC_CLASSIFIER = True
except ImportError:
    _HAVE_DOC_CLASSIFIER = False


# ── Keyword fallback (used if pkl files not found) ─────────
_FORM_KEYWORDS = {
    "form1a": ["child", "date of birth", "place of birth", "birth certificate",
               "mother", "father", "infant", "newborn", "bc registry"],
    "form2a": ["deceased", "date of death", "place of death", "cause of death",
               "death certificate", "burial", "died"],
    "form3a": ["husband", "wife", "date of marriage", "place of marriage",
               "marriage certificate", "solemnizing officer", "witnesses"],
    "form90": ["marriage license application", "applicant", "parental consent",
               "Form 90", "application for marriage license"],
}

_SEX_KEYWORDS = {
    "GROOM": ["sex: male", "sex male", "2. sex: male", " male"],
    "BRIDE": ["sex: female", "sex female", "2. sex: female", " female"],
}

def _keyword_classify_form(text: str) -> str:
    t = text.lower()
    scores = {k: sum(1 for kw in v if kw.lower() in t) for k, v in _FORM_KEYWORDS.items()}
    return max(scores, key=scores.get)

def _keyword_classify_sex(text: str) -> str:
    t = text.lower()
    scores = {k: sum(1 for kw in v if kw.lower() in t) for k, v in _SEX_KEYWORDS.items()}
    return max(scores, key=scores.get)


# ── Form code → NER hint map ──────────────────────────────
_FORM_CODE_TO_HINT = {
    "form1a": "birth",
    "form2a": "death",
    "form3a": "marriage",
    "form90": "marriage_license",
}


class MNBClassifier:
    """
    Wraps DocumentClassifier from form_classifier.py.

    Usage:
        mnb = MNBClassifier()

        # Classify a certification form (Path A)
        form_code = mnb.classify_form_type(ocr_text)
        # → 'form1a' | 'form2a' | 'form3a' | 'form90'

        # Get bridge-compatible hint string
        hint = mnb.get_ner_hint(ocr_text)
        # → 'birth' | 'death' | 'marriage' | 'marriage_license'

        # Full result with confidence
        result = mnb.classify_full(ocr_text)
        # → {'label': 'Form 1A - Birth Certificate',
        #    'form_code': 'form1a', 'confidence': 0.97, 'probabilities': {...}}

        # Path B — birth cert for Form 90 (separate sex classifier)
        sex_role = mnb.classify_sex(ocr_text)
        # → 'GROOM' | 'BRIDE'
    """

    def __init__(self, model_dir: str = "models"):
        self._doc_clf = None
        if _HAVE_DOC_CLASSIFIER:
            try:
                self._doc_clf = DocumentClassifier(model_dir=model_dir)
                print(f"  [MNB] Loaded DocumentClassifier from {model_dir}/")
            except FileNotFoundError as e:
                print(f"  [MNB] {e}")
                print(f"  [MNB] Using keyword fallback — run: python mnb/form_classifier.py")
        else:
            print("  [MNB] form_classifier.py not found — using keyword fallback")

    def classify_form_type(self, ocr_text: str) -> str:
        """
        Returns form code: 'form1a' | 'form2a' | 'form3a' | 'form90'
        """
        if self._doc_clf is not None:
            return self._doc_clf.predict(ocr_text)["form_code"]
        return _keyword_classify_form(ocr_text)

    def classify_full(self, ocr_text: str) -> dict:
        """
        Returns full result dict:
        {
            'label':        'Form 1A - Birth Certificate',
            'form_code':    'form1a',
            'confidence':   0.97,
            'probabilities': { ... }
        }
        """
        if self._doc_clf is not None:
            return self._doc_clf.predict(ocr_text)
        winner = _keyword_classify_form(ocr_text)
        return {
            "label":      winner,
            "form_code":  winner,
            "confidence": 1.0,
            "probabilities": {k: (1.0 if k == winner else 0.0) for k in _FORM_KEYWORDS},
        }

    def get_ner_hint(self, ocr_text: str) -> str:
        """
        Returns NER hint string used by bridge.py:
        'birth' | 'death' | 'marriage' | 'marriage_license'
        """
        code = self.classify_form_type(ocr_text)
        return _FORM_CODE_TO_HINT.get(code, "birth")

    def classify_sex(self, ocr_text: str) -> str:
        """
        Separate classifier for Form 90 routing.
        Reads the SEX field of a birth certificate.
        Returns 'GROOM' (Male) or 'BRIDE' (Female).
        """
        return _keyword_classify_sex(ocr_text)

    def classify_sex_proba(self, ocr_text: str) -> dict:
        """Returns {'GROOM': 0.9, 'BRIDE': 0.1}"""
        winner = _keyword_classify_sex(ocr_text)
        return {k: (1.0 if k == winner else 0.0) for k in _SEX_KEYWORDS}


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    mnb = MNBClassifier()

    tests = [
        ("Name of child Maria Santos Date of birth 01/15/1990 "
         "Place of birth Tarlac City Name of mother Lani Santos "
         "Sex Female birth certificate infant",
         "form1a"),
        ("Name of deceased Pedro Reyes Date of death 03/22/2020 "
         "Cause of death Cardiac Arrest death certificate burial",
         "form2a"),
        ("Name of husband Carlos Bautista Name of wife Ana Torres "
         "Date of marriage 07/04/2005 marriage certificate solemnizing officer",
         "form3a"),
        ("Name of applicant Roberto Lim Date of application 11/30/2023 "
         "Civil status Single parental consent marriage license application Form 90",
         "form90"),
    ]

    print("\n  Form type classification test:")
    for text, expected in tests:
        result = mnb.classify_full(text)
        mark = "✅" if result["form_code"] == expected else "❌"
        print(f"  {mark}  Expected={expected:<8}  Got={result['form_code']:<8}  "
              f"Confidence={result['confidence']:.1%}  ({result['label']})")

    print("\n  Sex role classification test (Form 90 routing):")
    sex_tests = [
        ("CHILD (First): Juan SEX: Male Date of Birth March 15 1990 Mother Maria", "GROOM"),
        ("CHILD (First): Ana  SEX: Female Date of Birth August 21 1995 Mother Gloria", "BRIDE"),
    ]
    for text, expected in sex_tests:
        pred = mnb.classify_sex(text)
        mark = "✅" if pred == expected else "❌"
        print(f"  {mark}  Expected={expected}  Got={pred}")
