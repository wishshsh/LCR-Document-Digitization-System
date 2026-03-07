# training/evaluate.py
# ============================================================
# STEP 4 of 4 — EVALUATE THE TRAINED MODEL
# ============================================================
# Uses CIVIL REGISTRY dev.spacy only (not merged_dev.spacy)
# so scores reflect actual civil label performance.
# ============================================================

import spacy, subprocess, sys, json
from pathlib import Path

MODEL_PATH = "./models/civil_registry_model/model-best"

# ── Visual test cases (civil registry forms) ───────────────
TEST = [
    {
        "form": "Form 102 — Birth Certificate",
        "text": (
            "Registry No.: 2024-001\n"
            "1. NAME (First): Ana  (Middle): Garcia  (Last): Reyes\n"
            "2. SEX: Female\n"
            "3. DATE OF BIRTH: August 21, 1995\n"
            "4. PLACE OF BIRTH: Pasig City\n"
            "7. MAIDEN NAME (First): Gloria  (Middle): Santos  (Last): Garcia\n"
            "8. CITIZENSHIP: Filipino\n"
            "14. NAME (First): Ramon  (Middle): Cruz  (Last): Reyes\n"
            "15. CITIZENSHIP: Filipino"
        ),
        "expected": [
            "F102_CHILD_FIRST", "F102_CHILD_MIDDLE", "F102_CHILD_LAST",
            "F102_SEX", "F102_DATE_OF_BIRTH", "F102_PLACE_OF_BIRTH",
            "F102_MOTHER_FIRST", "F102_FATHER_FIRST",
        ],
    },
    {
        "form": "Form 103 — Death Certificate",
        "text": (
            "1. NAME (First): Fernando  (Middle): Santos  (Last): Cruz\n"
            "2. SEX: Male\n"
            "4. AGE: 70\n"
            "5. PLACE OF DEATH: PGH Manila\n"
            "6. DATE OF DEATH: March 3, 2023\n"
            "Immediate cause: Renal Failure"
        ),
        "expected": [
            "F103_DECEASED_FIRST", "F103_DECEASED_MIDDLE", "F103_DECEASED_LAST",
            "F103_SEX", "F103_AGE", "F103_PLACE_OF_DEATH",
            "F103_DATE_OF_DEATH", "F103_CAUSE_IMMEDIATE",
        ],
    },
    {
        "form": "Form 97 — Marriage Certificate",
        "text": (
            "Husband (First): Miguel  (Middle): Santos  (Last): dela Cruz\n"
            "Wife   (First): Sofia   (Middle): Tan     (Last): Lim\n"
            "16. DATE OF MARRIAGE: December 12, 2021\n"
            "15. PLACE OF MARRIAGE: Taguig City\n"
            "Husband Age: 31   Wife Age: 28\n"
            "Husband Citizenship: Filipino   Wife Citizenship: Filipino"
        ),
        "expected": [
            "F97_HUSBAND_FIRST", "F97_HUSBAND_MIDDLE", "F97_HUSBAND_LAST",
            "F97_HUSBAND_AGE", "F97_HUSBAND_CITIZENSHIP",
            "F97_WIFE_FIRST", "F97_WIFE_MIDDLE", "F97_WIFE_LAST",
            "F97_WIFE_AGE", "F97_WIFE_CITIZENSHIP",
            "F97_DATE_OF_MARRIAGE", "F97_PLACE_OF_MARRIAGE",
        ],
    },
    {
        "form": "Form 90 — Marriage License (Groom + Bride)",
        "text": (
            "Registry No.: 2024-BC-001\n"
            "ML Date of Registration: January 10, 2024\n"
            "GROOM\n"
            "Groom (First): Jose\n"
            "Groom (Middle): Santos\n"
            "Groom (Last): Ramos\n"
            "Groom Date of Birth: March 15, 1995\n"
            "Groom Age: 39\n"
            "Groom Place of Birth: Manila\n"
            "Groom Sex: Male\n"
            "Groom Citizenship: Filipino\n"
            "Groom Father (First): Pedro\n"
            "Groom Father (Middle): dela Cruz\n"
            "Groom Father (Last): Villanueva\n"
            "Groom Father Citizenship: Filipino\n"
            "Groom Mother (First): Lourdes\n"
            "Groom Mother (Middle): Reyes\n"
            "Groom Mother (Last): Bautista\n"
            "Groom Mother Citizenship: Filipino\n"
            "BRIDE\n"
            "Bride (First): Maria\n"
            "Bride (Middle): Garcia\n"
            "Bride (Last): Torres\n"
            "Bride Date of Birth: August 3, 1995\n"
            "Bride Age: 35\n"
            "Bride Place of Birth: Quezon City\n"
            "Bride Sex: Female\n"
            "Bride Citizenship: Filipino\n"
            "Bride Father (First): Eduardo\n"
            "Bride Father (Middle): Mendoza\n"
            "Bride Father (Last): Aquino\n"
            "Bride Father Citizenship: Filipino\n"
            "Bride Mother (First): Gloria\n"
            "Bride Mother (Middle): Santos\n"
            "Bride Mother (Last): Lopez\n"
            "Bride Mother Citizenship: Filipino"
        ),
        "expected": [
            "F90_REGISTRY_NO", "F90_DATE_OF_REGISTRATION",
            "F90_GROOM_FIRST", "F90_GROOM_LAST",
            "F90_GROOM_DATE_OF_BIRTH", "F90_GROOM_AGE",
            "F90_GROOM_PLACE_OF_BIRTH", "F90_GROOM_SEX", "F90_GROOM_CITIZENSHIP",
            "F90_GROOM_FATHER_FIRST", "F90_GROOM_MOTHER_FIRST",
            "F90_BRIDE_FIRST", "F90_BRIDE_LAST",
            "F90_BRIDE_DATE_OF_BIRTH", "F90_BRIDE_AGE",
            "F90_BRIDE_PLACE_OF_BIRTH", "F90_BRIDE_SEX", "F90_BRIDE_CITIZENSHIP",
            "F90_BRIDE_FATHER_FIRST", "F90_BRIDE_MOTHER_FIRST",
        ],
    },
]


def visual_test(nlp):
    print("=" * 62)
    print("  VISUAL TEST — Does the model find the right labels?")
    print("=" * 62)

    total_correct = 0
    total_expected = 0

    for case in TEST:
        doc   = nlp(case["text"])
        found = {ent.label_: ent.text for ent in doc.ents}
        extra = {l: t for l, t in found.items()
                 if l not in case["expected"]}

        print(f"\n  {case['form']}")
        print(f"  {'─'*56}")

        correct = 0
        for label in case["expected"]:
            if label in found:
                print(f"  ✅  {label:<35} = '{found[label]}'")
                correct += 1
            else:
                print(f"  ❌  {label:<35} ← NOT FOUND")

        if extra:
            print(f"  {'·'*56}")
            for label, text in list(extra.items())[:5]:
                print(f"  ⚠️   {label:<35} = '{text}'  (extra)")

        pct = correct / len(case["expected"]) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        grade = "GOOD" if pct >= 70 else "PARTIAL" if pct >= 40 else "POOR"
        print(f"\n  [{bar}] {pct:.0f}%  {grade}  ({correct}/{len(case['expected'])})")

        total_correct  += correct
        total_expected += len(case["expected"])

    overall = total_correct / total_expected * 100
    bar = "█" * int(overall / 5) + "░" * (20 - int(overall / 5))

    print(f"\n{'=' * 62}")
    print(f"  OVERALL: [{bar}] {overall:.0f}%  ({total_correct}/{total_expected})")
    if overall >= 70:
        print(f"  Grade: ✅ GOOD — model is working well")
    elif overall >= 40:
        print(f"  Grade: ⚠️  PARTIAL — needs more training examples")
    else:
        print(f"  Grade: ❌ POOR — check training pipeline")
    print(f"{'=' * 62}")

    return overall


def spacy_eval(model_path):
    """Run official spaCy evaluate on civil-only dev.spacy."""
    dev   = Path("data/training/dev.spacy")
    if not dev.exists():
        print(f"\n  ⚠️  dev.spacy not found — skipping spaCy eval")
        print(f"  → Run: python training/prepare_data.py")
        return

    print(f"\n{'=' * 62}")
    print(f"  spaCy OFFICIAL EVAL — civil registry labels only")
    print(f"  Dev file: {dev}  (civil registry, NOT merged)")
    print(f"{'=' * 62}\n")

    result = subprocess.run([
        sys.executable, "-m", "spacy", "evaluate",
        str(model_path), str(dev),
        "--output", "data/training/eval_results.json",
    ])

    # Parse and show only civil labels (not FORM_*)
    results_file = Path("data/training/eval_results.json")
    if results_file.exists():
        data = json.loads(results_file.read_text())
        per_type = data.get("ents_per_type", {})

        civil = {k: v for k, v in per_type.items()
                 if not k.startswith("FORM_")}
        funsd  = {k: v for k, v in per_type.items()
                  if k.startswith("FORM_")}

        if civil:
            print(f"\n  CIVIL REGISTRY LABELS (what matters):")
            print(f"  {'Label':<35} {'P':>6} {'R':>6} {'F':>6}")
            print(f"  {'─'*57}")
            any_nonzero = False
            for label, scores in sorted(civil.items()):
                f = scores.get("f", 0)
                p = scores.get("p", 0)
                r = scores.get("r", 0)
                flag = "" if f > 0 else "  ← ❌ 0%"
                if f > 0:
                    any_nonzero = True
                print(f"  {label:<35} {p:>6.1f} {r:>6.1f} {f:>6.1f}{flag}")

            if not any_nonzero:
                print(f"\n  ❌ ALL civil labels are 0% — Phase 2 fine-tuning needed")
                print(f"  → Run: python training/train.py  (two-phase training)")

        if funsd:
            avg_f = sum(v.get("f", 0) for v in funsd.values()) / len(funsd)
            print(f"\n  FUNSD LABELS (background learning): avg F={avg_f:.1f}%")


if __name__ == "__main__":
    model_path = Path(MODEL_PATH)

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Run: python training/train.py")
        sys.exit(1)

    print(f"\n  Loading model: {model_path}\n")
    nlp = spacy.load(str(model_path))

    overall = visual_test(nlp)
    spacy_eval(model_path)

    print(f"\n  Results saved → data/training/eval_results.json")
