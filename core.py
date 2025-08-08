# core.py
import pandas as pd, numpy as np, re
from datetime import datetime
from io import BytesIO

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

PAYS_ISO = {'FRANCE':'FR','BELGIQUE':'BE','SUISSE':'CH','ALLEMAGNE':'DE','ESPAGNE':'ES','ITALIE':'IT',
'ROYAUME-UNI':'GB','LUXEMBOURG':'LU','PAYS-BAS':'NL','PORTUGAL':'PT','ETATS-UNIS':'US','CANADA':'CA',
'MAROC':'MA','ALGERIE':'DZ','TUNISIE':'TN','SENEGAL':'SN',"COTE D'IVOIRE":'CI','CAMEROUN':'CM',
'BRESIL':'BR','ARGENTINE':'AR','MEXIQUE':'MX','CHINE':'CN','JAPON':'JP','COREE DU SUD':'KR','INDE':'IN',
'AUSTRALIE':'AU','NOUVELLE-ZELANDE':'NZ','RUSSIE':'RU','POLOGNE':'PL','ROUMANIE':'RO','GRECE':'GR','TURQUIE':'TR'}

# --- utilitaires lecture ---
def read_table(upload, filename: str) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith('.xlsx') or name.endswith('.xls'):
        return pd.read_excel(upload)
    # CSV: test quelques séparateurs courants
    upload.seek(0)
    for sep in [',',';','\t','|']:
        upload.seek(0)
        try:
            df = pd.read_csv(upload, sep=sep, encoding='utf-8')
            if len(df.columns) > 1: return df
        except Exception:
            pass
    upload.seek(0)
    return pd.read_csv(upload, sep=None, engine='python')  # détection auto

# --- mapping auto très simple (reprend l’esprit de ta GUI) ---
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
    'Adresse personnelle': ['adresse','rue','street','adresse 1'],
    'Adresse personnelle - Code postal': ['code postal','cp','zip','postal'],
    'Adresse personnelle - Ville': ['ville','city','commune'],
    'Adresse personnelle - Pays (ISO - 2 lettres)': ['pays','country'],
    'Téléphone mobile personnel': ['mobile','portable','gsm','cell'],
    'Nationalité': ['nationalite','nationalité','citizenship'],
    'Titre du poste actuel': ['poste','titre','fonction','job title'],
    'Entreprise - Nom': ['entreprise','société','societe','company','employeur'],
    'Email professionnel': ['email pro','mail pro','email professionnel']
}

def auto_map(df: pd.DataFrame):
    src = [str(c) for c in df.columns]
    mapping = {}
    used = set()
    # exact
    for t in TEMPLATE_COLUMNS:
        if t in src:
            mapping[t] = t
            used.add(t)
    # keywords
    for t, kws in KEYWORDS.items():
        if t in mapping: continue
        best = None; score_best = 0
        for col in src:
            if col in used: continue
            low = col.lower()
            score = 0
            for i,kw in enumerate(kws):
                if low == kw: score = 100; break
                if low.startswith(kw) or low.endswith(kw): score = max(score, 50-i)
                if kw in low: score = max(score, 25-i)
            if score > score_best:
                score_best = score; best = col
        if best:
            mapping[t] = best; used.add(best)
    # nom si juste "nom" et prénom trouvé
    if "Nom de naissance / Nom d'état-civil* not in mapping" and 'Prénom*' in mapping:
        for col in src:
            if col in used: continue
            low = col.lower()
            if low in ['nom','name']:
                mapping["Nom de naissance / Nom d'état-civil*"] = col; used.add(col); break
    return mapping

# --- formatages (versions sans état GUI) ---
def format_civilite(value: str):
    v = value.strip().lower()
    if v in ['mme','madame','mlle','mademoiselle','f','femme']: return 'Mme'
    if v in ['m','mr','monsieur','h','homme','m.']: return 'M.'
    return value

def format_date(value: str):
    if re.match(r'^\d{2}/\d{2}/\d{4}$', value): return value
    value = value.replace('.', '/')
    for fmt in ['%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%Y/%m/%d','%m/%d/%Y']:
        try: return pd.to_datetime(value, format=fmt, dayfirst=True).strftime('%d/%m/%Y')
        except: pass
    try: return pd.to_datetime(value, dayfirst=True).strftime('%d/%m/%Y')
    except: return value

def format_boolean(value: str):
    v = value.strip().lower()
    if v in ['oui','o','yes','y','1','true','vrai','x']: return '1'
    if v in ['non','n','no','0','false','faux','']: return '0'
    return value

def format_country(value: str, warnings, rownum):
    v = value.strip().upper()
    if len(v)==2: return v
    if v in PAYS_ISO: return PAYS_ISO[v]
    for k,code in PAYS_ISO.items():
        if k in v or v in k: return code
    warnings.append(f"Ligne {rownum}: Code pays non reconnu '{value}'")
    return v[:2] if len(v)>=2 else v

def format_phone(value: str, warnings, rownum):
    phone = re.sub(r'\D','', str(value))
    if phone.startswith('33') and len(phone)==11: phone = '0'+phone[2:]
    if phone.startswith('0033') and len(phone)==13: phone = '0'+phone[4:]
    if phone.startswith('0') and len(phone)!=10:
        warnings.append(f"Ligne {rownum}: Téléphone suspect '{value}' ({len(phone)} chiffres)")
    return phone

def suggest_user_type(val: str):
    v = val.lower()
    if any(k in v for k in ['diplome','diplôme','diplômé','alumni','ancien']): return '1'
    if any(k in v for k in ['etudiant','étudiant','eleve','élève','student','stagiaire']): return '5'
    return None

def process(df: pd.DataFrame, mapping: dict, correct_dates=True, uppercase_names=True, user_type_map=None):
    user_type_map = user_type_map or {}
    errors, warnings = [], []
    rows_total = len(df)
    out_rows = []
    out_rows.append(TEMPLATE_COLUMNS)
    out_rows.append(['-']*len(TEMPLATE_COLUMNS))
    stats = {'total_rows':0,'valid_rows':0,'corrected_fields':0}

    for ridx, (_,row) in enumerate(df.iterrows(), start=2):
        stats['total_rows'] += 1
        out = ['']*len(TEMPLATE_COLUMNS)
        row_has_data = False
        # récupérer brut
        raw = {}
        for i,t in enumerate(TEMPLATE_COLUMNS):
            if t in mapping:
                val = row[mapping[t]]
                if pd.notna(val) and str(val).strip(): row_has_data=True
                raw[i] = val
            else:
                raw[i] = ''
        # formatter
        for i,t in enumerate(TEMPLATE_COLUMNS):
            val = raw.get(i,'')
            if pd.isna(val) or str(val).strip()=='':
                out[i] = ''
                continue
            s = str(val).strip()
            new = s
            if i==2: new = format_civilite(s)
            elif i==3: new = s.title()
            elif i in [4,5]: new = s.upper() if uppercase_names else s
            elif i==6:
                # user type
                if s in ['1','5']: new = s
                elif s in user_type_map:
                    new = user_type_map[s]
                    warnings.append(f"Ligne {ridx}: Type '{s}' → '{new}' (mapping)")
                else:
                    sug = suggest_user_type(s)
                    new = sug if sug else s
                    if sug: warnings.append(f"Ligne {ridx}: Type '{s}' → '{sug}' (déduit)")
            elif i in [7,13,14,44,45]:
                new = format_date(s) if correct_dates else s
            elif i in [8,9,43]:
                new = s.lower()
            elif i in [15,23]:
                new = format_boolean(s)
            elif i in [22,40]:
                new = format_country(s, warnings, ridx)
            elif i in [24,25,41,42]:
                new = format_phone(s, warnings, ridx)
            elif i==34:
                new = re.sub(r'\D','', s)
            out[i]=new
            if new!=s: stats['corrected_fields'] += 1

        # champs vraiment obligatoires si la ligne a des données
        if row_has_data:
            if (not out[3]) or (not out[4]):
                errors.append(f"Ligne {ridx}: Prénom/Nom manquant")
            else:
                stats['valid_rows'] += 1
            out_rows.append(out)

    df_out = pd.DataFrame(out_rows[2:], columns=out_rows[0])
    return df_out, stats, errors, warnings

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

def to_excel_bytes(df: pd.DataFrame):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Import Utilisateur')
        # feuilles de référence (facultatif ici)
        pd.DataFrame([['Code','Libellé'],['1','Diplômé'],['5','Étudiant']]).to_excel(w, index=False, header=False, sheet_name='Type_Utilisateur')
    bio.seek(0)
    return bio.getvalue()
