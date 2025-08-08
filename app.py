# app.py
import streamlit as st
import pandas as pd
from core import read_table, auto_map, process, to_csv_bytes, to_excel_bytes

st.set_page_config(
    page_title="Formateur d'Import Utilisateur",
    page_icon="📦",
    layout="wide"
)

# --- CSS rapide (sans lib) ---
st.markdown("""
<style>
/* Police système propre */
html, body, [class*="css"]  { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial; }

/* Cards */
.card { border: 1px solid #E5E7EB; background: #FFF; border-radius: 14px; padding: 18px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
.card-muted { border: 1px dashed #E5E7EB; background: #FAFAFA; }

/* KPI tiles */
.kpi { text-align:center; padding: 14px 8px; border:1px solid #E5E7EB; border-radius:12px; }
.kpi .label { color:#6B7280; font-size:13px; }
.kpi .value { font-weight:700; font-size:22px; margin-top:4px; }

/* Buttons row */
.btn-row { display:flex; gap:10px; flex-wrap: wrap; }
.btn-row > div { flex: 0 0 auto; }

/* Hide Streamlit default footer/menu for plus clean */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("### 📦 Formateur d’Import Utilisateur")
st.caption("Upload → mapping → formatage → téléchargement. Simple, propre, efficace.")

# --- Sidebar: options ---
with st.sidebar:
    st.markdown("#### ⚙️ Options")
    correct_dates = st.checkbox("Corriger automatiquement les dates", value=True)
    uppercase_names = st.checkbox("Noms en MAJUSCULES", value=True)
    out_fmt = st.radio("Format de sortie", ["CSV","Excel"], horizontal=True)
    st.divider()
    st.caption("Astuce : vous pouvez d’abord mapper vos colonnes dans l’onglet **Aperçu**.")

# --- Upload zone ---
with st.container():
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown('<div class="card card-muted">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Déposez un fichier CSV / XLSX", type=["csv","xlsx","xls"])
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Guide rapide**")
        st.markdown("- Utilisez un CSV ou un Excel (XLSX).\n- Vérifiez le **mapping** proposé.\n- Téléchargez le **fichier formaté**.")
        st.markdown("</div>", unsafe_allow_html=True)

if not uploaded:
    st.stop()

# --- Lecture + aperçu ---
try:
    df = read_table(uploaded, uploaded.name)
except Exception as e:
    st.error(f"Impossible de lire le fichier : {e}")
    st.stop()

st.success(f"Fichier chargé : **{uploaded.name}** · {df.shape[0]} lignes × {df.shape[1]} colonnes")

# --- Tabs ---
tab_preview, tab_report, tab_log = st.tabs(["🔎 Aperçu & Mapping", "📈 Rapport", "📝 Journal"])

# --- Mapping détecté + éditable ---
with tab_preview:
    st.markdown("#### 🔧 Mapping des colonnes")
    mapping = auto_map(df)

    # Editeur de mapping (une ligne = une colonne template ; select sur colonnes source)
    template_cols = list(mapping.keys())  # seulement celles détectées + clés importantes
    all_sources = ["(aucune)"] + list(map(str, df.columns))

    map_data = []
    for tcol in template_cols:
        map_data.append({"Colonne template": tcol, "Colonne source": mapping.get(tcol, "(aucune)")})

    map_df = pd.DataFrame(map_data)

    edited = st.data_editor(
        map_df,
        column_config={
            "Colonne source": st.column_config.SelectboxColumn(
                "Colonne source", options=all_sources, width="medium"
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # Nettoyage du mapping après édition
    mapping = {row["Colonne template"]: row["Colonne source"] for _, row in edited.iterrows() if row["Colonne source"] != "(aucune)"}

    st.markdown("#### 👀 Aperçu du fichier source (10 premières lignes)")
    st.dataframe(df.head(10), use_container_width=True)

    st.markdown("#### ▶️ Traitement")
    run = st.button("🚀 Lancer le traitement", type="primary")

# --- Traitement ---
if "last_result" not in st.session_state:
    st.session_state.last_result = None

if tab_preview and 'run' in locals() and run:
    with st.status("Traitement en cours…", expanded=True) as s:
        st.write("1/3 — Application du mapping…")
        st.write("2/3 — Formatage des champs…")
        out_df, stats, errors, warnings = process(
            df, mapping, correct_dates=correct_dates, uppercase_names=uppercase_names, user_type_map=None
        )
        st.write("3/3 — Génération du fichier de sortie…")
        st.session_state.last_result = (out_df, stats, errors, warnings)
        s.update(label="Terminé ✅", state="complete")

# --- Rapport & Téléchargement ---
if st.session_state.last_result:
    out_df, stats, errors, warnings = st.session_state.last_result

    with tab_report:
        st.markdown("#### 📈 Résumé du traitement")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.markdown(f'<div class="kpi"><div class="label">Lignes traitées</div><div class="value">{stats["total_rows"]}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><div class="label">Lignes valides</div><div class="value">{stats["valid_rows"]}</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><div class="label">Champs corrigés</div><div class="value">{stats["corrected_fields"]}</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi"><div class="label">Erreurs</div><div class="value">{len(errors)}</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="kpi"><div class="label">Avertissements</div><div class="value">{len(warnings)}</div></div>', unsafe_allow_html=True)

        st.markdown("#### 🧾 Aperçu du fichier formaté (30 premières lignes)")
        st.dataframe(out_df.head(30), use_container_width=True)

        st.markdown("#### ⬇️ Télécharger")
        cdl1, cdl2 = st.columns([1,1])
        if out_fmt == "CSV":
            cdl1.download_button(
                "Télécharger CSV",
                data=to_csv_bytes(out_df),
                file_name="import_formate.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            cdl1.download_button(
                "Télécharger Excel",
                data=to_excel_bytes(out_df),
                file_name="import_formate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        cdl2.button("Recommencer", on_click=lambda: st.session_state.pop("last_result", None), use_container_width=True)

    with tab_log:
        st.markdown("#### 📝 Journal")
        if warnings:
            with st.expander(f"⚠️ Avertissements ({len(warnings)})", expanded=False):
                st.write("\n".join(f"• {w}" for w in warnings))
        if errors:
            with st.expander(f"❌ Erreurs ({len(errors)})", expanded=True):
                st.write("\n".join(f"• {e}" for e in errors))
else:
    with tab_report:
        st.info("Lancez d’abord le traitement dans l’onglet **Aperçu & Mapping**.")
    with tab_log:
        st.info("Le journal s’affichera après un premier traitement.")
