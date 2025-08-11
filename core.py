from __future__ import annotations
import pandas as pd, numpy as np, re, json, unicodedata
from io import BytesIO
from datetime import datetime

# ---------- Template ----------
TEMPLATE_COLUMNS = [
    'Champ (Obligatoire) / (Optionnel) :',
    'Identifiant utilisateurs*',
    'Civilité (M. / Mme)',
    'Prénom*',
    "Nom de naissance / Nom d'état-civil*",
    'Nom d\'usage / Nom marital',
    "Type d'utilisateur* (Diplômé [1] / Etudiant [5])",
    'Date de naissance (jj/mm/aaaa)',
    'Email personnel 1',
    'Email personnel 2',
    'Données Académiques',
    'Référence du diplôme (Code étape)',
    'Mode de formation',
    "Date d'intégration  (jj/mm/aaaa)",
    "Date d'obtention du diplôme (jj/mm/aaaa)",
    "A obtenu son diplôme ? (Oui [1] / Non [0])",
    'Données Personnelles',
    'Adresse personnelle',
    'Adresse personnelle - Complément',
    'Adresse personnelle – Complément 2',
    'Adresse personnelle - Code postal',
    'Adresse personnelle - Ville',
    'Adresse personnelle - Pays (ISO - 2 lettres)',
    'NPAI (Oui [1] / Non [0])',
    'Téléphone fixe personnel',
    'Téléphone mobile personnel',
    'Nationalité',
    'Données Professionelles',
    'Situation actuelle',
    'Titre du poste actuel',
    'Type de contrat – Intitulé',
    "Fonction dans l'entreprise",
    'Entreprise - Nom',
    "Entreprise - Secteur d'activité – Intitulé",
    'Entreprise - Code SIRET',
    'Entreprise - Site internet',
    'Adresse professionnelle',
    'Adresse professionnelle - Complément',
    'Adresse professionnelle - Code postal',
    'Adresse professionnelle - Ville',
    'Adresse professionnelle - Pays (ISO - 2 lettres)',
    'Téléphone fixe professionnel',
    'Téléphone mobile professionnel',
    'Email professionnel',
    "Début de l'expérience (jj/mm/aaaa)",
    "Fin de l'expérience (jj/mm/aaaa)"
]

# ---------- Lecture robuste (CSV/XLSX) ----------
def _detect_encoding(file_obj) -> str:
    try:
        import chardet
        pos = file_obj.tell()
        raw = file_obj.read()
        file_obj.seek(pos)
        res = chardet.detect(raw)
        return res.get("encoding") or "utf-8"
    except Exception:
        return "utf-8"

def read_table(upload, filename: str) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(upload)
    enc = _detect_encoding(upload)
    for sep in [',',';','\t','|']:
        upload.seek(0)
        try:
            df = pd.read_csv(upload, sep=sep, encoding=enc)
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    upload.seek(0)
    return pd.read_csv(upload, sep=None, engine='python', encoding=enc)

# ---------- Auto-mapping (scoring mots-clés) ----------
KEYWORDS = {
    'Identifiant utilisateurs*': ['identifiant','id','matricule','code'],
    'Civilité (M. / Mme)': ['civilite','civilité','mr','mme','genre','titre'],
    'Prénom*': ['prénom','prenom','firstname','first_name','first name'],
    "Nom de naissance / Nom d'état-civil*": ['nom','lastname','last_name','last name','nom_famille'],
    "Type d'utilisateur* (Diplômé [1] / Etudiant [5])": ['type','statut','categorie','catégorie','profil','rôle','role'],
    'Date de naissance (jj/mm/aaaa)': ['naissance','birth','date_naissance','datenaissance'],
    'Email personnel 1': ['email','mail','courriel','e-mail'],
    'Email personnel 2': ['email 2','second email','email secondaire'],
    'Référence du diplôme (Code étape)': ['diplome','diplôme','formation','code étape','référence diplôme'],
    "Date d'obtention du diplôme (jj/mm/aaaa)": ['obtention','date diplome','date obtention','fin formation'],
    "A obtenu son diplôme ? (Oui [1] / Non [0])": ['obtenu','validé','diplômé','réussi'],
    'Adresse personnelle': ['adresse','rue','street','adresse 1','address'],
    'Adresse personnelle - Code postal': ['code postal','cp','zip','postal'],
    'Adresse personnelle - Ville': ['ville','city','commune'],
    'Adresse personnelle - Pays (ISO - 2 lettres)': ['pays','country'],
    'Téléphone mobile personnel': ['mobile','portable','gsm','cell'],
    'Nationalité': ['nationalite','nationalité','citizenship'],
    'Titre du poste actuel': ['poste','titre','fonction','job title'],
    'Entreprise - Nom': ['entreprise','société','societe','company','employeur'],
    'Email professionnel': ['email pro','mail pro','email professionnel']
}

def auto_map(df: pd.DataFrame) -> dict:
    cols = [str(c) for c in df.columns]
    mapping, used = {}, set()
    for t in TEMPLATE_COLUMNS:
        if t in cols:
            mapping[t] = t; used.add(t)
    for t, kws in KEYWORDS.items():
        if t in mapping: 
            continue
        best, score_best = None, 0
        for col in cols:
            if col in used: 
                continue
            low = col.lower()
            score = 0
            for i, kw in enumerate(kws):
                if low == kw: score = 100; break
                if low.startswith(kw) or low.endswith(kw): score = max(score, 60-i)
                if kw in low: score = max(score, 30-i)
            if score > score_best:
                best, score_best = col, score
        if best:
            mapping[t] = best; used.add(best)
    if "Nom de naissance / Nom d'état-civil*" not in mapping and 'Prénom*' in mapping:
        for col in cols:
            if col in used: continue
            if col.lower() in ['nom','name']:
                mapping["Nom de naissance / Nom d'état-civil*"] = col; used.add(col); break
    return mapping

# ---------- Normalisations & validations ----------
FEMALE_HINTS = {"mme","madame","mlle","mademoiselle","f","femme"}
MALE_HINTS   = {"m","mr","monsieur","h","homme","m."}

COMMON_FEMALE_FIRSTNAMES = {"marie","claire","camille","julie","emma","lea","léa","anna","anne","chloe","chloé",
    "sarah","laura","pauline","juliette","manon","lisa","ines","inès","lucie","eva"}
COMMON_MALE_FIRSTNAMES = {"pierre","paul","jean","louis","lucas","nathan","thomas","hugo","arthur","leo","léo",
    "maxime","antoine","julien","mathieu","alexandre","baptiste","nicolas","yanis"}

def _norm_firstname(x: str) -> str:
    s = str(x or "").strip()
    if not s: return ""
    s = re.split(r"[\s\-]+", s)[0]
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.lower()

# Déduction civilité : gender-guesser si dispo, sinon sets simples
try:
    import gender_guesser.detector as _gg
    _GG = _gg.Detector(case_sensitive=False)
    def deduce_civility_from_firstname(firstname: str) -> str:
        f = _norm_firstname(firstname)
        if not f: return ""
        g = _GG.get_gender(f)
        if g in ("female","mostly_female"): return "Mme"
        if g in ("male","mostly_male"):     return "M."
        return ""
except Exception:
    def deduce_civility_from_firstname(firstname: str) -> str:
        f = _norm_firstname(firstname)
        if not f: return ""
        if f in COMMON_FEMALE_FIRSTNAMES: return "Mme"
        if f in COMMON_MALE_FIRSTNAMES:   return "M."
        return ""

def format_civilite(value: str) -> str:
    s = str(value).strip().lower()
    if not s: return ""
    if s in FEMALE_HINTS: return "Mme"
    if s in MALE_HINTS:   return "M."
    if "madame" in s: return "Mme"
    if "monsieur" in s: return "M."
    return str(value).strip()

def format_date(value: str) -> str:
    s = str(value).strip()
    if not s: return ""
    s = s.replace('.', '/').replace('-', '/')
    if re.match(r'^\d{2}/\d{2}/\d{4}$', s): return s
    for fmt in ['%d/%m/%Y','%Y/%m/%d','%m/%d/%Y']:
        try: return pd.to_datetime(s, format=fmt, dayfirst=True).strftime('%d/%m/%Y')
        except: pass
    try: return pd.to_datetime(s, dayfirst=True).strftime('%d/%m/%Y')
    except: return s

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)

def format_email(value: str, warnings, rownum, strict: bool) -> str:
    if value is None or pd.isna(value):
        return ""
    s = str(value).strip().lower()
    if not s:
        return ""
    if not EMAIL_RE.match(s):
        msg = f"Ligne {rownum}: Email suspect '{value}'"
        if strict: raise ValueError(msg)
        warnings.append(msg)
    return s

def format_boolean(value: str) -> str:
    v = str(value).strip().lower()
    if v in ['oui','o','yes','y','1','true','vrai','x']: return '1'
    if v in ['non','n','no','0','false','faux','']: return '0'
    return v

# Pays : table légère FR/EU + fallback 2 lettres
FALLBACK_COUNTRIES = {
    'FRANCE':'FR','BELGIQUE':'BE','SUISSE':'CH','ALLEMAGNE':'DE','ESPAGNE':'ES','ITALIE':'IT',
    'ROYAUME-UNI':'GB','LUXEMBOURG':'LU','PAYS-BAS':'NL','PORTUGAL':'PT','ETATS-UNIS':'US','CANADA':'CA',
    'MAROC':'MA','ALGERIE':'DZ','TUNISIE':'TN','SENEGAL':'SN',"COTE D'IVOIRE":'CI','CAMEROUN':'CM'
}

def format_country(value: str, warnings, rownum, strict: bool) -> str:
    s = str(value).strip()
    if not s: return ""
    if len(s) == 2 and s.isalpha(): return s.upper()
    up = s.upper()
    for k,v in FALLBACK_COUNTRIES.items():
        if k in up or up in k:
            return v
    msg = f"Ligne {rownum}: Pays non reconnu '{value}'"
    if strict: raise ValueError(msg)
    warnings.append(msg)
    return s[:2].upper() if len(s)>=2 else s

# Téléphones : heuristique FR simple (+ avertissements)
def format_phone(value: str, warnings, rownum, strict: bool) -> str:
    s = re.sub(r'\D', '', str(value))
    if not s: return ""
    # FR : autorise 0XXXXXXXXX ; tolère +33/0033
    if s.startswith('33') and len(s)==11: s = '0'+s[2:]
    if s.startswith('0033') and len(s)==13: s = '0'+s[4:]
    if s.startswith('0') and len(s) != 10:
        msg = f"Ligne {rownum}: Téléphone suspect '{value}' ({len(s)} chiffres)"
        if strict: raise ValueError(msg)
        warnings.append(msg)
    return s

# SIRET (Luhn)
def _luhn_ok(num: str) -> bool:
    s = [int(d) for d in re.sub(r'\D','', num)]
    if not s: return False
    parity = len(s) % 2
    total = 0
    for i,d in enumerate(s):
        if i % 2 == parity:
            d = d*2
            if d>9: d -= 9
        total += d
    return total % 10 == 0

def format_siret(value: str, warnings, rownum, strict: bool) -> str:
    s = re.sub(r'\D','', str(value))
    if not s: return ""
    if len(s) != 14 or not _luhn_ok(s):
        msg = f"Ligne {rownum}: SIRET invalide '{value}'"
        if strict: raise ValueError(msg)
        warnings.append(msg)
    return s

def suggest_user_type(val: str) -> str | None:
    v = str(val).lower()
    if any(k in v for k in ['diplome','diplôme','diplômé','alumni','ancien']): return '1'
    if any(k in v for k in ['etudiant','étudiant','eleve','élève','student','stagiaire']): return '5'
    return None

# ========== NOUVELLES FONCTIONS D'AMÉLIORATION ==========

def suggest_civilite(val: str) -> str | None:
    """Suggère une civilité basée sur des variantes courantes"""
    v = str(val).lower().strip()
    
    # Variantes courantes
    CIVILITE_PATTERNS = {
        'M.': ['m', 'mr', 'monsieur', 'homme', 'h', 'm.', 'masculin', 'male', 'mister'],
        'Mme': ['mme', 'madame', 'femme', 'f', 'mlle', 'mademoiselle', 'feminin', 'female', 'mrs', 'miss', 'ms']
    }
    
    for correct, patterns in CIVILITE_PATTERNS.items():
        if v in patterns or any(p in v for p in patterns if len(p) > 2):
            return correct
    return None

def suggest_oui_non(val: str) -> str | None:
    """Suggère 1 ou 0 pour les champs booléens"""
    v = str(val).lower().strip()
    
    OUI_PATTERNS = ['oui', 'o', 'yes', 'y', '1', 'true', 'vrai', 'x', 'ok', 'validé', 'obtenu', 'diplômé']
    NON_PATTERNS = ['non', 'n', 'no', '0', 'false', 'faux', 'nok', 'ko', 'pas obtenu', 'en cours']
    
    if v in OUI_PATTERNS or any(p in v for p in ['oui', 'yes', 'validé', 'obtenu']):
        return '1'
    if v in NON_PATTERNS or any(p in v for p in ['non', 'no', 'pas', 'aucun']):
        return '0'
    return None

def suggest_country_code(val: str) -> str | None:
    """Suggère un code pays ISO à partir d'un nom de pays"""
    v = str(val).upper().strip()
    
    # Table étendue des pays courants
    COUNTRY_MAPPINGS = {
        'FR': ['FRANCE', 'FR', 'FRA', 'FRENCH', 'FRANÇAIS', 'FRANCAISE'],
        'BE': ['BELGIQUE', 'BE', 'BEL', 'BELGIUM', 'BELGE'],
        'CH': ['SUISSE', 'CH', 'CHE', 'SWITZERLAND', 'SWISS', 'SCHWEIZ'],
        'DE': ['ALLEMAGNE', 'DE', 'DEU', 'GERMANY', 'DEUTSCHLAND', 'ALLEMAND'],
        'ES': ['ESPAGNE', 'ES', 'ESP', 'SPAIN', 'ESPAÑA', 'ESPAGNOL'],
        'IT': ['ITALIE', 'IT', 'ITA', 'ITALY', 'ITALIA', 'ITALIEN'],
        'GB': ['ROYAUME-UNI', 'GB', 'GBR', 'UK', 'UNITED KINGDOM', 'ANGLETERRE', 'ENGLAND'],
        'US': ['ETATS-UNIS', 'US', 'USA', 'UNITED STATES', 'AMERICA', 'AMERIQUE'],
        'CA': ['CANADA', 'CA', 'CAN', 'CANADIEN'],
        'LU': ['LUXEMBOURG', 'LU', 'LUX', 'LUXEMBOURGEOIS'],
        'NL': ['PAYS-BAS', 'NL', 'NLD', 'NETHERLANDS', 'HOLLANDE', 'HOLLAND'],
        'PT': ['PORTUGAL', 'PT', 'PRT', 'PORTUGAIS'],
        'MA': ['MAROC', 'MA', 'MAR', 'MOROCCO', 'MAROCAIN'],
        'DZ': ['ALGERIE', 'DZ', 'DZA', 'ALGERIA', 'ALGERIEN'],
        'TN': ['TUNISIE', 'TN', 'TUN', 'TUNISIA', 'TUNISIEN'],
    }
    
    for code, patterns in COUNTRY_MAPPINGS.items():
        if v in patterns or any(p in v for p in patterns if len(p) > 3):
            return code
    
    # Si c'est déjà un code 2 lettres, le retourner
    if len(v) == 2 and v.isalpha():
        return v
    
    return None

def clean_phone_number(val: str) -> str:
    """Nettoie et formate un numéro de téléphone"""
    # Garder seulement les chiffres
    cleaned = re.sub(r'\D', '', str(val))
    
    # Gérer les préfixes internationaux courants
    if cleaned.startswith('33') and len(cleaned) == 11:  # France
        cleaned = '0' + cleaned[2:]
    elif cleaned.startswith('0033') and len(cleaned) == 13:
        cleaned = '0' + cleaned[4:]
    elif cleaned.startswith('32') and len(cleaned) == 11:  # Belgique
        cleaned = '0' + cleaned[2:]
    elif cleaned.startswith('41') and len(cleaned) == 11:  # Suisse
        cleaned = '0' + cleaned[2:]
    
    # Formater avec espaces pour la lisibilité (optionnel)
    if len(cleaned) == 10 and cleaned.startswith('0'):
        # Format français : 01 23 45 67 89
        formatted = ' '.join([cleaned[i:i+2] for i in range(0, 10, 2)])
        return formatted
    
    return cleaned

def detect_date_format(sample_dates: list) -> str:
    """Détecte automatiquement le format de date utilisé"""
    formats_to_try = [
        ('%d/%m/%Y', 'JJ/MM/AAAA'),
        ('%d-%m-%Y', 'JJ-MM-AAAA'),
        ('%Y/%m/%d', 'AAAA/MM/JJ'),
        ('%Y-%m-%d', 'AAAA-MM-JJ'),
        ('%m/%d/%Y', 'MM/JJ/AAAA'),
        ('%d.%m.%Y', 'JJ.MM.AAAA'),
    ]
    
    format_scores = {}
    
    for date_str in sample_dates[:10]:  # Tester sur 10 échantillons max
        if pd.isna(date_str) or not str(date_str).strip():
            continue
            
        for fmt, name in formats_to_try:
            try:
                datetime.strptime(str(date_str).strip(), fmt)
                format_scores[name] = format_scores.get(name, 0) + 1
            except:
                pass
    
    if format_scores:
        return max(format_scores, key=format_scores.get)
    return "Format non détecté"

def analyze_column_values(df: pd.DataFrame, col_name: str) -> dict:
    """Analyse les valeurs d'une colonne pour suggérer des transformations"""
    col = df[col_name]
    values = col.dropna().astype(str).str.strip()
    
    analysis = {
        'total': len(col),
        'non_empty': len(values),
        'unique': values.nunique(),
        'most_common': values.value_counts().head(5).to_dict() if len(values) > 0 else {},
        'suggestions': []
    }
    
    # Détection de patterns
    if values.nunique() < 10:  # Peu de valeurs uniques = probablement catégoriel
        analysis['type'] = 'categorical'
        
        # Suggérer des mappings pour les valeurs ambiguës
        for val in values.unique():
            # Pour civilité
            if col_name.lower() in ['civilite', 'civilité', 'genre', 'titre']:
                suggestion = suggest_civilite(val)
                if suggestion and suggestion != val:
                    analysis['suggestions'].append({
                        'original': val,
                        'suggested': suggestion,
                        'confidence': 'high'
                    })
            
            # Pour booléens
            elif any(word in col_name.lower() for word in ['obtenu', 'npai', 'validé']):
                suggestion = suggest_oui_non(val)
                if suggestion and suggestion != val:
                    analysis['suggestions'].append({
                        'original': val,
                        'suggested': suggestion,
                        'confidence': 'high'
                    })
    
    # Détection de dates
    elif any(word in col_name.lower() for word in ['date', 'naissance', 'obtention', 'integration']):
        analysis['type'] = 'date'
        analysis['format_detected'] = detect_date_format(values.tolist())
    
    # Détection d'emails
    elif '@' in ''.join(values.head(10).tolist()):
        analysis['type'] = 'email'
        invalid_emails = []
        for val in values.head(20):  # Vérifier les 20 premiers
            if not re.match(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", val, re.I):
                invalid_emails.append(val)
        if invalid_emails:
            analysis['invalid_examples'] = invalid_emails[:5]
    
    # Détection de téléphones
    elif any(re.search(r'\d{8,}', str(val)) for val in values.head(10)):
        analysis['type'] = 'phone'
        # Exemples de numéros mal formatés
        needs_cleaning = []
        for val in values.head(20):
            cleaned = clean_phone_number(val)
            if cleaned != val:
                needs_cleaning.append({'original': val, 'cleaned': cleaned})
        if needs_cleaning:
            analysis['needs_cleaning'] = needs_cleaning[:5]
    
    return analysis

def generate_data_quality_report(df: pd.DataFrame, mapping: dict) -> dict:
    """Génère un rapport de qualité des données avec suggestions"""
    report = {
        'summary': {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'mapped_columns': len(mapping),
            'unmapped_columns': len(df.columns) - len(mapping)
        },
        'column_analysis': {},
        'global_suggestions': []
    }
    
    # Analyser chaque colonne mappée
    for template_col, source_col in mapping.items():
        if source_col in df.columns:
            analysis = analyze_column_values(df, source_col)
            report['column_analysis'][template_col] = analysis
            
            # Ajouter des suggestions globales
            if analysis.get('suggestions'):
                report['global_suggestions'].append({
                    'column': template_col,
                    'type': 'value_mapping',
                    'suggestions': analysis['suggestions']
                })
    
    # Score de qualité global
    quality_score = 100
    
    # Pénalités
    if report['summary']['unmapped_columns'] > 0:
        quality_score -= report['summary']['unmapped_columns'] * 2
    
    for col, analysis in report['column_analysis'].items():
        # Pénalité pour données manquantes
        empty_ratio = 1 - (analysis['non_empty'] / analysis['total'])
        if empty_ratio > 0.5:
            quality_score -= 10
        elif empty_ratio > 0.2:
            quality_score -= 5
    
    report['quality_score'] = max(0, quality_score)
    
    return report

# ---------- Process principal ----------
def process(
    df: pd.DataFrame, mapping: dict,
    correct_dates: bool=True, uppercase_names: bool=True,
    user_type_map: dict | None=None,
    auto_civility: bool=True, auto_user_type: bool=True,
    strict: bool=False,
    civil_fallback: str="",                    # "", "M.", "Mme"
    default_user_type_when_missing: str | None=None,  # None / "1" / "5"
    require_user_type_choice: bool=False
):
    user_type_map = user_type_map or {}
    errors, warnings = [], []
    out_rows = [TEMPLATE_COLUMNS, ['-']*len(TEMPLATE_COLUMNS)]
    stats = {'total_rows':0,'valid_rows':0,'corrected_fields':0}

    for ridx, (_,row) in enumerate(df.iterrows(), start=2):
        stats['total_rows'] += 1
        out = ['']*len(TEMPLATE_COLUMNS)
        row_has_data = False

        raw = {}
        for i,t in enumerate(TEMPLATE_COLUMNS):
            val = row[mapping[t]] if t in mapping and mapping[t] in df.columns else ''
            if pd.notna(val) and str(val).strip(): row_has_data = True
            raw[i] = val

        prenom_raw = str(raw.get(3,"") or "").strip()

        try:
            for i,t in enumerate(TEMPLATE_COLUMNS):
                s = str(raw.get(i,"") if raw.get(i) is not None else "").strip()
                new = s

                if i == 2:  # Civilité
                    new = format_civilite(s)
                    if not new and auto_civility and prenom_raw:
                        ded = deduce_civility_from_firstname(prenom_raw)
                        if ded:
                            new = ded
                            warnings.append(f"Ligne {ridx}: Civilité déduite depuis le prénom '{prenom_raw}' → '{ded}'")
                    if not new and civil_fallback in ("M.","Mme"):
                        new = civil_fallback
                        warnings.append(f"Ligne {ridx}: Civilité manquante, fallback '{civil_fallback}'")

                elif i == 3:  # Prénom
                    new = s.title() if s else s

                elif i in [4,5]:  # Noms
                    new = s.upper() if (s and uppercase_names) else s

                elif i == 6:  # Type utilisateur
                    if s in ['1','5']:
                        new = s
                    elif s in user_type_map:
                        new = user_type_map[s]
                        warnings.append(f"Ligne {ridx}: Type '{s}' → '{new}' (mapping)")
                    elif auto_user_type:
                        sug = suggest_user_type(s)
                        if sug:
                            new = sug
                            warnings.append(f"Ligne {ridx}: Type '{s}' → '{sug}' (déduit)")
                        elif mapping.get("Type d'utilisateur* (Diplômé [1] / Etudiant [5])") is None:
                            has_company = any(str(raw.get(j,"")).strip() for j in [31,34])  # Entreprise / SIRET
                            new = '1' if has_company else s

                elif i in [7,13,14,44,45]:  # dates
                    new = format_date(s) if (s and correct_dates) else s
                    if strict and new and not re.match(r'^\d{2}/\d{2}/\d{4}$', new):
                        raise ValueError(f"Ligne {ridx}: Date invalide '{s}'")

                elif i in [8,9,43]:  # emails
                    new = format_email(s, warnings, ridx, strict)

                elif i in [15,23]:  # booléens
                    new = format_boolean(s)

                elif i in [22,40]:  # pays
                    new = format_country(s, warnings, ridx, strict) if s else s

                elif i in [24,25,41,42]:  # téléphones
                    new = format_phone(s, warnings, ridx, strict) if s else s

                elif i == 34:  # SIRET
                    new = format_siret(s, warnings, ridx, strict) if s else s

                out[i] = new
                if new != s and s != "":
                    stats['corrected_fields'] += 1

        except Exception as e:
            errors.append(str(e))

        # Post-traitement Type utilisateur manquant
        type_idx = 6
        if row_has_data:
            if not out[type_idx] or out[type_idx] not in ("1","5"):
                if require_user_type_choice and default_user_type_when_missing is None:
                    errors.append("TYPE_UTILISATEUR_MANQUANT")
                elif default_user_type_when_missing in ("1","5"):
                    out[type_idx] = default_user_type_when_missing
                    warnings.append(f"Ligne {ridx}: Type manquant → fallback '{default_user_type_when_missing}'")

        if row_has_data:
            if (not out[3]) or (not out[4]):
                errors.append(f"Ligne {ridx}: Prénom/Nom manquant")
            else:
                stats['valid_rows'] += 1
            out_rows.append(out)

    df_out = pd.DataFrame(out_rows[2:], columns=out_rows[0])
    return df_out, stats, errors, warnings

# ---------- Exports ----------
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Import Utilisateur')
        pd.DataFrame([['Code','Libellé'],['1','Diplômé'],['5','Étudiant']]).to_excel(
            w, index=False, header=False, sheet_name='Type_Utilisateur'
        )
    bio.seek(0)
    return bio.getvalue()
