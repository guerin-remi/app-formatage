# app.py
import streamlit as st
import pandas as pd
from core import (
    read_table, auto_map, process,
    to_csv_bytes, to_excel_bytes,
    suggest_civilite, suggest_oui_non, suggest_country_code,
    clean_phone_number, detect_date_format, 
    analyze_column_values, generate_data_quality_report
)

st.set_page_config(page_title="Import Utilisateur", page_icon="📦", layout="wide")
st.title("📦 Import Utilisateur")
st.caption("Uploader → Mapper → Formater → Télécharger")

# ---- Sidebar : options essentielles
with st.sidebar:
    st.header("Options")
    correct_dates   = st.checkbox("Corriger les dates", value=True)
    uppercase_names = st.checkbox("Noms en MAJUSCULES", value=True)
    auto_civility   = st.checkbox("Déduire civilité (si vide) depuis le prénom", value=True)
    auto_user_type  = st.checkbox("Déduire type utilisateur si ambigu/absent", value=True)
    strict          = st.toggle("Mode strict (erreurs bloquantes)", value=False)
    civil_fallback  = st.selectbox("Si civilité introuvable →", ["(laisser vide)", "M.", "Mme"], index=0)
    missing_type_mode = st.radio(
        "Si type utilisateur manquant →",
        ["Me demander", "Forcer 1 (Diplômé)", "Forcer 5 (Étudiant)", "Laisser vide"],
        horizontal=False
    )
    out_fmt         = st.radio("Format de sortie", ["CSV", "Excel"], horizontal=True)
    
    # Nouvelle section d'aide
    st.divider()
    st.subheader("💡 Aide rapide")
    
    with st.expander("Formats acceptés"):
        st.write("""
        **Dates** : JJ/MM/AAAA, JJ-MM-AAAA, AAAA-MM-JJ
        
        **Civilité** : M., Mme, Monsieur, Madame
        
        **Booléens** : 1/0, Oui/Non, True/False
        
        **Pays** : FR, France, FRANCE (→ FR)
        
        **Téléphones** : 0123456789, +33123456789
        """)
    
    with st.expander("Mapping automatique"):
        st.write("""
        L'app détecte automatiquement :
        - Les variantes de civilité
        - Les formats de dates
        - Les pays mal orthographiés
        - Les valeurs Oui/Non
        - Les numéros de téléphone
        
        ✅ Validez les suggestions
        ❌ Décochez celles à ignorer
        """)

uploaded = st.file_uploader("Déposez un fichier (.csv / .xlsx)", type=["csv", "xlsx", "xls"])
if not uploaded:
    st.info("En attente d'un fichier…")
    st.stop()

# ---- Lecture + aperçu
try:
    df = read_table(uploaded, uploaded.name)
except Exception as e:
    st.error(f"Lecture impossible : {e}")
    st.stop()

st.success(f"Fichier chargé : **{uploaded.name}** — {df.shape[0]} lignes × {df.shape[1]} colonnes")

tab_map, tab_result, tab_log = st.tabs(["Mapping", "Résultat", "Journal"])

if "res" not in st.session_state: st.session_state.res = None
if "user_type_map" not in st.session_state: st.session_state.user_type_map = {}

# Fonction helper pour appliquer les suggestions automatiques
def apply_automatic_suggestions(df, mapping, session_state):
    """Applique les suggestions automatiques validées par l'utilisateur"""
    df_copy = df.copy()
    
    for template_col, source_col in mapping.items():
        if source_col in df.columns:
            # Pour la civilité, combiner les suggestions de différents niveaux
            if template_col == 'Civilité (M. / Mme)':
                value_mapping = {}
                
                # Récupérer les suggestions haute confiance
                high_key = f"suggestions_{template_col}_high"
                if high_key in session_state:
                    value_mapping.update(session_state[high_key])
                
                # Récupérer les suggestions moyenne confiance
                medium_key = f"suggestions_{template_col}_medium"
                if medium_key in session_state:
                    value_mapping.update(session_state[medium_key])
                
                if value_mapping:
                    df_copy[source_col] = df_copy[source_col].replace(value_mapping)
            else:
                # Traitement normal pour les autres colonnes
                suggestions_key = f"suggestions_{template_col}"
                if suggestions_key in session_state:
                    value_mapping = session_state[suggestions_key]
                    if value_mapping:
                        df_copy[source_col] = df_copy[source_col].replace(value_mapping)
    
    return df_copy

with tab_map:
    st.subheader("1) Mapping des colonnes")
    mapping = auto_map(df)

    # Éditeur de mapping (sans presets)
    template_cols = list(set(list(mapping.keys())))
    choices = ["(aucune)"] + [str(c) for c in df.columns]
    map_df = pd.DataFrame(
        [{"Colonne template": t, "Colonne source": mapping.get(t, "(aucune)")} for t in template_cols]
    ).sort_values("Colonne template")

    edited = st.data_editor(
        map_df,
        column_config={
            "Colonne source": st.column_config.SelectboxColumn("Colonne source", options=choices, width="medium")
        },
        hide_index=True, use_container_width=True
    )
    mapping = {row["Colonne template"]: row["Colonne source"]
               for _, row in edited.iterrows() if row["Colonne source"] != "(aucune)"}

    # ---- NOUVELLE SECTION : Analyse automatique des données ----
    st.divider()
    st.subheader("📊 Analyse automatique des données")

    # Générer le rapport de qualité
    quality_report = generate_data_quality_report(df, mapping)

    # Afficher le score de qualité avec une métrique colorée
    col1, col2, col3 = st.columns(3)
    with col1:
        score = quality_report['quality_score']
        if score >= 80:
            st.success(f"**Score de qualité : {score}/100** ✅")
        elif score >= 60:
            st.warning(f"**Score de qualité : {score}/100** ⚠️")
        else:
            st.error(f"**Score de qualité : {score}/100** ❌")

    with col2:
        st.metric("Colonnes mappées", quality_report['summary']['mapped_columns'])

    with col3:
        st.metric("Colonnes non mappées", quality_report['summary']['unmapped_columns'])

    # Suggestions automatiques pour les valeurs ambiguës
    if quality_report['global_suggestions']:
        st.divider()
        st.subheader("🎯 Suggestions de mapping automatique")
        
        for suggestion_group in quality_report['global_suggestions']:
            col_name = suggestion_group['column']
            st.write(f"**{col_name}**")
            
            suggestions_to_apply = {}
            
            for sugg in suggestion_group['suggestions']:
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"'{sugg['original']}'")
                with col2:
                    st.write("→")
                with col3:
                    apply = st.checkbox(
                        f"Convertir en '{sugg['suggested']}'",
                        value=True,  # Coché par défaut
                        key=f"sugg_{col_name}_{sugg['original']}"
                    )
                    if apply:
                        suggestions_to_apply[sugg['original']] = sugg['suggested']
            
            # Stocker les suggestions à appliquer
            if f"suggestions_{col_name}" not in st.session_state:
                st.session_state[f"suggestions_{col_name}"] = {}
            st.session_state[f"suggestions_{col_name}"] = suggestions_to_apply

    # Détection automatique du format de date
    st.divider()
    st.subheader("📅 Détection du format de dates")

    date_columns = [col for col in mapping.values() if col in df.columns and 'date' in col.lower()]
    if date_columns:
        for col in date_columns:
            sample_dates = df[col].dropna().head(10).tolist()
            if sample_dates:
                detected_format = detect_date_format(sample_dates)
                st.info(f"**{col}** : Format détecté → {detected_format}")
    else:
        st.write("Aucune colonne de date détectée")

    st.divider()
    st.subheader("2) Mapping des valeurs de type utilisateur (si présent)")
    user_type_map = {}
    key_type = "Type d'utilisateur* (Diplômé [1] / Etudiant [5])"
    if key_type in mapping and mapping[key_type] in df.columns:
        col_type = mapping[key_type]
        vals = df[col_type].dropna().astype(str).str.strip().unique().tolist()
        vals = [v for v in vals if v not in ("1","5","")]
        if vals:
            cols = st.columns(min(3, len(vals)))
            for i, v in enumerate(vals):
                with cols[i % len(cols)]:
                    choice = st.selectbox(
                        f"'{v}' →",
                        ["(laisser tel quel)","1 (Diplômé)","5 (Étudiant)","(personnalisé)"],
                        key=f"type_map_{v}"
                    )
                    if choice == "1 (Diplômé)": user_type_map[v] = "1"
                    elif choice == "5 (Étudiant)": user_type_map[v] = "5"
                    elif choice == "(personnalisé)":
                        custom = st.text_input(f"Valeur personnalisée pour '{v}'", key=f"type_map_custom_{v}")
                        if custom: user_type_map[v] = custom
    st.session_state.user_type_map = user_type_map

    st.divider()
    st.subheader("3) Aperçu source (10 lignes)")
    st.dataframe(df.head(10), use_container_width=True)

    run = st.button("Lancer le traitement", type="primary")

# Traduction des choix "type manquant"
default_user_type_when_missing = None
require_user_type_choice = False
if missing_type_mode == "Forcer 1 (Diplômé)":
    default_user_type_when_missing = "1"
elif missing_type_mode == "Forcer 5 (Étudiant)":
    default_user_type_when_missing = "5"
elif missing_type_mode == "Me demander":
    require_user_type_choice = True

if run:
    try:
        # Appliquer d'abord les suggestions automatiques
        df_with_suggestions = apply_automatic_suggestions(df, mapping, st.session_state)
        
        out_df, stats, errors, warnings = process(
            df_with_suggestions,  # Utiliser le df avec les suggestions appliquées
            mapping,
            correct_dates=correct_dates,
            uppercase_names=uppercase_names,
            user_type_map=st.session_state.user_type_map,
            auto_civility=auto_civility,
            auto_user_type=auto_user_type,
            strict=strict,
            civil_fallback=(civil_fallback if civil_fallback in ("M.","Mme") else ""),
            default_user_type_when_missing=default_user_type_when_missing,
            require_user_type_choice=require_user_type_choice
        )
        st.session_state.res = (out_df, stats, errors, warnings)
    except ValueError as e:
        if "TYPE_UTILISATEUR_MANQUANT" in str(e):
            st.warning("Des lignes n'ont pas de **Type utilisateur**. Choisissez un fallback :")
            choice = st.radio("Compléter les types manquants par :", ["1 (Diplômé)", "5 (Étudiant)"], horizontal=True)
            if st.button("Appliquer et relancer"):
                fallback = "1" if choice.startswith("1") else "5"
                # Appliquer d'abord les suggestions automatiques
                df_with_suggestions = apply_automatic_suggestions(df, mapping, st.session_state)
                
                out_df, stats, errors, warnings = process(
                    df_with_suggestions,
                    mapping,
                    correct_dates=correct_dates,
                    uppercase_names=uppercase_names,
                    user_type_map=st.session_state.user_type_map,
                    auto_civility=auto_civility,
                    auto_user_type=auto_user_type,
                    strict=strict,
                    civil_fallback=(civil_fallback if civil_fallback in ("M.","Mme") else ""),
                    default_user_type_when_missing=fallback,
                    require_user_type_choice=False
                )
                st.session_state.res = (out_df, stats, errors, warnings)
        else:
            st.error(str(e))

if st.session_state.res:
    out_df, stats, errors, warnings = st.session_state.res

    with tab_result:
        st.subheader("Résumé")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Lignes traitées", stats["total_rows"])
        c2.metric("Lignes valides",  stats["valid_rows"])
        c3.metric("Champs corrigés", stats["corrected_fields"])
        c4.metric("Erreurs", len(errors))
        c5.metric("Avertissements", len(warnings))

        # ---- NOUVELLES STATISTIQUES DÉTAILLÉES ----
        st.divider()
        st.subheader("📈 Statistiques détaillées")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Taux de complétude par colonne importante
            st.write("**Taux de complétude des champs obligatoires**")
            required_fields = ['Identifiant utilisateurs*', 'Prénom*', 
                             "Nom de naissance / Nom d'état-civil*", 
                             "Type d'utilisateur* (Diplômé [1] / Etudiant [5])"]
            
            for field in required_fields:
                if field in out_df.columns:
                    completeness = (out_df[field].notna() & (out_df[field] != '')).mean() * 100
                    field_display = field[:30] + "..." if len(field) > 30 else field
                    if completeness == 100:
                        st.progress(1.0, f"{field_display} : {completeness:.0f}% ✅")
                    elif completeness >= 80:
                        st.progress(completeness/100, f"{field_display} : {completeness:.0f}% ⚠️")
                    else:
                        st.progress(completeness/100, f"{field_display} : {completeness:.0f}% ❌")
        
        with col2:
            # Répartition des types d'utilisateurs
            st.write("**Répartition des utilisateurs**")
            if "Type d'utilisateur* (Diplômé [1] / Etudiant [5])" in out_df.columns:
                type_col = out_df["Type d'utilisateur* (Diplômé [1] / Etudiant [5])"]
                type_counts = type_col.value_counts()
                
                # Afficher les métriques pour chaque type
                if '1' in type_counts.index:
                    st.metric("Diplômés", type_counts.get('1', 0))
                if '5' in type_counts.index:
                    st.metric("Étudiants", type_counts.get('5', 0))
                
                # Afficher les autres types s'il y en a
                other_types = [t for t in type_counts.index if t not in ['1', '5']]
                if other_types:
                    st.write("**Autres types détectés :**")
                    for type_val in other_types:
                        st.metric(f"Type {type_val}", type_counts[type_val])
            
            # Statistiques sur les emails
            email_cols = [col for col in out_df.columns if 'email' in col.lower()]
            if email_cols:
                st.write("**Emails détectés**")
                total_emails = 0
                for col in email_cols:
                    if col in out_df.columns:
                        valid_emails = (out_df[col].notna() & (out_df[col] != '')).sum()
                        total_emails += valid_emails
                st.metric("Total emails valides", total_emails)

        st.divider()
        st.subheader("Aperçu résultat (30 lignes)")
        st.dataframe(out_df.head(30), use_container_width=True)

        st.divider()
        if out_fmt == "CSV":
            st.download_button("Télécharger CSV", to_csv_bytes(out_df), "import_formate.csv", "text/csv", use_container_width=True)
        else:
            st.download_button("Télécharger Excel", to_excel_bytes(out_df), "import_formate.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with tab_log:
        if warnings:
            with st.expander(f"⚠️ Avertissements ({len(warnings)})", expanded=False):
                # Grouper les avertissements par type
                warning_types = {}
                for w in warnings:
                    if "Civilité déduite" in w:
                        warning_types.setdefault("Civilités déduites", []).append(w)
                    elif "Type manquant" in w:
                        warning_types.setdefault("Types manquants", []).append(w)
                    elif "Email suspect" in w:
                        warning_types.setdefault("Emails suspects", []).append(w)
                    elif "Téléphone suspect" in w:
                        warning_types.setdefault("Téléphones suspects", []).append(w)
                    elif "Date invalide" in w:
                        warning_types.setdefault("Dates invalides", []).append(w)
                    else:
                        warning_types.setdefault("Autres", []).append(w)
                
                # Afficher par catégorie
                for category, msgs in warning_types.items():
                    st.write(f"**{category} ({len(msgs)})**")
                    # Limiter l'affichage si trop de messages
                    if len(msgs) > 10:
                        st.write("\n".join(f"• {m}" for m in msgs[:10]))
                        st.write(f"... et {len(msgs) - 10} autres")
                    else:
                        st.write("\n".join(f"• {m}" for m in msgs))
                    st.write("")  # Espace entre catégories
                    
        if errors:
            with st.expander(f"❌ Erreurs ({len(errors)})", expanded=True):
                # Grouper les erreurs par type
                error_types = {}
                for e in errors:
                    if "Prénom/Nom manquant" in e:
                        error_types.setdefault("Données obligatoires manquantes", []).append(e)
                    elif "TYPE_UTILISATEUR_MANQUANT" in e:
                        error_types.setdefault("Type utilisateur manquant", []).append(e)
                    elif "Date invalide" in e:
                        error_types.setdefault("Dates invalides", []).append(e)
                    elif "Email invalide" in e:
                        error_types.setdefault("Emails invalides", []).append(e)
                    else:
                        error_types.setdefault("Autres erreurs", []).append(e)
                
                # Afficher par catégorie
                for category, msgs in error_types.items():
                    st.write(f"**{category} ({len(msgs)})**")
                    # Limiter l'affichage si trop de messages
                    if len(msgs) > 10:
                        st.write("\n".join(f"• {m}" for m in msgs[:10]))
                        st.write(f"... et {len(msgs) - 10} autres")
                    else:
                        st.write("\n".join(f"• {m}" for m in msgs))
                    st.write("")  # Espace entre catégories
else:
    with tab_result:
        st.info("Lancez le traitement depuis l'onglet **Mapping**.")
    with tab_log:
        st.info("Le journal s'affichera après un traitement.")
