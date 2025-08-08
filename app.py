import streamlit as st
import pandas as pd
from core import read_table, auto_map, process, to_csv_bytes, to_excel_bytes

st.set_page_config(page_title="Import Utilisateur", page_icon="📦", layout="wide")

# ---- En-tête simple
st.title("📦 Import Utilisateur")
st.caption("Uploader → Mapper → Formater → Télécharger")

# ---- Sidebar : options essentielles
with st.sidebar:
    st.header("Options")
    correct_dates   = st.checkbox("Corriger les dates", value=True)
    uppercase_names = st.checkbox("Noms en MAJUSCULES", value=True)
    out_fmt         = st.radio("Format de sortie", ["CSV", "Excel"], horizontal=True)
    st.divider()
    st.caption("Conseil : vérifiez le mapping avant de lancer.")

# ---- Zone d’upload
uploaded = st.file_uploader("Déposez un fichier (.csv / .xlsx)", type=["csv", "xlsx", "xls"])
if not uploaded:
    st.info("En attente d’un fichier…")
    st.stop()

# ---- Lecture + aperçu court
try:
    df = read_table(uploaded, uploaded.name)
except Exception as e:
    st.error(f"Lecture impossible : {e}")
    st.stop()

st.success(f"Fichier chargé : **{uploaded.name}** — {df.shape[0]} lignes × {df.shape[1]} colonnes")

# ---- Tabs sobres
tab_map, tab_result, tab_log = st.tabs(["Mapping", "Résultat", "Journal"])

with tab_map:
    st.subheader("Mapping des colonnes")
    mapping = auto_map(df)

    # Éditeur compact : Colonne template ↔ Colonne source
    template_cols = list(mapping.keys())
    choices = ["(aucune)"] + [str(c) for c in df.columns]
    map_df = pd.DataFrame(
        [{"Colonne template": t, "Colonne source": mapping.get(t, "(aucune)")} for t in template_cols]
    )
    edited = st.data_editor(
        map_df,
        column_config={
            "Colonne source": st.column_config.SelectboxColumn("Colonne source", options=choices, width="medium")
        },
        hide_index=True,
        use_container_width=True
    )
    mapping = {row["Colonne template"]: row["Colonne source"]
               for _, row in edited.iterrows() if row["Colonne source"] != "(aucune)"}

    st.divider()
    st.subheader("Aperçu source (10 lignes)")
    st.dataframe(df.head(10), use_container_width=True)

    run = st.button("Lancer le traitement", type="primary")

# ---- Traitement (sans fioritures)
if "res" not in st.session_state:
    st.session_state.res = None

if run:
    with st.spinner("Traitement…"):
        out_df, stats, errors, warnings = process(
            df, mapping, correct_dates=correct_dates, uppercase_names=uppercase_names, user_type_map=None
        )
    st.session_state.res = (out_df, stats, errors, warnings)

if st.session_state.res:
    out_df, stats, errors, warnings = st.session_state.res

    with tab_result:
        st.subheader("Résumé")
        c1, c2, c3 = st.columns(3)
        c1.metric("Lignes traitées", stats["total_rows"])
        c2.metric("Lignes valides",  stats["valid_rows"])
        c3.metric("Champs corrigés", stats["corrected_fields"])

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
