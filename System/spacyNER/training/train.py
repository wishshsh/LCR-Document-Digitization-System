# training/train.py
# ============================================================
# STEP 3 of 4 — TWO-PHASE TRAINING
# ============================================================
#
# WHY TWO PHASES?
#   The merged approach FAILED because:
#   - FUNSD has ~1000 docs  → ~15,000 FORM_* entities
#   - Civil has   ~80 docs  → ~1,440 F102_/F103_/F97_ entities
#   - 10:1 ratio → model learned FUNSD, ignored civil labels
#
# THE FIX — Two-phase training:
#
#   PHASE 1 — Pretrain on FUNSD only
#     Teaches the model: "documents have questions and answers"
#     General form understanding, spatial layout, field detection
#     Output: models/phase1_funsd/model-best  (intermediate)
#
#   PHASE 2 — Fine-tune on civil registry ONLY
#     Starts from Phase 1 weights (not from scratch)
#     Teaches: F102_CHILD_FIRST, F103_DECEASED_LAST, F97_*, F90_*
#     Lower learn rate (0.0001) — small updates to preserve Phase 1
#     Output: models/civil_registry_model/model-best  (final)
#
# USAGE:
#   python training/train.py
#
# OUTPUT:
#   models/civil_registry_model/model-best/  ← use this in main.py
# ============================================================

import subprocess
import sys
from pathlib import Path


def count_docs(path: str) -> int:
    try:
        import spacy
        from spacy.tokens import DocBin
        nlp = spacy.blank("en")
        return len(list(DocBin().from_disk(path).get_docs(nlp.vocab)))
    except Exception:
        return 0


def ensure_model(package: str) -> bool:
    try:
        import spacy
        spacy.load(package)
        print(f"  ✅ {package} ready")
        return True
    except OSError:
        print(f"  ⬇️  Installing {package}...")
        r = subprocess.run([sys.executable, "-m", "spacy", "download", package],
                           capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"  {'✅' if ok else '❌'} {package} {'installed' if ok else 'FAILED'}")
        return ok


def check_config(cfg: Path):
    if not cfg.exists():
        print(f"\n  ⚙️  Generating {cfg}...")
        r = subprocess.run([
            sys.executable, "-m", "spacy", "init", "config",
            str(cfg), "--lang", "en", "--pipeline", "ner",
            "--optimize", "accuracy"
        ], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ❌ {r.stderr[:300]}")
            sys.exit(1)
        print(f"  ✅ Generated: {cfg}")
    else:
        print(f"  ✅ Config: {cfg}")


def spacy_train(cfg, output_dir, train_path, dev_path,
                vectors=None, init_tok2vec=None,
                dropout=0.35, patience=1000, max_steps=4000,
                accumulate=3, learn_rate=0.001, label=""):
    """Run spacy train with given settings."""

    cmd = [
        sys.executable, "-m", "spacy", "train", str(cfg),
        "--output",      str(output_dir),
        "--paths.train", str(train_path),
        "--paths.dev",   str(dev_path),
        "--training.dropout",             str(dropout),
        "--training.patience",            str(patience),
        "--training.max_steps",           str(max_steps),
        "--training.accumulate_gradient", str(accumulate),
    ]

    if vectors:
        cmd += ["--initialize.vectors", vectors]
    if init_tok2vec:
        cmd += ["--paths.init_tok2vec", str(init_tok2vec)]
    if learn_rate:
        cmd += ["--training.optimizer.learn_rate", str(learn_rate)]

    print(f"\n  dropout={dropout}  patience={patience}  "
          f"max_steps={max_steps}  accumulate={accumulate}"
          + (f"  lr={learn_rate}" if learn_rate else ""))

    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\n  ❌ Training failed [{label}]")
        sys.exit(1)

    best = Path(output_dir) / "model-best"
    print(f"\n  ✅ [{label}] saved → {best}")
    return best


def run():
    print("=" * 62)
    print("  STEP 3 of 4 — TWO-PHASE NER TRAINING")
    print("=" * 62)
    print()
    print("  Phase 1: FUNSD pretrain   → general form understanding")
    print("  Phase 2: Civil fine-tune  → F102_*, F103_*, F97_*, F90_*")

    # ── Paths ──────────────────────────────────────────────
    cfg = Path("training/config.cfg")

    funsd_train = Path("data/training/funsd_train.spacy")
    funsd_dev   = Path("data/training/funsd_dev.spacy")
    civil_train = Path("data/training/train.spacy")
    civil_dev   = Path("data/training/dev.spacy")

    phase1_out  = Path("models/phase1_funsd")
    phase2_out  = Path("models/civil_registry_model")

    # ── Checks ─────────────────────────────────────────────
    check_config(cfg)

    print("\n  Checking vectors...")
    vectors = "en_core_web_md" if ensure_model("en_core_web_md") else "en_core_web_sm"
    if vectors == "en_core_web_sm":
        ensure_model("en_core_web_sm")

    # ── Verify data exists ─────────────────────────────────
    missing = []
    for p, name in [(civil_train, "train.spacy"), (civil_dev, "dev.spacy")]:
        if not p.exists():
            missing.append(name)
    if missing:
        print(f"\n  ❌ Missing civil registry data: {missing}")
        print("  → Run: python training/prepare_data.py")
        sys.exit(1)

    has_funsd = funsd_train.exists() and funsd_dev.exists()
    if not has_funsd:
        print("\n  ⚠️  FUNSD data not found — skipping Phase 1")
        print("  → Run: python training/funsd_integration.py to add FUNSD")
        print("  → Continuing with civil registry only (Phase 2 only)\n")

    # ── Data sizes ─────────────────────────────────────────
    n_funsd = count_docs(str(funsd_train)) if has_funsd else 0
    n_civil = count_docs(str(civil_train))

    print(f"\n  {'─'*58}")
    print(f"  {'Dataset':<30} {'Train':>6}  {'Dev':>6}")
    print(f"  {'─'*58}")
    if has_funsd:
        print(f"  {'FUNSD (Phase 1 pretrain)':<30} {n_funsd:>6}  "
              f"{count_docs(str(funsd_dev)):>6}")
    print(f"  {'Civil registry (Phase 2)':<30} {n_civil:>6}  "
          f"{count_docs(str(civil_dev)):>6}")
    print(f"  {'─'*58}")

    phase1_out.mkdir(parents=True, exist_ok=True)
    phase2_out.mkdir(parents=True, exist_ok=True)

    # ══════════════════════════════════════════════════════
    # PHASE 1 — FUNSD PRETRAIN
    # ══════════════════════════════════════════════════════
    if has_funsd:
        print(f"\n{'=' * 62}")
        print(f"  PHASE 1 — FUNSD PRETRAIN")
        print(f"  Goal: learn general form structure (questions/answers)")
        print(f"  Docs: {n_funsd} train")
        print(f"{'=' * 62}")

        phase1_best = spacy_train(
            cfg         = cfg,
            output_dir  = phase1_out,
            train_path  = funsd_train,
            dev_path    = funsd_dev,
            vectors     = vectors,
            dropout     = 0.3,       # moderate dropout for pretrain
            patience    = 800,       # stop early — we don't need perfect FUNSD score
            max_steps   = 3000,      # short — just enough to learn form structure
            accumulate  = 2,
            label       = "Phase 1 FUNSD",
        )

        # The tok2vec weights from Phase 1 are what we transfer
        phase1_tok2vec = phase1_best / "tok2vec"
        if not phase1_tok2vec.exists():
            # spaCy stores tok2vec inside the model directory
            phase1_tok2vec = None
            print("  ℹ️  tok2vec transfer not available — Phase 2 starts fresh")
        else:
            print(f"  ✅ tok2vec weights ready for transfer: {phase1_tok2vec}")
    else:
        phase1_tok2vec = None

    # ══════════════════════════════════════════════════════
    # PHASE 2 — CIVIL REGISTRY FINE-TUNE
    # ══════════════════════════════════════════════════════
    print(f"\n{'=' * 62}")
    print(f"  PHASE 2 — CIVIL REGISTRY FINE-TUNE")
    print(f"  Goal: learn F102_*, F103_*, F97_*, F90_* labels")
    print(f"  Docs: {n_civil} train")
    if has_funsd:
        print(f"  Starting from: Phase 1 weights (transfer learning)")
    else:
        print(f"  Starting from: {vectors} vectors (no Phase 1)")
    print(f"{'=' * 62}")

    phase2_best = spacy_train(
        cfg         = cfg,
        output_dir  = phase2_out,
        train_path  = civil_train,
        dev_path    = civil_dev,
        vectors     = vectors,
        # Normal learn rate — 70 new labels need full gradient updates
        learn_rate  = 0.001,
        # Higher dropout — civil dataset is only 80 docs
        dropout     = 0.35,
        # patience=3000 with eval_frequency=50 → 60 evals before stopping
        # = allows ~36 epochs of no improvement before giving up
        # (config.cfg sets eval_frequency=50)
        patience    = 3000,
        # 10000 steps = ~125 epochs on 80 docs — enough to find the pattern
        max_steps   = 10000,
        accumulate  = 4,
        label       = "Phase 2 Civil Registry",
    )

    # ══════════════════════════════════════════════════════
    # DONE
    # ══════════════════════════════════════════════════════
    print(f"\n{'=' * 62}")
    print(f"  ✅ TWO-PHASE TRAINING COMPLETE")
    print(f"{'=' * 62}")
    if has_funsd:
        print(f"\n  Phase 1 (FUNSD):          {phase1_out}/model-best/")
    print(f"  Phase 2 (Final model):    {phase2_out}/model-best/  ← USE THIS")
    print(f"\n  NEXT:  python training/evaluate.py")
    print(f"\n  In main.py:")
    print(f"    MODEL_PATH = 'models/civil_registry_model/model-best'")


if __name__ == "__main__":
    run()
