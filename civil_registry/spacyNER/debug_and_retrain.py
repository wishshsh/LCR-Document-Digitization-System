#!/usr/bin/env python3
# debug_and_retrain.py
# ============================================================
# USE THIS WHEN: training crashes with E024 or any span error
#
# WHAT IT DOES (in order):
#   1. Checks all .spacy files for bad spans (whitespace, empty)
#   2. Runs spaCy's official debug data command
#   3. Deletes corrupted .spacy files so they get rebuilt clean
#   4. Rebuilds: prepare_data → funsd_integration → train
#
# USAGE:
#   python debug_and_retrain.py           ← full check + retrain
#   python debug_and_retrain.py --check   ← check only, no retrain
#   python debug_and_retrain.py --retrain ← skip check, just retrain
# ============================================================

import subprocess
import sys
import argparse
from pathlib import Path


# ── All .spacy files to check ─────────────────────────────
SPACY_FILES = {
    "train.spacy":         "data/training/train.spacy",
    "dev.spacy":           "data/training/dev.spacy",
    "funsd_train.spacy":   "data/training/funsd_train.spacy",
    "funsd_dev.spacy":     "data/training/funsd_dev.spacy",
    "merged_train.spacy":  "data/training/merged_train.spacy",
    "merged_dev.spacy":    "data/training/merged_dev.spacy",
}

# Files that get REBUILT (delete these before retraining)
REBUILT_FILES = list(SPACY_FILES.values())

CFG = "training/config.cfg"


# ══════════════════════════════════════════════════════════
# STEP 1 — INSPECT .spacy FILES FOR BAD SPANS
# ══════════════════════════════════════════════════════════

def inspect_spacy_file(path: str):
    """
    Load a .spacy file and scan every entity span for problems.
    Returns (total_docs, total_ents, bad_spans_list).

    Bad span types that cause E024:
      - Leading whitespace:   span.text starts with ' ' or '\\n'
      - Trailing whitespace:  span.text ends with ' ' or '\\n'
      - Empty span:           span.text == ''
      - Punctuation-only:     e.g. '.' or ','
    """
    import spacy
    from spacy.tokens import DocBin

    nlp    = spacy.blank("en")
    db     = DocBin().from_disk(path)
    docs   = list(db.get_docs(nlp.vocab))

    total_ents = 0
    bad_spans  = []

    for i, doc in enumerate(docs):
        for ent in doc.ents:
            total_ents += 1
            t = ent.text

            if not t.strip():
                bad_spans.append({
                    "doc": i, "label": ent.label_, "text": repr(t),
                    "reason": "EMPTY or whitespace-only"
                })
            elif t != t.strip():
                bad_spans.append({
                    "doc": i, "label": ent.label_, "text": repr(t),
                    "reason": f"WHITESPACE — leading={repr(t[0])} trailing={repr(t[-1])}"
                })
            elif len(t) == 1 and not t.isalnum():
                bad_spans.append({
                    "doc": i, "label": ent.label_, "text": repr(t),
                    "reason": "SINGLE PUNCTUATION CHAR"
                })

    return len(docs), total_ents, bad_spans


def check_all_spacy_files():
    """Check every .spacy file and report problems."""
    try:
        import spacy
    except ImportError:
        print("  ❌ spaCy not installed. Run: pip install spacy")
        return False

    print("\n" + "=" * 62)
    print("  STEP 1 — SCANNING .spacy FILES FOR BAD SPANS")
    print("=" * 62)

    any_problems = False

    for name, path in SPACY_FILES.items():
        if not Path(path).exists():
            print(f"\n  ⚪ {name:30s}  not found — will be created")
            continue

        print(f"\n  📄 {name}")
        try:
            n_docs, n_ents, bad = inspect_spacy_file(path)
            print(f"     docs: {n_docs}   entities: {n_ents}   bad spans: {len(bad)}")

            if bad:
                any_problems = True
                print(f"     ❌ {len(bad)} PROBLEM SPAN(S):")
                for b in bad[:10]:   # show first 10
                    print(f"        doc {b['doc']:>3}  [{b['label']}]  {b['text']:30s}  ← {b['reason']}")
                if len(bad) > 10:
                    print(f"        ... and {len(bad) - 10} more")
            else:
                print(f"     ✅ All spans clean")

        except Exception as e:
            print(f"     ❌ Could not read file: {e}")
            any_problems = True

    return any_problems


# ══════════════════════════════════════════════════════════
# STEP 2 — spaCy OFFICIAL DEBUG DATA
# ══════════════════════════════════════════════════════════

def run_spacy_debug():
    """
    Run spaCy's built-in debug data command.
    This catches problems our scanner might miss.
    """
    print("\n" + "=" * 62)
    print("  STEP 2 — spaCy OFFICIAL DEBUG DATA")
    print("=" * 62)

    train = "data/training/merged_train.spacy"
    dev   = "data/training/merged_dev.spacy"

    # Fall back to civil-only if merged doesn't exist
    if not Path(train).exists():
        train = "data/training/train.spacy"
        dev   = "data/training/dev.spacy"

    if not Path(train).exists():
        print("\n  ⚪ No training data found yet — skipping debug.")
        print("  → Run: python training/prepare_data.py first")
        return

    if not Path(CFG).exists():
        print(f"\n  ⚪ Config not found: {CFG} — skipping debug.")
        return

    print(f"\n  Checking: {train}")
    print(f"  Dev:      {dev}\n")

    result = subprocess.run([
        sys.executable, "-m", "spacy", "debug", "data", CFG,
        "--paths.train", train,
        "--paths.dev",   dev,
    ])

    if result.returncode != 0:
        print("\n  ⚠️  debug data found issues — see above.")
    else:
        print("\n  ✅ debug data passed — no issues found.")


# ══════════════════════════════════════════════════════════
# STEP 3 — DELETE OLD .spacy FILES
# ══════════════════════════════════════════════════════════

def delete_spacy_files():
    """Delete all generated .spacy files so they get rebuilt clean."""
    print("\n" + "=" * 62)
    print("  STEP 3 — DELETING OLD .spacy FILES")
    print("=" * 62)

    deleted = 0
    for path in REBUILT_FILES:
        p = Path(path)
        if p.exists():
            p.unlink()
            print(f"  🗑️  Deleted: {path}")
            deleted += 1

    if deleted == 0:
        print("  ⚪ Nothing to delete.")
    else:
        print(f"\n  ✅ Deleted {deleted} file(s) — will be rebuilt clean.")


# ══════════════════════════════════════════════════════════
# STEP 4 — REBUILD + RETRAIN
# ══════════════════════════════════════════════════════════

def run_script(script: str, label: str) -> bool:
    """Run a training script. Returns True on success."""
    print(f"\n{'─' * 62}")
    print(f"  ▶ {label}")
    print(f"  Script: {script}")
    print(f"{'─' * 62}\n")

    if not Path(script).exists():
        print(f"  ❌ Script not found: {script}")
        return False

    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"\n  ❌ {label} failed.")
        return False

    print(f"\n  ✅ {label} complete.")
    return True


def retrain():
    """Run the full rebuild pipeline: prepare → funsd → train."""
    print("\n" + "=" * 62)
    print("  STEP 4 — REBUILD + RETRAIN")
    print("=" * 62)

    steps = [
        ("training/prepare_data.py",      "Step 1/3: Build civil registry data"),
        ("training/funsd_integration.py", "Step 2/3: Merge FUNSD + civil registry"),
        ("training/train.py",             "Step 3/3: Train NER model"),
    ]

    for script, label in steps:
        ok = run_script(script, label)
        if not ok:
            print(f"\n  ❌ Pipeline stopped at: {script}")
            print(f"  Fix the error above, then re-run:")
            print(f"    python debug_and_retrain.py --retrain")
            sys.exit(1)

    print("\n" + "=" * 62)
    print("  ✅ RETRAIN COMPLETE")
    print("=" * 62)
    print("\n  Best model → models/civil_registry_model/model-best/")
    print("\n  NEXT:  python training/evaluate.py")


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Debug FUNSD/civil data and retrain NER model"
    )
    parser.add_argument("--check",   action="store_true",
                        help="Check for bad spans only — don't retrain")
    parser.add_argument("--retrain", action="store_true",
                        help="Skip check — delete old files and retrain immediately")
    args = parser.parse_args()

    print("\n" + "=" * 62)
    print("  CIVIL REGISTRY NER — DEBUG & RETRAIN")
    print("=" * 62)
    print("\n  This script fixes the E024 'bad span' training error.")
    print("  Root causes: whitespace in spans, wrong alignment_mode,")
    print("               offset shift from text.strip() after build.")

    if args.retrain:
        # Skip checking — just delete and rebuild
        delete_spacy_files()
        retrain()
        return

    # ── Always run checks ─────────────────────────────────
    has_problems = check_all_spacy_files()
    run_spacy_debug()

    if args.check:
        # Check-only mode — stop here
        print("\n" + "=" * 62)
        if has_problems:
            print("  ⚠️  Problems found — run without --check to fix:")
            print("      python debug_and_retrain.py")
        else:
            print("  ✅ No problems found — safe to train:")
            print("      python training/train.py")
        print("=" * 62)
        return

    # ── Ask before deleting ───────────────────────────────
    print("\n" + "=" * 62)
    if has_problems:
        print("  ⚠️  Bad spans detected in .spacy files.")
        print("  The fixed funsd_integration.py will rebuild them cleanly.")
    else:
        print("  ✅ No bad spans detected in existing files.")

    print("\n  Proceeding to delete old .spacy files and retrain...")
    print("  (Ctrl+C now to cancel)")
    print("=" * 62)

    try:
        input("\n  Press ENTER to continue, Ctrl+C to cancel...\n")
    except KeyboardInterrupt:
        print("\n  Cancelled.")
        return

    delete_spacy_files()
    retrain()


if __name__ == "__main__":
    main()
