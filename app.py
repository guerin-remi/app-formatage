# app.py
import streamlit as st
from core import read_table, auto_map, process, to_csv_bytes, to_excel_bytes

st.set_page_config(page_title="Formateur d'Import Utilisateur", layout="wide")
st.title("📦 Formateur d'Import Utilisateur (version web)")

st.markdown("Charge un CSV/Excel, je mappe et je formate selon le template, puis tu télécharges le résultat.")

uploaded = st.file_uploader("Dépose ton fichier CSV/XLSX", type=["csv","xlsx","xls"])
col1,col2,col3 = st.columns(3)
with col1:
    correct_dates = st.checkbox("Corriger dates", value=True)
with col2:
    uppercase_names = st.checkbox("Noms en MAJUSCULES", value=True)
with col3:
    out_fmt = st.radio("Format de sortie", ["CSV","Excel"], horizontal=True)

if uploaded:
    st.info(f"Fichier détecté: **{uploaded.name}**")
    try:
        df = read_table(uploaded, uploaded.name)
    except Exception as e:
        st.error(f"Impossible de lire le fichier: {e}")
        st.stop()

    st.write("Aperçu (10 premières lignes) :")
    st.dataframe(df.head(10))

    # Mapping auto + édition légère
    mapping = auto_map(df)
    with st.expander("Voir/éditer le mapping détecté"):
        st.caption("Colonne source → Colonne template")
        for tcol in mapping.copy():
            mapping[tcol] = st.selectbox(
                f"{tcol}", 
                options=["(aucune)"] + list(df.columns), 
                index=(list(df.columns).index(mapping[tcol]) + 1) if mapping[tcol] in df.columns else 0
            )
        # nettoyer "(aucune)"
        mapping = {k:v for k,v in mapping.items() if v and v!="(aucune)"}

    # Détection types utilisateurs (optionnel)
    user_type_map = {}
    type_col_key = "Type d'utilisateur* (Diplômé [1] / Etudiant [5])"
    if type_col_key in mapping:
        uniq = (
            df[mapping[type_col_key]]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )
        uniq = [u for u in uniq if u not in ['1','5','']]
        if uniq:
            st.subheader("Mapping des **types d’utilisateurs**")
            st.caption("Associe chaque valeur au code souhaité (1 = Diplômé, 5 = Étudiant) ou laisse tel quel.")
            for u in uniq:
                choice = st.selectbox(
                    f"'{u}' →",
                    options=['(conserver)','1 (Diplômé)','5 (Étudiant)','(valeur personnalisée)'],
                    key=f"type_{u}"
                )
                if choice == '1 (Diplômé)': user_type_map[u]='1'
                elif choice == '5 (Étudiant)': user_type_map[u]='5'
                elif choice == '(valeur personnalisée)':
                    custom = st.text_input(f"Valeur perso pour '{u}'", key=f"custom_{u}")
                    if custom: user_type_map[u]=custom

    if st.button("🚀 Traiter le fichier", type="primary"):
        with st.spinner("Traitement en cours..."):
            out_df, stats, errors, warnings = process(
                df, mapping, correct_dates=correct_dates, uppercase_names=uppercase_names, user_type_map=user_type_map
            )
        st.success("Terminé ✅")
        st.write(f"**Lignes traitées**: {stats['total_rows']}  •  **Valides**: {stats['valid_rows']}  •  **Champs corrigés**: {stats['corrected_fields']}")
        if warnings:
            with st.expander(f"⚠️ Avertissements ({len(warnings)})"):
                st.write("\n".join(f"• {w}" for w in warnings))
        if errors:
            with st.expander(f"❌ Erreurs ({len(errors)})"):
                st.write("\n".join(f"• {e}" for e in errors))

        st.write("Aperçu du fichier formaté :")
        st.dataframe(out_df.head(30))

        if out_fmt == "CSV":
            st.download_button("⬇️ Télécharger CSV", data=to_csv_bytes(out_df), file_name="import_formate.csv", mime="text/csv")
        else:
            st.download_button("⬇️ Télécharger Excel", data=to_excel_bytes(out_df), file_name="import_formate.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
