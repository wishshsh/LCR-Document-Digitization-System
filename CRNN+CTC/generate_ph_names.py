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
print("\n[1/5] Loading NameDataset...")
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
print("\n[2/5] Extracting Filipino first names (Male + Female)...")

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
print("\n[3/5] Extracting Filipino last names...")

ph_last_raw = nd.get_top_names(n=300, country_alpha2='PH', use_first_names=False)
print(f"      Raw last name API type : {type(ph_last_raw)}")

ph_last_ph = ph_last_raw.get('PH', {})
print(f"      PH entry type          : {type(ph_last_ph)}")

raw_last = []

if isinstance(ph_last_ph, list):
    raw_last = ph_last_ph
elif isinstance(ph_last_ph, dict):
    first_val = next(iter(ph_last_ph.values()), None)
    if isinstance(first_val, list):
        for lst in ph_last_ph.values():
            raw_last.extend(lst)
    elif isinstance(first_val, dict):
        raw_last = list(ph_last_ph.keys())
    else:
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

# ── Step 4: Build MIDDLE names pool ──────────────────────────
# Middle names in Filipino naming convention are the mother's
# maiden last name. We build a large pool by combining:
#   A) The last names pool already extracted (primary source)
#   B) A curated extended list of common Filipino surnames
#      used specifically as middle names
print("\n[4/5] Building middle names pool...")

EXTENDED_MIDDLE_NAMES = [
    # Common Filipino surnames used as middle names
    'Abad', 'Abaya', 'Abella', 'Ablaza', 'Abrera',
    'Acosta', 'Adriano', 'Afable', 'Africa', 'Agcaoili',
    'Agno', 'Agpalo', 'Aguinaldo', 'Agustin', 'Ahorro',
    'Alano', 'Alba', 'Albano', 'Alberto', 'Alcantara',
    'Alcazar', 'Alcon', 'Aldana', 'Alegre', 'Alejandro',
    'Aligaen', 'Alim', 'Alinea', 'Alipio', 'Almario',
    'Almeda', 'Almendras', 'Alminiana', 'Almodiel', 'Alonto',
    'Alvarado', 'Alvarez', 'Amante', 'Amaro', 'Ambrocio',
    'Amor', 'Amores', 'Amparo', 'Anastacio', 'Andal',
    'Andaya', 'Angeles', 'Angsioco', 'Antiporda', 'Antonio',
    'Apalisok', 'Apolinario', 'Apostol', 'Aquino', 'Araneta',
    'Aranas', 'Aranda', 'Arceo', 'Arenas', 'Arias',
    'Ariate', 'Arillo', 'Arimado', 'Arjona', 'Arlante',
    'Arnaldo', 'Arnaiz', 'Arnoco', 'Arocena', 'Arroyo',
    'Asejo', 'Asuncion', 'Austria', 'Avecilla', 'Avena',
    'Avila', 'Avinante', 'Ayala', 'Azucena', 'Azul',
    'Bacani', 'Bacunawa', 'Baguio', 'Bagunu', 'Balagtas',
    'Balangue', 'Balbin', 'Balde', 'Baldeo', 'Balgos',
    'Balili', 'Balinas', 'Balitaan', 'Balladares', 'Ballesteros',
    'Balmeo', 'Balmores', 'Banaag', 'Banaag', 'Bandola',
    'Bangayan', 'Bansil', 'Bansode', 'Bantigue', 'Bantug',
    'Barbin', 'Barcenas', 'Bareng', 'Barrion', 'Barroga',
    'Bartolome', 'Bases', 'Batac', 'Bataller', 'Batanes',
    'Batungbakal', 'Bautista', 'Bayani', 'Bayot', 'Baysic',
    'Belarmino', 'Beldia', 'Belen', 'Belgica', 'Bello',
    'Benavides', 'Bendaña', 'Benedicto', 'Benigno', 'Benitez',
    'Bernardino', 'Bernardo', 'Bernarte', 'Besares', 'Billones',
    'Binay', 'Binayas', 'Biscocho', 'Blanco', 'Bondoc',
    'Borja', 'Borromeo', 'Bravo', 'Buenaobra', 'Buenaflor',
    'Buenafe', 'Buenaseda', 'Buenconsejo', 'Buendia', 'Bugarin',
    'Bulalacao', 'Bulalacao', 'Bulatao', 'Bumanlag', 'Bunag',
    'Caballero', 'Cabigting', 'Cabral', 'Cabreros', 'Cacal',
    'Cagampan', 'Cagas', 'Caguioa', 'Cahilig', 'Cajucom',
    'Calagos', 'Calamba', 'Calasanz', 'Calatrava', 'Calderon',
    'Calimag', 'Calimutan', 'Calinawan', 'Calleja', 'Callejo',
    'Caluag', 'Calugay', 'Camacho', 'Camino', 'Campaner',
    'Camposano', 'Candelario', 'Canete', 'Caning', 'Canlas',
    'Caoile', 'Capili', 'Carandang', 'Carbonell', 'Cariaga',
    'Carino', 'Carunungan', 'Casaje', 'Casas', 'Casidsid',
    'Castañeda', 'Castillo', 'Castillo', 'Catalan', 'Catapang',
    'Cayabyab', 'Cayco', 'Celdran', 'Cerillo', 'Cervantes',
    'Chico', 'Chikiamco', 'Chiongbian', 'Cipriano', 'Clarin',
    'Claudio', 'Clavecillas', 'Climaco', 'Cobankiat', 'Colambo',
    'Collado', 'Comafay', 'Comia', 'Concepcion', 'Condino',
    'Consing', 'Contraras', 'Coquia', 'Cordero', 'Corotan',
    'Corpus', 'Cosico', 'Costales', 'Crisostomo', 'Cristobal',
    'Cueto', 'Culala', 'Cunanan', 'Cunanon', 'Curato',
    'Dadivas', 'Daep', 'Daez', 'Daguplo', 'Dalida',
    'Dalisay', 'Dalmacion', 'Dalusong', 'Damasco', 'Damo',
    'Danao', 'Dancel', 'Dandan', 'Danila', 'Daquigan',
    'Dario', 'Datoc', 'Datumanong', 'David', 'Dayao',
    'Dayrit', 'De Borja', 'De Castro', 'De Jesus', 'De Jose',
    'De La Cruz', 'De La Pena', 'De La Rosa', 'De Leon', 'De Lima',
    'De Los Angeles', 'De Los Reyes', 'De Los Santos', 'De Luna', 'De Mesa',
    'De Ocampo', 'De Paz', 'De Vera', 'De Villa', 'Delos Reyes',
    'Demaisip', 'Delos Santos', 'Demillo', 'Demonteverde', 'Denosta',
    'Derequito', 'Deri', 'Detablan', 'Deveraturda', 'Diaz',
    'Dichoso', 'Diego', 'Diesto', 'Dimaano', 'Dimabuyu',
    'Dimagiba', 'Dimaguila', 'Dimaio', 'Dimanlig', 'Dimayuga',
    'Dingal', 'Dinglasan', 'Dionisio', 'Dioquino', 'Ditan',
    'Diwata', 'Domingo', 'Dominguez', 'Donato', 'Dorado',
    'Doria', 'Duallo', 'Duenas', 'Duerme', 'Dulay',
    'Dumalaog', 'Dumpit', 'Duque', 'Duran', 'Durante',
    'Ebdane', 'Echavez', 'Echevarria', 'Edralin', 'Ejercito',
    'Elago', 'Elazegui', 'Elises', 'Elumba', 'Enage',
    'Encarnacion', 'Enriquez', 'Escobar', 'Escueta', 'Escutin',
    'Esguerra', 'Eslit', 'Espejo', 'Espeleta', 'Espinas',
    'Espino', 'Espiritu', 'Estepa', 'Esteves', 'Estrada',
    'Estrellas', 'Evangelista', 'Evasco', 'Evidente', 'Eyas',
    'Fabella', 'Fabros', 'Faelnar', 'Fajardo', 'Fajutag',
    'Famadico', 'Famador', 'Faustino', 'Favila', 'Feliciano',
    'Felipe', 'Fermin', 'Fernandez', 'Fernando', 'Ferrer',
    'Figueras', 'Fider', 'Florendo', 'Florentino', 'Floreta',
    'Flores', 'Florido', 'Floriza', 'Foja', 'Fonacier',
    'Fontanilla', 'Formoso', 'Fornier', 'Fortich', 'Fortuna',
    'Francisco', 'Frano', 'Frasco', 'Frias', 'Fuentes',
    'Gaabucayan', 'Gabutero', 'Gaerlan', 'Gaffud', 'Galapon',
    'Galera', 'Galicia', 'Galindez', 'Gallardo', 'Gallo',
    'Galvez', 'Gamalinda', 'Gamboa', 'Gammad', 'Gandionco',
    'Ganzon', 'Garado', 'Garayblas', 'Garcia', 'Garduce',
    'Garrido', 'Gatdula', 'Gatmaitan', 'Gatus', 'Gawat',
    'Gelera', 'Gelua', 'Gemora', 'Genato', 'Generoso',
    'Gequillana', 'Gerona', 'Gerundio', 'Gianan', 'Gimenez',
    'Gloria', 'Glorioso', 'Glova', 'Golez', 'Gomez',
    'Gonzaga', 'Gonzales', 'Gordoncillo', 'Gorre', 'Grafilo',
    'Gregorio', 'Griño', 'Guanzon', 'Guerrero', 'Guevara',
    'Guiao', 'Guillen', 'Guinto', 'Guison', 'Gullas',
    'Gutierrez', 'Guzman', 'Hernandez', 'Herrera', 'Hizon',
    'Honasan', 'Hontiveros', 'Horca', 'Hufana', 'Humilde',
    'Ibañez', 'Ignacio', 'Ilustre', 'Imbong', 'Imperial',
    'Infante', 'Inion', 'Inocentes', 'Inso', 'Iringan',
    'Jacinto', 'Javier', 'Jimenez', 'Jose', 'Joson',
    'Juan', 'Juico', 'Jurado', 'Kabigting', 'Kalaw',
    'Kho', 'Lacaba', 'Lacadin', 'Lacson', 'Ladesma',
    'Laderas', 'Lagman', 'Lagua', 'Laguna', 'Lainez',
    'Lajarca', 'Lamayo', 'Lambino', 'Lapid', 'Lapuz',
    'Lara', 'Largo', 'Lariza', 'Larizal', 'Laserna',
    'Latorre', 'Laurel', 'Laurente', 'Lazaro', 'Leano',
    'Legarda', 'Leonor', 'Leynes', 'Libunao', 'Licup',
    'Lim', 'Limkaichong', 'Limpag', 'Liwanag', 'Llanes',
    'Llamado', 'Llaneta', 'Locsin', 'Logarta', 'Lopez',
    'Lorenzo', 'Lorilla', 'Lozada', 'Lucero', 'Luistro',
    'Luna', 'Luneta', 'Luzon', 'Macalintal', 'Macam',
    'Maceda', 'Madera', 'Madrazo', 'Magtanggol', 'Malabanan',
    'Malacaman', 'Malajacan', 'Malanyaon', 'Malaya', 'Malbas',
    'Malcampo', 'Maldia', 'Maligalig', 'Malinao', 'Malonzo',
    'Mangahas', 'Mangubat', 'Manigbas', 'Manila', 'Manlangit',
    'Manlapaz', 'Manlongat', 'Manrique', 'Mansalay', 'Mante',
    'Manuel', 'Manzano', 'Marcelo', 'Marcos', 'Mariano',
    'Maristela', 'Marquez', 'Maravilla', 'Masangkay', 'Masapol',
    'Mateo', 'Matienzo', 'Matining', 'Matugas', 'Maula',
    'Maulion', 'Mayuga', 'Medina', 'Mejia', 'Melchor',
    'Melo', 'Menor', 'Mercado', 'Mesina', 'Miguel',
    'Miralles', 'Miranda', 'Molano', 'Molina', 'Mondejar',
    'Monreal', 'Montano', 'Montenegro', 'Montero', 'Montes',
    'Montesa', 'Montoya', 'Moraga', 'Moraleda', 'Moreno',
    'Morial', 'Muncal', 'Muñoz', 'Murillo', 'Musni',
    'Nacion', 'Nadal', 'Nagrampa', 'Nalzaro', 'Napeñas',
    'Narciso', 'Natividad', 'Navales', 'Navarro', 'Neri',
    'Nicolas', 'Nisperos', 'Nolasco', 'Noynay', 'Nuñez',
    'Oaminal', 'Ocampo', 'Ocfemia', 'Ochoa', 'Olaguera',
    'Olano', 'Oliva', 'Olivares', 'Oliveros', 'Olpindo',
    'Omadto', 'Ombion', 'Onate', 'Ong', 'Orbeta',
    'Orbita', 'Ordoño', 'Orendain', 'Orense', 'Orobia',
    'Orozco', 'Ortega', 'Osmeña', 'Osorio', 'Ostrea',
    'Ouano', 'Pabiton', 'Pableo', 'Pabriaga', 'Pacanan',
    'Padayao', 'Padilla', 'Padua', 'Paguio', 'Pagulayan',
    'Palad', 'Palacios', 'Palafox', 'Palaganas', 'Palattao',
    'Palencia', 'Palma', 'Palo', 'Paloma', 'Palomares',
    'Pamaran', 'Pamintuan', 'Panaligan', 'Panganiban', 'Pangilinan',
    'Panopio', 'Papa', 'Paqueo', 'Paras', 'Paredes',
    'Parreño', 'Pascua', 'Pascual', 'Pastor', 'Paterno',
    'Patron', 'Pavia', 'Pecaña', 'Pecho', 'Pedrosa',
    'Pelayo', 'Peña', 'Peñaflor', 'Peñaranda', 'Penarroyo',
    'Peralta', 'Perez', 'Perlas', 'Pernia', 'Pesquera',
    'Pestano', 'Piccio', 'Picardal', 'Pineda', 'Pimentel',
    'Pilapil', 'Pili', 'Piliin', 'Pillar', 'Pilorin',
    'Poblete', 'Poliquit', 'Ponce', 'Ponferrada', 'Porras',
    'Prado', 'Prieto', 'Prodigalidad', 'Prudente', 'Punsalan',
    'Quezon', 'Quiambao', 'Quiaoit', 'Quijano', 'Quimpo',
    'Quinit', 'Quinones', 'Quiogue', 'Quirino', 'Quisao',
    'Racelis', 'Rada', 'Ramirez', 'Ramon', 'Ramos',
    'Ravalo', 'Rayala', 'Razon', 'Recinto', 'Recometa',
    'Reforma', 'Regalado', 'Reganit', 'Regio', 'Regidor',
    'Regis', 'Reodica', 'Respicio', 'Revilla', 'Reyes',
    'Ricafort', 'Ricalde', 'Ridad', 'Rillo', 'Rivera',
    'Rivero', 'Rizal', 'Robles', 'Roca', 'Rocamora',
    'Rocero', 'Rodriguez', 'Rojas', 'Romero', 'Ronquillo',
    'Rosales', 'Rosario', 'Rosete', 'Rotor', 'Roxas',
    'Rubio', 'Rufino', 'Ruiz', 'Sabal', 'Sabando',
    'Sabido', 'Sabijon', 'Sabio', 'Saceda', 'Saclolo',
    'Sagum', 'Salceda', 'Salcedo', 'Salgado', 'Salinas',
    'Saludar', 'Saluta', 'Salvador', 'Sambrano', 'Samson',
    'Sanchez', 'Sandoval', 'Sangalang', 'Santiago', 'Santillan',
    'Sanz', 'Sarino', 'Sarmiento', 'Sarona', 'Savellano',
    'Sebastian', 'Segovia', 'Sendin', 'Seneres', 'Serafica',
    'Sereno', 'Senga', 'Serrano', 'Sierra', 'Sigua',
    'Silva', 'Silvestre', 'Simon', 'Sinco', 'Singson',
    'Siy', 'Sobejana', 'Soberano', 'Socrates', 'Soliman',
    'Solis', 'Soliven', 'Solomon', 'Sotto', 'Suansing',
    'Suarez', 'Subido', 'Sulit', 'Sultan', 'Sumagaysay',
    'Sunga', 'Tabamo', 'Tabinas', 'Tabuena', 'Tagle',
    'Taguba', 'Tajonera', 'Talabong', 'Talavera', 'Talento',
    'Taleon', 'Talosig', 'Tamano', 'Tambalo', 'Tanada',
    'Tandoc', 'Tañada', 'Tarriela', 'Tating', 'Tautho',
    'Tayag', 'Tayco', 'Tecson', 'Tejano', 'Tejero',
    'Teodoro', 'Tibay', 'Tigas', 'Tiglao', 'Timbol',
    'Tingzon', 'Tiongco', 'Tiongson', 'Tirol', 'Tobias',
    'Toledo', 'Tolentino', 'Tomelden', 'Tomas', 'Tomaro',
    'Tomaroy', 'Torino', 'Torralba', 'Torrente', 'Torno',
    'Trea', 'Trinidad', 'Tuazon', 'Tubig', 'Tubigan',
    'Tugade', 'Tumbocon', 'Tupas', 'Tuquero', 'Turla',
    'Umagat', 'Umali', 'Usman', 'Uson', 'Uy',
    'Valdez', 'Valencia', 'Valenciano', 'Valentin', 'Valera',
    'Valiao', 'Varela', 'Vargas', 'Vasquez', 'Velarde',
    'Velasco', 'Velasquez', 'Velez', 'Vera', 'Vergara',
    'Vibandor', 'Vicente', 'Victorino', 'Vidal', 'Viernes',
    'Villacorta', 'Villaflor', 'Villafranca', 'Villagomez', 'Villagonzalo',
    'Villanueva', 'Villar', 'Villareal', 'Villaruel', 'Villaverde',
    'Villena', 'Virata', 'Vista', 'Vivar', 'Vizconde',
    'Yabes', 'Yap', 'Yasay', 'Yatco', 'Ylagan',
    'Yñiguez', 'Yorac', 'Yulo', 'Zabala', 'Zaldivar',
    'Zamora', 'Zapanta', 'Zaragoza', 'Zosa', 'Zulueta',
]

# Combine last names pool + extended middle names, deduplicated
middle_seen = set()
all_middle  = []
for name in (all_last + EXTENDED_MIDDLE_NAMES):
    if isinstance(name, str) and name not in middle_seen:
        middle_seen.add(name)
        all_middle.append(name)

print(f"      Total middle names : {len(all_middle)}")
print(f"      Sample             : {all_middle[:5]}")

# ── Step 5: Save to JSON ──────────────────────────────────────
print("\n[5/5] Saving to data/ph_names.json ...")

os.makedirs('data', exist_ok=True)

output = {
    "first_names": {
        "male":   male_first,
        "female": female_first,
        "all":    all_first
    },
    "last_names":   all_last,
    "middle_names": all_middle,
    "metadata": {
        "source":              "names-dataset (PyPI) -- country_alpha2='PH'",
        "total_first":         len(all_first),
        "total_last":          len(all_last),
        "total_middle":        len(all_middle),
        "total_name_combos":   len(all_first) * len(all_middle) * len(all_last),
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
print(f"  Middle names       : {len(all_middle)}")
print(f"  Possible 3-part name combos : {len(all_first) * len(all_middle) * len(all_last):,}")
print(f"\n  Saved to: data/ph_names.json")
print(f"\n  Next step: python fix_data.py")
print("=" * 60)