"""
Inference Script for CRNN+CTC Civil Registry OCR

TWO NORMALIZERS:
  SimpleNormalizer   — for PIL-rendered synthetic images (matches training exactly)
  AdaptiveNormalizer — for physical/scanned images (any zoom, any size)

AUTO-DETECT MODE: automatically decides which pipeline to use based on
text density in the image — zoomed-in images get adaptive treatment,
clean synthetic images get simple treatment.
"""

import torch
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List

from crnn_model import get_crnn_model
from utils import decode_ctc_predictions, extract_form_fields


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _to_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.copy()


def _binarize(gray: np.ndarray) -> np.ndarray:
    """Otsu, falls back to adaptive for uneven backgrounds."""
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    white_ratio = np.mean(otsu == 255)
    if white_ratio < 0.30 or white_ratio > 0.97:
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2)
    return otsu


def _crop_to_text(gray: np.ndarray, pad_ratio=0.15) -> np.ndarray:
    """Crop tightly around dark pixels (the text)."""
    inv = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(inv, 20, 255, cv2.THRESH_BINARY)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return gray
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    pad   = max(4, int((y_max - y_min) * pad_ratio))
    y_min = max(0, y_min - pad)
    x_min = max(0, x_min - pad)
    y_max = min(gray.shape[0] - 1, y_max + pad)
    x_max = min(gray.shape[1] - 1, x_max + pad)
    return gray[y_min:y_max+1, x_min:x_max+1]


def _aspect_resize(gray: np.ndarray, H: int, W: int) -> np.ndarray:
    """Resize preserving aspect ratio, pad with white to fill canvas."""
    h, w = gray.shape
    if h == 0 or w == 0:
        return np.ones((H, W), dtype=np.uint8) * 255
    scale = H / h
    new_w = int(w * scale)
    new_h = H
    if new_w > W:
        scale = W / w
        new_h = int(h * scale)
        new_w = W
    resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    canvas  = np.ones((H, W), dtype=np.uint8) * 255
    y_off   = (H - new_h) // 2
    x_off   = (W - new_w) // 2
    canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
    return canvas


def _detect_mode(gray: np.ndarray) -> str:
    """
    Auto-detect whether image needs adaptive or simple normalization.

    Logic:
      - If >25% of pixels are dark, text is very large/zoomed → adaptive.
      - If image size is far from training size (400x64) → adaptive.
      - Otherwise → simple (matches training pipeline).
    """
    h, w  = gray.shape
    _, bw = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    dark_px = np.mean(bw == 0)

    # Text fills too much of the image → zoomed in (like shane.jpg)
    if dark_px > 0.25:
        return 'adaptive'

    # Image is far from expected training size (allow 50% tolerance)
    if not (256 <= w <= 1024 and 32 <= h <= 128):
        return 'adaptive'

    return 'simple'


def _to_tensor(img: np.ndarray) -> torch.Tensor:
    return torch.FloatTensor(
        img.astype(np.float32) / 255.0
    ).unsqueeze(0).unsqueeze(0)


# ─────────────────────────────────────────────────────────────────────────────
# SIMPLE NORMALIZER  ← for PIL-rendered / training-matched images
# ─────────────────────────────────────────────────────────────────────────────

class SimpleNormalizer:
    """
    Matches fix_data.py training pipeline exactly:
      grayscale → resize → binarize
    Best for test images created by create_test_images.py.
    """
    def __init__(self, H=64, W=512):
        self.H, self.W = H, W

    def normalize(self, img: np.ndarray) -> np.ndarray:
        gray    = _to_gray(img)
        resized = cv2.resize(gray, (self.W, self.H), interpolation=cv2.INTER_LANCZOS4)
        return _binarize(resized)

    def normalize_from_path(self, path: str) -> np.ndarray:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Cannot load: {path}")
        return self.normalize(img)


# ─────────────────────────────────────────────────────────────────────────────
# ADAPTIVE NORMALIZER  ← for real / physical / scanned images
# ─────────────────────────────────────────────────────────────────────────────

class AdaptiveNormalizer:
    """
    For physical documents or images with non-standard zoom/size:
      grayscale → denoise → crop text → aspect-ratio resize → binarize

    Crops to actual text first, so a zoomed-in image like shane.jpg
    gets scaled down to training size instead of being squeezed/stretched.
    """
    def __init__(self, H=64, W=512):
        self.H, self.W = H, W

    def normalize(self, img: np.ndarray) -> np.ndarray:
        gray   = _to_gray(img)
        gray   = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        gray   = _crop_to_text(gray)
        canvas = _aspect_resize(gray, self.H, self.W)
        return _binarize(canvas)

    def normalize_from_path(self, path: str) -> np.ndarray:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Cannot load: {path}")
        return self.normalize(img)


# ─────────────────────────────────────────────────────────────────────────────
# AUTO NORMALIZER  ← detects which pipeline to use per image automatically
# ─────────────────────────────────────────────────────────────────────────────

class AutoNormalizer:
    """
    Automatically picks Simple or Adaptive based on image characteristics.

    Examples:
      demo.jpg  (clean 400x64 PIL)   → Simple   (matches training)
      name1.jpg (clean 400x64 PIL)   → Simple
      shane.jpg (huge zoomed text)   → Adaptive (crop then resize)
      real scan (any size/zoom)      → Adaptive
    """
    def __init__(self, H=64, W=512, verbose=False):
        self.H, self.W = H, W
        self.verbose   = verbose
        self._simple   = SimpleNormalizer(H, W)
        self._adaptive = AdaptiveNormalizer(H, W)

    def normalize(self, img: np.ndarray) -> np.ndarray:
        gray = _to_gray(img)
        mode = _detect_mode(gray)
        if self.verbose:
            print(f"      auto → {mode}")
        return self._simple.normalize(img) if mode == 'simple' \
               else self._adaptive.normalize(img)

    def normalize_from_path(self, path: str) -> np.ndarray:
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Cannot load: {path}")
        gray = _to_gray(img)
        mode = _detect_mode(gray)
        if self.verbose:
            print(f"      [{Path(path).name}] → {mode}")
        return self._simple.normalize(img) if mode == 'simple' \
               else self._adaptive.normalize(img)

    def to_tensor(self, img: np.ndarray) -> torch.Tensor:
        return _to_tensor(img)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN OCR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class CivilRegistryOCR:

    def __init__(self, checkpoint_path, device='cuda', mode='auto', verbose=False):
        """
        Args:
            checkpoint_path : path to best_model.pth
            device          : 'cuda' or 'cpu'
            mode            : 'auto'     → auto-detect per image  (recommended)
                              'simple'   → always use simple pipeline
                              'adaptive' → always use adaptive pipeline
            verbose         : print which mode was chosen per image
        """
        if device == 'cuda' and not torch.cuda.is_available():
            device = 'cpu'

        self.device  = torch.device(device)
        self.verbose = verbose
        print(f"Loading model from {checkpoint_path}...")

        checkpoint = torch.load(checkpoint_path, map_location=self.device,
                                weights_only=False)

        self.char_to_idx = checkpoint['char_to_idx']
        self.idx_to_char = checkpoint['idx_to_char']
        self.config      = checkpoint.get('config', {})

        img_height = self.config.get('img_height', 64)
        img_width  = self.config.get('img_width',  512)

        if mode == 'simple':
            self.normalizer = SimpleNormalizer(img_height, img_width)
        elif mode == 'adaptive':
            self.normalizer = AdaptiveNormalizer(img_height, img_width)
        else:
            self.normalizer = AutoNormalizer(img_height, img_width, verbose=verbose)

        self.model = get_crnn_model(
            model_type=self.config.get('model_type', 'standard'),
            img_height=img_height,
            num_chars=len(self.char_to_idx),
            hidden_size=self.config.get('hidden_size', 256),
            num_lstm_layers=self.config.get('num_lstm_layers', 2)
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model = self.model.to(self.device)
        self.model.eval()

        print(f"Model loaded successfully")
        print(f"  Val CER  : {checkpoint.get('val_cer', 0):.2f}%")
        print(f"  Device   : {self.device}")
        print(f"  Mode     : {mode}  ({img_height}x{img_width})")

    def _preprocess(self, image_path) -> torch.Tensor:
        normalized = self.normalizer.normalize_from_path(str(image_path))
        return _to_tensor(normalized)

    def predict(self, image_path, decode_method='greedy') -> str:
        img = self._preprocess(image_path).to(self.device)
        with torch.no_grad():
            outputs = self.model(img)
            decoded = decode_ctc_predictions(
                outputs.cpu(), self.idx_to_char, method=decode_method)
        return decoded[0]

    def predict_batch(self, image_paths, decode_method='greedy') -> List[Dict]:
        results = []
        for image_path in image_paths:
            try:
                text = self.predict(image_path, decode_method)
                results.append({'image_path': str(image_path),
                                'text': text, 'success': True})
            except Exception as e:
                results.append({'image_path': str(image_path),
                                'error': str(e), 'success': False})
        return results

    def process_form(self, form_image_path, form_type) -> Dict:
        text   = self.predict(form_image_path)
        fields = extract_form_fields(text, form_type)
        fields['raw_text'] = text
        return fields


# ─────────────────────────────────────────────────────────────────────────────
# FORM FIELD EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

class FormFieldExtractor:
    def __init__(self, ocr_model: CivilRegistryOCR):
        self.ocr = ocr_model

    def extract_form1a_fields(self, path):
        text = self.ocr.predict(path)
        return {'form_type': 'Form 1A - Birth Certificate', 'raw_text': text}

    def extract_form2a_fields(self, path):
        text = self.ocr.predict(path)
        return {'form_type': 'Form 2A - Death Certificate', 'raw_text': text}

    def extract_form3a_fields(self, path):
        text = self.ocr.predict(path)
        return {'form_type': 'Form 3A - Marriage Certificate', 'raw_text': text}

    def extract_form90_fields(self, path):
        text = self.ocr.predict(path)
        return {'form_type': 'Form 90 - Marriage License Application',
                'raw_text': text}


# ─────────────────────────────────────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────────────────────────────────────

def demo_inference():
    print("=" * 70)
    print("Civil Registry OCR  (auto-adaptive normalizer)")
    print("=" * 70)

    ocr = CivilRegistryOCR(
        checkpoint_path='checkpoints/best_model.pth',
        device='cuda',
        mode='auto',
        verbose=True   # shows which mode each image triggers
    )

    print("\n1. Single Prediction:")
    try:
        result = ocr.predict('test_images/date1.jpg')
        print(f"   Recognized text: {result}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n2. Batch Prediction:")
    '''batch_results = ocr.predict_batch([
        'test_images/name1.jpg',
        'test_images/shane.jpg',
        'test_images/date1.jpg',
        'test_images/place1.jpg',
    ])
    for r in batch_results:
        status = r['text'] if r['success'] else f"ERROR - {r['error']}"
        print(f"   {r['image_path']}: {status}")'''

    print("\n3. Form Processing:")
    try:
        form_data = ocr.process_form('test_images/form1a_sample.jpg', 'form1a')
        print(f"   Form Type: Form 1A - Birth Certificate")
        print(f"   Raw Text: {form_data['raw_text']}")
    except Exception as e:
        print(f"   Error: {e}")


def create_inference_api():
    class OCR_API:
        def __init__(self, checkpoint_path, mode='auto'):
            self.ocr       = CivilRegistryOCR(checkpoint_path, mode=mode)
            self.extractor = FormFieldExtractor(self.ocr)
        def recognize_text(self, p):
            return {'text': self.ocr.predict(p), 'success': True}
        def process_birth_certificate(self, p):
            return self.extractor.extract_form1a_fields(p)
        def process_death_certificate(self, p):
            return self.extractor.extract_form2a_fields(p)
        def process_marriage_certificate(self, p):
            return self.extractor.extract_form3a_fields(p)
        def process_marriage_license(self, p):
            return self.extractor.extract_form90_fields(p)
    return OCR_API


if __name__ == "__main__":
    demo_inference()
