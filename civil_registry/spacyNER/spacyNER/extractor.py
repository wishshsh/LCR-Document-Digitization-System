# ============================================================
# spacyNER/extractor.py
# ------------------------------------------------------------
# THE BRAIN — reads OCR text and extracts field values.
#
# HOW IT WORKS:
#   1. The OCR (CRNN+CTC) gives us raw text from a scanned form
#   2. This extractor scans the text line by line
#   3. When it sees a known field label (like "1. NAME"),
#      it grabs the value after the colon or on the next line
#   4. spaCy NER runs on top to catch anything keyword scan missed
#   5. Regex patterns catch dates, sex, citizenship words, etc.
#
# NAME FIELDS — IMPORTANT:
#   Forms have separate boxes for (First), (Middle), (Last).
#   OCR may output them as:
#     "1. NAME (First): Juan  (Middle): dela Cruz  (Last): Santos"
#   OR on separate lines:
#     "First: Juan"
#     "Middle: dela Cruz"
#     "Last: Santos"
#   We extract each part separately, then assemble in autofill.py.
#
# FORM 97 NAME ORDER NOTE:
#   Form 97 prints: (Last) (Middle) (First)
#   We detect this and store them correctly as First/Middle/Last.
# ============================================================

import re
import spacy
from typing import Optional

from spacyNER.labels import (
    # Form 102 labels
    F102_CHILD_FIRST, F102_CHILD_MIDDLE, F102_CHILD_LAST,
    F102_SEX, F102_DATE_OF_BIRTH, F102_PLACE_OF_BIRTH,
    F102_TYPE_OF_BIRTH, F102_BIRTH_ORDER,
    F102_MOTHER_FIRST, F102_MOTHER_MIDDLE, F102_MOTHER_LAST,
    F102_MOTHER_CITIZENSHIP, F102_MOTHER_RELIGION, F102_MOTHER_RESIDENCE,
    F102_FATHER_FIRST, F102_FATHER_MIDDLE, F102_FATHER_LAST,
    F102_FATHER_CITIZENSHIP, F102_FATHER_RELIGION, F102_FATHER_RESIDENCE,
    F102_MARRIAGE_DATE, F102_MARRIAGE_PLACE,
    F102_REGISTRY_NO, F102_DATE_OF_REGISTRATION,
    # Form 103 labels
    F103_DECEASED_FIRST, F103_DECEASED_MIDDLE, F103_DECEASED_LAST,
    F103_SEX, F103_RELIGION, F103_AGE,
    F103_PLACE_OF_DEATH, F103_DATE_OF_DEATH,
    F103_CITIZENSHIP, F103_RESIDENCE, F103_CIVIL_STATUS, F103_OCCUPATION,
    F103_CAUSE_IMMEDIATE, F103_CAUSE_ANTECEDENT, F103_CAUSE_UNDERLYING,
    F103_REGISTRY_NO, F103_DATE_OF_REGISTRATION,
    # Form 97 labels
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
)


# ──────────────────────────────────────────────────────────
# REGEX BACKUP PATTERNS
# ──────────────────────────────────────────────────────────

# Matches "March 15, 1990" or "15/03/1990" or "15-03-1990"
RE_DATE = re.compile(
    r'\b(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
    r'|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
    re.IGNORECASE
)

# Matches Male or Female
RE_SEX = re.compile(r'\b(Male|Female)\b', re.IGNORECASE)

# Matches civil status words
RE_CIVIL = re.compile(
    r'\b(Single|Married|Widowed|Divorced|Annulled|Separated)\b',
    re.IGNORECASE
)

# Matches citizenship words
RE_CITIZEN = re.compile(
    r'\b(Filipino|American|Chinese|Japanese|Korean|Spanish|British|'
    r'Australian|Canadian|Indian|Stateless)\b',
    re.IGNORECASE
)

# Matches religions
RE_RELIGION = re.compile(
    r'\b(Roman\s*Catholic|Catholic|Islam|Muslim|Protestant|'
    r'Iglesia\s*ni\s*Cristo|Baptist|Born\s*Again|Christian|'
    r'Seventh\s*Day\s*Adventist|Aglipayan)\b',
    re.IGNORECASE
)

# Matches registry numbers like "2024-001" or "NCR-2024-00123"
RE_REGISTRY = re.compile(
    r'\b(?:[A-Z]{0,5}[-]?)?\d{4}[-]\d{3,6}\b'
)

# Matches numbers used as age
RE_AGE = re.compile(r'\b(\d{1,3})\s*(?:years?\s*old)?\b')


# ──────────────────────────────────────────────────────────
# KEYWORD MAPS — maps form field labels to our NER labels
# ──────────────────────────────────────────────────────────
# Each entry: "text we expect to see in OCR" → "our label"
# Keys are lowercase for case-insensitive matching.

# ── Form 102 keyword map ───────────────────────────────────
FORM_102_MAP = {
    # Registry
    "registry no":              F102_REGISTRY_NO,
    "registry number":          F102_REGISTRY_NO,
    "date of registration":     F102_DATE_OF_REGISTRATION,

    # Child name — OCR may output as "1. name (first)"
    "1. name":                  F102_CHILD_FIRST,   # start of name field
    "name (first)":             F102_CHILD_FIRST,
    "name (middle)":            F102_CHILD_MIDDLE,
    "name (last)":              F102_CHILD_LAST,
    "child first":              F102_CHILD_FIRST,
    "child middle":             F102_CHILD_MIDDLE,
    "child last":               F102_CHILD_LAST,
    "(first)":                  F102_CHILD_FIRST,   # fallback
    "(middle)":                 F102_CHILD_MIDDLE,
    "(last)":                   F102_CHILD_LAST,

    # Child details
    "2. sex":                   F102_SEX,
    "sex":                      F102_SEX,
    "3. date of birth":         F102_DATE_OF_BIRTH,
    "date of birth":            F102_DATE_OF_BIRTH,
    "4. place of birth":        F102_PLACE_OF_BIRTH,
    "place of birth":           F102_PLACE_OF_BIRTH,
    "5a. type of birth":        F102_TYPE_OF_BIRTH,
    "type of birth":            F102_TYPE_OF_BIRTH,
    "5c. birth order":          F102_BIRTH_ORDER,
    "birth order":              F102_BIRTH_ORDER,

    # Mother — "7. maiden name"
    "7. maiden name":           F102_MOTHER_FIRST,
    "maiden name (first)":      F102_MOTHER_FIRST,
    "maiden name (middle)":     F102_MOTHER_MIDDLE,
    "maiden name (last)":       F102_MOTHER_LAST,
    "mother first":             F102_MOTHER_FIRST,
    "mother middle":            F102_MOTHER_MIDDLE,
    "mother last":              F102_MOTHER_LAST,
    "8. citizenship":           F102_MOTHER_CITIZENSHIP,
    "9. religion":              F102_MOTHER_RELIGION,
    "13. residence":            F102_MOTHER_RESIDENCE,

    # Father — "14. name"
    "14. name":                 F102_FATHER_FIRST,
    "father name (first)":      F102_FATHER_FIRST,
    "father name (middle)":     F102_FATHER_MIDDLE,
    "father name (last)":       F102_FATHER_LAST,
    "father first":             F102_FATHER_FIRST,
    "father middle":            F102_FATHER_MIDDLE,
    "father last":              F102_FATHER_LAST,
    "15. citizenship":          F102_FATHER_CITIZENSHIP,
    "16. religion":             F102_FATHER_RELIGION,
    "19. residence":            F102_FATHER_RESIDENCE,

    # Marriage of parents
    "20a. date":                F102_MARRIAGE_DATE,
    "date of marriage of parents": F102_MARRIAGE_DATE,
    "20b. place":               F102_MARRIAGE_PLACE,
    "place of marriage of parents": F102_MARRIAGE_PLACE,
}

# ── Form 103 keyword map ───────────────────────────────────
FORM_103_MAP = {
    "registry no":              F103_REGISTRY_NO,
    "registry number":          F103_REGISTRY_NO,
    "date of registration":     F103_DATE_OF_REGISTRATION,

    # Deceased name — Field 1
    "1. name":                  F103_DECEASED_FIRST,
    "name (first)":             F103_DECEASED_FIRST,
    "name (middle)":            F103_DECEASED_MIDDLE,
    "name (last)":              F103_DECEASED_LAST,
    "deceased first":           F103_DECEASED_FIRST,
    "deceased middle":          F103_DECEASED_MIDDLE,
    "deceased last":            F103_DECEASED_LAST,

    # Details
    "2. sex":                   F103_SEX,
    "sex":                      F103_SEX,
    "3. religion":              F103_RELIGION,
    "religion":                 F103_RELIGION,
    "4. age":                   F103_AGE,
    "age":                      F103_AGE,
    "5. place of death":        F103_PLACE_OF_DEATH,
    "place of death":           F103_PLACE_OF_DEATH,
    "6. date of death":         F103_DATE_OF_DEATH,
    "date of death":            F103_DATE_OF_DEATH,
    "7. citizenship":           F103_CITIZENSHIP,
    "citizenship":              F103_CITIZENSHIP,
    "8. residence":             F103_RESIDENCE,
    "residence":                F103_RESIDENCE,
    "9. civil status":          F103_CIVIL_STATUS,
    "civil status":             F103_CIVIL_STATUS,
    "10. occupation":           F103_OCCUPATION,
    "occupation":               F103_OCCUPATION,

    # Causes of death — Field 17
    "immediate cause":          F103_CAUSE_IMMEDIATE,
    "17a":                      F103_CAUSE_IMMEDIATE,
    "antecedent cause":         F103_CAUSE_ANTECEDENT,
    "17b":                      F103_CAUSE_ANTECEDENT,
    "underlying cause":         F103_CAUSE_UNDERLYING,
    "17c":                      F103_CAUSE_UNDERLYING,
}

# ── Form 97 keyword map ────────────────────────────────────
# NOTE: Form 97 has HUSBAND and WIFE columns side by side.
# OCR may output them as "Husband:" / "Wife:" sections.
FORM_97_HUSBAND_MAP = {
    "husband name (first)":         F97_HUSBAND_FIRST,
    "husband (first)":              F97_HUSBAND_FIRST,
    "husband first":                F97_HUSBAND_FIRST,
    "husband name (middle)":        F97_HUSBAND_MIDDLE,
    "husband middle":               F97_HUSBAND_MIDDLE,
    "husband name (last)":          F97_HUSBAND_LAST,
    "husband last":                 F97_HUSBAND_LAST,
    "husband date of birth":        F97_HUSBAND_DOB,
    "husband age":                  F97_HUSBAND_AGE,
    "husband place of birth":       F97_HUSBAND_PLACE_BIRTH,
    "husband sex":                  F97_HUSBAND_SEX,
    "husband citizenship":          F97_HUSBAND_CITIZENSHIP,
    "husband residence":            F97_HUSBAND_RESIDENCE,
    "husband religion":             F97_HUSBAND_RELIGION,
    "husband civil status":         F97_HUSBAND_CIVIL_STATUS,
    "husband father (first)":       F97_HUSBAND_FATHER_FIRST,
    "husband father (middle)":      F97_HUSBAND_FATHER_MIDDLE,
    "husband father (last)":        F97_HUSBAND_FATHER_LAST,
    "husband father citizenship":   F97_HUSBAND_FATHER_CITIZENSHIP,
    "husband mother (first)":       F97_HUSBAND_MOTHER_FIRST,
    "husband mother (middle)":      F97_HUSBAND_MOTHER_MIDDLE,
    "husband mother (last)":        F97_HUSBAND_MOTHER_LAST,
    "husband mother citizenship":   F97_HUSBAND_MOTHER_CITIZENSHIP,
}

FORM_97_WIFE_MAP = {
    "wife name (first)":            F97_WIFE_FIRST,
    "wife (first)":                 F97_WIFE_FIRST,
    "wife first":                   F97_WIFE_FIRST,
    "wife name (middle)":           F97_WIFE_MIDDLE,
    "wife middle":                  F97_WIFE_MIDDLE,
    "wife name (last)":             F97_WIFE_LAST,
    "wife last":                    F97_WIFE_LAST,
    "wife date of birth":           F97_WIFE_DOB,
    "wife age":                     F97_WIFE_AGE,
    "wife place of birth":          F97_WIFE_PLACE_BIRTH,
    "wife sex":                     F97_WIFE_SEX,
    "wife citizenship":             F97_WIFE_CITIZENSHIP,
    "wife residence":               F97_WIFE_RESIDENCE,
    "wife religion":                F97_WIFE_RELIGION,
    "wife civil status":            F97_WIFE_CIVIL_STATUS,
    "wife father (first)":          F97_WIFE_FATHER_FIRST,
    "wife father (middle)":         F97_WIFE_FATHER_MIDDLE,
    "wife father (last)":           F97_WIFE_FATHER_LAST,
    "wife father citizenship":      F97_WIFE_FATHER_CITIZENSHIP,
    "wife mother (first)":          F97_WIFE_MOTHER_FIRST,
    "wife mother (middle)":         F97_WIFE_MOTHER_MIDDLE,
    "wife mother (last)":           F97_WIFE_MOTHER_LAST,
    "wife mother citizenship":      F97_WIFE_MOTHER_CITIZENSHIP,
}

FORM_97_SHARED_MAP = {
    "registry no":                  F97_REGISTRY_NO,
    "registry number":              F97_REGISTRY_NO,
    "date of registration":         F97_DATE_OF_REGISTRATION,
    "15. place of marriage":        F97_PLACE_OF_MARRIAGE,
    "place of marriage":            F97_PLACE_OF_MARRIAGE,
    "16. date of marriage":         F97_DATE_OF_MARRIAGE,
    "date of marriage":             F97_DATE_OF_MARRIAGE,
}


# ──────────────────────────────────────────────────────────
# MAIN EXTRACTOR CLASS
# ──────────────────────────────────────────────────────────

class CivilRegistryNER:
    """
    Extracts civil registry field values from OCR text.

    Usage:
        extractor = CivilRegistryNER()

        # From Form 102 OCR text → Form 1A fields
        data_1a = extractor.extract_form_102(text)

        # From Form 103 OCR text → Form 2A fields
        data_2a = extractor.extract_form_103(text)

        # From Form 97 OCR text → Form 3A fields
        data_3a = extractor.extract_form_97(text)
    """

    def __init__(self, model_path: str = "en_core_web_sm"):
        """
        Load the spaCy model.

        Parameters:
            model_path:
                "en_core_web_sm"  → default (use before fine-tuning)
                "./models/civil_registry_model/model-best"  → after training
        """
        print(f"\n  Loading spaCy model: '{model_path}' ...")
        try:
            self.nlp = spacy.load(model_path)
            print(f"  ✅ Model loaded.\n")
        except OSError:
            print(f"  ⚠️  '{model_path}' not found. Using blank model.")
            print(f"      Run: python -m spacy download en_core_web_sm\n")
            self.nlp = spacy.blank("en")


    # ── PRIVATE: Keyword scan ──────────────────────────────

    def _scan_by_keywords(self, text: str, keyword_map: dict) -> dict:
        """
        Scan OCR text line by line for known field labels.

        When a line contains a keyword like "place of birth:",
        we grab everything after the colon as the field value.

        Parameters:
            text:        raw OCR output from a scanned form
            keyword_map: { "keyword": "LABEL_CONSTANT" }

        Returns:
            { "LABEL_CONSTANT": "extracted value", ... }
        """
        results = {}

        # Clean and split into individual lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            line_lower = line.lower()

            # Check each keyword against this line
            for keyword, label in keyword_map.items():
                if keyword in line_lower:
                    # Try to get value after the colon
                    if ":" in line:
                        value = line.split(":", 1)[1].strip()
                        if value and label not in results:
                            results[label] = value
                    break   # matched — move to next line

        return results


    # ── PRIVATE: spaCy NER pass ────────────────────────────

    def _run_spacy(self, text: str) -> dict:
        """Run spaCy NER and return { label: [values] }."""
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            val = ent.text.strip()
            if val not in entities[ent.label_]:
                entities[ent.label_].append(val)
        return entities


    # ── PRIVATE: Regex fallback ────────────────────────────

    def _regex_fallback(self, text: str, results: dict,
                         date_label: str = None,
                         sex_label: str = None,
                         age_label: str = None,
                         citizen_label: str = None,
                         civil_label: str = None,
                         religion_label: str = None) -> dict:
        """
        Fill in any fields still empty using regex patterns.
        Only fills if the field hasn't already been found.
        """
        if date_label and date_label not in results:
            m = RE_DATE.search(text)
            if m:
                results[date_label] = m.group(0)

        if sex_label and sex_label not in results:
            m = RE_SEX.search(text)
            if m:
                results[sex_label] = m.group(0).capitalize()

        if age_label and age_label not in results:
            m = RE_AGE.search(text)
            if m:
                results[age_label] = m.group(1)

        if citizen_label and citizen_label not in results:
            m = RE_CITIZEN.search(text)
            if m:
                results[citizen_label] = m.group(0).capitalize()

        if civil_label and civil_label not in results:
            m = RE_CIVIL.search(text)
            if m:
                results[civil_label] = m.group(0).capitalize()

        if religion_label and religion_label not in results:
            m = RE_RELIGION.search(text)
            if m:
                results[religion_label] = m.group(0)

        return results


    # ── PUBLIC: Form 102 → Form 1A extraction ─────────────

    def extract_form_102(self, text: str) -> dict:
        """
        Extract all Form 1A fields from Form 102 OCR text.
        (Certificate of Live Birth)

        NAME PARTS EXTRACTED SEPARATELY:
          F102_CHILD_FIRST, F102_CHILD_MIDDLE, F102_CHILD_LAST
          F102_MOTHER_FIRST, F102_MOTHER_MIDDLE, F102_MOTHER_LAST
          F102_FATHER_FIRST, F102_FATHER_MIDDLE, F102_FATHER_LAST

        These are assembled into full names in autofill.py.

        Parameters:
            text: OCR text from scanned Form 102

        Returns:
            Dictionary { F102_LABEL: value, ... }
        """
        # Step 1: Keyword scan
        results = self._scan_by_keywords(text, FORM_102_MAP)

        # Step 2: spaCy NER — supplement with standard entity types
        spacy_ents = self._run_spacy(text)

        # Use spaCy's PERSON entities as fallback for name parts
        persons = spacy_ents.get("PERSON", [])
        if persons and F102_CHILD_FIRST not in results:
            # Try to split first spaCy person into name parts
            from spacyNER.name_assembler import split_full_name
            first, middle, last = split_full_name(persons[0])
            if first:  results.setdefault(F102_CHILD_FIRST, first)
            if middle: results.setdefault(F102_CHILD_MIDDLE, middle)
            if last:   results.setdefault(F102_CHILD_LAST, last)

        # Use spaCy's GPE/LOC for place of birth fallback
        places = spacy_ents.get("GPE", spacy_ents.get("LOC", []))
        if places and F102_PLACE_OF_BIRTH not in results:
            results.setdefault(F102_PLACE_OF_BIRTH, places[0])

        # Use spaCy's DATE for date of birth fallback
        dates = spacy_ents.get("DATE", [])
        if dates and F102_DATE_OF_BIRTH not in results:
            results.setdefault(F102_DATE_OF_BIRTH, dates[0])

        # Step 3: Regex fallback for any remaining empty fields
        results = self._regex_fallback(
            text, results,
            date_label    = F102_DATE_OF_BIRTH,
            sex_label     = F102_SEX,
            citizen_label = F102_MOTHER_CITIZENSHIP,
        )

        return results


    # ── PUBLIC: Form 103 → Form 2A extraction ─────────────

    def extract_form_103(self, text: str) -> dict:
        """
        Extract all Form 2A fields from Form 103 OCR text.
        (Certificate of Death)

        NAME PARTS EXTRACTED SEPARATELY:
          F103_DECEASED_FIRST, F103_DECEASED_MIDDLE, F103_DECEASED_LAST

        Assembled into full name in autofill.py.

        Parameters:
            text: OCR text from scanned Form 103

        Returns:
            Dictionary { F103_LABEL: value, ... }
        """
        results = self._scan_by_keywords(text, FORM_103_MAP)

        # spaCy fallbacks
        spacy_ents = self._run_spacy(text)

        persons = spacy_ents.get("PERSON", [])
        if persons and F103_DECEASED_FIRST not in results:
            from spacyNER.name_assembler import split_full_name
            first, middle, last = split_full_name(persons[0])
            if first:  results.setdefault(F103_DECEASED_FIRST, first)
            if middle: results.setdefault(F103_DECEASED_MIDDLE, middle)
            if last:   results.setdefault(F103_DECEASED_LAST, last)

        places = spacy_ents.get("GPE", spacy_ents.get("LOC", []))
        if places and F103_PLACE_OF_DEATH not in results:
            results.setdefault(F103_PLACE_OF_DEATH, places[0])

        dates = spacy_ents.get("DATE", [])
        if dates and F103_DATE_OF_DEATH not in results:
            results.setdefault(F103_DATE_OF_DEATH, dates[0])

        # Regex fallbacks
        results = self._regex_fallback(
            text, results,
            date_label     = F103_DATE_OF_DEATH,
            sex_label      = F103_SEX,
            age_label      = F103_AGE,
            citizen_label  = F103_CITIZENSHIP,
            civil_label    = F103_CIVIL_STATUS,
            religion_label = F103_RELIGION,
        )

        return results


    # ── PUBLIC: Form 97 → Form 3A extraction ──────────────

    def extract_form_97(self, text: str) -> dict:
        """
        Extract all Form 3A fields from Form 97 OCR text.
        (Certificate of Marriage)

        NAME PARTS EXTRACTED SEPARATELY for husband and wife:
          F97_HUSBAND_FIRST, F97_HUSBAND_MIDDLE, F97_HUSBAND_LAST
          F97_WIFE_FIRST, F97_WIFE_MIDDLE, F97_WIFE_LAST
          (and for their parents too)

        NOTE: Form 97 shows names as (Last)(Middle)(First).
              We detect this from the keyword context and
              store them correctly as First/Middle/Last.

        Assembled into full names in autofill.py.

        Parameters:
            text: OCR text from scanned Form 97

        Returns:
            Dictionary { F97_LABEL: value, ... }
        """
        # Combine all three maps
        combined_map = {
            **FORM_97_HUSBAND_MAP,
            **FORM_97_WIFE_MAP,
            **FORM_97_SHARED_MAP,
        }

        results = self._scan_by_keywords(text, combined_map)

        # spaCy fallbacks
        spacy_ents = self._run_spacy(text)

        places = spacy_ents.get("GPE", spacy_ents.get("LOC", []))
        if places and F97_PLACE_OF_MARRIAGE not in results:
            results.setdefault(F97_PLACE_OF_MARRIAGE, places[0])

        dates = spacy_ents.get("DATE", [])
        if dates and F97_DATE_OF_MARRIAGE not in results:
            results.setdefault(F97_DATE_OF_MARRIAGE, dates[0])

        # Regex fallbacks
        results = self._regex_fallback(
            text, results,
            date_label     = F97_DATE_OF_MARRIAGE,
            citizen_label  = F97_HUSBAND_CITIZENSHIP,
            civil_label    = F97_HUSBAND_CIVIL_STATUS,
        )

        return results


    # ── HELPER: get first non-empty value ──────────────────

    def get(self, data: dict, *labels) -> Optional[str]:
        """
        Return the first non-empty value found for any of the labels.
        Returns None if nothing is found.
        """
        for label in labels:
            val = data.get(label)
            if val:
                return val.strip()
        return None
