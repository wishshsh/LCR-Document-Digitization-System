"""
template_matcher.py
================================================
Extracts field values from Philippine civil registry scanned forms.

PIPELINE
--------
1. Pre-flight image quality check (upside-down, skew, blur, aspect, ORB fit)
2. Auto-correct image (rotate 180° if upside-down, de-skew if tilted)
3. Detect form type
4. Align image to reference (perspective + ECC + ORB)
5. Preprocess aligned image
6. Use PaddleOCR ONLY for text-box detection / field localization
7. Batch all field crops → single CRNN+CTC forward pass
8. Smart-merge CRNN and PaddleOCR text using _text_quality_score

NOTES
-----
- PaddleOCR is not the final OCR engine for all fields; CRNN+CTC remains the
  primary text reader.
- PaddleOCR is used for detection/localization and as selective assist text
  for certain fields such as province, registry number, municipality, etc.
- This file is written to be a drop-in replacement for the EasyOCR-based version.
"""

import sys as _sys
import os
import sys
import re as _re

import numpy as np
from PIL import Image

try:
    import cv2 as _cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

# ── Reference images ─────────────────────────────────────────────
_REF_DIR = os.path.join(os.path.dirname(__file__), 'references')
REFERENCE_IMAGES = {
    '102': os.path.join(_REF_DIR, 'reference-102.png'),
    '103': os.path.join(_REF_DIR, 'reference-103.png'),
    '90':  os.path.join(_REF_DIR, 'reference-90.png'),
    '97':  os.path.join(_REF_DIR, 'reference-97.png'),
}

# ── Reference image cache (avoid repeated disk reads) ────────────
_REF_CACHE: dict = {}


def _get_ref_gray(form_type: str):
    """Return cached grayscale reference image for form_type, or None."""
    if form_type not in _REF_CACHE:
        path = REFERENCE_IMAGES.get(form_type)
        if path and os.path.exists(path) and _CV2_OK:
            _REF_CACHE[form_type] = _cv2.imread(path, _cv2.IMREAD_GRAYSCALE)
        else:
            _REF_CACHE[form_type] = None
    return _REF_CACHE[form_type]


# ── CRNN+CTC engine ──────────────────────────────────────────────
_CRNN_DIR = os.path.join(os.path.dirname(__file__), 'CRNN+CTC')
if _CRNN_DIR not in _sys.path:
    _sys.path.insert(0, _CRNN_DIR)

_CRNN_CHECKPOINT = os.path.join(_CRNN_DIR, 'checkpoints', 'best_model_v6.pth')
_crnn_ocr = None
_crnn_decode = None


def _get_crnn():
    global _crnn_ocr, _crnn_decode
    if _crnn_ocr is None:
        try:
            import torch
            from inference import CivilRegistryOCR
            from utils import decode_ctc_predictions as _dcp

            print('[template_matcher] Loading CRNN+CTC model...')
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _crnn_ocr = CivilRegistryOCR(
                checkpoint_path=_CRNN_CHECKPOINT,
                device=device,
                mode='adaptive',
            )
            _crnn_decode = _dcp
            print('[template_matcher] CRNN+CTC ready.')
        except Exception as e:
            print(f'[template_matcher] CRNN+CTC load error: {e}')
    return _crnn_ocr


def _crnn_read(crop_img: Image.Image) -> str:
    """Run CRNN+CTC on a single PIL Image crop and return decoded text."""
    ocr = _get_crnn()
    if ocr is None or _crnn_decode is None:
        return ''
    try:
        import torch

        rgb = np.array(crop_img.convert('RGB'))
        bgr = rgb[:, :, ::-1].copy()
        normalized = ocr.normalizer.normalize(bgr)
        tensor = torch.FloatTensor(
            normalized.astype(np.float32) / 255.0
        ).unsqueeze(0).unsqueeze(0).to(ocr.device)

        with torch.no_grad():
            outputs = ocr.model(tensor)

        decoded = _crnn_decode(outputs.cpu(), ocr.idx_to_char, method='greedy')
        return decoded[0].strip()
    except Exception as e:
        print(f'[template_matcher] CRNN+CTC read error: {e}')
        return ''


def _crnn_read_batch(crops: list) -> list:
    """
    Run CRNN+CTC on a list of PIL Image crops in one forward pass.
    """
    if not crops:
        return []

    ocr = _get_crnn()
    if ocr is None or _crnn_decode is None:
        return [''] * len(crops)

    try:
        import torch

        tensors = []
        for crop in crops:
            rgb = np.array(crop.convert('RGB'))
            bgr = rgb[:, :, ::-1].copy()
            normalized = ocr.normalizer.normalize(bgr)
            t = torch.FloatTensor(
                normalized.astype(np.float32) / 255.0
            ).unsqueeze(0).unsqueeze(0)
            tensors.append(t)

        batch = torch.cat(tensors, dim=0).to(ocr.device)

        with torch.no_grad():
            outputs = ocr.model(batch)

        decoded = _crnn_decode(outputs.cpu(), ocr.idx_to_char, method='greedy')
        return [d.strip() for d in decoded]

    except Exception as e:
        print(f'[template_matcher] CRNN batch error: {e}; falling back to serial')
        return [_crnn_read(c) for c in crops]


# ── PaddleOCR engine (DETECTION + OPTIONAL ASSIST TEXT) ──────────
_paddle_reader = None
_PADDLE_DETECT_SCALE = 0.75


def _get_paddleocr():
    global _paddle_reader
    if _paddle_reader is None:
        try:
            from paddleocr import PaddleOCR
            print('[template_matcher] Loading PaddleOCR...')
            _paddle_reader = PaddleOCR(
                use_angle_cls=True,
                lang='en',
            )
            print('[template_matcher] PaddleOCR ready.')
        except Exception as e:
            print(f'[template_matcher] PaddleOCR unavailable: {e}')
    return _paddle_reader


def _paddle_detect(img: Image.Image, scale: float = _PADDLE_DETECT_SCALE):
    """
    Return PaddleOCR detections from a downscaled image and scale boxes back
    to the original image coordinates.

    Output:
      [
        {
          'box': (x1, y1, x2, y2),
          'text': 'detected text',
          'conf': 0.95,
          'cx': center_x,
          'cy': center_y,
          'poly': [[x, y], ...]
        },
        ...
      ]
    """
    ocr = _get_paddleocr()
    if ocr is None:
        return []

    try:
        orig_w, orig_h = img.size
        small_w = max(1, int(orig_w * scale))
        small_h = max(1, int(orig_h * scale))
        small = img.resize((small_w, small_h), Image.BILINEAR)
        arr = np.array(small.convert('RGB'))

        raw = ocr.ocr(arr, cls=True)
        if not raw:
            return []

        detections = []
        pages = raw if isinstance(raw, list) else [raw]
        for page in pages:
            if not page:
                continue
            for item in page:
                if not item or len(item) < 2:
                    continue
                box, rec = item
                text, conf = rec if isinstance(rec, (list, tuple)) and len(rec) >= 2 else ('', 0.0)
                xs = [p[0] / scale for p in box]
                ys = [p[1] / scale for p in box]
                x1, y1 = int(min(xs)), int(min(ys))
                x2, y2 = int(max(xs)), int(max(ys))
                detections.append({
                    'box': (x1, y1, x2, y2),
                    'text': (text or '').strip(),
                    'conf': float(conf),
                    'cx': (x1 + x2) // 2,
                    'cy': (y1 + y2) // 2,
                    'poly': [[float(px) / scale, float(py) / scale] for px, py in box],
                })

        return detections
    except Exception as e:
        print(f'[template_matcher] PaddleOCR detect error: {e}')
        return []


def _paddle_read(crop_img: Image.Image) -> str:
    """
    Optional helper for debugging only.
    Not used as final OCR in extraction unless selected by smart merge.
    """
    ocr = _get_paddleocr()
    if ocr is None:
        return ''

    try:
        arr = np.array(crop_img.convert('RGB'))
        raw = ocr.ocr(arr, cls=True)
        if not raw:
            return ''

        pieces = []
        pages = raw if isinstance(raw, list) else [raw]
        for page in pages:
            if not page:
                continue
            page_sorted = sorted(
                page,
                key=lambda item: min(pt[0] for pt in item[0]) if item and item[0] else 0
            )
            for item in page_sorted:
                if item and len(item) >= 2 and item[1]:
                    pieces.append((item[1][0] or '').strip())

        return ' '.join([p for p in pieces if p]).strip()
    except Exception as e:
        print(f'[template_matcher] PaddleOCR read error: {e}')
        return ''


# Backward-compatible aliases so old code paths still work.
def _easyocr_detect(img: Image.Image, scale: float = _PADDLE_DETECT_SCALE):
    return _paddle_detect(img, scale=scale)


def _easyocr_read(crop_img: Image.Image) -> str:
    return _paddle_read(crop_img)


# Hint constants
_LINE = 'line'
_BLOCK = 'block'
_WORD = 'word'

# ── Post-processing ───────────────────────────────────────────────
_SEX_KEYWORDS = {
    'female': 'FEMALE', 'fem': 'FEMALE', 'f': 'FEMALE',
    'male':   'MALE',   'm':  'MALE',
}

_NATIONALITY_CANONICAL = {
    'filipino': 'Filipino', 'filipine': 'Filipino', 'filipioo': 'Filipino',
    'filipiao': 'Filipino', 'filipinc': 'Filipino', 'filipin': 'Filipino',
    'filipina': 'Filipino', 'fillipino': 'Filipino', 'fillipine': 'Filipino',
    'philipino': 'Filipino', 'philippino': 'Filipino', 'pilipino': 'Filipino',
    'pilipina': 'Filipino', 'pilipiino': 'Filipino', 'fiipino': 'Filipino',
    'fllipino': 'Filipino', 'fiiipino': 'Filipino', 'filipno': 'Filipino',
    'filipimo': 'Filipino', 'fihpino': 'Filipino',
    'american': 'American', 'americian': 'American', 'amercan': 'American', 'amrican': 'American',
    'chinese': 'Chinese', 'chineze': 'Chinese', 'chines': 'Chinese',
    'japanese': 'Japanese', 'japanase': 'Japanese', 'japanes': 'Japanese',
    'korean': 'Korean', 'koreon': 'Korean',
    'british': 'British', 'britsh': 'British',
    'australian': 'Australian', 'australan': 'Australian',
    'indian': 'Indian', 'indin': 'Indian',
    'spanish': 'Spanish', 'spansh': 'Spanish',
    'indonesian': 'Indonesian', 'malaysian': 'Malaysian', 'thai': 'Thai',
    'vietnamese': 'Vietnamese', 'singaporean': 'Singaporean', 'canadian': 'Canadian',
    'german': 'German', 'french': 'French', 'italian': 'Italian', 'dutch': 'Dutch',
}


def _fix_nationality(text: str) -> str:
    key = _re.sub(r'[^a-z]', '', text.lower())
    if not key:
        return text

    if key in _NATIONALITY_CANONICAL:
        return _NATIONALITY_CANONICAL[key]

    if len(key) >= 5:
        for canon_key, canon_val in _NATIONALITY_CANONICAL.items():
            if canon_key.startswith(key) or key.startswith(canon_key[:max(5, len(key) - 1)]):
                return canon_val

    best_val = None
    best_ratio = 0.0
    for canon_key, canon_val in _NATIONALITY_CANONICAL.items():
        longer = max(len(key), len(canon_key))
        if longer == 0:
            continue
        matches = sum(a == b for a, b in zip(key, canon_key))
        ratio = matches / longer
        if ratio > best_ratio:
            best_ratio = ratio
            best_val = canon_val

    if best_ratio >= 0.78 and best_val is not None:
        return best_val

    return text


_MONTH_CANONICAL = {
    'january': 'January', 'januray': 'January', 'janury': 'January',
    'janaury': 'January', 'janary': 'January', 'januarry': 'January', 'jan': 'January',
    'february': 'February', 'feburary': 'February', 'febuary': 'February',
    'febraury': 'February', 'februray': 'February', 'februay': 'February', 'feb': 'February',
    'march': 'March', 'marct': 'March', 'mauct': 'March', 'mauch': 'March',
    'marh': 'March', 'marc': 'March', 'mach': 'March', 'mrach': 'March', 'mar': 'March',
    'april': 'April', 'apirl': 'April', 'apil': 'April', 'aprl': 'April', 'apri': 'April', 'apr': 'April',
    'may': 'May',
    'june': 'June', 'jun': 'June', 'juen': 'June',
    'july': 'July', 'jully': 'July', 'jul': 'July', 'juy': 'July', 'jly': 'July',
    'august': 'August', 'augst': 'August', 'auguts': 'August', 'agust': 'August', 'aug': 'August',
    'september': 'September', 'septmber': 'September', 'septembar': 'September',
    'sepember': 'September', 'sepetmber': 'September', 'sep': 'September', 'sept': 'September',
    'october': 'October', 'ocober': 'October', 'octber': 'October', 'octobr': 'October', 'oct': 'October',
    'november': 'November', 'novmber': 'November', 'noveber': 'November', 'novembr': 'November', 'nov': 'November',
    'december': 'December', 'decmber': 'December', 'deceber': 'December', 'decembr': 'December', 'dec': 'December',
}

_MONTH_ORDER = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12,
}


def _fix_month_word(word: str) -> str:
    key = _re.sub(r'[^a-z]', '', word.lower())
    if not key:
        return word
    if key in _MONTH_CANONICAL:
        return _MONTH_CANONICAL[key]
    if len(key) >= 3:
        for mkey, mval in _MONTH_CANONICAL.items():
            if mkey.startswith(key) or key.startswith(mkey):
                return mval
    return word


def _fix_year(year_str: str, context_text: str = '') -> str:
    y = _re.sub(r'[^0-9]', '', year_str)
    if not y:
        return year_str

    if len(y) == 4:
        yr = int(y)
        if 1900 <= yr <= 2030:
            return y
        if y.startswith('0'):
            candidate = '2' + y[1:]
            if 1900 <= int(candidate) <= 2030:
                return candidate
        return y

    if len(y) == 3:
        specific = {
            '202': '2022', '201': '2015', '200': '2000',
            '199': '1999', '198': '1985', '197': '1975',
            '196': '1965', '195': '1955',
        }
        if y in specific:
            return specific[y]
        return y + '0'

    if len(y) == 2:
        yr = int(y)
        return str(1900 + yr) if yr >= 40 else str(2000 + yr)

    return y


def _fix_date_string(text: str) -> str:
    text = _re.sub(r'[^\w\s\-/,.]', '', text).strip()
    if not text:
        return text

    if _re.fullmatch(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
        return text
    if _re.fullmatch(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
        parts = _re.split(r'[-/]', text)
        sep = '-' if '-' in text else '/'
        parts[-1] = _fix_year(parts[-1], text)
        return sep.join(parts)

    tokens = _re.split(r'([\s,\-/.]+)', text)
    result = []

    for tok in tokens:
        stripped = tok.strip(' ,.-/')
        if not stripped:
            result.append(tok)
            continue

        if _re.fullmatch(r'\d+', stripped):
            num = int(stripped)
            if 1 <= num <= 31 and len(stripped) <= 2:
                result.append(tok)
            elif len(stripped) in (2, 3, 4):
                fixed = _fix_year(stripped, text)
                result.append(tok.replace(stripped, fixed))
            else:
                result.append(tok)
            continue

        corrected_month = _fix_month_word(stripped)
        if corrected_month != stripped:
            result.append(tok.replace(stripped, corrected_month))
            continue

        result.append(tok)

    return ''.join(result).strip()


_FIELD_TYPE = {
    'sex': 'sex', 'groom_sex': 'sex', 'bride_sex': 'sex',
    'husband_sex': 'sex', 'wife_sex': 'sex',
    'dob_year': 'year',
    'age': 'digits', 'groom_age': 'digits', 'bride_age': 'digits',
    'husband_age': 'digits', 'wife_age': 'digits', 'dob_day': 'digits',
    'registration_date': 'date', 'marriage_date': 'date',
    'date_of_marriage': 'date', 'date_of_death': 'date',
    'date_of_birth': 'date', 'date_issued': 'date',
    'groom_dob': 'date', 'bride_dob': 'date',
    'husband_dob': 'date', 'wife_dob': 'date',
    'registry_no': 'registry', 'marriage_license_no': 'registry',
    'mother_citizenship': 'nationality', 'father_citizenship': 'nationality',
    'citizenship': 'nationality',
    'groom_citizenship': 'nationality', 'bride_citizenship': 'nationality',
    'husband_citizenship': 'nationality', 'wife_citizenship': 'nationality',
    'groom_father_citizenship': 'nationality', 'groom_mother_citizenship': 'nationality',
    'bride_father_citizenship': 'nationality', 'bride_mother_citizenship': 'nationality',
    'husband_father_citizenship': 'nationality', 'husband_mother_citizenship': 'nationality',
    'wife_father_citizenship': 'nationality', 'wife_mother_citizenship': 'nationality',
}


def _postprocess(text: str, field_name: str) -> str:
    text = text.strip()
    if not text:
        return ''

    rule = _FIELD_TYPE.get(field_name)

    if rule == 'sex':
        tl = text.lower()
        for kw in sorted(_SEX_KEYWORDS, key=len, reverse=True):
            if kw in tl:
                return _SEX_KEYWORDS[kw]
        return ''

    if rule == 'nationality':
        parts = text.split()
        whole = _fix_nationality(text)
        if whole.lower() != text.lower():
            return whole
        fixed = [_fix_nationality(p) for p in parts]
        return ' '.join(fixed)

    if rule == 'year':
        m = _re.search(r'(19|20)\d{2}', text)
        if m:
            return m.group(0)
        m3 = _re.search(r'\b(19\d|20\d)\b', text)
        if m3:
            return _fix_year(m3.group(0))
        digits = _re.sub(r'\D', '', text)
        if len(digits) >= 4:
            return digits[:4]
        if len(digits) == 3:
            return _fix_year(digits)
        return ''

    if rule == 'digits':
        d = _re.sub(r'\D', '', text)
        return d if d else ''

    if rule == 'date':
        cleaned = _re.sub(r'[^\w\s\-/,.]', '', text).strip()
        if len(cleaned) < 3:
            return ''
        return _fix_date_string(cleaned)

    if rule == 'registry':
        cleaned = _re.sub(r'[^\w\s\-/]', '', text).strip()
        return cleaned if len(cleaned) >= 2 else ''

    cleaned = _re.sub(r'\s+', ' ', text).strip()

    if len(cleaned) == 1:
        return ''

    if len(cleaned) <= 2 and not _re.search(r'[aeiou0-9]', cleaned.lower()):
        return ''

    return cleaned


def _is_valid_field_value(field_name: str, text: str) -> bool:
    if not text:
        return False

    rule = _FIELD_TYPE.get(field_name)
    if rule in ('digits', 'year', 'date', 'registry', 'sex', 'nationality'):
        return True

    cleaned = text.strip()
    if not _re.search(r'[A-Za-z0-9]', cleaned):
        return False
    if len(cleaned) <= 1:
        return False
    return True


def _text_quality_score(field_name: str, text: str) -> float:
    if not text:
        return -999.0

    score = 0.0
    t = text.strip()

    score += len(t)
    score -= len(_re.findall(r'[^A-Za-z0-9\s\-/,.]', t)) * 2.0
    score += len(_re.findall(r'[A-Za-z0-9]', t)) * 0.5

    rule = _FIELD_TYPE.get(field_name)

    if rule == 'digits':
        if _re.fullmatch(r'\d+', _re.sub(r'\D', '', t)):
            score += 8.0
    elif rule == 'year':
        if _re.search(r'(19|20)\d{2}', t):
            score += 10.0
    elif rule == 'date':
        if _re.search(r'\b\d{1,2}\b', t) or _re.search(
            r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)', t.upper()
        ):
            score += 8.0
        for month in _MONTH_ORDER:
            if month in t:
                score += 5.0
                break
        if _re.search(r'(19|20)\d{2}', t):
            score += 5.0
    elif rule == 'sex':
        tl = t.lower()
        if 'male' in tl or 'female' in tl or tl in ('m', 'f'):
            score += 10.0
    elif rule == 'registry':
        if _re.search(r'[A-Za-z0-9]', t):
            score += 8.0
    elif rule == 'nationality':
        key = _re.sub(r'[^a-z]', '', t.lower())
        if key in _NATIONALITY_CANONICAL:
            score += 12.0
        elif len(key) >= 5 and any(k.startswith(key[:5]) for k in _NATIONALITY_CANONICAL):
            score += 6.0

    return score


def _smart_merge(field_name: str, crnn_text: str, assist_text: str) -> str:
    crnn_post = _postprocess(crnn_text, field_name)
    assist_post = _postprocess(assist_text, field_name)

    crnn_ok = _is_valid_field_value(field_name, crnn_post)
    assist_ok = _is_valid_field_value(field_name, assist_post)

    if crnn_ok and not assist_ok:
        return crnn_post
    if assist_ok and not crnn_ok:
        return assist_post
    if not crnn_ok and not assist_ok:
        return crnn_post or assist_post or ''

    crnn_score = _text_quality_score(field_name, crnn_post)
    assist_score = _text_quality_score(field_name, assist_post)
    return crnn_post if crnn_score >= assist_score else assist_post


TEMPLATES = {
    '102': {
        'province':             (0.169, 0.109, 0.608, 0.134, _LINE),
        'registry_no':          (0.613, 0.119, 0.884, 0.152, _LINE),
        'city_municipality':    (0.220, 0.132, 0.608, 0.153, _LINE),
        'name_first':           (0.132, 0.165, 0.398, 0.185, _LINE),
        'name_middle':          (0.397, 0.165, 0.646, 0.186, _LINE),
        'name_last':            (0.646, 0.165, 0.882, 0.185, _LINE),
        'sex':                  (0.122, 0.195, 0.325, 0.215, _WORD),
        'dob_day':              (0.458, 0.197, 0.565, 0.216, _WORD),
        'dob_month':            (0.564, 0.195, 0.750, 0.216, _LINE),
        'dob_year':             (0.748, 0.196, 0.883, 0.216, _WORD),
        'place_of_birth':       (0.380, 0.225, 0.886, 0.244, _LINE),
        'type_of_birth':        (0.124, 0.268, 0.329, 0.290, _WORD),
        'birth_order':          (0.543, 0.275, 0.746, 0.290, _WORD),
        'weight_at_birth':      (0.752, 0.257, 0.838, 0.289, _WORD),
        'mother_name':          (0.184, 0.302, 0.885, 0.322, _LINE),
        'mother_citizenship':   (0.126, 0.332, 0.503, 0.354, _LINE),
        'mother_religion':      (0.508, 0.335, 0.882, 0.354, _LINE),
        'mother_occupation':    (0.512, 0.364, 0.759, 0.392, _LINE),
        'mother_age_at_birth':  (0.758, 0.373, 0.888, 0.392, _WORD),
        'mother_residence':     (0.139, 0.402, 0.888, 0.426, _LINE),
        'father_name':          (0.129, 0.437, 0.885, 0.458, _LINE),
        'father_citizenship':   (0.124, 0.470, 0.314, 0.497, _LINE),
        'father_religion':      (0.316, 0.470, 0.546, 0.498, _LINE),
        'father_occupation':    (0.546, 0.470, 0.750, 0.496, _LINE),
        'father_age_at_birth':  (0.750, 0.478, 0.887, 0.498, _WORD),
        'father_residence':     (0.139, 0.508, 0.889, 0.531, _LINE),
        'marriage_date':        (0.105, 0.556, 0.397, 0.581, _LINE),
        'marriage_place':       (0.399, 0.557, 0.887, 0.582, _LINE),
        'registration_date':    (0.540, 0.898, 0.880, 0.917, _LINE),
    },
    '103': {
        'province':           (0.164, 0.082, 0.628, 0.102, _LINE),
        'registry_no':        (0.636, 0.093, 0.925, 0.123, _LINE),
        'city_municipality':  (0.219, 0.099, 0.629, 0.122, _LINE),
        'deceased_name':      (0.106, 0.144, 0.721, 0.174, _LINE),
        'sex':                (0.723, 0.140, 0.925, 0.174, _WORD),
        'date_of_death':      (0.094, 0.192, 0.311, 0.220, _LINE),
        'date_of_birth':      (0.315, 0.192, 0.560, 0.218, _LINE),
        'age':                (0.562, 0.199, 0.703, 0.218, _WORD),
        'place_of_death':     (0.092, 0.233, 0.703, 0.258, _LINE),
        'civil_status':       (0.701, 0.236, 0.930, 0.258, _WORD),
        'religion':           (0.092, 0.273, 0.312, 0.298, _LINE),
        'citizenship':        (0.311, 0.272, 0.507, 0.298, _LINE),
        'residence':          (0.507, 0.269, 0.929, 0.297, _LINE),
        'occupation':         (0.090, 0.309, 0.285, 0.336, _LINE),
        'father_name':        (0.284, 0.311, 0.603, 0.334, _LINE),
        'mother_name':        (0.601, 0.309, 0.932, 0.333, _LINE),
        'cause_immediate':    (0.295, 0.373, 0.690, 0.389, _LINE),
        'cause_antecedent':   (0.301, 0.388, 0.697, 0.407, _LINE),
        'cause_underlying':   (0.301, 0.406, 0.685, 0.425, _LINE),
        'registration_date':  (0.559, 0.955, 0.922, 0.974, _LINE),
    },
    '90': {
        'province':                  (0.199, 0.094, 0.637, 0.116, _LINE),
        'registry_no':               (0.645, 0.108, 0.909, 0.133, _LINE),
        'city_municipality':         (0.248, 0.114, 0.634, 0.133, _LINE),
        'marriage_license_no':       (0.666, 0.133, 0.916, 0.151, _LINE),
        'date_issued':               (0.766, 0.148, 0.916, 0.166, _LINE),
        'groom_name_first':          (0.170, 0.292, 0.467, 0.311, _LINE),
        'groom_name_middle':         (0.172, 0.307, 0.471, 0.323, _LINE),
        'groom_name_last':           (0.172, 0.323, 0.471, 0.338, _LINE),
        'bride_name_first':          (0.617, 0.292, 0.918, 0.307, _LINE),
        'bride_name_middle':         (0.621, 0.308, 0.917, 0.324, _LINE),
        'bride_name_last':           (0.615, 0.323, 0.915, 0.338, _LINE),
        'groom_dob':                 (0.133, 0.348, 0.396, 0.370, _LINE),
        'groom_age':                 (0.396, 0.347, 0.473, 0.368, _WORD),
        'bride_dob':                 (0.574, 0.349, 0.840, 0.369, _LINE),
        'bride_age':                 (0.842, 0.348, 0.921, 0.370, _WORD),
        'groom_place_of_birth':      (0.136, 0.380, 0.480, 0.402, _LINE),
        'bride_place_of_birth':      (0.577, 0.379, 0.923, 0.402, _LINE),
        'groom_sex':                 (0.133, 0.408, 0.267, 0.426, _WORD),
        'groom_citizenship':         (0.265, 0.409, 0.476, 0.428, _LINE),
        'bride_sex':                 (0.581, 0.408, 0.711, 0.429, _WORD),
        'bride_citizenship':         (0.708, 0.410, 0.921, 0.430, _LINE),
        'groom_residence':           (0.133, 0.437, 0.479, 0.463, _LINE),
        'bride_residence':           (0.579, 0.439, 0.932, 0.466, _LINE),
        'groom_religion':            (0.129, 0.465, 0.480, 0.494, _LINE),
        'bride_religion':            (0.580, 0.464, 0.927, 0.490, _LINE),
        'groom_civil_status':        (0.128, 0.493, 0.480, 0.518, _WORD),
        'bride_civil_status':        (0.580, 0.493, 0.925, 0.517, _WORD),
        'groom_father_name':         (0.132, 0.648, 0.477, 0.670, _LINE),
        'groom_father_citizenship':  (0.128, 0.668, 0.475, 0.691, _LINE),
        'bride_father_name':         (0.575, 0.649, 0.925, 0.670, _LINE),
        'bride_father_citizenship':  (0.575, 0.671, 0.925, 0.693, _LINE),
        'groom_mother_name':         (0.125, 0.740, 0.476, 0.762, _LINE),
        'groom_mother_citizenship':  (0.122, 0.762, 0.477, 0.780, _LINE),
        'bride_mother_name':         (0.575, 0.739, 0.923, 0.762, _LINE),
        'bride_mother_citizenship':  (0.572, 0.760, 0.922, 0.780, _LINE),
    },
    '97': {
        'province':                    (0.186, 0.092, 0.603, 0.113, _LINE),
        'registry_no':                 (0.743, 0.094, 0.941, 0.129, _LINE),
        'city_municipality':           (0.184, 0.112, 0.603, 0.132, _LINE),
        'husband_name_first':          (0.244, 0.154, 0.553, 0.175, _LINE),
        'husband_name_middle':         (0.245, 0.175, 0.549, 0.196, _LINE),
        'husband_name_last':           (0.244, 0.198, 0.553, 0.215, _LINE),
        'wife_name_first':             (0.631, 0.154, 0.940, 0.176, _LINE),
        'wife_name_middle':            (0.630, 0.174, 0.941, 0.195, _LINE),
        'wife_name_last':              (0.633, 0.197, 0.942, 0.216, _LINE),
        'husband_dob':                 (0.191, 0.228, 0.475, 0.249, _LINE),
        'husband_age':                 (0.480, 0.230, 0.543, 0.248, _WORD),
        'wife_dob':                    (0.579, 0.226, 0.862, 0.248, _LINE),
        'wife_age':                    (0.863, 0.228, 0.937, 0.248, _WORD),
        'husband_place_of_birth':      (0.169, 0.259, 0.554, 0.279, _LINE),
        'wife_place_of_birth':         (0.557, 0.258, 0.953, 0.280, _LINE),
        'husband_sex':                 (0.211, 0.282, 0.309, 0.309, _WORD),
        'wife_sex':                    (0.597, 0.281, 0.701, 0.310, _WORD),
        'husband_citizenship':         (0.309, 0.290, 0.553, 0.310, _LINE),
        'wife_citizenship':            (0.698, 0.289, 0.939, 0.310, _LINE),
        'husband_residence':           (0.177, 0.324, 0.550, 0.361, _LINE),
        'wife_residence':              (0.566, 0.323, 0.942, 0.362, _LINE),
        'husband_religion':            (0.177, 0.363, 0.550, 0.391, _LINE),
        'wife_religion':               (0.563, 0.363, 0.943, 0.387, _LINE),
        'husband_civil_status':        (0.171, 0.392, 0.554, 0.416, _WORD),
        'wife_civil_status':           (0.570, 0.395, 0.955, 0.415, _WORD),
        'husband_father_name':         (0.181, 0.427, 0.551, 0.448, _LINE),
        'wife_father_name':            (0.561, 0.425, 0.955, 0.446, _LINE),
        'husband_father_citizenship':  (0.175, 0.449, 0.551, 0.466, _LINE),
        'wife_father_citizenship':     (0.561, 0.447, 0.943, 0.467, _LINE),
        'husband_mother_name':         (0.181, 0.476, 0.557, 0.496, _LINE),
        'wife_mother_name':            (0.564, 0.477, 0.955, 0.499, _LINE),
        'husband_mother_citizenship':  (0.184, 0.500, 0.550, 0.518, _LINE),
        'wife_mother_citizenship':     (0.561, 0.499, 0.939, 0.518, _LINE),
        'place_of_marriage':           (0.179, 0.640, 0.941, 0.665, _LINE),
        'date_of_marriage':            (0.182, 0.674, 0.556, 0.696, _LINE),
        'time_of_marriage':            (0.734, 0.674, 0.889, 0.696, _LINE),
        'registration_date':           (0.655, 0.749, 0.935, 0.769, _LINE),
    },
}

USE_SELECTIVE_PADDLE_ASSIST = True
PADDLE_ASSIST_FIELDS = {
    'province',
    'registry_no',
    'city_municipality',
    'date_issued',
    'registration_date',
    'marriage_license_no',
}


def warmup():
    print('[template_matcher] Warming up models and caches...')
    _get_crnn()
    _get_paddleocr()
    for ft in REFERENCE_IMAGES:
        img = _get_ref_gray(ft)
        status = 'OK' if img is not None else 'NOT FOUND'
        print(f'[template_matcher] Reference {ft}: {status}')
    print('[template_matcher] Warmup complete.')


def _order_corners(pts: np.ndarray) -> np.ndarray:
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).flatten()
    return np.array([
        pts[np.argmin(s)],
        pts[np.argmin(d)],
        pts[np.argmax(s)],
        pts[np.argmax(d)],
    ], dtype=np.float32)


def _correct_perspective(scan_rgb: np.ndarray, ref_w: int, ref_h: int) -> np.ndarray:
    if not _CV2_OK:
        return scan_rgb

    gray = _cv2.cvtColor(scan_rgb, _cv2.COLOR_RGB2GRAY)
    kernel = _cv2.getStructuringElement(_cv2.MORPH_RECT, (5, 5))
    blur = _cv2.GaussianBlur(gray, (7, 7), 0)
    _, thresh = _cv2.threshold(blur, 0, 255, _cv2.THRESH_BINARY + _cv2.THRESH_OTSU)
    dilated = _cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = _cv2.findContours(dilated, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return scan_rgb

    c = max(contours, key=_cv2.contourArea)
    area = _cv2.contourArea(c)
    if area < 0.30 * gray.shape[0] * gray.shape[1]:
        print('[align] perspective: contour too small, skipping')
        return scan_rgb

    peri = _cv2.arcLength(c, True)
    approx = _cv2.approxPolyDP(c, 0.02 * peri, True)
    if len(approx) != 4:
        print(f'[align] perspective: {len(approx)} corners (need 4), skipping')
        return scan_rgb

    src = _order_corners(approx.reshape(4, 2).astype(np.float32))
    dst = np.array([
        [0, 0], [ref_w - 1, 0],
        [ref_w - 1, ref_h - 1], [0, ref_h - 1],
    ], dtype=np.float32)

    M = _cv2.getPerspectiveTransform(src, dst)
    warped = _cv2.warpPerspective(
        scan_rgb, M, (ref_w, ref_h),
        flags=_cv2.INTER_LINEAR, borderMode=_cv2.BORDER_REPLICATE,
    )
    print('[align] perspective correction applied')
    return warped


def _ecc_align(scan_gray: np.ndarray, ref_gray: np.ndarray, scan_rgb: np.ndarray):
    try:
        h, w = ref_gray.shape
        scale = min(1.0, 500.0 / max(h, w))
        sh, sw = max(1, int(h * scale)), max(1, int(w * scale))

        ref_s = _cv2.resize(ref_gray, (sw, sh))
        scn_s = _cv2.resize(_cv2.resize(scan_gray, (w, h)), (sw, sh))

        warp = np.eye(2, 3, dtype=np.float32)
        criteria = (_cv2.TERM_CRITERIA_EPS | _cv2.TERM_CRITERIA_COUNT, 50, 1e-3)
        cc, warp = _cv2.findTransformECC(ref_s, scn_s, warp, _cv2.MOTION_AFFINE, criteria)

        if cc < 0.3:
            print(f'[align] ECC low confidence (cc={cc:.4f}), skipping')
            return None

        angle = np.degrees(np.arctan2(warp[1, 0], warp[0, 0]))
        if abs(angle) > 1.0:
            clamped = np.radians(np.clip(angle, -1.0, 1.0))
            warp[0, 0] = np.cos(clamped)
            warp[0, 1] = -np.sin(clamped)
            warp[1, 0] = np.sin(clamped)
            warp[1, 1] = np.cos(clamped)

        warp[0, 2] /= scale
        warp[1, 2] /= scale

        scan_full = _cv2.resize(scan_rgb, (w, h))
        aligned = _cv2.warpAffine(
            scan_full, warp, (w, h),
            flags=_cv2.INTER_LINEAR, borderMode=_cv2.BORDER_REPLICATE,
        )
        print(f'[align] ECC applied (cc={cc:.4f} angle={angle:.2f}°)')
        return aligned
    except Exception as e:
        print(f'[align] ECC failed: {e}')
        return None


def _orb_align(scan_gray: np.ndarray, ref_gray: np.ndarray, scan_rgb: np.ndarray):
    h, w = scan_gray.shape
    ref_resized = _cv2.resize(ref_gray, (w, h))

    orb = _cv2.ORB_create(nfeatures=5000)
    kp1, des1 = orb.detectAndCompute(scan_gray, None)
    kp2, des2 = orb.detectAndCompute(ref_resized, None)

    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return None, 0

    matcher = _cv2.BFMatcher(_cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(matcher.match(des1, des2), key=lambda m: m.distance)
    good = matches[:max(10, len(matches) // 3)]

    if len(good) < 6:
        return None, 0

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    M, mask = _cv2.estimateAffinePartial2D(
        src_pts, dst_pts, method=_cv2.RANSAC, ransacReprojThreshold=5.0,
    )
    if M is None:
        return None, 0

    inliers = int(mask.sum()) if mask is not None else 0
    aligned = _cv2.warpAffine(
        scan_rgb, M, (w, h),
        flags=_cv2.INTER_LINEAR, borderMode=_cv2.BORDER_REPLICATE,
    )
    print(f'[align] ORB applied ({inliers} inliers)')
    return aligned, inliers


def _orb_inliers(scan_gray: np.ndarray, ref_gray: np.ndarray) -> int:
    orb = _cv2.ORB_create(nfeatures=3000)
    kp1, des1 = orb.detectAndCompute(scan_gray, None)
    kp2, des2 = orb.detectAndCompute(ref_gray, None)

    if des1 is None or des2 is None or len(kp1) < 10 or len(kp2) < 10:
        return 0

    matcher = _cv2.BFMatcher(_cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(matcher.match(des1, des2), key=lambda m: m.distance)
    good = matches[:max(10, len(matches) // 3)]

    if len(good) < 6:
        return 0

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    _, mask = _cv2.findHomography(src_pts, dst_pts, _cv2.RANSAC, 5.0)
    return int(mask.sum()) if mask is not None else 0


def check_image_quality(image_path: str, form_type: str) -> dict:
    if not _CV2_OK:
        return {
            'ok': True,
            'upside_down': False,
            'skew_angle': 0.0,
            'aspect_mismatch': 1.0,
            'orb_fit': 0,
            'orb_fit_normal': 0,
            'orb_fit_180': 0,
            'blur_score': 9999.0,
            'warnings': ['OpenCV not available; skipping quality check'],
        }

    result = {}
    warnings = []

    try:
        img = Image.open(image_path).convert('RGB')
    except Exception as e:
        return {
            'ok': False,
            'upside_down': False,
            'skew_angle': 0.0,
            'aspect_mismatch': 0.0,
            'orb_fit': 0,
            'orb_fit_normal': 0,
            'orb_fit_180': 0,
            'blur_score': 0.0,
            'warnings': [f'Cannot open image: {e}'],
        }

    scan_rgb = np.array(img)
    scan_gray = _cv2.cvtColor(scan_rgb, _cv2.COLOR_RGB2GRAY)
    h, w = scan_gray.shape

    blur_score = float(_cv2.Laplacian(scan_gray, _cv2.CV_64F).var())
    result['blur_score'] = round(blur_score, 1)
    if blur_score < 80:
        warnings.append(
            f'Image appears blurry (Laplacian variance={blur_score:.1f}; threshold 80).'
        )

    edges = _cv2.Canny(scan_gray, 50, 150, apertureSize=3)
    lines = _cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=80,
        minLineLength=60, maxLineGap=15,
    )
    skew_angle = 0.0
    if lines is not None:
        angles = [
            np.degrees(np.arctan2(y2 - y1, x2 - x1))
            for x1, y1, x2, y2 in lines[:, 0]
            if abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) < 45
        ]
        if angles:
            skew_angle = float(np.median(angles))

    result['skew_angle'] = round(skew_angle, 2)
    if abs(skew_angle) > 3.0:
        warnings.append(f'Page is significantly skewed ({skew_angle:.1f}°).')

    upside_down = False
    orb_fit = 0
    inliers_normal = 0
    inliers_180 = 0

    ref_gray = _get_ref_gray(form_type)
    if ref_gray is not None:
        ref_h, ref_w = ref_gray.shape
        scan_rs = _cv2.resize(scan_gray, (ref_w, ref_h))
        scan_180 = _cv2.rotate(scan_rs, _cv2.ROTATE_180)

        inliers_normal = _orb_inliers(scan_rs, ref_gray)
        inliers_180 = _orb_inliers(scan_180, ref_gray)
        orb_fit = inliers_normal

        if inliers_180 > inliers_normal * 1.5 and inliers_180 > 10:
            upside_down = True
            orb_fit = inliers_180
            warnings.append(
                f'Image appears upside down (ORB normal={inliers_normal}, rotated_180={inliers_180}).'
            )

        if orb_fit < 10:
            warnings.append(f'Poor alignment fit for form {form_type} (ORB inliers={orb_fit}).')
        elif orb_fit < 25:
            warnings.append(f'Weak alignment fit for form {form_type} (ORB inliers={orb_fit}).')

        scan_aspect = w / max(h, 1)
        ref_aspect = ref_w / max(ref_h, 1)
        aspect_ratio = scan_aspect / max(ref_aspect, 1e-6)
        result['aspect_mismatch'] = round(aspect_ratio, 3)
    else:
        result['aspect_mismatch'] = 1.0

    result['upside_down'] = upside_down
    result['orb_fit'] = orb_fit
    result['orb_fit_normal'] = inliers_normal
    result['orb_fit_180'] = inliers_180
    result['warnings'] = warnings
    result['ok'] = len(warnings) == 0
    return result


def correct_image(img: Image.Image, quality: dict):
    applied = []

    if not _CV2_OK:
        print('[correct_image] OpenCV not available; skipping corrections.')
        return img, applied

    rgb = np.array(img.convert('RGB'))

    if quality.get('upside_down'):
        rgb = _cv2.rotate(rgb, _cv2.ROTATE_180)
        applied.append('rotated 180° (upside-down correction)')
        print('[correct_image] Applied: 180° rotation')

    skew_angle = quality.get('skew_angle', 0.0)
    if 1.0 < abs(skew_angle) < 15.0:
        correction_angle = -skew_angle
        h, w = rgb.shape[:2]
        center = (w / 2.0, h / 2.0)
        M = _cv2.getRotationMatrix2D(center, correction_angle, 1.0)

        cos_a = abs(M[0, 0])
        sin_a = abs(M[0, 1])
        new_w = int(h * sin_a + w * cos_a)
        new_h = int(h * cos_a + w * sin_a)
        M[0, 2] += (new_w - w) / 2.0
        M[1, 2] += (new_h - h) / 2.0

        rgb = _cv2.warpAffine(
            rgb, M, (new_w, new_h),
            flags=_cv2.INTER_CUBIC,
            borderMode=_cv2.BORDER_REPLICATE,
        )
        applied.append(f'de-skewed {correction_angle:+.2f}°')
        print(f'[correct_image] Applied: de-skew {correction_angle:+.2f}°')

    result_img = Image.fromarray(rgb)
    if img.mode != 'RGB':
        result_img = result_img.convert(img.mode)
    return result_img, applied


def align_to_reference(img: Image.Image, form_type: str):
    if not _CV2_OK:
        return img, 0

    ref_gray = _get_ref_gray(form_type)
    if ref_gray is None:
        return img, 0

    ref_h, ref_w = ref_gray.shape
    scan_rgb = np.array(img.convert('RGB'))

    stage0 = _correct_perspective(scan_rgb, ref_w, ref_h)
    stage0_gray = _cv2.cvtColor(stage0, _cv2.COLOR_RGB2GRAY)

    precheck = _orb_inliers(stage0_gray, ref_gray)
    print(f'[align] ORB pre-check: {precheck} inliers')

    if precheck >= 40:
        orb_aligned, orb_inliers = _orb_align(stage0_gray, ref_gray, stage0)
        if orb_aligned is not None:
            return Image.fromarray(orb_aligned), orb_inliers

    ecc_aligned = _ecc_align(stage0_gray, ref_gray, stage0)
    if ecc_aligned is not None:
        ecc_gray = _cv2.cvtColor(ecc_aligned, _cv2.COLOR_RGB2GRAY)
        orb_aligned, orb_inliers = _orb_align(ecc_gray, ref_gray, ecc_aligned)
        if orb_aligned is not None:
            return Image.fromarray(orb_aligned), orb_inliers
        return Image.fromarray(ecc_aligned), _orb_inliers(ecc_gray, ref_gray)

    orb_aligned, orb_inliers = _orb_align(stage0_gray, ref_gray, stage0)
    if orb_aligned is not None:
        return Image.fromarray(orb_aligned), orb_inliers

    resized = _cv2.resize(stage0, (ref_w, ref_h))
    return Image.fromarray(resized), precheck


def _deskew(gray: np.ndarray) -> np.ndarray:
    if not _CV2_OK:
        return gray

    edges = _cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = _cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=100,
        minLineLength=100, maxLineGap=10,
    )
    if lines is None:
        return gray

    angles = [
        np.degrees(np.arctan2(y2 - y1, x2 - x1))
        for x1, y1, x2, y2 in lines[:, 0]
        if -3 < np.degrees(np.arctan2(y2 - y1, x2 - x1)) < 3
    ]

    if not angles:
        return gray

    angle = float(np.median(angles))
    if abs(angle) < 0.5:
        return gray

    h, w = gray.shape
    M = _cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return _cv2.warpAffine(
        gray, M, (w, h),
        flags=_cv2.INTER_CUBIC, borderMode=_cv2.BORDER_REPLICATE,
    )


def _preprocess(img: Image.Image) -> Image.Image:
    if not _CV2_OK:
        return img.convert('L')
    gray = np.array(img.convert('L'))
    gray = _deskew(gray)
    return Image.fromarray(gray)


def _crop_field(img: Image.Image, x1r, y1r, x2r, y2r) -> Image.Image:
    w, h = img.size
    pad = 4
    x1 = max(0, int(x1r * w) - pad)
    y1 = max(0, int(y1r * h) - pad)
    x2 = min(w, int(x2r * w) + pad)
    y2 = min(h, int(y2r * h) + pad)
    return img.crop((x1, y1, x2, y2))


def _expand_box(box, img_w, img_h, pad_x=10, pad_y=8):
    x1, y1, x2, y2 = box
    return (
        max(0, x1 - pad_x),
        max(0, y1 - pad_y),
        min(img_w, x2 + pad_x),
        min(img_h, y2 + pad_y),
    )


def _crop_from_box(img: Image.Image, box):
    return img.crop(box)


def _norm_text(s: str) -> str:
    return _re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def _find_nearby_detection(field_rect, detections, expected_hint=None):
    fx1, fy1, fx2, fy2 = field_rect
    fcx = (fx1 + fx2) / 2
    fcy = (fy1 + fy2) / 2
    fw = max(1, fx2 - fx1)
    fh = max(1, fy2 - fy1)

    best = None
    best_score = -1e9

    for det in detections:
        x1, y1, x2, y2 = det['box']
        dcx = det['cx']
        dcy = det['cy']
        dw = max(1, x2 - x1)
        dh = max(1, y2 - y1)

        dist = ((dcx - fcx) ** 2 + (dcy - fcy) ** 2) ** 0.5
        overlap_x = max(0, min(fx2, x2) - max(fx1, x1))
        overlap_y = max(0, min(fy2, y2) - max(fy1, y1))
        overlap = overlap_x * overlap_y

        size_penalty = abs(dw - fw) * 0.2 + abs(dh - fh) * 0.2
        score = overlap * 0.02 - dist - size_penalty + det.get('conf', 0.0) * 40.0

        text = (det.get('text') or '').strip()
        if expected_hint == _WORD and len(text.split()) <= 3:
            score += 10
        elif expected_hint == _LINE and 1 <= len(text.split()) <= 12:
            score += 8
        elif expected_hint == _BLOCK and len(text.split()) >= 2:
            score += 6

        if score > best_score:
            best_score = score
            best = det

    return best if best_score > -150 else None


def _get_field_crop_with_paddle(processed_img: Image.Image, field_coords, detections):
    w, h = processed_img.size
    x1r, y1r, x2r, y2r, hint = field_coords

    fx1 = int(x1r * w)
    fy1 = int(y1r * h)
    fx2 = int(x2r * w)
    fy2 = int(y2r * h)
    field_rect = (fx1, fy1, fx2, fy2)

    det = _find_nearby_detection(field_rect, detections, expected_hint=hint)
    if det is not None:
        box = _expand_box(det['box'], w, h, pad_x=10, pad_y=8)
        return _crop_from_box(processed_img, box), 'paddle-detect', det

    return _crop_field(processed_img, x1r, y1r, x2r, y2r), 'absolute', None


def _get_field_crop_with_easyocr(processed_img: Image.Image, field_coords, detections):
    return _get_field_crop_with_paddle(processed_img, field_coords, detections)


def detect_form_type(image_path: str) -> str:
    if _CV2_OK:
        try:
            img = Image.open(image_path).convert('RGB')
            scan_rgb = np.array(img)
            scan_gray = _cv2.cvtColor(scan_rgb, _cv2.COLOR_RGB2GRAY)

            best_type, best_inliers = None, 0
            det_w = 800

            for ft in REFERENCE_IMAGES:
                ref_gray = _get_ref_gray(ft)
                if ref_gray is None:
                    continue

                ref_h, ref_w = ref_gray.shape
                sc = min(1.0, det_w / ref_w)
                dw = max(1, int(ref_w * sc))
                dh = max(1, int(ref_h * sc))
                ref_ds = _cv2.resize(ref_gray, (dw, dh))
                scan_ds = _cv2.resize(_cv2.resize(scan_gray, (ref_w, ref_h)), (dw, dh))

                count = _orb_inliers(scan_ds, ref_ds)
                print(f'[detect] Form {ft}: {count} ORB inliers')

                if count > best_inliers:
                    best_inliers, best_type = count, ft

            if best_type and best_inliers >= 15:
                print(f'[detect] Best: Form {best_type} ({best_inliers} inliers)')
                return best_type

            print(f'[detect] ORB inconclusive ({best_inliers}), trying OCR title')
        except Exception as e:
            print(f'[template_matcher] detect_form_type ORB error: {e}')

    try:
        img_l = Image.open(image_path).convert('L')
        w, h = img_l.size
        title_crop = img_l.crop((0, int(h * 0.04), w, int(h * 0.15)))
        title = _crnn_read(title_crop).upper()

        if title:
            if 'LIVE BIRTH' in title or ('BIRTH' in title and 'DEATH' not in title and 'MARRIAGE' not in title):
                return '102'
            if 'DEATH' in title:
                return '103'
            if 'MARRIAGE' in title and 'LICENSE' in title:
                return '90'
            if 'MARRIAGE' in title:
                return '97'
    except Exception as e:
        print(f'[template_matcher] detect_form_type OCR error: {e}')

    print('[detect] Could not detect form type; defaulting to 102.')
    return '102'


def is_blank_image(img: Image.Image, threshold: float = 0.995) -> bool:
    if not _CV2_OK:
        return False

    gray = np.array(img.convert('L'))
    h, w = gray.shape

    y1 = int(h * 0.20)
    y2 = int(h * 0.80)
    x1 = int(w * 0.20)
    x2 = int(w * 0.80)
    center = gray[y1:y2, x1:x2]

    light_pixels = np.sum(center > 240)
    total_pixels = center.size
    ratio = light_pixels / max(total_pixels, 1)
    variance = float(np.var(center))

    print(f'[template_matcher] Blank check: {ratio:.2%} light pixels, variance={variance:.1f}')
    return ratio >= threshold and variance < 50.0


def extract_fields(image_path: str, form_type: str = None):
    try:
        if not form_type:
            form_type = detect_form_type(image_path)

        template = TEMPLATES.get(form_type)
        if not template:
            return {'status': 'error', 'message': f'No template for form {form_type}.'}

        quality = check_image_quality(image_path, form_type)
        img = Image.open(image_path).convert('RGB')

        if is_blank_image(img):
            return {'status': 'error', 'message': 'Blank or near-blank image detected.'}

        img, corrections = correct_image(img, quality)
        img, orb_fit = align_to_reference(img, form_type)
        processed = _preprocess(img)
        detections = _paddle_detect(processed)

        fields = {}
        debug_methods = {}
        field_names = []
        crops = []
        assist_texts = []

        for field_name, coords in template.items():
            crop, method, det = _get_field_crop_with_paddle(processed, coords, detections)
            field_names.append(field_name)
            crops.append(crop)
            debug_methods[field_name] = method

            assist_text = ''
            if USE_SELECTIVE_PADDLE_ASSIST and field_name in PADDLE_ASSIST_FIELDS:
                if det is not None:
                    assist_text = (det.get('text') or '').strip()
                if not assist_text:
                    assist_text = _paddle_read(crop)
            assist_texts.append(assist_text)

        crnn_texts = _crnn_read_batch(crops)

        for field_name, crnn_text, assist_text in zip(field_names, crnn_texts, assist_texts):
            final_text = _smart_merge(field_name, crnn_text, assist_text)
            if final_text:
                fields[field_name] = final_text

        print(f'[template_matcher] Extracted: {len(fields)}/{len(template)} fields')
        paddle_count = sum(1 for m in debug_methods.values() if m == 'paddle-detect')
        abs_count = sum(1 for m in debug_methods.values() if m == 'absolute')
        print(f'[template_matcher] Crop source: paddle={paddle_count}, absolute={abs_count}, orb_fit={orb_fit}')

        if len(fields) == 0:
            return {'status': 'error', 'message': 'No readable text found.'}

        fields['_quality'] = quality
        fields['_corrections'] = corrections
        return fields
    except Exception as e:
        print(f'[template_matcher] extract_fields error: {e}')
        return {'status': 'error', 'message': str(e)}


def debug_draw_boxes(image_path: str, form_type: str, out_path: str = None) -> str:
    from PIL import ImageDraw, ImageFont

    template = TEMPLATES.get(form_type)
    if not template:
        print(f'No template for {form_type}')
        return None

    quality = check_image_quality(image_path, form_type)
    img = Image.open(image_path).convert('RGB')
    img, _ = correct_image(img, quality)
    img, _ = align_to_reference(img, form_type)

    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    except Exception:
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 11)
        except Exception:
            font = ImageFont.load_default()

    for field_name, coords in template.items():
        x1r, y1r, x2r, y2r, _ = coords
        bx1, by1 = int(x1r * w), int(y1r * h)
        bx2, by2 = int(x2r * w), int(y2r * h)
        draw.rectangle([bx1, by1, bx2, by2], outline='#1a6fd4', width=1)
        draw.text((bx1 + 2, by1 + 2), field_name, fill='#1a6fd4', font=font)

    base, ext = os.path.splitext(image_path)
    out = out_path or f'{base}_debug_{form_type}{ext}'
    img.save(out)
    print(f'[template_matcher] Debug image saved: {out}')
    return out


def debug_draw_paddle_matches(image_path: str, form_type: str, out_path: str = None) -> str:
    from PIL import ImageDraw, ImageFont

    template = TEMPLATES.get(form_type)
    if not template:
        print(f'No template for {form_type}')
        return None

    quality = check_image_quality(image_path, form_type)
    img = Image.open(image_path).convert('RGB')
    img, _ = correct_image(img, quality)
    img, _ = align_to_reference(img, form_type)
    processed = _preprocess(img)
    detections = _paddle_detect(processed)

    canvas = img.copy()
    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    except Exception:
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 11)
        except Exception:
            font = ImageFont.load_default()

    for det in detections:
        x1, y1, x2, y2 = det['box']
        draw.rectangle([x1, y1, x2, y2], outline='red', width=1)

    for field_name, coords in template.items():
        x1r, y1r, x2r, y2r, hint = coords
        fx1 = int(x1r * w)
        fy1 = int(y1r * h)
        fx2 = int(x2r * w)
        fy2 = int(y2r * h)
        draw.rectangle([fx1, fy1, fx2, fy2], outline='blue', width=2)
        draw.text((fx1 + 2, fy1 + 2), field_name, fill='blue', font=font)

        det = _find_nearby_detection((fx1, fy1, fx2, fy2), detections, expected_hint=hint)
        if det is not None:
            dx1, dy1, dx2, dy2 = det['box']
            draw.rectangle([dx1, dy1, dx2, dy2], outline='green', width=2)

    base, ext = os.path.splitext(image_path)
    out = out_path or f'{base}_paddle_debug_{form_type}{ext}'
    canvas.save(out)
    print(f'[template_matcher] Paddle debug image saved: {out}')
    return out


def debug_draw_easyocr_matches(image_path: str, form_type: str, out_path: str = None) -> str:
    # Backward-compatible function name.
    return debug_draw_paddle_matches(image_path, form_type, out_path)


def pdf_to_image(pdf_path: str, page: int = 0) -> str:
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=150)
        out_path = pdf_path.replace('.pdf', f'_page{page}.png')
        pages[page].save(out_path, 'PNG')
        return out_path
    except ImportError:
        print('[template_matcher] pdf2image not installed.')
        return None
    except Exception as e:
        print(f'[template_matcher] PDF conversion failed: {e}')
        return None


if __name__ == '__main__':
    warmup()

    if len(sys.argv) < 2:
        print('Usage:')
        print('  python template_matcher.py <image_path> <form_type> [out_path]')
        print('  python template_matcher.py <image_path> check [form_type]')
        print('  form_type: 102 | 103 | 90 | 97')
        sys.exit(1)

    img_path = sys.argv[1]

    if len(sys.argv) >= 3 and sys.argv[2] == 'check':
        ft = sys.argv[3] if len(sys.argv) > 3 else detect_form_type(img_path)
        q = check_image_quality(img_path, ft)

        print(f'\nQuality report for form {ft}:')
        for k, v in q.items():
            if k != 'warnings':
                print(f'  {k:<22} = {v}')

        if q['warnings']:
            print('\nWarnings:')
            for msg in q['warnings']:
                print(f'  • {msg}')

        img_pil = Image.open(img_path).convert('RGB')
        _, corrections = correct_image(img_pil, q)
        print('\nCorrections that would be applied:')
        if corrections:
            for c in corrections:
                print(f'  ✓ {c}')
        else:
            print('  (none needed)')

        sys.exit(0 if q['ok'] else 1)

    form_type = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else None

    debug_draw_boxes(img_path, form_type, out_path)
    debug_draw_paddle_matches(img_path, form_type)

    result = extract_fields(img_path, form_type)
    meta_keys = {'_quality', '_corrections'}

    data_fields = {k: v for k, v in result.items() if k not in meta_keys}
    print(f'\nExtracted fields ({len(data_fields)}):')
    for k, v in data_fields.items():
        print(f'  {k:<40} = {v}')

    template = TEMPLATES.get(form_type, {})
    missing = [k for k in template if k not in data_fields]
    if missing:
        print(f'\nEmpty fields ({len(missing)}):')
        for k in missing:
            print(f'  {k}')

    corrections = result.get('_corrections', [])
    if corrections:
        print('\nAuto-corrections applied:')
        for c in corrections:
            print(f'  ✓ {c}')

    quality = result.get('_quality', {})
    if quality.get('warnings'):
        print('\nQuality warnings:')
        for w_msg in quality['warnings']:
            print(f'  • {w_msg}')