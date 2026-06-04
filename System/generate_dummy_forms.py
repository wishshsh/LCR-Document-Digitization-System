"""
generate_dummy_forms.py
=======================
Generates dummy-filled civil registry forms by overlaying
handwritten-style text onto the ACTUAL blank PDF form templates.

Coordinates measured directly from grid images (200 DPI render).
  Form 102: 1700 x 2800 px
  Form 103: 1700 x 2600 px
  Form  97: 1700 x 2600 px
  Form  90: 1700 x 2600 px

Usage:
    python generate_dummy_forms.py
"""

import os, random
import fitz
from PIL import Image, ImageDraw, ImageFont

OUT_DIR   = "dummy_forms"
FORMS_DIR = "CRNN+CTC"
os.makedirs(OUT_DIR, exist_ok=True)

PDF_102 = os.path.join(FORMS_DIR, "FORM 102 (BIRTH CERTIFICATE).pdf")
PDF_103 = os.path.join(FORMS_DIR, "FORM 103 (DEATH CERTIFICATE).pdf")
PDF_97  = os.path.join(FORMS_DIR, "FORM 97 (MARRIAGE CERTIFICATE).pdf")
PDF_90  = os.path.join(FORMS_DIR, "FORM 90-MARRIAGE-LICENCE-FORM.pdf")

HW_FONT = "C:/Windows/Fonts/Inkfree.ttf"

def get_font(size):
    try:    return ImageFont.truetype(HW_FONT, size)
    except: return ImageFont.load_default()

# ── Filipino dummy data ──────────────────────────────────────────────────────
FM  = ["Juan","Pedro","Jose","Carlos","Roberto","Eduardo","Miguel","Antonio","Ramon","Fernando","Andres","Ricardo"]
FF  = ["Maria","Rosa","Elena","Luisa","Carmen","Gloria","Lourdes","Felicitas","Conchita","Remedios","Natividad","Cristina"]
MID = ["dela Cruz","Reyes","Santos","Garcia","Lopez","Mendoza","Torres","Aquino","Bautista","Villanueva","Castro","Ramos"]
LN  = ["Santos","Reyes","Cruz","Garcia","Mendoza","Torres","Lopez","Ramos","Bautista","Aquino","Villanueva","Castro"]
CTY = ["Tarlac City","Makati City","Quezon City","Manila","Caloocan","Pasig City","Marikina City","Malabon"]
PRV = ["Tarlac","Metro Manila","Cavite","Laguna","Bulacan","Pampanga","Rizal","Batangas"]
HSP = ["Tarlac Provincial Hospital","Ospital ng Maynila","Philippine General Hospital",
       "Quezon City Medical Center","San Juan de Dios Hospital","Capitol Medical Center"]
REL = ["Roman Catholic","Iglesia ni Cristo","Protestant","Born Again Christian"]
OCC = ["Farmer","Teacher","Engineer","Driver","Housewife","Businessman","Carpenter","Nurse","Laborer"]
CST = ["Single","Married","Widowed"]
MON = ["January","February","March","April","May","June",
       "July","August","September","October","November","December"]
VEN = ["Saint Joseph Parish","City Hall","San Sebastian Cathedral","Sto. Nino Parish","Saint Peter Parish"]
COD = ["Cardiopulmonary Arrest","Pneumonia","Myocardial Infarction","Renal Failure","Sepsis"]

rm  = lambda: random.choice(FM)
rf  = lambda: random.choice(FF)
rmd = lambda: random.choice(MID)
rln = lambda: random.choice(LN)
rc  = lambda: random.choice(CTY)
rp  = lambda: random.choice(PRV)
rd  = lambda: str(random.randint(1, 28))
rmo = lambda: random.choice(MON)
ry  = lambda s=1960, e=2005: str(random.randint(s, e))
rrn = lambda pfx: f"{random.randint(2020,2025)}-{pfx}-{random.randint(1000,9999):05d}"

# ── Core helpers ─────────────────────────────────────────────────────────────
def pdf_to_image(pdf_path, dpi=200):
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = doc[0].get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img

X_OFFSET = 170  # shift all fields right — increase if still too far left


def hw(draw, x, y, text, size=20, color="#1a1a6e"):
    font = get_font(size)
    ox = random.randint(-1, 1)
    oy = random.randint(-1, 1)
    draw.text((x + X_OFFSET + ox, y+oy), str(text), fill=color, font=font)

def save(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path, dpi=(200, 200))
    print(f"  Saved: {path}")


# ══════════════════════════════════════════════════════════════════════════════
#  FORM 102 — Certificate of Live Birth  (1700 x 2800)
# ══════════════════════════════════════════════════════════════════════════════
def generate_form_102(n):
    img, draw = pdf_to_image(PDF_102), None
    draw = ImageDraw.Draw(img)

    def f(x, y, text, size=20): hw(draw, x, y, text, size)

    # ── Header ──────────────────────────────────────────────────
    f(178, 322, rp())                          # Province
    f(1255, 322, rrn("BC"))                    # Registry No
    f(178, 370, rc())                          # City/Municipality

    # ── CHILD ───────────────────────────────────────────────────
    f(205, 438, rm())                          # 1. NAME First
    f(600, 438, rmd())                         #    Middle
    f(1060, 438, rln())                        #    Last

    f(205, 495, random.choice(["Male","Female"]))  # 2. SEX
    f(585, 495, rd())                          # 3. DATE OF BIRTH Day
    f(742, 495, rmo())                         #    Month
    f(975, 495, ry(1970,2024))                 #    Year

    f(295, 552, random.choice(HSP))            # 4. PLACE OF BIRTH Hospital
    f(738, 552, rc())                          #    City
    f(1120, 552, rp())                         #    Province

    f(205, 603, "Single")                      # 5a. TYPE OF BIRTH
    f(900, 603, "First")                       # 5c. BIRTH ORDER

    # ── MOTHER ──────────────────────────────────────────────────
    f(205, 695, rf())                          # 7. MAIDEN NAME First
    f(600, 695, rmd())                         #    Middle
    f(1060, 695, rln())                        #    Last

    f(205, 752, "Filipino")                    # 8. CITIZENSHIP
    f(685, 752, random.choice(REL))            # 9. RELIGION

    f(645, 810, random.choice(OCC))            # 11. OCCUPATION
    f(1415, 810, str(random.randint(20,50)))   # 12. AGE

    f(295, 870, f"{random.randint(1,999)} Rizal St., Brgy. San Antonio")  # 13. RESIDENCE
    f(738, 870, rc())
    f(1120, 870, rp())

    # ── FATHER ──────────────────────────────────────────────────
    f(205, 985, rm())                          # 14. NAME First
    f(600, 985, rmd())                         #     Middle
    f(1060, 985, rln())                        #     Last

    f(205, 1048, "Filipino")                   # 15. CITIZENSHIP
    f(425, 1048, random.choice(REL))           # 16. RELIGION
    f(785, 1048, random.choice(OCC))           # 17. OCCUPATION
    f(1415, 1048, str(random.randint(22,55)))  # 18. AGE

    f(295, 1105, f"{random.randint(1,999)} Mabini St., Brgy. Poblacion")  # 19. RESIDENCE
    f(738, 1105, rc())
    f(1120, 1105, rp())

    # ── MARRIAGE OF PARENTS ──────────────────────────────────────
    f(175, 1215, rmo())                        # 20a. DATE Month
    f(385, 1215, rd())                         #       Day
    f(510, 1215, ry(1960,2010))                #       Year
    f(762, 1215, rc())                         # 20b. PLACE City
    f(1062, 1215, rp())                        #       Province

    save(img, f"form_102_{n:03d}.png")


# ══════════════════════════════════════════════════════════════════════════════
#  FORM 103 — Certificate of Death  (1700 x 2600)
# ══════════════════════════════════════════════════════════════════════════════
def generate_form_103(n):
    img  = pdf_to_image(PDF_103)
    draw = ImageDraw.Draw(img)

    def f(x, y, text, size=20): hw(draw, x, y, text, size)

    # ── Header ──────────────────────────────────────────────────
    f(178, 218, rp())                          # Province
    f(1255, 218, rrn("DC"))                    # Registry No
    f(178, 260, rc())                          # City/Municipality

    # ── Row 1 NAME + 2 SEX ──────────────────────────────────────
    f(178, 335, rm())                          # 1. NAME First
    f(535, 335, rmd())                         #    Middle
    f(878, 335, rln())                         #    Last
    f(1325, 335, random.choice(["Male","Female"]))  # 2. SEX

    # ── Row 3 DATE OF DEATH + 4 DATE OF BIRTH + 5 AGE ───────────
    f(178, 418, f"{rd()} {rmo()} {ry(2010,2025)}")  # 3. DATE OF DEATH
    f(618, 418, rd())                          # 4. DATE OF BIRTH Day
    f(712, 418, rmo())                         #    Month
    f(830, 418, ry(1930,1990))                 #    Year
    f(1055, 418, str(random.randint(30,90)))   # 5. AGE

    # ── Row 6 PLACE OF DEATH + 7 CIVIL STATUS ───────────────────
    f(178, 480, f"{random.choice(HSP)}, {rc()}")    # 6. PLACE OF DEATH
    f(1255, 480, random.choice(CST))           # 7. CIVIL STATUS

    # ── Row 8 RELIGION + 9 CITIZENSHIP + 10 RESIDENCE ───────────
    f(178, 548, random.choice(REL))            # 8. RELIGION
    f(555, 548, "Filipino")                    # 9. CITIZENSHIP
    f(818, 548, f"{random.randint(1,999)} Rizal St., {rc()}")  # 10. RESIDENCE

    # ── Row 11 OCCUPATION + 12 FATHER + 13 MOTHER ───────────────
    f(178, 628, random.choice(OCC))            # 11. OCCUPATION
    f(428, 628, f"{rm()} {rmd()} {rln()}")     # 12. NAME OF FATHER
    f(1028, 628, f"{rf()} {rmd()} {rln()}")    # 13. MAIDEN NAME OF MOTHER

    # ── 19b CAUSES OF DEATH ──────────────────────────────────────
    f(368, 905, random.choice(COD))            # Immediate cause
    f(368, 953, random.choice(["Hypertensive CVD","COPD","Septicemia"]))   # Antecedent
    f(368, 1003, random.choice(["Hypertension","Diabetes Mellitus","Old Age"]))  # Underlying

    save(img, f"form_103_{n:03d}.png")


# ══════════════════════════════════════════════════════════════════════════════
#  FORM 97 — Certificate of Marriage  (1700 x 2600)
# ══════════════════════════════════════════════════════════════════════════════
def generate_form_97(n):
    img  = pdf_to_image(PDF_97)
    draw = ImageDraw.Draw(img)

    def f(x, y, text, size=20): hw(draw, x, y, text, size)

    # ── Header ──────────────────────────────────────────────────
    f(178, 242, rp())                          # Province
    f(1385, 242, rrn("MC"))                    # Registry No
    f(178, 282, rc())                          # City/Municipality

    # ── Row 1 NAME ───────────────────────────────────────────────
    # HUSBAND                                  # WIFE
    f(178, 372, rm());     f(892, 372, rf())   # First
    f(178, 410, rmd());    f(892, 410, rmd())  # Middle
    f(178, 448, rln());    f(892, 448, rln())  # Last

    # ── Row 2a DATE OF BIRTH / 2b AGE ───────────────────────────
    h_dob_y = ry(1975, 2000)
    w_dob_y = ry(1975, 2000)
    h_age   = str(random.randint(18,45))
    w_age   = str(random.randint(18,45))

    f(178, 493, rd());     f(892, 493, rd())   # Day
    f(308, 493, rmo());    f(1022, 493, rmo()) # Month
    f(478, 493, h_dob_y);  f(1188, 493, w_dob_y)  # Year
    f(635, 493, h_age);    f(1348, 493, w_age) # Age

    # ── Row 3 PLACE OF BIRTH ─────────────────────────────────────
    f(178, 548, rc());     f(892, 548, rc())   # City
    f(418, 548, rp());     f(1122, 548, rp())  # Province

    # ── Row 4a SEX / 4b CITIZENSHIP ─────────────────────────────
    f(178, 618, "Male");   f(892, 618, "Female")
    f(352, 618, "Filipino"); f(1062, 618, "Filipino")

    # ── Row 5 RESIDENCE ──────────────────────────────────────────
    f(178, 672, f"{random.randint(1,999)} Rizal St., {rc()}, {rp()}")
    f(892, 672, f"{random.randint(1,999)} Mabini St., {rc()}, {rp()}")

    # ── Row 6 RELIGION ───────────────────────────────────────────
    f(178, 768, random.choice(REL));  f(892, 768, random.choice(REL))

    # ── Row 7 CIVIL STATUS ───────────────────────────────────────
    f(178, 835, "Single");  f(892, 835, "Single")

    # ── Row 8 NAME OF FATHER ─────────────────────────────────────
    f(178, 902, rm());     f(892, 902, rm())   # First
    f(368, 902, rmd());    f(1088, 902, rmd()) # Middle
    f(562, 902, rln());    f(1278, 902, rln()) # Last

    # ── Row 9 CITIZENSHIP (Father) ───────────────────────────────
    f(178, 985, "Filipino");  f(892, 985, "Filipino")

    # ── Row 10 NAME OF MOTHER ────────────────────────────────────
    f(178, 1050, rf());    f(892, 1050, rf())  # First
    f(368, 1050, rmd());   f(1088, 1050, rmd())  # Middle
    f(562, 1050, rln());   f(1278, 1050, rln())  # Last

    # ── Row 11 CITIZENSHIP (Mother) ──────────────────────────────
    f(178, 1138, "Filipino");  f(892, 1138, "Filipino")

    # ── Row 15 PLACE OF MARRIAGE ─────────────────────────────────
    f(222, 1578, random.choice(VEN))           # Office/Church
    f(698, 1578, rc())                         # City
    f(1102, 1578, rp())                        # Province

    # ── Row 16 DATE OF MARRIAGE ──────────────────────────────────
    f(178, 1638, rd())                         # Day
    f(308, 1638, rmo())                        # Month
    f(502, 1638, ry(2015,2025))                # Year
    f(1282, 1638, f"{random.randint(8,11)}:00 {random.choice(['AM','PM'])}")  # 17. TIME

    save(img, f"form_97_{n:03d}.png")


# ══════════════════════════════════════════════════════════════════════════════
#  FORM 90 — Application for Marriage License  (1700 x 2600)
# ══════════════════════════════════════════════════════════════════════════════
def generate_form_90(n):
    img  = pdf_to_image(PDF_90)
    draw = ImageDraw.Draw(img)

    def f(x, y, text, size=20): hw(draw, x, y, text, size)

    # ── Header ──────────────────────────────────────────────────
    f(178, 232, rp())                          # Province
    f(1252, 232, rrn("ML"))                    # Registry No
    f(178, 272, rc())                          # City/Municipality
    f(1002, 308, rrn("LN"))                    # Marriage License No
    f(1002, 348, f"{rmo()} {rd()}, {ry(2023,2025)}")  # Date of Issuance

    # ── 1. NAME OF APPLICANT ─────────────────────────────────────
    # GROOM (left)                             # BRIDE (right)
    f(102, 708, rm());     f(872, 708, rf())   # First
    f(102, 752, rmd());    f(872, 752, rmd())  # Middle
    f(102, 795, rln());    f(872, 795, rln())  # Last

    # ── 2. DATE OF BIRTH / AGE ───────────────────────────────────
    f(102, 835, rd());     f(872, 835, rd())   # Day
    f(228, 835, rmo());    f(998, 835, rmo())  # Month
    f(388, 835, ry(1980,2005)); f(1158, 835, ry(1980,2005))  # Year
    f(568, 835, str(random.randint(18,45))); f(1338, 835, str(random.randint(18,45)))  # Age

    # ── 3. PLACE OF BIRTH ────────────────────────────────────────
    f(102, 882, rc());     f(872, 882, rc())   # City
    f(288, 882, rp());     f(1058, 882, rp())  # Province

    # ── 4. SEX / CITIZENSHIP ─────────────────────────────────────
    f(102, 952, "Male");   f(872, 952, "Female")
    f(268, 952, "Filipino"); f(1038, 952, "Filipino")

    # ── 5. RESIDENCE ─────────────────────────────────────────────
    f(102, 1015, f"{random.randint(1,999)} Rizal St., {rc()}")
    f(872, 1015, f"{random.randint(1,999)} Mabini St., {rc()}")

    # ── 6. RELIGION ──────────────────────────────────────────────
    f(102, 1100, random.choice(REL))
    f(872, 1100, random.choice(REL))

    # ── 7. CIVIL STATUS ──────────────────────────────────────────
    f(102, 1175, "Single");  f(872, 1175, "Single")

    # ── 12. NAME OF FATHER ───────────────────────────────────────
    f(102, 1562, rm());    f(872, 1562, rm())  # First
    f(272, 1562, rmd());   f(1042, 1562, rmd()) # Middle
    f(462, 1562, rln());   f(1232, 1562, rln()) # Last

    # ── 13. CITIZENSHIP (Father) ─────────────────────────────────
    f(102, 1642, "Filipino");  f(872, 1642, "Filipino")

    # ── 15. MAIDEN NAME OF MOTHER ────────────────────────────────
    f(102, 1762, rf());    f(872, 1762, rf())  # First
    f(272, 1762, rmd());   f(1042, 1762, rmd()) # Middle
    f(462, 1762, rln());   f(1232, 1762, rln()) # Last

    # ── 16. CITIZENSHIP (Mother) ─────────────────────────────────
    f(102, 1842, "Filipino");  f(872, 1842, "Filipino")

    save(img, f"form_90_{n:03d}.png")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    COUNT = 1  # ← set to 30 when alignment is confirmed

    missing = [p for p in [PDF_102, PDF_103, PDF_97, PDF_90] if not os.path.exists(p)]
    if missing:
        print("ERROR: Missing PDF form files:")
        for m in missing: print(f"  {m}")
        exit(1)

    print(f"Generating {COUNT} dummy forms per type ({COUNT*4} total)...")
    print(f"Output: {os.path.abspath(OUT_DIR)}/\n")

    for i in range(1, COUNT + 1):
        print(f"[{i}/{COUNT}]")
        generate_form_102(i)
        generate_form_103(i)
        generate_form_97(i)
        generate_form_90(i)

    print(f"\nDone! {COUNT*4} forms saved to: {os.path.abspath(OUT_DIR)}/")
    print("\nNext: upload dummy_forms/ to Roboflow and annotate field bounding boxes.")
