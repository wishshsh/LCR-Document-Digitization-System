# =============================================================
# spacyNER/name_assembler.py
# =============================================================
# Joins separate First / Middle / Last name parts extracted
# by spaCy NER into full name strings.
#
# Imports from:   labels.py  (NAME_GROUPS_* lists)
# Called by:      extractor.py  (after raw NER extraction)
#
# Rule: join non-empty parts with a single space.
#   "Juan" + "" + "Santos"          → "Juan Santos"
#   "Juan" + "dela Cruz" + "Santos" → "Juan dela Cruz Santos"
#
# Form 90 NOTE:
#   Form 90 (Accountable Form No. 54) is the Marriage License and
#   Fee Receipt document itself — groom and bride are both on the
#   same document. assemble_form_90_groom / assemble_form_90_bride
#   produce name_of_groom and name_of_bride respectively.
# =============================================================

from spacyNER.labels import (
    NAME_GROUPS_102,
    NAME_GROUPS_103,
    NAME_GROUPS_97_HUSBAND,
    NAME_GROUPS_97_WIFE,
    NAME_GROUPS_90_GROOM,
    NAME_GROUPS_90_BRIDE,
)


def _join(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip())


def assemble_names(extracted: dict, name_groups: list) -> dict:
    """
    Add assembled full-name strings to the extracted dict.

    Parameters
    ----------
    extracted    {F102_CHILD_FIRST: "Juan", ...}
    name_groups  [(first_label, middle_label, last_label, output_field), ...]
                 middle_label may be None

    Returns
    -------
    dict with extra keys:  name_of_child, name_of_mother, ...
    """
    result = dict(extracted)
    for first_lbl, mid_lbl, last_lbl, out_field in name_groups:
        first  = extracted.get(first_lbl, "") or ""
        middle = (extracted.get(mid_lbl, "") or "") if mid_lbl else ""
        last   = extracted.get(last_lbl,  "") or ""
        full   = _join(first, middle, last)
        if full:
            result[out_field] = full
    return result


# ── Convenience wrappers ──────────────────────────────────────

def assemble_form_102(extracted: dict) -> dict:
    """Adds: name_of_child, name_of_mother, name_of_father"""
    return assemble_names(extracted, NAME_GROUPS_102)

def assemble_form_103(extracted: dict) -> dict:
    """Adds: name_of_deceased"""
    return assemble_names(extracted, NAME_GROUPS_103)

def assemble_form_97_husband(extracted: dict) -> dict:
    """Adds: name, name_of_father, name_of_mother  (for husband)"""
    return assemble_names(extracted, NAME_GROUPS_97_HUSBAND)

def assemble_form_97_wife(extracted: dict) -> dict:
    """Adds: name, name_of_father, name_of_mother  (for wife)"""
    return assemble_names(extracted, NAME_GROUPS_97_WIFE)

def assemble_form_90_groom(extracted: dict) -> dict:
    """
    Form 90 / Form 54 — Groom name assembly.
    Adds: name_of_groom
    Uses F90_GROOM_* labels.
    """
    return assemble_names(extracted, NAME_GROUPS_90_GROOM)

def assemble_form_90_bride(extracted: dict) -> dict:
    """
    Form 90 / Form 54 — Bride name assembly.
    Adds: name_of_bride
    Uses F90_BRIDE_* labels.
    """
    return assemble_names(extracted, NAME_GROUPS_90_BRIDE)


# ── Utility: split a full name back into parts ────────────────

def assemble_name(first: str, middle: str, last: str) -> str:
    """Join three name parts into a full name string."""
    return _join(first or "", middle or "", last or "")


def split_full_name(full_name: str):
    """
    Split a full name string into (first, middle, last).
    Used as a spaCy NER fallback when keyword scan misses name parts.

    Returns (first, middle, last) — middle and last may be None.
    """
    if not full_name or not full_name.strip():
        return None, None, None

    parts = full_name.strip().split()

    if len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], None, parts[1]
    else:
        # Everything between first and last is the middle
        return parts[0], " ".join(parts[1:-1]), parts[-1]
