# app.py
# ============================================================
#  Flask API — Civil Registry Pipeline
#
#  TWO MODES (switch via USE_REAL_PIPELINE below):
#
#  USE_REAL_PIPELINE = False  →  fake data (safe, always works)
#  USE_REAL_PIPELINE = True   →  calls pipeline.py (real models)
#
#  HOW TO ENABLE THE REAL PIPELINE:
#  1. Set USE_REAL_PIPELINE = True
#  2. Set PIPELINE_REPO_PATH to the absolute path of your repo
#     e.g. r"C:\Users\YourName\Documents\thesis-repo"
#  3. Make sure venv has all model dependencies installed
#  4. Run: python app.py
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
from datetime import datetime

# ── sys.path setup ────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
for _p in [
    _BASE,
    os.path.join(_BASE, 'CRNN+CTC'),
    os.path.join(_BASE, 'MNB'),
    os.path.join(_BASE, 'spacyNER'),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

app = Flask(__name__)
CORS(app)

# ── CONFIGURATION ─────────────────────────────────────────────
USE_REAL_PIPELINE = False
USE_TEMPLATE_MATCHING = True
PIPELINE_REPO_PATH = r"C:\xampp\htdocs\python"
# ─────────────────────────────────────────────────────────────

# ── Load template matcher ─────────────────────────────────────
try:
    from template_matcher import (
        extract_fields,
        pdf_to_image,
        detect_form_type,
        _get_crnn,
        _get_paddleocr,
    )
    _template_matcher_ok = True
    print("[app.py] Template matcher loaded")

    print("[app.py] Preloading CRNN+CTC model...")
    _get_crnn()
    print("[app.py] CRNN+CTC preloaded.")

    print("[app.py] Preloading PaddleOCR...")
    _get_paddleocr()
    print("[app.py] PaddleOCR preloaded.")

except Exception as _tm_err:
    _template_matcher_ok = False
    print(f"[app.py] Template matcher unavailable: {_tm_err}")

# ── Load bridge (MNB + spaCyNER) ──────────────────────────────
_bridge = None
try:
    from bridge import CivilRegistryBridge
    print("[app.py] Loading MNB + spaCyNER bridge...")
    _bridge = CivilRegistryBridge()
    print("[app.py] Bridge (MNB + spaCyNER) ready.")
except Exception as _br_err:
    print(f"[app.py] Bridge unavailable (MNB/NER disabled): {_br_err}")

TEMP_DIR = os.environ.get('TEMP_DIR', os.path.join('/tmp', 'uploads', 'temp'))

# ── Load real pipeline (only if enabled) ─────────────────────
_pipeline = None
_pipeline_error = None

if USE_REAL_PIPELINE:
    try:
        if PIPELINE_REPO_PATH not in sys.path:
            sys.path.insert(0, PIPELINE_REPO_PATH)
        from pipeline import CivilRegistryPipeline
        print("[app.py] Loading pipeline models — this may take a moment...")
        _pipeline = CivilRegistryPipeline()
        print("[app.py] ✅ Pipeline ready")
    except Exception:
        _pipeline_error = traceback.format_exc()
        print(f"[app.py] ❌ Pipeline failed to load:\n{_pipeline_error}")
        print("[app.py] ⚠️ Falling back to fake data")


# ── /process endpoint ─────────────────────────────────────────
@app.route('/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    file = request.files['file']
    file2 = request.files.get('file2')
    form_hint = request.form.get('form_hint', '1A')

    hint_to_type = {
        '1A': 'birth',
        '2A': 'death',
        '3A': 'marriage',
        '90': 'marriage',
    }
    form_type = hint_to_type.get(form_hint, 'birth')

    os.makedirs(TEMP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    ext = os.path.splitext(file.filename)[1] or '.pdf'
    saved_path = os.path.join(TEMP_DIR, f'upload_{timestamp}{ext}')
    file.save(saved_path)

    saved_path2 = None
    if file2 and file2.filename:
        ext2 = os.path.splitext(file2.filename)[1] or '.pdf'
        saved_path2 = os.path.join(TEMP_DIR, f'upload_{timestamp}_bride{ext2}')
        file2.save(saved_path2)

    try:
        if USE_REAL_PIPELINE and _pipeline is not None:
            fields, confidence, form_class = _run_real_pipeline(
                saved_path, form_hint, form_type, file2_path=saved_path2
            )
        elif USE_TEMPLATE_MATCHING and _template_matcher_ok:
            fields, confidence, form_class = _run_template_pipeline(
                saved_path, form_hint, file2_path=saved_path2
            )
        else:
            fields, confidence, form_class = _run_fake_pipeline(form_hint)

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[app.py] ❌ Processing error:\n{tb}")
        is_user_error = isinstance(e, ValueError)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'trace': '' if is_user_error else tb,
        }), 200 if is_user_error else 500

    finally:
        try:
            os.remove(saved_path)
        except Exception:
            pass
        if saved_path2:
            try:
                os.remove(saved_path2)
            except Exception:
                pass

    preview_file = f'form_{form_class}_{timestamp}.html'
    preview_path = os.path.join(TEMP_DIR, preview_file)
    with open(preview_path, 'w', encoding='utf-8') as fh:
        fh.write(_build_preview_html(form_class, fields))

    mode_label = "pipeline" if (USE_REAL_PIPELINE and _pipeline) else "template/fake"

    return jsonify({
        'status': 'success',
        'form_class': form_class,
        'raw_text': f'Processed via {mode_label} — Form {form_class}',
        'fields': fields,
        'confidence': confidence,
        'saved_file': preview_file,
        'preview_url': f'/uploads/temp/{preview_file}',
    })


# ── /status endpoint ──────────────────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'mode': 'real_pipeline' if (USE_REAL_PIPELINE and _pipeline) else 'fake_data',
        'pipeline_ready': _pipeline is not None,
        'pipeline_error': _pipeline_error,
        'repo_path': PIPELINE_REPO_PATH if USE_REAL_PIPELINE else None,
    })


# ── /debug endpoint ───────────────────────────────────────────
@app.route('/debug', methods=['GET'])
def debug():
    try:
        import pipeline as _pl_module  # noqa: F401
        return jsonify({'import': 'ok', 'sys_path': sys.path[:6]})
    except Exception:
        return jsonify({
            'import': 'FAILED',
            'trace': traceback.format_exc(),
            'sys_path': sys.path[:6]
        }), 500


# ═════════════════════════════════════════════════════════════
#  REAL PIPELINE
# ═════════════════════════════════════════════════════════════
def _run_real_pipeline(file_path, form_hint, form_type, file2_path=None):
    if form_hint == '90':
        raw_groom = _pipeline.process_pdf(file_path, form_type='marriage')
        groom_fields, groom_conf = _map_pipeline_output_form90(raw_groom, role='groom')

        bride_fields = {}
        bride_conf = {}
        if file2_path:
            raw_bride = _pipeline.process_pdf(file2_path, form_type='marriage')
            bride_fields, bride_conf = _map_pipeline_output_form90(raw_bride, role='bride')

        fields = {**bride_fields, **groom_fields}
        confidence = {**bride_conf, **groom_conf}

        for key in [
            'registry_no', 'city_municipality', 'date_issuance', 'license_no',
            'marriage_day', 'marriage_month', 'marriage_year',
            'marriage_venue', 'marriage_city',
            'groom_first', 'groom_middle', 'groom_last', 'groom_age',
            'groom_citizenship', 'groom_mother_first', 'groom_mother_last',
            'groom_father_first', 'groom_father_last',
            'bride_first', 'bride_middle', 'bride_last', 'bride_age',
            'bride_citizenship', 'bride_mother_first', 'bride_mother_last',
            'bride_father_first', 'bride_father_last',
        ]:
            fields.setdefault(key, '')

        return fields, confidence, '90'

    raw_result = _pipeline.process_pdf(file_path, form_type=form_type)
    actual_class = getattr(raw_result, 'form_class', None) or form_hint
    class_map = {'form1a': '1A', 'form2a': '2A', 'form3a': '3A', 'form90': '90'}
    form_class = class_map.get(str(actual_class).lower(), form_hint)

    fields, confidence = _map_pipeline_output(raw_result, form_class)
    return fields, confidence, form_class


def _map_pipeline_output(raw: dict, form_hint: str):
    confidence = {k: 0.90 for k in raw.keys()}

    if form_hint == '1A':
        fields = {
            'registry_no': raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality': raw.get('city_municipality') or raw.get('city', ''),
            'province': raw.get('province', ''),
            'date_issuance': raw.get('date_issuance') or raw.get('date', ''),
            'child_first': raw.get('child_first') or raw.get('name_of_child_first', ''),
            'child_middle': raw.get('child_middle') or raw.get('name_of_child_middle', ''),
            'child_last': raw.get('child_last') or raw.get('name_of_child_last', ''),
            'sex': raw.get('sex', ''),
            'dob_day': raw.get('dob_day') or raw.get('date_of_birth_day', ''),
            'dob_month': raw.get('dob_month') or raw.get('date_of_birth_month', ''),
            'dob_year': raw.get('dob_year') or raw.get('date_of_birth_year', ''),
            'pob_hospital': raw.get('pob_hospital') or raw.get('place_of_birth_hospital', ''),
            'pob_city': raw.get('pob_city') or raw.get('place_of_birth_city', ''),
            'pob_province': raw.get('pob_province') or raw.get('place_of_birth_province', ''),
            'mother_first': raw.get('mother_first') or raw.get('mother_name_first', ''),
            'mother_middle': raw.get('mother_middle') or raw.get('mother_name_middle', ''),
            'mother_last': raw.get('mother_last') or raw.get('mother_name_last', ''),
            'mother_citizenship': raw.get('mother_citizenship') or raw.get('mother_nationality', ''),
            'mother_age': raw.get('mother_age', ''),
            'father_first': raw.get('father_first') or raw.get('father_name_first', ''),
            'father_middle': raw.get('father_middle') or raw.get('father_name_middle', ''),
            'father_last': raw.get('father_last') or raw.get('father_name_last', ''),
            'father_citizenship': raw.get('father_citizenship') or raw.get('father_nationality', ''),
            'parents_marriage_day': raw.get('parents_marriage_day', ''),
            'parents_marriage_month': raw.get('parents_marriage_month', ''),
            'parents_marriage_year': raw.get('parents_marriage_year', ''),
            'parents_marriage_city': raw.get('parents_marriage_city', ''),
            'parents_marriage_province': raw.get('parents_marriage_province', ''),
            'date_submitted': raw.get('date_submitted') or raw.get('date_of_registration', ''),
            'prepared_by': raw.get('prepared_by', ''),
        }

    elif form_hint == '2A':
        fields = {
            'registry_no': raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality': raw.get('city_municipality') or raw.get('city', ''),
            'province': raw.get('province', ''),
            'date_issuance': raw.get('date_issuance') or raw.get('date', ''),
            'deceased_first': raw.get('deceased_first') or raw.get('name_of_deceased_first', ''),
            'deceased_middle': raw.get('deceased_middle') or raw.get('name_of_deceased_middle', ''),
            'deceased_last': raw.get('deceased_last') or raw.get('name_of_deceased_last', ''),
            'sex': raw.get('sex', ''),
            'age_years': raw.get('age_years') or raw.get('age', ''),
            'civil_status': raw.get('civil_status', ''),
            'citizenship': raw.get('citizenship') or raw.get('nationality', ''),
            'dod_day': raw.get('dod_day') or raw.get('date_of_death_day', ''),
            'dod_month': raw.get('dod_month') or raw.get('date_of_death_month', ''),
            'dod_year': raw.get('dod_year') or raw.get('date_of_death_year', ''),
            'pod_hospital': raw.get('pod_hospital') or raw.get('place_of_death_hospital', ''),
            'pod_city': raw.get('pod_city') or raw.get('place_of_death_city', ''),
            'pod_province': raw.get('pod_province') or raw.get('place_of_death_province', ''),
            'cause_immediate': raw.get('cause_immediate') or raw.get('cause_of_death', ''),
            'cause_antecedent': raw.get('cause_antecedent', ''),
            'cause_underlying': raw.get('cause_underlying', ''),
            'date_submitted': raw.get('date_submitted') or raw.get('date_of_registration', ''),
        }

    else:
        fields = {
            'registry_no': raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality': raw.get('city_municipality') or raw.get('city', ''),
            'province': raw.get('province', ''),
            'date_issuance': raw.get('date_issuance') or raw.get('date', ''),
            'husband_first': raw.get('husband_first') or raw.get('husband_name_first', ''),
            'husband_middle': raw.get('husband_middle') or raw.get('husband_name_middle', ''),
            'husband_last': raw.get('husband_last') or raw.get('husband_name_last', ''),
            'husband_age': raw.get('husband_age', ''),
            'husband_citizenship': raw.get('husband_citizenship') or raw.get('husband_nationality', ''),
            'husband_mother_first': raw.get('husband_mother_first', ''),
            'husband_mother_last': raw.get('husband_mother_last', ''),
            'husband_mother_citizenship': raw.get('husband_mother_citizenship', ''),
            'husband_father_first': raw.get('husband_father_first', ''),
            'husband_father_last': raw.get('husband_father_last', ''),
            'husband_father_citizenship': raw.get('husband_father_citizenship', ''),
            'wife_first': raw.get('wife_first') or raw.get('wife_name_first', ''),
            'wife_middle': raw.get('wife_middle') or raw.get('wife_name_middle', ''),
            'wife_last': raw.get('wife_last') or raw.get('wife_name_last', ''),
            'wife_age': raw.get('wife_age', ''),
            'wife_citizenship': raw.get('wife_citizenship') or raw.get('wife_nationality', ''),
            'wife_mother_first': raw.get('wife_mother_first', ''),
            'wife_mother_last': raw.get('wife_mother_last', ''),
            'wife_mother_citizenship': raw.get('wife_mother_citizenship', ''),
            'wife_father_first': raw.get('wife_father_first', ''),
            'wife_father_last': raw.get('wife_father_last', ''),
            'wife_father_citizenship': raw.get('wife_father_citizenship', ''),
            'marriage_day': raw.get('marriage_day') or raw.get('date_of_marriage_day', ''),
            'marriage_month': raw.get('marriage_month') or raw.get('date_of_marriage_month', ''),
            'marriage_year': raw.get('marriage_year') or raw.get('date_of_marriage_year', ''),
            'marriage_venue': raw.get('marriage_venue', ''),
            'marriage_city': raw.get('marriage_city', ''),
            'marriage_province': raw.get('marriage_province', ''),
            'date_submitted': raw.get('date_submitted') or raw.get('date_of_registration', ''),
        }

    for k, v in raw.items():
        if k not in fields and v:
            fields[k] = v

    return fields, confidence


def _map_pipeline_output_form90(raw: dict, role: str):
    confidence = {k: 0.90 for k in raw.keys()}

    husband = raw.get('husband') or {}
    wife = raw.get('wife') or {}
    if not isinstance(husband, dict):
        husband = {}
    if not isinstance(wife, dict):
        wife = {}

    dom_raw = raw.get('date_of_marriage') or ''
    dom_parts = [p.strip() for p in str(dom_raw).split(',') if p.strip()]
    marriage_day = dom_parts[0] if len(dom_parts) > 0 else ''
    marriage_month = dom_parts[1] if len(dom_parts) > 1 else ''
    marriage_year = dom_parts[2] if len(dom_parts) > 2 else ''

    pom_raw = raw.get('place_of_marriage') or ''
    pom_parts = [p.strip() for p in str(pom_raw).split(',') if p.strip()]
    marriage_venue = pom_parts[0] if len(pom_parts) > 0 else ''
    marriage_city = pom_parts[1] if len(pom_parts) > 1 else ''

    shared = {
        'registry_no': str(raw.get('registry_number') or '').strip(),
        'city_municipality': marriage_city,
        'date_issuance': str(raw.get('date_of_registration') or '').strip(),
        'license_no': str(raw.get('license_no') or raw.get('license_number') or '').strip(),
        'marriage_day': marriage_day,
        'marriage_month': marriage_month,
        'marriage_year': marriage_year,
        'marriage_venue': marriage_venue,
        'marriage_city': marriage_city,
        'marriage_province': str(raw.get('province') or '').strip(),
    }

    if role == 'groom':
        person = husband
        fields = {
            **shared,
            'groom_first': str(person.get('first_name') or person.get('first') or raw.get('groom_first') or '').strip(),
            'groom_middle': str(person.get('middle_name') or person.get('middle') or raw.get('groom_middle') or '').strip(),
            'groom_last': str(person.get('last_name') or person.get('last') or raw.get('groom_last') or '').strip(),
            'groom_age': str(person.get('age') or raw.get('groom_age') or '').strip(),
            'groom_citizenship': str(person.get('citizenship') or person.get('nationality') or raw.get('groom_citizenship') or '').strip(),
            'groom_civil_status': str(person.get('civil_status') or '').strip(),
            'groom_residence': str(person.get('residence') or person.get('address') or '').strip(),
            'groom_mother_first': str(person.get('mother_first') or person.get('mother_name') or '').strip(),
            'groom_mother_last': str(person.get('mother_last') or '').strip(),
            'groom_father_first': str(person.get('father_first') or person.get('father_name') or '').strip(),
            'groom_father_last': str(person.get('father_last') or '').strip(),
        }
    else:
        person = wife
        fields = {
            **shared,
            'bride_first': str(person.get('first_name') or person.get('first') or raw.get('bride_first') or '').strip(),
            'bride_middle': str(person.get('middle_name') or person.get('middle') or raw.get('bride_middle') or '').strip(),
            'bride_last': str(person.get('last_name') or person.get('last') or raw.get('bride_last') or '').strip(),
            'bride_age': str(person.get('age') or raw.get('bride_age') or '').strip(),
            'bride_citizenship': str(person.get('citizenship') or person.get('nationality') or raw.get('bride_citizenship') or '').strip(),
            'bride_civil_status': str(person.get('civil_status') or '').strip(),
            'bride_residence': str(person.get('residence') or person.get('address') or '').strip(),
            'bride_mother_first': str(person.get('mother_first') or person.get('mother_name') or '').strip(),
            'bride_mother_last': str(person.get('mother_last') or '').strip(),
            'bride_father_first': str(person.get('father_first') or person.get('father_name') or '').strip(),
            'bride_father_last': str(person.get('father_last') or '').strip(),
        }

    fields = {k: v for k, v in fields.items() if v}
    return fields, confidence


# ═════════════════════════════════════════════════════════════
#  TEMPLATE MATCHING PIPELINE
# ═════════════════════════════════════════════════════════════
def _run_template_pipeline(file_path, form_hint, file2_path=None):
    img_path = file_path
    if file_path.lower().endswith('.pdf'):
        img_path = pdf_to_image(file_path) or file_path

    hint_to_source = {'1A': '102', '2A': '103', '3A': '97', '90': '90'}
    source_type = hint_to_source.get(form_hint, '102')

    detected_source = detect_form_type(img_path)
    source_to_hint = {'102': '1A', '103': '2A', '97': '3A', '90': '90'}
    detected_hint = source_to_hint.get(detected_source, '1A')

    CERT_HINTS = {'1A', '2A', '3A'}
    LICENSE_HINTS = {'90'}

    if form_hint in CERT_HINTS and detected_hint in LICENSE_HINTS:
        raise ValueError(
            'Wrong form uploaded. This appears to be a Marriage License (Form 90). '
            'Please upload it under Marriage License instead.'
        )
    if form_hint in LICENSE_HINTS and detected_hint in CERT_HINTS:
        raise ValueError(
            f'Wrong form uploaded. This appears to be a Form {detected_hint} (Certification). '
            f'Please upload it under Certifications instead.'
        )

    if form_hint == '1A':
        form_hint = detected_hint
        source_type = detected_source

    raw = extract_fields(img_path, source_type)

    if isinstance(raw, dict) and raw.get('status') == 'error':
        print('[app.py] Blank page detected — skipping extraction')
        raise ValueError('Blank page detected. Please try another file.')

    if form_hint == '90' and file2_path:
        img_path2 = file2_path
        if file2_path.lower().endswith('.pdf'):
            img_path2 = pdf_to_image(file2_path) or file2_path
        raw2 = extract_fields(img_path2, '90')
        if isinstance(raw2, dict) and raw2.get('status') == 'error':
            print(f'[app.py] Bride file aborted: {raw2["message"]}')
        else:
            raw = {**raw, **raw2}

    fields = _map_template_output(raw, form_hint)
    form_class = form_hint if form_hint in ('1A', '2A', '3A', '90') else '1A'

    if _bridge is not None:
        try:
            ner_text = _raw_to_ner_text(raw, source_type)

            if source_type == '90':
                mnb_result = {
                    'label': 'Form 90 - Application for Marriage License',
                    'form_code': 'form90',
                    'confidence': 1.0
                }
            else:
                mnb_result = _bridge.mnb.classify_full(ner_text)

            print(f'[app.py] MNB: {mnb_result["label"]} ({mnb_result["confidence"]:.1%})')

            if source_type == '102':
                ner_form = _bridge.filler.fill_form_1a(ner_text)
            elif source_type == '103':
                ner_form = _bridge.filler.fill_form_2a(ner_text)
            elif source_type == '97':
                ner_form = _bridge.filler.fill_form_3a(ner_text)
            else:
                ner_form = _bridge.filler.fill_form_90(ner_text, ner_text)

            ner_fields = _ner_to_fields(ner_form, raw, form_hint)

            TRUST_TEMPLATE_KEYS = {
                'groom_name', 'bride_name',
                'groom_age', 'bride_age', 'husband_age', 'wife_age',
                'groom_dob', 'bride_dob', 'husband_dob', 'wife_dob',
                'registry_no', 'license_no', 'date_issuance',
            }

            def _better(ner_val, tmpl_val, key):
                if key in TRUST_TEMPLATE_KEYS:
                    return tmpl_val if tmpl_val else ner_val
                if not ner_val:
                    return tmpl_val
                if not tmpl_val:
                    return ner_val
                return ner_val if len(ner_val) >= len(tmpl_val) else tmpl_val

            fields = {k: _better(ner_fields.get(k, ''), v, k) for k, v in fields.items()}
            for k, v in ner_fields.items():
                if k not in fields and v:
                    fields[k] = v

            ner_count = sum(1 for v in ner_fields.values() if v)
            print(f'[app.py] NER enriched {ner_count} fields')
            confidence = {k: mnb_result['confidence'] for k in fields}

        except Exception as _ner_err:
            print(f'[app.py] NER error (using template only): {_ner_err}')
            confidence = {k: 0.85 for k in fields}
    else:
        confidence = {k: 0.85 for k in fields}

    non_empty = {k: v for k, v in fields.items() if v}
    print(f'[app.py] form_class={form_class}, {len(non_empty)}/{len(fields)} non-empty fields')
    for k, v in non_empty.items():
        print(f'  {k:<30} = {v}')

    return fields, confidence, form_class


def _clean_ocr(text: str) -> str:
    import re
    if not text:
        return text
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip('.,;:')
    return text


def _clean_age(text: str) -> str:
    import re
    nums = re.findall(r'\b\d+\b', text)
    return nums[-1] if nums else _clean_ocr(text)


def _clean_civil_status(text: str) -> str:
    t = text.lower().replace(' ', '')
    if any(x in t for x in ['singl', 'fngle', 'fingle', 'single']):
        return 'Single'
    if any(x in t for x in ['marr', 'maried', 'married']):
        return 'Married'
    if any(x in t for x in ['widow', 'widw']):
        return 'Widowed'
    if any(x in t for x in ['separ', 'annul']):
        return 'Separated'
    return _clean_ocr(text)


def _map_template_output(raw: dict, form_hint: str) -> dict:
    def g(key, *aliases):
        for k in (key,) + aliases:
            if raw.get(k):
                return raw[k]
        return ''

    if form_hint == '1A':
        return {
            'registry_no': g('registry_no'),
            'city_municipality': g('city_municipality'),
            'province': g('province'),
            'date_submitted': g('registration_date'),
            'child_first': g('name_first'),
            'child_middle': g('name_middle'),
            'child_last': g('name_last'),
            'sex': g('sex'),
            'dob_day': g('dob_day'),
            'dob_month': g('dob_month'),
            'dob_year': g('dob_year'),
            'pob_city': g('place_of_birth'),
            'mother_first': g('mother_name'),
            'mother_citizenship': g('mother_citizenship'),
            'father_first': g('father_name'),
            'father_citizenship': g('father_citizenship'),
            'parents_marriage_month': g('marriage_date'),
            'parents_marriage_city': g('marriage_place'),
        }

    elif form_hint == '2A':
        cause = ' / '.join(filter(None, [
            g('cause_immediate'), g('cause_antecedent'), g('cause_underlying')
        ]))
        return {
            'registry_no': g('registry_no'),
            'city_municipality': g('city_municipality'),
            'province': g('province'),
            'date_submitted': g('registration_date'),
            'deceased_first': g('deceased_name'),
            'sex': g('sex'),
            'age_years': g('age'),
            'civil_status': g('civil_status'),
            'citizenship': g('citizenship'),
            'dod_full': g('date_of_death'),
            'pod_hospital': g('place_of_death'),
            'cause_immediate': cause,
        }

    elif form_hint == '3A':
        return {
            'registry_no': g('registry_no'),
            'city_municipality': g('city_municipality'),
            'province': g('province'),
            'date_submitted': g('registration_date'),
            'husband_first': g('husband_name_first'),
            'husband_middle': g('husband_name_middle'),
            'husband_last': g('husband_name_last'),
            'husband_age': g('husband_age'),
            'husband_citizenship': g('husband_citizenship'),
            'husband_mother_first': g('husband_mother_name'),
            'husband_father_first': g('husband_father_name'),
            'husband_mother_citizenship': g('husband_mother_citizenship'),
            'husband_father_citizenship': g('husband_father_citizenship'),
            'wife_first': g('wife_name_first'),
            'wife_middle': g('wife_name_middle'),
            'wife_last': g('wife_name_last'),
            'wife_age': g('wife_age'),
            'wife_citizenship': g('wife_citizenship'),
            'wife_mother_first': g('wife_mother_name'),
            'wife_father_first': g('wife_father_name'),
            'wife_mother_citizenship': g('wife_mother_citizenship'),
            'wife_father_citizenship': g('wife_father_citizenship'),
            'marriage_venue': g('place_of_marriage'),
            'marriage_city': g('city_municipality'),
            'marriage_month': g('date_of_marriage'),
        }

    else:
        def _join_name(*keys):
            return ' '.join(raw.get(k, '') for k in keys).strip()

        return {
            'registry_no': g('registry_no'),
            'city_municipality': g('city_municipality'),
            'province': raw.get('province', '').strip(),
            'license_no': g('marriage_license_no'),
            'date_issuance': g('date_issued'),
            'groom_name': _join_name('groom_name_first', 'groom_name_middle', 'groom_name_last'),
            'groom_dob': g('groom_dob'),
            'groom_age': g('groom_age'),
            'groom_place_of_birth': g('groom_place_of_birth'),
            'groom_sex': g('groom_sex'),
            'groom_citizenship': g('groom_citizenship'),
            'groom_civil_status': g('groom_civil_status'),
            'groom_residence': g('groom_residence'),
            'groom_religion': g('groom_religion'),
            'groom_father_first': g('groom_father_name'),
            'groom_father_citizenship': g('groom_father_citizenship'),
            'groom_mother_first': g('groom_mother_name'),
            'groom_mother_citizenship': g('groom_mother_citizenship'),
            'bride_name': _join_name('bride_name_first', 'bride_name_middle', 'bride_name_last'),
            'bride_dob': g('bride_dob'),
            'bride_age': g('bride_age'),
            'bride_place_of_birth': g('bride_place_of_birth'),
            'bride_sex': g('bride_sex'),
            'bride_citizenship': g('bride_citizenship'),
            'bride_civil_status': g('bride_civil_status'),
            'bride_residence': g('bride_residence'),
            'bride_religion': g('bride_religion'),
            'bride_father_first': g('bride_father_name'),
            'bride_father_citizenship': g('bride_father_citizenship'),
            'bride_mother_first': g('bride_mother_name'),
            'bride_mother_citizenship': g('bride_mother_citizenship'),
        }


# ═════════════════════════════════════════════════════════════
#  BRIDGE HELPERS
# ═════════════════════════════════════════════════════════════
def _raw_to_ner_text(raw: dict, source_type: str) -> str:
    def g(*keys):
        for k in keys:
            v = raw.get(k, '')
            if v:
                return str(v)
        return ''

    if source_type == '102':
        return (
            f"Registry No.: {g('registry_no')}\n"
            f"Date of Registration: {g('registration_date')}\n"
            f"1. NAME: {g('name_first')} {g('name_middle')} {g('name_last')}\n"
            f"2. SEX: {g('sex')}\n"
            f"3. DATE OF BIRTH: {g('dob_month')} {g('dob_day')}, {g('dob_year')}\n"
            f"4. PLACE OF BIRTH: {g('place_of_birth')}\n"
            f"MOTHER:\n"
            f"7. MAIDEN NAME: {g('mother_name')}\n"
            f"8. CITIZENSHIP/NATIONALITY: {g('mother_citizenship')}\n"
            f"FATHER:\n"
            f"14. NAME: {g('father_name')}\n"
            f"15. CITIZENSHIP/NATIONALITY: {g('father_citizenship')}\n"
            f"MARRIAGE OF PARENTS:\n"
            f"20a. DATE: {g('marriage_date')}\n"
            f"20b. PLACE: {g('marriage_place')}\n"
        )

    elif source_type == '103':
        return (
            f"Registry No.: {g('registry_no')}\n"
            f"Date of Registration: {g('registration_date')}\n"
            f"1. NAME (First): {g('deceased_name')}\n"
            f"2. SEX: {g('sex')}\n"
            f"4. AGE: {g('age')}\n"
            f"9. CIVIL STATUS: {g('civil_status')}\n"
            f"7. CITIZENSHIP/NATIONALITY: {g('citizenship')}\n"
            f"6. DATE OF DEATH: {g('date_of_death')}\n"
            f"5. PLACE OF DEATH: {g('place_of_death')}\n"
            f"17. CAUSE OF DEATH: {g('cause_immediate')}\n"
            f"Antecedent cause: {g('cause_antecedent')}\n"
            f"Underlying cause: {g('cause_underlying')}\n"
        )

    elif source_type == '97':
        return (
            f"Registry No.: {g('registry_no')}\n"
            f"Date of Registration: {g('registration_date')}\n"
            f"HUSBAND:\n"
            f"1. NAME (First): {g('husband_name_first')}  (Middle): {g('husband_name_middle')}  (Last): {g('husband_name_last')}\n"
            f"2b. AGE: {g('husband_age')}\n"
            f"4b. CITIZENSHIP/NATIONALITY: {g('husband_citizenship')}\n"
            f"8. NAME OF FATHER: {g('husband_father_name')}\n"
            f"8b. FATHER CITIZENSHIP/NATIONALITY: {g('husband_father_citizenship')}\n"
            f"10. NAME OF MOTHER: {g('husband_mother_name')}\n"
            f"10b. MOTHER CITIZENSHIP/NATIONALITY: {g('husband_mother_citizenship')}\n"
            f"WIFE:\n"
            f"1. NAME (First): {g('wife_name_first')}  (Middle): {g('wife_name_middle')}  (Last): {g('wife_name_last')}\n"
            f"2b. AGE: {g('wife_age')}\n"
            f"4b. CITIZENSHIP/NATIONALITY: {g('wife_citizenship')}\n"
            f"8. NAME OF FATHER: {g('wife_father_name')}\n"
            f"8b. FATHER CITIZENSHIP/NATIONALITY: {g('wife_father_citizenship')}\n"
            f"10. NAME OF MOTHER: {g('wife_mother_name')}\n"
            f"10b. MOTHER CITIZENSHIP/NATIONALITY: {g('wife_mother_citizenship')}\n"
            f"15. PLACE OF MARRIAGE: {g('place_of_marriage')}\n"
            f"16. DATE OF MARRIAGE: {g('date_of_marriage')}\n"
        )

    else:
        return (
            f"GROOM:\n"
            f"1. NAME (First): {g('groom_name_first')}  (Middle): {g('groom_name_middle')}  (Last): {g('groom_name_last')}\n"
            f"2. DATE OF BIRTH: {g('groom_dob')}\n"
            f"3. PLACE OF BIRTH: {g('groom_place_of_birth')}\n"
            f"4. SEX: {g('groom_sex')}\n"
            f"5. CITIZENSHIP/NATIONALITY: {g('groom_citizenship')}\n"
            f"NAME OF FATHER: {g('groom_father_name')}\n"
            f"FATHER CITIZENSHIP/NATIONALITY: {g('groom_father_citizenship')}\n"
            f"NAME OF MOTHER: {g('groom_mother_name')}\n"
            f"MOTHER CITIZENSHIP/NATIONALITY: {g('groom_mother_citizenship')}\n"
            f"BRIDE:\n"
            f"1. NAME (First): {g('bride_name_first')}  (Middle): {g('bride_name_middle')}  (Last): {g('bride_name_last')}\n"
            f"2. DATE OF BIRTH: {g('bride_dob')}\n"
            f"3. PLACE OF BIRTH: {g('bride_place_of_birth')}\n"
            f"4. SEX: {g('bride_sex')}\n"
            f"5. CITIZENSHIP/NATIONALITY: {g('bride_citizenship')}\n"
            f"NAME OF FATHER: {g('bride_father_name')}\n"
            f"FATHER CITIZENSHIP/NATIONALITY: {g('bride_father_citizenship')}\n"
            f"NAME OF MOTHER: {g('bride_mother_name')}\n"
            f"MOTHER CITIZENSHIP/NATIONALITY: {g('bride_mother_citizenship')}\n"
        )


def _split_name(full: str):
    parts = (full or '').split()
    if not parts:
        return '', '', ''
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ''
    mid = ' '.join(parts[1:-1]) if len(parts) > 2 else ''
    return first, mid, last


def _ner_to_fields(form, raw: dict, form_hint: str) -> dict:
    def r(*keys):
        for k in keys:
            v = raw.get(k, '')
            if v:
                return v
        return ''

    def ga(attr, *fallback_keys):
        v = getattr(form, attr, None) or ''
        return v or r(*fallback_keys)

    if form_hint == '1A':
        cf, cm, cl = _split_name(getattr(form, 'name_of_child', '') or '')
        return {
            'registry_no': ga('registry_number', 'registry_no'),
            'city_municipality': r('city_municipality'),
            'province': r('province'),
            'date_submitted': ga('date_of_registration', 'registration_date'),
            'child_first': cf or r('name_first'),
            'child_middle': cm or r('name_middle'),
            'child_last': cl or r('name_last'),
            'sex': ga('sex', 'sex'),
            'dob_day': r('dob_day'),
            'dob_month': r('dob_month'),
            'dob_year': r('dob_year'),
            'pob_city': ga('place_of_birth', 'place_of_birth'),
            'mother_first': ga('name_of_mother', 'mother_name'),
            'mother_citizenship': ga('nationality_of_mother', 'mother_citizenship'),
            'father_first': ga('name_of_father', 'father_name'),
            'father_citizenship': ga('nationality_of_father', 'father_citizenship'),
            'parents_marriage_month': ga('date_of_marriage_of_parents', 'marriage_date'),
            'parents_marriage_city': ga('place_of_marriage_of_parents', 'marriage_place'),
        }

    elif form_hint == '2A':
        cause = ' / '.join(filter(None, [
            getattr(form, 'cause_of_death', ''),
            getattr(form, 'cause_antecedent', ''),
            getattr(form, 'cause_underlying', ''),
        ])) or ' / '.join(filter(None, [
            r('cause_immediate'), r('cause_antecedent'), r('cause_underlying')
        ]))
        return {
            'registry_no': ga('registry_number', 'registry_no'),
            'city_municipality': r('city_municipality'),
            'province': r('province'),
            'date_submitted': ga('date_of_registration', 'registration_date'),
            'deceased_first': ga('name_of_deceased', 'deceased_name'),
            'sex': ga('sex', 'sex'),
            'age_years': ga('age', 'age'),
            'civil_status': ga('civil_status', 'civil_status'),
            'citizenship': ga('nationality', 'citizenship'),
            'dod_full': ga('date_of_death', 'date_of_death'),
            'pod_hospital': ga('place_of_death', 'place_of_death'),
            'cause_immediate': cause,
        }

    elif form_hint == '3A':
        h = getattr(form, 'husband', None)
        w = getattr(form, 'wife', None)
        hd = h.to_dict() if h else {}
        wd = w.to_dict() if w else {}
        return {
            'registry_no': ga('registry_number', 'registry_no'),
            'city_municipality': r('city_municipality'),
            'province': r('province'),
            'date_submitted': ga('date_of_registration', 'registration_date'),
            'husband_first': hd.get('name') or r('husband_name_first'),
            'husband_middle': r('husband_name_middle'),
            'husband_last': r('husband_name_last'),
            'husband_age': hd.get('age') or r('husband_age'),
            'husband_citizenship': hd.get('nationality') or r('husband_citizenship'),
            'husband_mother_first': hd.get('name_of_mother') or r('husband_mother_name'),
            'husband_mother_citizenship': hd.get('nationality_of_mother') or r('husband_mother_citizenship'),
            'husband_father_first': hd.get('name_of_father') or r('husband_father_name'),
            'husband_father_citizenship': hd.get('nationality_of_father') or r('husband_father_citizenship'),
            'wife_first': wd.get('name') or r('wife_name_first'),
            'wife_middle': r('wife_name_middle'),
            'wife_last': r('wife_name_last'),
            'wife_age': wd.get('age') or r('wife_age'),
            'wife_citizenship': wd.get('nationality') or r('wife_citizenship'),
            'wife_mother_first': wd.get('name_of_mother') or r('wife_mother_name'),
            'wife_mother_citizenship': wd.get('nationality_of_mother') or r('wife_mother_citizenship'),
            'wife_father_first': wd.get('name_of_father') or r('wife_father_name'),
            'wife_father_citizenship': wd.get('nationality_of_father') or r('wife_father_citizenship'),
            'marriage_venue': ga('place_of_marriage', 'place_of_marriage'),
            'marriage_city': r('city_municipality'),
            'marriage_month': ga('date_of_marriage', 'date_of_marriage'),
        }

    else:
        groom = getattr(form, 'groom', None)
        bride = getattr(form, 'bride', None)
        gd = groom.to_dict() if groom else {}
        bd = bride.to_dict() if bride else {}
        return {
            'registry_no': r('registry_no'),
            'city_municipality': r('city_municipality'),
            'province': r('province'),
            'license_no': r('marriage_license_no'),
            'date_issuance': r('date_issued'),
            'groom_name': (gd.get('name_of_applicant') or ' '.join(filter(None, [
                r('groom_name_first'), r('groom_name_middle'), r('groom_name_last')
            ]))).strip(),
            'groom_dob': gd.get('date_of_birth') or r('groom_dob'),
            'groom_age': gd.get('age') or r('groom_age'),
            'groom_place_of_birth': gd.get('place_of_birth') or r('groom_place_of_birth'),
            'groom_sex': gd.get('sex') or r('groom_sex'),
            'groom_citizenship': gd.get('citizenship') or r('groom_citizenship'),
            'groom_civil_status': gd.get('civil_status', r('groom_civil_status')),
            'groom_residence': gd.get('residence') or r('groom_residence'),
            'groom_religion': gd.get('religion') or r('groom_religion'),
            'groom_father_first': gd.get('name_of_father') or r('groom_father_name'),
            'groom_father_citizenship': gd.get('father_citizenship') or r('groom_father_citizenship'),
            'groom_mother_first': gd.get('maiden_name_of_mother') or r('groom_mother_name'),
            'groom_mother_citizenship': gd.get('mother_citizenship') or r('groom_mother_citizenship'),
            'bride_name': (bd.get('name_of_applicant') or ' '.join(filter(None, [
                r('bride_name_first'), r('bride_name_middle'), r('bride_name_last')
            ]))).strip(),
            'bride_dob': bd.get('date_of_birth') or r('bride_dob'),
            'bride_age': bd.get('age') or r('bride_age'),
            'bride_place_of_birth': bd.get('place_of_birth') or r('bride_place_of_birth'),
            'bride_sex': bd.get('sex') or r('bride_sex'),
            'bride_citizenship': bd.get('citizenship') or r('bride_citizenship'),
            'bride_civil_status': bd.get('civil_status', r('bride_civil_status')),
            'bride_residence': bd.get('residence') or r('bride_residence'),
            'bride_religion': bd.get('religion') or r('bride_religion'),
            'bride_father_first': bd.get('name_of_father') or r('bride_father_name'),
            'bride_father_citizenship': bd.get('father_citizenship') or r('bride_father_citizenship'),
            'bride_mother_first': bd.get('maiden_name_of_mother') or r('bride_mother_name'),
            'bride_mother_citizenship': bd.get('mother_citizenship') or r('bride_mother_citizenship'),
        }


# ═════════════════════════════════════════════════════════════
#  FAKE PIPELINE
# ═════════════════════════════════════════════════════════════
def _run_fake_pipeline(form_hint):
    if form_hint == '1A':
        fields = {
            'registry_no': '2026-BC-00123',
            'city_municipality': 'Tarlac City',
            'province': 'Tarlac',
            'date_issuance': datetime.now().strftime('%B %d, %Y'),
            'child_first': 'Maria Luisa',
            'child_middle': 'Dela Cruz',
            'child_last': 'Santos',
            'sex': 'Female',
            'dob_day': '10',
            'dob_month': 'January',
            'dob_year': '2026',
            'pob_city': 'Tarlac City',
            'pob_province': 'Tarlac',
            'mother_first': 'Rosa',
            'mother_middle': 'Reyes',
            'mother_last': 'Dela Cruz',
            'mother_citizenship': 'Filipino',
            'mother_age': '28',
            'father_first': 'Juan Pedro',
            'father_middle': '',
            'father_last': 'Santos',
            'father_citizenship': 'Filipino',
            'parents_marriage_day': '12',
            'parents_marriage_month': 'June',
            'parents_marriage_year': '2020',
            'parents_marriage_city': 'Tarlac City',
            'parents_marriage_province': 'Tarlac',
            'date_submitted': 'January 15, 2026',
            'processed_by': 'John Doe',
            'verified_position': 'City Civil Registrar',
            'issued_to': 'Rosa Reyes Dela Cruz',
            'amount_paid': '75.00',
            'or_number': 'OR-2026-00456',
            'date_paid': datetime.now().strftime('%B %d, %Y'),
        }

    elif form_hint == '2A':
        fields = {
            'registry_no': '2026-DC-00045',
            'city_municipality': 'Tarlac City',
            'province': 'Tarlac',
            'date_issuance': datetime.now().strftime('%B %d, %Y'),
            'deceased_first': 'Roberto',
            'deceased_middle': 'Cruz',
            'deceased_last': 'Villanueva',
            'sex': 'Male',
            'age_years': '72',
            'civil_status': 'Married',
            'citizenship': 'Filipino',
            'dod_day': '28',
            'dod_month': 'January',
            'dod_year': '2026',
            'pod_hospital': 'Tarlac Provincial Hospital',
            'pod_city': 'Tarlac City',
            'pod_province': 'Tarlac',
            'cause_immediate': 'Cardiopulmonary Arrest',
            'date_submitted': 'February 1, 2026',
            'processed_by': 'John Doe',
        }

    elif form_hint == '3A':
        fields = {
            'registry_no': '2026-MC-00112',
            'city_municipality': 'Tarlac City',
            'province': 'Tarlac',
            'date_issuance': datetime.now().strftime('%B %d, %Y'),
            'husband_first': 'Carlos',
            'husband_middle': 'Mendoza',
            'husband_last': 'Reyes',
            'husband_age': '29',
            'husband_citizenship': 'Filipino',
            'husband_mother_first': 'Ana',
            'husband_father_first': 'Pedro',
            'husband_mother_citizenship': 'Filipino',
            'husband_father_citizenship': 'Filipino',
            'wife_first': 'Elena',
            'wife_middle': 'Santos',
            'wife_last': 'Garcia',
            'wife_age': '27',
            'wife_citizenship': 'Filipino',
            'wife_mother_first': 'Luz',
            'wife_father_first': 'Mario',
            'wife_mother_citizenship': 'Filipino',
            'wife_father_citizenship': 'Filipino',
            'marriage_venue': 'St. Sebastian Cathedral',
            'marriage_city': 'Tarlac City',
            'marriage_month': 'January 25, 2026',
            'date_submitted': 'January 26, 2026',
        }

    else:
        fields = {
            'registry_no': 'ML-2026-00788',
            'city_municipality': 'Tarlac City',
            'province': 'Tarlac',
            'license_no': 'LIC-2026-0455',
            'date_issuance': 'March 02, 2026',
            'groom_name': 'Mark Anthony Dela Cruz',
            'groom_dob': 'May 04, 1998',
            'groom_age': '27',
            'groom_place_of_birth': 'Tarlac City',
            'groom_sex': 'MALE',
            'groom_citizenship': 'Filipino',
            'groom_civil_status': 'Single',
            'groom_residence': 'San Roque, Tarlac',
            'groom_religion': 'Catholic',
            'groom_father_first': 'Jose Dela Cruz',
            'groom_father_citizenship': 'Filipino',
            'groom_mother_first': 'Maria Santos',
            'groom_mother_citizenship': 'Filipino',
            'bride_name': 'Jane Marie Garcia',
            'bride_dob': 'August 11, 1999',
            'bride_age': '26',
            'bride_place_of_birth': 'Capas, Tarlac',
            'bride_sex': 'FEMALE',
            'bride_citizenship': 'Filipino',
            'bride_civil_status': 'Single',
            'bride_residence': 'Capas, Tarlac',
            'bride_religion': 'Catholic',
            'bride_father_first': 'Ramon Garcia',
            'bride_father_citizenship': 'Filipino',
            'bride_mother_first': 'Luisa Mendoza',
            'bride_mother_citizenship': 'Filipino',
        }

    confidence = {k: 0.95 for k in fields}
    form_class = form_hint if form_hint in ('1A', '2A', '3A', '90') else '1A'
    return fields, confidence, form_class


# ═════════════════════════════════════════════════════════════
#  HTML PREVIEW
# ═════════════════════════════════════════════════════════════
def _build_preview_html(form_class: str, fields: dict) -> str:
    def row(label, value):
        return (
            f'<tr><td class="lbl">{label}</td>'
            f'<td class="val">{value or ""}</td></tr>'
        )

    rows = ""
    title = f"Form {form_class}"

    if form_class == '1A':
        child = " ".join(filter(None, [
            fields.get('child_first', ''),
            fields.get('child_middle', ''),
            fields.get('child_last', ''),
        ])).strip()
        rows = (
            row('Registry No.', fields.get('registry_no', '')) +
            row('City/Municipality', fields.get('city_municipality', '')) +
            row('Province', fields.get('province', '')) +
            row('Date Submitted', fields.get('date_submitted', '')) +
            '<tr><td colspan="2">CHILD</td></tr>' +
            row('Name', child) +
            row('Sex', fields.get('sex', '')) +
            row('Date of Birth', " ".join(filter(None, [
                fields.get('dob_month', ''),
                fields.get('dob_day', ''),
                fields.get('dob_year', ''),
            ])).strip()) +
            row('Place of Birth', fields.get('pob_city', '')) +
            '<tr><td colspan="2">MOTHER</td></tr>' +
            row('Name', fields.get('mother_first', '')) +
            row('Citizenship', fields.get('mother_citizenship', '')) +
            '<tr><td colspan="2">FATHER</td></tr>' +
            row('Name', fields.get('father_first', '')) +
            row('Citizenship', fields.get('father_citizenship', ''))
        )
        title = child or 'Form 1A — Live Birth'

    elif form_class == '2A':
        deceased = " ".join(filter(None, [
            fields.get('deceased_first', ''),
            fields.get('deceased_middle', ''),
            fields.get('deceased_last', ''),
        ])).strip()
        rows = (
            row('Registry No.', fields.get('registry_no', '')) +
            row('City/Municipality', fields.get('city_municipality', '')) +
            row('Province', fields.get('province', '')) +
            row('Date Submitted', fields.get('date_submitted', '')) +
            row('Name of Deceased', deceased) +
            row('Sex', fields.get('sex', '')) +
            row('Age', fields.get('age_years', '')) +
            row('Civil Status', fields.get('civil_status', '')) +
            row('Citizenship', fields.get('citizenship', '')) +
            row('Date of Death', fields.get('dod_full', '')) +
            row('Place of Death', fields.get('pod_hospital', '')) +
            row('Cause of Death', fields.get('cause_immediate', ''))
        )
        title = deceased or 'Form 2A — Death Certificate'

    elif form_class == '3A':
        husband = " ".join(filter(None, [
            fields.get('husband_first', ''),
            fields.get('husband_middle', ''),
            fields.get('husband_last', ''),
        ])).strip()
        wife = " ".join(filter(None, [
            fields.get('wife_first', ''),
            fields.get('wife_middle', ''),
            fields.get('wife_last', ''),
        ])).strip()
        rows = (
            row('Registry No.', fields.get('registry_no', '')) +
            row('City/Municipality', fields.get('city_municipality', '')) +
            row('Province', fields.get('province', '')) +
            row('Date Submitted', fields.get('date_submitted', '')) +
            '<tr><td colspan="2">HUSBAND</td></tr>' +
            row('Name', husband) +
            row('Age', fields.get('husband_age', '')) +
            row('Citizenship', fields.get('husband_citizenship', '')) +
            row('Mother', fields.get('husband_mother_first', '')) +
            row('Father', fields.get('husband_father_first', '')) +
            '<tr><td colspan="2">WIFE</td></tr>' +
            row('Name', wife) +
            row('Age', fields.get('wife_age', '')) +
            row('Citizenship', fields.get('wife_citizenship', '')) +
            row('Mother', fields.get('wife_mother_first', '')) +
            row('Father', fields.get('wife_father_first', '')) +
            '<tr><td colspan="2">MARRIAGE</td></tr>' +
            row('Venue', fields.get('marriage_venue', '')) +
            row('City', fields.get('marriage_city', '')) +
            row('Date', fields.get('marriage_month', ''))
        )
        title = f'Form 3A — {husband} & {wife}' if (husband or wife) else 'Form 3A — Marriage Certificate'

    else:
        g = fields.get('groom_name', '')
        b = fields.get('bride_name', '')
        dom = " ".join(filter(None, [
            fields.get('marriage_month', ''),
            fields.get('marriage_day', ''),
            fields.get('marriage_year', ''),
        ])).strip()
        pom = " ".join(filter(None, [
            fields.get('marriage_venue', ''),
            fields.get('marriage_city', ''),
        ])).strip()

        rows = (
            row('Registry No.', fields.get('registry_no', '')) +
            row('City/Municipality', fields.get('city_municipality', '')) +
            row('Province', fields.get('province', '')) +
            row('License No.', fields.get('license_no', '')) +
            row('Date Issuance', fields.get('date_issuance', '')) +
            '<tr><td colspan="2" style="padding:8px 0;font-weight:bold;background:#f9f9f9;text-align:center;">GROOM</td></tr>' +
            row('Name', g) +
            row('Date of Birth', fields.get('groom_dob', '')) +
            row('Age', fields.get('groom_age', '')) +
            row('Place of Birth', fields.get('groom_place_of_birth', '')) +
            row('Sex', fields.get('groom_sex', '')) +
            row('Citizenship', fields.get('groom_citizenship', '')) +
            row('Civil Status', fields.get('groom_civil_status', '')) +
            row('Residence', fields.get('groom_residence', '')) +
            row('Religion', fields.get('groom_religion', '')) +
            row('Father', fields.get('groom_father_first', '')) +
            row('Father Citizenship', fields.get('groom_father_citizenship', '')) +
            row('Mother', fields.get('groom_mother_first', '')) +
            row('Mother Citizenship', fields.get('groom_mother_citizenship', '')) +
            '<tr><td colspan="2" style="padding:8px 0;font-weight:bold;background:#f9f9f9;text-align:center;">BRIDE</td></tr>' +
            row('Name', b) +
            row('Date of Birth', fields.get('bride_dob', '')) +
            row('Age', fields.get('bride_age', '')) +
            row('Place of Birth', fields.get('bride_place_of_birth', '')) +
            row('Sex', fields.get('bride_sex', '')) +
            row('Citizenship', fields.get('bride_citizenship', '')) +
            row('Civil Status', fields.get('bride_civil_status', '')) +
            row('Residence', fields.get('bride_residence', '')) +
            row('Religion', fields.get('bride_religion', '')) +
            row('Father', fields.get('bride_father_first', '')) +
            row('Father Citizenship', fields.get('bride_father_citizenship', '')) +
            row('Mother', fields.get('bride_mother_first', '')) +
            row('Mother Citizenship', fields.get('bride_mother_citizenship', '')) +
            '<tr><td colspan="2" style="padding:8px 0;font-weight:bold;background:#f9f9f9;text-align:center;">MARRIAGE</td></tr>' +
            row('Date of Marriage', dom) +
            row('Place of Marriage', pom)
        )
        title = f'Form 90 — {g} & {b}' if (g or b) else 'Form 90 — Marriage License'

    mode = 'REAL PIPELINE' if (USE_REAL_PIPELINE and _pipeline) else 'FAKE DATA (dev mode)'

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{title}</title>
<style>
body{{font-family:Arial,sans-serif;font-size:13px;padding:40px 50px;color:#111;}}
h2{{font-size:15px;border-bottom:2px solid #333;padding-bottom:8px;margin-bottom:16px;}}
.mode{{font-size:11px;color:#888;margin-bottom:12px;}}
table{{width:100%;border-collapse:collapse;}}
td{{padding:6px 8px;border-bottom:1px dotted #ccc;vertical-align:top;}}
td.lbl{{width:220px;color:#555;}}
td.val{{font-weight:bold;background:#fffde7;border-bottom:1px solid #f0d000;}}
tr td[colspan]{{background:#f5f5f5;font-weight:bold;text-align:center;color:#333;border-bottom:2px solid #ddd;}}
</style></head><body>
<h2>LCR Form No. {form_class} — {fields.get('city_municipality', '')}</h2>
<div class="mode">Mode: {mode}</div>
<table>{rows}</table>
</body></html>"""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)