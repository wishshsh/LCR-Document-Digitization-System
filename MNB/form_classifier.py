"""
form_classifier.py
=======================
Multinomial Naive Bayes (MNB) Document Classifier
for Local Civil Registry Document Digitization System

Classifies extracted OCR text into:
  - Form 102  (Certificate of Live Birth)       ← Certifications page
  - Form 103  (Certificate of Death)             ← Certifications page
  - Form 97   (Certificate of Marriage)          ← Certifications page

NOTE: Form 90 (Application for Marriage License) is NOT classified here.
      Form 90 has its OWN upload page where the user uploads:
        - Groom's Birth Certificate (PSA/NSO sealed)
        - Bride's Birth Certificate (PSA/NSO sealed)
      The SEX field on each birth cert determines GROOM (Male) or BRIDE (Female).
      See classify_sex() in classifier.py for that routing.

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
# 1.  LABEL MAP  (Certifications page only — NO Form 90 here)
# ─────────────────────────────────────────────────────────────
LABEL_MAP = {
    0: 'Form 102 - Certificate of Live Birth',
    1: 'Form 103 - Certificate of Death',
    2: 'Form 97 - Certificate of Marriage',
}
LABEL_NAMES = list(LABEL_MAP.values())

# ─────────────────────────────────────────────────────────────
# 2.  VOCABULARY POOLS  (Filipino civil registry)
# ─────────────────────────────────────────────────────────────
FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Carlos', 'Lani',
    'Roberto', 'Nena', 'Ramon', 'Cynthia', 'Eduardo', 'Marites', 'Danilo',
    'Rowena', 'Renato', 'Melinda', 'Ernesto', 'Josephine', 'Michael',
    'Jennifer', 'Angelo', 'Christine', 'Mark', 'Patricia', 'John', 'Mary'
]
LAST_NAMES = [
    'Dela Cruz', 'Santos', 'Reyes', 'Garcia', 'Torres', 'Flores',
    'Bautista', 'Villanueva', 'Mendoza', 'Castro', 'Ramos', 'Lim',
    'Aquino', 'Diaz', 'Fernandez', 'Lopez', 'Gonzales', 'Ramirez',
    'Abad', 'Aguilar', 'Manalo', 'Navarro', 'Ocampo', 'Pascual'
]
MUNICIPALITIES = [
    'Tarlac City', 'Capas', 'Paniqui', 'Gerona', 'Camiling',
    'Victoria', 'San Manuel', 'Concepcion', 'La Paz', 'Sta. Ignacia',
    'Bamban', 'Moncada', 'Pura', 'Ramos', 'Anao'
]
PROVINCES = ['Tarlac', 'Pampanga', 'Nueva Ecija', 'Bulacan', 'Zambales']
BARANGAYS = [
    'Brgy. San Jose', 'Brgy. Poblacion', 'Brgy. Sto. Cristo',
    'Brgy. Tibag', 'Brgy. Maliwalo', 'Brgy. San Nicolas',
    'Brgy. San Roque', 'Brgy. San Vicente', 'Brgy. Salapungan'
]
DATES = [
    '01/15/1990', '03/22/1985', '07/04/2000', '11/30/1995',
    '05/18/1988', '09/12/1975', '02/28/1993', '06/06/1980',
    '12/25/1998', '04/17/2001', '08/08/1965', '10/31/1970',
]

def _name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def _date():
    return random.choice(DATES)

def _place():
    return f"{random.choice(BARANGAYS)}, {random.choice(MUNICIPALITIES)}, {random.choice(PROVINCES)}"


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

        # Template D: PSA/NSO sealed copy (used when filing Form 90)
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


# ─────────────────────────────────────────────────────────────
# 4.  DATASET GENERATOR  (3 classes only — no Form 90)
# ─────────────────────────────────────────────────────────────
def generate_dataset(samples_per_class=150):
    generators = [generate_form102, generate_form103, generate_form97]
    labels_map = [0, 1, 2]  # 0=Form102, 1=Form103, 2=Form97

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
    print("  Certifications Page: Form 102 / 103 / 97 ONLY")
    print("  (Form 90 routing is handled separately via SEX field)")
    print("=" * 60)

    print(f"\n  Generating dataset ({samples_per_class} samples × 3 forms = {samples_per_class * 3} total)...")
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
    headers = ['Form102', 'Form103', 'Form97']
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
        'total_samples': samples_per_class * 3,
        'labels': LABEL_MAP,
        'note': 'Form 90 routing is handled by classify_sex() — not this model',
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
    """Load trained MNB model and classify OCR text from Certifications page."""

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
        Classify OCR text from Certifications page.

        Returns:
            {
                'label':        'Form 102 - Certificate of Live Birth',
                'form_code':    'form102',
                'confidence':   0.95,
                'probabilities': { ... }
            }
        """
        vec   = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(vec)[0]
        idx   = int(np.argmax(probs))

        form_codes = ['form102', 'form103', 'form97']
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
    print("  Testing DocumentClassifier — Certifications Page")
    print("=" * 60)

    classifier = DocumentClassifier()

    test_cases = [
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
