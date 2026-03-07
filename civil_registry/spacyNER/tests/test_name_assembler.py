# tests/test_name_assembler.py
# Run with: pytest tests/ -v

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spacyNER.name_assembler import assemble_name, split_full_name


# ── assemble_name tests ────────────────────────────────────

def test_assemble_full_name():
    result = assemble_name("Juan", "dela Cruz", "Santos")
    assert result == "Juan dela Cruz Santos"

def test_assemble_no_middle():
    result = assemble_name("Maria", None, "Reyes")
    assert result == "Maria Reyes"

def test_assemble_empty_middle():
    result = assemble_name("Carlos", "", "Mendoza")
    assert result == "Carlos Mendoza"

def test_assemble_all_none():
    result = assemble_name(None, None, None)
    assert result == ""

def test_assemble_strips_whitespace():
    result = assemble_name("  Juan  ", "  dela Cruz  ", "  Santos  ")
    assert result == "Juan dela Cruz Santos"

def test_assemble_first_only():
    result = assemble_name("Jose", None, None)
    assert result == "Jose"

def test_assemble_last_only():
    result = assemble_name(None, None, "Ramos")
    assert result == "Ramos"


# ── split_full_name tests ──────────────────────────────────

def test_split_three_words():
    first, middle, last = split_full_name("Juan dela Santos")
    assert first == "Juan"
    assert middle == "dela"
    assert last == "Santos"

def test_split_four_words():
    first, middle, last = split_full_name("Juan dela Cruz Santos")
    assert first == "Juan"
    assert middle == "dela Cruz"
    assert last == "Santos"

def test_split_two_words():
    first, middle, last = split_full_name("Maria Reyes")
    assert first == "Maria"
    assert middle is None
    assert last == "Reyes"

def test_split_one_word():
    first, middle, last = split_full_name("Carlos")
    assert first == "Carlos"
    assert middle is None
    assert last is None

def test_split_empty():
    first, middle, last = split_full_name("")
    assert first is None
    assert middle is None
    assert last is None

def test_roundtrip():
    """Splitting then assembling should give back the original name."""
    name = "Juan dela Cruz Santos"
    first, middle, last = split_full_name(name)
    result = assemble_name(first, middle, last)
    assert result == name
