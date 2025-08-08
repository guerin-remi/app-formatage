# core.py
from __future__ import annotations
import pandas as pd, numpy as np, re, json
from io import BytesIO
from datetime import datetime
from html import escape


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

# ---------- Lecture robuste ----------
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
    # CSV : test encodage + séparateurs
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

# ---------- Mapping auto (scoring mots-clés) ----------
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

    # exact
    for t in TEMPLATE_COLUMNS:
        if t in cols:
            mapping[t] = t
            used.add(t)

    # mots-clés
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

    # fallback "nom"
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

try:
    import gender_guesser.detector as _gg
    _GG = _gg.Detector(case_sensitive=False)
    def deduce_civility_from_firstname(firstname: str) -> str:
        if not firstname: return ""
        g = _GG.get_gender(str(firstname))
        if g in ("female","mostly_female"): return "Mme"
        if g in ("male","mostly_male"):     return "M."
        return ""
except Exception:
    def deduce_civility_from_firstname(firstname: str) -> str:
        if not firstname: return ""
        f = str(firstname).strip().lower()
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
    # si déjà jj/mm/aaaa
    if re.match(r'^\d{2}/\d{2}/\d{4}$', s): return s
    for fmt in ['%d/%m/%Y','%Y/%m/%d','%m/%d/%Y']:
        try: return pd.to_datetime(s, format=fmt, dayfirst=True).strftime('%d/%m/%Y')
        except: pass
    try: return pd.to_datetime(s, dayfirst=True).strftime('%d/%m/%Y')
    except: return s

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)

def format_email(value: str, warnings, rownum, strict: bool) -> str:
    s = str(value).strip().lower()
    if not s: return ""
    if not EMAIL_RE.match(s):
        msg = f"Ligne {rownum}: Email suspect '{value}'"
        (warnings if not strict else warnings).append(msg)  # en strict, sera promu en erreur plus bas si besoin
    return s

def format_boolean(value: str) -> str:
    v = str(value).strip().lower()
    if v in ['oui','o','yes','y','1','true','vrai','x']: return '1'
    if v in ['non','n','no','0','false','faux','']: return '0'
    return v

# Pays
def _iso2_from_name(name: str) -> str | None:
    try:
        import pycountry
        n = name.upper()
        # essai exact
        for c in pycountry.countries:
            if n in {c.name.upper(), getattr(c, 'official_name', '').upper()}:
                return c.alpha_2
        # essai partiel
        for c in pycountry.countries:
            if n in c.name.upper() or c.name.upper() in n:
                return c.alpha_2
    except Exception:
        pass
    # fallback mini table
    fallback = {'FRANCE':'FR','BELGIQUE':'BE','SUISSE':'CH','ALLEMAGNE':'DE','ESPAGNE':'ES','ITALIE':'IT',
                'ROYAUME-UNI':'GB','LUXEMBOURG':'LU','PAYS-BAS':'NL','PORTUGAL':'PT','ETATS-UNIS':'US','CANADA':'CA',
                'MAROC':'MA','ALGERIE':'DZ','TUNISIE':'TN','SENEGAL':'SN',"COTE D'IVOIRE":'CI','CAMEROUN':'CM'}
    for k,v in fallback.items():
        if k in name.upper() or name.upper() in k: return v
    return None

def format_country(value: str, warnings, rownum, strict: bool) -> str:
    s = str(value).strip()
    if not s: return ""
    if len(s) == 2 and s.isalpha(): return s.upper()
    code = _iso2_from_name(s)
    if not code:
        msg = f"Ligne {rownum}: Pays non reconnu '{value}'"
        if strict: raise ValueError(msg)
        warnings.append(msg)
        return s[:2].upper() if len(s)>=2 else s
    return code

# Téléphones
def format_phone(value: str, warnings, rownum, strict: bool) -> str:
    s = re.sub(r'\D', '', str(value))
    if not s: return ""
    try:
        import phonenumbers
        # Si FR probable, complète au besoin
        if s.startswith('0') and len(s)==10:
            parsed = phonenumbers.parse(s, "FR")
        else:
            parsed = phonenumbers.parse(s, None)  # laisse la lib deviner si indicatif présent
        if not phonenumbers.is_valid_number(parsed):
            raise Exception("invalid")
        # retourne format national FR si FR, sinon E164
        region = phonenumbers.region_code_for_number(parsed)
        if region == "FR":
            nat = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            return re.sub(r'\D','', nat)  # 0XXXXXXXXX
        else:
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        msg = f"Ligne {rownum}: Téléphone suspect '{value}'"
        if strict: raise ValueError(msg)
        warnings.append(msg)
        # fallback FR simple
        if s.startswith('33') and len(s)==11: s = '0'+s[2:]
        if s.startswith('0033') and len(s)==13: s = '0'+s[4:]
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

# ---------- Process principal ----------
def process(
    df: pd.DataFrame, mapping: dict,
    correct_dates: bool=True, uppercase_names: bool=True,
    user_type_map: dict | None=None,
    auto_civility: bool=True, auto_user_type: bool=True,
    strict: bool=False
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
                            has_company = any(str(raw.get(j,"")).strip() for j in [31,34])  # Entreprise - Nom / SIRET
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

# ---------- Rapport HTML ----------
def report_html_bytes(df_out: pd.DataFrame, stats: dict, errors: list[str], warnings: list[str]) -> bytes:
def li(items):
    return "".join(f"<li>{escape(str(x))}</li>" for x in items)
    html = f"""
<!doctype html><html><head><meta charset="utf-8"><title>Rapport Import</title>
<style>
body{{font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial; margin:24px; color:#111827}}
h1,h2{{margin:0 0 8px}} .muted{{color:#6B7280}}
.card{{border:1px solid #E5E7EB; border-radius:10px; padding:16px; margin:12px 0}}
.kpis{{display:flex; gap:12px; flex-wrap:wrap}}
.kpi{{border:1px solid #E5E7EB; border-radius:10px; padding:10px 12px}}
</style></head><body>
<h1>Rapport d'import</h1>
<p class="muted">Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
<div class="kpis">
<div class="kpi">Lignes traitées: <b>{stats.get("total_rows",0)}</b></div>
<div class="kpi">Lignes valides: <b>{stats.get("valid_rows",0)}</b></div>
<div class="kpi">Champs corrigés: <b>{stats.get("corrected_fields",0)}</b></div>
<div class="kpi">Erreurs: <b>{len(errors)}</b></div>
<div class="kpi">Avertissements: <b>{len(warnings)}</b></div>
</div>
<div class="card"><h2>Erreurs</h2><ul>{li(errors) if errors else "<li>Aucune</li>"}</ul></div>
<div class="card"><h2>Avertissements</h2><ul>{li(warnings) if warnings else "<li>Aucun</li>"}</ul></div>
</body></html>
"""
    return html.encode("utf-8")

# ---------- Presets mapping ----------
def mapping_to_json(mapping: dict) -> bytes:
    return json.dumps(mapping, ensure_ascii=False, indent=2).encode("utf-8")

def mapping_from_json(b: bytes) -> dict:
    return json.loads(b.decode("utf-8"))
