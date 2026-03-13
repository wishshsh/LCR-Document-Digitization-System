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
#   # Path A — single cert PDF (birth / death / marriage)
#   result = pipeline.process_pdf("form_102.pdf", form_type="birth")
#   print(result["name_of_child"])
#
#   # Path B — Form 90 (needs two birth certs)
#   result = pipeline.process_form90(
#       groom_pdf="groom_birth_cert.pdf",
#       bride_pdf="bride_birth_cert.pdf"
#   )
# ============================================================

import sys
import os
import json
from pathlib import Path

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


class CivilRegistryPipeline:
    """
    Connects CRNN+CTC → MNB → spaCy NER in one call.

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
        self.bridge = CivilRegistryBridge(ner_model_path=ner_model_path, mnb_model_dir=mnb_model_dir)

        print("\n  ✅ Pipeline ready\n")

    # ─────────────────────────────────────────────────────────
    # PATH A — Single certification form (102 / 103 / 97)
    # ─────────────────────────────────────────────────────────
    def process_pdf(self,
                    pdf_path:  str,
                    form_type: str = None,
                    dpi:       int = 200) -> dict:
        """
        Process one PDF through the full pipeline.

        Parameters
        ----------
        pdf_path  : str   Path to scanned PDF
        form_type : str   'birth' | 'death' | 'marriage'
                          If None, MNB auto-detects.
        dpi       : int   Render DPI (default 200)

        Returns
        -------
        dict with all extracted form fields
        """
        print(f"\n  Processing: {pdf_path}")

        # Step 1 — CRNN+CTC: PDF → field dict
        crnn_fields = self._run_crnn(pdf_path, form_type, dpi)

        # Step 2+3 — MNB → NER via bridge
        form_obj = self.bridge.process(crnn_fields, form_hint=form_type)

        result = form_obj.to_dict()
        print(f"  ✅ Done — {len([v for v in result.values() if v])} fields extracted")
        return result

    # ─────────────────────────────────────────────────────────
    # PATH B — Form 90 (two birth certs → marriage license)
    # ─────────────────────────────────────────────────────────
    def process_form90(self,
                       groom_pdf: str,
                       bride_pdf: str,
                       dpi: int = 200) -> dict:
        """
        Process two birth cert PDFs into a Form 90.

        Parameters
        ----------
        groom_pdf : str   Path to groom's birth certificate PDF
        bride_pdf : str   Path to bride's birth certificate PDF
        dpi       : int   Render DPI (default 200)

        Returns
        -------
        dict with all Form 90 fields (groom_* and bride_*)
        """
        print(f"\n  Processing Form 90")
        print(f"  Groom: {groom_pdf}")
        print(f"  Bride: {bride_pdf}")

        # Step 1 — CRNN+CTC both birth certs
        groom_fields = self._run_crnn(groom_pdf, "birth", dpi)
        bride_fields = self._run_crnn(bride_pdf,  "birth", dpi)

        # Step 2+3 — bridge fills Form 90
        form90 = self.bridge.process_marriage_license(groom_fields, bride_fields)

        result = form90.to_dict()
        print(f"  ✅ Done — {len([v for v in result.values() if v])} fields extracted")
        return result

    # ─────────────────────────────────────────────────────────
    # Internal — run CRNN on one PDF
    # ─────────────────────────────────────────────────────────
    def _run_crnn(self, pdf_path: str, form_type: str, dpi: int) -> dict:
        """Convert PDF → run CRNN → return field dict."""
        # 1. PDF → image
        page_image = pdf_to_image(pdf_path, dpi=dpi)

        # 2. Resolve form_type — default to 'birth' if unknown/None
        # extract_field_images uses the form_type string to pick the
        # correct field map (BIRTH_FIELDS / DEATH_FIELDS / MARRIAGE_FIELDS)
        resolved_type = form_type if form_type in FORM_FIELDS_MAP else "birth"

        # 3. Crop fields from image using form_type string
        crops = extract_field_images(page_image, form_type=resolved_type)

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
    parser.add_argument("--pdf",      required=True, help="Path to PDF")
    parser.add_argument("--form",     default=None,
                        choices=["birth", "death", "marriage", "form90"],
                        help="Form type (optional, MNB auto-detects if not given)")
    parser.add_argument("--groom",    default=None, help="Groom birth cert PDF (Form 90 only)")
    parser.add_argument("--bride",    default=None, help="Bride birth cert PDF (Form 90 only)")
    parser.add_argument("--output",   default=None, help="Save result to JSON file")
    parser.add_argument("--dpi",      type=int, default=200)
    args = parser.parse_args()

    pipeline = CivilRegistryPipeline()

    if args.form == "form90":
        if not args.groom or not args.bride:
            print("ERROR: --groom and --bride required for form90")
        else:
            result = pipeline.process_form90(args.groom, args.bride, dpi=args.dpi)
    else:
        result = pipeline.process_pdf(args.pdf, form_type=args.form, dpi=args.dpi)

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
