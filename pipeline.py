# pipeline.py
# ============================================================
# FULL PIPELINE — connects all three algorithms
#
#   CRNN+CTC (field_extractor.py)
#       ↓  field dict
#   bridge.py  →  MNB (form_classifier.py)
#       ↓  form type
#   spaCy NER (extractor.py)
#       ↓
#   Populated Form object (Form1A / Form2A / Form3A / Form90)
#
# USAGE:
#   from pipeline import CivilRegistryPipeline
#
#   pipeline = CivilRegistryPipeline()
#
#   # Path A — single cert PDF, JPG, or PNG (birth / death / marriage)
#   result = pipeline.process_file("form_102.pdf", form_type="birth")
#   result = pipeline.process_file("form_102.jpg", form_type="birth")
#   result = pipeline.process_file("form_102.png", form_type="birth")
#   print(result["name_of_child"])
#
#   # Path B — Form 90 (needs two birth certs, any format)
#   result = pipeline.process_form90(
#       groom_file="groom_birth_cert.pdf",
#       bride_file="bride_birth_cert.png"
#   )
#
# SUPPORTED FILE TYPES:
#   .pdf  — converted to image via pdf_to_image() at given DPI
#   .jpg  — loaded directly as PIL Image
#   .jpeg — loaded directly as PIL Image
#   .png  — loaded directly as PIL Image
# ============================================================

import sys
import os
import json
from pathlib import Path
from PIL import Image

# ── Make sure all three algorithm folders are importable ─────
_ROOT = Path(__file__).parent
for folder in ["CRNN+CTC", "MNB", "spacyNER"]:
    p = str(_ROOT / folder)
    if p not in sys.path:
        sys.path.insert(0, p)
sys.path.insert(0, str(_ROOT))

# ── Import CRNN+CTC (Irish's module) ─────────────────────────
# CRNN+CTC folder is already on sys.path, import directly
from field_extractor import (
    pdf_to_image,
    extract_field_images,
    run_crnn_ocr,
    load_crnn_model,
    BIRTH_FIELDS,
    DEATH_FIELDS,
    MARRIAGE_FIELDS,
)

# ── Import bridge (MNB + NER connector) ──────────────────────
from bridge import CivilRegistryBridge, crnn_birth_to_text

import torch

# ── Config ────────────────────────────────────────────────────
CRNN_CHECKPOINT = str(_ROOT / "CRNN+CTC" / "checkpoints" / "best_model.pth")
NER_MODEL_PATH  = str(_ROOT / "spacyNER" / "models" / "civil_registry_model" / "model-best")
MNB_MODEL_DIR   = str(_ROOT / "MNB" / "models")

FORM_FIELDS_MAP = {
    "birth":    BIRTH_FIELDS,
    "death":    DEATH_FIELDS,
    "marriage": MARRIAGE_FIELDS,
}

# Supported file extensions
PDF_EXTENSIONS   = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALL_EXTENSIONS   = PDF_EXTENSIONS | IMAGE_EXTENSIONS


class CivilRegistryPipeline:
    """
    Connects CRNN+CTC → MNB → spaCy NER in one call.
    Accepts PDF, JPG, and PNG uploaded files.

    Each member's code is untouched:
      - Irish   : crnn_ctc/field_extractor.py  (CRNN+CTC)
      - Princess: mnb/form_classifier.py        (MNB)
      - Shane   : spacyNER/extractor.py         (NER)
    """

    def __init__(self,
                 crnn_checkpoint: str = CRNN_CHECKPOINT,
                 ner_model_path:  str = NER_MODEL_PATH,
                 mnb_model_dir:   str = MNB_MODEL_DIR):

        print("=" * 55)
        print("  Initializing Civil Registry Pipeline")
        print("=" * 55)

        # ── 1. Load CRNN model (Irish) ────────────────────────
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        print(f"\n  [CRNN] Loading model...")
        self.crnn_model, self.idx_to_char, self.img_h, self.img_w = (
            load_crnn_model(crnn_checkpoint, self.device)
        )

        # ── 2. Load MNB + NER via bridge ─────────────────────
        print(f"\n  [MNB + NER] Loading models...")
        self.bridge = CivilRegistryBridge(
            ner_model_path=ner_model_path,
            mnb_model_dir=mnb_model_dir
        )

        print("\n  ✅ Pipeline ready\n")
        print(f"  Supported formats: PDF, JPG, JPEG, PNG\n")

    # ─────────────────────────────────────────────────────────
    # PATH A — Single certification form (102 / 103 / 97)
    # Accepts PDF, JPG, or PNG
    # ─────────────────────────────────────────────────────────
    def process_file(self,
                     file_path: str,
                     form_type: str = None,
                     dpi:       int = 200) -> dict:
        """
        Process one file (PDF, JPG, or PNG) through the full pipeline.

        Parameters
        ----------
        file_path : str   Path to scanned file (.pdf / .jpg / .jpeg / .png)
        form_type : str   'birth' | 'death' | 'marriage'
                          If None, MNB auto-detects.
        dpi       : int   Render DPI for PDFs (default 200, ignored for images)

        Returns
        -------
        dict with all extracted form fields
        """
        ext = Path(file_path).suffix.lower()
        if ext not in ALL_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: '{ext}'. "
                f"Accepted formats: PDF, JPG, JPEG, PNG"
            )

        print(f"\n  Processing: {file_path}  [{ext}]")

        # Step 1 — CRNN+CTC: file → field dict
        crnn_fields = self._run_crnn(file_path, form_type, dpi)

        # Step 2+3 — MNB → NER via bridge
        form_obj = self.bridge.process(crnn_fields, form_hint=form_type)

        result = form_obj.to_dict()
        print(f"  ✅ Done — {len([v for v in result.values() if v])} fields extracted")
        return result

    # Keep process_pdf as an alias so existing code doesn't break
    def process_pdf(self,
                    pdf_path:  str,
                    form_type: str = None,
                    dpi:       int = 200) -> dict:
        """Alias for process_file() — kept for backwards compatibility."""
        return self.process_file(pdf_path, form_type=form_type, dpi=dpi)

    # ─────────────────────────────────────────────────────────
    # PATH B — Form 90 (two birth certs → marriage license)
    # Each cert can be PDF, JPG, or PNG independently
    # ─────────────────────────────────────────────────────────
    def process_form90(self,
                       groom_file: str,
                       bride_file: str,
                       dpi: int = 200) -> dict:
        """
        Process two birth cert files (PDF/JPG/PNG) into a Form 90.

        Parameters
        ----------
        groom_file : str   Path to groom's birth certificate (.pdf/.jpg/.png)
        bride_file : str   Path to bride's birth certificate (.pdf/.jpg/.png)
        dpi        : int   Render DPI for PDFs (ignored for images)

        Returns
        -------
        dict with all Form 90 fields (groom_* and bride_*)
        """
        print(f"\n  Processing Form 90")
        print(f"  Groom: {groom_file}  [{Path(groom_file).suffix.lower()}]")
        print(f"  Bride: {bride_file}  [{Path(bride_file).suffix.lower()}]")

        # Step 1 — CRNN+CTC both birth certs (each may be a different format)
        groom_fields = self._run_crnn(groom_file, "birth", dpi)
        bride_fields = self._run_crnn(bride_file,  "birth", dpi)

        # Step 2+3 — bridge fills Form 90
        form90 = self.bridge.process_marriage_license(groom_fields, bride_fields)

        result = form90.to_dict()
        print(f"  ✅ Done — {len([v for v in result.values() if v])} fields extracted")
        return result

    # Keep process_form90 with old param names as alias
    def process_form90_pdf(self,
                           groom_pdf: str,
                           bride_pdf: str,
                           dpi: int = 200) -> dict:
        """Alias for process_form90() — kept for backwards compatibility."""
        return self.process_form90(groom_pdf, bride_pdf, dpi=dpi)

    # ─────────────────────────────────────────────────────────
    # Internal — load file into a PIL Image (PDF or image)
    # ─────────────────────────────────────────────────────────
    def _load_image(self, file_path: str, dpi: int) -> Image.Image:
        """
        Load any supported file into a PIL Image.

        - PDF  : converted to image via pdf_to_image() at given DPI
        - JPG/JPEG/PNG : opened directly with Pillow, converted to RGB
        """
        ext = Path(file_path).suffix.lower()

        if ext in PDF_EXTENSIONS:
            # pdf_to_image() is Irish's function — returns a PIL Image
            return pdf_to_image(file_path, dpi=dpi)

        elif ext in IMAGE_EXTENSIONS:
            # Open directly — convert to RGB so it matches PDF output format
            img = Image.open(file_path).convert("RGB")
            print(f"  [Pipeline] Image loaded: {img.size[0]}x{img.size[1]}px")
            return img

        else:
            raise ValueError(f"Unsupported file type: '{ext}'")

    # ─────────────────────────────────────────────────────────
    # Internal — run CRNN on one file (PDF, JPG, or PNG)
    # ─────────────────────────────────────────────────────────
    def _run_crnn(self, file_path: str, form_type: str, dpi: int) -> dict:
        """
        Load file → crop fields → run CRNN OCR → return field dict.

        Works for PDF, JPG, JPEG, and PNG.
        """
        # 1. Load file into a PIL Image (handles PDF vs image internally)
        page_image = self._load_image(file_path, dpi)

        # 2. Select correct field map
        if form_type in FORM_FIELDS_MAP:
            fields = FORM_FIELDS_MAP[form_type]
        else:
            # Let MNB decide — run a quick preview pass on birth fields
            # then bridge will auto-detect from field keys
            fields = BIRTH_FIELDS

        # 3. Crop fields from image
        crops = extract_field_images(page_image, fields)

        # 4. CRNN OCR each crop
        crnn_output = run_crnn_ocr(
            crops, self.crnn_model, self.idx_to_char,
            self.img_h, self.img_w, self.device
        )
        return crnn_output


# ── Standalone demo ───────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Civil Registry Pipeline — CRNN + MNB + NER"
    )
    parser.add_argument("--file",     required=True,
                        help="Path to file (.pdf / .jpg / .jpeg / .png)")
    parser.add_argument("--form",     default=None,
                        choices=["birth", "death", "marriage", "form90"],
                        help="Form type (optional, MNB auto-detects if not given)")
    parser.add_argument("--groom",    default=None,
                        help="Groom birth cert file — PDF/JPG/PNG (Form 90 only)")
    parser.add_argument("--bride",    default=None,
                        help="Bride birth cert file — PDF/JPG/PNG (Form 90 only)")
    parser.add_argument("--output",   default=None,
                        help="Save result to JSON file")
    parser.add_argument("--dpi",      type=int, default=200,
                        help="DPI for PDF rendering (ignored for JPG/PNG)")
    args = parser.parse_args()

    pipeline = CivilRegistryPipeline()

    if args.form == "form90":
        if not args.groom or not args.bride:
            print("ERROR: --groom and --bride required for form90")
            print("  Example: python pipeline.py --form form90 "
                  "--groom groom.pdf --bride bride.jpg")
        else:
            result = pipeline.process_form90(
                args.groom, args.bride, dpi=args.dpi
            )
    else:
        result = pipeline.process_file(
            args.file, form_type=args.form, dpi=args.dpi
        )

    # Print result
    print("\n" + "=" * 55)
    print("  EXTRACTED FIELDS")
    print("=" * 55)
    for field, value in result.items():
        if value:
            print(f"  {field:<35} {value}")

    # Save to JSON
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n  Saved → {args.output}")