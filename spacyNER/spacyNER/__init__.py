# spacyNER/__init__.py
from spacyNER.extractor      import CivilRegistryNER
from spacyNER.autofill       import AutoFillEngine
from spacyNER.name_assembler import (
    assemble_names,
    assemble_form_102,
    assemble_form_103,
    assemble_form_97_husband,
    assemble_form_97_wife,
    assemble_form_90_groom,   # Form 90 — Male birth cert (Groom)
    assemble_form_90_bride,   # Form 90 — Female birth cert (Bride)
)
from spacyNER.models  import Form1A, Form2A, Form3A, Form90
from spacyNER.labels  import ALL_LABELS
