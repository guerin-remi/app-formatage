# app.py
import streamlit as st
import pandas as pd
from core import (
    read_table, auto_map, process,
    to_csv_bytes, to_excel_bytes, report_html_bytes,
    mapping_to_json, mapping_from_json
)

st.set_page_config(page_title="Import Utilisateur", page_icon="📦", layout="wide")
st.title("📦 Import Utilisateur")
st.caption("Uploader → Mapper → Formater → Télécharger")

# ---- Sidebar : options
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
    st.divider()
    st.caption("Astuce : enregistrez un preset de mapping pour les prochains imports.")

uploaded = st.file_uploader("Déposez un fichier (.csv / .xlsx)", type=["csv", "xlsx", "xls"])
if not uploaded:
    st.info("En attente d’un fichier…")
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

with tab_map:
    st.subheader("1) Mapping des colonnes")
    mapping = auto_map(df)

    c1, c2 = st.columns([1,1])
    with c1:
        preset_file = st.file_uploader("Charger un preset (.json)", type=["json"], key="preset_up")
        if preset_file:
            try:
                preset_map = mapping_from_json(preset_file.read())
                mapping = {k:v for k,v in preset_map.items() if v in df.columns}
                st.success("Preset chargé.")
            except Exception as e:
                st.error(f"Preset invalide : {e}")
    with c2:
        st.download_button(
            "Enregistrer le preset courant",
            data=mapping_to_json(mapping),
            file_name="mapping_preset.json",
            mime="application/json",
            use_container_width=True
        )

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

    with st.expander("Diagnostic rapide (pré-traitement)"):
        nb_civ_vide = 0
        if "Civilité (M. / Mme)" in mapping and mapping["Civilité (M. / Mme)"] in df.columns:
            civ_col = df[mapping["Civilité (M. / Mme)"]].astype(str).str.strip()
            nb_civ_vide = int((civ_col == "").sum())
        st.write(f"• Civilité manquante (brut) : **{nb_civ_vide}**")
        if key_type in mapping and mapping[key_type] in df.columns:
            tcol = df[mapping[key_type]].astype(str).str.strip()
            nb_type_vide = int((tcol == "").sum())
            st.write(f"• Type utilisateur manquant (brut) : **{nb_type_vide}**")

    run = st.button("Lancer le traitement", type="primary")

# Traduction des choix “type manquant”
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
        out_df, stats, errors, warnings = process(
            df, mapping,
            correct_dates=correct_dates, uppercase_names=uppercase_names,
            user_type_map=st.session_state.user_type_map,
            auto_civility=auto_civility, auto_user_type=auto_user_type,
            strict=strict,
            civil_fallback=(civil_fallback if civil_fallback in ("M.","Mme") else ""),
            default_user_type_when_missing=default_user_type_when_missing,
            require_user_type_choice=require_user_type_choice
        )
        st.session_state.res = (out_df, stats, errors, warnings)
    except ValueError as e:
        if "TYPE_UTILISATEUR_MANQUANT" in str(e):
            st.warning("Des lignes n’ont pas de **Type utilisateur**. Choisissez un fallback :")
            choice = st.radio("Compléter les types manquants par :", ["1 (Diplômé)", "5 (Étudiant)"], horizontal=True)
            if st.button("Appliquer et relancer"):
                fallback = "1" if choice.startswith("1") else "5"
                out_df, stats, errors, warnings = process(
                    df, mapping,
                    correct_dates=correct_dates, uppercase_names=uppercase_names,
                    user_type_map=st.session_state.user_type_map,
                    auto_civility=auto_civility, auto_user_type=auto_user_type,
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

        st.divider()
        st.subheader("Aperçu résultat (30 lignes)")
        st.dataframe(out_df.head(30), use_container_width=True)

        st.divider()
        cdl1, cdl2, cdl3 = st.columns([1,1,1])
        if out_fmt == "CSV":
            cdl1.download_button("Télécharger CSV", to_csv_bytes(out_df), "import_formate.csv", "text/csv", use_container_width=True)
        else:
            cdl1.download_button("Télécharger Excel", to_excel_bytes(out_df), "import_formate.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        cdl2.download_button("Télécharger le rapport HTML",
                             report_html_bytes(out_df, stats, errors, warnings),
                             "rapport_import.html", "text/html", use_container_width=True)
        cdl3.button("Réinitialiser", on_click=lambda: st.session_state.pop("res", None), use_container_width=True)

    with tab_log:
        if warnings:
            with st.expander(f"Avertissements ({len(warnings)})"):
                st.write("\n".join(f"• {w}" for w in warnings))
        if errors:
            with st.expander(f"Erreurs ({len(errors)})", expanded=True):
                st.write("\n".join(f"• {e}" for e in errors))
else:
    with tab_result:
        st.info("Lancez le traitement depuis l’onglet **Mapping**.")
    with tab_log:
        st.info("Le journal s’affichera après un traitement.")
