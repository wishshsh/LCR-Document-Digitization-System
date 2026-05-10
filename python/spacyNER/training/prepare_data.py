# training/prepare_data.py
# ============================================================
# STEP 1 of 4 — BUILD CIVIL REGISTRY TRAINING DATA
# ============================================================
# 101 annotated examples:
#   27  Form 102 → 1A  (Birth Certificate)
#   27  Form 103 → 2A  (Death Certificate)
#   26  Form 97  → 3A  (Marriage Certificate)
#   21  Form 90      (Marriage License — birth cert source)
#
# OUTPUT:
#   data/training/train.spacy   (80 docs)
#   data/training/dev.spacy     (21 docs)
#
# NEXT STEP:
#   python training/funsd_integration.py
# ============================================================
import spacy
from spacy.tokens import DocBin
from spacy.util   import filter_spans
from pathlib      import Path


def find_clean(text, phrase, start_from=0):
    phrase = phrase.strip()
    i = text.find(phrase, start_from)
    if i == -1:
        return None
    return (i, i + len(phrase))


def make_entities(text, pairs):
    entities = []
    # Track last end position per phrase to handle duplicate values
    # e.g. "Filipino" appears as both MOTHER_CITIZENSHIP and FATHER_CITIZENSHIP
    phrase_last_end = {}
    for phrase, label in pairs:
        phrase_key = phrase.strip()
        start_from = phrase_last_end.get(phrase_key, 0)
        result = find_clean(text, phrase, start_from)
        if result is None:
            # Try from beginning in case ordering is off
            result = find_clean(text, phrase, 0)
        if result is None:
            print(f"  WARNING NOT FOUND: '{phrase}' for {label}")
            continue
        start, end = result
        actual = text[start:end]
        if actual != actual.strip():
            stripped = actual.strip()
            offset = actual.index(stripped)
            start = start + offset
            end   = start + len(stripped)
        # Check for span conflicts with already-added entities
        conflict = False
        for (es, ee, el) in entities:
            if not (end <= es or start >= ee):
                conflict = True
                break
        if conflict:
            # Try finding next occurrence after conflicting span
            result2 = find_clean(text, phrase, end)
            if result2:
                start, end = result2
            else:
                print(f"  WARNING CONFLICT: '{phrase}' for {label} overlaps existing span")
                continue
        phrase_last_end[phrase_key] = end
        entities.append((start, end, label))
    return entities


# ============================================================
# FORM 102 -> FORM 1A (BIRTH CERTIFICATE)
# Labels: REGISTRY_NO, DATE_OF_REGISTRATION, CHILD_FIRST,
#         CHILD_MIDDLE, CHILD_LAST, SEX, DATE_OF_BIRTH,
#         PLACE_OF_BIRTH, MOTHER_FIRST, MOTHER_MIDDLE,
#         MOTHER_LAST, MOTHER_CITIZENSHIP, FATHER_FIRST,
#         FATHER_MIDDLE, FATHER_LAST, FATHER_CITIZENSHIP,
#         MARRIAGE_DATE, MARRIAGE_PLACE
# ============================================================

def form102_examples():
    examples = []

    t = ("BC Registry No.: 2024-BC-001\nBC Date of Registration: January 5, 2024\nCHILD (First): Juan\nCHILD (Middle): dela Cruz\nCHILD (Last): Santos\n2. SEX: Male\n3. Child Date of Birth: March 15, 1990\n4. PLACE OF BIRTH: Makati City\nMother (First): Maria\nMother (Middle): Reyes\nMother (Last): dela Cruz\nMother Citizenship: Filipino\nFather (First): Pedro\nFather (Middle): Cruz\nFather (Last): Santos\nFather Citizenship: Filipino\n20a. DATE: June 10, 1985\n20b. PLACE: Manila")
    examples.append((t, {"entities": make_entities(t, [(("2024-BC-001","F102_REGISTRY_NO")),("January 5, 2024","F102_DATE_OF_REGISTRATION"),("Juan","F102_CHILD_FIRST"),("dela Cruz","F102_CHILD_MIDDLE"),("Santos","F102_CHILD_LAST"),("Male","F102_SEX"),("March 15, 1990","F102_DATE_OF_BIRTH"),("Makati City","F102_PLACE_OF_BIRTH"),("Maria","F102_MOTHER_FIRST"),("Reyes","F102_MOTHER_MIDDLE"),("dela Cruz","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Pedro","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Santos","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP"),("June 10, 1985","F102_MARRIAGE_DATE"),("Manila","F102_MARRIAGE_PLACE")])}))

    t = ("BC Registry No.: 2023-BC-112\nBC Date of Registration: March 2, 2023\nCHILD (First): Ana\nCHILD (Middle): Garcia\nCHILD (Last): Reyes\n2. SEX: Female\n3. Child Date of Birth: August 21, 1995\n4. PLACE OF BIRTH: Pasig City\n5a. TYPE OF BIRTH: Twin\nMother (First): Gloria\nMother (Middle): Santos\nMother (Last): Garcia\nMother Citizenship: Filipino\nFather (First): Ramon\nFather (Middle): Cruz\nFather (Last): Reyes\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2023-BC-112","F102_REGISTRY_NO")),("March 2, 2023","F102_DATE_OF_REGISTRATION"),("Ana","F102_CHILD_FIRST"),("Garcia","F102_CHILD_MIDDLE"),("Reyes","F102_CHILD_LAST"),("Female","F102_SEX"),("August 21, 1995","F102_DATE_OF_BIRTH"),("Pasig City","F102_PLACE_OF_BIRTH"),("Gloria","F102_MOTHER_FIRST"),("Santos","F102_MOTHER_MIDDLE"),("Garcia","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ramon","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Reyes","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2010-BC-089\nBC Date of Registration: December 15, 2010\nCHILD (First): Carlo\nCHILD (Middle): Santos\nCHILD (Last): Lim\n2. SEX: Male\n3. Child Date of Birth: December 1, 2010\n4. PLACE OF BIRTH: Cebu City\nMother (First): Rosa\nMother (Middle): Villanueva\nMother (Last): Santos\nMother Citizenship: Filipino\nFather (First): Bernard\nFather (Middle): Cruz\nFather (Last): Lim\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2010-BC-089","F102_REGISTRY_NO")),("December 15, 2010","F102_DATE_OF_REGISTRATION"),("Carlo","F102_CHILD_FIRST"),("Santos","F102_CHILD_MIDDLE"),("Lim","F102_CHILD_LAST"),("Male","F102_SEX"),("December 1, 2010","F102_DATE_OF_BIRTH"),("Cebu City","F102_PLACE_OF_BIRTH"),("Rosa","F102_MOTHER_FIRST"),("Villanueva","F102_MOTHER_MIDDLE"),("Santos","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Bernard","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Lim","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 1988-BC-045\nBC Date of Registration: July 20, 1988\nCHILD (First): Liza\nCHILD (Middle): Ramos\nCHILD (Last): Delos Santos\n2. SEX: Female\n3. Child Date of Birth: July 7, 1988\n4. PLACE OF BIRTH: Davao City\nMother (First): Perla\nMother (Middle): Aquino\nMother (Last): Ramos\nMother Citizenship: Filipino\nFather (First): Manuel\nFather (Middle): Santos\nFather (Last): Delos Santos\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("1988-BC-045","F102_REGISTRY_NO")),("July 20, 1988","F102_DATE_OF_REGISTRATION"),("Liza","F102_CHILD_FIRST"),("Ramos","F102_CHILD_MIDDLE"),("Delos Santos","F102_CHILD_LAST"),("Female","F102_SEX"),("July 7, 1988","F102_DATE_OF_BIRTH"),("Davao City","F102_PLACE_OF_BIRTH"),("Perla","F102_MOTHER_FIRST"),("Aquino","F102_MOTHER_MIDDLE"),("Ramos","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Manuel","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Delos Santos","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2005-BC-200\nBC Date of Registration: December 10, 2005\nCHILD (First): Sofia\nCHILD (Middle): Mendoza\nCHILD (Last): Santos-Cruz\n2. SEX: Female\n3. Child Date of Birth: November 30, 2005\n4. PLACE OF BIRTH: Quezon City\nMother (First): Carmen\nMother (Middle): Uy\nMother (Last): Mendoza\nMother Citizenship: Filipino\nFather (First): Roberto\nFather (Middle): Cruz\nFather (Last): Santos-Cruz\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2005-BC-200","F102_REGISTRY_NO")),("December 10, 2005","F102_DATE_OF_REGISTRATION"),("Sofia","F102_CHILD_FIRST"),("Mendoza","F102_CHILD_MIDDLE"),("Santos-Cruz","F102_CHILD_LAST"),("Female","F102_SEX"),("November 30, 2005","F102_DATE_OF_BIRTH"),("Quezon City","F102_PLACE_OF_BIRTH"),("Carmen","F102_MOTHER_FIRST"),("Uy","F102_MOTHER_MIDDLE"),("Mendoza","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Roberto","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Santos-Cruz","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2000-BC-011\nBC Date of Registration: January 20, 2000\nCHILD (First): Miguel\nCHILD (Middle): Ocampo\nCHILD (Last): Villanueva\n2. SEX: Male\n3. Child Date of Birth: January 5, 2000\n4. PLACE OF BIRTH: Iloilo City\nMother (First): Rosario\nMother (Middle): de Leon\nMother (Last): Ocampo\nMother Citizenship: Filipino\n14. NAME (First): Eduardo (Middle): dela Cruz (Last): Villanueva\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2000-BC-011","F102_REGISTRY_NO")),("January 20, 2000","F102_DATE_OF_REGISTRATION"),("Miguel","F102_CHILD_FIRST"),("Ocampo","F102_CHILD_MIDDLE"),("Villanueva","F102_CHILD_LAST"),("Male","F102_SEX"),("January 5, 2000","F102_DATE_OF_BIRTH"),("Iloilo City","F102_PLACE_OF_BIRTH"),("Rosario","F102_MOTHER_FIRST"),("de Leon","F102_MOTHER_MIDDLE"),("Ocampo","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Eduardo","F102_FATHER_FIRST"),("dela Cruz","F102_FATHER_MIDDLE"),("Villanueva","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2003-BC-077\nBC Date of Registration: May 25, 2003\nCHILD (First): Kristine\nCHILD (Middle): Bautista\nCHILD (Last): Tan\n2. SEX: Female\n3. Child Date of Birth: May 12, 2003\n4. PLACE OF BIRTH: Taguig City\n5a. TYPE OF BIRTH: Single\n5b. BIRTH ORDER: 2nd\nMother (First): Felicia\nMother (Middle): Sy\nMother (Last): Bautista\nMother Citizenship: Filipino\nFather (First): Ricardo\nFather (Middle): Go\nFather (Last): Tan\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2003-BC-077","F102_REGISTRY_NO")),("May 25, 2003","F102_DATE_OF_REGISTRATION"),("Kristine","F102_CHILD_FIRST"),("Bautista","F102_CHILD_MIDDLE"),("Tan","F102_CHILD_LAST"),("Female","F102_SEX"),("May 12, 2003","F102_DATE_OF_BIRTH"),("Taguig City","F102_PLACE_OF_BIRTH"),("Felicia","F102_MOTHER_FIRST"),("Sy","F102_MOTHER_MIDDLE"),("Bautista","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ricardo","F102_FATHER_FIRST"),("Go","F102_FATHER_MIDDLE"),("Tan","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 1998-BC-156\nBC Date of Registration: November 1, 1998\nCHILD (First): Emmanuel\nCHILD (Middle): dela Paz\nCHILD (Last): Reyes\n2. SEX: Male\n3. Child Date of Birth: October 20, 1998\n4. PLACE OF BIRTH: Manila\nMother (First): Leonora\nMother (Middle): Castillo\nMother (Last): dela Paz\nMother Citizenship: Filipino\nFather (First): Rodrigo\nFather (Middle): Santos\nFather (Last): Reyes\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("1998-BC-156","F102_REGISTRY_NO")),("November 1, 1998","F102_DATE_OF_REGISTRATION"),("Emmanuel","F102_CHILD_FIRST"),("dela Paz","F102_CHILD_MIDDLE"),("Reyes","F102_CHILD_LAST"),("Male","F102_SEX"),("October 20, 1998","F102_DATE_OF_BIRTH"),("Manila","F102_PLACE_OF_BIRTH"),("Leonora","F102_MOTHER_FIRST"),("Castillo","F102_MOTHER_MIDDLE"),("dela Paz","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Rodrigo","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Reyes","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2015-BC-033\nBC Date of Registration: March 10, 2015\nCHILD (First): Patricia\nCHILD (Middle): Gonzales\nCHILD (Last): Lopez\n2. SEX: Female\n3. Child Date of Birth: February 28, 2015\n4. PLACE OF BIRTH: Caloocan City\nMother (First): Maricel\nMother (Middle): Torres\nMother (Last): Gonzales\nMother Citizenship: Filipino\nFather (First): Alfredo\nFather (Middle): Reyes\nFather (Last): Lopez\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2015-BC-033","F102_REGISTRY_NO")),("March 10, 2015","F102_DATE_OF_REGISTRATION"),("Patricia","F102_CHILD_FIRST"),("Gonzales","F102_CHILD_MIDDLE"),("Lopez","F102_CHILD_LAST"),("Female","F102_SEX"),("February 28, 2015","F102_DATE_OF_BIRTH"),("Caloocan City","F102_PLACE_OF_BIRTH"),("Maricel","F102_MOTHER_FIRST"),("Torres","F102_MOTHER_MIDDLE"),("Gonzales","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Alfredo","F102_FATHER_FIRST"),("Reyes","F102_FATHER_MIDDLE"),("Lopez","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2019-BC-044\nBC Date of Registration: April 15, 2019\nCHILD (First): Celine\nCHILD (Middle): Macaraeg\nCHILD (Last): Buenaventura\n2. SEX: Female\n3. Child Date of Birth: April 3, 2019\n4. PLACE OF BIRTH: Batangas City\nMother (First): Anita\nMother (Middle): dela Rosa\nMother (Last): Macaraeg\nMother Citizenship: Filipino\nFather (First): Marcelino\nFather (Middle): Cruz\nFather (Last): Buenaventura\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2019-BC-044","F102_REGISTRY_NO")),("April 15, 2019","F102_DATE_OF_REGISTRATION"),("Celine","F102_CHILD_FIRST"),("Macaraeg","F102_CHILD_MIDDLE"),("Buenaventura","F102_CHILD_LAST"),("Female","F102_SEX"),("April 3, 2019","F102_DATE_OF_BIRTH"),("Batangas City","F102_PLACE_OF_BIRTH"),("Anita","F102_MOTHER_FIRST"),("dela Rosa","F102_MOTHER_MIDDLE"),("Macaraeg","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Marcelino","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Buenaventura","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2008-BC-099\nBC Date of Registration: January 22, 2008\nCHILD (First): Marco\nCHILD (Middle): Santos\nCHILD (Last): Dela Cruz\n2. SEX: Male\n3. Child Date of Birth: January 10, 2008\n4. PLACE OF BIRTH: Marikina City\nMother (First): Nena\nMother (Middle): Reyes\nMother (Last): Santos\nMother Citizenship: Filipino\nFather (First): Victor\nFather (Middle): Cruz\nFather (Last): Dela Cruz\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2008-BC-099","F102_REGISTRY_NO")),("January 22, 2008","F102_DATE_OF_REGISTRATION"),("Marco","F102_CHILD_FIRST"),("Santos","F102_CHILD_MIDDLE"),("Dela Cruz","F102_CHILD_LAST"),("Male","F102_SEX"),("January 10, 2008","F102_DATE_OF_BIRTH"),("Marikina City","F102_PLACE_OF_BIRTH"),("Nena","F102_MOTHER_FIRST"),("Reyes","F102_MOTHER_MIDDLE"),("Santos","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Victor","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Dela Cruz","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2012-BC-134\nBC Date of Registration: September 28, 2012\nCHILD (First): Bianca\nCHILD (Middle): Torres\nCHILD (Last): Navarro\n2. SEX: Female\n3. Child Date of Birth: September 14, 2012\n4. PLACE OF BIRTH: San Juan City\nMother (First): Luisa\nMother (Middle): Magno\nMother (Last): Torres\nMother Citizenship: Filipino\nFather (First): Ernesto\nFather (Middle): Navarro\nFather (Last): Navarro\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2012-BC-134","F102_REGISTRY_NO")),("September 28, 2012","F102_DATE_OF_REGISTRATION"),("Bianca","F102_CHILD_FIRST"),("Torres","F102_CHILD_MIDDLE"),("Navarro","F102_CHILD_LAST"),("Female","F102_SEX"),("September 14, 2012","F102_DATE_OF_BIRTH"),("San Juan City","F102_PLACE_OF_BIRTH"),("Luisa","F102_MOTHER_FIRST"),("Magno","F102_MOTHER_MIDDLE"),("Torres","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ernesto","F102_FATHER_FIRST"),("Navarro","F102_FATHER_MIDDLE"),("Navarro","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2017-BC-021\nBC Date of Registration: February 20, 2017\nCHILD (First): Nathan\nCHILD (Middle): Ramos\nCHILD (Last): Padilla\n2. SEX: Male\n3. Child Date of Birth: February 7, 2017\n4. PLACE OF BIRTH: Muntinlupa City\nMother (First): Carla\nMother (Middle): Abad\nMother (Last): Ramos\nMother Citizenship: Filipino\nFather (First): Dennis\nFather (Middle): Cruz\nFather (Last): Padilla\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2017-BC-021","F102_REGISTRY_NO")),("February 20, 2017","F102_DATE_OF_REGISTRATION"),("Nathan","F102_CHILD_FIRST"),("Ramos","F102_CHILD_MIDDLE"),("Padilla","F102_CHILD_LAST"),("Male","F102_SEX"),("February 7, 2017","F102_DATE_OF_BIRTH"),("Muntinlupa City","F102_PLACE_OF_BIRTH"),("Carla","F102_MOTHER_FIRST"),("Abad","F102_MOTHER_MIDDLE"),("Ramos","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Dennis","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Padilla","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2001-BC-067\nBC Date of Registration: July 15, 2001\nCHILD (First): Joshua\nCHILD (Middle): Bautista\nCHILD (Last): Enriquez\n2. SEX: Male\n3. Child Date of Birth: July 30, 2001\n4. PLACE OF BIRTH: Paranaque City\nMother (First): Natividad\nMother (Middle): Ramos\nMother (Last): Bautista\nMother Citizenship: Filipino\nFather (First): Nestor\nFather (Middle): Flores\nFather (Last): Enriquez\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2001-BC-067","F102_REGISTRY_NO")),("July 15, 2001","F102_DATE_OF_REGISTRATION"),("Joshua","F102_CHILD_FIRST"),("Bautista","F102_CHILD_MIDDLE"),("Enriquez","F102_CHILD_LAST"),("Male","F102_SEX"),("July 30, 2001","F102_DATE_OF_BIRTH"),("Paranaque City","F102_PLACE_OF_BIRTH"),("Natividad","F102_MOTHER_FIRST"),("Ramos","F102_MOTHER_MIDDLE"),("Bautista","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Nestor","F102_FATHER_FIRST"),("Flores","F102_FATHER_MIDDLE"),("Enriquez","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2006-BC-088\nBC Date of Registration: August 20, 2006\nCHILD (First): Renz\nCHILD (Middle): Dela Rosa\nCHILD (Last): Manalo\n2. SEX: Male\n3. Child Date of Birth: August 8, 2006\n4. PLACE OF BIRTH: Navotas City\nMother (First): Florinda\nMother (Middle): Ocampo\nMother (Last): Dela Rosa\nMother Citizenship: Filipino\nFather (First): Ronaldo\nFather (Middle): Cruz\nFather (Last): Manalo\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2006-BC-088","F102_REGISTRY_NO")),("August 20, 2006","F102_DATE_OF_REGISTRATION"),("Renz","F102_CHILD_FIRST"),("Dela Rosa","F102_CHILD_MIDDLE"),("Manalo","F102_CHILD_LAST"),("Male","F102_SEX"),("August 8, 2006","F102_DATE_OF_BIRTH"),("Navotas City","F102_PLACE_OF_BIRTH"),("Florinda","F102_MOTHER_FIRST"),("Ocampo","F102_MOTHER_MIDDLE"),("Dela Rosa","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ronaldo","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Manalo","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2013-BC-111\nBC Date of Registration: November 25, 2013\nCHILD (First): Daniel\nCHILD (Middle): Soriano\nCHILD (Last): Velasco\n2. SEX: Male\n3. Child Date of Birth: November 11, 2013\n4. PLACE OF BIRTH: Bacoor, Cavite\nMother (First): Milagros\nMother (Middle): Santos\nMother (Last): Soriano\nMother Citizenship: Filipino\nFather (First): Rolando\nFather (Middle): Reyes\nFather (Last): Velasco\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2013-BC-111","F102_REGISTRY_NO")),("November 25, 2013","F102_DATE_OF_REGISTRATION"),("Daniel","F102_CHILD_FIRST"),("Soriano","F102_CHILD_MIDDLE"),("Velasco","F102_CHILD_LAST"),("Male","F102_SEX"),("November 11, 2013","F102_DATE_OF_BIRTH"),("Bacoor, Cavite","F102_PLACE_OF_BIRTH"),("Milagros","F102_MOTHER_FIRST"),("Santos","F102_MOTHER_MIDDLE"),("Soriano","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Rolando","F102_FATHER_FIRST"),("Reyes","F102_FATHER_MIDDLE"),("Velasco","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2020-BC-055\nBC Date of Registration: April 30, 2020\nCHILD (First): Jasmine\nCHILD (Middle): Cunanan\nCHILD (Last): Dizon\n2. SEX: Female\n3. Child Date of Birth: April 16, 2020\n4. PLACE OF BIRTH: Angeles City\nMother (First): Rowena\nMother (Middle): dela Cruz\nMother (Last): Cunanan\nMother Citizenship: Filipino\nFather (First): Marvin\nFather (Middle): Santos\nFather (Last): Dizon\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2020-BC-055","F102_REGISTRY_NO")),("April 30, 2020","F102_DATE_OF_REGISTRATION"),("Jasmine","F102_CHILD_FIRST"),("Cunanan","F102_CHILD_MIDDLE"),("Dizon","F102_CHILD_LAST"),("Female","F102_SEX"),("April 16, 2020","F102_DATE_OF_BIRTH"),("Angeles City","F102_PLACE_OF_BIRTH"),("Rowena","F102_MOTHER_FIRST"),("dela Cruz","F102_MOTHER_MIDDLE"),("Cunanan","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Marvin","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Dizon","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2018-BC-022\nBC Date of Registration: February 10, 2018\nCHILD (First): Elijah\nCHILD (Middle): Pascual\nCHILD (Last): Bernardo\n2. SEX: Male\n3. Child Date of Birth: January 29, 2018\n4. PLACE OF BIRTH: San Fernando, Pampanga\nMother (First): Marivic\nMother (Middle): Reyes\nMother (Last): Pascual\nMother Citizenship: Filipino\nFather (First): Danilo\nFather (Middle): Cruz\nFather (Last): Bernardo\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2018-BC-022","F102_REGISTRY_NO")),("February 10, 2018","F102_DATE_OF_REGISTRATION"),("Elijah","F102_CHILD_FIRST"),("Pascual","F102_CHILD_MIDDLE"),("Bernardo","F102_CHILD_LAST"),("Male","F102_SEX"),("January 29, 2018","F102_DATE_OF_BIRTH"),("San Fernando, Pampanga","F102_PLACE_OF_BIRTH"),("Marivic","F102_MOTHER_FIRST"),("Reyes","F102_MOTHER_MIDDLE"),("Pascual","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Danilo","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Bernardo","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2007-BC-143\nBC Date of Registration: October 25, 2007\nCHILD (First): Samantha\nCHILD (Middle): Villanueva\nCHILD (Last): Tolentino\n2. SEX: Female\n3. Child Date of Birth: October 10, 2007\n4. PLACE OF BIRTH: Lipa City\nMother (First): Yolanda\nMother (Middle): Bautista\nMother (Last): Villanueva\nMother Citizenship: Filipino\nFather (First): Aurelio\nFather (Middle): Santos\nFather (Last): Tolentino\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2007-BC-143","F102_REGISTRY_NO")),("October 25, 2007","F102_DATE_OF_REGISTRATION"),("Samantha","F102_CHILD_FIRST"),("Villanueva","F102_CHILD_MIDDLE"),("Tolentino","F102_CHILD_LAST"),("Female","F102_SEX"),("October 10, 2007","F102_DATE_OF_BIRTH"),("Lipa City","F102_PLACE_OF_BIRTH"),("Yolanda","F102_MOTHER_FIRST"),("Bautista","F102_MOTHER_MIDDLE"),("Villanueva","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Aurelio","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Tolentino","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2014-BC-077\nBC Date of Registration: July 18, 2014\nCHILD (First): Adrian\nCHILD (Middle): Espiritu\nCHILD (Last): Reyes\n2. SEX: Male\n3. Child Date of Birth: July 4, 2014\n4. PLACE OF BIRTH: Legazpi City\nMother (First): Nenita\nMother (Middle): Gomez\nMother (Last): Espiritu\nMother Citizenship: Filipino\nFather (First): Eduardo\nFather (Middle): Santos\nFather (Last): Reyes\nFather Citizenship: Filipino")
    examples.append((t, {"entities": make_entities(t, [(("2014-BC-077","F102_REGISTRY_NO")),("July 18, 2014","F102_DATE_OF_REGISTRATION"),("Adrian","F102_CHILD_FIRST"),("Espiritu","F102_CHILD_MIDDLE"),("Reyes","F102_CHILD_LAST"),("Male","F102_SEX"),("July 4, 2014","F102_DATE_OF_BIRTH"),("Legazpi City","F102_PLACE_OF_BIRTH"),("Nenita","F102_MOTHER_FIRST"),("Gomez","F102_MOTHER_MIDDLE"),("Espiritu","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Eduardo","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Reyes","F102_FATHER_LAST"),("Filipino","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2022-BC-009\nBC Date of Registration: March 15, 2022\nCHILD (First): Mia\nCHILD (Middle): Carbonell\nCHILD (Last): Santos\n2. SEX: Female\n3. Child Date of Birth: March 1, 2022\n4. PLACE OF BIRTH: Zamboanga City\nMother (First): Glenda\nMother (Middle): Reyes\nMother (Last): Carbonell\nMother Citizenship: Filipino\nFather (First): Freddie\nFather (Middle): Cruz\nFather (Last): Santos\nFather Citizenship: American")
    examples.append((t, {"entities": make_entities(t, [(("2022-BC-009","F102_REGISTRY_NO")),("March 15, 2022","F102_DATE_OF_REGISTRATION"),("Mia","F102_CHILD_FIRST"),("Carbonell","F102_CHILD_MIDDLE"),("Santos","F102_CHILD_LAST"),("Female","F102_SEX"),("March 1, 2022","F102_DATE_OF_BIRTH"),("Zamboanga City","F102_PLACE_OF_BIRTH"),("Glenda","F102_MOTHER_FIRST"),("Reyes","F102_MOTHER_MIDDLE"),("Carbonell","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Freddie","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Santos","F102_FATHER_LAST"),("American","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2016-BC-058\nBC Date of Registration: May 20, 2016\nCHILD (First): Angelica\nCHILD (Middle): Pingol\nCHILD (Last): Reyes\n2. SEX: Female\n3. Child Date of Birth: May 5, 2016\n4. PLACE OF BIRTH: Cavite City\nMother (First): Teresita\nMother (Middle): Mercado\nMother (Last): Pingol\nMother Citizenship: Filipino\nFather (First): Aldrin\nFather (Middle): Garcia\nFather (Last): Reyes\nFather Citizenship: American")
    examples.append((t, {"entities": make_entities(t, [(("2016-BC-058","F102_REGISTRY_NO")),("May 20, 2016","F102_DATE_OF_REGISTRATION"),("Angelica","F102_CHILD_FIRST"),("Pingol","F102_CHILD_MIDDLE"),("Reyes","F102_CHILD_LAST"),("Female","F102_SEX"),("May 5, 2016","F102_DATE_OF_BIRTH"),("Cavite City","F102_PLACE_OF_BIRTH"),("Teresita","F102_MOTHER_FIRST"),("Mercado","F102_MOTHER_MIDDLE"),("Pingol","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Aldrin","F102_FATHER_FIRST"),("Garcia","F102_FATHER_MIDDLE"),("Reyes","F102_FATHER_LAST"),("American","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2004-BC-190\nBC Date of Registration: June 30, 2004\nCHILD (First): Kevin\nCHILD (Middle): Aguilar\nCHILD (Last): Serrano\n2. SEX: Male\n3. Child Date of Birth: June 25, 2004\n4. PLACE OF BIRTH: Valenzuela City\nMother (First): Jocelyn\nMother (Middle): Bato\nMother (Last): Aguilar\nMother Citizenship: Filipino\nFather (First): Rodel\nFather (Middle): Reyes\nFather (Last): Serrano\nFather Citizenship: American")
    examples.append((t, {"entities": make_entities(t, [(("2004-BC-190","F102_REGISTRY_NO")),("June 30, 2004","F102_DATE_OF_REGISTRATION"),("Kevin","F102_CHILD_FIRST"),("Aguilar","F102_CHILD_MIDDLE"),("Serrano","F102_CHILD_LAST"),("Male","F102_SEX"),("June 25, 2004","F102_DATE_OF_BIRTH"),("Valenzuela City","F102_PLACE_OF_BIRTH"),("Jocelyn","F102_MOTHER_FIRST"),("Bato","F102_MOTHER_MIDDLE"),("Aguilar","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Rodel","F102_FATHER_FIRST"),("Reyes","F102_FATHER_MIDDLE"),("Serrano","F102_FATHER_LAST"),("American","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2009-BC-033\nBC Date of Registration: December 30, 2009\nCHILD (First): Trisha\nCHILD (Middle): Vergara\nCHILD (Last): Aquino\n2. SEX: Female\n3. Child Date of Birth: December 18, 2009\n4. PLACE OF BIRTH: Malabon City\nMother (First): Corazon\nMother (Middle): dela Torre\nMother (Last): Vergara\nMother Citizenship: Filipino\nFather (First): Gilbert\nFather (Middle): Santos\nFather (Last): Aquino\nFather Citizenship: American")
    examples.append((t, {"entities": make_entities(t, [(("2009-BC-033","F102_REGISTRY_NO")),("December 30, 2009","F102_DATE_OF_REGISTRATION"),("Trisha","F102_CHILD_FIRST"),("Vergara","F102_CHILD_MIDDLE"),("Aquino","F102_CHILD_LAST"),("Female","F102_SEX"),("December 18, 2009","F102_DATE_OF_BIRTH"),("Malabon City","F102_PLACE_OF_BIRTH"),("Corazon","F102_MOTHER_FIRST"),("dela Torre","F102_MOTHER_MIDDLE"),("Vergara","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Gilbert","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Aquino","F102_FATHER_LAST"),("American","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2011-BC-088\nBC Date of Registration: March 30, 2011\nCHILD (First): Hannah\nCHILD (Middle): Delos Reyes\nCHILD (Last): Magpayo\n2. SEX: Female\n3. Child Date of Birth: March 22, 2011\n4. PLACE OF BIRTH: Las Pinas City\nMother (First): Evelyn\nMother (Middle): Cruz\nMother (Last): Delos Reyes\nMother Citizenship: Filipino\nFather (First): Ariel\nFather (Middle): Santos\nFather (Last): Magpayo\nFather Citizenship: American")
    examples.append((t, {"entities": make_entities(t, [(("2011-BC-088","F102_REGISTRY_NO")),("March 30, 2011","F102_DATE_OF_REGISTRATION"),("Hannah","F102_CHILD_FIRST"),("Delos Reyes","F102_CHILD_MIDDLE"),("Magpayo","F102_CHILD_LAST"),("Female","F102_SEX"),("March 22, 2011","F102_DATE_OF_BIRTH"),("Las Pinas City","F102_PLACE_OF_BIRTH"),("Evelyn","F102_MOTHER_FIRST"),("Cruz","F102_MOTHER_MIDDLE"),("Delos Reyes","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ariel","F102_FATHER_FIRST"),("Santos","F102_FATHER_MIDDLE"),("Magpayo","F102_FATHER_LAST"),("American","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 1999-BC-044\nBC Date of Registration: May 10, 1999\nCHILD (First): Renaldo\nCHILD (Middle): Aquino\nCHILD (Last): Bautista\n2. SEX: Male\n3. Child Date of Birth: April 25, 1999\n4. PLACE OF BIRTH: Tarlac City\nMother (First): Cecilia\nMother (Middle): Ramos\nMother (Last): Aquino\nMother Citizenship: Filipino\nFather (First): Norberto\nFather (Middle): Cruz\nFather (Last): Bautista\nFather Citizenship: Chinese")
    examples.append((t, {"entities": make_entities(t, [(("1999-BC-044","F102_REGISTRY_NO")),("May 10, 1999","F102_DATE_OF_REGISTRATION"),("Renaldo","F102_CHILD_FIRST"),("Aquino","F102_CHILD_MIDDLE"),("Bautista","F102_CHILD_LAST"),("Male","F102_SEX"),("April 25, 1999","F102_DATE_OF_BIRTH"),("Tarlac City","F102_PLACE_OF_BIRTH"),("Cecilia","F102_MOTHER_FIRST"),("Ramos","F102_MOTHER_MIDDLE"),("Aquino","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Norberto","F102_FATHER_FIRST"),("Cruz","F102_FATHER_MIDDLE"),("Bautista","F102_FATHER_LAST"),("Chinese","F102_FATHER_CITIZENSHIP")])}))

    t = ("BC Registry No.: 2021-BC-077\nBC Date of Registration: August 5, 2021\nCHILD (First): Clarisse\nCHILD (Middle): Dela Pena\nCHILD (Last): Guevara\n2. SEX: Female\n3. Child Date of Birth: July 19, 2021\n4. PLACE OF BIRTH: Olongapo City\nMother (First): Analiza\nMother (Middle): Santos\nMother (Last): Dela Pena\nMother Citizenship: Filipino\nFather (First): Wilfredo\nFather (Middle): Reyes\nFather (Last): Guevara\nFather Citizenship: Chinese")
    examples.append((t, {"entities": make_entities(t, [(("2021-BC-077","F102_REGISTRY_NO")),("August 5, 2021","F102_DATE_OF_REGISTRATION"),("Clarisse","F102_CHILD_FIRST"),("Dela Pena","F102_CHILD_MIDDLE"),("Guevara","F102_CHILD_LAST"),("Female","F102_SEX"),("July 19, 2021","F102_DATE_OF_BIRTH"),("Olongapo City","F102_PLACE_OF_BIRTH"),("Analiza","F102_MOTHER_FIRST"),("Santos","F102_MOTHER_MIDDLE"),("Dela Pena","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Wilfredo","F102_FATHER_FIRST"),("Reyes","F102_FATHER_MIDDLE"),("Guevara","F102_FATHER_LAST"),("Chinese","F102_FATHER_CITIZENSHIP")])}))



    # Extra examples targeting rare labels: MARRIAGE_DATE, MARRIAGE_PLACE, TYPE_OF_BIRTH
    t = "BC Registry No.: 2015-BC-033\nBC Date of Registration: February 14, 2015\nCHILD (First): Mia\nCHILD (Middle): Buenaventura\nCHILD (Last): Tolentino\n2. SEX: Female\n3. Child Date of Birth: February 1, 2015\n4. PLACE OF BIRTH: Tarlac City\nMother (First): Luz\nMother (Middle): Pascual\nMother (Last): Buenaventura\nMother Citizenship: Filipino\nFather (First): Dante\nFather (Middle): Rivera\nFather (Last): Tolentino\nFather Citizenship: Chinese\n20a. DATE: April 12, 2010\n20b. PLACE: Tarlac City"
    examples.append((t, {"entities": make_entities(t, [(("2015-BC-033","F102_REGISTRY_NO")),("February 14, 2015","F102_DATE_OF_REGISTRATION"),("Mia","F102_CHILD_FIRST"),("Buenaventura","F102_CHILD_MIDDLE"),("Tolentino","F102_CHILD_LAST"),("Female","F102_SEX"),("February 1, 2015","F102_DATE_OF_BIRTH"),("Tarlac City","F102_PLACE_OF_BIRTH"),("Luz","F102_MOTHER_FIRST"),("Pascual","F102_MOTHER_MIDDLE"),("Buenaventura","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Dante","F102_FATHER_FIRST"),("Rivera","F102_FATHER_MIDDLE"),("Tolentino","F102_FATHER_LAST"),("Chinese","F102_FATHER_CITIZENSHIP"),("April 12, 2010","F102_MARRIAGE_DATE"),("Tarlac City","F102_MARRIAGE_PLACE")])}))

    t = "BC Registry No.: 1999-BC-077\nBC Date of Registration: May 3, 1999\nCHILD (First): Jerome\nCHILD (Middle): Espiritu\nCHILD (Last): Castillo\n2. SEX: Male\n3. Child Date of Birth: April 20, 1999\n4. PLACE OF BIRTH: San Pablo City\nMother (First): Nelia\nMother (Middle): Torres\nMother (Last): Espiritu\nMother Citizenship: Filipino\nFather (First): Ronaldo\nFather (Middle): Agno\nFather (Last): Castillo\nFather Citizenship: Chinese\n20a. DATE: December 8, 1990\n20b. PLACE: San Pablo City"
    examples.append((t, {"entities": make_entities(t, [(("1999-BC-077","F102_REGISTRY_NO")),("May 3, 1999","F102_DATE_OF_REGISTRATION"),("Jerome","F102_CHILD_FIRST"),("Espiritu","F102_CHILD_MIDDLE"),("Castillo","F102_CHILD_LAST"),("Male","F102_SEX"),("April 20, 1999","F102_DATE_OF_BIRTH"),("San Pablo City","F102_PLACE_OF_BIRTH"),("Nelia","F102_MOTHER_FIRST"),("Torres","F102_MOTHER_MIDDLE"),("Espiritu","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Ronaldo","F102_FATHER_FIRST"),("Agno","F102_FATHER_MIDDLE"),("Castillo","F102_FATHER_LAST"),("Chinese","F102_FATHER_CITIZENSHIP"),("December 8, 1990","F102_MARRIAGE_DATE"),("San Pablo City","F102_MARRIAGE_PLACE")])}))

    t = "BC Registry No.: 2018-BC-004\nBC Date of Registration: March 5, 2018\nCHILD (First): Luis\nCHILD (Middle): Aguilar\nCHILD (Last): Medina\n2. SEX: Male\n3. Child Date of Birth: February 28, 2018\n4. PLACE OF BIRTH: Antipolo City\n5a. TYPE OF BIRTH: Single\nMother (First): Corazon\nMother (Middle): Diaz\nMother (Last): Aguilar\nMother Citizenship: Filipino\nFather (First): Oscar\nFather (Middle): Soriano\nFather (Last): Medina\nFather Citizenship: Korean\n20a. DATE: September 21, 2005\n20b. PLACE: Antipolo City"
    examples.append((t, {"entities": make_entities(t, [(("2018-BC-004","F102_REGISTRY_NO")),("March 5, 2018","F102_DATE_OF_REGISTRATION"),("Luis","F102_CHILD_FIRST"),("Aguilar","F102_CHILD_MIDDLE"),("Medina","F102_CHILD_LAST"),("Male","F102_SEX"),("February 28, 2018","F102_DATE_OF_BIRTH"),("Antipolo City","F102_PLACE_OF_BIRTH"),("Corazon","F102_MOTHER_FIRST"),("Diaz","F102_MOTHER_MIDDLE"),("Aguilar","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Oscar","F102_FATHER_FIRST"),("Soriano","F102_FATHER_MIDDLE"),("Medina","F102_FATHER_LAST"),("Korean","F102_FATHER_CITIZENSHIP"),("September 21, 2005","F102_MARRIAGE_DATE"),("Antipolo City","F102_MARRIAGE_PLACE")])}))

    t = "BC Registry No.: 2020-BC-150\nBC Date of Registration: October 10, 2020\nCHILD (First): Bea\nCHILD (Middle): Navarro\nCHILD (Last): Padilla\n2. SEX: Female\n3. Child Date of Birth: October 1, 2020\n4. PLACE OF BIRTH: Bacoor City\n5a. TYPE OF BIRTH: Twin\nMother (First): Imelda\nMother (Middle): Reyes\nMother (Last): Navarro\nMother Citizenship: Filipino\nFather (First): Fernando\nFather (Middle): Salcedo\nFather (Last): Padilla\nFather Citizenship: Korean\n20a. DATE: June 12, 2015\n20b. PLACE: Bacoor City"
    examples.append((t, {"entities": make_entities(t, [(("2020-BC-150","F102_REGISTRY_NO")),("October 10, 2020","F102_DATE_OF_REGISTRATION"),("Bea","F102_CHILD_FIRST"),("Navarro","F102_CHILD_MIDDLE"),("Padilla","F102_CHILD_LAST"),("Female","F102_SEX"),("October 1, 2020","F102_DATE_OF_BIRTH"),("Bacoor City","F102_PLACE_OF_BIRTH"),("Imelda","F102_MOTHER_FIRST"),("Reyes","F102_MOTHER_MIDDLE"),("Navarro","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Fernando","F102_FATHER_FIRST"),("Salcedo","F102_FATHER_MIDDLE"),("Padilla","F102_FATHER_LAST"),("Korean","F102_FATHER_CITIZENSHIP"),("June 12, 2015","F102_MARRIAGE_DATE"),("Bacoor City","F102_MARRIAGE_PLACE")])}))

    t = "BC Registry No.: 2007-BC-088\nBC Date of Registration: November 22, 2007\nCHILD (First): Kristine\nCHILD (Middle): Flores\nCHILD (Last): Bernardo\n2. SEX: Female\n3. Child Date of Birth: November 10, 2007\n4. PLACE OF BIRTH: Las Pinas City\n5a. TYPE OF BIRTH: Triplet\nMother (First): Maricel\nMother (Middle): Lim\nMother (Last): Flores\nMother Citizenship: Filipino\nFather (First): Arnold\nFather (Middle): Guinto\nFather (Last): Bernardo\nFather Citizenship: Korean\n20a. DATE: March 25, 2000\n20b. PLACE: Manila"
    examples.append((t, {"entities": make_entities(t, [(("2007-BC-088","F102_REGISTRY_NO")),("November 22, 2007","F102_DATE_OF_REGISTRATION"),("Kristine","F102_CHILD_FIRST"),("Flores","F102_CHILD_MIDDLE"),("Bernardo","F102_CHILD_LAST"),("Female","F102_SEX"),("November 10, 2007","F102_DATE_OF_BIRTH"),("Las Pinas City","F102_PLACE_OF_BIRTH"),("Maricel","F102_MOTHER_FIRST"),("Lim","F102_MOTHER_MIDDLE"),("Flores","F102_MOTHER_LAST"),("Filipino","F102_MOTHER_CITIZENSHIP"),("Arnold","F102_FATHER_FIRST"),("Guinto","F102_FATHER_MIDDLE"),("Bernardo","F102_FATHER_LAST"),("Korean","F102_FATHER_CITIZENSHIP"),("March 25, 2000","F102_MARRIAGE_DATE"),("Manila","F102_MARRIAGE_PLACE")])}))

    return examples


# ============================================================
# FORM 103 -> FORM 2A (DEATH CERTIFICATE)
# Labels: REGISTRY_NO, DATE_OF_REGISTRATION, DECEASED_FIRST,
#         DECEASED_MIDDLE, DECEASED_LAST, SEX, AGE,
#         CIVIL_STATUS, CITIZENSHIP, DATE_OF_DEATH,
#         PLACE_OF_DEATH, CAUSE_IMMEDIATE, CAUSE_ANTECEDENT,
#         CAUSE_UNDERLYING, OCCUPATION, RESIDENCE, RELIGION
# ============================================================

def form103_examples():
    examples = []

    t = ("Registry No.: 2020-301\nDC Date of Registration: September 10, 2020\nDECEASED (First): Carlos (Middle): Reyes (Last): Mendoza\n2. SEX: Male\n4. AGE: 65\n5. PLACE OF DEATH: Quezon City\n6. DATE OF DEATH: September 2, 2020\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Cardiac Arrest")
    examples.append((t, {"entities": make_entities(t, [("2020-301","F103_REGISTRY_NO"),("September 10, 2020","F103_DATE_OF_REGISTRATION"),("Carlos","F103_DECEASED_FIRST"),("Reyes","F103_DECEASED_MIDDLE"),("Mendoza","F103_DECEASED_LAST"),("Male","F103_SEX"),("65","F103_AGE"),("Quezon City","F103_PLACE_OF_DEATH"),("September 2, 2020","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Cardiac Arrest","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2023-088\nDC Date of Registration: March 10, 2023\nDECEASED (First): Fernando (Middle): Santos (Last): Cruz\n2. SEX: Male\n4. AGE: 70\n5. PLACE OF DEATH: PGH Manila\n6. DATE OF DEATH: March 3, 2023\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Retired Teacher\nImmediate cause: Renal Failure\nAntecedent cause: Chronic Kidney Disease\nUnderlying cause: Diabetes Mellitus")
    examples.append((t, {"entities": make_entities(t, [("2023-088","F103_REGISTRY_NO"),("March 10, 2023","F103_DATE_OF_REGISTRATION"),("Fernando","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Cruz","F103_DECEASED_LAST"),("Male","F103_SEX"),("70","F103_AGE"),("PGH Manila","F103_PLACE_OF_DEATH"),("March 3, 2023","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Renal Failure","F103_CAUSE_IMMEDIATE"),("Chronic Kidney Disease","F103_CAUSE_ANTECEDENT"),("Diabetes Mellitus","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2022-011\nDC Date of Registration: January 10, 2022\nDECEASED (First): Josefa (Middle): dela Paz (Last): Gonzales\n2. SEX: Female\n3. RELIGION: Roman Catholic\n4. AGE: 91\n5. PLACE OF DEATH: Batangas City\n6. DATE OF DEATH: December 31, 2021\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Old Age")
    examples.append((t, {"entities": make_entities(t, [("2022-011","F103_REGISTRY_NO"),("January 10, 2022","F103_DATE_OF_REGISTRATION"),("Josefa","F103_DECEASED_FIRST"),("dela Paz","F103_DECEASED_MIDDLE"),("Gonzales","F103_DECEASED_LAST"),("Female","F103_SEX"),("91","F103_AGE"),("Batangas City","F103_PLACE_OF_DEATH"),("December 31, 2021","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Old Age","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2018-199\nDC Date of Registration: May 28, 2018\nDECEASED (First): Benjamin (Middle): Ocampo (Last): Velasquez\n2. SEX: Male\n4. AGE: 48\n5. PLACE OF DEATH: Makati Medical Center\n6. DATE OF DEATH: May 20, 2018\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 12 Ayala Avenue, Makati City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Accountant\nImmediate cause: Myocardial Infarction")
    examples.append((t, {"entities": make_entities(t, [("2018-199","F103_REGISTRY_NO"),("May 28, 2018","F103_DATE_OF_REGISTRATION"),("Benjamin","F103_DECEASED_FIRST"),("Ocampo","F103_DECEASED_MIDDLE"),("Velasquez","F103_DECEASED_LAST"),("Male","F103_SEX"),("48","F103_AGE"),("Makati Medical Center","F103_PLACE_OF_DEATH"),("May 20, 2018","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Myocardial Infarction","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2016-077\nDC Date of Registration: June 15, 2016\nDECEASED (First): Cristina (Middle): Evangelista (Last): Sy\n2. SEX: Female\n4. AGE: 29\n5. PLACE OF DEATH: Philippine General Hospital\n6. DATE OF DEATH: June 6, 2016\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Single\nImmediate cause: Dengue Hemorrhagic Fever")
    examples.append((t, {"entities": make_entities(t, [("2016-077","F103_REGISTRY_NO"),("June 15, 2016","F103_DATE_OF_REGISTRATION"),("Cristina","F103_DECEASED_FIRST"),("Evangelista","F103_DECEASED_MIDDLE"),("Sy","F103_DECEASED_LAST"),("Female","F103_SEX"),("29","F103_AGE"),("Philippine General Hospital","F103_PLACE_OF_DEATH"),("June 6, 2016","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Single","F103_CIVIL_STATUS"),("Dengue Hemorrhagic Fever","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2017-300\nDC Date of Registration: November 20, 2017\nDECEASED (First): Ernesto (Middle): Macapagal (Last): Villafuerte\n2. SEX: Male\n4. AGE: 77\n5. PLACE OF DEATH: Veterans Memorial Medical Center\n6. DATE OF DEATH: November 11, 2017\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Multi-Organ Failure\nAntecedent cause: Septicemia\nUnderlying cause: Pneumonia")
    examples.append((t, {"entities": make_entities(t, [("2017-300","F103_REGISTRY_NO"),("November 20, 2017","F103_DATE_OF_REGISTRATION"),("Ernesto","F103_DECEASED_FIRST"),("Macapagal","F103_DECEASED_MIDDLE"),("Villafuerte","F103_DECEASED_LAST"),("Male","F103_SEX"),("77","F103_AGE"),("Veterans Memorial Medical Center","F103_PLACE_OF_DEATH"),("November 11, 2017","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Multi-Organ Failure","F103_CAUSE_IMMEDIATE"),("Septicemia","F103_CAUSE_ANTECEDENT"),("Pneumonia","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2019-210\nDC Date of Registration: August 22, 2019\nDECEASED (First): Amelia (Middle): Torres (Last): Ramos\n2. SEX: Female\n3. RELIGION: Iglesia ni Cristo\n4. AGE: 56\n5. PLACE OF DEATH: Cebu City Medical Center\n6. DATE OF DEATH: August 15, 2019\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Nurse\nImmediate cause: Breast Cancer")
    examples.append((t, {"entities": make_entities(t, [("2019-210","F103_REGISTRY_NO"),("August 22, 2019","F103_DATE_OF_REGISTRATION"),("Amelia","F103_DECEASED_FIRST"),("Torres","F103_DECEASED_MIDDLE"),("Ramos","F103_DECEASED_LAST"),("Female","F103_SEX"),("56","F103_AGE"),("Cebu City Medical Center","F103_PLACE_OF_DEATH"),("August 15, 2019","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Breast Cancer","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2022-015\nDC Date of Registration: January 18, 2022\nDECEASED (First): Rodrigo (Middle): dela Cruz (Last): Santos\n2. SEX: Male\n4. AGE: 83\n5. PLACE OF DEATH: Jose Reyes Memorial Medical Center\n6. DATE OF DEATH: January 10, 2022\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Farmer\nImmediate cause: Stroke")
    examples.append((t, {"entities": make_entities(t, [("2022-015","F103_REGISTRY_NO"),("January 18, 2022","F103_DATE_OF_REGISTRATION"),("Rodrigo","F103_DECEASED_FIRST"),("dela Cruz","F103_DECEASED_MIDDLE"),("Santos","F103_DECEASED_LAST"),("Male","F103_SEX"),("83","F103_AGE"),("Jose Reyes Memorial Medical Center","F103_PLACE_OF_DEATH"),("January 10, 2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Stroke","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2014-099\nDC Date of Registration: April 14, 2014\nDECEASED (First): Marilou (Middle): Bautista (Last): Reyes\n2. SEX: Female\n4. AGE: 44\n5. PLACE OF DEATH: Ospital ng Maynila\n6. DATE OF DEATH: April 4, 2014\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Separated\nImmediate cause: Cervical Cancer\nUnderlying cause: HPV Infection")
    examples.append((t, {"entities": make_entities(t, [("2014-099","F103_REGISTRY_NO"),("April 14, 2014","F103_DATE_OF_REGISTRATION"),("Marilou","F103_DECEASED_FIRST"),("Bautista","F103_DECEASED_MIDDLE"),("Reyes","F103_DECEASED_LAST"),("Female","F103_SEX"),("44","F103_AGE"),("Ospital ng Maynila","F103_PLACE_OF_DEATH"),("April 4, 2014","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Separated","F103_CIVIL_STATUS"),("Cervical Cancer","F103_CAUSE_IMMEDIATE"),("HPV Infection","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2025-033\nDC Date of Registration: February 20, 2025\nDECEASED (First): Antonio (Middle): Velarde (Last): Pascual\n2. SEX: Male\n4. AGE: 61\n5. PLACE OF DEATH: Manila Doctors Hospital\n6. DATE OF DEATH: February 14, 2025\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Engineer\nImmediate cause: Liver Cirrhosis\nAntecedent cause: Hepatitis B\nUnderlying cause: Alcoholic Liver Disease")
    examples.append((t, {"entities": make_entities(t, [("2025-033","F103_REGISTRY_NO"),("February 20, 2025","F103_DATE_OF_REGISTRATION"),("Antonio","F103_DECEASED_FIRST"),("Velarde","F103_DECEASED_MIDDLE"),("Pascual","F103_DECEASED_LAST"),("Male","F103_SEX"),("61","F103_AGE"),("Manila Doctors Hospital","F103_PLACE_OF_DEATH"),("February 14, 2025","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Liver Cirrhosis","F103_CAUSE_IMMEDIATE"),("Hepatitis B","F103_CAUSE_ANTECEDENT"),("Alcoholic Liver Disease","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2024-055\nDC Date of Registration: March 18, 2024\nDECEASED (First): Ricardo (Middle): Buenaventura (Last): Gomez\n2. SEX: Male\n4. AGE: 74\n5. PLACE OF DEATH: Caloocan City\n6. DATE OF DEATH: March 10, 2024\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Hypertension")
    examples.append((t, {"entities": make_entities(t, [("2024-055","F103_REGISTRY_NO"),("March 18, 2024","F103_DATE_OF_REGISTRATION"),("Ricardo","F103_DECEASED_FIRST"),("Buenaventura","F103_DECEASED_MIDDLE"),("Gomez","F103_DECEASED_LAST"),("Male","F103_SEX"),("74","F103_AGE"),("Caloocan City","F103_PLACE_OF_DEATH"),("March 10, 2024","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Hypertension","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2022-188\nDC Date of Registration: July 30, 2022\nDECEASED (First): Rosalinda (Middle): Andres (Last): Peralta\n2. SEX: Female\n4. AGE: 68\n5. PLACE OF DEATH: Mandaluyong City\n6. DATE OF DEATH: July 21, 2022\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Housewife\nImmediate cause: Pulmonary Tuberculosis")
    examples.append((t, {"entities": make_entities(t, [("2022-188","F103_REGISTRY_NO"),("July 30, 2022","F103_DATE_OF_REGISTRATION"),("Rosalinda","F103_DECEASED_FIRST"),("Andres","F103_DECEASED_MIDDLE"),("Peralta","F103_DECEASED_LAST"),("Female","F103_SEX"),("68","F103_AGE"),("Mandaluyong City","F103_PLACE_OF_DEATH"),("July 21, 2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Pulmonary Tuberculosis","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2020-144\nDC Date of Registration: January 25, 2020\nDECEASED (First): Lorena (Middle): Valdez (Last): Soriano\n2. SEX: Female\n4. AGE: 38\n5. PLACE OF DEATH: Cardinal Santos Medical Center\n6. DATE OF DEATH: January 17, 2020\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Eclampsia")
    examples.append((t, {"entities": make_entities(t, [("2020-144","F103_REGISTRY_NO"),("January 25, 2020","F103_DATE_OF_REGISTRATION"),("Lorena","F103_DECEASED_FIRST"),("Valdez","F103_DECEASED_MIDDLE"),("Soriano","F103_DECEASED_LAST"),("Female","F103_SEX"),("38","F103_AGE"),("Cardinal Santos Medical Center","F103_PLACE_OF_DEATH"),("January 17, 2020","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Eclampsia","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2021-222\nDC Date of Registration: August 18, 2021\nDECEASED (First): Felicidad (Middle): Ramos (Last): Lim\n2. SEX: Female\n4. AGE: 52\n5. PLACE OF DEATH: Dagupan City\n6. DATE OF DEATH: August 9, 2021\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Teacher\nImmediate cause: Septic Shock\nUnderlying cause: Urinary Tract Infection")
    examples.append((t, {"entities": make_entities(t, [("2021-222","F103_REGISTRY_NO"),("August 18, 2021","F103_DATE_OF_REGISTRATION"),("Felicidad","F103_DECEASED_FIRST"),("Ramos","F103_DECEASED_MIDDLE"),("Lim","F103_DECEASED_LAST"),("Female","F103_SEX"),("52","F103_AGE"),("Dagupan City","F103_PLACE_OF_DEATH"),("August 9, 2021","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Septic Shock","F103_CAUSE_IMMEDIATE"),("Urinary Tract Infection","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2022-044\nDC Date of Registration: December 20, 2022\nDECEASED (First): Norma (Middle): Espino (Last): Aquino\n2. SEX: Female\n4. AGE: 43\n5. PLACE OF DEATH: Baguio General Hospital\n6. DATE OF DEATH: December 12, 2022\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Brain Tumor")
    examples.append((t, {"entities": make_entities(t, [("2022-044","F103_REGISTRY_NO"),("December 20, 2022","F103_DATE_OF_REGISTRATION"),("Norma","F103_DECEASED_FIRST"),("Espino","F103_DECEASED_MIDDLE"),("Aquino","F103_DECEASED_LAST"),("Female","F103_SEX"),("43","F103_AGE"),("Baguio General Hospital","F103_PLACE_OF_DEATH"),("December 12, 2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Brain Tumor","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2023-177\nDC Date of Registration: May 25, 2023\nDECEASED (First): Domingo (Middle): Padilla (Last): Cruz\n2. SEX: Male\n4. AGE: 66\n5. PLACE OF DEATH: Cagayan de Oro Medical Center\n6. DATE OF DEATH: May 15, 2023\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Driver\nImmediate cause: Acute Pancreatitis")
    examples.append((t, {"entities": make_entities(t, [("2023-177","F103_REGISTRY_NO"),("May 25, 2023","F103_DATE_OF_REGISTRATION"),("Domingo","F103_DECEASED_FIRST"),("Padilla","F103_DECEASED_MIDDLE"),("Cruz","F103_DECEASED_LAST"),("Male","F103_SEX"),("66","F103_AGE"),("Cagayan de Oro Medical Center","F103_PLACE_OF_DEATH"),("May 15, 2023","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Acute Pancreatitis","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2021-055\nDC Date of Registration: April 10, 2021\nDECEASED (First): Lucila (Middle): Santos (Last): Bautista\n2. SEX: Female\n4. AGE: 33\n5. PLACE OF DEATH: Davao Medical School Foundation\n6. DATE OF DEATH: April 1, 2021\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Single\nImmediate cause: Leukemia")
    examples.append((t, {"entities": make_entities(t, [("2021-055","F103_REGISTRY_NO"),("April 10, 2021","F103_DATE_OF_REGISTRATION"),("Lucila","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Bautista","F103_DECEASED_LAST"),("Female","F103_SEX"),("33","F103_AGE"),("Davao Medical School Foundation","F103_PLACE_OF_DEATH"),("April 1, 2021","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Single","F103_CIVIL_STATUS"),("Leukemia","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2018-244\nDC Date of Registration: September 5, 2018\nDECEASED (First): Renato (Middle): Abad (Last): Torres\n2. SEX: Male\n4. AGE: 58\n5. PLACE OF DEATH: Bacolod City\n6. DATE OF DEATH: August 28, 2018\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Businessman\nImmediate cause: Hemorrhagic Stroke")
    examples.append((t, {"entities": make_entities(t, [("2018-244","F103_REGISTRY_NO"),("September 5, 2018","F103_DATE_OF_REGISTRATION"),("Renato","F103_DECEASED_FIRST"),("Abad","F103_DECEASED_MIDDLE"),("Torres","F103_DECEASED_LAST"),("Male","F103_SEX"),("58","F103_AGE"),("Bacolod City","F103_PLACE_OF_DEATH"),("August 28, 2018","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Hemorrhagic Stroke","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2024-222\nDC Date of Registration: October 22, 2024\nDECEASED (First): Gloria (Middle): Macapagal (Last): Cruz\n2. SEX: Female\n4. AGE: 76\n5. PLACE OF DEATH: Pasig City General Hospital\n6. DATE OF DEATH: October 14, 2024\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Kidney Failure\nUnderlying cause: Hypertensive Nephropathy")
    examples.append((t, {"entities": make_entities(t, [("2024-222","F103_REGISTRY_NO"),("October 22, 2024","F103_DATE_OF_REGISTRATION"),("Gloria","F103_DECEASED_FIRST"),("Macapagal","F103_DECEASED_MIDDLE"),("Cruz","F103_DECEASED_LAST"),("Female","F103_SEX"),("76","F103_AGE"),("Pasig City General Hospital","F103_PLACE_OF_DEATH"),("October 14, 2024","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Kidney Failure","F103_CAUSE_IMMEDIATE"),("Hypertensive Nephropathy","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2023-099\nDC Date of Registration: March 30, 2023\nDECEASED (First): Milagros (Middle): Reyes (Last): Garcia\n2. SEX: Female\n4. AGE: 49\n5. PLACE OF DEATH: Lung Center of the Philippines\n6. DATE OF DEATH: March 25, 2023\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Nurse\nImmediate cause: Lung Cancer\nUnderlying cause: Chronic Smoking")
    examples.append((t, {"entities": make_entities(t, [("2023-099","F103_REGISTRY_NO"),("March 30, 2023","F103_DATE_OF_REGISTRATION"),("Milagros","F103_DECEASED_FIRST"),("Reyes","F103_DECEASED_MIDDLE"),("Garcia","F103_DECEASED_LAST"),("Female","F103_SEX"),("49","F103_AGE"),("Lung Center of the Philippines","F103_PLACE_OF_DEATH"),("March 25, 2023","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Lung Cancer","F103_CAUSE_IMMEDIATE"),("Chronic Smoking","F103_CAUSE_UNDERLYING")])}))

    t = ("Registry No.: 2024-155\nDC Date of Registration: July 15, 2024\nDECEASED (First): Wilfredo (Middle): Tolentino (Last): Medina\n2. SEX: Male\n4. AGE: 35\n5. PLACE OF DEATH: Rizal Medical Center\n6. DATE OF DEATH: July 7, 2024\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Single\nImmediate cause: Gunshot Wound")
    examples.append((t, {"entities": make_entities(t, [("2024-155","F103_REGISTRY_NO"),("July 15, 2024","F103_DATE_OF_REGISTRATION"),("Wilfredo","F103_DECEASED_FIRST"),("Tolentino","F103_DECEASED_MIDDLE"),("Medina","F103_DECEASED_LAST"),("Male","F103_SEX"),("35","F103_AGE"),("Rizal Medical Center","F103_PLACE_OF_DEATH"),("July 7, 2024","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Single","F103_CIVIL_STATUS"),("Gunshot Wound","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2019-088\nDC Date of Registration: July 8, 2019\nDECEASED (First): Melchor (Middle): Navarro (Last): Flores\n2. SEX: Male\n4. AGE: 88\n5. PLACE OF DEATH: Naga City\n6. DATE OF DEATH: June 30, 2019\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Senility")
    examples.append((t, {"entities": make_entities(t, [("2019-088","F103_REGISTRY_NO"),("July 8, 2019","F103_DATE_OF_REGISTRATION"),("Melchor","F103_DECEASED_FIRST"),("Navarro","F103_DECEASED_MIDDLE"),("Flores","F103_DECEASED_LAST"),("Male","F103_SEX"),("88","F103_AGE"),("Naga City","F103_PLACE_OF_DEATH"),("June 30, 2019","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Senility","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2024-008\nDC Date of Registration: February 10, 2024\nDECEASED (First): Aurelio (Middle): dela Vega (Last): Santos\n2. SEX: Male\n4. AGE: 79\n5. PLACE OF DEATH: Iloilo City\n6. DATE OF DEATH: February 2, 2024\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Congestive Heart Failure")
    examples.append((t, {"entities": make_entities(t, [("2024-008","F103_REGISTRY_NO"),("February 10, 2024","F103_DATE_OF_REGISTRATION"),("Aurelio","F103_DECEASED_FIRST"),("dela Vega","F103_DECEASED_MIDDLE"),("Santos","F103_DECEASED_LAST"),("Male","F103_SEX"),("79","F103_AGE"),("Iloilo City","F103_PLACE_OF_DEATH"),("February 2, 2024","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Congestive Heart Failure","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2022-066\nDC Date of Registration: June 12, 2022\nDECEASED (First): Teofilo (Middle): Mangubat (Last): Rojas\n2. SEX: Male\n4. AGE: 62\n5. PLACE OF DEATH: Palawan Provincial Hospital\n6. DATE OF DEATH: June 3, 2022\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Drowning")
    examples.append((t, {"entities": make_entities(t, [("2022-066","F103_REGISTRY_NO"),("June 12, 2022","F103_DATE_OF_REGISTRATION"),("Teofilo","F103_DECEASED_FIRST"),("Mangubat","F103_DECEASED_MIDDLE"),("Rojas","F103_DECEASED_LAST"),("Male","F103_SEX"),("62","F103_AGE"),("Palawan Provincial Hospital","F103_PLACE_OF_DEATH"),("June 3, 2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Drowning","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2020-088\nDC Date of Registration: September 28, 2020\nDECEASED (First): Virginia (Middle): Mendez (Last): Reyes\n2. SEX: Female\n4. AGE: 85\n5. PLACE OF DEATH: Zamboanga City Medical Center\n6. DATE OF DEATH: September 19, 2020\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Aspiration Pneumonia")
    examples.append((t, {"entities": make_entities(t, [("2020-088","F103_REGISTRY_NO"),("September 28, 2020","F103_DATE_OF_REGISTRATION"),("Virginia","F103_DECEASED_FIRST"),("Mendez","F103_DECEASED_MIDDLE"),("Reyes","F103_DECEASED_LAST"),("Female","F103_SEX"),("85","F103_AGE"),("Zamboanga City Medical Center","F103_PLACE_OF_DEATH"),("September 19, 2020","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Aspiration Pneumonia","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2015-066\nDC Date of Registration: June 10, 2015\nDECEASED (First): Conrado (Middle): Villanueva (Last): Padilla\n2. SEX: Male\n4. AGE: 59\n5. PLACE OF DEATH: Cabanatuan City\n6. DATE OF DEATH: June 1, 2015\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Security Guard\nImmediate cause: Aortic Aneurysm")
    examples.append((t, {"entities": make_entities(t, [("2015-066","F103_REGISTRY_NO"),("June 10, 2015","F103_DATE_OF_REGISTRATION"),("Conrado","F103_DECEASED_FIRST"),("Villanueva","F103_DECEASED_MIDDLE"),("Padilla","F103_DECEASED_LAST"),("Male","F103_SEX"),("59","F103_AGE"),("Cabanatuan City","F103_PLACE_OF_DEATH"),("June 1, 2015","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Aortic Aneurysm","F103_CAUSE_IMMEDIATE")])}))

    t = ("Registry No.: 2019-033\nDC Date of Registration: March 5, 2019\nDECEASED (First): Divina (Middle): Santos (Last): Evangelista\n2. SEX: Female\n4. AGE: 47\n5. PLACE OF DEATH: San Pablo City\n6. DATE OF DEATH: February 20, 2019\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\n10. OCCUPATION: Dressmaker\nImmediate cause: Colon Cancer\nUnderlying cause: Colorectal Adenocarcinoma")
    examples.append((t, {"entities": make_entities(t, [("2019-033","F103_REGISTRY_NO"),("March 5, 2019","F103_DATE_OF_REGISTRATION"),("Divina","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Evangelista","F103_DECEASED_LAST"),("Female","F103_SEX"),("47","F103_AGE"),("San Pablo City","F103_PLACE_OF_DEATH"),("February 20, 2019","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Colon Cancer","F103_CAUSE_IMMEDIATE"),("Colorectal Adenocarcinoma","F103_CAUSE_UNDERLYING")])}))


    # Extra examples targeting rare labels: RELIGION, RESIDENCE, CAUSE_ANTECEDENT
    t = ('Registry No.: 2019-055\nDC Date of Registration: June 5, 2019\nDECEASED (First): Ricardo (Middle): Macaraeg (Last): Soriano\n2. SEX: Male\n3. RELIGION: Roman Catholic\n4. AGE: 78\n5. PLACE OF DEATH: Valenzuela City\n6. DATE OF DEATH: May 28, 2019\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: Valenzuela City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Farmer\nImmediate cause: Myocardial Infarction\nAntecedent cause: Hypertension\nUnderlying cause: Cardiovascular Disease')
    examples.append((t, {"entities": make_entities(t, [("2019-055","F103_REGISTRY_NO"),("June 5, 2019","F103_DATE_OF_REGISTRATION"),("Ricardo","F103_DECEASED_FIRST"),("Macaraeg","F103_DECEASED_MIDDLE"),("Soriano","F103_DECEASED_LAST"),("Male","F103_SEX"),("78","F103_AGE"),("Valenzuela City","F103_PLACE_OF_DEATH"),("May 28, 2019","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Myocardial Infarction","F103_CAUSE_IMMEDIATE"),("Hypertension","F103_CAUSE_ANTECEDENT"),("Cardiovascular Disease","F103_CAUSE_UNDERLYING")])}))

    t = ('Registry No.: 2021-200\nDC Date of Registration: April 2, 2021\nDECEASED (First): Soledad (Middle): Bautista (Last): Ignacio\n2. SEX: Female\n3. RELIGION: Iglesia ni Cristo\n4. AGE: 85\n5. PLACE OF DEATH: Caloocan City\n6. DATE OF DEATH: March 25, 2021\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: Caloocan City\n9. CIVIL STATUS: Widow\n10. OCCUPATION: Housewife\nImmediate cause: Pneumonia\nAntecedent cause: COPD\nUnderlying cause: Pulmonary Tuberculosis')
    examples.append((t, {"entities": make_entities(t, [("2021-200","F103_REGISTRY_NO"),("April 2, 2021","F103_DATE_OF_REGISTRATION"),("Soledad","F103_DECEASED_FIRST"),("Bautista","F103_DECEASED_MIDDLE"),("Ignacio","F103_DECEASED_LAST"),("Female","F103_SEX"),("85","F103_AGE"),("Caloocan City","F103_PLACE_OF_DEATH"),("March 25, 2021","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widow","F103_CIVIL_STATUS"),("Pneumonia","F103_CAUSE_IMMEDIATE"),("COPD","F103_CAUSE_ANTECEDENT"),("Pulmonary Tuberculosis","F103_CAUSE_UNDERLYING")])}))

    t = ('Registry No.: 2017-099\nDC Date of Registration: August 15, 2017\nDECEASED (First): Amado (Middle): Ferrer (Last): Pascual\n2. SEX: Male\n3. RELIGION: Aglipayan\n4. AGE: 72\n5. PLACE OF DEATH: Batangas City\n6. DATE OF DEATH: August 10, 2017\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: Batangas City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Driver\nImmediate cause: Cerebrovascular Accident\nAntecedent cause: Atrial Fibrillation\nUnderlying cause: Hypertensive Heart Disease')
    examples.append((t, {"entities": make_entities(t, [("2017-099","F103_REGISTRY_NO"),("August 15, 2017","F103_DATE_OF_REGISTRATION"),("Amado","F103_DECEASED_FIRST"),("Ferrer","F103_DECEASED_MIDDLE"),("Pascual","F103_DECEASED_LAST"),("Male","F103_SEX"),("72","F103_AGE"),("Batangas City","F103_PLACE_OF_DEATH"),("August 10, 2017","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Cerebrovascular Accident","F103_CAUSE_IMMEDIATE"),("Atrial Fibrillation","F103_CAUSE_ANTECEDENT"),("Hypertensive Heart Disease","F103_CAUSE_UNDERLYING")])}))

    t = ('Registry No.: 2023-007\nDC Date of Registration: January 20, 2023\nDECEASED (First): Ligaya (Middle): Hernandez (Last): Ramos\n2. SEX: Female\n3. RELIGION: Born Again Christian\n4. AGE: 61\n5. PLACE OF DEATH: Marikina City\n6. DATE OF DEATH: January 14, 2023\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: Marikina City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Teacher\nImmediate cause: Sepsis\nAntecedent cause: Urinary Tract Infection\nUnderlying cause: Diabetes Mellitus Type 2')
    examples.append((t, {"entities": make_entities(t, [("2023-007","F103_REGISTRY_NO"),("January 20, 2023","F103_DATE_OF_REGISTRATION"),("Ligaya","F103_DECEASED_FIRST"),("Hernandez","F103_DECEASED_MIDDLE"),("Ramos","F103_DECEASED_LAST"),("Female","F103_SEX"),("61","F103_AGE"),("Marikina City","F103_PLACE_OF_DEATH"),("January 14, 2023","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Sepsis","F103_CAUSE_IMMEDIATE"),("Urinary Tract Infection","F103_CAUSE_ANTECEDENT"),("Diabetes Mellitus Type 2","F103_CAUSE_UNDERLYING")])}))

    t = ('Registry No.: 2016-188\nDC Date of Registration: September 3, 2016\nDECEASED (First): Domingo (Middle): Villafuerte (Last): Ocampo\n2. SEX: Male\n3. RELIGION: Roman Catholic\n4. AGE: 69\n5. PLACE OF DEATH: Naga City\n6. DATE OF DEATH: August 30, 2016\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: Naga City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Vendor\nImmediate cause: Liver Failure\nAntecedent cause: Hepatitis B\nUnderlying cause: Liver Cirrhosis')
    examples.append((t, {"entities": make_entities(t, [("2016-188","F103_REGISTRY_NO"),("September 3, 2016","F103_DATE_OF_REGISTRATION"),("Domingo","F103_DECEASED_FIRST"),("Villafuerte","F103_DECEASED_MIDDLE"),("Ocampo","F103_DECEASED_LAST"),("Male","F103_SEX"),("69","F103_AGE"),("Naga City","F103_PLACE_OF_DEATH"),("August 30, 2016","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Liver Failure","F103_CAUSE_IMMEDIATE"),("Hepatitis B","F103_CAUSE_ANTECEDENT"),("Liver Cirrhosis","F103_CAUSE_UNDERLYING")])}))


    # Extra examples targeting F103_RESIDENCE with DECEASED RESIDENCE: context
    t = "Registry No.: 2021-155\nDC Date of Registration: April 12, 2021\nDECEASED (First): Rodrigo (Middle): Santos (Last): Dela Cruz\n2. SEX: Male\n3. RELIGION: Roman Catholic\n4. AGE: 65\n5. PLACE OF DEATH: Lung Center of the Philippines\n6. DATE OF DEATH: April 5, 2021\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 22 Katipunan Ave, Quezon City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Farmer\nImmediate cause: Pneumonia\nAntecedent cause: Pulmonary Tuberculosis\nUnderlying cause: Malnutrition"
    examples.append((t, {"entities": make_entities(t, [("2021-155","F103_REGISTRY_NO"),("April 12, 2021","F103_DATE_OF_REGISTRATION"),("Rodrigo","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Dela Cruz","F103_DECEASED_LAST"),("Male","F103_SEX"),("65","F103_AGE"),("Lung Center of the Philippines","F103_PLACE_OF_DEATH"),("April 5, 2021","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Pneumonia","F103_CAUSE_IMMEDIATE"),("Pulmonary Tuberculosis","F103_CAUSE_ANTECEDENT"),("Malnutrition","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2019-088\nDC Date of Registration: June 20, 2019\nDECEASED (First): Erlinda (Middle): Cruz (Last): Villanueva\n2. SEX: Female\n3. RELIGION: Aglipayan\n4. AGE: 78\n5. PLACE OF DEATH: St. Luke's Medical Center\n6. DATE OF DEATH: June 15, 2019\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 45 Mabini St, Pasay City\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Housewife\nImmediate cause: Cardiac Arrest\nAntecedent cause: Hypertensive Heart Disease\nUnderlying cause: Hypertension"
    examples.append((t, {"entities": make_entities(t, [("2019-088","F103_REGISTRY_NO"),("June 20, 2019","F103_DATE_OF_REGISTRATION"),("Erlinda","F103_DECEASED_FIRST"),("Cruz","F103_DECEASED_MIDDLE"),("Villanueva","F103_DECEASED_LAST"),("Female","F103_SEX"),("78","F103_AGE"),("St. Luke's Medical Center","F103_PLACE_OF_DEATH"),("June 15, 2019","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Cardiac Arrest","F103_CAUSE_IMMEDIATE"),("Hypertensive Heart Disease","F103_CAUSE_ANTECEDENT"),("Hypertension","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2022-210\nDC Date of Registration: September 8, 2022\nDECEASED (First): Danilo (Middle): Reyes (Last): Garcia\n2. SEX: Male\n3. RELIGION: Iglesia ni Cristo\n4. AGE: 55\n5. PLACE OF DEATH: Jose Reyes Memorial Medical Center\n6. DATE OF DEATH: September 1, 2022\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 78 P. Burgos St, Caloocan City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Driver\nImmediate cause: Septicemia\nAntecedent cause: Urinary Tract Infection\nUnderlying cause: Prostate Cancer"
    examples.append((t, {"entities": make_entities(t, [("2022-210","F103_REGISTRY_NO"),("September 8, 2022","F103_DATE_OF_REGISTRATION"),("Danilo","F103_DECEASED_FIRST"),("Reyes","F103_DECEASED_MIDDLE"),("Garcia","F103_DECEASED_LAST"),("Male","F103_SEX"),("55","F103_AGE"),("Jose Reyes Memorial Medical Center","F103_PLACE_OF_DEATH"),("September 1, 2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Septicemia","F103_CAUSE_IMMEDIATE"),("Urinary Tract Infection","F103_CAUSE_ANTECEDENT"),("Prostate Cancer","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2020-175\nDC Date of Registration: November 3, 2020\nDECEASED (First): Corazon (Middle): Lim (Last): Navarro\n2. SEX: Female\n3. RELIGION: Born Again Christian\n4. AGE: 83\n5. PLACE OF DEATH: Makati Medical Center\n6. DATE OF DEATH: October 28, 2020\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 12 Ayala Ave, Makati City\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Retired\nImmediate cause: Multi-Organ Failure\nAntecedent cause: Sepsis\nUnderlying cause: Colon Cancer"
    examples.append((t, {"entities": make_entities(t, [("2020-175","F103_REGISTRY_NO"),("November 3, 2020","F103_DATE_OF_REGISTRATION"),("Corazon","F103_DECEASED_FIRST"),("Lim","F103_DECEASED_MIDDLE"),("Navarro","F103_DECEASED_LAST"),("Female","F103_SEX"),("83","F103_AGE"),("Makati Medical Center","F103_PLACE_OF_DEATH"),("October 28, 2020","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Multi-Organ Failure","F103_CAUSE_IMMEDIATE"),("Sepsis","F103_CAUSE_ANTECEDENT"),("Colon Cancer","F103_CAUSE_UNDERLYING")])}))


    # Extra targeted F103_RESIDENCE examples
    t = "Registry No.: 2017-044\nDC Date of Registration: March 5, 2017\nDECEASED (First): Aurelio (Middle): Bautista (Last): Mendez\n2. SEX: Male\n3. RELIGION: Roman Catholic\n4. AGE: 72\n5. PLACE OF DEATH: Ospital ng Maynila\n6. DATE OF DEATH: February 28, 2017\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 55 Taft Ave, Manila\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Retired\nImmediate cause: Stroke\nAntecedent cause: Atrial Fibrillation\nUnderlying cause: Hypertension"
    examples.append((t, {"entities": make_entities(t, [("2017-044","F103_REGISTRY_NO"),("March 5, 2017","F103_DATE_OF_REGISTRATION"),("Aurelio","F103_DECEASED_FIRST"),("Bautista","F103_DECEASED_MIDDLE"),("Mendez","F103_DECEASED_LAST"),("Male","F103_SEX"),("72","F103_AGE"),("Ospital ng Maynila","F103_PLACE_OF_DEATH"),("February 28, 2017","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Stroke","F103_CAUSE_IMMEDIATE"),("Atrial Fibrillation","F103_CAUSE_ANTECEDENT"),("Hypertension","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2016-322\nDC Date of Registration: July 15, 2016\nDECEASED (First): Remedios (Middle): Santos (Last): Flores\n2. SEX: Female\n3. RELIGION: Iglesia ni Cristo\n4. AGE: 60\n5. PLACE OF DEATH: East Avenue Medical Center\n6. DATE OF DEATH: July 10, 2016\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 33 Kamias Rd, Quezon City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Teacher\nImmediate cause: Respiratory Failure\nAntecedent cause: Pneumonia\nUnderlying cause: Lung Cancer"
    examples.append((t, {"entities": make_entities(t, [("2016-322","F103_REGISTRY_NO"),("July 15, 2016","F103_DATE_OF_REGISTRATION"),("Remedios","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Flores","F103_DECEASED_LAST"),("Female","F103_SEX"),("60","F103_AGE"),("East Avenue Medical Center","F103_PLACE_OF_DEATH"),("July 10, 2016","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Respiratory Failure","F103_CAUSE_IMMEDIATE"),("Pneumonia","F103_CAUSE_ANTECEDENT"),("Lung Cancer","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2018-501\nDC Date of Registration: December 20, 2018\nDECEASED (First): Vicente (Middle): Cruz (Last): Abad\n2. SEX: Male\n3. RELIGION: Aglipayan\n4. AGE: 68\n5. PLACE OF DEATH: V. Luna Medical Center\n6. DATE OF DEATH: December 15, 2018\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 11 Quirino Ave, Paranaque City\n9. CIVIL STATUS: Married\n10. OCCUPATION: Engineer\nImmediate cause: Acute MI\nAntecedent cause: Coronary Artery Disease\nUnderlying cause: Diabetes Mellitus"
    examples.append((t, {"entities": make_entities(t, [("2018-501","F103_REGISTRY_NO"),("December 20, 2018","F103_DATE_OF_REGISTRATION"),("Vicente","F103_DECEASED_FIRST"),("Cruz","F103_DECEASED_MIDDLE"),("Abad","F103_DECEASED_LAST"),("Male","F103_SEX"),("68","F103_AGE"),("V. Luna Medical Center","F103_PLACE_OF_DEATH"),("December 15, 2018","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Acute MI","F103_CAUSE_IMMEDIATE"),("Coronary Artery Disease","F103_CAUSE_ANTECEDENT"),("Diabetes Mellitus","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2015-188\nDC Date of Registration: August 10, 2015\nDECEASED (First): Perla (Middle): Ramos (Last): Gonzales\n2. SEX: Female\n3. RELIGION: Born Again Christian\n4. AGE: 55\n5. PLACE OF DEATH: Philippine General Hospital\n6. DATE OF DEATH: August 5, 2015\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 88 España Blvd, Sampaloc Manila\n9. CIVIL STATUS: Single\n10. OCCUPATION: Nurse\nImmediate cause: Hemorrhagic Stroke\nAntecedent cause: Hypertensive Emergency\nUnderlying cause: Hypertension"
    examples.append((t, {"entities": make_entities(t, [("2015-188","F103_REGISTRY_NO"),("August 10, 2015","F103_DATE_OF_REGISTRATION"),("Perla","F103_DECEASED_FIRST"),("Ramos","F103_DECEASED_MIDDLE"),("Gonzales","F103_DECEASED_LAST"),("Female","F103_SEX"),("55","F103_AGE"),("Philippine General Hospital","F103_PLACE_OF_DEATH"),("August 5, 2015","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Single","F103_CIVIL_STATUS"),("Hemorrhagic Stroke","F103_CAUSE_IMMEDIATE"),("Hypertensive Emergency","F103_CAUSE_ANTECEDENT"),("Hypertension","F103_CAUSE_UNDERLYING")])}))

    t = "Registry No.: 2023-709\nDC Date of Registration: October 2, 2023\nDECEASED (First): Nestor (Middle): Villanueva (Last): Torres\n2. SEX: Male\n3. RELIGION: Roman Catholic\n4. AGE: 81\n5. PLACE OF DEATH: National Kidney Institute\n6. DATE OF DEATH: September 28, 2023\n7. CITIZENSHIP: Filipino\nDECEASED RESIDENCE: 19 Morayta St, Binondo Manila\n9. CIVIL STATUS: Widowed\n10. OCCUPATION: Retired\nImmediate cause: Renal Failure\nAntecedent cause: Chronic Kidney Disease Stage 5\nUnderlying cause: Hypertension"
    examples.append((t, {"entities": make_entities(t, [("2023-709","F103_REGISTRY_NO"),("October 2, 2023","F103_DATE_OF_REGISTRATION"),("Nestor","F103_DECEASED_FIRST"),("Villanueva","F103_DECEASED_MIDDLE"),("Torres","F103_DECEASED_LAST"),("Male","F103_SEX"),("81","F103_AGE"),("National Kidney Institute","F103_PLACE_OF_DEATH"),("September 28, 2023","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Renal Failure","F103_CAUSE_IMMEDIATE"),("Chronic Kidney Disease Stage 5","F103_CAUSE_ANTECEDENT"),("Hypertension","F103_CAUSE_UNDERLYING")])}))

    return examples


# ============================================================
# FORM 97 -> FORM 3A (MARRIAGE CERTIFICATE)
# Labels: REGISTRY_NO, DATE_OF_REGISTRATION,
#         HUSBAND_FIRST, HUSBAND_MIDDLE, HUSBAND_LAST,
#         HUSBAND_AGE, HUSBAND_CITIZENSHIP,
#         HUSBAND_FATHER_FIRST, HUSBAND_FATHER_LAST,
#         HUSBAND_MOTHER_FIRST, HUSBAND_MOTHER_LAST,
#         WIFE_FIRST, WIFE_MIDDLE, WIFE_LAST,
#         WIFE_AGE, WIFE_CITIZENSHIP,
#         WIFE_FATHER_FIRST, WIFE_FATHER_LAST,
#         WIFE_MOTHER_FIRST, WIFE_MOTHER_LAST,
#         DATE_OF_MARRIAGE, PLACE_OF_MARRIAGE,
#         DATE_OF_REGISTRATION
# ============================================================

def form97_examples():
    examples = []

    t = ("Registry No.: 2022-MC-055\nMC Date of Registration: February 20, 2022\nHusband (First): Jose\nHusband (Middle): Cruz\nHusband (Last): Ramos\nHusband AGE: 28\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Ernesto (Last): Ramos\nHusband NAME OF MOTHER (First): Lourdes (Last): Cruz\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Elena\nWife (Middle): Bautista\nWife (Last): Torres\nWife AGE: 25\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Antonio (Last): Torres\nWife NAME OF MOTHER (First): Carmen (Last): Bautista\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: February 14, 2022\nPLACE OF MARRIAGE: Makati City Hall")
    examples.append((t, {"entities": make_entities(t, [(("2022-MC-055","F97_REGISTRY_NO")),("February 20, 2022","F97_DATE_OF_REGISTRATION"),("Jose","F97_HUSBAND_FIRST"),("Cruz","F97_HUSBAND_MIDDLE"),("Ramos","F97_HUSBAND_LAST"),("28","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Ernesto","F97_HUSBAND_FATHER_FIRST"),("Ramos","F97_HUSBAND_FATHER_LAST"),("Lourdes","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Cruz","F97_HUSBAND_MOTHER_LAST"),("Elena","F97_WIFE_FIRST"),("Bautista","F97_WIFE_MIDDLE"),("Torres","F97_WIFE_LAST"),("25","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Antonio","F97_WIFE_FATHER_FIRST"),("Torres","F97_WIFE_FATHER_LAST"),("Carmen","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Bautista","F97_WIFE_MOTHER_LAST"),("February 14, 2022","F97_DATE_OF_MARRIAGE"),("Makati City Hall","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2021-MC-188\nMC Date of Registration: December 20, 2021\nHusband (First): Miguel\nHusband (Middle): Santos\nHusband (Last): dela Cruz\nHusband AGE: 31\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Roberto (Last): dela Cruz\nHusband NAME OF MOTHER (First): Nelia (Last): Santos\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Sofia\nWife (Middle): Tan\nWife (Last): Lim\nWife AGE: 28\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): William (Last): Lim\nWife NAME OF MOTHER (First): Shirley (Last): Tan\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: December 12, 2021\nPLACE OF MARRIAGE: Taguig City")
    examples.append((t, {"entities": make_entities(t, [(("2021-MC-188","F97_REGISTRY_NO")),("December 20, 2021","F97_DATE_OF_REGISTRATION"),("Miguel","F97_HUSBAND_FIRST"),("Santos","F97_HUSBAND_MIDDLE"),("dela Cruz","F97_HUSBAND_LAST"),("31","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Roberto","F97_HUSBAND_FATHER_FIRST"),("dela Cruz","F97_HUSBAND_FATHER_LAST"),("Nelia","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Santos","F97_HUSBAND_MOTHER_LAST"),("Sofia","F97_WIFE_FIRST"),("Tan","F97_WIFE_MIDDLE"),("Lim","F97_WIFE_LAST"),("28","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("William","F97_WIFE_FATHER_FIRST"),("Lim","F97_WIFE_FATHER_LAST"),("Shirley","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Tan","F97_WIFE_MOTHER_LAST"),("December 12, 2021","F97_DATE_OF_MARRIAGE"),("Taguig City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2019-MC-199\nMC Date of Registration: October 12, 2019\nHusband (First): Ricardo (Middle): dela Torre (Last): Magsaysay\nHusband AGE: 35\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Alfredo (Last): Magsaysay\nHusband NAME OF MOTHER (First): Florencia (Last): dela\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino Torre\nWife (First): Consuelo\nWife (Middle): Reyes\nWife (Last): Pascual\nWife AGE: 30\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Rodrigo (Last): Pascual\nWife NAME OF MOTHER (First): Susana (Last): Reyes\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: October 4, 2019\nPLACE OF MARRIAGE: Quezon City")
    examples.append((t, {"entities": make_entities(t, [(("2019-MC-199","F97_REGISTRY_NO")),("October 12, 2019","F97_DATE_OF_REGISTRATION"),("Ricardo","F97_HUSBAND_FIRST"),("dela Torre","F97_HUSBAND_MIDDLE"),("Magsaysay","F97_HUSBAND_LAST"),("35","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Alfredo","F97_HUSBAND_FATHER_FIRST"),("Magsaysay","F97_HUSBAND_FATHER_LAST"),("Florencia","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Consuelo","F97_WIFE_FIRST"),("Reyes","F97_WIFE_MIDDLE"),("Pascual","F97_WIFE_LAST"),("30","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Rodrigo","F97_WIFE_FATHER_FIRST"),("Pascual","F97_WIFE_FATHER_LAST"),("Susana","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Reyes","F97_WIFE_MOTHER_LAST"),("October 4, 2019","F97_DATE_OF_MARRIAGE"),("Quezon City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2010-MC-077\nMC Date of Registration: March 22, 2010\nHUSBAND NAME (First): Albert (Middle): Garcia (Last): Santos\nHUSBAND AGE: 40\nHUSBAND CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHUSBAND RELIGION: Roman Catholic\nHUSBAND NAME OF FATHER (First): Domingo (Last): Santos\nHUSBAND NAME OF MOTHER (First): Caridad (Last): Garcia\nWIFE NAME (First): Rowena (Middle): Alvarez (Last): Reyes\nWIFE AGE: 36\nWIFE CITIZENSHIP: Filipino\nHusband Civil Status: Single\nWIFE RELIGION: Roman Catholic\nWIFE NAME OF FATHER (First): Cesar (Last): Reyes\nWIFE NAME OF MOTHER (First): Natividad (Last): Alvarez\nDATE OF MARRIAGE: March 14, 2010\nPLACE OF MARRIAGE: Victory Christian Center, Pasig")
    examples.append((t, {"entities": make_entities(t, [(("2010-MC-077","F97_REGISTRY_NO")),("March 22, 2010","F97_DATE_OF_REGISTRATION"),("Albert","F97_HUSBAND_FIRST"),("Garcia","F97_HUSBAND_MIDDLE"),("Santos","F97_HUSBAND_LAST"),("40","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Domingo","F97_HUSBAND_FATHER_FIRST"),("Santos","F97_HUSBAND_FATHER_LAST"),("Caridad","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Garcia","F97_HUSBAND_MOTHER_LAST"),("Rowena","F97_WIFE_FIRST"),("Alvarez","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("36","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Cesar","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Natividad","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Alvarez","F97_WIFE_MOTHER_LAST"),("March 14, 2010","F97_DATE_OF_MARRIAGE"),("Victory Christian Center, Pasig","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2023-MC-144\nMC Date of Registration: July 1, 2023\nHusband (First): Patrick\nHusband (Middle): Sy\nHusband (Last): Chua\nHusband AGE: 33\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Henry (Last): Chua\nHusband NAME OF MOTHER (First): Linda (Last): Sy\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Christine\nWife (Middle): Lim\nWife (Last): Go\nWife AGE: 29\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): George (Last): Go\nWife NAME OF MOTHER (First): Susan (Last): Lim\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: July 7, 2023\nPLACE OF MARRIAGE: Binondo Church, Manila")
    examples.append((t, {"entities": make_entities(t, [(("2023-MC-144","F97_REGISTRY_NO")),("July 1, 2023","F97_DATE_OF_REGISTRATION"),("Patrick","F97_HUSBAND_FIRST"),("Sy","F97_HUSBAND_MIDDLE"),("Chua","F97_HUSBAND_LAST"),("33","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Henry","F97_HUSBAND_FATHER_FIRST"),("Chua","F97_HUSBAND_FATHER_LAST"),("Linda","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Sy","F97_HUSBAND_MOTHER_LAST"),("Christine","F97_WIFE_FIRST"),("Lim","F97_WIFE_MIDDLE"),("Go","F97_WIFE_LAST"),("29","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("George","F97_WIFE_FATHER_FIRST"),("Go","F97_WIFE_FATHER_LAST"),("Susan","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Lim","F97_WIFE_MOTHER_LAST"),("July 7, 2023","F97_DATE_OF_MARRIAGE"),("Binondo Church, Manila","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2018-MC-099\nMC Date of Registration: May 15, 2018\nHusband (First): Danilo\nHusband (Middle): Reyes\nHusband (Last): Flores\nHusband AGE: 22\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Renato (Last): Flores\nHusband NAME OF MOTHER (First): Marieta (Last): Reyes\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Marianne\nWife (Middle): Santos\nWife (Last): Cruz\nWife AGE: 21\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Roberto (Last): Cruz\nWife NAME OF MOTHER (First): Elvira (Last): Santos\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: May 5, 2018\nPLACE OF MARRIAGE: San Agustin Church, Intramuros")
    examples.append((t, {"entities": make_entities(t, [(("2018-MC-099","F97_REGISTRY_NO")),("May 15, 2018","F97_DATE_OF_REGISTRATION"),("Danilo","F97_HUSBAND_FIRST"),("Reyes","F97_HUSBAND_MIDDLE"),("Flores","F97_HUSBAND_LAST"),("22","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Renato","F97_HUSBAND_FATHER_FIRST"),("Flores","F97_HUSBAND_FATHER_LAST"),("Marieta","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Reyes","F97_HUSBAND_MOTHER_LAST"),("Marianne","F97_WIFE_FIRST"),("Santos","F97_WIFE_MIDDLE"),("Cruz","F97_WIFE_LAST"),("21","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Roberto","F97_WIFE_FATHER_FIRST"),("Cruz","F97_WIFE_FATHER_LAST"),("Elvira","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Santos","F97_WIFE_MOTHER_LAST"),("May 5, 2018","F97_DATE_OF_MARRIAGE"),("San Agustin Church, Intramuros","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2009-MC-188\nMC Date of Registration: September 18, 2009\nHusband (First): Leonardo\nHusband (Middle): Aquino\nHusband (Last): Delos Reyes\nHusband AGE: 45\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Cesar (Last): Delos Reyes\nHusband NAME OF MOTHER (First): Rosario (Last): Aquino\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Angelica\nWife (Middle): Pascual\nWife (Last): Mendoza\nWife AGE: 42\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Fernando (Last): Mendoza\nWife NAME OF MOTHER (First): Gloria (Last): Pascual\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: September 9, 2009\nPLACE OF MARRIAGE: Barasoain Church, Malolos")
    examples.append((t, {"entities": make_entities(t, [(("2009-MC-188","F97_REGISTRY_NO")),("September 18, 2009","F97_DATE_OF_REGISTRATION"),("Leonardo","F97_HUSBAND_FIRST"),("Aquino","F97_HUSBAND_MIDDLE"),("Delos Reyes","F97_HUSBAND_LAST"),("45","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Cesar","F97_HUSBAND_FATHER_FIRST"),("Delos Reyes","F97_HUSBAND_FATHER_LAST"),("Rosario","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Aquino","F97_HUSBAND_MOTHER_LAST"),("Angelica","F97_WIFE_FIRST"),("Pascual","F97_WIFE_MIDDLE"),("Mendoza","F97_WIFE_LAST"),("42","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Fernando","F97_WIFE_FATHER_FIRST"),("Mendoza","F97_WIFE_FATHER_LAST"),("Gloria","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Pascual","F97_WIFE_MOTHER_LAST"),("September 9, 2009","F97_DATE_OF_MARRIAGE"),("Barasoain Church, Malolos","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2015-MC-244\nMC Date of Registration: December 10, 2015\nHusband (First): Ramon (Middle): dela Cruz (Last): Villanueva\nHusband AGE: 38\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Nestor (Last): Villanueva\nHusband NAME OF MOTHER (First): Corazon (Last): dela\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino Cruz\nWife (First): Lourdes\nWife (Middle): Garcia\nWife (Last): Aquino\nWife AGE: 35\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Alfredo (Last): Aquino\nWife NAME OF MOTHER (First): Teodora (Last): Garcia\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: November 30, 2015\nPLACE OF MARRIAGE: Our Lady of Penaranda, Manila")
    examples.append((t, {"entities": make_entities(t, [(("2015-MC-244","F97_REGISTRY_NO")),("December 10, 2015","F97_DATE_OF_REGISTRATION"),("Ramon","F97_HUSBAND_FIRST"),("dela Cruz","F97_HUSBAND_MIDDLE"),("Villanueva","F97_HUSBAND_LAST"),("38","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Nestor","F97_HUSBAND_FATHER_FIRST"),("Villanueva","F97_HUSBAND_FATHER_LAST"),("Corazon","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Lourdes","F97_WIFE_FIRST"),("Garcia","F97_WIFE_MIDDLE"),("Aquino","F97_WIFE_LAST"),("35","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Alfredo","F97_WIFE_FATHER_FIRST"),("Aquino","F97_WIFE_FATHER_LAST"),("Teodora","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Garcia","F97_WIFE_MOTHER_LAST"),("November 30, 2015","F97_DATE_OF_MARRIAGE"),("Our Lady of Penaranda, Manila","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2023-MC-055\nMC Date of Registration: July 1, 2023\nHusband (First): Marco\nHusband (Middle): Villanueva\nHusband (Last): Concepcion\nHusband AGE: 26\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Victor (Last): Concepcion\nHusband NAME OF MOTHER (First): Lilia (Last): Villanueva\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Patricia\nWife (Middle): Guevara\nWife (Last): Luna\nWife AGE: 24\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Mario (Last): Luna\nWife NAME OF MOTHER (First): Felisa (Last): Guevara\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: June 21, 2023\nPLACE OF MARRIAGE: Iloilo City Hall")
    examples.append((t, {"entities": make_entities(t, [(("2023-MC-055","F97_REGISTRY_NO")),("July 1, 2023","F97_DATE_OF_REGISTRATION"),("Marco","F97_HUSBAND_FIRST"),("Villanueva","F97_HUSBAND_MIDDLE"),("Concepcion","F97_HUSBAND_LAST"),("26","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Victor","F97_HUSBAND_FATHER_FIRST"),("Concepcion","F97_HUSBAND_FATHER_LAST"),("Lilia","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Villanueva","F97_HUSBAND_MOTHER_LAST"),("Patricia","F97_WIFE_FIRST"),("Guevara","F97_WIFE_MIDDLE"),("Luna","F97_WIFE_LAST"),("24","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Mario","F97_WIFE_FATHER_FIRST"),("Luna","F97_WIFE_FATHER_LAST"),("Felisa","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Guevara","F97_WIFE_MOTHER_LAST"),("June 21, 2023","F97_DATE_OF_MARRIAGE"),("Iloilo City Hall","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2020-MC-011\nMC Date of Registration: January 15, 2020\nHusband (First): Bryan\nHusband (Middle): Santos\nHusband (Last): Ocampo\nHusband AGE: 32\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Eduardo (Last): Ocampo\nHusband NAME OF MOTHER (First): Maricel (Last): Santos\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Katrina (Middle): dela Cruz (Last): Reyes\nWife AGE: 29\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Domingo (Last): Reyes\nWife NAME OF MOTHER (First): Conchita (Last): dela\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino Cruz\nDATE OF MARRIAGE: January 5, 2020\nPLACE OF MARRIAGE: Immaculate Conception Parish, Cubao")
    examples.append((t, {"entities": make_entities(t, [(("2020-MC-011","F97_REGISTRY_NO")),("January 15, 2020","F97_DATE_OF_REGISTRATION"),("Bryan","F97_HUSBAND_FIRST"),("Santos","F97_HUSBAND_MIDDLE"),("Ocampo","F97_HUSBAND_LAST"),("32","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Eduardo","F97_HUSBAND_FATHER_FIRST"),("Ocampo","F97_HUSBAND_FATHER_LAST"),("Maricel","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Santos","F97_HUSBAND_MOTHER_LAST"),("Katrina","F97_WIFE_FIRST"),("dela Cruz","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("29","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Domingo","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Conchita","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Reyes","F97_WIFE_MOTHER_LAST"),("January 5, 2020","F97_DATE_OF_MARRIAGE"),("Immaculate Conception Parish, Cubao","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2024-MC-033\nMC Date of Registration: June 25, 2024\nHusband (First): Francis\nHusband (Middle): Mendoza\nHusband (Last): Lopez\nHusband AGE: 24\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Armando (Last): Lopez\nHusband NAME OF MOTHER (First): Teresita (Last): Mendoza\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Karen\nWife (Middle): Bautista\nWife (Last): Cruz\nWife AGE: 22\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Eduardo (Last): Cruz\nWife NAME OF MOTHER (First): Lourdes (Last): Bautista\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: June 15, 2024\nPLACE OF MARRIAGE: Shrine of Saint Anne, Pampanga")
    examples.append((t, {"entities": make_entities(t, [(("2024-MC-033","F97_REGISTRY_NO")),("June 25, 2024","F97_DATE_OF_REGISTRATION"),("Francis","F97_HUSBAND_FIRST"),("Mendoza","F97_HUSBAND_MIDDLE"),("Lopez","F97_HUSBAND_LAST"),("24","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Armando","F97_HUSBAND_FATHER_FIRST"),("Lopez","F97_HUSBAND_FATHER_LAST"),("Teresita","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Mendoza","F97_HUSBAND_MOTHER_LAST"),("Karen","F97_WIFE_FIRST"),("Bautista","F97_WIFE_MIDDLE"),("Cruz","F97_WIFE_LAST"),("22","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Eduardo","F97_WIFE_FATHER_FIRST"),("Cruz","F97_WIFE_FATHER_LAST"),("Lourdes","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Bautista","F97_WIFE_MOTHER_LAST"),("June 15, 2024","F97_DATE_OF_MARRIAGE"),("Shrine of Saint Anne, Pampanga","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2022-MC-099\nMC Date of Registration: October 20, 2022\nHusband (First): Dennis\nHusband (Middle): Aguilar\nHusband (Last): Dela Cruz\nHusband AGE: 29\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Reynaldo (Last): Dela Cruz\nHusband NAME OF MOTHER (First): Violeta (Last): Aguilar\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Sheena\nWife (Middle): Ramos\nWife (Last): Flores\nWife AGE: 26\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Alfredo (Last): Flores\nWife NAME OF MOTHER (First): Cynthia (Last): Ramos\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: October 10, 2022\nPLACE OF MARRIAGE: Batangas City Hall")
    examples.append((t, {"entities": make_entities(t, [(("2022-MC-099","F97_REGISTRY_NO")),("October 20, 2022","F97_DATE_OF_REGISTRATION"),("Dennis","F97_HUSBAND_FIRST"),("Aguilar","F97_HUSBAND_MIDDLE"),("Dela Cruz","F97_HUSBAND_LAST"),("29","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Reynaldo","F97_HUSBAND_FATHER_FIRST"),("Dela Cruz","F97_HUSBAND_FATHER_LAST"),("Violeta","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Aguilar","F97_HUSBAND_MOTHER_LAST"),("Sheena","F97_WIFE_FIRST"),("Ramos","F97_WIFE_MIDDLE"),("Flores","F97_WIFE_LAST"),("26","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Alfredo","F97_WIFE_FATHER_FIRST"),("Flores","F97_WIFE_FATHER_LAST"),("Cynthia","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Ramos","F97_WIFE_MOTHER_LAST"),("October 10, 2022","F97_DATE_OF_MARRIAGE"),("Batangas City Hall","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2019-MC-099\nMC Date of Registration: September 28, 2019\nHusband (First): Gerald\nHusband (Middle): Reyes\nHusband (Last): Pascual\nHusband AGE: 30\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Arturo (Last): Pascual\nHusband NAME OF MOTHER (First): Milagros (Last): Reyes\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Alyssa\nWife (Middle): Santos\nWife (Last): Aquino\nWife AGE: 27\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Danilo (Last): Aquino\nWife NAME OF MOTHER (First): Evelina (Last): Santos\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: September 20, 2019\nPLACE OF MARRIAGE: Manila Hotel")
    examples.append((t, {"entities": make_entities(t, [(("2019-MC-099","F97_REGISTRY_NO")),("September 28, 2019","F97_DATE_OF_REGISTRATION"),("Gerald","F97_HUSBAND_FIRST"),("Reyes","F97_HUSBAND_MIDDLE"),("Pascual","F97_HUSBAND_LAST"),("30","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Arturo","F97_HUSBAND_FATHER_FIRST"),("Pascual","F97_HUSBAND_FATHER_LAST"),("Milagros","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Reyes","F97_HUSBAND_MOTHER_LAST"),("Alyssa","F97_WIFE_FIRST"),("Santos","F97_WIFE_MIDDLE"),("Aquino","F97_WIFE_LAST"),("27","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Danilo","F97_WIFE_FATHER_FIRST"),("Aquino","F97_WIFE_FATHER_LAST"),("Evelina","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Santos","F97_WIFE_MOTHER_LAST"),("September 20, 2019","F97_DATE_OF_MARRIAGE"),("Manila Hotel","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2016-MC-177\nMC Date of Registration: August 18, 2016\nHusband (First): Henry\nHusband (Middle): Cruz\nHusband (Last): Valdes\nHusband AGE: 37\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Rolando (Last): Valdes\nHusband NAME OF MOTHER (First): Rosita (Last): Cruz\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Dianne\nWife (Middle): Flores\nWife (Last): Reyes\nWife AGE: 34\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Arsenio (Last): Reyes\nWife NAME OF MOTHER (First): Priscilla (Last): Flores\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: August 8, 2016\nPLACE OF MARRIAGE: Davao City")
    examples.append((t, {"entities": make_entities(t, [(("2016-MC-177","F97_REGISTRY_NO")),("August 18, 2016","F97_DATE_OF_REGISTRATION"),("Henry","F97_HUSBAND_FIRST"),("Cruz","F97_HUSBAND_MIDDLE"),("Valdes","F97_HUSBAND_LAST"),("37","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Rolando","F97_HUSBAND_FATHER_FIRST"),("Valdes","F97_HUSBAND_FATHER_LAST"),("Rosita","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Cruz","F97_HUSBAND_MOTHER_LAST"),("Dianne","F97_WIFE_FIRST"),("Flores","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("34","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Arsenio","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Priscilla","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Flores","F97_WIFE_MOTHER_LAST"),("August 8, 2016","F97_DATE_OF_MARRIAGE"),("Davao City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2012-MC-033\nMC Date of Registration: July 22, 2012\nHusband (First): Leo\nHusband (Middle): Soriano\nHusband (Last): Manalo\nHusband AGE: 39\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Ernesto (Last): Manalo\nHusband NAME OF MOTHER (First): Leonora (Last): Soriano\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Trina\nWife (Middle): Ocampo\nWife (Last): Santos\nWife AGE: 36\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Esteban (Last): Santos\nWife NAME OF MOTHER (First): Felicitas (Last): Ocampo\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: July 14, 2012\nPLACE OF MARRIAGE: Malate Church, Manila")
    examples.append((t, {"entities": make_entities(t, [(("2012-MC-033","F97_REGISTRY_NO")),("July 22, 2012","F97_DATE_OF_REGISTRATION"),("Leo","F97_HUSBAND_FIRST"),("Soriano","F97_HUSBAND_MIDDLE"),("Manalo","F97_HUSBAND_LAST"),("39","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Ernesto","F97_HUSBAND_FATHER_FIRST"),("Manalo","F97_HUSBAND_FATHER_LAST"),("Leonora","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Soriano","F97_HUSBAND_MOTHER_LAST"),("Trina","F97_WIFE_FIRST"),("Ocampo","F97_WIFE_MIDDLE"),("Santos","F97_WIFE_LAST"),("36","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Esteban","F97_WIFE_FATHER_FIRST"),("Santos","F97_WIFE_FATHER_LAST"),("Felicitas","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Ocampo","F97_WIFE_MOTHER_LAST"),("July 14, 2012","F97_DATE_OF_MARRIAGE"),("Malate Church, Manila","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2024-MC-009\nMC Date of Registration: March 18, 2024\nHusband (First): Mario\nHusband (Middle): Reyes\nHusband (Last): Dizon\nHusband AGE: 26\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Celso (Last): Dizon\nHusband NAME OF MOTHER (First): Remedios (Last): Reyes\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Susan\nWife (Middle): Villanueva\nWife (Last): Cruz\nWife AGE: 24\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Rogelio (Last): Cruz\nWife NAME OF MOTHER (First): Belen (Last): Villanueva\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: March 8, 2024\nPLACE OF MARRIAGE: Vigan City")
    examples.append((t, {"entities": make_entities(t, [(("2024-MC-009","F97_REGISTRY_NO")),("March 18, 2024","F97_DATE_OF_REGISTRATION"),("Mario","F97_HUSBAND_FIRST"),("Reyes","F97_HUSBAND_MIDDLE"),("Dizon","F97_HUSBAND_LAST"),("26","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Celso","F97_HUSBAND_FATHER_FIRST"),("Dizon","F97_HUSBAND_FATHER_LAST"),("Remedios","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Reyes","F97_HUSBAND_MOTHER_LAST"),("Susan","F97_WIFE_FIRST"),("Villanueva","F97_WIFE_MIDDLE"),("Cruz","F97_WIFE_LAST"),("24","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Rogelio","F97_WIFE_FATHER_FIRST"),("Cruz","F97_WIFE_FATHER_LAST"),("Belen","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Villanueva","F97_WIFE_MOTHER_LAST"),("March 8, 2024","F97_DATE_OF_MARRIAGE"),("Vigan City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2025-MC-011\nMC Date of Registration: January 28, 2025\nHusband (First): Paolo\nHusband (Middle): Mendez\nHusband (Last): Garcia\nHusband AGE: 28\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Ricardo (Last): Garcia\nHusband NAME OF MOTHER (First): Erlinda (Last): Mendez\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Yvonne\nWife (Middle): Reyes\nWife (Last): Dela Cruz\nWife AGE: 25\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Bernardo (Last): Dela Cruz\nWife NAME OF MOTHER (First): Dolores (Last): Reyes\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: January 18, 2025\nPLACE OF MARRIAGE: Butuan City")
    examples.append((t, {"entities": make_entities(t, [(("2025-MC-011","F97_REGISTRY_NO")),("January 28, 2025","F97_DATE_OF_REGISTRATION"),("Paolo","F97_HUSBAND_FIRST"),("Mendez","F97_HUSBAND_MIDDLE"),("Garcia","F97_HUSBAND_LAST"),("28","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Ricardo","F97_HUSBAND_FATHER_FIRST"),("Garcia","F97_HUSBAND_FATHER_LAST"),("Erlinda","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Mendez","F97_HUSBAND_MOTHER_LAST"),("Yvonne","F97_WIFE_FIRST"),("Reyes","F97_WIFE_MIDDLE"),("Dela Cruz","F97_WIFE_LAST"),("25","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Bernardo","F97_WIFE_FATHER_FIRST"),("Dela Cruz","F97_WIFE_FATHER_LAST"),("Dolores","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Reyes","F97_WIFE_MOTHER_LAST"),("January 18, 2025","F97_DATE_OF_MARRIAGE"),("Butuan City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2011-MC-055\nMC Date of Registration: August 20, 2011\nHusband (First): Edwin\nHusband (Middle): Castillo\nHusband (Last): Reyes\nHusband AGE: 41\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Victorino (Last): Reyes\nHusband NAME OF MOTHER (First): Erlinda (Last): Castillo\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Luz\nWife (Middle): Navarro\nWife (Last): Santos\nWife AGE: 38\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Gregorio (Last): Santos\nWife NAME OF MOTHER (First): Perlita (Last): Navarro\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: March 3, 2008\nPLACE OF MARRIAGE: Pampanga")
    examples.append((t, {"entities": make_entities(t, [(("2011-MC-055","F97_REGISTRY_NO")),("August 20, 2011","F97_DATE_OF_REGISTRATION"),("Edwin","F97_HUSBAND_FIRST"),("Castillo","F97_HUSBAND_MIDDLE"),("Reyes","F97_HUSBAND_LAST"),("41","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Victorino","F97_HUSBAND_FATHER_FIRST"),("Reyes","F97_HUSBAND_FATHER_LAST"),("Erlinda","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Castillo","F97_HUSBAND_MOTHER_LAST"),("Luz","F97_WIFE_FIRST"),("Navarro","F97_WIFE_MIDDLE"),("Santos","F97_WIFE_LAST"),("38","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Gregorio","F97_WIFE_FATHER_FIRST"),("Santos","F97_WIFE_FATHER_LAST"),("Perlita","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Navarro","F97_WIFE_MOTHER_LAST"),("March 3, 2008","F97_DATE_OF_MARRIAGE"),("Pampanga","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2018-MC-033\nMC Date of Registration: August 18, 2018\nHusband (First): Arnold\nHusband (Middle): Ramos\nHusband (Last): Villanueva\nHusband AGE: 27\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Noel (Last): Villanueva\nHusband NAME OF MOTHER (First): Mercedita (Last): Ramos\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Jasmine\nWife (Middle): Cruz\nWife (Last): Padilla\nWife AGE: 24\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Danilo (Last): Padilla\nWife NAME OF MOTHER (First): Soledad (Last): Cruz\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: April 20, 2023\nPLACE OF MARRIAGE: Laguna")
    examples.append((t, {"entities": make_entities(t, [(("2018-MC-033","F97_REGISTRY_NO")),("August 18, 2018","F97_DATE_OF_REGISTRATION"),("Arnold","F97_HUSBAND_FIRST"),("Ramos","F97_HUSBAND_MIDDLE"),("Villanueva","F97_HUSBAND_LAST"),("27","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Noel","F97_HUSBAND_FATHER_FIRST"),("Villanueva","F97_HUSBAND_FATHER_LAST"),("Mercedita","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Ramos","F97_HUSBAND_MOTHER_LAST"),("Jasmine","F97_WIFE_FIRST"),("Cruz","F97_WIFE_MIDDLE"),("Padilla","F97_WIFE_LAST"),("24","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Danilo","F97_WIFE_FATHER_FIRST"),("Padilla","F97_WIFE_FATHER_LAST"),("Soledad","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Cruz","F97_WIFE_MOTHER_LAST"),("April 20, 2023","F97_DATE_OF_MARRIAGE"),("Laguna","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2017-MC-066\nMC Date of Registration: April 30, 2017\nHusband (First): Neil\nHusband (Middle): Santos\nHusband (Last): Bernardo\nHusband AGE: 35\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Domingo (Last): Bernardo\nHusband NAME OF MOTHER (First): Norma (Last): Santos\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Vanessa\nWife (Middle): Cruz\nWife (Last): Lopez\nWife AGE: 32\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Aurelio (Last): Lopez\nWife NAME OF MOTHER (First): Generosa (Last): Cruz\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: April 25, 2017\nPLACE OF MARRIAGE: Tuguegarao City")
    examples.append((t, {"entities": make_entities(t, [(("2017-MC-066","F97_REGISTRY_NO")),("April 30, 2017","F97_DATE_OF_REGISTRATION"),("Neil","F97_HUSBAND_FIRST"),("Santos","F97_HUSBAND_MIDDLE"),("Bernardo","F97_HUSBAND_LAST"),("35","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Domingo","F97_HUSBAND_FATHER_FIRST"),("Bernardo","F97_HUSBAND_FATHER_LAST"),("Norma","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Santos","F97_HUSBAND_MOTHER_LAST"),("Vanessa","F97_WIFE_FIRST"),("Cruz","F97_WIFE_MIDDLE"),("Lopez","F97_WIFE_LAST"),("32","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Aurelio","F97_WIFE_FATHER_FIRST"),("Lopez","F97_WIFE_FATHER_LAST"),("Generosa","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Cruz","F97_WIFE_MOTHER_LAST"),("April 25, 2017","F97_DATE_OF_MARRIAGE"),("Tuguegarao City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2018-MC-111\nMC Date of Registration: November 20, 2018\nHusband (First): Oscar\nHusband (Middle): Aquino\nHusband (Last): Reyes\nHusband AGE: 43\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Rolando (Last): Reyes\nHusband NAME OF MOTHER (First): Marivic (Last): Aquino\nWife\nHusband Father Citizenship: Filipino\nHusband Mother Citizenship: Filipino (First): Wendy\nWife (Middle): Flores\nWife (Last): Santos\nWife AGE: 39\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Hilario (Last): Santos\nWife NAME OF MOTHER (First): Concepcion (Last): Flores\nDATE\nWife Father Citizenship: Filipino\nWife Mother Citizenship: Filipino OF MARRIAGE: August 30, 2011\nPLACE OF MARRIAGE: Calbayog City")
    examples.append((t, {"entities": make_entities(t, [(("2018-MC-111","F97_REGISTRY_NO")),("November 20, 2018","F97_DATE_OF_REGISTRATION"),("Oscar","F97_HUSBAND_FIRST"),("Aquino","F97_HUSBAND_MIDDLE"),("Reyes","F97_HUSBAND_LAST"),("43","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Rolando","F97_HUSBAND_FATHER_FIRST"),("Reyes","F97_HUSBAND_FATHER_LAST"),("Marivic","F97_HUSBAND_MOTHER_FIRST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Aquino","F97_HUSBAND_MOTHER_LAST"),("Wendy","F97_WIFE_FIRST"),("Flores","F97_WIFE_MIDDLE"),("Santos","F97_WIFE_LAST"),("39","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Hilario","F97_WIFE_FATHER_FIRST"),("Santos","F97_WIFE_FATHER_LAST"),("Concepcion","F97_WIFE_MOTHER_FIRST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("Flores","F97_WIFE_MOTHER_LAST"),("August 30, 2011","F97_DATE_OF_MARRIAGE"),("Calbayog City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2018-MC-155\nMC Date of Registration: November 20, 2018\nHusband (First): Quentin (Middle): dela Cruz (Last): Torres\nHusband AGE: 33\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Proceso (Last): Torres\nHusband NAME OF MOTHER (First): Estelita (Last): dela\nHusband Father Citizenship: American\nHusband Mother Citizenship: American Cruz\nWife (First): Zara\nWife (Middle): Santos\nWife (Last): Reyes\nWife AGE: 30\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Crisanto (Last): Reyes\nWife NAME OF MOTHER (First): Amparo (Last): Santos\nDATE\nWife Father Citizenship: American\nWife Mother Citizenship: American OF MARRIAGE: November 1, 2018\nPLACE OF MARRIAGE: General Santos City")
    examples.append((t, {"entities": make_entities(t, [(("2018-MC-155","F97_REGISTRY_NO")),("November 20, 2018","F97_DATE_OF_REGISTRATION"),("Quentin","F97_HUSBAND_FIRST"),("dela Cruz","F97_HUSBAND_MIDDLE"),("Torres","F97_HUSBAND_LAST"),("33","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Proceso","F97_HUSBAND_FATHER_FIRST"),("Torres","F97_HUSBAND_FATHER_LAST"),("Estelita","F97_HUSBAND_MOTHER_FIRST"),("American","F97_HUSBAND_FATHER_CITIZENSHIP"),("American","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Zara","F97_WIFE_FIRST"),("Santos","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("30","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Crisanto","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Amparo","F97_WIFE_MOTHER_FIRST"),("American","F97_WIFE_FATHER_CITIZENSHIP"),("American","F97_WIFE_MOTHER_CITIZENSHIP"),("Santos","F97_WIFE_MOTHER_LAST"),("November 1, 2018","F97_DATE_OF_MARRIAGE"),("General Santos City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2013-MC-099\nMC Date of Registration: October 10, 2013\nHusband (First): Ruel\nHusband (Middle): Bautista\nHusband (Last): Hernandez\nHusband AGE: 34\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Amado (Last): Hernandez\nHusband NAME OF MOTHER (First): Perla (Last): Bautista\nWife\nHusband Father Citizenship: American\nHusband Mother Citizenship: American (First): Vivian\nWife (Middle): Reyes\nWife (Last): Castillo\nWife AGE: 31\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Porfirio (Last): Castillo\nWife NAME OF MOTHER (First): Carina (Last): Reyes\nDATE\nWife Father Citizenship: American\nWife Mother Citizenship: American OF MARRIAGE: September 28, 2013\nPLACE OF MARRIAGE: Tacloban City")
    examples.append((t, {"entities": make_entities(t, [(("2013-MC-099","F97_REGISTRY_NO")),("October 10, 2013","F97_DATE_OF_REGISTRATION"),("Ruel","F97_HUSBAND_FIRST"),("Bautista","F97_HUSBAND_MIDDLE"),("Hernandez","F97_HUSBAND_LAST"),("34","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Amado","F97_HUSBAND_FATHER_FIRST"),("Hernandez","F97_HUSBAND_FATHER_LAST"),("Perla","F97_HUSBAND_MOTHER_FIRST"),("American","F97_HUSBAND_FATHER_CITIZENSHIP"),("American","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Bautista","F97_HUSBAND_MOTHER_LAST"),("Vivian","F97_WIFE_FIRST"),("Reyes","F97_WIFE_MIDDLE"),("Castillo","F97_WIFE_LAST"),("31","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Porfirio","F97_WIFE_FATHER_FIRST"),("Castillo","F97_WIFE_FATHER_LAST"),("Carina","F97_WIFE_MOTHER_FIRST"),("American","F97_WIFE_FATHER_CITIZENSHIP"),("American","F97_WIFE_MOTHER_CITIZENSHIP"),("Reyes","F97_WIFE_MOTHER_LAST"),("September 28, 2013","F97_DATE_OF_MARRIAGE"),("Tacloban City","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2007-MC-044\nMC Date of Registration: April 20, 2007\nHusband (First): Dindo\nHusband (Middle): Soriano\nHusband (Last): Pascual\nHusband AGE: 29\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Simplicio (Last): Pascual\nHusband NAME OF MOTHER (First): Clarita (Last): Soriano\nWife\nHusband Father Citizenship: American\nHusband Mother Citizenship: American (First): Rowena\nWife (Middle): Santos\nWife (Last): Flores\nWife AGE: 26\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Isidro (Last): Flores\nWife NAME OF MOTHER (First): Nilda (Last): Santos\nDATE\nWife Father Citizenship: American\nWife Mother Citizenship: American OF MARRIAGE: April 7, 2007\nPLACE OF MARRIAGE: Camarines Sur")
    examples.append((t, {"entities": make_entities(t, [(("2007-MC-044","F97_REGISTRY_NO")),("April 20, 2007","F97_DATE_OF_REGISTRATION"),("Dindo","F97_HUSBAND_FIRST"),("Soriano","F97_HUSBAND_MIDDLE"),("Pascual","F97_HUSBAND_LAST"),("29","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Simplicio","F97_HUSBAND_FATHER_FIRST"),("Pascual","F97_HUSBAND_FATHER_LAST"),("Clarita","F97_HUSBAND_MOTHER_FIRST"),("American","F97_HUSBAND_FATHER_CITIZENSHIP"),("American","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Soriano","F97_HUSBAND_MOTHER_LAST"),("Rowena","F97_WIFE_FIRST"),("Santos","F97_WIFE_MIDDLE"),("Flores","F97_WIFE_LAST"),("26","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Isidro","F97_WIFE_FATHER_FIRST"),("Flores","F97_WIFE_FATHER_LAST"),("Nilda","F97_WIFE_MOTHER_FIRST"),("American","F97_WIFE_FATHER_CITIZENSHIP"),("American","F97_WIFE_MOTHER_CITIZENSHIP"),("Santos","F97_WIFE_MOTHER_LAST"),("April 7, 2007","F97_DATE_OF_MARRIAGE"),("Camarines Sur","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2014-MC-055\nMC Date of Registration: March 15, 2014\nHusband (First): Erick\nHusband (Middle): Villanueva\nHusband (Last): Medina\nHusband AGE: 27\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Efren (Last): Medina\nHusband NAME OF MOTHER (First): Natividad (Last): Villanueva\nWife\nHusband Father Citizenship: American\nHusband Mother Citizenship: American (First): Joanna (Middle): dela Cruz (Last): Ramos\nWife AGE: 25\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Wilfredo (Last): Ramos\nWife NAME OF MOTHER (First): Resurreccion (Last): dela\nWife Father Citizenship: American\nWife Mother Citizenship: American Cruz\nDATE OF MARRIAGE: March 1, 2014\nPLACE OF MARRIAGE: Palawan")
    examples.append((t, {"entities": make_entities(t, [(("2014-MC-055","F97_REGISTRY_NO")),("March 15, 2014","F97_DATE_OF_REGISTRATION"),("Erick","F97_HUSBAND_FIRST"),("Villanueva","F97_HUSBAND_MIDDLE"),("Medina","F97_HUSBAND_LAST"),("27","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Efren","F97_HUSBAND_FATHER_FIRST"),("Medina","F97_HUSBAND_FATHER_LAST"),("Natividad","F97_HUSBAND_MOTHER_FIRST"),("American","F97_HUSBAND_FATHER_CITIZENSHIP"),("American","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Villanueva","F97_HUSBAND_MOTHER_LAST"),("Joanna","F97_WIFE_FIRST"),("dela Cruz","F97_WIFE_MIDDLE"),("Ramos","F97_WIFE_LAST"),("25","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Wilfredo","F97_WIFE_FATHER_FIRST"),("Ramos","F97_WIFE_FATHER_LAST"),("Resurreccion","F97_WIFE_MOTHER_FIRST"),("American","F97_WIFE_FATHER_CITIZENSHIP"),("American","F97_WIFE_MOTHER_CITIZENSHIP"),("March 1, 2014","F97_DATE_OF_MARRIAGE"),("Palawan","F97_PLACE_OF_MARRIAGE")])}))

    t = ("Registry No.: 2024-MC-077\nMC Date of Registration: August 8, 2024\nHusband (First): Kenneth\nHusband (Middle): Garcia\nHusband (Last): Pascual\nHusband AGE: 31\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband NAME OF FATHER (First): Hernando (Last): Pascual\nHusband NAME OF MOTHER (First): Norma (Last): Garcia\nWife\nHusband Father Citizenship: American\nHusband Mother Citizenship: American (First): Rachel (Middle): dela Cruz (Last): Reyes\nWife AGE: 28\nWife CITIZENSHIP: Filipino\nWife NAME OF FATHER (First): Celestino (Last): Reyes\nWife NAME OF MOTHER (First): Emelinda (Last): dela\nWife Father Citizenship: American\nWife Mother Citizenship: American Cruz\nDATE OF MARRIAGE: May 1, 2021\nPLACE OF MARRIAGE: Tagaytay City")
    examples.append((t, {"entities": make_entities(t, [(("2024-MC-077","F97_REGISTRY_NO")),("August 8, 2024","F97_DATE_OF_REGISTRATION"),("Kenneth","F97_HUSBAND_FIRST"),("Garcia","F97_HUSBAND_MIDDLE"),("Pascual","F97_HUSBAND_LAST"),("31","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Hernando","F97_HUSBAND_FATHER_FIRST"),("Pascual","F97_HUSBAND_FATHER_LAST"),("Norma","F97_HUSBAND_MOTHER_FIRST"),("American","F97_HUSBAND_FATHER_CITIZENSHIP"),("American","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Garcia","F97_HUSBAND_MOTHER_LAST"),("Rachel","F97_WIFE_FIRST"),("dela Cruz","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("28","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Celestino","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Emelinda","F97_WIFE_MOTHER_FIRST"),("American","F97_WIFE_FATHER_CITIZENSHIP"),("American","F97_WIFE_MOTHER_CITIZENSHIP"),("May 1, 2021","F97_DATE_OF_MARRIAGE"),("Tagaytay City","F97_PLACE_OF_MARRIAGE")])}))


    # Extra examples targeting: HUSBAND_RELIGION, WIFE_MIDDLE, WIFE_CITIZENSHIP
    t = "Registry No.: 2022-MC-011\nMC Date of Registration: February 20, 2022\n19. HUSBAND (First): Patrick (Middle): Soriano (Last): Navarro\nAge: 30\nCitizenship: Filipino\nReligion: Roman Catholic\nCivil Status: Single\n20. WIFE (First): Donna (Middle): Evangelista (Last): Cruz\nAge: 27\nCitizenship: Filipino\n21. DATE OF MARRIAGE: February 14, 2022\n22. PLACE OF MARRIAGE: Makati City"
    examples.append((t, {"entities": make_entities(t, [("2022-MC-011","F97_REGISTRY_NO"),("February 20, 2022","F97_DATE_OF_REGISTRATION"),("Patrick","F97_HUSBAND_FIRST"),("Soriano","F97_HUSBAND_MIDDLE"),("Navarro","F97_HUSBAND_LAST"),("30","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Donna","F97_WIFE_FIRST"),("Evangelista","F97_WIFE_MIDDLE"),("Cruz","F97_WIFE_LAST"),("27","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("February 14, 2022","F97_DATE_OF_MARRIAGE"),("Makati City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2019-MC-044\nMC Date of Registration: November 5, 2019\n19. HUSBAND (First): Rodrigo (Middle): dela Torre (Last): Villanueva\nAge: 35\nCitizenship: Filipino\nReligion: Iglesia ni Cristo\nCivil Status: Single\n20. WIFE (First): Precious (Middle): Buenaventura (Last): Hernandez\nAge: 32\nCitizenship: Filipino\n21. DATE OF MARRIAGE: October 31, 2019\n22. PLACE OF MARRIAGE: Quezon City"
    examples.append((t, {"entities": make_entities(t, [("2019-MC-044","F97_REGISTRY_NO"),("November 5, 2019","F97_DATE_OF_REGISTRATION"),("Rodrigo","F97_HUSBAND_FIRST"),("dela Torre","F97_HUSBAND_MIDDLE"),("Villanueva","F97_HUSBAND_LAST"),("35","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Precious","F97_WIFE_FIRST"),("Buenaventura","F97_WIFE_MIDDLE"),("Hernandez","F97_WIFE_LAST"),("32","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("October 31, 2019","F97_DATE_OF_MARRIAGE"),("Quezon City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2015-MC-088\nMC Date of Registration: June 15, 2015\n19. HUSBAND (First): Erwin (Middle): Pascual (Last): Bautista\nAge: 29\nCitizenship: Filipino\nReligion: Aglipayan\nCivil Status: Single\n20. WIFE (First): Sheila (Middle): Tolentino (Last): Reyes\nAge: 26\nCitizenship: Filipino\n21. DATE OF MARRIAGE: June 10, 2015\n22. PLACE OF MARRIAGE: Cebu City"
    examples.append((t, {"entities": make_entities(t, [("2015-MC-088","F97_REGISTRY_NO"),("June 15, 2015","F97_DATE_OF_REGISTRATION"),("Erwin","F97_HUSBAND_FIRST"),("Pascual","F97_HUSBAND_MIDDLE"),("Bautista","F97_HUSBAND_LAST"),("29","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Sheila","F97_WIFE_FIRST"),("Tolentino","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("26","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("June 10, 2015","F97_DATE_OF_MARRIAGE"),("Cebu City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2018-MC-033\nMC Date of Registration: September 2, 2018\n19. HUSBAND (First): Vincent (Middle): Magno (Last): Santos\nAge: 33\nCitizenship: Filipino\nReligion: Born Again Christian\nCivil Status: Single\n20. WIFE (First): Abigail (Middle): Ferrer (Last): Torres\nAge: 30\nCitizenship: Filipino\n21. DATE OF MARRIAGE: August 25, 2018\n22. PLACE OF MARRIAGE: Davao City"
    examples.append((t, {"entities": make_entities(t, [("2018-MC-033","F97_REGISTRY_NO"),("September 2, 2018","F97_DATE_OF_REGISTRATION"),("Vincent","F97_HUSBAND_FIRST"),("Magno","F97_HUSBAND_MIDDLE"),("Santos","F97_HUSBAND_LAST"),("33","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Abigail","F97_WIFE_FIRST"),("Ferrer","F97_WIFE_MIDDLE"),("Torres","F97_WIFE_LAST"),("30","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("August 25, 2018","F97_DATE_OF_MARRIAGE"),("Davao City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2020-MC-077\nMC Date of Registration: March 10, 2020\n19. HUSBAND (First): Gerald (Middle): Catalan (Last): Marquez\nAge: 28\nCitizenship: Filipino\nReligion: Roman Catholic\nCivil Status: Single\n20. WIFE (First): Camille (Middle): Aguilar (Last): Ramos\nAge: 25\nCitizenship: Filipino\n21. DATE OF MARRIAGE: March 5, 2020\n22. PLACE OF MARRIAGE: Taguig City"
    examples.append((t, {"entities": make_entities(t, [("2020-MC-077","F97_REGISTRY_NO"),("March 10, 2020","F97_DATE_OF_REGISTRATION"),("Gerald","F97_HUSBAND_FIRST"),("Catalan","F97_HUSBAND_MIDDLE"),("Marquez","F97_HUSBAND_LAST"),("28","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Camille","F97_WIFE_FIRST"),("Aguilar","F97_WIFE_MIDDLE"),("Ramos","F97_WIFE_LAST"),("25","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("March 5, 2020","F97_DATE_OF_MARRIAGE"),("Taguig City","F97_PLACE_OF_MARRIAGE")])}))


    # Extra examples with PARENT CITIZENSHIP (F97_HUSBAND/WIFE_FATHER/MOTHER_CITIZENSHIP)
    t = "Registry No.: 2021-MC-055\nMC Date of Registration: July 15, 2021\nHusband (First): Marco (Middle): Dela Cruz (Last): Santos\nHusband AGE: 31\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband RELIGION: Roman Catholic\nHusband NAME OF FATHER (First): Roberto (Middle): Santos (Last): Santos\nHusband FATHER CITIZENSHIP: Filipino\nHusband NAME OF MOTHER (First): Luisa (Middle): Reyes (Last): Dela Cruz\nHusband MOTHER CITIZENSHIP: Filipino\nWife (First): Angela\nWife (Middle): Torres\nWife (Last): Mendoza\nWife AGE: 28\nWife CITIZENSHIP: Filipino\nWife Civil Status: Single\nWife NAME OF FATHER (First): Ernesto (Middle): Mendoza (Last): Mendoza\nWife FATHER CITIZENSHIP: Filipino\nWife NAME OF MOTHER (First): Cristina (Middle): Lim (Last): Torres\nWife MOTHER CITIZENSHIP: Filipino\nDATE OF MARRIAGE: July 10, 2021\nPLACE OF MARRIAGE: Quezon City Hall"
    examples.append((t, {"entities": make_entities(t, [("2021-MC-055","F97_REGISTRY_NO"),("July 15, 2021","F97_DATE_OF_REGISTRATION"),("Marco","F97_HUSBAND_FIRST"),("Dela Cruz","F97_HUSBAND_MIDDLE"),("Santos","F97_HUSBAND_LAST"),("31","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Roberto","F97_HUSBAND_FATHER_FIRST"),("Santos","F97_HUSBAND_FATHER_LAST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Luisa","F97_HUSBAND_MOTHER_FIRST"),("Dela Cruz","F97_HUSBAND_MOTHER_LAST"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Angela","F97_WIFE_FIRST"),("Torres","F97_WIFE_MIDDLE"),("Mendoza","F97_WIFE_LAST"),("28","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Ernesto","F97_WIFE_FATHER_FIRST"),("Mendoza","F97_WIFE_FATHER_LAST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Cristina","F97_WIFE_MOTHER_FIRST"),("Torres","F97_WIFE_MOTHER_LAST"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("July 10, 2021","F97_DATE_OF_MARRIAGE"),("Quezon City Hall","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2020-MC-099\nMC Date of Registration: December 5, 2020\nHusband (First): Bryan\nHusband (Middle): Ocampo\nHusband (Last): Villanueva\nHusband AGE: 27\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband RELIGION: Iglesia ni Cristo\nHusband NAME OF FATHER (First): Eduardo (Middle): Villanueva (Last): Villanueva\nHusband FATHER CITIZENSHIP: Filipino\nHusband NAME OF MOTHER (First): Marites (Middle): Pascual (Last): Ocampo\nHusband MOTHER CITIZENSHIP: Filipino\nWife (First): Joanna\nWife (Middle): Castillo\nWife (Last): Reyes\nWife AGE: 25\nWife CITIZENSHIP: Filipino\nWife Civil Status: Single\nWife NAME OF FATHER (First): Alfredo (Middle): Reyes (Last): Reyes\nWife FATHER CITIZENSHIP: Filipino\nWife NAME OF MOTHER (First): Nora (Middle): Gutierrez (Last): Castillo\nWife MOTHER CITIZENSHIP: Filipino\nDATE OF MARRIAGE: November 28, 2020\nPLACE OF MARRIAGE: Cebu City"
    examples.append((t, {"entities": make_entities(t, [("2020-MC-099","F97_REGISTRY_NO"),("December 5, 2020","F97_DATE_OF_REGISTRATION"),("Bryan","F97_HUSBAND_FIRST"),("Ocampo","F97_HUSBAND_MIDDLE"),("Villanueva","F97_HUSBAND_LAST"),("27","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Eduardo","F97_HUSBAND_FATHER_FIRST"),("Villanueva","F97_HUSBAND_FATHER_LAST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Marites","F97_HUSBAND_MOTHER_FIRST"),("Ocampo","F97_HUSBAND_MOTHER_LAST"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Joanna","F97_WIFE_FIRST"),("Castillo","F97_WIFE_MIDDLE"),("Reyes","F97_WIFE_LAST"),("25","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Alfredo","F97_WIFE_FATHER_FIRST"),("Reyes","F97_WIFE_FATHER_LAST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Nora","F97_WIFE_MOTHER_FIRST"),("Castillo","F97_WIFE_MOTHER_LAST"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("November 28, 2020","F97_DATE_OF_MARRIAGE"),("Cebu City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2019-MC-077\nMC Date of Registration: August 20, 2019\nHusband (First): Carlo\nHusband (Middle): Navarro\nHusband (Last): Bautista\nHusband AGE: 34\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband RELIGION: Aglipayan\nHusband NAME OF FATHER (First): Dominic (Middle): Bautista (Last): Bautista\nHusband FATHER CITIZENSHIP: Filipino\nHusband NAME OF MOTHER (First): Rowena (Middle): Cruz (Last): Navarro\nHusband MOTHER CITIZENSHIP: Filipino\nWife (First): Shirley\nWife (Middle): Ferrer\nWife (Last): Garcia\nWife AGE: 30\nWife CITIZENSHIP: Filipino\nWife Civil Status: Single\nWife NAME OF FATHER (First): Ramon (Middle): Garcia (Last): Garcia\nWife FATHER CITIZENSHIP: Filipino\nWife NAME OF MOTHER (First): Cecilia (Middle): Padilla (Last): Ferrer\nWife MOTHER CITIZENSHIP: Filipino\nDATE OF MARRIAGE: August 15, 2019\nPLACE OF MARRIAGE: Davao City"
    examples.append((t, {"entities": make_entities(t, [("2019-MC-077","F97_REGISTRY_NO"),("August 20, 2019","F97_DATE_OF_REGISTRATION"),("Carlo","F97_HUSBAND_FIRST"),("Navarro","F97_HUSBAND_MIDDLE"),("Bautista","F97_HUSBAND_LAST"),("34","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Dominic","F97_HUSBAND_FATHER_FIRST"),("Bautista","F97_HUSBAND_FATHER_LAST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Rowena","F97_HUSBAND_MOTHER_FIRST"),("Navarro","F97_HUSBAND_MOTHER_LAST"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Shirley","F97_WIFE_FIRST"),("Ferrer","F97_WIFE_MIDDLE"),("Garcia","F97_WIFE_LAST"),("30","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Ramon","F97_WIFE_FATHER_FIRST"),("Garcia","F97_WIFE_FATHER_LAST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Cecilia","F97_WIFE_MOTHER_FIRST"),("Ferrer","F97_WIFE_MOTHER_LAST"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("August 15, 2019","F97_DATE_OF_MARRIAGE"),("Davao City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2023-MC-012\nMC Date of Registration: March 5, 2023\nHusband (First): Jerome\nHusband (Middle): Espiritu\nHusband (Last): Ramos\nHusband AGE: 29\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband RELIGION: Born Again Christian\nHusband NAME OF FATHER (First): Arsenio (Middle): Ramos (Last): Ramos\nHusband FATHER CITIZENSHIP: Filipino\nHusband NAME OF MOTHER (First): Felisa (Middle): Torres (Last): Espiritu\nHusband MOTHER CITIZENSHIP: Filipino\nWife (First): Hazel\nWife (Middle): Aguilar\nWife (Last): Dela Cruz\nWife AGE: 26\nWife CITIZENSHIP: Filipino\nWife Civil Status: Single\nWife NAME OF FATHER (First): Crisanto (Middle): Dela Cruz (Last): Dela Cruz\nWife FATHER CITIZENSHIP: Filipino\nWife NAME OF MOTHER (First): Imelda (Middle): Soriano (Last): Aguilar\nWife MOTHER CITIZENSHIP: Filipino\nDATE OF MARRIAGE: February 25, 2023\nPLACE OF MARRIAGE: Iloilo City"
    examples.append((t, {"entities": make_entities(t, [("2023-MC-012","F97_REGISTRY_NO"),("March 5, 2023","F97_DATE_OF_REGISTRATION"),("Jerome","F97_HUSBAND_FIRST"),("Espiritu","F97_HUSBAND_MIDDLE"),("Ramos","F97_HUSBAND_LAST"),("29","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Arsenio","F97_HUSBAND_FATHER_FIRST"),("Ramos","F97_HUSBAND_FATHER_LAST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Felisa","F97_HUSBAND_MOTHER_FIRST"),("Espiritu","F97_HUSBAND_MOTHER_LAST"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Hazel","F97_WIFE_FIRST"),("Aguilar","F97_WIFE_MIDDLE"),("Dela Cruz","F97_WIFE_LAST"),("26","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Crisanto","F97_WIFE_FATHER_FIRST"),("Dela Cruz","F97_WIFE_FATHER_LAST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Imelda","F97_WIFE_MOTHER_FIRST"),("Aguilar","F97_WIFE_MOTHER_LAST"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("February 25, 2023","F97_DATE_OF_MARRIAGE"),("Iloilo City","F97_PLACE_OF_MARRIAGE")])}))

    t = "Registry No.: 2018-MC-044\nMC Date of Registration: May 12, 2018\nHusband (First): Anthony\nHusband (Middle): Villafuerte\nHusband (Last): Cruz\nHusband AGE: 32\nHusband CITIZENSHIP: Filipino\nHusband Civil Status: Single\nHusband RELIGION: Roman Catholic\nHusband NAME OF FATHER (First): Rogelio (Middle): Cruz (Last): Cruz\nHusband FATHER CITIZENSHIP: Filipino\nHusband NAME OF MOTHER (First): Divina (Middle): Magno (Last): Villafuerte\nHusband MOTHER CITIZENSHIP: Filipino\nWife (First): Lovely\nWife (Middle): Hernandez\nWife (Last): Santos\nWife AGE: 28\nWife CITIZENSHIP: Filipino\nWife Civil Status: Single\nWife NAME OF FATHER (First): Virgilio (Middle): Santos (Last): Santos\nWife FATHER CITIZENSHIP: Filipino\nWife NAME OF MOTHER (First): Milagros (Middle): Buenaventura (Last): Hernandez\nWife MOTHER CITIZENSHIP: Filipino\nDATE OF MARRIAGE: May 7, 2018\nPLACE OF MARRIAGE: Manila Cathedral"
    examples.append((t, {"entities": make_entities(t, [("2018-MC-044","F97_REGISTRY_NO"),("May 12, 2018","F97_DATE_OF_REGISTRATION"),("Anthony","F97_HUSBAND_FIRST"),("Villafuerte","F97_HUSBAND_MIDDLE"),("Cruz","F97_HUSBAND_LAST"),("32","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Rogelio","F97_HUSBAND_FATHER_FIRST"),("Cruz","F97_HUSBAND_FATHER_LAST"),("Filipino","F97_HUSBAND_FATHER_CITIZENSHIP"),("Divina","F97_HUSBAND_MOTHER_FIRST"),("Villafuerte","F97_HUSBAND_MOTHER_LAST"),("Filipino","F97_HUSBAND_MOTHER_CITIZENSHIP"),("Lovely","F97_WIFE_FIRST"),("Hernandez","F97_WIFE_MIDDLE"),("Santos","F97_WIFE_LAST"),("28","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Virgilio","F97_WIFE_FATHER_FIRST"),("Santos","F97_WIFE_FATHER_LAST"),("Filipino","F97_WIFE_FATHER_CITIZENSHIP"),("Milagros","F97_WIFE_MOTHER_FIRST"),("Hernandez","F97_WIFE_MOTHER_LAST"),("Filipino","F97_WIFE_MOTHER_CITIZENSHIP"),("May 7, 2018","F97_DATE_OF_MARRIAGE"),("Manila Cathedral","F97_PLACE_OF_MARRIAGE")])}))

    return examples


# ============================================================
# FORM 90 → FORM 54
# Source: Accountable Form No. 54 / Form No. 10
#         (Marriage License and Fee Receipt of Two Pesos)
#
# The document certifies that [GROOM NAME] aged [GROOM AGE],
# resident of [GROOM RESIDENCE] may legally contract marriage
# with [BRIDE NAME] aged [BRIDE AGE], resident of [BRIDE RESIDENCE].
# Issued on [DATE_OF_ISSUANCE].
#
# NER LABELS (F90_*):
#   F90_REGISTRY_NO          F90_DATE_OF_REGISTRATION
#   F90_GROOM_FIRST          F90_GROOM_MIDDLE     F90_GROOM_LAST
#   F90_GROOM_AGE            F90_GROOM_RESIDENCE
#   F90_BRIDE_FIRST          F90_BRIDE_MIDDLE     F90_BRIDE_LAST
#   F90_BRIDE_AGE            F90_BRIDE_RESIDENCE
#   F90_DATE_OF_ISSUANCE
# ============================================================


def form90_examples():
    examples = []

    # ── Example 1 — Based on actual Accountable Form No. 54 ──────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "Republic of the Philippines\n"
        "City or Municipality of Mandaluyong City\n"
        "Province of Metro Manila\n"
        "No. 5975035\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "This is to certify that Erastus Noel T. Delizo aged 42 years and 10 months\n"
        "and resident of No. 17 Tehran St., BF Homes International Las Pinas City\n"
        "may legally contract marriage\n"
        "with Maria Fatima A. Villena aged 30 years\n"
        "and resident of 709-A Coronado St., Brgy. Hulo Mandaluyong City\n"
        "having paid the license fee of P2.00 prescribed under\n"
        "Articles 65 of Republic Act No. 386.\n"
        "issued this 17th day of October, 2008\n"
        "MARRIAGE LICENSE VALID UNTIL FEB 13 2009\n"
        "Local Civil Registrar of Mandaluyong City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("5975035",                                           "F90_REGISTRY_NO"),
        ("Erastus",                                          "F90_GROOM_FIRST"),
        ("Noel T.",                                          "F90_GROOM_MIDDLE"),
        ("Delizo",                                           "F90_GROOM_LAST"),
        ("42",                                               "F90_GROOM_AGE"),
        ("No. 17 Tehran St., BF Homes International Las Pinas City", "F90_GROOM_RESIDENCE"),
        ("Maria",                                            "F90_BRIDE_FIRST"),
        ("Fatima A.",                                        "F90_BRIDE_MIDDLE"),
        ("Villena",                                          "F90_BRIDE_LAST"),
        ("30",                                               "F90_BRIDE_AGE"),
        ("709-A Coronado St., Brgy. Hulo Mandaluyong City",  "F90_BRIDE_RESIDENCE"),
        ("17th day of October, 2008",                        "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 2 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Quezon City\n"
        "No. 4812033\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: January 5, 2020\n"
        "This is to certify that Jose Santos Ramos aged 29 years\n"
        "and resident of 123 Rizal Street Makati City\n"
        "may legally contract marriage\n"
        "with Maria Garcia Torres aged 26 years\n"
        "and resident of 456 Mabini Avenue Quezon City\n"
        "license fee Articles 65 Republic Act No. 386\n"
        "issued this 5th day of January, 2020\n"
        "MARRIAGE LICENSE VALID UNTIL May 4, 2020\n"
        "Local Civil Registrar of Quezon City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("4812033",                       "F90_REGISTRY_NO"),
        ("January 5, 2020",              "F90_DATE_OF_REGISTRATION"),
        ("Jose",                          "F90_GROOM_FIRST"),
        ("Santos",                        "F90_GROOM_MIDDLE"),
        ("Ramos",                         "F90_GROOM_LAST"),
        ("29",                            "F90_GROOM_AGE"),
        ("123 Rizal Street Makati City",  "F90_GROOM_RESIDENCE"),
        ("Maria",                         "F90_BRIDE_FIRST"),
        ("Garcia",                        "F90_BRIDE_MIDDLE"),
        ("Torres",                        "F90_BRIDE_LAST"),
        ("26",                            "F90_BRIDE_AGE"),
        ("456 Mabini Avenue Quezon City", "F90_BRIDE_RESIDENCE"),
        ("5th day of January, 2020",      "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 3 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Taguig City\n"
        "No. 6023441\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: March 10, 2022\n"
        "This is to certify that Carlos Reyes Mendoza aged 35 years\n"
        "and resident of 88 Aurora Blvd., Brgy. Bagumbayan Taguig City\n"
        "may legally contract marriage\n"
        "with Ana dela Cruz Santos aged 31 years\n"
        "and resident of 22 Magsaysay Ave., Brgy. Hulo Mandaluyong City\n"
        "having paid the license fee prescribed under Articles 65 of Republic Act No. 386\n"
        "issued this 10th day of March, 2022\n"
        "MARRIAGE LICENSE VALID UNTIL July 7, 2022"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("6023441",                                            "F90_REGISTRY_NO"),
        ("March 10, 2022",                                    "F90_DATE_OF_REGISTRATION"),
        ("Carlos",                                             "F90_GROOM_FIRST"),
        ("Reyes",                                              "F90_GROOM_MIDDLE"),
        ("Mendoza",                                            "F90_GROOM_LAST"),
        ("35",                                                 "F90_GROOM_AGE"),
        ("88 Aurora Blvd., Brgy. Bagumbayan Taguig City",     "F90_GROOM_RESIDENCE"),
        ("Ana",                                                "F90_BRIDE_FIRST"),
        ("dela Cruz",                                          "F90_BRIDE_MIDDLE"),
        ("Santos",                                             "F90_BRIDE_LAST"),
        ("31",                                                 "F90_BRIDE_AGE"),
        ("22 Magsaysay Ave., Brgy. Hulo Mandaluyong City",    "F90_BRIDE_RESIDENCE"),
        ("10th day of March, 2022",                           "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 4 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Cebu City\n"
        "No. 3901122\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: July 20, 2019\n"
        "This is to certify that Roberto dela Cruz Villanueva aged 28 years\n"
        "and resident of 5 Osmena Blvd., Cebu City\n"
        "may legally contract marriage\n"
        "with Gloria Santos Aquino aged 25 years\n"
        "and resident of 10 Colon Street, Cebu City\n"
        "license fee P2.00 Articles 65 Republic Act No. 386\n"
        "issued this 20th day of July, 2019\n"
        "MARRIAGE LICENSE VALID UNTIL November 16, 2019\n"
        "Local Civil Registrar of Cebu City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("3901122",                     "F90_REGISTRY_NO"),
        ("July 20, 2019",              "F90_DATE_OF_REGISTRATION"),
        ("Roberto",                     "F90_GROOM_FIRST"),
        ("dela Cruz",                   "F90_GROOM_MIDDLE"),
        ("Villanueva",                  "F90_GROOM_LAST"),
        ("28",                          "F90_GROOM_AGE"),
        ("5 Osmena Blvd., Cebu City",  "F90_GROOM_RESIDENCE"),
        ("Gloria",                      "F90_BRIDE_FIRST"),
        ("Santos",                      "F90_BRIDE_MIDDLE"),
        ("Aquino",                      "F90_BRIDE_LAST"),
        ("25",                          "F90_BRIDE_AGE"),
        ("10 Colon Street, Cebu City", "F90_BRIDE_RESIDENCE"),
        ("20th day of July, 2019",     "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 5 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Davao City\n"
        "No. 7140089\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: 05/10/2021\n"
        "This is to certify that Pedro Bautista Flores aged 33 years\n"
        "and resident of 300 JP Laurel Ave., Davao City\n"
        "may legally contract marriage\n"
        "with Lourdes Navarro Castillo aged 30 years\n"
        "and resident of 45 Pichon Street, Davao City\n"
        "Articles 65 Republic Act No. 386\n"
        "issued this 10th day of May, 2021\n"
        "MARRIAGE LICENSE VALID UNTIL 09/06/2021"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("7140089",                         "F90_REGISTRY_NO"),
        ("05/10/2021",                      "F90_DATE_OF_REGISTRATION"),
        ("Pedro",                            "F90_GROOM_FIRST"),
        ("Bautista",                         "F90_GROOM_MIDDLE"),
        ("Flores",                           "F90_GROOM_LAST"),
        ("33",                               "F90_GROOM_AGE"),
        ("300 JP Laurel Ave., Davao City",  "F90_GROOM_RESIDENCE"),
        ("Lourdes",                          "F90_BRIDE_FIRST"),
        ("Navarro",                          "F90_BRIDE_MIDDLE"),
        ("Castillo",                         "F90_BRIDE_LAST"),
        ("30",                               "F90_BRIDE_AGE"),
        ("45 Pichon Street, Davao City",    "F90_BRIDE_RESIDENCE"),
        ("10th day of May, 2021",           "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 6 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Makati City\n"
        "No. 8812501\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: November 15, 2023\n"
        "This is to certify that Juan dela Paz Ocampo aged 40 years\n"
        "and resident of Unit 4B, Torre de Manila, Ermita, Manila\n"
        "may legally contract marriage\n"
        "with Elena Soriano Reyes aged 36 years\n"
        "and resident of 12 Gen. Luna Street, Intramuros, Manila\n"
        "license fee P2.00 prescribed under Articles 65 of Republic Act No. 386\n"
        "issued this 15th day of November, 2023\n"
        "MARRIAGE LICENSE VALID UNTIL March 13, 2024\n"
        "Local Civil Registrar of Makati City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("8812501",                                       "F90_REGISTRY_NO"),
        ("November 15, 2023",                            "F90_DATE_OF_REGISTRATION"),
        ("Juan",                                          "F90_GROOM_FIRST"),
        ("dela Paz",                                      "F90_GROOM_MIDDLE"),
        ("Ocampo",                                        "F90_GROOM_LAST"),
        ("40",                                            "F90_GROOM_AGE"),
        ("Unit 4B, Torre de Manila, Ermita, Manila",     "F90_GROOM_RESIDENCE"),
        ("Elena",                                         "F90_BRIDE_FIRST"),
        ("Soriano",                                       "F90_BRIDE_MIDDLE"),
        ("Reyes",                                         "F90_BRIDE_LAST"),
        ("36",                                            "F90_BRIDE_AGE"),
        ("12 Gen. Luna Street, Intramuros, Manila",      "F90_BRIDE_RESIDENCE"),
        ("15th day of November, 2023",                   "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 7 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Iloilo City\n"
        "No. 2255019\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: 14 February 2018\n"
        "This is to certify that Marco Espiritu Padilla aged 27 years\n"
        "and resident of Brgy. Molo, Iloilo City\n"
        "may legally contract marriage\n"
        "with Sheila Aguilar Navarro aged 24 years\n"
        "and resident of Brgy. La Paz, Iloilo City\n"
        "having paid the license fee prescribed under Articles 65 of Republic Act No. 386\n"
        "issued this 14th day of February, 2018\n"
        "MARRIAGE LICENSE VALID UNTIL June 13, 2018"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("2255019",                     "F90_REGISTRY_NO"),
        ("14 February 2018",           "F90_DATE_OF_REGISTRATION"),
        ("Marco",                       "F90_GROOM_FIRST"),
        ("Espiritu",                    "F90_GROOM_MIDDLE"),
        ("Padilla",                     "F90_GROOM_LAST"),
        ("27",                          "F90_GROOM_AGE"),
        ("Brgy. Molo, Iloilo City",    "F90_GROOM_RESIDENCE"),
        ("Sheila",                      "F90_BRIDE_FIRST"),
        ("Aguilar",                     "F90_BRIDE_MIDDLE"),
        ("Navarro",                     "F90_BRIDE_LAST"),
        ("24",                          "F90_BRIDE_AGE"),
        ("Brgy. La Paz, Iloilo City",  "F90_BRIDE_RESIDENCE"),
        ("14th day of February, 2018", "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 8 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Caloocan City\n"
        "No. 9030871\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: 08/22/2016\n"
        "This is to certify that Dante Aquino Villanueva aged 32 years\n"
        "and resident of 18 Samson Road, Caloocan City\n"
        "may legally contract marriage\n"
        "with Diana Cruz Santos aged 28 years\n"
        "and resident of 99 A. Mabini Street, Malabon City\n"
        "Articles 65 Republic Act No. 386\n"
        "issued this 22nd day of August, 2016\n"
        "MARRIAGE LICENSE VALID UNTIL 12/19/2016\n"
        "Local Civil Registrar of Caloocan City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("9030871",                             "F90_REGISTRY_NO"),
        ("08/22/2016",                          "F90_DATE_OF_REGISTRATION"),
        ("Dante",                                "F90_GROOM_FIRST"),
        ("Aquino",                               "F90_GROOM_MIDDLE"),
        ("Villanueva",                           "F90_GROOM_LAST"),
        ("32",                                   "F90_GROOM_AGE"),
        ("18 Samson Road, Caloocan City",       "F90_GROOM_RESIDENCE"),
        ("Diana",                                "F90_BRIDE_FIRST"),
        ("Cruz",                                 "F90_BRIDE_MIDDLE"),
        ("Santos",                               "F90_BRIDE_LAST"),
        ("28",                                   "F90_BRIDE_AGE"),
        ("99 A. Mabini Street, Malabon City",   "F90_BRIDE_RESIDENCE"),
        ("22nd day of August, 2016",            "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 9 ─────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Paranaque City\n"
        "No. 5501340\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: June 1, 2024\n"
        "This is to certify that Lester Gomez Padilla aged 33 years\n"
        "and resident of 7 BF Resort Village, Las Pinas City\n"
        "may legally contract marriage\n"
        "with Leslie Navarro Espiritu aged 29 years\n"
        "and resident of 3 Moonwalk Subdivision, Paranaque City\n"
        "having paid the license fee of P2.00 prescribed under Articles 65 of Republic Act No. 386\n"
        "issued this 1st day of June, 2024\n"
        "MARRIAGE LICENSE VALID UNTIL September 28, 2024\n"
        "Local Civil Registrar of Paranaque City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("5501340",                                   "F90_REGISTRY_NO"),
        ("June 1, 2024",                             "F90_DATE_OF_REGISTRATION"),
        ("Lester",                                    "F90_GROOM_FIRST"),
        ("Gomez",                                     "F90_GROOM_MIDDLE"),
        ("Padilla",                                   "F90_GROOM_LAST"),
        ("33",                                        "F90_GROOM_AGE"),
        ("7 BF Resort Village, Las Pinas City",      "F90_GROOM_RESIDENCE"),
        ("Leslie",                                    "F90_BRIDE_FIRST"),
        ("Navarro",                                   "F90_BRIDE_MIDDLE"),
        ("Espiritu",                                  "F90_BRIDE_LAST"),
        ("29",                                        "F90_BRIDE_AGE"),
        ("3 Moonwalk Subdivision, Paranaque City",   "F90_BRIDE_RESIDENCE"),
        ("1st day of June, 2024",                    "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Example 10 ────────────────────────────────────────────────────────────
    t = (
        "Accountable Form No. 54 Form No. 10\n"
        "City or Municipality of Pasig City\n"
        "No. 3340092\n"
        "MARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\n"
        "ML Date of Registration: September 3, 2015\n"
        "This is to certify that Eduardo Garcia Mendoza aged 38 years\n"
        "and resident of Blk 5 Lot 3, Greenpark Village, Pasig City\n"
        "may legally contract marriage\n"
        "with Elena Torres Garcia aged 34 years\n"
        "and resident of 101 Shaw Boulevard, Mandaluyong City\n"
        "license fee P2.00 Articles 65 Republic Act No. 386\n"
        "issued this 3rd day of September, 2015\n"
        "MARRIAGE LICENSE VALID UNTIL January 30, 2016\n"
        "Local Civil Registrar of Pasig City"
    )
    examples.append((t, {"entities": make_entities(t, [
        ("3340092",                                       "F90_REGISTRY_NO"),
        ("September 3, 2015",                            "F90_DATE_OF_REGISTRATION"),
        ("Eduardo",                                       "F90_GROOM_FIRST"),
        ("Garcia",                                        "F90_GROOM_MIDDLE"),
        ("Mendoza",                                       "F90_GROOM_LAST"),
        ("38",                                            "F90_GROOM_AGE"),
        ("Blk 5 Lot 3, Greenpark Village, Pasig City",  "F90_GROOM_RESIDENCE"),
        ("Elena",                                         "F90_BRIDE_FIRST"),
        ("Torres",                                        "F90_BRIDE_MIDDLE"),
        ("Garcia",                                        "F90_BRIDE_LAST"),
        ("34",                                            "F90_BRIDE_AGE"),
        ("101 Shaw Boulevard, Mandaluyong City",         "F90_BRIDE_RESIDENCE"),
        ("3rd day of September, 2015",                   "F90_DATE_OF_ISSUANCE"),
    ])}))

    # ── Examples 11–21 (date-format + address variation boosters) ─────────────
    short_formats = [
        ("Accountable Form No. 54 Form No. 10\nCity of Marikina\nNo. 1122334\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 03/15/2017\nThis is to certify that Victor Cruz Dela Cruz aged 30 years\nand resident of 5 Park Ave., Marikina City\nmay legally contract marriage\nwith Nena Reyes Santos aged 27 years\nand resident of 12 Sumulong Hwy., Marikina City\nArticles 65 Republic Act No. 386\nissued this 15th day of March, 2017\nMARRIAGE LICENSE VALID UNTIL 07/12/2017",
         [("1122334","F90_REGISTRY_NO"),("03/15/2017","F90_DATE_OF_REGISTRATION"),("Victor","F90_GROOM_FIRST"),("Cruz","F90_GROOM_MIDDLE"),("Dela Cruz","F90_GROOM_LAST"),("30","F90_GROOM_AGE"),("5 Park Ave., Marikina City","F90_GROOM_RESIDENCE"),("Nena","F90_BRIDE_FIRST"),("Reyes","F90_BRIDE_MIDDLE"),("Santos","F90_BRIDE_LAST"),("27","F90_BRIDE_AGE"),("12 Sumulong Hwy., Marikina City","F90_BRIDE_RESIDENCE"),("15th day of March, 2017","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Valenzuela\nNo. 8843210\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 20 August 2020\nThis is to certify that Dennis Cruz Padilla aged 45 years\nand resident of 33 Karuhatan Road, Valenzuela City\nmay legally contract marriage\nwith Carla Torres Santos aged 40 years\nand resident of 7 Dalangin Street, Valenzuela City\nArticles 65 Republic Act No. 386\nissued this 20th day of August, 2020\nMARRIAGE LICENSE VALID UNTIL 16 December 2020",
         [("8843210","F90_REGISTRY_NO"),("20 August 2020","F90_DATE_OF_REGISTRATION"),("Dennis","F90_GROOM_FIRST"),("Cruz","F90_GROOM_MIDDLE"),("Padilla","F90_GROOM_LAST"),("45","F90_GROOM_AGE"),("33 Karuhatan Road, Valenzuela City","F90_GROOM_RESIDENCE"),("Carla","F90_BRIDE_FIRST"),("Torres","F90_BRIDE_MIDDLE"),("Santos","F90_BRIDE_LAST"),("40","F90_BRIDE_AGE"),("7 Dalangin Street, Valenzuela City","F90_BRIDE_RESIDENCE"),("20th day of August, 2020","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of San Juan\nNo. 4419933\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: December 28, 2013\nThis is to certify that Anthony Villafuerte Cruz aged 32 years\nand resident of 44 N. Domingo Street, San Juan City\nmay legally contract marriage\nwith Lovely Hernandez Santos aged 28 years\nand resident of 9 Pinaglabanan Street, San Juan City\nArticles 65 Republic Act No. 386\nissued this 28th day of December, 2013\nMARRIAGE LICENSE VALID UNTIL April 26, 2014\nLocal Civil Registrar of San Juan City",
         [("4419933","F90_REGISTRY_NO"),("December 28, 2013","F90_DATE_OF_REGISTRATION"),("Anthony","F90_GROOM_FIRST"),("Villafuerte","F90_GROOM_MIDDLE"),("Cruz","F90_GROOM_LAST"),("32","F90_GROOM_AGE"),("44 N. Domingo Street, San Juan City","F90_GROOM_RESIDENCE"),("Lovely","F90_BRIDE_FIRST"),("Hernandez","F90_BRIDE_MIDDLE"),("Santos","F90_BRIDE_LAST"),("28","F90_BRIDE_AGE"),("9 Pinaglabanan Street, San Juan City","F90_BRIDE_RESIDENCE"),("28th day of December, 2013","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nMunicipality of Tarlac City\nNo. 6617204\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 04/18/2011\nThis is to certify that Marco dela Paz Valdez aged 26 years\nand resident of Brgy. San Miguel, Tarlac City\nmay legally contract marriage\nwith Marcia Castillo de Guzman aged 22 years\nand resident of Brgy. Sto. Cristo, Tarlac City\nArticles 65 Republic Act No. 386\nissued this 18th day of April, 2011\nMARRIAGE LICENSE VALID UNTIL 08/15/2011",
         [("6617204","F90_REGISTRY_NO"),("04/18/2011","F90_DATE_OF_REGISTRATION"),("Marco","F90_GROOM_FIRST"),("dela Paz","F90_GROOM_MIDDLE"),("Valdez","F90_GROOM_LAST"),("26","F90_GROOM_AGE"),("Brgy. San Miguel, Tarlac City","F90_GROOM_RESIDENCE"),("Marcia","F90_BRIDE_FIRST"),("Castillo","F90_BRIDE_MIDDLE"),("de Guzman","F90_BRIDE_LAST"),("22","F90_BRIDE_AGE"),("Brgy. Sto. Cristo, Tarlac City","F90_BRIDE_RESIDENCE"),("18th day of April, 2011","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Muntinlupa\nNo. 7700145\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 10 March 2009\nThis is to certify that Nathan Ramos Padilla aged 22 years\nand resident of Blk 2 Lot 5, Alabang Hills, Muntinlupa City\nmay legally contract marriage\nwith Hazel Aguilar Dela Cruz aged 20 years\nand resident of 6 Crestwood Drive, Alabang, Muntinlupa City\nArticles 65 Republic Act No. 386\nissued this 10th day of March, 2009\nMARRIAGE LICENSE VALID UNTIL 07/07/2009",
         [("7700145","F90_REGISTRY_NO"),("10 March 2009","F90_DATE_OF_REGISTRATION"),("Nathan","F90_GROOM_FIRST"),("Ramos","F90_GROOM_MIDDLE"),("Padilla","F90_GROOM_LAST"),("22","F90_GROOM_AGE"),("Blk 2 Lot 5, Alabang Hills, Muntinlupa City","F90_GROOM_RESIDENCE"),("Hazel","F90_BRIDE_FIRST"),("Aguilar","F90_BRIDE_MIDDLE"),("Dela Cruz","F90_BRIDE_LAST"),("20","F90_BRIDE_AGE"),("6 Crestwood Drive, Alabang, Muntinlupa City","F90_BRIDE_RESIDENCE"),("10th day of March, 2009","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Las Pinas\nNo. 5123098\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: May 5, 2022\nThis is to certify that Jerome Espiritu Ramos aged 29 years\nand resident of 14 Pulang Lupa, Las Pinas City\nmay legally contract marriage\nwith Felisa Torres Aguilar aged 26 years\nand resident of 20 CAA Road, Las Pinas City\nArticles 65 Republic Act No. 386\nissued this 5th day of May, 2022\nMARRIAGE LICENSE VALID UNTIL September 1, 2022\nLocal Civil Registrar of Las Pinas City",
         [("5123098","F90_REGISTRY_NO"),("May 5, 2022","F90_DATE_OF_REGISTRATION"),("Jerome","F90_GROOM_FIRST"),("Espiritu","F90_GROOM_MIDDLE"),("Ramos","F90_GROOM_LAST"),("29","F90_GROOM_AGE"),("14 Pulang Lupa, Las Pinas City","F90_GROOM_RESIDENCE"),("Felisa","F90_BRIDE_FIRST"),("Torres","F90_BRIDE_MIDDLE"),("Aguilar","F90_BRIDE_LAST"),("26","F90_BRIDE_AGE"),("20 CAA Road, Las Pinas City","F90_BRIDE_RESIDENCE"),("5th day of May, 2022","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Malabon\nNo. 9988776\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 01/30/2024\nThis is to certify that Gerald Catalan Marquez aged 28 years\nand resident of 55 Longos, Malabon City\nmay legally contract marriage\nwith Camille Aguilar Ramos aged 25 years\nand resident of 11 Tinajeros, Malabon City\nArticles 65 Republic Act No. 386\nissued this 30th day of January, 2024\nMARRIAGE LICENSE VALID UNTIL 05/28/2024",
         [("9988776","F90_REGISTRY_NO"),("01/30/2024","F90_DATE_OF_REGISTRATION"),("Gerald","F90_GROOM_FIRST"),("Catalan","F90_GROOM_MIDDLE"),("Marquez","F90_GROOM_LAST"),("28","F90_GROOM_AGE"),("55 Longos, Malabon City","F90_GROOM_RESIDENCE"),("Camille","F90_BRIDE_FIRST"),("Aguilar","F90_BRIDE_MIDDLE"),("Ramos","F90_BRIDE_LAST"),("25","F90_BRIDE_AGE"),("11 Tinajeros, Malabon City","F90_BRIDE_RESIDENCE"),("30th day of January, 2024","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Navotas\nNo. 3301210\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 25 September 2010\nThis is to certify that Joshua Bautista Enriquez aged 23 years\nand resident of 8 M. Naval Street, Navotas City\nmay legally contract marriage\nwith Natividad Ramos Bautista aged 21 years\nand resident of 3 Tanza Street, Navotas City\nArticles 65 Republic Act No. 386\nissued this 25th day of September, 2010\nMARRIAGE LICENSE VALID UNTIL January 21, 2011",
         [("3301210","F90_REGISTRY_NO"),("25 September 2010","F90_DATE_OF_REGISTRATION"),("Joshua","F90_GROOM_FIRST"),("Bautista","F90_GROOM_MIDDLE"),("Enriquez","F90_GROOM_LAST"),("23","F90_GROOM_AGE"),("8 M. Naval Street, Navotas City","F90_GROOM_RESIDENCE"),("Natividad","F90_BRIDE_FIRST"),("Ramos","F90_BRIDE_MIDDLE"),("Bautista","F90_BRIDE_LAST"),("21","F90_BRIDE_AGE"),("3 Tanza Street, Navotas City","F90_BRIDE_RESIDENCE"),("25th day of September, 2010","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Mandaluyong\nNo. 4402987\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: August 8, 2023\nThis is to certify that Kenneth Garcia Pascual aged 31 years\nand resident of 34 Wack-Wack Village, Mandaluyong City\nmay legally contract marriage\nwith Emelinda dela Cruz Reyes aged 28 years\nand resident of 22 Vergara Street, Mandaluyong City\nArticles 65 Republic Act No. 386\nissued this 8th day of August, 2023\nMARRIAGE LICENSE VALID UNTIL December 5, 2023\nLocal Civil Registrar of Mandaluyong City",
         [("4402987","F90_REGISTRY_NO"),("August 8, 2023","F90_DATE_OF_REGISTRATION"),("Kenneth","F90_GROOM_FIRST"),("Garcia","F90_GROOM_MIDDLE"),("Pascual","F90_GROOM_LAST"),("31","F90_GROOM_AGE"),("34 Wack-Wack Village, Mandaluyong City","F90_GROOM_RESIDENCE"),("Emelinda","F90_BRIDE_FIRST"),("dela Cruz","F90_BRIDE_MIDDLE"),("Reyes","F90_BRIDE_LAST"),("28","F90_BRIDE_AGE"),("22 Vergara Street, Mandaluyong City","F90_BRIDE_RESIDENCE"),("8th day of August, 2023","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nMunicipality of Antipolo City\nNo. 6693021\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 12/12/2007\nThis is to certify that Rodrigo dela Torre Villanueva aged 35 years\nand resident of Brgy. San Roque, Antipolo City\nmay legally contract marriage\nwith Precious Buenaventura Hernandez aged 32 years\nand resident of Brgy. San Luis, Antipolo City\nArticles 65 Republic Act No. 386\nissued this 12th day of December, 2007\nMARRIAGE LICENSE VALID UNTIL 04/09/2008",
         [("6693021","F90_REGISTRY_NO"),("12/12/2007","F90_DATE_OF_REGISTRATION"),("Rodrigo","F90_GROOM_FIRST"),("dela Torre","F90_GROOM_MIDDLE"),("Villanueva","F90_GROOM_LAST"),("35","F90_GROOM_AGE"),("Brgy. San Roque, Antipolo City","F90_GROOM_RESIDENCE"),("Precious","F90_BRIDE_FIRST"),("Buenaventura","F90_BRIDE_MIDDLE"),("Hernandez","F90_BRIDE_LAST"),("32","F90_BRIDE_AGE"),("Brgy. San Luis, Antipolo City","F90_BRIDE_RESIDENCE"),("12th day of December, 2007","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Bacoor\nNo. 5039877\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: February 20, 2014\nThis is to certify that Patrick Soriano Navarro aged 30 years\nand resident of 7 Habay I, Bacoor City, Cavite\nmay legally contract marriage\nwith Donna Evangelista Cruz aged 27 years\nand resident of 15 Molino III, Bacoor City, Cavite\nArticles 65 Republic Act No. 386\nissued this 20th day of February, 2014\nMARRIAGE LICENSE VALID UNTIL June 19, 2014\nLocal Civil Registrar of Bacoor City",
         [("5039877","F90_REGISTRY_NO"),("February 20, 2014","F90_DATE_OF_REGISTRATION"),("Patrick","F90_GROOM_FIRST"),("Soriano","F90_GROOM_MIDDLE"),("Navarro","F90_GROOM_LAST"),("30","F90_GROOM_AGE"),("7 Habay I, Bacoor City, Cavite","F90_GROOM_RESIDENCE"),("Donna","F90_BRIDE_FIRST"),("Evangelista","F90_BRIDE_MIDDLE"),("Cruz","F90_BRIDE_LAST"),("27","F90_BRIDE_AGE"),("15 Molino III, Bacoor City, Cavite","F90_BRIDE_RESIDENCE"),("20th day of February, 2014","F90_DATE_OF_ISSUANCE")]),
    ]
    for t, pairs in short_formats:
        examples.append((t, {"entities": make_entities(t, pairs)}))

    return examples


# Target: DATE_OF_REGISTRATION (all forms) — was 0–40% F1
#         F90_GROOM/BRIDE_DATE_OF_BIRTH — was 29–35% F1
#         F102_CHILD_LAST — was 40% F1
# Strategy: more examples + more date FORMAT variation
# ============================================================

def weak_label_booster_examples():
    examples = []

    # ── DATE_OF_REGISTRATION — Form 102 (was 0%) ─────────────
    formats_102 = [
        ("BC Registry No.: 2023-BC-301\nBC Date of Registration: 05/10/2023\nCHILD (First): Leo\nCHILD (Middle): Santos\nCHILD (Last): Reyes\n2. SEX: Male\n3. Child Date of Birth: 04/28/2023\n4. PLACE OF BIRTH: Manila",
         [("2023-BC-301","F102_REGISTRY_NO"),("05/10/2023","F102_DATE_OF_REGISTRATION"),("Leo","F102_CHILD_FIRST"),("Santos","F102_CHILD_MIDDLE"),("Reyes","F102_CHILD_LAST"),("Male","F102_SEX"),("04/28/2023","F102_DATE_OF_BIRTH"),("Manila","F102_PLACE_OF_BIRTH")]),

        ("BC Registry No.: 2021-BC-018\nBC Date of Registration: 18 June 2021\nCHILD (First): Elena\nCHILD (Middle): Cruz\nCHILD (Last): Flores\n2. SEX: Female\n3. Child Date of Birth: 04 June 2021\n4. PLACE OF BIRTH: Cebu City",
         [("2021-BC-018","F102_REGISTRY_NO"),("18 June 2021","F102_DATE_OF_REGISTRATION"),("Elena","F102_CHILD_FIRST"),("Cruz","F102_CHILD_MIDDLE"),("Flores","F102_CHILD_LAST"),("Female","F102_SEX"),("04 June 2021","F102_DATE_OF_BIRTH"),("Cebu City","F102_PLACE_OF_BIRTH")]),

        ("BC Registry No.: 2019-BC-222\nBC Date of Registration: September 2, 2019\nCHILD (First): Marco\nCHILD (Middle): Lim\nCHILD (Last): Tan\n2. SEX: Male\n3. Child Date of Birth: August 20, 2019\n4. PLACE OF BIRTH: Davao City",
         [("2019-BC-222","F102_REGISTRY_NO"),("September 2, 2019","F102_DATE_OF_REGISTRATION"),("Marco","F102_CHILD_FIRST"),("Lim","F102_CHILD_MIDDLE"),("Tan","F102_CHILD_LAST"),("Male","F102_SEX"),("August 20, 2019","F102_DATE_OF_BIRTH"),("Davao City","F102_PLACE_OF_BIRTH")]),

        ("BC Registry No.: 2010-BC-077\nBC Date of Registration: 03/15/2010\nCHILD (First): Alyssa\nCHILD (Middle): Reyes\nCHILD (Last): Gonzales\n2. SEX: Female\n3. Child Date of Birth: 02/28/2010\n4. PLACE OF BIRTH: Quezon City",
         [("2010-BC-077","F102_REGISTRY_NO"),("03/15/2010","F102_DATE_OF_REGISTRATION"),("Alyssa","F102_CHILD_FIRST"),("Reyes","F102_CHILD_MIDDLE"),("Gonzales","F102_CHILD_LAST"),("Female","F102_SEX"),("02/28/2010","F102_DATE_OF_BIRTH"),("Quezon City","F102_PLACE_OF_BIRTH")]),

        ("BC Registry No.: 2016-BC-190\nBC Date of Registration: 22 October 2016\nCHILD (First): Andrei\nCHILD (Middle): Navarro\nCHILD (Last): Dela Cruz\n2. SEX: Male\n3. Child Date of Birth: 10 October 2016\n4. PLACE OF BIRTH: Makati City",
         [("2016-BC-190","F102_REGISTRY_NO"),("22 October 2016","F102_DATE_OF_REGISTRATION"),("Andrei","F102_CHILD_FIRST"),("Navarro","F102_CHILD_MIDDLE"),("Dela Cruz","F102_CHILD_LAST"),("Male","F102_SEX"),("10 October 2016","F102_DATE_OF_BIRTH"),("Makati City","F102_PLACE_OF_BIRTH")]),

        ("BC Registry No.: 2024-BC-055\nBC Date of Registration: January 30, 2024\nCHILD (First): Isabella\nCHILD (Middle): Ocampo\nCHILD (Last): Bautista\n2. SEX: Female\n3. Child Date of Birth: January 15, 2024\n4. PLACE OF BIRTH: Taguig City",
         [("2024-BC-055","F102_REGISTRY_NO"),("January 30, 2024","F102_DATE_OF_REGISTRATION"),("Isabella","F102_CHILD_FIRST"),("Ocampo","F102_CHILD_MIDDLE"),("Bautista","F102_CHILD_LAST"),("Female","F102_SEX"),("January 15, 2024","F102_DATE_OF_BIRTH"),("Taguig City","F102_PLACE_OF_BIRTH")]),
    ]
    for t, pairs in formats_102:
        examples.append((t, {"entities": make_entities(t, pairs)}))

    # ── DATE_OF_REGISTRATION — Form 103 (was 40%) ────────────
    formats_103 = [
        ("Registry No.: 2022-DC-041\nDC Date of Registration: 07/22/2022\nDECEASED (First): Roberto (Middle): Santos (Last): Lim\n2. SEX: Male\n4. AGE: 78\n5. PLACE OF DEATH: Manila\n6. DATE OF DEATH: 07/15/2022\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Pneumonia",
         [("2022-DC-041","F103_REGISTRY_NO"),("07/22/2022","F103_DATE_OF_REGISTRATION"),("Roberto","F103_DECEASED_FIRST"),("Santos","F103_DECEASED_MIDDLE"),("Lim","F103_DECEASED_LAST"),("Male","F103_SEX"),("78","F103_AGE"),("Manila","F103_PLACE_OF_DEATH"),("07/15/2022","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Pneumonia","F103_CAUSE_IMMEDIATE")]),

        ("Registry No.: 2018-DC-109\nDC Date of Registration: 15 March 2018\nDECEASED (First): Consuelo (Middle): Reyes (Last): Torres\n2. SEX: Female\n4. AGE: 82\n5. PLACE OF DEATH: Cebu City\n6. DATE OF DEATH: 10 March 2018\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Married\nImmediate cause: Stroke",
         [("2018-DC-109","F103_REGISTRY_NO"),("15 March 2018","F103_DATE_OF_REGISTRATION"),("Consuelo","F103_DECEASED_FIRST"),("Reyes","F103_DECEASED_MIDDLE"),("Torres","F103_DECEASED_LAST"),("Female","F103_SEX"),("82","F103_AGE"),("Cebu City","F103_PLACE_OF_DEATH"),("10 March 2018","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Married","F103_CIVIL_STATUS"),("Stroke","F103_CAUSE_IMMEDIATE")]),

        ("Registry No.: 2020-DC-077\nDC Date of Registration: December 28, 2020\nDECEASED (First): Danilo (Middle): Cruz (Last): Santos\n2. SEX: Male\n4. AGE: 55\n5. PLACE OF DEATH: Quezon City\n6. DATE OF DEATH: December 20, 2020\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Single\nImmediate cause: COVID-19",
         [("2020-DC-077","F103_REGISTRY_NO"),("December 28, 2020","F103_DATE_OF_REGISTRATION"),("Danilo","F103_DECEASED_FIRST"),("Cruz","F103_DECEASED_MIDDLE"),("Santos","F103_DECEASED_LAST"),("Male","F103_SEX"),("55","F103_AGE"),("Quezon City","F103_PLACE_OF_DEATH"),("December 20, 2020","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Single","F103_CIVIL_STATUS"),("COVID-19","F103_CAUSE_IMMEDIATE")]),

        ("Registry No.: 2015-DC-033\nDC Date of Registration: 05/05/2015\nDECEASED (First): Leonora (Middle): Villanueva (Last): Garcia\n2. SEX: Female\n4. AGE: 91\n5. PLACE OF DEATH: Davao City\n6. DATE OF DEATH: 04/30/2015\n7. CITIZENSHIP: Filipino\n9. CIVIL STATUS: Widowed\nImmediate cause: Heart Failure",
         [("2015-DC-033","F103_REGISTRY_NO"),("05/05/2015","F103_DATE_OF_REGISTRATION"),("Leonora","F103_DECEASED_FIRST"),("Villanueva","F103_DECEASED_MIDDLE"),("Garcia","F103_DECEASED_LAST"),("Female","F103_SEX"),("91","F103_AGE"),("Davao City","F103_PLACE_OF_DEATH"),("04/30/2015","F103_DATE_OF_DEATH"),("Filipino","F103_CITIZENSHIP"),("Widowed","F103_CIVIL_STATUS"),("Heart Failure","F103_CAUSE_IMMEDIATE")]),
    ]
    for t, pairs in formats_103:
        examples.append((t, {"entities": make_entities(t, pairs)}))

    # ── DATE_OF_REGISTRATION — Form 97 (was 22%) ─────────────
    formats_97 = [
        ("Registry No.: 2022-MC-014\nMC Date of Registration: 02/20/2022\nHUSBAND:\n1. NAME (First): Jose (Middle): Reyes (Last): Santos\n2a. DATE OF BIRTH: 03/10/1990\n2b. AGE: 32\n4b. CITIZENSHIP: Filipino\nWIFE:\n1. NAME (First): Clara (Middle): Cruz (Last): Santos\n2a. DATE OF BIRTH: 05/15/1992\n2b. AGE: 29\n4b. CITIZENSHIP: Filipino\n15. PLACE OF MARRIAGE: Manila\n16. DATE OF MARRIAGE: 02/14/2022",
         [("2022-MC-014","F97_REGISTRY_NO"),("02/20/2022","F97_DATE_OF_REGISTRATION"),("Jose","F97_HUSBAND_FIRST"),("Reyes","F97_HUSBAND_MIDDLE"),("Santos","F97_HUSBAND_LAST"),("32","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Clara","F97_WIFE_FIRST"),("Cruz","F97_WIFE_MIDDLE"),("Santos","F97_WIFE_LAST"),("29","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Manila","F97_PLACE_OF_MARRIAGE"),("02/14/2022","F97_DATE_OF_MARRIAGE")]),

        ("Registry No.: 2019-MC-088\nMC Date of Registration: 20 December 2019\nHUSBAND:\n1. NAME (First): Rafael (Middle): Bautista (Last): Torres\n2a. DATE OF BIRTH: 14 July 1985\n2b. AGE: 34\n4b. CITIZENSHIP: Filipino\nWIFE:\n1. NAME (First): Maribel (Middle): Lim (Last): Torres\n2a. DATE OF BIRTH: 20 August 1989\n2b. AGE: 30\n4b. CITIZENSHIP: Filipino\n15. PLACE OF MARRIAGE: Cebu City\n16. DATE OF MARRIAGE: 15 December 2019",
         [("2019-MC-088","F97_REGISTRY_NO"),("20 December 2019","F97_DATE_OF_REGISTRATION"),("Rafael","F97_HUSBAND_FIRST"),("Bautista","F97_HUSBAND_MIDDLE"),("Torres","F97_HUSBAND_LAST"),("34","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Maribel","F97_WIFE_FIRST"),("Lim","F97_WIFE_MIDDLE"),("Torres","F97_WIFE_LAST"),("30","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Cebu City","F97_PLACE_OF_MARRIAGE"),("15 December 2019","F97_DATE_OF_MARRIAGE")]),

        ("Registry No.: 2024-MC-003\nMC Date of Registration: March 10, 2024\nHUSBAND:\n1. NAME (First): Kevin (Middle): Navarro (Last): Diaz\n2a. DATE OF BIRTH: January 5, 1995\n2b. AGE: 29\n4b. CITIZENSHIP: Filipino\nWIFE:\n1. NAME (First): Angela (Middle): Ramos (Last): Diaz\n2a. DATE OF BIRTH: April 12, 1997\n2b. AGE: 26\n4b. CITIZENSHIP: Filipino\n15. PLACE OF MARRIAGE: Quezon City\n16. DATE OF MARRIAGE: March 5, 2024",
         [("2024-MC-003","F97_REGISTRY_NO"),("March 10, 2024","F97_DATE_OF_REGISTRATION"),("Kevin","F97_HUSBAND_FIRST"),("Navarro","F97_HUSBAND_MIDDLE"),("Diaz","F97_HUSBAND_LAST"),("29","F97_HUSBAND_AGE"),("Filipino","F97_HUSBAND_CITIZENSHIP"),("Angela","F97_WIFE_FIRST"),("Ramos","F97_WIFE_MIDDLE"),("Diaz","F97_WIFE_LAST"),("26","F97_WIFE_AGE"),("Filipino","F97_WIFE_CITIZENSHIP"),("Quezon City","F97_PLACE_OF_MARRIAGE"),("March 5, 2024","F97_DATE_OF_MARRIAGE")]),
    ]
    for t, pairs in formats_97:
        examples.append((t, {"entities": make_entities(t, pairs)}))

    # ── DATE_OF_REGISTRATION + DATE_OF_ISSUANCE — Form 90 ──
    # Source: Accountable Form No. 54 / Form No. 10
    # Target labels: F90_DATE_OF_REGISTRATION, F90_DATE_OF_ISSUANCE,
    #                F90_GROOM/BRIDE_RESIDENCE (address variation)
    formats_90 = [
        ("Accountable Form No. 54 Form No. 10\nCity of Makati\nNo. 2023-ML-055\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 03/05/2023\nThis is to certify that Carlo Mendoza Reyes aged 33 years\nand resident of 10 Ayala Ave., Makati City\nmay legally contract marriage\nwith Carla Torres Santos aged 29 years\nand resident of 5 Paseo de Roxas, Makati City\nArticles 65 Republic Act No. 386\nissued this 5th day of March, 2023\nMARRIAGE LICENSE VALID UNTIL 07/02/2023",
         [("2023-ML-055","F90_REGISTRY_NO"),("03/05/2023","F90_DATE_OF_REGISTRATION"),("Carlo","F90_GROOM_FIRST"),("Mendoza","F90_GROOM_MIDDLE"),("Reyes","F90_GROOM_LAST"),("33","F90_GROOM_AGE"),("10 Ayala Ave., Makati City","F90_GROOM_RESIDENCE"),("Carla","F90_BRIDE_FIRST"),("Torres","F90_BRIDE_MIDDLE"),("Santos","F90_BRIDE_LAST"),("29","F90_BRIDE_AGE"),("5 Paseo de Roxas, Makati City","F90_BRIDE_RESIDENCE"),("5th day of March, 2023","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Iloilo\nNo. 2020-ML-121\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 14 February 2020\nThis is to certify that Dante Aquino Villanueva aged 32 years\nand resident of Brgy. Mandurriao, Iloilo City\nmay legally contract marriage\nwith Diana Cruz Aquino aged 27 years\nand resident of Brgy. Jaro, Iloilo City\nArticles 65 Republic Act No. 386\nissued this 14th day of February, 2020\nMARRIAGE LICENSE VALID UNTIL June 12, 2020",
         [("2020-ML-121","F90_REGISTRY_NO"),("14 February 2020","F90_DATE_OF_REGISTRATION"),("Dante","F90_GROOM_FIRST"),("Aquino","F90_GROOM_MIDDLE"),("Villanueva","F90_GROOM_LAST"),("32","F90_GROOM_AGE"),("Brgy. Mandurriao, Iloilo City","F90_GROOM_RESIDENCE"),("Diana","F90_BRIDE_FIRST"),("Cruz","F90_BRIDE_MIDDLE"),("Aquino","F90_BRIDE_LAST"),("27","F90_BRIDE_AGE"),("Brgy. Jaro, Iloilo City","F90_BRIDE_RESIDENCE"),("14th day of February, 2020","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nCity of Taguig\nNo. 2024-ML-009\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: May 20, 2024\nThis is to certify that Lester Gomez Padilla aged 33 years\nand resident of 2 McKinley Pkwy., BGC, Taguig City\nmay legally contract marriage\nwith Leslie Navarro Espiritu aged 29 years\nand resident of 8 26th Street, BGC, Taguig City\nArticles 65 Republic Act No. 386\nissued this 20th day of May, 2024\nMARRIAGE LICENSE VALID UNTIL September 16, 2024",
         [("2024-ML-009","F90_REGISTRY_NO"),("May 20, 2024","F90_DATE_OF_REGISTRATION"),("Lester","F90_GROOM_FIRST"),("Gomez","F90_GROOM_MIDDLE"),("Padilla","F90_GROOM_LAST"),("33","F90_GROOM_AGE"),("2 McKinley Pkwy., BGC, Taguig City","F90_GROOM_RESIDENCE"),("Leslie","F90_BRIDE_FIRST"),("Navarro","F90_BRIDE_MIDDLE"),("Espiritu","F90_BRIDE_LAST"),("29","F90_BRIDE_AGE"),("8 26th Street, BGC, Taguig City","F90_BRIDE_RESIDENCE"),("20th day of May, 2024","F90_DATE_OF_ISSUANCE")]),

        ("Accountable Form No. 54 Form No. 10\nMunicipality of Tarlac City\nNo. 2017-ML-066\nMARRIAGE LICENSE AND FEE RECEIPT OF TWO PESOS\nML Date of Registration: 12/18/2017\nThis is to certify that Marco dela Paz Valdez aged 32 years\nand resident of Brgy. San Vicente, Tarlac City\nmay legally contract marriage\nwith Marcia Castillo de Guzman aged 27 years\nand resident of Brgy. San Nicolas, Tarlac City\nArticles 65 Republic Act No. 386\nissued this 18th day of December, 2017\nMARRIAGE LICENSE VALID UNTIL 04/16/2018",
         [("2017-ML-066","F90_REGISTRY_NO"),("12/18/2017","F90_DATE_OF_REGISTRATION"),("Marco","F90_GROOM_FIRST"),("dela Paz","F90_GROOM_MIDDLE"),("Valdez","F90_GROOM_LAST"),("32","F90_GROOM_AGE"),("Brgy. San Vicente, Tarlac City","F90_GROOM_RESIDENCE"),("Marcia","F90_BRIDE_FIRST"),("Castillo","F90_BRIDE_MIDDLE"),("de Guzman","F90_BRIDE_LAST"),("27","F90_BRIDE_AGE"),("Brgy. San Nicolas, Tarlac City","F90_BRIDE_RESIDENCE"),("18th day of December, 2017","F90_DATE_OF_ISSUANCE")]),
    ]
    for t, pairs in formats_90:
        examples.append((t, {"entities": make_entities(t, pairs)}))

    return examples


def build_spacy_file(data, output_path):
    nlp     = spacy.blank("en")
    doc_bin = DocBin()
    skipped = 0
    saved   = 0
    for text, annotation in data:
        doc  = nlp.make_doc(text)
        ents = []
        for start, end, label in annotation["entities"]:
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if start >= end:
                skipped += 1
                continue
            # Try expand first — catches short single-token values (ages: '88', '24')
            # contract returns None for these when char boundaries don't align exactly
            span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span is None:
                print(f"  WARNING skipped: [{label}] '{text[start:end]}'")
                skipped += 1
                continue
            # If expand grew into whitespace, fall back to contract
            if span.text != span.text.strip():
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is None:
                    skipped += 1
                    continue
            # Final guard — zero tolerance for whitespace (causes E024)
            if not span.text.strip() or span.text != span.text.strip():
                print(f"  WARNING whitespace span: [{label}] '{text[start:end]}'")
                skipped += 1
                continue
            ents.append(span)
        doc.ents = filter_spans(ents)
        doc_bin.add(doc)
        saved += 1
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc_bin.to_disk(output_path)
    print(f"  Saved {saved} docs -> {output_path}")
    if skipped:
        print(f"  Skipped {skipped} bad spans")


if __name__ == "__main__":
    print("=" * 60)
    print("  PREPARING CIVIL REGISTRY NER TRAINING DATA")
    print("=" * 60)
    print("\n  NER role: extract FIELD VALUES from documents")
    print("  Form 90 source: Accountable Form No. 54 (Marriage License Receipt)\n")

    f102  = form102_examples()
    f103  = form103_examples()
    f97   = form97_examples()
    f90   = form90_examples()
    boost = weak_label_booster_examples()

    print(f"  Form 102 -> 1A  (Birth Certificate):           {len(f102):>3} examples")
    print(f"  Form 103 -> 2A  (Death Certificate):           {len(f103):>3} examples")
    print(f"  Form 97  -> 3A  (Marriage Certificate):        {len(f97):>3} examples")
    print(f"  Form 90  -> 54  (Marriage License Receipt):    {len(f90):>3} examples")
    print(f"  Weak label boosters (DATE_OF_REG / ISSUANCE):  {len(boost):>3} examples")
    print(f"  {'─'*52}")
    total = len(f102) + len(f103) + len(f97) + len(f90) + len(boost)
    print(f"  Total:                                         {total:>3} examples")

    # ── STRATIFIED SPLIT ──────────────────────────────────
    # Take 20% from EACH form type separately.
    # A flat split (all_data[:80]) put all F90 in dev and none in train
    # which caused ENTS_F=0.00 because model never saw F90 labels.
    def stratified_split(examples, dev_ratio=0.2):
        n_dev = max(1, int(len(examples) * dev_ratio))
        return examples[n_dev:], examples[:n_dev]  # train, dev

    train102, dev102 = stratified_split(f102)
    train103, dev103 = stratified_split(f103)
    train97,  dev97  = stratified_split(f97)
    train90,  dev90  = stratified_split(f90)

    # Boosters go entirely into train (they are targeted augmentations)
    train = train102 + train103 + train97 + train90 + boost
    dev   = dev102   + dev103   + dev97   + dev90

    print(f"\n  Stratified split (20% from each form type):")
    print(f"  {'Form':<10} {'Train':>6}  {'Dev':>6}")
    print(f"  {'─'*26}")
    print(f"  {'F102':<10} {len(train102):>6}  {len(dev102):>6}")
    print(f"  {'F103':<10} {len(train103):>6}  {len(dev103):>6}")
    print(f"  {'F97':<10}  {len(train97):>6}  {len(dev97):>6}")
    print(f"  {'F90':<10}  {len(train90):>6}  {len(dev90):>6}")
    print(f"  {'─'*26}")
    print(f"  {'TOTAL':<10} {len(train):>6}  {len(dev):>6}\n")

    build_spacy_file(train, "data/training/train.spacy")
    build_spacy_file(dev,   "data/training/dev.spacy")
    print("\n  Done! Next steps:")
    print("    1. python training/train.py       (train NER)")
    print("    2. python training/train_mnb.py   (train MNB classifier)")
