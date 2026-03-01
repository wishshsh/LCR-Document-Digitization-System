"""
generate_ph_names.py
====================
Run this file ONCE to extract Filipino names from the
names-dataset library and save them to data/ph_names.json.

Install first:
    pip install names-dataset

Usage:
    python generate_ph_names.py

Output:
    data/ph_names.json  <-- used by fix_data.py every run
"""

import json
import os

print("=" * 60)
print("  Filipino Name Extractor  |  names-dataset (PyPI)")
print("=" * 60)

# ── Step 1: Load NameDataset ──────────────────────────────────
print("\n[1/4] Loading NameDataset...")
print("      (This takes 30-60 seconds and needs ~3.2 GB RAM)")

try:
    from names_dataset import NameDataset
    nd = NameDataset()
    print("      OK - Dataset loaded!")
except ImportError:
    print("\n  ERROR: names-dataset is not installed.")
    print("  Fix:   pip install names-dataset")
    exit(1)
except MemoryError:
    print("\n  ERROR: Not enough RAM. Need ~3.2 GB free.")
    exit(1)

# ── Step 2: Extract Filipino FIRST names ─────────────────────
print("\n[2/4] Extracting Filipino first names (Male + Female)...")

ph_male   = nd.get_top_names(n=300, gender='Male',   country_alpha2='PH')
ph_female = nd.get_top_names(n=300, gender='Female', country_alpha2='PH')

# API returns: { 'PH': { 'M': [...] } }
male_first   = ph_male.get('PH',   {}).get('M', [])
female_first = ph_female.get('PH', {}).get('F', [])
all_first    = male_first + female_first

print(f"      Male   first names : {len(male_first)}")
print(f"      Female first names : {len(female_first)}")
print(f"      Total  first names : {len(all_first)}")
print(f"      Sample (male)      : {male_first[:5]}")
print(f"      Sample (female)    : {female_first[:5]}")

# ── Step 3: Extract Filipino LAST names ──────────────────────
print("\n[3/4] Extracting Filipino last names...")

# Debug: print the raw structure so we know what we're working with
ph_last_raw = nd.get_top_names(n=300, country_alpha2='PH', use_first_names=False)
print(f"      Raw last name API type : {type(ph_last_raw)}")

ph_last_ph = ph_last_raw.get('PH', {})
print(f"      PH entry type          : {type(ph_last_ph)}")

# Handle both possible structures the API might return:
#   Structure A: { 'PH': ['Santos', 'Reyes', ...] }          -> list directly
#   Structure B: { 'PH': { 'M': [...], 'F': [...] } }        -> dict of lists
#   Structure C: { 'PH': { 'Santos': {...}, 'Reyes': {...} }} -> dict of dicts

raw_last = []

if isinstance(ph_last_ph, list):
    # Structure A - direct list
    raw_last = ph_last_ph

elif isinstance(ph_last_ph, dict):
    # Peek at first value to figure out structure B vs C
    first_val = next(iter(ph_last_ph.values()), None)

    if isinstance(first_val, list):
        # Structure B - dict of lists e.g. {'M': [...], 'F': [...]}
        for lst in ph_last_ph.values():
            raw_last.extend(lst)

    elif isinstance(first_val, dict):
        # Structure C - dict of dicts, keys ARE the last names
        raw_last = list(ph_last_ph.keys())

    else:
        # Unknown - just take the keys as names
        raw_last = list(ph_last_ph.keys())

# Deduplicate while preserving order
seen     = set()
all_last = []
for name in raw_last:
    if isinstance(name, str) and name not in seen:
        seen.add(name)
        all_last.append(name)

print(f"      Total last names   : {len(all_last)}")
print(f"      Sample             : {all_last[:5]}")

if len(all_last) == 0:
    print("\n  WARNING: Could not extract last names from API.")
    print("  Using common Filipino last names as fallback...")
    all_last = [
        'Santos', 'Reyes', 'Cruz', 'Bautista', 'Ocampo',
        'Garcia', 'Mendoza', 'Torres', 'Flores', 'Aquino',
        'Dela Cruz', 'Del Rosario', 'San Jose', 'De Guzman',
        'Villanueva', 'Gonzales', 'Ramos', 'Diaz', 'Castro',
        'Morales', 'Ortega', 'Gutierrez', 'Lopez', 'Ramirez',
        'Navarro', 'Aguilar', 'Espinosa', 'Mercado', 'Tolentino',
        'Lim', 'Tan', 'Go', 'Chua', 'Sy', 'Ong', 'Co',
        'Macaraeg', 'Macapagal', 'Magsaysay', 'Magno',
        'Pascual', 'Buenaventura', 'Concepcion', 'Resurreccion',
        'Ilagan', 'Manalo', 'Soriano', 'Evangelista', 'Salazar',
    ]
    print(f"      Fallback last names: {len(all_last)}")

# ── Step 4: Save to JSON ──────────────────────────────────────
print("\n[4/4] Saving to data/ph_names.json ...")

os.makedirs('data', exist_ok=True)

output = {
    "first_names": {
        "male":   male_first,
        "female": female_first,
        "all":    all_first
    },
    "last_names": all_last,
    "metadata": {
        "source":       "names-dataset (PyPI) -- country_alpha2='PH'",
        "total_first":  len(all_first),
        "total_last":   len(all_last),
        "total_combos": len(all_first) * len(all_last)
    }
}

with open('data/ph_names.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  DONE!")
print("=" * 60)
print(f"  Male first names   : {len(male_first)}")
print(f"  Female first names : {len(female_first)}")
print(f"  Last names         : {len(all_last)}")
print(f"  Possible combos    : {len(all_first) * len(all_last):,}")
print(f"\n  Saved to: data/ph_names.json")
print(f"\n  Next step: python fix_data.py")
print("=" * 60)
