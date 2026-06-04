# training/funsd_integration.py
# ============================================================
# FUNSD + FUNSD+ INTEGRATION
# ============================================================
#
# PURPOSE:
#   Converts FUNSD / FUNSD+ form datasets into spaCy .spacy
#   format, then merges them with civil registry training data.
#
# WHY TWO DATASETS?
#   FUNSD original   — 199 real scanned forms, 149 train / 50 test
#   FUNSD+           — improved labels, same forms (from HuggingFace)
#   Civil Registry   — 101 custom annotated examples (prepare_data.py)
#
#   FUNSD teaches the model what FORM STRUCTURE looks like:
#     questions (field labels), answers (field values), headers.
#   Civil Registry teaches the SPECIFIC LABELS we care about:
#     F102_CHILD_FIRST, F103_DECEASED_LAST, F90_DATE_OF_BIRTH, etc.
#
# PIPELINE:
#   Step 1 → python training/prepare_data.py      (civil registry)
#   Step 2 → python training/funsd_integration.py (this file)
#   Step 3 → python training/train.py             (train on merged)
#   Step 4 → python training/evaluate.py          (check accuracy)
#
# FUNSD ORIGINAL — YOU ALREADY DOWNLOADED THIS:
#   Place dataset.zip in any of these locations (auto-detected):
#     data/funsd/dataset.zip          ← recommended
#     dataset.zip                     ← project root
#     ~/Downloads/dataset.zip
#
# FUNSD+ (HUGGINGFACE):
#   pip install datasets
#   python training/download_funsd_plus.py
#   Creates: data/funsd_plus/train.json and test.json
#
# WHAT IF I ONLY HAVE ONE?
#   Script uses whichever is available.
#   If both: uses BOTH (maximum pretraining data).
#   If neither: warns and exits gracefully.
# ============================================================

import json
import zipfile
import urllib.request
from pathlib import Path

import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

# ── Paths ──────────────────────────────────────────────────
FUNSD_DIR      = Path("data/funsd")
FUNSD_PLUS_DIR = Path("data/funsd_plus")
OUTPUT_DIR     = Path("data/training")

# ── FUNSD auto-detection ───────────────────────────────────
# Supports three ways the user may have placed FUNSD:
#   A. Zip file  → data/funsd/dataset.zip  (we extract it)
#   B. Extracted folder already inside data/funsd/
#      e.g. data/funsd/dataset/training/annotations/
#      e.g. data/funsd/training/annotations/
#   C. Zip elsewhere (Downloads, project root)

FUNSD_ZIP_CANDIDATES = [
    Path("data/funsd/dataset.zip"),
    Path("dataset.zip"),
    Path.home() / "Downloads" / "dataset.zip",
    Path.home() / "Downloads" / "FUNSD.zip",
]

FUNSD_URL = "https://guillaumejaume.github.io/FUNSD/dataset.zip"

# ── Label maps ─────────────────────────────────────────────
FUNSD_LABEL_MAP = {
    "answer":   "FORM_ANSWER",
    "question": "FORM_QUESTION",
    "header":   "FORM_HEADER",
    "other":    "FORM_OTHER",
}

FUNSD_PLUS_LABEL_MAP = {
    0: "FORM_OTHER",
    1: "FORM_HEADER",
    2: "FORM_QUESTION",
    3: "FORM_ANSWER",
}


# ══════════════════════════════════════════════════════════
# FUNSD ORIGINAL
# ══════════════════════════════════════════════════════════

def find_annotations_dir(search_root: Path, split: str):
    """
    Find the annotations/ directory for the given split.

    Handles all possible ways the user may have placed FUNSD:
      - data/funsd/dataset/training/annotations/   (zip extracted here)
      - data/funsd/training/annotations/           (inner folder placed directly)
      - data/funsd/<anyfolder>/training/annotations/
      - any annotations/ folder whose path contains the split name

    split: "training" or "testing"
    """
    # Fixed candidate paths (most common layouts first)
    candidates = [
        search_root / "dataset" / split / "annotations",
        search_root / split / "annotations",
        search_root / "FUNSD" / "dataset" / split / "annotations",
        search_root / "extracted" / "dataset" / split / "annotations",
        search_root / "extracted" / split / "annotations",
    ]
    # Recursive fallback: any annotations/ folder that contains the split name
    for found in search_root.rglob("annotations"):
        if found.is_dir() and split in str(found).replace("\\", "/"):
            if found not in candidates:
                candidates.append(found)

    for c in candidates:
        if c.exists() and any(c.glob("*.json")):
            return c
    return None


def find_funsd_root():
    """
    Find the FUNSD data root — works whether the user placed:
      A. A zip file  (we extract it, return the extract folder)
      B. An already-extracted folder inside data/funsd/
      C. Nothing (returns None)

    Returns: (root_path, source_description) or (None, None)
    """
    # ── B: Check for already-extracted folder in data/funsd/ ──
    # If data/funsd/ contains any folder with a training/annotations subdir,
    # or directly contains a training/annotations subdir → use it as-is
    if FUNSD_DIR.exists():
        # Direct: data/funsd/training/annotations/ or data/funsd/dataset/training/...
        ann = find_annotations_dir(FUNSD_DIR, "training")
        if ann is not None:
            print(f"  ✅ Found FUNSD folder: {FUNSD_DIR}")
            print(f"     annotations at: {ann}")
            return FUNSD_DIR, "pre-extracted folder"

    # ── A: Check for a zip file ────────────────────────────────
    for candidate in FUNSD_ZIP_CANDIDATES:
        if candidate.exists():
            print(f"  ✅ Found FUNSD zip: {candidate}")
            extract_path = FUNSD_DIR / "extracted"
            if extract_path.exists() and any(extract_path.iterdir()):
                print(f"  ✅ Already extracted → {extract_path}")
            else:
                print(f"  📦 Extracting {candidate} ...")
                FUNSD_DIR.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(candidate, "r") as zf:
                    zf.extractall(extract_path)
                print(f"  ✅ Extracted → {extract_path}")
            return extract_path, f"extracted from {candidate.name}"

    return None, None


def download_funsd():
    """Download FUNSD from official URL as a last resort."""
    FUNSD_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FUNSD_DIR / "dataset.zip"
    if zip_path.exists():
        print(f"  ✅ Already downloaded: {zip_path}")
        return zip_path
    print(f"  ⬇️  Downloading FUNSD (~170MB) ...")
    try:
        urllib.request.urlretrieve(FUNSD_URL, zip_path)
        print("  ✅ Download complete.")
        return zip_path
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None


def load_funsd_original(split: str = "training"):
    """
    Load FUNSD original for the given split.
    split: "training" (149 forms) or "testing" (50 forms)

    Works whether user placed:
      - An already-extracted folder in data/funsd/
      - A zip file (data/funsd/dataset.zip or ~/Downloads/dataset.zip)
    """
    funsd_root, source = find_funsd_root()

    if funsd_root is None:
        print("  ⚠️  FUNSD not found locally — attempting download...")
        zip_path = download_funsd()
        if zip_path is None:
            print("  ❌ Could not get FUNSD data.")
            print("  → Place your FUNSD folder in: data/funsd/")
            print("    It should contain a 'training' or 'dataset' subfolder.")
            return []
        # After download, find the root again
        funsd_root = FUNSD_DIR / "extracted"
        FUNSD_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(funsd_root)

    ann_dir = find_annotations_dir(funsd_root, split)

    if ann_dir is None:
        print(f"  ❌ Could not find {split}/annotations/ in extracted FUNSD.")
        # Show what IS inside to help debug
        all_json = list(extract_path.rglob("*.json"))[:8]
        print(f"     JSON files found: {[str(p) for p in all_json]}")
        return []

    json_files = sorted(ann_dir.glob("*.json"))
    print(f"  📂 FUNSD [{split}]: {len(json_files)} annotation files  ← {ann_dir}")

    examples = []
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)

        form_items = data.get("form", [])

        # ── Build blocks first, then join with exact offsets ──────────
        # CRITICAL: Never call .strip() on full_text after computing
        # entity offsets — it shifts all char positions and causes E024.
        # Instead: strip each block individually, join with single space,
        # remove only the trailing space (not leading).
        blocks = []
        for item in form_items:
            label      = item.get("label", "other").lower()
            words      = item.get("words", [])
            if not words:
                continue
            # Strip individual word texts (FUNSD OCR has leading/trailing spaces)
            block_text = " ".join(w.get("text", "").strip() for w in words).strip()
            if not block_text:
                continue
            blocks.append((block_text, FUNSD_LABEL_MAP.get(label, "FORM_OTHER")))

        if not blocks:
            continue

        # Build full_text and compute offsets in one pass
        full_text = ""
        entities  = []
        for block_text, spacy_label in blocks:
            start = len(full_text)
            end   = start + len(block_text)
            entities.append((start, end, spacy_label))
            full_text += block_text + " "
        full_text = full_text[:-1]  # remove trailing space only — preserves offsets

        if full_text:
            examples.append((full_text, {"entities": entities}))

    print(f"  ✅ Loaded {len(examples)} docs from FUNSD [{split}]")
    return examples


# ══════════════════════════════════════════════════════════
# FUNSD+ (HUGGINGFACE)
# ══════════════════════════════════════════════════════════

def load_funsd_plus(json_path: str):
    """
    Load FUNSD+ from HuggingFace download.
    Labels: 0=other 1=header 2=question 3=answer
    """
    p = Path(json_path)
    if not p.exists():
        print(f"  ❌ Not found: {json_path}")
        print("  → pip install datasets")
        print("  → python training/download_funsd_plus.py")
        return []

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = []
    for item in data:
        words  = item.get("words", [])
        labels = item.get("labels", [])
        if not words:
            continue

        # ── Strip each word individually before joining ────────────
        # FUNSD+ words from HuggingFace can have surrounding whitespace.
        # We strip each word, then rebuild full_text and recompute
        # offsets from the clean joined string.
        clean_words  = [w.strip() for w in words]
        clean_labels = [l for w, l in zip(words, labels) if w.strip()]
        clean_words  = [w for w in clean_words if w]

        if not clean_words:
            continue

        full_text = ""
        entities  = []
        for word, lnum in zip(clean_words, clean_labels):
            start = len(full_text)
            end   = start + len(word)
            entities.append((start, end, FUNSD_PLUS_LABEL_MAP.get(lnum, "FORM_OTHER")))
            full_text += word + " "
        full_text = full_text[:-1]  # remove trailing space only

        if full_text:
            examples.append((full_text, {"entities": entities}))

    print(f"  ✅ Loaded {len(examples)} docs from FUNSD+ [{p.name}]")
    return examples


# ══════════════════════════════════════════════════════════
# SPACY CONVERSION + MERGING
# ══════════════════════════════════════════════════════════

def build_spacy_file(examples: list, output_path: str, label: str = ""):
    """
    Convert list of (text, {entities}) into a .spacy binary.

    Span cleaning rules (all required to prevent E024):
      1. Trim char-level whitespace from start/end before alignment
      2. Use alignment_mode="expand" to catch short tokens (ages, IDs)
         BUT immediately re-trim if expand pulled in whitespace
      3. Reject spans where text != text.strip() (E024 trigger)
      4. Reject empty spans and spans > 200 chars (OCR noise)
      5. Reject single-punctuation-only spans (FUNSD noise: ':', '%')
    """
    nlp     = spacy.blank("en")
    doc_bin = DocBin()
    skipped = 0
    n_ents  = 0

    # Single-char punctuation to skip entirely (FUNSD OCR noise)
    SKIP_PUNCT = set(".:,;!?()[]{}%$#@&*+-=/<>|\\'\"")

    for text, annotation in examples:
        doc  = nlp.make_doc(text)
        ents = []
        for start, end, lbl in annotation["entities"]:
            # 1. Skip empty or huge spans
            if start >= end or end - start > 200:
                skipped += 1
                continue

            # 2. Trim char-level whitespace BEFORE alignment
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if start >= end:
                skipped += 1
                continue

            # 3. Skip single-punctuation spans (FUNSD noise: ':', '%', '(')
            span_text = text[start:end]
            if len(span_text) == 1 and span_text in SKIP_PUNCT:
                skipped += 1
                continue

            # 4. Use "expand" to handle short tokens (ages like '88', IDs)
            #    "contract" returns None for single short tokens
            span = doc.char_span(start, end, label=lbl,
                                 alignment_mode="expand")
            if span is None:
                skipped += 1
                continue

            # 5. If expand grew the span into whitespace, shrink it back
            #    by re-creating from stripped token boundaries
            if span.text != span.text.strip():
                # Try contract instead — it won't add whitespace
                span = doc.char_span(start, end, label=lbl,
                                     alignment_mode="contract")
                if span is None:
                    skipped += 1
                    continue

            # 6. Final guard — reject if still has leading/trailing space
            #    This is the E024 trigger — must be zero tolerance
            if not span.text.strip() or span.text != span.text.strip():
                skipped += 1
                continue

            ents.append(span)

        doc.ents = filter_spans(ents)
        n_ents  += len(doc.ents)
        doc_bin.add(doc)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc_bin.to_disk(output_path)
    tag = f" [{label}]" if label else ""
    print(f"  💾 Saved{tag}: {len(examples)} docs, {n_ents} entities → {output_path}")
    if skipped:
        print(f"     ⚠️  Skipped {skipped} bad spans")


def merge_spacy_files(paths: list, output_path: str, label: str = ""):
    """Merge multiple .spacy files into one output file."""
    nlp    = spacy.blank("en")
    merged = DocBin()
    counts = []
    for p in paths:
        if not Path(p).exists():
            print(f"  ⚠️  Skipping missing: {p}")
            continue
        db   = DocBin().from_disk(p)
        docs = list(db.get_docs(nlp.vocab))
        for doc in docs:
            merged.add(doc)
        counts.append((Path(p).name, len(docs)))

    merged.to_disk(output_path)
    total = sum(c for _, c in counts)
    tag   = f" [{label}]" if label else ""
    print(f"  🔗 Merged{tag} → {output_path}  ({total} docs total)")
    for name, cnt in counts:
        print(f"       {cnt:>4}  {name}")


def count_spacy(path: str) -> int:
    if not Path(path).exists():
        return 0
    nlp = spacy.blank("en")
    return len(list(DocBin().from_disk(path).get_docs(nlp.vocab)))


def print_sample(examples: list, n: int = 1, title: str = ""):
    if not examples:
        return
    print(f"  Sample [{title}]:")
    for text, ann in examples[:n]:
        print(f"    text:     {text[:70].replace(chr(10),' ')}...")
        print(f"    entities: {len(ann['entities'])} total")
        for s, e, lbl in ann["entities"][:3]:
            print(f"      [{lbl}] '{text[s:e]}'")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 62)
    print("  STEP 2 of 4 — FUNSD INTEGRATION")
    print("  Merge form pretraining data with civil registry data")
    print("=" * 62)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Detect available datasets ──────────────────────────
    funsd_root, funsd_source = find_funsd_root()
    has_orig  = funsd_root is not None
    has_plus  = (FUNSD_PLUS_DIR / "train.json").exists()

    if has_orig:
        print(f"\n  FUNSD original:      ✅ {funsd_source}")
    else:
        print(f"\n  FUNSD original:      ❌ not found")
        print(f"     → Place your FUNSD folder in: data/funsd/")
        print(f"     → It should contain 'training/' or 'dataset/' subfolder")
    print(f"  FUNSD+ HuggingFace:  {'✅ found at ' + str(FUNSD_PLUS_DIR) if has_plus else '❌ not found'}")

    if not has_orig and not has_plus:
        print("\n  ❌ No FUNSD data found.")
        print("\n  To add FUNSD original:")
        print("     1. Download: https://guillaumejaume.github.io/FUNSD/download/")
        print("     2. Move dataset.zip → data/funsd/dataset.zip")
        print("     3. Re-run this script")
        print("\n  To add FUNSD+:")
        print("     pip install datasets")
        print("     python training/download_funsd_plus.py")
        print("\n  ⚠️  You can still train with civil registry data only:")
        print("     python training/train.py")
        exit(0)

    all_train = []
    all_dev   = []
    all_test  = []

    # ── A. FUNSD original ─────────────────────────────────
    if has_orig:
        print("\n[A] FUNSD ORIGINAL ─────────────────────────────────")
        train_orig = load_funsd_original("training")   # 149 forms
        test_orig  = load_funsd_original("testing")    # 50 forms
        if train_orig:
            print_sample(train_orig, title="FUNSD original")
            split = int(len(train_orig) * 0.8)
            all_train.extend(train_orig[:split])
            all_dev.extend(train_orig[split:])
        all_test.extend(test_orig)

    # ── B. FUNSD+ ─────────────────────────────────────────
    if has_plus:
        print("\n[B] FUNSD+ (HUGGINGFACE) ────────────────────────────")
        train_plus = load_funsd_plus(str(FUNSD_PLUS_DIR / "train.json"))
        test_plus  = load_funsd_plus(str(FUNSD_PLUS_DIR / "test.json"))
        if train_plus:
            print_sample(train_plus, title="FUNSD+")
            split = int(len(train_plus) * 0.8)
            all_train.extend(train_plus[:split])
            all_dev.extend(train_plus[split:])
        all_test.extend(test_plus)

    # ── C. Write FUNSD spacy files ────────────────────────
    print(f"\n[C] WRITING FUNSD .SPACY FILES ──────────────────────")
    print(f"    Combined train: {len(all_train)} docs")
    print(f"    Combined dev:   {len(all_dev)} docs")
    print(f"    Combined test:  {len(all_test)} docs")

    if all_train:
        build_spacy_file(all_train, str(OUTPUT_DIR / "funsd_train.spacy"), "FUNSD train")
    if all_dev:
        build_spacy_file(all_dev,   str(OUTPUT_DIR / "funsd_dev.spacy"),   "FUNSD dev")
    if all_test:
        build_spacy_file(all_test,  str(OUTPUT_DIR / "funsd_test.spacy"),  "FUNSD test")

    # ── D. Merge with civil registry ──────────────────────
    print(f"\n[D] MERGING WITH CIVIL REGISTRY ─────────────────────")
    civil_train = str(OUTPUT_DIR / "train.spacy")
    civil_dev   = str(OUTPUT_DIR / "dev.spacy")

    if not Path(civil_train).exists():
        print("  ❌ Civil registry data not found!")
        print("  → Run first: python training/prepare_data.py")
        exit(1)

    n_ctr = count_spacy(civil_train)
    n_cdev = count_spacy(civil_dev)
    print(f"  Civil registry: {n_ctr} train / {n_cdev} dev")

    merge_spacy_files(
        [str(OUTPUT_DIR / "funsd_train.spacy"), civil_train],
        str(OUTPUT_DIR / "merged_train.spacy"),
        "train"
    )
    merge_spacy_files(
        [str(OUTPUT_DIR / "funsd_dev.spacy"), civil_dev],
        str(OUTPUT_DIR / "merged_dev.spacy"),
        "dev"
    )

    # ── Final summary ──────────────────────────────────────
    n_mt = count_spacy(str(OUTPUT_DIR / "merged_train.spacy"))
    n_md = count_spacy(str(OUTPUT_DIR / "merged_dev.spacy"))

    print("\n" + "=" * 62)
    print("  ✅ STEP 2 COMPLETE")
    print("=" * 62)
    print(f"\n  {'Source':<28} {'Train':>6}  {'Dev':>6}")
    print(f"  {'─'*42}")
    if has_orig:
        orig_t = int(len(load_funsd_original.__doc__ and [] or []) * 0.8) if False else len(all_train) - (int(len(all_train)*0) if not has_plus else 0)
        print(f"  {'FUNSD original':<28} {'(see above)':>6}")
    if has_plus:
        print(f"  {'FUNSD+ (HuggingFace)':<28} {'(see above)':>6}")
    print(f"  {'Civil registry':<28} {n_ctr:>6}  {n_cdev:>6}")
    print(f"  {'─'*42}")
    print(f"  {'MERGED TOTAL':<28} {n_mt:>6}  {n_md:>6}")
    print(f"\n  NEXT STEP:")
    print(f"    python training/train.py")
