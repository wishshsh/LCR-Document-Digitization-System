# Civil Registry NER System

spaCy NER for Philippine Local Civil Registry Document Digitization.

## Form Mapping

| Source Form | Output Form | Document |
|---|---|---|
| Form 102 | Form 1A | Certificate of Live Birth |
| Form 103 | Form 2A | Certificate of Death |
| Form 97  | Form 3A | Certificate of Marriage |

## Name Assembly Rule

Forms split names into separate boxes:  `(First)` `(Middle)` `(Last)`

NER extracts each part separately, then `name_assembler.py` joins them:

```
"Juan" + "dela Cruz" + "Santos"  →  "Juan dela Cruz Santos"
```

**Form 97 special case:** Form displays `(Last)(Middle)(First)` but output is always `First Middle Last`.

## Project Structure

```
spacyNER/
  labels.py          ← all NER label constants (F102_, F103_, F97_)
  models.py          ← output form dataclasses (Form1A, Form2A, Form3A)
  name_assembler.py  ← joins First+Middle+Last into full names
  extractor.py       ← reads OCR text, extracts field values
  autofill.py        ← maps extracted values → fills form objects
  ocr.py             ← converts scanned images/PDFs to text

training/
  prepare_data.py    ← annotated data → .spacy binary
  train.py           ← fine-tune the model
  evaluate.py        ← check accuracy

tests/
  test_name_assembler.py
```

## Setup (Python 3.9–3.12 required)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python main.py
```

## Fine-Tuning

```bash
# 1. Add name-part annotated examples to training/prepare_data.py
python training/prepare_data.py
python training/train.py
python training/evaluate.py
```
