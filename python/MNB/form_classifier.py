"""
form_classifier.py
=======================
Multinomial Naive Bayes (MNB) Document Classifier
for Local Civil Registry Document Digitization System

Classifies extracted OCR text into:
  - Form 102  (Certificate of Live Birth)                     ← Certifications page
  - Form 103  (Certificate of Death)                          ← Certifications page
  - Form 97   (Certificate of Marriage)                       ← Certifications page
  - Form 90   (Application for Marriage License)              ← Marriage License page
  - Form 54   (Marriage License and Fee Receipt of Two Pesos) ← Marriage License Receipt page
                Accountable Form No. 54 / Form No. 10

Form 54 NER entities (extracted after classification):
  NAME_OF_GROOM, AGE_OF_GROOM, RESIDENCE_OF_GROOM
  NAME_OF_BRIDE, AGE_OF_BRIDE, RESIDENCE_OF_BRIDE
  DATE_OF_ISSUANCE

Usage:
    python form_classifier.py            # trains and saves model
    python form_classifier.py --test     # runs test predictions
"""

import os
import json
import random
import argparse
import pickle
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)

# ─────────────────────────────────────────────────────────────
# 1.  LABEL MAP
# ─────────────────────────────────────────────────────────────
LABEL_MAP = {
    0: 'Form 102 - Certificate of Live Birth',
    1: 'Form 103 - Certificate of Death',
    2: 'Form 97 - Certificate of Marriage',
    3: 'Form 90 - Application for Marriage License',
    4: 'Form 54 - Marriage License and Fee Receipt',
}
LABEL_NAMES = list(LABEL_MAP.values())

# ─────────────────────────────────────────────────────────────
# 2.  VOCABULARY POOLS  (Filipino civil registry)
# ─────────────────────────────────────────────────────────────
FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Carlos', 'Lani',
    'Roberto', 'Nena', 'Ramon', 'Cynthia', 'Eduardo', 'Marites', 'Danilo',
    'Rowena', 'Renato', 'Melinda', 'Ernesto', 'Josephine', 'Michael',
    'Jennifer', 'Angelo', 'Christine', 'Mark', 'Patricia', 'John', 'Mary',
    'Erastus', 'Fatima', 'Noel', 'Gloria', 'Ricardo', 'Lourdes',
]
LAST_NAMES = [
    'Dela Cruz', 'Santos', 'Reyes', 'Garcia', 'Torres', 'Flores',
    'Bautista', 'Villanueva', 'Mendoza', 'Castro', 'Ramos', 'Lim',
    'Aquino', 'Diaz', 'Fernandez', 'Lopez', 'Gonzales', 'Ramirez',
    'Abad', 'Aguilar', 'Manalo', 'Navarro', 'Ocampo', 'Pascual',
    'Delizo', 'Villena', 'Buenaventura', 'Salazar',
]
MUNICIPALITIES = [
    'Tarlac City', 'Capas', 'Paniqui', 'Gerona', 'Camiling',
    'Victoria', 'San Manuel', 'Concepcion', 'La Paz', 'Sta. Ignacia',
    'Bamban', 'Moncada', 'Pura', 'Ramos', 'Anao',
    'Mandaluyong City', 'Las Pinas City', 'Quezon City', 'Pasig City',
]
PROVINCES = ['Tarlac', 'Pampanga', 'Nueva Ecija', 'Bulacan', 'Zambales', 'Metro Manila']
BARANGAYS = [
    'Brgy. San Jose', 'Brgy. Poblacion', 'Brgy. Sto. Cristo',
    'Brgy. Tibag', 'Brgy. Maliwalo', 'Brgy. San Nicolas',
    'Brgy. San Roque', 'Brgy. San Vicente', 'Brgy. Salapungan',
    'Brgy. Hulo', 'Brgy. BF Homes', 'Brgy. Coronado',
]
DATES = [
    '01/15/1990', '03/22/1985', '07/04/2000', '11/30/1995',
    '05/18/1988', '09/12/1975', '02/28/1993', '06/06/1980',
    '12/25/1998', '04/17/2001', '08/08/1965', '10/31/1970',
]
MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]
YEARS = ['2005', '2006', '2007', '2008', '2009', '2010',
         '2011', '2012', '2015', '2018', '2020', '2022']
CITIZENSHIPS = ['Filipino', 'Chinese', 'American', 'Japanese']
REG_OFFICERS = [
    'Registration Officer I', 'Registration Officer II',
    'Registration Officer III', 'Local Civil Registrar',
]


def _name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def _date():
    return random.choice(DATES)

def _place():
    return f"{random.choice(BARANGAYS)}, {random.choice(MUNICIPALITIES)}, {random.choice(PROVINCES)}"

def _address():
    return (f"No. {random.randint(1, 999)} {random.choice(['Rizal St.', 'Mabini Ave.', 'Tehran St.', 'Coronado St.', 'Quezon Blvd.'])} "
            f"{random.choice(BARANGAYS)} {random.choice(MUNICIPALITIES)}")


# ─────────────────────────────────────────────────────────────
# 3.  SAMPLE GENERATORS
#     Each generator uses the EXACT Philippine form header
#     so MNB learns the real keywords from actual documents.
# ─────────────────────────────────────────────────────────────

def generate_form102():
    """
    Form 102 — Certificate of Live Birth
    Header keywords: 'Municipal Form No. 102', 'Certificate of Live Birth'
    """
    templates = [
        # Template A: Exact header present
        f"Municipal Form No. 102 Certificate of Live Birth "
        f"Name of child {_name()} Date of birth {_date()} Place of birth {_place()} "
        f"Name of mother {_name()} Name of father {_name()} "
        f"Sex {random.choice(['Male', 'Female'])} "
        f"Legitimacy {random.choice(['Legitimate', 'Illegitimate'])} "
        f"Attendant {random.choice(['Physician', 'Midwife', 'Nurse'])} "
        f"birth certificate registry birth registration infant newborn child",

        # Template B: No. without space
        f"Municipal Form No.102 Certificate of Live Birth "
        f"Child {_name()} born {_date()} at {_place()} "
        f"mother {_name()} father {_name()} "
        f"birth weight {random.randint(2, 4)}.{random.randint(1, 9)} kg "
        f"birth order {random.choice(['First', 'Second', 'Third'])} "
        f"birth certificate Form 102",

        # Template C: Registry number format
        f"Municipal Form No. 102 Certificate of Live Birth "
        f"Registry number {random.randint(100, 999)}-{random.randint(1, 99):02d} "
        f"name of child {_name()} date of birth {_date()} "
        f"place of birth {_place()} birth certificate municipal civil registrar",

        # Template D: PSA/NSO sealed copy
        f"Municipal Form No. 102 Certificate of Live Birth "
        f"PSA {_name()} born on {_date()} "
        f"place of birth {_place()} "
        f"mother maiden name {_name()} father {_name()} "
        f"type of birth {random.choice(['Single', 'Twin'])} infant newborn",

        # Template E: NSO variation
        f"Municipal Form No.102 Certificate of Live Birth "
        f"NSO birth registration {_name()} "
        f"birth date {_date()} birthplace {_place()} "
        f"parents mother {_name()} father {_name()} "
        f"attendant at birth {random.choice(['hospital', 'midwife', 'physician'])} "
        f"sex {random.choice(['male', 'female'])}",
    ]
    return random.choice(templates)


def generate_form103():
    """
    Form 103 — Certificate of Death
    Header keywords: 'Municipal Form No. 103', 'Certificate of Death'
    """
    causes = [
        'Cardiac Arrest', 'Pneumonia', 'Hypertension', 'Diabetes Mellitus',
        'Stroke', 'Respiratory Failure', 'Natural Causes', 'Cancer',
        'Septicemia', 'Renal Failure'
    ]
    templates = [
        # Template A: Exact header
        f"Municipal Form No. 103 Certificate of Death "
        f"Name of deceased {_name()} Date of death {_date()} Place of death {_place()} "
        f"Cause of death {random.choice(causes)} Age at death {random.randint(1, 95)} "
        f"Sex {random.choice(['Male', 'Female'])} "
        f"Civil status {random.choice(['Single', 'Married', 'Widowed'])} "
        f"death certificate deceased burial interment",

        # Template B: No space
        f"Municipal Form No.103 Certificate of Death "
        f"Deceased {_name()} died on {_date()} at {_place()} "
        f"cause {random.choice(causes)} corpse informant {_name()} "
        f"death certificate Form 103 municipal civil registrar",

        # Template C: Registry format
        f"Municipal Form No. 103 Certificate of Death "
        f"Registry number death {random.randint(100, 999)}-{random.randint(1, 99):02d} "
        f"name of deceased {_name()} date of death {_date()} "
        f"place of death {_place()} cause of death {random.choice(causes)} "
        f"death certificate burial permit",

        # Template D: Clinical format
        f"Municipal Form No.103 Certificate of Death "
        f"{_name()} died {_date()} "
        f"place {_place()} cause of death {random.choice(causes)} "
        f"informant {_name()} relationship {random.choice(['spouse', 'child', 'sibling', 'parent'])} "
        f"death deceased cadaver",

        # Template E: Full form
        f"Municipal Form No. 103 Certificate of Death "
        f"Form 103 death registration {_name()} "
        f"date of death {_date()} place of death {_place()} "
        f"immediate cause {random.choice(causes)} "
        f"attending physician {_name()} certificate of death",
    ]
    return random.choice(templates)


def generate_form97():
    """
    Form 97 — Certificate of Marriage
    Header keywords: 'Municipal Form No. 97', 'Certificate of Marriage'
    """
    officers = ['Rev.', 'Judge', 'Mayor', 'Pastor', 'Fr.']
    licenses = [f"{random.randint(10000, 99999)}", f"ML-{random.randint(1000, 9999)}"]
    templates = [
        # Template A: Exact header
        f"Municipal Form No. 97 Certificate of Marriage "
        f"Name of husband {_name()} Name of wife {_name()} "
        f"Date of marriage {_date()} Place of marriage {_place()} "
        f"Solemnizing officer {random.choice(officers)} {_name()} "
        f"Marriage license number {random.choice(licenses)} witnesses {_name()} {_name()} "
        f"marriage certificate contracting parties wedding",

        # Template B: No space
        f"Municipal Form No.97 Certificate of Marriage "
        f"Husband {_name()} wife {_name()} "
        f"married on {_date()} at {_place()} "
        f"officiated by {random.choice(officers)} {_name()} "
        f"marriage certificate Form 97 solemnizing officer",

        # Template C: Registry format
        f"Municipal Form No. 97 Certificate of Marriage "
        f"Registry number marriage {random.randint(100, 999)}-{random.randint(1, 99):02d} "
        f"husband {_name()} wife {_name()} "
        f"date of marriage {_date()} place {_place()} "
        f"marriage license {random.choice(licenses)} issued at {_place()} "
        f"marriage certificate civil registrar",

        # Template D: Ceremony format
        f"Municipal Form No.97 Certificate of Marriage "
        f"{_name()} and {_name()} "
        f"solemnized {_date()} at {_place()} "
        f"solemnizing officer {random.choice(officers)} {_name()} "
        f"witnesses {_name()} {_name()} "
        f"marriage contracting parties husband wife ceremony",

        # Template E: Full form
        f"Municipal Form No. 97 Certificate of Marriage "
        f"Form 97 marriage registration husband {_name()} "
        f"wife {_name()} date of marriage {_date()} "
        f"place of marriage {_place()} "
        f"license number {random.choice(licenses)} marriage nuptial wed",
    ]
    return random.choice(templates)


def generate_form90():
    """
    Form 90 — Application for Marriage License
    Header keyword: 'Application for Marriage License'
    """
    prev_marriages = ['0', '1', 'none', 'one']
    templates = [
        # Template A: Full form — first applicant (groom)
        f"Application for Marriage License "
        f"Name of applicant {_name()} "
        f"Date of birth of applicant {_date()} "
        f"Place of birth of applicant {_place()} "
        f"Citizenship {random.choice(CITIZENSHIPS)} "
        f"Residence of applicant {_address()} "
        f"Name of father {_name()} citizenship of father {random.choice(CITIZENSHIPS)} "
        f"Name of mother {_name()} citizenship of mother {random.choice(CITIZENSHIPS)} "
        f"No. of previous marriages {random.choice(prev_marriages)} "
        f"Parental consent {random.choice(['given', 'waived', 'not required'])} "
        f"affidavit marriage license application",

        # Template B: Full form — second applicant (bride)
        f"Application for Marriage License "
        f"Applicant {_name()} "
        f"Date of birth of applicant {_date()} "
        f"Place of birth of applicant {_place()} "
        f"Citizenship Filipino "
        f"Residence of applicant {_address()} "
        f"Father {_name()} citizenship of father {random.choice(CITIZENSHIPS)} "
        f"Mother {_name()} citizenship of mother {random.choice(CITIZENSHIPS)} "
        f"No. of previous marriages {random.choice(prev_marriages)} "
        f"parental advice affidavit marriage license application Form 90",

        # Template C: Abbreviated / OCR-heavy
        f"Application for Marriage License "
        f"Name {_name()} birthdate {_date()} birthplace {_place()} "
        f"citizenship {random.choice(CITIZENSHIPS)} "
        f"residence {_address()} "
        f"father {_name()} mother {_name()} "
        f"previous marriages {random.choice(prev_marriages)} "
        f"applicant parental consent marriage license application",

        # Template D: Registry copy format
        f"Application for Marriage License "
        f"Registry No. {random.randint(100, 999)}-{random.randint(1, 99):02d} "
        f"name of applicant {_name()} "
        f"date of birth of applicant {_date()} "
        f"citizenship of applicant {random.choice(CITIZENSHIPS)} "
        f"residence of applicant {_address()} "
        f"citizenship of father {random.choice(CITIZENSHIPS)} "
        f"citizenship of mother {random.choice(CITIZENSHIPS)} "
        f"parental advice no. of previous marriages {random.choice(prev_marriages)} "
        f"affidavit applicant",

        # Template E: Minimal scan
        f"Application for Marriage License "
        f"{_name()} born {_date()} {_place()} "
        f"citizenship Filipino residence {_address()} "
        f"father {_name()} mother {_name()} "
        f"marriage license application no. of previous marriages 0 "
        f"parental consent affidavit applicant",
    ]
    return random.choice(templates)


def generate_form54():
    """
    Form 54 — Accountable Form No. 54 / Form No. 10
    Marriage License and Fee Receipt of Two Pesos
    Header keywords: 'Accountable Form No. 54', 'Form No. 10',
                     'Marriage License and Fee Receipt of Two Pesos'
    NER entities: NAME_OF_GROOM, AGE_OF_GROOM, RESIDENCE_OF_GROOM,
                  NAME_OF_BRIDE,  AGE_OF_BRIDE,  RESIDENCE_OF_BRIDE,
                  DATE_OF_ISSUANCE
    """
    groom_name = _name()
    bride_name = _name()
    groom_age  = random.randint(18, 55)
    groom_mos  = random.randint(0, 11)
    bride_age  = random.randint(18, 50)
    bride_mos  = random.randint(0, 11)
    groom_res  = _address()
    bride_res  = _address()
    issue_day  = random.randint(1, 28)
    issue_mon  = random.choice(MONTHS)
    issue_yr   = random.choice(YEARS)
    lic_no     = random.randint(1000000, 9999999)
    muni       = random.choice(MUNICIPALITIES)

    templates = [
        # Template A: Full printed layout (closest to actual document)
        f"Accountable Form No. 54 Form No. 10 "
        f"Republic of the Philippines City or Municipality of {muni} "
        f"No. {lic_no} "
        f"Marriage License and Fee Receipt of Two Pesos "
        f"This is to certify that {groom_name} aged {groom_age} years and {groom_mos} months "
        f"and resident of {groom_res} may legally contract marriage "
        f"with {bride_name} aged {bride_age} years and {bride_mos} months "
        f"and resident of {bride_res} "
        f"he having paid the license fee of P2.00 prescribed under "
        f"Articles 65 of Republic Act No. 386 "
        f"This license shall be valid in any part of the Philippines "
        f"but it shall be good for no more than one hundred and twenty days "
        f"In witness whereof I have signed and issued this license this {issue_day}th "
        f"day of {issue_mon} {issue_yr} "
        f"{random.choice(REG_OFFICERS)} Local Civil Registrar of {muni}",

        # Template B: Abbreviated scan
        f"Accountable Form No.54 Form No.10 "
        f"Marriage License and Fee Receipt "
        f"No. {lic_no} {muni} "
        f"This is to certify that {groom_name} aged {groom_age} years "
        f"resident of {groom_res} may legally contract marriage with "
        f"{bride_name} aged {bride_age} years resident of {bride_res} "
        f"license fee paid Articles 65 Republic Act No. 386 "
        f"issued this {issue_day} {issue_mon} {issue_yr} "
        f"marriage license valid until {muni}",

        # Template C: OCR-heavy (partial recognition)
        f"Form No. 10 Accountable Form No. 54 "
        f"Marriage License and Fee Receipt of Two Pesos "
        f"certify that {groom_name} {groom_age} years and {groom_mos} months "
        f"resident {groom_res} contract marriage "
        f"{bride_name} {bride_age} years {bride_mos} months "
        f"resident {bride_res} "
        f"license fee P2.00 Republic Act No. 386 "
        f"one hundred twenty days notice and application "
        f"{issue_day}th {issue_mon} {issue_yr} "
        f"{random.choice(REG_OFFICERS)}",

        # Template D: Bottom-stamp variant
        f"Accountable Form No. 54 Form No. 10 "
        f"Marriage License and Fee Receipt of Two Pesos "
        f"{muni} No. {lic_no} "
        f"groom {groom_name} age {groom_age} residence {groom_res} "
        f"bride {bride_name} age {bride_age} residence {bride_res} "
        f"date of issuance {issue_day} {issue_mon} {issue_yr} "
        f"marriage license valid until contracting parties "
        f"having paid the license fee registration officer",

        # Template E: Minimal / torn document
        f"Accountable Form No. 54 Form No. 10 "
        f"Marriage License and Fee Receipt "
        f"No. {lic_no} "
        f"This is to certify that {groom_name} aged {groom_age} "
        f"may legally contract marriage with {bride_name} aged {bride_age} "
        f"resident of {bride_res} "
        f"issued {issue_day} {issue_mon} {issue_yr} "
        f"Local Civil Registrar of {muni} "
        f"notice & application contracting parties",
    ]
    return random.choice(templates)


# ─────────────────────────────────────────────────────────────
# 4.  DATASET GENERATOR  (5 classes: 102 / 103 / 97 / 90 / 54)
# ─────────────────────────────────────────────────────────────
def generate_dataset(samples_per_class=150):
    generators = [
        generate_form102,
        generate_form103,
        generate_form97,
        generate_form90,
        generate_form54,
    ]
    labels_map = [0, 1, 2, 3, 4]  # 0=Form102, 1=Form103, 2=Form97, 3=Form90, 4=Form54

    texts, labels = [], []
    for gen, label in zip(generators, labels_map):
        for _ in range(samples_per_class):
            texts.append(gen())
            labels.append(label)

    combined = list(zip(texts, labels))
    random.shuffle(combined)
    texts, labels = zip(*combined)
    return list(texts), list(labels)


# ─────────────────────────────────────────────────────────────
# 5.  TRAIN & SAVE
# ─────────────────────────────────────────────────────────────
def train(samples_per_class=150, save_dir='models'):
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 60)
    print("  MNB Document Classifier  |  Filipino Civil Registry")
    print("  Forms: 102 / 103 / 97 / 90 / 54")
    print("=" * 60)

    print(f"\n  Generating dataset ({samples_per_class} samples × 5 forms = {samples_per_class * 5} total)...")
    texts, labels = generate_dataset(samples_per_class)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

    # TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
        min_df=1,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec  = vectorizer.transform(X_test)

    # Train MNB
    clf = MultinomialNB(alpha=0.1)
    clf.fit(X_train_vec, y_train)

    # Evaluate
    y_pred = clf.predict(X_test_vec)
    acc    = accuracy_score(y_test, y_pred)

    print(f"\n  Accuracy : {acc * 100:.2f}%")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=LABEL_NAMES))

    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    headers = ['Form102', 'Form103', 'Form97', 'Form90', 'Form54']
    print(f"  {'':30s} " + "  ".join(headers))
    for i, row in enumerate(cm):
        print(f"  Actual {headers[i]}: {str(row)}")

    # Save
    model_path = os.path.join(save_dir, 'mnb_classifier.pkl')
    vec_path   = os.path.join(save_dir, 'tfidf_vectorizer.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
    with open(vec_path, 'wb') as f:
        pickle.dump(vectorizer, f)

    meta = {
        'accuracy': round(acc * 100, 2),
        'samples_per_class': samples_per_class,
        'total_samples': samples_per_class * 5,
        'labels': {str(k): v for k, v in LABEL_MAP.items()},
        'note': (
            'Form 54 NER entities: NAME_OF_GROOM, AGE_OF_GROOM, RESIDENCE_OF_GROOM, '
            'NAME_OF_BRIDE, AGE_OF_BRIDE, RESIDENCE_OF_BRIDE, DATE_OF_ISSUANCE'
        ),
        'pages': {
            'certifications':    'Classifies Form 102 / 103 / 97 from uploaded certification scan',
            'marriage_license':  'Classifies Form 90 (Application for Marriage License)',
            'license_receipt':   'Classifies Form 54 (Accountable Form No. 54 / Form No. 10)',
        },
        'form54_ner_entities': [
            'NAME_OF_GROOM', 'AGE_OF_GROOM', 'RESIDENCE_OF_GROOM',
            'NAME_OF_BRIDE', 'AGE_OF_BRIDE', 'RESIDENCE_OF_BRIDE',
            'DATE_OF_ISSUANCE',
        ],
        'model_path': model_path,
        'vectorizer_path': vec_path,
    }
    with open(os.path.join(save_dir, 'mnb_metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"\n  Model saved     : {model_path}")
    print(f"  Vectorizer saved: {vec_path}")
    print(f"\n  Target accuracy : >90%")
    print(f"  Achieved        : {acc * 100:.2f}% {'✓' if acc >= 0.90 else '✗ (try increasing samples_per_class)'}")
    print("=" * 60)

    return clf, vectorizer, acc


# ─────────────────────────────────────────────────────────────
# 6.  DOCUMENT CLASSIFIER CLASS
# ─────────────────────────────────────────────────────────────
class DocumentClassifier:
    """Load trained MNB model and classify OCR text."""

    def __init__(self, model_dir='models'):
        model_path = os.path.join(model_dir, 'mnb_classifier.pkl')
        vec_path   = os.path.join(model_dir, 'tfidf_vectorizer.pkl')

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run: python form_classifier.py"
            )

        with open(model_path, 'rb') as f:
            self.clf = pickle.load(f)
        with open(vec_path, 'rb') as f:
            self.vectorizer = pickle.load(f)

    def predict(self, text: str) -> dict:
        """
        Classify OCR text.

        Returns:
            {
                'label':        'Form 54 - Marriage License and Fee Receipt',
                'form_code':    'form54',
                'confidence':   0.97,
                'probabilities': { ... }
            }
        """
        vec   = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(vec)[0]
        idx   = int(np.argmax(probs))

        form_codes = ['form102', 'form103', 'form97', 'form90', 'form54']
        return {
            'label':      LABEL_MAP[idx],
            'form_code':  form_codes[idx],
            'confidence': round(float(probs[idx]), 4),
            'probabilities': {
                LABEL_MAP[i]: round(float(p), 4)
                for i, p in enumerate(probs)
            }
        }


# ─────────────────────────────────────────────────────────────
# 7.  TEST DEMO
# ─────────────────────────────────────────────────────────────
def run_test():
    print("\n" + "=" * 60)
    print("  Testing DocumentClassifier — All Forms")
    print("=" * 60)

    classifier = DocumentClassifier()

    test_cases = [
        # ── Form 102 ──
        (
            "Municipal Form No. 102 Certificate of Live Birth "
            "Name of child Maria Santos Date of birth 01/15/1990 "
            "Place of birth Brgy. San Jose, Tarlac City, Tarlac "
            "Name of mother Lani Santos Name of father Jose Santos "
            "Sex Female birth certificate infant",
            "Form 102 - Certificate of Live Birth"
        ),
        (
            "Municipal Form No.102 Certificate of Live Birth "
            "PSA Child Juan Dela Cruz born 03/22/1985 "
            "Place of birth Capas Tarlac mother Rosa Dela Cruz "
            "father Pedro Dela Cruz Sex Male",
            "Form 102 - Certificate of Live Birth"
        ),
        # ── Form 103 ──
        (
            "Municipal Form No. 103 Certificate of Death "
            "Name of deceased Pedro Reyes Date of death 03/22/2020 "
            "Place of death Capas, Tarlac Cause of death Cardiac Arrest "
            "Age at death 75 death certificate deceased burial",
            "Form 103 - Certificate of Death"
        ),
        (
            "Municipal Form No.103 Certificate of Death "
            "Deceased Ana Torres died 07/04/2000 "
            "cause Pneumonia burial permit interment",
            "Form 103 - Certificate of Death"
        ),
        # ── Form 97 ──
        (
            "Municipal Form No. 97 Certificate of Marriage "
            "Name of husband Carlos Bautista Name of wife Ana Torres "
            "Date of marriage 07/04/2005 Place of marriage Paniqui, Tarlac "
            "Solemnizing officer Rev. Santos witnesses marriage certificate",
            "Form 97 - Certificate of Marriage"
        ),
        (
            "Municipal Form No.97 Certificate of Marriage "
            "Husband Jose Santos wife Maria Reyes "
            "married 11/30/1995 contracting parties solemnizing officer",
            "Form 97 - Certificate of Marriage"
        ),
        # ── Form 90 ──
        (
            "Application for Marriage License "
            "Name of applicant Juan Dela Cruz "
            "Date of birth of applicant 03/22/1990 "
            "Place of birth of applicant Tarlac City Tarlac "
            "Citizenship Filipino residence of applicant Brgy. Poblacion Tarlac City "
            "Name of father Pedro Dela Cruz citizenship of father Filipino "
            "Name of mother Rosa Santos citizenship of mother Filipino "
            "No. of previous marriages 0 parental consent affidavit",
            "Form 90 - Application for Marriage License"
        ),
        (
            "Application for Marriage License "
            "Applicant Maria Santos date of birth 07/15/1995 "
            "place of birth Capas Tarlac residence Brgy. San Jose "
            "citizenship Filipino parental advice "
            "marriage license application",
            "Form 90 - Application for Marriage License"
        ),
        # ── Form 54 ──
        (
            "Accountable Form No. 54 Form No. 10 "
            "Republic of the Philippines City or Municipality of Mandaluyong City "
            "No. 5975035 "
            "Marriage License and Fee Receipt of Two Pesos "
            "This is to certify that Erastus Noel T. Delizo aged 42 years and 10 months "
            "and resident of No. 17 Tehran St. BF Homes International Las Pinas City "
            "may legally contract marriage with Maria Fatima A. Villena aged 30 years "
            "and resident of 709-A Coronado St. Brgy. Hulo Mandaluyong City "
            "he having paid the license fee of P2.00 Articles 65 Republic Act No. 386 "
            "issued this 17th day of October 2008 "
            "Registration Officer III Local Civil Registrar of Mandaluyong City",
            "Form 54 - Marriage License and Fee Receipt"
        ),
        (
            "Accountable Form No.54 Form No.10 "
            "Marriage License and Fee Receipt "
            "No. 1234567 Tarlac City "
            "This is to certify that Carlos Bautista aged 35 years and 2 months "
            "resident of Brgy. Poblacion Tarlac City may legally contract marriage with "
            "Ana Reyes aged 28 years resident of Brgy. San Jose Capas Tarlac "
            "having paid the license fee Republic Act No. 386 "
            "issued 15 March 2015 notice and application "
            "Local Civil Registrar of Tarlac City",
            "Form 54 - Marriage License and Fee Receipt"
        ),
    ]

    correct = 0
    for text, expected in test_cases:
        result = classifier.predict(text)
        status = '✓' if expected in result['label'] else '✗'
        if expected in result['label']:
            correct += 1
        print(f"\n  {status} Expected : {expected}")
        print(f"    Predicted: {result['label']} ({result['confidence'] * 100:.1f}% confidence)")

    print(f"\n  Test Accuracy: {correct}/{len(test_cases)} ({correct / len(test_cases) * 100:.0f}%)")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────
# 8.  MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run test predictions only')
    parser.add_argument('--samples', type=int, default=150, help='Samples per class (default: 150)')
    args = parser.parse_args()

    if args.test:
        run_test()
    else:
        train(samples_per_class=args.samples)
        print("\nTo test predictions, run:")
        print("  python form_classifier.py --test")
