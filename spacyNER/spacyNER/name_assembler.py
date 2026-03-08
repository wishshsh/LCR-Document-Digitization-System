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
#   "Juan" + "" + "Santos"       → "Juan Santos"
#   "Juan" + "dela Cruz" + "Santos" → "Juan dela Cruz Santos"
# =============================================================

from spacyNER.labels import (
    NAME_GROUPS_102,
    NAME_GROUPS_103,
    NAME_GROUPS_97_HUSBAND,
    NAME_GROUPS_97_WIFE,
    NAME_GROUPS_90,
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
                 middle_label may be None (Form 90 father/mother)

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

def assemble_form_90(extracted: dict) -> dict:
    """Adds: name_of_applicant, name_of_father, maiden_name_of_mother"""
    return assemble_names(extracted, NAME_GROUPS_90)
