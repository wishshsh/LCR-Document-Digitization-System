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
import os, sys, json, traceback
from datetime import datetime

# ── sys.path setup ────────────────────────────────────────────
# _BASE = python/ folder (where app.py lives)
# Keep _BASE so "from spacyNER.X" / "from MNB.X" package imports work
# Also add subfolders so direct imports work (field_extractor, etc.)
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

# ── CONFIGURATION — edit these two lines ─────────────────────
USE_REAL_PIPELINE = True   # ← set True when models are ready
PIPELINE_REPO_PATH = r"C:\xampp\htdocs\python"
# ─────────────────────────────────────────────────────────────

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'temp')

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
    except Exception as e:
        _pipeline_error = traceback.format_exc()
        print(f"[app.py] ❌ Pipeline failed to load:\n{_pipeline_error}")
        print("[app.py] ⚠️  Falling back to fake data")


# ── /process endpoint ─────────────────────────────────────────
@app.route('/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    file      = request.files['file']
    form_hint = request.form.get('form_hint', '1A')

    # Map form_hint (1A/2A/3A/90) → pipeline form_type (birth/death/marriage)
    hint_to_type = {'1A': 'birth', '2A': 'death', '3A': 'marriage', '90': 'marriage'}
    form_type = hint_to_type.get(form_hint, 'birth')

    # ── Save uploaded file temporarily ───────────────────────
    os.makedirs(TEMP_DIR, exist_ok=True)
    timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext        = os.path.splitext(file.filename)[1] or '.pdf'
    saved_path = os.path.join(TEMP_DIR, f'upload_{timestamp}{ext}')
    file.save(saved_path)

    # ── Run pipeline or fake data ─────────────────────────────
    try:
        if USE_REAL_PIPELINE and _pipeline is not None:
            fields, confidence, form_class = _run_real_pipeline(
                saved_path, form_hint, form_type
            )
        else:
            fields, confidence, form_class = _run_fake_pipeline(form_hint)
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[app.py] ❌ Processing error:\n{tb}")
        return jsonify({
            'status':  'error',
            'message': str(e),
            'trace':   tb
        }), 500
    finally:
        # Clean up temp upload
        try: os.remove(saved_path)
        except: pass

    # ── Save preview HTML ─────────────────────────────────────
    preview_file = f'form_{form_class}_{timestamp}.html'
    preview_path = os.path.join(TEMP_DIR, preview_file)
    with open(preview_path, 'w', encoding='utf-8') as fh:
        fh.write(_build_preview_html(form_class, fields))

    return jsonify({
        'status':      'success',
        'form_class':  form_class,
        'raw_text':    f'Processed via {"pipeline" if USE_REAL_PIPELINE and _pipeline else "fake data"} — Form {form_class}',
        'fields':      fields,
        'confidence':  confidence,
        'saved_file':  preview_file,
        'preview_url': f'/uploads/temp/{preview_file}',
    })


# ── /status endpoint — check pipeline health ─────────────────
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'mode':           'real_pipeline' if (USE_REAL_PIPELINE and _pipeline) else 'fake_data',
        'pipeline_ready': _pipeline is not None,
        'pipeline_error': _pipeline_error,
        'repo_path':      PIPELINE_REPO_PATH if USE_REAL_PIPELINE else None,
    })


# ── /debug endpoint — test pipeline with a dummy call ────────
@app.route('/debug', methods=['GET'])
def debug():
    """Test the pipeline import and show full traceback if it fails."""
    try:
        import pipeline as _pl_module
        return jsonify({'import': 'ok', 'sys_path': sys.path[:6]})
    except Exception:
        return jsonify({'import': 'FAILED', 'trace': traceback.format_exc(), 'sys_path': sys.path[:6]}), 500


# ═════════════════════════════════════════════════════════════
#  REAL PIPELINE — calls pipeline.py
# ═════════════════════════════════════════════════════════════
def _run_real_pipeline(file_path, form_hint, form_type):
    """
    Call CivilRegistryPipeline.process_pdf() and map the result
    to the thesis DB field names.

    NOTE: Once you know what Form.to_dict() actually returns,
    update the _map_pipeline_output() function below.
    """
    if form_hint == '90':
        # Form 90 needs two PDFs — single upload not supported yet
        # TODO: update process_upload.php to accept two files
        raise NotImplementedError(
            "Form 90 requires two PDFs (groom + bride). "
            "Single-file upload not yet supported for Form 90."
        )

    # Call the real pipeline
    raw_result = _pipeline.process_pdf(file_path, form_type=form_type)

    # Map pipeline output → thesis DB field names
    fields, confidence = _map_pipeline_output(raw_result, form_hint)
    form_class = form_hint  # MNB already determined this inside pipeline

    return fields, confidence, form_class


def _map_pipeline_output(raw: dict, form_hint: str):
    """
    Map Form.to_dict() keys → thesis DB field names.

    ⚠️  THIS FUNCTION NEEDS TO BE UPDATED once you test
        what pipeline.process_pdf() actually returns.

    Steps to update:
      1. Run pipeline manually:
           python pipeline.py --pdf test.pdf --form birth
      2. Note the printed field names
      3. Update the mapping dicts below to match
    """

    # ── Confidence — pipeline may or may not return scores ───
    # If pipeline returns confidence per field, map them here too.
    # For now default all to 0.90.
    confidence = {k: 0.90 for k in raw.keys()}

    # ── BIRTH (Form 1A) — update keys once pipeline is tested ─
    if form_hint == '1A':
        fields = {
            # Header
            'registry_no':               raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality':         raw.get('city_municipality') or raw.get('city', ''),
            'province':                  raw.get('province', ''),
            'date_issuance':             raw.get('date_issuance') or raw.get('date', ''),
            # Child
            'child_first':               raw.get('child_first') or raw.get('name_of_child_first', ''),
            'child_middle':              raw.get('child_middle') or raw.get('name_of_child_middle', ''),
            'child_last':                raw.get('child_last') or raw.get('name_of_child_last', ''),
            'sex':                       raw.get('sex', ''),
            'dob_day':                   raw.get('dob_day') or raw.get('date_of_birth_day', ''),
            'dob_month':                 raw.get('dob_month') or raw.get('date_of_birth_month', ''),
            'dob_year':                  raw.get('dob_year') or raw.get('date_of_birth_year', ''),
            'pob_hospital':              raw.get('pob_hospital') or raw.get('place_of_birth_hospital', ''),
            'pob_city':                  raw.get('pob_city') or raw.get('place_of_birth_city', ''),
            'pob_province':              raw.get('pob_province') or raw.get('place_of_birth_province', ''),
            # Mother
            'mother_first':              raw.get('mother_first') or raw.get('mother_name_first', ''),
            'mother_middle':             raw.get('mother_middle') or raw.get('mother_name_middle', ''),
            'mother_last':               raw.get('mother_last') or raw.get('mother_name_last', ''),
            'mother_citizenship':        raw.get('mother_citizenship') or raw.get('mother_nationality', ''),
            'mother_age':                raw.get('mother_age', ''),
            # Father
            'father_first':              raw.get('father_first') or raw.get('father_name_first', ''),
            'father_middle':             raw.get('father_middle') or raw.get('father_name_middle', ''),
            'father_last':               raw.get('father_last') or raw.get('father_name_last', ''),
            'father_citizenship':        raw.get('father_citizenship') or raw.get('father_nationality', ''),
            # Parents marriage
            'parents_marriage_day':      raw.get('parents_marriage_day', ''),
            'parents_marriage_month':    raw.get('parents_marriage_month', ''),
            'parents_marriage_year':     raw.get('parents_marriage_year', ''),
            'parents_marriage_city':     raw.get('parents_marriage_city', ''),
            'parents_marriage_province': raw.get('parents_marriage_province', ''),
            # Registration
            'date_submitted':            raw.get('date_submitted') or raw.get('date_of_registration', ''),
            'prepared_by':               raw.get('prepared_by', ''),
        }

    # ── DEATH (Form 2A) ───────────────────────────────────────
    elif form_hint == '2A':
        fields = {
            'registry_no':       raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality': raw.get('city_municipality') or raw.get('city', ''),
            'province':          raw.get('province', ''),
            'date_issuance':     raw.get('date_issuance') or raw.get('date', ''),
            'deceased_first':    raw.get('deceased_first') or raw.get('name_of_deceased_first', ''),
            'deceased_middle':   raw.get('deceased_middle') or raw.get('name_of_deceased_middle', ''),
            'deceased_last':     raw.get('deceased_last') or raw.get('name_of_deceased_last', ''),
            'sex':               raw.get('sex', ''),
            'age_years':         raw.get('age_years') or raw.get('age', ''),
            'civil_status':      raw.get('civil_status', ''),
            'citizenship':       raw.get('citizenship') or raw.get('nationality', ''),
            'dod_day':           raw.get('dod_day') or raw.get('date_of_death_day', ''),
            'dod_month':         raw.get('dod_month') or raw.get('date_of_death_month', ''),
            'dod_year':          raw.get('dod_year') or raw.get('date_of_death_year', ''),
            'pod_hospital':      raw.get('pod_hospital') or raw.get('place_of_death_hospital', ''),
            'pod_city':          raw.get('pod_city') or raw.get('place_of_death_city', ''),
            'pod_province':      raw.get('pod_province') or raw.get('place_of_death_province', ''),
            'cause_immediate':   raw.get('cause_immediate') or raw.get('cause_of_death', ''),
            'cause_antecedent':  raw.get('cause_antecedent', ''),
            'cause_underlying':  raw.get('cause_underlying', ''),
            'date_submitted':    raw.get('date_submitted') or raw.get('date_of_registration', ''),
        }

    # ── MARRIAGE CERT (Form 3A) ───────────────────────────────
    else:
        fields = {
            'registry_no':               raw.get('registry_number') or raw.get('registry_no', ''),
            'city_municipality':         raw.get('city_municipality') or raw.get('city', ''),
            'province':                  raw.get('province', ''),
            'date_issuance':             raw.get('date_issuance') or raw.get('date', ''),
            'husband_first':             raw.get('husband_first') or raw.get('husband_name_first', ''),
            'husband_middle':            raw.get('husband_middle') or raw.get('husband_name_middle', ''),
            'husband_last':              raw.get('husband_last') or raw.get('husband_name_last', ''),
            'husband_age':               raw.get('husband_age', ''),
            'husband_citizenship':       raw.get('husband_citizenship') or raw.get('husband_nationality', ''),
            'husband_mother_first':      raw.get('husband_mother_first', ''),
            'husband_mother_last':       raw.get('husband_mother_last', ''),
            'husband_mother_citizenship':raw.get('husband_mother_citizenship', ''),
            'husband_father_first':      raw.get('husband_father_first', ''),
            'husband_father_last':       raw.get('husband_father_last', ''),
            'husband_father_citizenship':raw.get('husband_father_citizenship', ''),
            'wife_first':                raw.get('wife_first') or raw.get('wife_name_first', ''),
            'wife_middle':               raw.get('wife_middle') or raw.get('wife_name_middle', ''),
            'wife_last':                 raw.get('wife_last') or raw.get('wife_name_last', ''),
            'wife_age':                  raw.get('wife_age', ''),
            'wife_citizenship':          raw.get('wife_citizenship') or raw.get('wife_nationality', ''),
            'wife_mother_first':         raw.get('wife_mother_first', ''),
            'wife_mother_last':          raw.get('wife_mother_last', ''),
            'wife_mother_citizenship':   raw.get('wife_mother_citizenship', ''),
            'wife_father_first':         raw.get('wife_father_first', ''),
            'wife_father_last':          raw.get('wife_father_last', ''),
            'wife_father_citizenship':   raw.get('wife_father_citizenship', ''),
            'marriage_day':              raw.get('marriage_day') or raw.get('date_of_marriage_day', ''),
            'marriage_month':            raw.get('marriage_month') or raw.get('date_of_marriage_month', ''),
            'marriage_year':             raw.get('marriage_year') or raw.get('date_of_marriage_year', ''),
            'marriage_venue':            raw.get('marriage_venue', ''),
            'marriage_city':             raw.get('marriage_city', ''),
            'marriage_province':         raw.get('marriage_province', ''),
            'date_submitted':            raw.get('date_submitted') or raw.get('date_of_registration', ''),
        }

    # Add any remaining raw fields not yet mapped (future-proofing)
    for k, v in raw.items():
        if k not in fields and v:
            fields[k] = v

    return fields, confidence


# ═════════════════════════════════════════════════════════════
#  FAKE PIPELINE — returns hardcoded data (for development)
# ═════════════════════════════════════════════════════════════
def _run_fake_pipeline(form_hint):
    """Returns fake data using real thesis DB field names."""

    if form_hint == '1A':
        fields = {
            'registry_no':              '2026-BC-00123',
            'city_municipality':        'Tarlac City',
            'province':                 'Tarlac',
            'date_issuance':            datetime.now().strftime('%B %d, %Y'),
            'child_first':              'Maria Luisa',
            'child_middle':             'Dela Cruz',
            'child_last':               'Santos',
            'sex':                      'Female',
            'dob_day':                  '10',
            'dob_month':                'January',
            'dob_year':                 '2026',
            'pob_city':                 'Tarlac City',
            'pob_province':             'Tarlac',
            'mother_first':             'Rosa',
            'mother_middle':            'Reyes',
            'mother_last':              'Dela Cruz',
            'mother_citizenship':       'Filipino',
            'mother_age':               '28',
            'father_first':             'Juan Pedro',
            'father_middle':            '',
            'father_last':              'Santos',
            'father_citizenship':       'Filipino',
            'parents_marriage_day':     '12',
            'parents_marriage_month':   'June',
            'parents_marriage_year':    '2020',
            'parents_marriage_city':    'Tarlac City',
            'parents_marriage_province':'Tarlac',
            'date_submitted':           'January 15, 2026',
            'processed_by':             'John Doe',
            'verified_position':        'City Civil Registrar',
            'issued_to':                'Rosa Reyes Dela Cruz',
            'amount_paid':              '75.00',
            'or_number':                'OR-2026-00456',
            'date_paid':                datetime.now().strftime('%B %d, %Y'),
        }
        confidence = {k: 0.95 for k in fields}

    elif form_hint == '2A':
        fields = {
            'registry_no':       '2026-DC-00045',
            'city_municipality': 'Tarlac City',
            'province':          'Tarlac',
            'date_issuance':     datetime.now().strftime('%B %d, %Y'),
            'deceased_first':    'Roberto',
            'deceased_middle':   'Cruz',
            'deceased_last':     'Villanueva',
            'sex':               'Male',
            'age_years':         '72',
            'civil_status':      'Married',
            'citizenship':       'Filipino',
            'dod_day':           '28',
            'dod_month':         'January',
            'dod_year':          '2026',
            'pod_hospital':      'Tarlac Provincial Hospital',
            'pod_city':          'Tarlac City',
            'pod_province':      'Tarlac',
            'cause_immediate':   'Cardiopulmonary Arrest',
            'date_submitted':    'February 1, 2026',
            'processed_by':      'John Doe',
            'verified_position': 'City Civil Registrar',
            'issued_to':         'Maria Villanueva',
            'amount_paid':       '75.00',
            'or_number':         'OR-2026-00457',
            'date_paid':         datetime.now().strftime('%B %d, %Y'),
        }
        confidence = {k: 0.95 for k in fields}

    elif form_hint == '3A':
        fields = {
            'registry_no':               '2026-MC-00078',
            'city_municipality':         'Tarlac City',
            'province':                  'Tarlac',
            'date_issuance':             datetime.now().strftime('%B %d, %Y'),
            'husband_first':             'Carlos Miguel',
            'husband_middle':            '',
            'husband_last':              'Bautista',
            'husband_age':               '28',
            'husband_citizenship':       'Filipino',
            'husband_mother_first':      'Lourdes',
            'husband_mother_last':       'Bautista',
            'husband_mother_citizenship':'Filipino',
            'husband_father_first':      'Ramon',
            'husband_father_last':       'Bautista',
            'husband_father_citizenship':'Filipino',
            'wife_first':                'Elena Grace',
            'wife_middle':               '',
            'wife_last':                 'Reyes',
            'wife_age':                  '26',
            'wife_citizenship':          'Filipino',
            'wife_mother_first':         'Susan',
            'wife_mother_last':          'Reyes',
            'wife_mother_citizenship':   'Filipino',
            'wife_father_first':         'Eduardo',
            'wife_father_last':          'Reyes',
            'wife_father_citizenship':   'Filipino',
            'marriage_day':              '14',
            'marriage_month':            'February',
            'marriage_year':             '2026',
            'marriage_venue':            'Saint John Parish',
            'marriage_city':             'Tarlac City',
            'marriage_province':         'Tarlac',
            'date_submitted':            'March 1, 2026',
            'processed_by':              'John Doe',
            'verified_position':         'City Civil Registrar',
            'issued_to':                 'Carlos Miguel Bautista',
            'amount_paid':               '75.00',
            'or_number':                 'OR-2026-00458',
            'date_paid':                 datetime.now().strftime('%B %d, %Y'),
        }
        confidence = {k: 0.95 for k in fields}

    else:  # Form 90
        fields = {
            'registry_no':       '2026-ML-00031',
            'city_municipality': 'Tarlac City',
            'date_issuance':     datetime.now().strftime('%B %d, %Y'),
            'groom_first':       'Paolo Gabriel',
            'groom_last':        'Mendoza',
            'groom_age':         '27',
            'groom_citizenship': 'Filipino',
            'bride_first':       'Kristine Ann',
            'bride_last':        'Santos',
            'bride_age':         '25',
            'bride_citizenship': 'Filipino',
            'marriage_day':      '10',
            'marriage_month':    'April',
            'marriage_year':     '2026',
            'marriage_city':     'Tarlac City',
        }
        confidence = {k: 0.95 for k in fields}

    form_class = form_hint if form_hint in ('1A','2A','3A','90') else '1A'
    return fields, confidence, form_class


# ═════════════════════════════════════════════════════════════
#  Preview HTML builder
# ═════════════════════════════════════════════════════════════
def _build_preview_html(form_class, fields):
    def row(label, value):
        val = value or '_______________'
        return f'<div class="row"><span class="lbl">{label}</span><span class="val">{val}</span></div>'

    if form_class == '1A':
        child  = f"{fields.get('child_first','')} {fields.get('child_middle','')} {fields.get('child_last','')}".strip()
        mother = f"{fields.get('mother_first','')} {fields.get('mother_last','')}".strip()
        father = f"{fields.get('father_first','')} {fields.get('father_last','')}".strip()
        dob    = f"{fields.get('dob_month','')} {fields.get('dob_day','')}, {fields.get('dob_year','')}".strip(', ')
        pob    = f"{fields.get('pob_city','')}, {fields.get('pob_province','')}".strip(', ')
        rows   = row('Registry No', fields.get('registry_no','')) + row('Name of Child', child) + row('Sex', fields.get('sex','')) + row('Date of Birth', dob) + row('Place of Birth', pob) + row('Mother', mother) + row('Father', father)
        title  = f'Form 1A — {child}'
    elif form_class == '2A':
        deceased = f"{fields.get('deceased_first','')} {fields.get('deceased_middle','')} {fields.get('deceased_last','')}".strip()
        dod      = f"{fields.get('dod_month','')} {fields.get('dod_day','')}, {fields.get('dod_year','')}".strip(', ')
        rows     = row('Registry No', fields.get('registry_no','')) + row('Name of Deceased', deceased) + row('Date of Death', dod) + row('Cause', fields.get('cause_immediate',''))
        title    = f'Form 2A — {deceased}'
    else:
        h     = f"{fields.get('husband_first', fields.get('groom_first',''))} {fields.get('husband_last', fields.get('groom_last',''))}".strip()
        w     = f"{fields.get('wife_first', fields.get('bride_first',''))} {fields.get('wife_last', fields.get('bride_last',''))}".strip()
        dom   = f"{fields.get('marriage_month','')} {fields.get('marriage_day','')}, {fields.get('marriage_year','')}".strip(', ')
        rows  = row('Registry No', fields.get('registry_no','')) + row('Husband/Groom', h) + row('Wife/Bride', w) + row('Date of Marriage', dom)
        title = f'Form {form_class} — {h} & {w}'

    mode = 'REAL PIPELINE' if (USE_REAL_PIPELINE and _pipeline) else 'FAKE DATA (dev mode)'
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{title}</title>
<style>
body{{font-family:Arial,sans-serif;font-size:13px;padding:40px 50px;color:#111;}}
h2{{font-size:15px;border-bottom:2px solid #333;padding-bottom:8px;margin-bottom:16px;}}
.mode{{font-size:11px;color:#888;margin-bottom:12px;}}
.row{{display:flex;padding:5px 0;border-bottom:1px dotted #ccc;}}
.lbl{{min-width:220px;color:#555;}}
.val{{font-weight:bold;background:#fffde7;padding:0 6px;border-bottom:1px solid #f0d000;}}
</style></head><body>
<h2>LCR Form No. {form_class} — {fields.get('city_municipality','')}</h2>
<div class="mode">Mode: {mode}</div>
{rows}
</body></html>"""


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)