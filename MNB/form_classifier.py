"""
form_classifier.py
=======================
Multinomial Naive Bayes (MNB) Document Classifier
for Local Civil Registry Document Digitization System

Classifies extracted OCR text into:
  - Form 1A  (Birth Certificate)
  - Form 2A  (Death Certificate)
  - Form 3A  (Marriage Certificate)
  - Form 90  (Application for Marriage License)

Usage:
    pythom form_classifier.py          # trains and saves model
    python form_classifier.py --test   # runs test predictions
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
    0: 'Form 1A - Birth Certificate',
    1: 'Form 2A - Death Certificate',
    2: 'Form 3A - Marriage Certificate',
    3: 'Form 90 - Application for Marriage License',
}
LABEL_NAMES = list(LABEL_MAP.values())

# ─────────────────────────────────────────────────────────────
# 2.  VOCABULARY POOLS  (domain-specific Filipino civil registry)
# ─────────────────────────────────────────────────────────────

# Filipino names pool (subset for sample generation)
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
# 3.  SAMPLE GENERATORS  (one per form type)
# ─────────────────────────────────────────────────────────────

def generate_form1a():
    """Birth Certificate — Form 1A keywords and structure."""
    templates = [
        f"Name of child {_name()} Date of birth {_date()} Place of birth {_place()} "
        f"Name of mother {_name()} Name of father {_name()} Sex {random.choice(['Male','Female'])} "
        f"Legitimacy {random.choice(['Legitimate','Illegitimate'])} Attendant {random.choice(['Physician','Midwife','Nurse'])} "
        f"birth certificate registry birth registration infant newborn child",

        f"Child {_name()} born {_date()} at {_place()} "
        f"mother {_name()} father {_name()} "
        f"birth weight {random.randint(2,4)}.{random.randint(1,9)} kg "
        f"birth order {random.choice(['First','Second','Third'])} birth certificate Form 1A",

        f"Registry number birth {random.randint(100,999)}-{random.randint(1,99):02d} "
        f"name of child {_name()} date of birth {_date()} "
        f"place of birth {_place()} birth certificate municipal civil registrar",

        f"Birth certificate {_name()} born on {_date()} "
        f"place of birth {_place()} "
        f"mother maiden name {_name()} father {_name()} "
        f"type of birth {random.choice(['Single','Twin'])} infant newborn",

        f"Form 1A birth registration {_name()} "
        f"birth date {_date()} birthplace {_place()} "
        f"parents mother {_name()} father {_name()} "
        f"attendant at birth {random.choice(['hospital','midwife','physician'])} sex {random.choice(['male','female'])}",
    ]
    return random.choice(templates)


def generate_form2a():
    """Death Certificate — Form 2A keywords and structure."""
    causes = [
        'Cardiac Arrest', 'Pneumonia', 'Hypertension', 'Diabetes Mellitus',
        'Stroke', 'Respiratory Failure', 'Natural Causes', 'Cancer',
        'Septicemia', 'Renal Failure'
    ]
    templates = [
        f"Name of deceased {_name()} Date of death {_date()} Place of death {_place()} "
        f"Cause of death {random.choice(causes)} Age at death {random.randint(1,95)} "
        f"Sex {random.choice(['Male','Female'])} Civil status {random.choice(['Single','Married','Widowed'])} "
        f"death certificate deceased burial interment",

        f"Deceased {_name()} died on {_date()} at {_place()} "
        f"cause {random.choice(causes)} corpse informant {_name()} "
        f"death certificate Form 2A municipal civil registrar",

        f"Registry number death {random.randint(100,999)}-{random.randint(1,99):02d} "
        f"name of deceased {_name()} date of death {_date()} "
        f"place of death {_place()} cause of death {random.choice(causes)} "
        f"death certificate burial permit",

        f"Death certificate {_name()} died {_date()} "
        f"place {_place()} cause of death {random.choice(causes)} "
        f"informant {_name()} relationship {random.choice(['spouse','child','sibling','parent'])} "
        f"death deceased cadaver autopsy",

        f"Form 2A death registration {_name()} "
        f"date of death {_date()} place of death {_place()} "
        f"immediate cause {random.choice(causes)} "
        f"attending physician {_name()} certificate of death",
    ]
    return random.choice(templates)


def generate_form3a():
    """Marriage Certificate — Form 3A keywords and structure."""
    officers = ['Rev.', 'Judge', 'Mayor', 'Pastor', 'Fr.']
    licenses = [f"{random.randint(10000,99999)}", f"ML-{random.randint(1000,9999)}"]
    templates = [
        f"Name of husband {_name()} Name of wife {_name()} "
        f"Date of marriage {_date()} Place of marriage {_place()} "
        f"Solemnizing officer {random.choice(officers)} {_name()} "
        f"Marriage license number {random.choice(licenses)} witnesses {_name()} {_name()} "
        f"marriage certificate contracting parties wedding",

        f"Husband {_name()} wife {_name()} "
        f"married on {_date()} at {_place()} "
        f"officiated by {random.choice(officers)} {_name()} "
        f"marriage certificate Form 3A solemnizing officer",

        f"Registry number marriage {random.randint(100,999)}-{random.randint(1,99):02d} "
        f"husband {_name()} wife {_name()} "
        f"date of marriage {_date()} place {_place()} "
        f"marriage license {random.choice(licenses)} issued at {_place()} "
        f"marriage certificate civil registrar",

        f"Marriage certificate {_name()} and {_name()} "
        f"solemnized {_date()} at {_place()} "
        f"solemnizing officer {random.choice(officers)} {_name()} "
        f"witnesses {_name()} {_name()} "
        f"marriage contracting parties husband wife ceremony",

        f"Form 3A marriage registration husband {_name()} "
        f"wife {_name()} date of marriage {_date()} "
        f"place of marriage {_place()} "
        f"license number {random.choice(licenses)} marriage nuptial wed",
    ]
    return random.choice(templates)


def generate_form90():
    """Form 90 — Application for Marriage License keywords and structure."""
    statuses = ['Single', 'Widowed', 'Divorced']
    citizenships = ['Filipino', 'Filipino-American', 'Filipino-Chinese']
    templates = [
        f"Name of applicant {_name()} Date of application {_date()} "
        f"Residence {_place()} Civil status {random.choice(statuses)} "
        f"Citizenship {random.choice(citizenships)} "
        f"Name of parent father {_name()} mother {_name()} "
        f"marriage license application Form 90",

        f"Applicant {_name()} applying for marriage license {_date()} "
        f"address {_place()} status {random.choice(statuses)} "
        f"parental consent {_name()} "
        f"marriage license application Form 90 registry",

        f"Registry number application {random.randint(100,999)}-{random.randint(1,99):02d} "
        f"applicant {_name()} co-applicant {_name()} "
        f"date of application {_date()} residence {_place()} "
        f"citizenship {random.choice(citizenships)} marriage license application",

        f"Marriage license application {_name()} and {_name()} "
        f"date {_date()} address {_place()} "
        f"civil status {random.choice(statuses)} citizenship {random.choice(citizenships)} "
        f"parental consent required Form 90 application marriage license",

        f"Form 90 marriage license application {_name()} "
        f"residence {_place()} date {_date()} "
        f"civil status {random.choice(statuses)} "
        f"supporting documents birth certificate baptismal application license",
    ]
    return random.choice(templates)


# ─────────────────────────────────────────────────────────────
# 4.  DATASET GENERATOR
# ─────────────────────────────────────────────────────────────
GENERATORS = [generate_form1a, generate_form2a, generate_form3a, generate_form90]

def generate_dataset(samples_per_class=150):
    """Generate synthetic labeled training data."""
    texts, labels = [], []
    for label, gen in enumerate(GENERATORS):
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
    print("=" * 60)

    print(f"\n  Generating dataset ({samples_per_class} samples × 4 forms = {samples_per_class*4} total)...")
    texts, labels = generate_dataset(samples_per_class)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

    # TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),   # unigrams + bigrams
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

    print(f"\n  Accuracy : {acc*100:.2f}%")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=LABEL_NAMES))

    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  {'':35s} " + "  ".join([f"P{i}" for i in range(4)]))
    for i, row in enumerate(cm):
        print(f"  Actual Form {i+1}A/90: {str(row):40s}")

    # Save model + vectorizer
    model_path = os.path.join(save_dir, 'mnb_classifier.pkl')
    vec_path   = os.path.join(save_dir, 'tfidf_vectorizer.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(clf, f)
    with open(vec_path, 'wb') as f:
        pickle.dump(vectorizer, f)

    # Save metadata
    meta = {
        'accuracy': round(acc * 100, 2),
        'samples_per_class': samples_per_class,
        'total_samples': samples_per_class * 4,
        'labels': LABEL_MAP,
        'model_path': model_path,
        'vectorizer_path': vec_path,
    }
    with open(os.path.join(save_dir, 'mnb_metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"\n  Model saved     : {model_path}")
    print(f"  Vectorizer saved: {vec_path}")
    print(f"\n  Target accuracy : >90%")
    print(f"  Achieved        : {acc*100:.2f}% {'✓' if acc >= 0.90 else '✗ (try increasing samples_per_class)'}")
    print("=" * 60)

    return clf, vectorizer, acc


# ─────────────────────────────────────────────────────────────
# 6.  PREDICT  (use in Flask integration)
# ─────────────────────────────────────────────────────────────
class DocumentClassifier:
    """Load trained MNB model and classify OCR text."""

    def __init__(self, model_dir='models'):
        model_path = os.path.join(model_dir, 'mnb_classifier.pkl')
        vec_path   = os.path.join(model_dir, 'tfidf_vectorizer.pkl')

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run: python document_classifier.py"
            )

        with open(model_path, 'rb') as f:
            self.clf = pickle.load(f)
        with open(vec_path, 'rb') as f:
            self.vectorizer = pickle.load(f)

    def predict(self, text: str) -> dict:
        """
        Classify OCR text and return form type + confidence.

        Returns:
            {
                'label': 'Form 1A - Birth Certificate',
                'form_code': 'form1a',
                'confidence': 0.95,
                'probabilities': { 'Form 1A': 0.95, 'Form 2A': 0.02, ... }
            }
        """
        vec   = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(vec)[0]
        idx   = int(np.argmax(probs))

        form_codes = ['form1a', 'form2a', 'form3a', 'form90']
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
    print("  Testing DocumentClassifier")
    print("=" * 60)

    classifier = DocumentClassifier()

    test_cases = [
        (
            "Name of child Maria Santos Date of birth 01/15/1990 "
            "Place of birth Brgy. San Jose, Tarlac City, Tarlac "
            "Name of mother Lani Santos Name of father Jose Santos "
            "Sex Female birth certificate infant",
            "Form 1A - Birth Certificate"
        ),
        (
            "Name of deceased Pedro Reyes Date of death 03/22/2020 "
            "Place of death Capas, Tarlac Cause of death Cardiac Arrest "
            "Age at death 75 death certificate deceased burial",
            "Form 2A - Death Certificate"
        ),
        (
            "Name of husband Carlos Bautista Name of wife Ana Torres "
            "Date of marriage 07/04/2005 Place of marriage Paniqui, Tarlac "
            "Solemnizing officer Rev. Santos witnesses marriage certificate",
            "Form 3A - Marriage Certificate"
        ),
        (
            "Name of applicant Roberto Lim Date of application 11/30/2023 "
            "Residence Brgy. San Jose, Tarlac City Civil status Single "
            "Citizenship Filipino parental consent marriage license application Form 90",
            "Form 90 - Application for Marriage License"
        ),
    ]

    correct = 0
    for text, expected in test_cases:
        result = classifier.predict(text)
        status = '✓' if expected in result['label'] else '✗'
        if expected in result['label']:
            correct += 1
        print(f"\n  {status} Expected : {expected}")
        print(f"    Predicted: {result['label']} ({result['confidence']*100:.1f}% confidence)")

    print(f"\n  Test Accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%)")
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
        print("  python document_classifier.py --test")
