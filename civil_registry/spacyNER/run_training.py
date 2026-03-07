#!/usr/bin/env python3
# run_training.py
# ============================================================
# COMPLETE TRAINING PIPELINE — runs all 4 steps in order
# ============================================================
#
# STEPS:
#   Step 1 — prepare_data.py      Build civil registry .spacy files
#   Step 2 — funsd_integration.py Merge FUNSD + civil registry
#   Step 3 — train.py             Train the NER model
#   Step 4 — evaluate.py          Report accuracy
#
# BEFORE RUNNING:
#   1. Place FUNSD dataset.zip in:  data/funsd/dataset.zip
#      Download from: https://guillaumejaume.github.io/FUNSD/download/
#
#   2. (Optional) For FUNSD+ too:
#      pip install datasets
#      python training/download_funsd_plus.py
#
# USAGE:
#   python run_training.py
#
#   Or skip steps:
#   python run_training.py --skip-funsd     (civil registry only)
#   python run_training.py --start-from 3  (skip steps 1-2)
#   python run_training.py --only 4        (evaluate only)
# ============================================================

import subprocess
import sys
import argparse
from pathlib import Path


STEPS = {
    1: ("prepare_data",      "training/prepare_data.py",      "Build civil registry training data"),
    2: ("funsd_integration", "training/funsd_integration.py", "Merge FUNSD + civil registry data"),
    3: ("train",             "training/train.py",             "Train NER model"),
    4: ("evaluate",          "training/evaluate.py",          "Evaluate model accuracy"),
}


def run_step(step_num: int, skip_on_fail: bool = False) -> bool:
    name, script, desc = STEPS[step_num]
    print(f"\n{'='*62}")
    print(f"  STEP {step_num}/4 — {desc.upper()}")
    print(f"  Script: {script}")
    print(f"{'='*62}\n")

    if not Path(script).exists():
        print(f"  ❌ Script not found: {script}")
        return False

    result = subprocess.run([sys.executable, script])

    if result.returncode != 0:
        if skip_on_fail:
            print(f"\n  ⚠️  Step {step_num} failed — continuing anyway.")
            return False
        else:
            print(f"\n  ❌ Step {step_num} failed. Stopping.")
            print(f"  Fix the error above, then re-run:")
            print(f"    python run_training.py --start-from {step_num}")
            sys.exit(1)

    print(f"\n  ✅ Step {step_num} complete.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Civil Registry NER Training Pipeline")
    parser.add_argument("--skip-funsd",   action="store_true",
                        help="Skip FUNSD integration (Step 2), use civil registry only")
    parser.add_argument("--start-from",  type=int, default=1, metavar="N",
                        help="Start from step N (1-4). Default: 1")
    parser.add_argument("--only",        type=int, metavar="N",
                        help="Run only step N")
    args = parser.parse_args()

    print("\n" + "=" * 62)
    print("  CIVIL REGISTRY NER — COMPLETE TRAINING PIPELINE")
    print("=" * 62)
    print("\n  Dataset sources:")
    print("  ┌─ FUNSD original  (149 train, 50 test forms)")
    print("  ├─ FUNSD+          (improved labels, HuggingFace)")
    print("  └─ Civil Registry  (101 annotated examples)")
    print("\n  FUNSD teaches: form structure (questions, answers, headers)")
    print("  Civil Registry teaches: F102_*, F103_*, F97_*, F90_* labels")

    # Check FUNSD zip location
    funsd_zip_found = any([
        Path("data/funsd/dataset.zip").exists(),
        Path("dataset.zip").exists(),
        (Path.home() / "Downloads" / "dataset.zip").exists(),
    ])

    if not funsd_zip_found and not args.skip_funsd:
        print("\n  ⚠️  FUNSD dataset.zip not found in expected locations.")
        print("  → Download: https://guillaumejaume.github.io/FUNSD/download/")
        print("  → Place at: data/funsd/dataset.zip")
        print("  → Or run:   python run_training.py --skip-funsd")
        print()

    # Determine which steps to run
    if args.only:
        steps_to_run = [args.only]
    else:
        steps_to_run = list(range(args.start_from, 5))
        if args.skip_funsd and 2 in steps_to_run:
            steps_to_run.remove(2)

    print(f"\n  Steps to run: {steps_to_run}")

    for step in steps_to_run:
        if step not in STEPS:
            print(f"  ❌ Invalid step: {step}")
            continue
        # Step 2 (FUNSD) is allowed to fail without stopping everything
        skip_fail = (step == 2)
        run_step(step, skip_on_fail=skip_fail)

    print("\n" + "=" * 62)
    print("  PIPELINE COMPLETE")
    print("=" * 62)
    print("\n  Model location: models/civil_registry_model/model-best/")
    print("\n  Update your app:")
    print("    MODEL_PATH = 'models/civil_registry_model/model-best'")
    print()


if __name__ == "__main__":
    main()
