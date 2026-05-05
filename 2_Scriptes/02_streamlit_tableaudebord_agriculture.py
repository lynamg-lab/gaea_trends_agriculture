#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tableau de bord Streamlit — Modèle réutilisable
================================================
Structure : Séries temporelles | Composition (camembert) | Carte choroplèthe

Ce fichier est conçu pour être réutilisé sur n'importe quel domaine.
Pour l'adapter à votre projet, modifiez UNIQUEMENT la section
"CONFIGURATION DU PROJET" ci-dessous — le reste du script n'a pas
besoin d'être touché.

Lancer l'application :
    py -m streamlit run .\2_Scriptes\streamlit_dashboard_template.py
"""

# ==============================================================================
# IMPORTS — bibliothèques externes
# ==============================================================================
# Ces trois lignes chargent les outils dont on a besoin :
#   streamlit → construit l'interface web (widgets, onglets, graphiques…)
#   pandas    → manipule les données tabulaires (CSV, filtres, agrégations…)
#   altair    → crée des graphiques déclaratifs (courbes, camemberts, barres…)
#   pathlib   → gère les chemins de fichiers de façon cross-plateforme

from __future__ import annotations
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

# Plotly est optionnel : utilisé uniquement pour la carte choroplèthe.
# Le bloc try/except évite que l'application plante si Plotly n'est pas installé.
# Si absent, l'onglet Carte affichera un message d'installation à la place.
try:
    import plotly.express as px
    HAS_PLOTLY = True
    # Palette de couleurs pour la carte (du vert clair au rouge foncé)
    CORP_SCALE = [
        [0.00, "#ABDDA4"], [0.11, "#66C2A5"], [0.22, "#3288BD"],
        [0.33, "#5E4FA2"], [0.44, "#FEE08B"], [0.56, "#FDAE61"],
        [0.67, "#F46D43"], [0.78, "#D53E4F"], [1.00, "#9E0142"],
    ]
except Exception:
    HAS_PLOTLY = False


# ==============================================================================
# ██████████████████████████████████████████████████████████████████████████████
# CONFIGURATION DU PROJET — MODIFIEZ UNIQUEMENT CETTE SECTION
# ██████████████████████████████████████████████████████████████████████████████
# ==============================================================================
#
# Deux exemples de configuration sont fournis ci-dessous :
#   • THÈME A : Émissions du cheptel (actif par défaut)
#   • THÈME B : Énergies renouvelables (commenté — décommentez pour l'utiliser)
#
# Pour passer d'un thème à l'autre :
#   1. Mettez en commentaire (ajoutez # devant) le bloc du thème actif
#   2. Décommentez (retirez les #) le bloc du nouveau thème
# ------------------------------------------------------------------------------


# ──────────────────────────────────────────────────────────────────────────────
# THÈME A — Émissions du cheptel (actif)
# ──────────────────────────────────────────────────────────────────────────────

# Titre affiché dans l'onglet du navigateur et en haut de la page
PAGE_TITLE  = "Tableau de bord Émissions — Totaux & Stocks"
APP_TITLE   = "Tableau de bord Émissions — Émissions du cheptel & Stocks"

# Chemin absolu vers votre fichier CSV préparé.
# Remplacez par le chemin de votre propre fichier.
CSV_PATH = r"C:\Users\lynam\Documents\01_steamlit_gaea_template_tutorial\1_Donnees\Emissions_livestock_E_Europe_PROPRE_indicateur.csv"

# Colonnes de votre CSV — noms exacts tels qu'ils apparaissent dans le fichier.
COL_COUNTRY  = "Area 3"           # Colonne contenant les noms de pays/zones
COL_ITEM     = "Categorie_animal" # Colonne contenant les catégories d'items (ex. type d'animal, source d'énergie…)
COL_YEAR     = "Annee"            # Colonne contenant les années (entiers)
COL_METRIC   = "Indicateur"       # Colonne contenant le nom de l'indicateur mesuré
COL_VALUE    = "Valeur"           # Colonne contenant les valeurs numériques
COL_KIND     = "categorie_type"   # Colonne indiquant le niveau de détail : 'All' | 'aggregated' | 'atomic'

# Indicateurs disponibles dans votre CSV (valeurs exactes de la colonne COL_METRIC).
# Le premier de la liste sera sélectionné par défaut dans les menus.
INDICATORS = [
    "Emissions totales du cheptel (CO2 eq.)",
    "Effectifs",
]

# Indicateur utilisé dans l'onglet Composition (camembert) et Carte.
# Doit correspondre à l'une des valeurs de INDICATORS ci-dessus.
INDICATOR_PIE = "Emissions totales du cheptel (CO2 eq.)"
INDICATOR_MAP = "Emissions totales du cheptel (CO2 eq.)"

# Étiquettes d'unité affichées sur les axes Y des graphiques.
# Clé = valeur exacte de INDICATORS, valeur = texte de l'axe.
METRIC_LABELS = {
    "Emissions totales du cheptel (CO2 eq.)": "Total (kt CO₂e)",
    "Effectifs":                               "Effectifs (têtes)",
}

# Régions géographiques disponibles dans vos données.
# REGION_OPTIONS : noms affichés dans les menus.
# FLAG_MAP       : pour chaque région, la colonne booléenne du CSV
#                  qui vaut True si le pays appartient à cette région.
REGION_OPTIONS = ["EU", "EU/EEA+UK"]
FLAG_MAP       = {
    "EU":        "region_EU",
    "EU/EEA+UK": "region_EUEEAUK",
}

# Colonnes de région supplémentaires requises dans le CSV (utilisées dans load_prepared).
REGION_COLS = ["region_EU", "region_EUEEAUK"]

# Plage d'années affichée par défaut dans le curseur (sera ajustée selon les données).
DEFAULT_START = 1990
DEFAULT_END   = 2022

# Corrections de noms de pays pour Plotly (carte choroplèthe).
# Plotly attend les noms complets en anglais. Ajoutez ici les cas particuliers de votre CSV.
NAME_FIX = {
    "UK":     "United Kingdom",
    "Russia": "Russian Federation",
}

# Région utilisée pour filtrer la carte (valeur exacte de REGION_OPTIONS).
MAP_REGION = "EU"

# Palette de couleurs de l'interface (codes hexadécimaux).
CORP = {
    "bg":     "#f5f0e6",  # fond de l'application
    "panel":  "#e7dfcf",  # fond de la barre latérale
    "text":   "#2e2b26",  # texte principal
    "accent": "#6b8e23",  # boutons et onglet actif
}


# ──────────────────────────────────────────────────────────────────────────────
# THÈME B — Énergies renouvelables (commenté — décommentez pour l'activer)
# ──────────────────────────────────────────────────────────────────────────────
# Pour utiliser ce thème, supprimez le # au début de chaque ligne ci-dessous
# et ajoutez # devant toutes les lignes du Thème A.

# PAGE_TITLE  = "Tableau de bord Énergie — Production renouvelable"
# APP_TITLE   = "Tableau de bord Énergie — Production renouvelable par pays"
# CSV_PATH    = r"C:\chemin\vers\votre\fichier_energie.csv"
#
# COL_COUNTRY  = "Country"          # ex. "France", "Germany"…
# COL_ITEM     = "Source"           # ex. "Solaire", "Éolien", "Hydraulique"…
# COL_YEAR     = "Year"
# COL_METRIC   = "Indicator"
# COL_VALUE    = "Value"
# COL_KIND     = "detail_level"     # ex. 'All' | 'aggregated' | 'atomic'
#
# INDICATORS = [
#     "Production d'électricité (GWh)",
#     "Capacité installée (MW)",
# ]
# INDICATOR_PIE = "Production d'électricité (GWh)"
# INDICATOR_MAP = "Production d'électricité (GWh)"
#
# METRIC_LABELS = {
#     "Production d'électricité (GWh)": "Production (GWh)",
#     "Capacité installée (MW)":         "Capacité (MW)",
# }
#
# REGION_OPTIONS = ["Europe", "OCDE"]
# FLAG_MAP       = {"Europe": "region_europe", "OCDE": "region_ocde"}
# REGION_COLS    = ["region_europe", "region_ocde"]
#
# DEFAULT_START = 2000
# DEFAULT_END   = 2023
#
# NAME_FIX = {}  # Pas de corrections nécessaires si les noms sont déjà en anglais
# MAP_REGION = "Europe"
#
# CORP = {
#     "bg":     "#e8f4f8",  # bleu très clair
#     "panel":  "#cce5f0",
#     "text":   "#1a3a4a",
#     "accent": "#0077b6",  # bleu vif
# }


# ==============================================================================
# ██████████████████████████████████████████████████████████████████████████████
# FIN DE LA CONFIGURATION — ne pas modifier en dessous sauf cas avancés
# ██████████████████████████████████████████████████████████████████████████████
# ==============================================================================


# ==============================================================================
# CONFIGURATION DE LA PAGE
# ==============================================================================
# st.set_page_config doit toujours être le premier appel Streamlit du script.
# Elle fixe le titre de l'onglet du navigateur et active la mise en page large.

st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(APP_TITLE)


# ==============================================================================
# THÈME VISUEL — CSS et couleurs des graphiques
# ==============================================================================
# Streamlit permet d'injecter du CSS pour personnaliser l'apparence.
# Les couleurs viennent du dictionnaire CORP défini dans la configuration.
# Les doubles accolades {{ }} dans le CSS sont obligatoires dans les f-strings
# (les simples { } sont réservées aux variables Python).

st.markdown(f"""
<style>
.stApp {{ background-color: {CORP["bg"]}; color: {CORP["text"]}; }}
section[data-testid="stSidebar"] > div:first-child {{ background-color: {CORP["panel"]} !important; }}
.stButton button, .stDownloadButton button {{
    background-color: {CORP["accent"]} !important;
    color: white !important;
    border: 0 !important;
    border-radius: 10px !important;
}}
.stButton button:hover, .stDownloadButton button:hover {{ filter: brightness(0.95); }}
.stTabs [role="tablist"] button[role="tab"] {{ color: {CORP["text"]}; }}
.stTabs [role="tablist"] button[aria-selected="true"] {{ border-bottom: 3px solid {CORP["accent"]}; }}
.block-container {{ background: transparent; }}
label, .stSelectbox label, .stRadio label {{ color: {CORP["text"]} !important; }}
</style>
""", unsafe_allow_html=True)

# Palette de couleurs pour distinguer les séries dans les graphiques Altair.
# Répétée x4 pour avoir suffisamment de couleurs même avec beaucoup de catégories.
ALT_CATEGORY = [
    "#9E0142", "#D53E4F", "#F46D43", "#FDAE61", "#FEE08B",
    "#E6F598", "#ABDDA4", "#66C2A5", "#3288BD", "#5E4FA2",
] * 4

# Enregistrement du thème Altair : applique les couleurs CORP à tous les graphiques.
def _corp_altair_theme():
    return {
        "config": {
            "range":  {"category": ALT_CATEGORY},
            "view":   {"stroke": "transparent"},
            "axis":   {"labelColor": CORP["text"], "titleColor": CORP["text"]},
            "legend": {"labelColor": CORP["text"], "titleColor": CORP["text"]},
            "title":  {"color": CORP["text"]},
            "mark":   {"strokeWidth": 2},
        }
    }

alt.themes.register("corp", _corp_altair_theme)
alt.themes.enable("corp")


# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def metric_unit_label(metric: str) -> str:
    """Retourne l'étiquette d'axe Y pour un indicateur donné (défini dans METRIC_LABELS)."""
    return METRIC_LABELS.get(metric, metric)


def normalize_kind_value(v: str) -> str:
    """
    Normalise les valeurs de la colonne COL_KIND en trois catégories standard.
    Insensible à la casse et aux espaces : "All Animals" → "All", etc.
    """
    s = str(v).strip().lower()
    if s in {"all", "all animals", "all_animals"}:
        return "All"
    if s in {"aggregated", "aggregate"}:
        return "aggregated"
    return "atomic"


# ==============================================================================
# CHARGEMENT ET VALIDATION DES DONNÉES
# ==============================================================================
# @st.cache_data met le résultat en cache : le CSV n'est lu qu'une seule fois,
# même si l'utilisateur interagit avec des widgets. Cela évite les rechargements
# lents à chaque clic.

@st.cache_data
def load_prepared(path: Path) -> pd.DataFrame:
    """
    Charge le CSV et vérifie que les colonnes requises sont présentes.
    Retourne un DataFrame filtré sur les indicateurs définis dans INDICATORS.

    Colonnes requises (définies dans la section Configuration) :
        COL_COUNTRY, COL_ITEM, COL_YEAR, COL_METRIC, COL_VALUE, COL_KIND
        + toutes les colonnes listées dans REGION_COLS
    """
    df = pd.read_csv(path)

    # Vérification que toutes les colonnes nécessaires existent dans le fichier
    need = {COL_COUNTRY, COL_ITEM, COL_YEAR, COL_METRIC, COL_VALUE, COL_KIND} | set(REGION_COLS)
    miss = need.difference(df.columns)
    if miss:
        st.error(f"Colonnes manquantes dans le CSV : {', '.join(sorted(miss))}")
        st.stop()

    # On ne garde que les lignes correspondant aux indicateurs déclarés dans INDICATORS
    df = df[df[COL_METRIC].isin(INDICATORS)].copy()
    df[COL_KIND] = df[COL_KIND].astype(str)
    return df


# Chargement des données : depuis le chemin par défaut, ou via upload si introuvable
path = Path(CSV_PATH)

if not path.exists():
    # Le fichier n'a pas été trouvé à l'emplacement indiqué.
    # On propose à l'utilisateur de le charger directement depuis le navigateur.
    st.warning(f"Fichier CSV introuvable :\n{path}\nImportez-le ci-dessous ou modifiez CSV_PATH.")
    uploaded = st.file_uploader("Importer le CSV préparé", type=["csv"])
    if uploaded is None:
        st.stop()
    df = pd.read_csv(uploaded)
    df = df[df[COL_METRIC].isin(INDICATORS)].copy()
else:
    df = load_prepared(path)

# Bornes temporelles réelles des données (pour le slider d'années)
year_min = int(df[COL_YEAR].min())
year_max = int(df[COL_YEAR].max())
DEFAULT_START = max(DEFAULT_START, year_min)
DEFAULT_END   = min(DEFAULT_END,   year_max)


# ==============================================================================
# STRUCTURE EN ONGLETS
# ==============================================================================
# st.tabs crée les onglets cliquables en haut de la page.
# Chaque onglet est utilisé dans un bloc "with tab_xxx:" plus bas.

tab_ts, tab_pie, tab_map = st.tabs(["Séries temporelles", "Composition", "Carte"])


# ==============================================================================
# ONGLET 1 — SÉRIES TEMPORELLES
# ==============================================================================
# Affiche l'évolution d'un indicateur dans le temps, par pays ou par région.
# Les filtres (indicateur, période, niveau de détail, pays) sont dans la barre latérale.

with tab_ts:

    # --- Barre latérale : indicateur et plage d'années ---
    # st.sidebar place les widgets dans le panneau latéral gauche.
    # st.selectbox crée un menu déroulant ; st.slider un curseur double.
    with st.sidebar:
        st.header("Indicateur & période")
        metric = st.selectbox("Indicateur", INDICATORS, index=0)
        year_range = st.slider(
            "Plage d'années",
            min_value=year_min, max_value=year_max,
            value=(DEFAULT_START, DEFAULT_END), step=1,
        )

    # --- Niveau de détail : Tous / Agrégé / Atomique ---
    # Les données peuvent contenir plusieurs niveaux de granularité.
    # On détecte quels niveaux sont présents et on laisse l'utilisateur choisir.
    kinds_present = sorted({normalize_kind_value(v) for v in df[COL_KIND].unique()})
    kind_label_to_value = {"Tous": "All", "Agrégé": "aggregated", "Atomique": "atomic"}
    default_kind_label = (
        "Tous" if "All" in kinds_present
        else ("Agrégé" if "aggregated" in kinds_present else "Atomique")
    )

    with st.sidebar:
        st.header("Niveau de détail")
        kind_label = st.radio(
            "Choisir un niveau",
            ["Tous", "Agrégé", "Atomique"],
            index=["Tous", "Agrégé", "Atomique"].index(default_kind_label),
        )

    kind_value = kind_label_to_value[kind_label]

    # Filtrage des données sur le niveau de détail choisi
    subset    = df[df[COL_KIND].apply(lambda x: normalize_kind_value(x) == kind_value)]
    items_all = sorted(subset[COL_ITEM].dropna().unique().tolist())

    # --- Sélection des items (catégories d'animaux, sources d'énergie, etc.) ---
    # st.session_state mémorise la sélection entre les interactions utilisateur.
    # Sans cela, Streamlit réinitialiserait la sélection à chaque clic.
    ITEMS_KEY = "items_template_multiselect"
    if ITEMS_KEY not in st.session_state:
        st.session_state[ITEMS_KEY] = items_all[:1] if kind_value == "All" else items_all
    if st.session_state.get("last_kind_value") != kind_value:
        # Réinitialise la sélection quand le niveau de détail change
        st.session_state[ITEMS_KEY] = items_all[:1] if kind_value == "All" else items_all
    st.session_state["last_kind_value"] = kind_value

    # S'assure que les items mémorisés existent toujours dans la liste actuelle
    valid_defaults = [d for d in st.session_state[ITEMS_KEY] if d in items_all]
    if not valid_defaults:
        valid_defaults = items_all[:1] if kind_value == "All" else items_all
    st.session_state[ITEMS_KEY] = valid_defaults

    # Boutons de sélection rapide + liste multi-sélection
    st.write(f"**Items — {kind_label}**")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Tout sélectionner"):
            st.session_state[ITEMS_KEY] = items_all[:1] if kind_value == "All" else items_all
    with c2:
        if st.button("Effacer"):
            st.session_state[ITEMS_KEY] = []
    with c3:
        if kind_value == "All":
            st.caption("'All' est exclusif par conception")

    # st.multiselect affiche une liste déroulante avec sélection multiple.
    # max_selections=1 pour "All" car ce niveau ne contient qu'une seule valeur totale.
    items = st.multiselect(
        "",
        options=items_all,
        key=ITEMS_KEY,
        max_selections=(1 if kind_value == "All" else None),
    )
    if not items:
        st.info("Sélectionnez au moins un item.")
        st.stop()

    # --- Mode d'affichage : pays individuels ou total régional ---
    with st.sidebar:
        st.header("Mode d'affichage")
        show_region   = st.checkbox("Afficher le total régional plutôt que les pays", value=False)
        region_choice = st.selectbox("Région", REGION_OPTIONS, index=0, disabled=not show_region)

    # --- Filtrage des données selon tous les critères sélectionnés ---
    base = df[
        (df[COL_METRIC] == metric) &
        (df[COL_YEAR]   >= year_range[0]) &
        (df[COL_YEAR]   <= year_range[1])
    ]
    base = base[base[COL_KIND].apply(lambda x: normalize_kind_value(x) == kind_value)]
    base = base[base[COL_ITEM].isin(items)]

    if base.empty:
        st.info("Aucune donnée pour ces filtres.")
        st.stop()

    # --- Calcul des séries à tracer ---
    if show_region:
        # Mode région : on additionne tous les pays de la région par année
        flag_col = FLAG_MAP[region_choice]
        sub = base[
            base[flag_col] &
            ~base[COL_COUNTRY].str.contains("(group total)", case=False, na=False)
        ].copy()
        if sub.empty:
            st.info(f"Aucun pays marqué pour la région : {region_choice}.")
            st.stop()
        totals = (
            sub.groupby([COL_YEAR], as_index=False)[COL_VALUE].sum()
               .assign(**{COL_COUNTRY: region_choice})[[COL_COUNTRY, COL_YEAR, COL_VALUE]]
               .rename(columns={COL_VALUE: "SeriesValue"})
        )
    else:
        # Mode pays : sélection manuelle ou Top 10 d'une région prédéfinie
        with st.sidebar:
            st.header("Pays")
            mode = st.radio("Mode de sélection des pays", ["Prédéfini (Top 10)", "Personnalisé"])
            add_ch = False
            preset_choice = None
            available_countries = sorted(
                base[~base[COL_COUNTRY].str.contains("(group total)", case=False, na=False)]
                [COL_COUNTRY].dropna().unique().tolist()
            )
            if mode == "Prédéfini (Top 10)":
                preset_choice = st.selectbox("Groupe prédéfini", REGION_OPTIONS, index=0)
                add_ch = st.checkbox("Ajouter la Suisse 🇨🇭", value=False)
            else:
                selected_countries = st.multiselect(
                    "Pays (max 12)", options=available_countries, max_selections=12
                )

        sub = base.copy()
        if mode == "Prédéfini (Top 10)":
            # Classe les pays de la région par valeur décroissante sur la dernière année
            flag_col    = FLAG_MAP[preset_choice]
            pool        = sorted(
                sub.loc[
                    sub[flag_col] &
                    ~sub[COL_COUNTRY].str.contains("(group total)", case=False, na=False),
                    COL_COUNTRY
                ].unique().tolist()
            )
            latest_year = sub[COL_YEAR].max()
            ranked      = (
                sub[(sub[COL_YEAR] == latest_year) & (sub[COL_COUNTRY].isin(pool))]
                .groupby(COL_COUNTRY, as_index=False)[COL_VALUE].sum()
                .sort_values(COL_VALUE, ascending=False)[COL_COUNTRY]
                .tolist()
            )
            keep = ranked[:10]
            if add_ch and "Switzerland" in base[COL_COUNTRY].values and "Switzerland" not in keep:
                keep.append("Switzerland")
        else:
            keep = selected_countries if "selected_countries" in locals() and selected_countries else []

        if keep:
            sub = sub[sub[COL_COUNTRY].isin(keep)]
        if sub.empty:
            st.info("Aucune donnée après sélection des pays.")
            st.stop()

        totals = (
            sub.groupby([COL_COUNTRY, COL_YEAR], as_index=False)[COL_VALUE]
               .sum()
               .rename(columns={COL_VALUE: "SeriesValue"})
        )

    # --- Graphique Altair : courbes temporelles ---
    # alt.Chart construit le graphique ; .encode() lie les colonnes aux axes et couleurs.
    # use_container_width=True étire le graphique sur toute la largeur disponible.
    y_label  = metric_unit_label(metric)
    subtitle = f"{y_label} — {year_range[0]}–{year_range[1]}"
    if show_region:
        subtitle += f" — {region_choice}"

    st.subheader(subtitle)
    st.caption(f"Niveau : {kind_label}")

    # Tri de la légende par valeur décroissante sur la dernière année
    order_latest = (
        totals[totals[COL_YEAR] == totals[COL_YEAR].max()]
        .sort_values("SeriesValue", ascending=False)[COL_COUNTRY]
        .tolist()
    )

    chart = (
        alt.Chart(totals)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{COL_YEAR}:O",      title="Année"),
            y=alt.Y("SeriesValue:Q",        title=y_label),
            color=alt.Color(
                f"{COL_COUNTRY}:N",
                sort=order_latest,
                legend=alt.Legend(title="Région" if show_region else "Pays"),
            ),
            tooltip=[
                alt.Tooltip(f"{COL_COUNTRY}:N", title="Région" if show_region else "Pays"),
                alt.Tooltip(f"{COL_YEAR}:O",    title="Année"),
                alt.Tooltip("SeriesValue:Q",     title=y_label, format=",.0f"),
            ],
        )
        .properties(height=520)
    )
    st.altair_chart(chart, use_container_width=True)

    # Bouton de téléchargement des données affichées au format CSV
    csv_bytes = totals.to_csv(index=False).encode("utf-8")
    fname = f"series_{metric}_{kind_value}_{year_range[0]}_{year_range[1]}"
    fname += f"_{region_choice}_REGION.csv" if show_region else ".csv"
    st.download_button("Télécharger les données en CSV", data=csv_bytes, file_name=fname, mime="text/csv")


# ==============================================================================
# ONGLET 2 — COMPOSITION (CAMEMBERT + BARRES EMPILÉES)
# ==============================================================================
# Affiche la répartition par catégorie d'items pour une année et un territoire donnés.
# Utilise les données "aggregated" (niveau intermédiaire) pour une lecture claire.

with tab_pie:
    st.subheader("Parts par groupe agrégé (camembert)")
    st.caption(f"Indicateur : {INDICATOR_PIE}")

    # Sélection de l'année d'analyse (liste déroulante, année la plus récente en premier)
    years_available = sorted(df[COL_YEAR].unique().tolist(), reverse=True)
    year_pie = st.selectbox(
        "Année", years_available,
        index=years_available.index(min(DEFAULT_END, year_max))
              if min(DEFAULT_END, year_max) in years_available else 0,
        key="year_pie",
    )

    # Filtrage sur l'indicateur, l'année et le niveau "aggregated"
    agg = df[
        (df[COL_KIND].apply(lambda x: str(x).strip().lower() in {"aggregated", "aggregate"})) &
        (df[COL_METRIC] == INDICATOR_PIE) &
        (df[COL_YEAR]   == year_pie)
    ].copy()

    if agg.empty:
        st.info("Aucune ligne 'aggregated' trouvée pour cette année.")
        st.stop()

    # Construction de la liste des pays/régions disponibles pour le camembert
    countries   = [a for a in sorted(agg[COL_COUNTRY].dropna().unique()) if "group total" not in str(a).lower()]
    area_choice = st.selectbox("Choisir un pays ou une région", REGION_OPTIONS + countries, index=0)

    # Calcul des données du camembert selon le territoire choisi
    if area_choice in REGION_OPTIONS:
        # Région → on additionne tous les pays membres
        flag_col = FLAG_MAP[area_choice]
        pie_df = (
            agg[agg[flag_col] & ~agg[COL_COUNTRY].str.contains("(group total)", case=False, na=False)]
            [[COL_ITEM, COL_VALUE]]
            .groupby(COL_ITEM, as_index=False)[COL_VALUE].sum()
        )
        title_area = area_choice
    else:
        # Pays individuel → on filtre directement
        pie_df = (
            agg[agg[COL_COUNTRY] == area_choice][[COL_ITEM, COL_VALUE]]
            .groupby(COL_ITEM, as_index=False)[COL_VALUE].sum()
        )
        title_area = area_choice

    total_val = float(pie_df[COL_VALUE].sum()) if not pie_df.empty else 0.0
    if total_val <= 0 or pie_df.empty:
        st.info("Aucune valeur positive à afficher pour cette sélection.")
        st.stop()

    # Calcul des parts en pourcentage
    pie_df["Part"]     = pie_df[COL_VALUE] / total_val
    pie_df["Part (%)"] = (pie_df["Part"] * 100).round(1)

    val_label = metric_unit_label(INDICATOR_PIE)
    pie_df_display = (
        pie_df[[COL_ITEM, COL_VALUE, "Part (%)"]]
        .sort_values(COL_VALUE, ascending=False)
        .rename(columns={COL_VALUE: val_label})
    )
    pie_df_display[val_label] = pie_df_display[val_label].round(0)

    # Graphique camembert (mark_arc) : chaque secteur = une catégorie d'item
    pie = (
        alt.Chart(pie_df)
        .mark_arc(outerRadius=160)
        .encode(
            theta=alt.Theta(field=COL_VALUE, type="quantitative", stack=True),
            color=alt.Color(
                field=COL_ITEM, type="nominal",
                scale=alt.Scale(range=ALT_CATEGORY[:12]),
                legend=alt.Legend(title="Groupe agrégé"),
            ),
            tooltip=[
                alt.Tooltip(f"{COL_ITEM}:N",  title="Groupe"),
                alt.Tooltip(f"{COL_VALUE}:Q", title=val_label, format=",.0f"),
                alt.Tooltip("Part:Q",          title="Part",    format=".1%"),
            ],
        )
        .properties(
            width=520, height=520,
            title=f"{val_label} — {title_area} — {year_pie}",
        )
    )
    st.altair_chart(pie, use_container_width=False)

    st.write("Données du camembert :")
    st.dataframe(pie_df_display, use_container_width=True)
    st.download_button(
        "Télécharger les données en CSV",
        data=pie_df_display.to_csv(index=False).encode("utf-8"),
        file_name=f"camembert_{INDICATOR_PIE}_{title_area.replace(' ', '_')}_{year_pie}.csv",
        mime="text/csv",
    )

    # --- Graphique secondaire : Top 10 pays en barres empilées ---
    # Même indicateur et année que le camembert, mais tous les pays côte à côte.
    # Utile pour comparer la structure des émissions entre pays.
    st.markdown("---")
    st.subheader(f"Top 10 pays par {val_label} — {year_pie}")

    # Identification des 10 pays les plus importants
    bar_data   = agg[~agg[COL_COUNTRY].str.contains("(group total)", case=False, na=False)].copy()
    top10_pays = bar_data.groupby(COL_COUNTRY)[COL_VALUE].sum().nlargest(10).index.tolist()
    bar_data   = bar_data[bar_data[COL_COUNTRY].isin(top10_pays)]

    if bar_data.empty:
        st.info("Pas assez de données pays pour afficher le graphique.")
    else:
        # Tri des pays du plus au moins important (de gauche à droite)
        order_pays = (
            bar_data.groupby(COL_COUNTRY)[COL_VALUE]
            .sum().sort_values(ascending=False).index.tolist()
        )
        # Barres empilées : chaque couleur = une catégorie d'item
        bar_chart = (
            alt.Chart(bar_data)
            .mark_bar()
            .encode(
                x=alt.X(f"{COL_COUNTRY}:N", sort=order_pays, title="Pays"),
                y=alt.Y(f"{COL_VALUE}:Q",   title=val_label),
                color=alt.Color(
                    f"{COL_ITEM}:N",
                    scale=alt.Scale(range=ALT_CATEGORY[:12]),
                    legend=alt.Legend(title="Groupe agrégé"),
                ),
                tooltip=[
                    alt.Tooltip(f"{COL_COUNTRY}:N", title="Pays"),
                    alt.Tooltip(f"{COL_ITEM}:N",    title="Groupe"),
                    alt.Tooltip(f"{COL_VALUE}:Q",   title=val_label, format=",.0f"),
                ],
            )
            .properties(height=450)
        )
        st.altair_chart(bar_chart, use_container_width=True)

        bar_display = (
            bar_data[[COL_COUNTRY, COL_ITEM, COL_VALUE]]
            .sort_values([COL_COUNTRY, COL_VALUE], ascending=[True, False])
            .rename(columns={COL_COUNTRY: "Pays", COL_ITEM: "Groupe", COL_VALUE: val_label})
        )
        st.download_button(
            "Télécharger les données barres en CSV",
            data=bar_display.to_csv(index=False).encode("utf-8"),
            file_name=f"barres_top10_{year_pie}.csv",
            mime="text/csv",
        )


# ==============================================================================
# ONGLET 3 — CARTE CHOROPLÈTHE
# ==============================================================================
# Affiche une carte colorée où chaque pays est teinté selon la valeur de l'indicateur.
# Utilise Plotly Express (bibliothèque externe — requiert une installation séparée).

with tab_map:
    st.subheader(f"Carte des totaux — {MAP_REGION} (groupe Tous uniquement)")

    years_available = sorted(df[COL_YEAR].unique().tolist(), reverse=True)
    year_map = st.selectbox(
        "Année", years_available,
        index=years_available.index(min(DEFAULT_END, year_max))
              if min(DEFAULT_END, year_max) in years_available else 0,
        key="year_map",
    )

    if not HAS_PLOTLY:
        st.error("Plotly n'est pas installé. Exécutez dans un terminal : py -m pip install plotly")
        st.stop()

    # Filtrage : groupe "All" uniquement (total toutes catégories), indicateur carte, année choisie
    sub_all = df[df[COL_KIND].apply(
        lambda v: str(v).strip().lower() in {"all", "all animals", "all_animals"}
    )]
    sub = sub_all[
        (sub_all[COL_METRIC] == INDICATOR_MAP) &
        (sub_all[COL_YEAR]   == year_map)
    ].copy()
    sub    = sub[~sub[COL_COUNTRY].str.contains("(group total)", case=False, na=False)]
    sub    = sub[sub[FLAG_MAP[MAP_REGION]] == True]  # On garde uniquement les pays de la région carte
    map_df = sub.groupby([COL_COUNTRY], as_index=False)[COL_VALUE].sum()

    # Correction des noms de pays pour que Plotly les reconnaisse géographiquement
    map_df[COL_COUNTRY] = map_df[COL_COUNTRY].replace(NAME_FIX)

    map_label = metric_unit_label(INDICATOR_MAP)

    # px.choropleth : carte où la couleur de chaque pays reflète la valeur de l'indicateur.
    # locationmode="country names" → Plotly reconnaît les pays par leur nom anglais.
    # scope → zone géographique affichée ("europe", "world", "usa", "asia"…)
    fig = px.choropleth(
        map_df,
        locations=COL_COUNTRY,
        locationmode="country names",
        color=COL_VALUE,
        scope="europe",
        color_continuous_scale=CORP_SCALE,
        labels={COL_VALUE: map_label, COL_COUNTRY: "Pays"},
        title=f"{map_label} — {MAP_REGION} — {year_map}",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor=CORP["bg"],
        plot_bgcolor=CORP["panel"],
        font_color=CORP["text"],
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tableau et téléchargement des valeurs affichées sur la carte
    map_df_display = map_df.rename(columns={COL_VALUE: map_label})
    map_df_display[map_label] = map_df_display[map_label].round(0)
    st.write("Valeurs cartographiées :")
    st.dataframe(map_df_display.sort_values(map_label, ascending=False), use_container_width=True)
    st.download_button(
        "Télécharger les données en CSV",
        data=map_df_display.to_csv(index=False).encode("utf-8"),
        file_name=f"carte_{INDICATOR_MAP.replace(' ', '_')}_{year_map}.csv",
        mime="text/csv",
    )
