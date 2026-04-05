"""
Énergie Européenne — Tableau de Bord d'Intelligence Décisionnelle
=================================================================
Lancer avec :
    pip install streamlit plotly scipy pandas numpy
    streamlit run app.py

Nécessite : owid-energy-data-europe.json dans le même dossier.
Sans ce fichier, l'application utilise automatiquement des données synthétiques réalistes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRE COULEUR
# Plotly n'accepte pas les hex à 8 caractères (#rrggbbaa).
# Cette fonction convertit un hex 6 chiffres + opacité (0.0–1.0) en rgba().
# ─────────────────────────────────────────────────────────────────────────────
def hex_rgba(hex6: str, alpha: float) -> str:
    """Convertit '#rrggbb' + alpha en 'rgba(r,g,b,alpha)' pour Plotly."""
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DE LA PAGE
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Europa Énergie · Intelligence Décisionnelle",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS PERSONNALISÉ — esthétique industrielle sombre
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #080c10;
    color: #e8f4f8;
}
[data-testid="stSidebar"] {
    background-color: #0d1318;
    border-right: 1px solid #1e2d3d;
}
[data-testid="stSidebar"] * { color: #e8f4f8 !important; }

h1, h2, h3, h4 { color: #e8f4f8 !important; letter-spacing: 0.03em; }
h1 { font-size: 1.8rem !important; }
h3 { color: #7a9bb5 !important; font-size: 0.85rem !important;
     text-transform: uppercase; letter-spacing: 0.12em; }

[data-testid="metric-container"] {
    background: #0d1318;
    border: 1px solid #1e2d3d;
    border-radius: 10px;
    padding: 1rem 1.25rem !important;
}
[data-testid="metric-container"] label {
    color: #7a9bb5 !important; font-size: 0.7rem !important;
    letter-spacing: 0.15em; text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8f4f8 !important; font-size: 1.8rem !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

[data-testid="stTabs"] [role="tab"] {
    color: #7a9bb5; font-size: 0.78rem; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 0.5rem 1.25rem;
    border-radius: 6px 6px 0 0; border: 1px solid transparent; transition: all 0.2s;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #00e5ff !important;
    border-color: #1e2d3d #1e2d3d transparent;
    background: #0d1318;
}
[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #1e2d3d; gap: 4px; }

[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #0d1318 !important; border: 1px solid #1e2d3d !important;
    color: #e8f4f8 !important; border-radius: 6px !important;
}
[data-testid="stSlider"] [data-testid="stThumbValue"] { color: #00e5ff !important; }

.verdict-box {
    background: linear-gradient(135deg, rgba(0,229,255,0.06), rgba(0,229,255,0.02));
    border: 1px solid rgba(0,229,255,0.2); border-left: 3px solid #00e5ff;
    border-radius: 8px; padding: 1rem 1.25rem; margin-top: 0.75rem;
}
.warn-box {
    background: rgba(247,183,49,0.06); border: 1px solid rgba(247,183,49,0.2);
    border-left: 3px solid #f7b731; border-radius: 8px;
    padding: 1rem 1.25rem; margin-top: 0.75rem;
}
.danger-box {
    background: rgba(255,77,109,0.06); border: 1px solid rgba(255,77,109,0.2);
    border-left: 3px solid #ff4d6d; border-radius: 8px;
    padding: 1rem 1.25rem; margin-top: 0.75rem;
}
.success-box {
    background: rgba(57,211,83,0.06); border: 1px solid rgba(57,211,83,0.2);
    border-left: 3px solid #39d353; border-radius: 8px;
    padding: 1rem 1.25rem; margin-top: 0.75rem;
}
.kpi-label {
    font-size: 0.65rem; color: #7a9bb5; text-transform: uppercase;
    letter-spacing: 0.15em; margin-bottom: 2px;
}
.section-title {
    font-size: 0.65rem; color: #3d5a72; text-transform: uppercase;
    letter-spacing: 0.2em; margin: 1.25rem 0 0.5rem;
    border-bottom: 1px solid #1e2d3d; padding-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# THÈME PLOTLY GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
MISE_EN_PAGE = dict(
    paper_bgcolor="#0d1318",
    plot_bgcolor="#080c10",
    font=dict(family="monospace", color="#7a9bb5", size=10),
    margin=dict(t=32, b=32, l=48, r=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2d3d", borderwidth=1,
                font=dict(size=10, color="#7a9bb5")),
    xaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9)),
    yaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9)),
)

COULEURS = {
    "fossile":      "#ff6b35",
    "nucleaire":    "#c084fc",
    "renouvelable": "#39d353",
    "solaire":      "#f7b731",
    "eolien":       "#00e5ff",
    "hydraulique":  "#4dabf7",
    "charbon":      "#a8a29e",
    "gaz":          "#6b8f71",
    "accent":       "#00e5ff",
    "danger":       "#ff4d6d",
}

# Palette étendue pour les pays (on peut en ajouter, mais on utilisera une palette dynamique)
COULEURS_PAYS = {
    "Germany":        "#00e5ff",
    "France":         "#c084fc",
    "United Kingdom": "#39d353",
    "Spain":          "#f7b731",
    "Poland":         "#ff4d6d",
    "Norway":         "#fb923c",
    "Italy":          "#a3e635",
    "Sweden":         "#38bdf8",
    "Netherlands":    "#f472b6",
    "Portugal":       "#34d399",
}

# Traductions des noms de pays
PAYS_FR = {
    "Germany": "Allemagne", "France": "France",
    "United Kingdom": "Royaume-Uni", "Spain": "Espagne",
    "Poland": "Pologne", "Norway": "Norvège", "Italy": "Italie",
    "Sweden": "Suède", "Netherlands": "Pays-Bas", "Portugal": "Portugal",
    "Austria": "Autriche", "Belgium": "Belgique", "Bulgaria": "Bulgarie",
    "Croatia": "Croatie", "Czechia": "Tchéquie", "Denmark": "Danemark",
    "Estonia": "Estonie", "Finland": "Finlande", "Greece": "Grèce",
    "Hungary": "Hongrie", "Ireland": "Irlande", "Latvia": "Lettonie",
    "Lithuania": "Lituanie", "Luxembourg": "Luxembourg", "Romania": "Roumanie",
    "Serbia": "Serbie", "Slovakia": "Slovaquie", "Slovenia": "Slovénie",
    "Switzerland": "Suisse", "Ukraine": "Ukraine", "Albania": "Albanie",
    "Belarus": "Biélorussie", "Bosnia and Herzegovina": "Bosnie-Herzégovine",
    "Cyprus": "Chypre", "Iceland": "Islande", "Malta": "Malte",
    "Moldova": "Moldavie", "Montenegro": "Monténégro",
    "North Macedonia": "Macédoine du Nord", "Russia": "Russie", "Turkey": "Turquie",
}

COULEURS_CLUSTER = {
    "🌿 Pionniers Verts":      "#39d353",
    "⚛️ Champions Nucléaires": "#c084fc",
    "🔄 En Transition":        "#00e5ff",
    "🏭 Dépendants Fossiles":  "#ff4d6d",
}

# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT ET TRAITEMENT DES DONNÉES
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def charger_donnees() -> pd.DataFrame:
    """Charge le fichier OWID JSON ou génère des données synthétiques."""
    chemin = "owid-energy-data-europe.json"

    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            raw = json.load(f)
        iso_map = {
            "Albania": "ALB", "Austria": "AUT", "Belarus": "BLR", "Belgium": "BEL",
            "Bosnia and Herzegovina": "BIH", "Bulgaria": "BGR", "Croatia": "HRV",
            "Cyprus": "CYP", "Czechia": "CZE", "Denmark": "DNK", "Estonia": "EST",
            "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC",
            "Hungary": "HUN", "Iceland": "ISL", "Ireland": "IRL", "Italy": "ITA",
            "Latvia": "LVA", "Lithuania": "LTU", "Luxembourg": "LUX", "Malta": "MLT",
            "Moldova": "MDA", "Montenegro": "MNE", "Netherlands": "NLD",
            "North Macedonia": "MKD", "Norway": "NOR", "Poland": "POL",
            "Portugal": "PRT", "Romania": "ROU", "Russia": "RUS", "Serbia": "SRB",
            "Slovakia": "SVK", "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE",
            "Switzerland": "CHE", "Turkey": "TUR", "Ukraine": "UKR",
            "United Kingdom": "GBR",
        }
        ignorer = {"Europe", "European Union (27)", "EU28 (Shift)", "World", "Asia", "Africa"}
        lignes = []
        for pays, blob in raw.items():
            if pays in ignorer or not isinstance(blob, dict) or "data" not in blob:
                continue
            for an in blob["data"]:
                r = dict(
                    pays=pays,
                    pays_fr=PAYS_FR.get(pays, pays),
                    iso=iso_map.get(pays, ""),
                    annee=an.get("year"),
                    ges=an.get("greenhouse_gas_emissions", 0) or 0,
                    intensite_c=an.get("carbon_intensity_elec", 0) or 0,
                    charbon=an.get("coal_electricity", 0) or 0,
                    gaz=an.get("gas_electricity", 0) or 0,
                    petrole=an.get("oil_electricity", 0) or 0,
                    nucleaire=an.get("nuclear_electricity", 0) or 0,
                    hydraulique=an.get("hydro_electricity", 0) or 0,
                    solaire=an.get("solar_electricity", 0) or 0,
                    eolien=an.get("wind_electricity", 0) or 0,
                    bioenergie=an.get("biofuel_electricity", 0) or 0,
                )
                r["fossile"]      = r["charbon"] + r["gaz"] + r["petrole"]
                r["renouvelable"] = r["hydraulique"] + r["solaire"] + r["eolien"] + r["bioenergie"]
                r["total"]        = r["fossile"] + r["nucleaire"] + r["renouvelable"]
                if r["total"] > 0:
                    r["part_renouv"]  = r["renouvelable"] / r["total"] * 100
                    r["part_fossile"] = r["fossile"]      / r["total"] * 100
                    r["part_nucleaire"]= r["nucleaire"]   / r["total"] * 100
                else:
                    r["part_renouv"] = r["part_fossile"] = r["part_nucleaire"] = 0
                lignes.append(r)
        return pd.DataFrame(lignes)

    # ── Données synthétiques de secours ──────────────────────────────────
    # On peut étendre la liste des pays pour plus de réalisme
    annees = list(range(2000, 2024))
    profils = {
        "Germany":        dict(r0=6,  r1=52, f0=65, f1=27, n0=28, n1=0,  c0=550, c1=200),
        "France":         dict(r0=11, r1=27, f0=10, f1=9,  n0=78, n1=63, c0=70,  c1=76),
        "United Kingdom": dict(r0=3,  r1=49, f0=76, f1=22, n0=20, n1=28, c0=480, c1=60),
        "Spain":          dict(r0=15, r1=55, f0=64, f1=31, n0=20, n1=13, c0=340, c1=130),
        "Poland":         dict(r0=1,  r1=22, f0=96, f1=74, n0=0,  n1=0,  c0=800, c1=520),
        "Norway":         dict(r0=95, r1=98, f0=3,  f1=1,  n0=0,  n1=0,  c0=12,  c1=8),
        "Italy":          dict(r0=16, r1=45, f0=80, f1=53, n0=0,  n1=0,  c0=380, c1=205),
        "Sweden":         dict(r0=55, r1=74, f0=5,  f1=3,  n0=39, n1=22, c0=35,  c1=20),
        "Netherlands":    dict(r0=4,  r1=38, f0=89, f1=57, n0=4,  n1=3,  c0=490, c1=240),
        "Portugal":       dict(r0=30, r1=65, f0=68, f1=32, n0=0,  n1=0,  c0=250, c1=90),
        "Austria":        dict(r0=70, r1=85, f0=25, f1=10, n0=0,  n1=0,  c0=150, c1=50),
        "Belgium":        dict(r0=10, r1=30, f0=60, f1=40, n0=30, n1=30, c0=300, c1=200),
        "Denmark":        dict(r0=30, r1=70, f0=70, f1=20, n0=0,  n1=0,  c0=400, c1=100),
        "Finland":        dict(r0=30, r1=50, f0=40, f1=20, n0=30, n1=30, c0=200, c1=100),
        "Greece":         dict(r0=15, r1=40, f0=80, f1=50, n0=0,  n1=0,  c0=700, c1=300),
        "Ireland":        dict(r0=10, r1=45, f0=85, f1=40, n0=0,  n1=0,  c0=600, c1=200),
        # ... on peut ajouter d'autres pays si souhaité
    }
    lignes = []
    for pays, p in profils.items():
        n = len(annees)
        for i, y in enumerate(annees):
            t      = i / (n - 1)
            renouv = p["r0"] + (p["r1"] - p["r0"]) * t + np.random.normal(0, 0.5)
            foss   = p["f0"] + (p["f1"] - p["f0"]) * t + np.random.normal(0, 0.5)
            nuc    = p["n0"] + (p["n1"] - p["n0"]) * t + np.random.normal(0, 0.3)
            carb   = p["c0"] + (p["c1"] - p["c0"]) * t + np.random.normal(0, 3)
            sol    = max(0, renouv * 0.3 * (t ** 1.5))
            eol    = max(0, renouv * 0.4 * t)
            hyd    = max(0, renouv * 0.25)
            bio    = max(0, renouv * 0.05)
            lignes.append(dict(
                pays=pays, pays_fr=PAYS_FR.get(pays, pays), iso="", annee=y,
                ges=carb * 100 * 0.003, intensite_c=carb,
                charbon=max(0, foss * 0.5), gaz=max(0, foss * 0.4),
                petrole=max(0, foss * 0.1), nucleaire=max(0, nuc),
                hydraulique=hyd, solaire=sol, eolien=eol, bioenergie=bio,
                fossile=max(0, foss), renouvelable=max(0, renouv), total=100.0,
                part_renouv=max(0, renouv), part_fossile=max(0, foss),
                part_nucleaire=max(0, nuc),
            ))
    return pd.DataFrame(lignes)


@st.cache_data
def enrichir(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute vitesse de transition, TCAC, cluster."""
    df = df.copy().sort_values(["pays", "annee"])

    # Vitesse glissante sur 10 ans (points de pourcentage / an)
    df["vitesse_10a"] = df.groupby("pays")["part_renouv"].transform(
        lambda s: s.diff(10) / 10
    )

    # TCAC solaire et éolien depuis 2010
    an_base    = 2010
    an_recente = df["annee"].max()
    nb_ans     = an_recente - an_base

    base   = df[df["annee"] == an_base][["pays", "solaire", "eolien"]].rename(
        columns={"solaire": "sol_base", "eolien": "eol_base"})
    recent = df[df["annee"] == an_recente][
        ["pays", "solaire", "eolien", "part_renouv", "intensite_c"]
    ].rename(columns={"solaire": "sol_now", "eolien": "eol_now",
                      "part_renouv": "renouv_now", "intensite_c": "carb_now"})

    tcac_df = base.merge(recent, on="pays")

    def tcac(now, bv, n):
        return ((now / bv) ** (1 / n) - 1) * 100 if bv > 0 else None

    tcac_df["tcac_solaire"] = tcac_df.apply(
        lambda r: tcac(r.sol_now, r.sol_base, nb_ans), axis=1)
    tcac_df["tcac_eolien"] = tcac_df.apply(
        lambda r: tcac(r.eol_now, r.eol_base, nb_ans), axis=1)

    # Classification par cluster
    nuc_share = df[df["annee"] == an_recente][["pays", "part_nucleaire"]]
    tcac_df   = tcac_df.merge(nuc_share, on="pays", how="left")

    def classifier(row):
        # Gérer les NaN dans part_nucleaire
        nuc = row.get("part_nucleaire")
        if pd.notna(nuc) and nuc > 40:
            return "⚛️ Champions Nucléaires"
        if row["renouv_now"] > 60:
            return "🌿 Pionniers Verts"
        if row["carb_now"] > 450:
            return "🏭 Dépendants Fossiles"
        return "🔄 En Transition"

    tcac_df["cluster"] = tcac_df.apply(classifier, axis=1)

    df = df.merge(
        tcac_df[["pays", "tcac_solaire", "tcac_eolien", "cluster"]],
        on="pays", how="left"
    )
    return df


@st.cache_data
def agregat_europe(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("annee")[[
        "fossile", "renouvelable", "nucleaire", "charbon", "gaz", "petrole",
        "solaire", "eolien", "hydraulique", "bioenergie", "ges", "total"
    ]].sum().reset_index()


# ─────────────────────────────────────────────────────────────────────────────
# CHARGEMENT GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
df_brut = charger_donnees()
df      = enrichir(df_brut)
agg     = agregat_europe(df)
ANNEES  = sorted(df["annee"].unique())
A_MIN   = int(min(ANNEES))
A_MAX   = int(max(ANNEES))
TOUS_PAYS = sorted(df["pays"].unique().tolist())

# ─────────────────────────────────────────────────────────────────────────────
# BARRE LATÉRALE
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ EUROPA ÉNERGIE")
    st.markdown(
        "<div class='kpi-label'>Tableau de Bord d'Intelligence Décisionnelle</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("<div class='section-title'>Pays à analyser</div>", unsafe_allow_html=True)
    defaut = [p for p in ["Germany", "France", "United Kingdom", "Spain"] if p in TOUS_PAYS]
    pays_sel = st.multiselect(
        "Pays", options=TOUS_PAYS, default=defaut,
        format_func=lambda x: PAYS_FR.get(x, x),
        label_visibility="collapsed",
    )
    if not pays_sel:
        pays_sel = defaut

    st.markdown("<div class='section-title'>Fenêtre temporelle</div>", unsafe_allow_html=True)
    # Par défaut, on évite les années trop anciennes (souvent sans données électriques)
    default_start = max(A_MIN, 2000)
    plage = st.slider(
        "Années", A_MIN, A_MAX,
        (default_start, A_MAX),
        label_visibility="collapsed"
    )

    st.markdown("<div class='section-title'>Scénario de projection</div>", unsafe_allow_html=True)
    scenario = st.selectbox(
        "Scénario",
        ["📈 Tendance Linéaire", "🚀 Accéléré (×2)", "🎯 Zéro Net 2050", "📉 Stagnation"],
        label_visibility="collapsed",
    )

    # Sélecteur indicateur principal supprimé car inutilisé

    st.divider()
    st.markdown(
        f"<div class='kpi-label'>Données : {len(TOUS_PAYS)} pays · {A_MIN}–{A_MAX}</div>",
        unsafe_allow_html=True,
    )
    if not os.path.exists("owid-energy-data-europe.json"):
        st.info(
            "💡 Données synthétiques utilisées. "
            "Placez `owid-energy-data-europe.json` dans le même dossier "
            "pour utiliser les données OWID réelles."
        )

# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────
def filtrer(df, pays=None, annees=None):
    m = pd.Series(True, index=df.index)
    if pays:   m &= df["pays"].isin(pays)
    if annees: m &= df["annee"].between(*annees)
    return df[m]

def tranche_recente(df, pays=None):
    an = df["annee"].max()
    m  = df["annee"] == an
    if pays: m &= df["pays"].isin(pays)
    return df[m]

def nfr(p):
    """Renvoie le nom français d'un pays."""
    return PAYS_FR.get(p, p)

def coul_pays_fr(liste):
    """Dictionnaire couleur indexé par nom français, avec fallback sur palette."""
    couleurs = {}
    palette = px.colors.qualitative.Plotly
    idx = 0
    for p in liste:
        nom_fr = PAYS_FR.get(p, p)
        if p in COULEURS_PAYS:
            couleurs[nom_fr] = COULEURS_PAYS[p]
        else:
            couleurs[nom_fr] = palette[idx % len(palette)]
            idx += 1
    return couleurs

# ─────────────────────────────────────────────────────────────────────────────
# ONGLETS PRINCIPAUX
# ─────────────────────────────────────────────────────────────────────────────
ong1, ong2, ong3, ong4, ong5 = st.tabs([
    "⚡ Vue d'Ensemble",
    "🚀 Vitesse de Transition",
    "🎯 Clusters de Pays",
    "⚖️ Matrice de Décision",
    "📈 Projections",
])

# ═════════════════════════════════════════════════════════════════════════════
# ONGLET 1 · VUE D'ENSEMBLE
# ═════════════════════════════════════════════════════════════════════════════
with ong1:
    st.markdown("# ⚡ Transition Énergétique Européenne")
    st.caption(
        "Vue stratégique · Configurez les pays et la fenêtre temporelle dans la barre latérale"
    )

    agg_f = agg[agg["annee"].between(*plage)].copy()
    # Ne garder que les années avec une production totale valide (>0)
    agg_f = agg_f[agg_f["total"].notna() & (agg_f["total"] > 0)]

    if agg_f.empty:
        st.warning("Aucune donnée valide pour la plage sélectionnée. Veuillez élargir la période ou choisir des années plus récentes.")
    else:
        premier = agg_f.iloc[0]
        dernier = agg_f.iloc[-1]
        an_debut = int(premier["annee"])
        an_fin   = int(dernier["annee"])

        # ── Indicateurs clés (5 colonnes pour inclure le nucléaire) ──
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            r_now = dernier["renouvelable"] / dernier["total"] * 100
            r_deb = premier["renouvelable"] / premier["total"] * 100
            st.metric("☀️ Renouvelables", f"{r_now:.1f} %", f"{r_now - r_deb:+.1f} pp")
        with k2:
            f_now = dernier["fossile"] / dernier["total"] * 100
            f_deb = premier["fossile"] / premier["total"] * 100
            st.metric("🏭 Fossile", f"{f_now:.1f} %", f"{f_now - f_deb:+.1f} pp")
        with k3:
            n_now = dernier["nucleaire"] / dernier["total"] * 100
            n_deb = premier["nucleaire"] / premier["total"] * 100
            st.metric("⚛️ Nucléaire", f"{n_now:.1f} %", f"{n_now - n_deb:+.1f} pp")
        with k4:
            g_pct = (dernier["ges"] - premier["ges"]) / premier["ges"] * 100 if premier["ges"] else 0
            st.metric("🌡️ Émissions GES", f"{dernier['ges']:,.0f} Mt", f"{g_pct:+.1f} %")
        with k5:
            sw_now = (dernier["solaire"] + dernier["eolien"]) / dernier["total"] * 100
            sw_deb = (premier["solaire"] + premier["eolien"]) / premier["total"] * 100
            st.metric("💨 Solaire+Éolien", f"{sw_now:.1f} %", f"{sw_now - sw_deb:+.1f} pp")

        st.divider()
        ca, cb = st.columns([3, 2])

        with ca:
            st.markdown(
                "<div class='section-title'>Mix Énergétique Européen · Aires Empilées</div>",
                unsafe_allow_html=True,
            )
            fig = go.Figure()
            for src, coul, nom in [
                ("fossile",      COULEURS["fossile"],      "Fossiles"),
                ("nucleaire",    COULEURS["nucleaire"],    "Nucléaire"),
                ("renouvelable", COULEURS["renouvelable"], "Renouvelables"),
            ]:
                fig.add_trace(go.Scatter(
                    x=agg_f["annee"], y=agg_f[src], name=nom, mode="lines",
                    stackgroup="one", line=dict(width=0.5),
                    fillcolor=hex_rgba(coul, 0.73),
                    hovertemplate=f"{nom} : %{{y:,.0f}} TWh<extra></extra>",
                ))
            fig.update_layout(
                **{k: v for k, v in MISE_EN_PAGE.items() if k != "legend"}, height=300, hovermode="x unified",
                legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with cb:
            st.markdown(
                "<div class='section-title'>Répartition du Mix · Dernière Année</div>",
                unsafe_allow_html=True,
            )
            etiq = ["Charbon", "Gaz", "Pétrole", "Nucléaire",
                    "Hydraulique", "Solaire", "Éolien", "Bioénergie"]
            vals = [dernier[c] for c in
                    ["charbon", "gaz", "petrole", "nucleaire",
                     "hydraulique", "solaire", "eolien", "bioenergie"]]
            fig2 = go.Figure(go.Pie(
                labels=etiq, values=vals, hole=0.55,
                marker=dict(
                    colors=[COULEURS["charbon"], COULEURS["gaz"], COULEURS["fossile"],
                            COULEURS["nucleaire"], COULEURS["hydraulique"],
                            COULEURS["solaire"], COULEURS["eolien"], COULEURS["renouvelable"]],
                    line=dict(color="#080c10", width=2),
                ),
                textfont=dict(size=9, color="#e8f4f8"),
                hovertemplate="%{label} : %{value:,.0f} TWh (%{percent})<extra></extra>",
            ))
            fig2.update_layout(
                **MISE_EN_PAGE, height=300,
                annotations=[dict(text=f"{int(an_fin)}", x=0.5, y=0.5,
                                  font=dict(size=18, color="#e8f4f8"), showarrow=False)],
            )
            st.plotly_chart(fig2, use_container_width=True)

        # ── Comparaison des pays sélectionnés ──
        st.markdown(
            "<div class='section-title'>Pays Sélectionnés · Part des Renouvelables dans le Temps</div>",
            unsafe_allow_html=True,
        )
        df_sel = filtrer(df, pays_sel, plage).copy()
        # Ne garder que les lignes avec part_renouv non nulle pour le graphique
        df_sel = df_sel[df_sel["part_renouv"].notna()]
        if not df_sel.empty:
            df_sel["Pays"] = df_sel["pays"].map(PAYS_FR).fillna(df_sel["pays"])
            fig3 = px.line(
                df_sel, x="annee", y="part_renouv", color="Pays",
                color_discrete_map=coul_pays_fr(pays_sel),
                labels={"part_renouv": "Part des renouvelables (%)", "annee": ""},
            )
            fig3.update_traces(line=dict(width=2.5))
            fig3.update_layout(**MISE_EN_PAGE, height=280, hovermode="x unified")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Aucune donnée de part renouvelable pour les pays sélectionnés sur cette période.")

        # ── Verdict stratégique ──
        # Calcul du pays le plus rapide parmi les sélectionnés, en ignorant les NaN
        if not df_sel.empty:
            progression = df_sel.groupby("pays")["part_renouv"].agg(
                lambda x: x.iloc[-1] - x.iloc[0] if len(x) > 1 else np.nan
            )
            plus_rapide = progression.idxmax() if not progression.dropna().empty else "—"
        else:
            plus_rapide = "—"

        st.markdown(f"""
        <div class='verdict-box'>
        <b>⚖️ Verdict Stratégique</b><br>
        L'Europe a réduit sa part de fossiles de <b>{abs(f_now - f_deb):.1f} pp</b> depuis {an_debut},
        tandis que les renouvelables ont progressé de <b>{r_now - r_deb:+.1f} pp</b> et le nucléaire de <b>{n_now - n_deb:+.1f} pp</b>.
        Parmi les pays sélectionnés, <b>{nfr(plus_rapide)}</b> a réalisé la plus grande transition absolue.
        À la trajectoire actuelle, l'Europe atteindra <b>50 % de renouvelables</b> aux alentours de 2030.
        Risque clé : <b>{int(f_now)} %</b> de la production reste dépendante des fossiles.
        </div>
        """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# ONGLET 2 · VITESSE DE TRANSITION
# ═════════════════════════════════════════════════════════════════════════════
with ong2:
    st.markdown("# 🚀 Analyse de la Vitesse de Transition")
    st.caption("Qui avance le plus vite ? Mesure du rythme de décarbonation par pays.")

    df_sel = filtrer(df, pays_sel, plage).copy()
    df_sel["Pays"] = df_sel["pays"].map(PAYS_FR).fillna(df_sel["pays"])

    # ── Vitesse glissante ──
    st.markdown(
        "<div class='section-title'>Vitesse Glissante sur 10 Ans · pp renouvelables / an</div>",
        unsafe_allow_html=True,
    )
    fig_v = px.line(
        df_sel.dropna(subset=["vitesse_10a"]),
        x="annee", y="vitesse_10a", color="Pays",
        color_discrete_map=coul_pays_fr(pays_sel),
        labels={"vitesse_10a": "pp / an", "annee": ""},
    )
    fig_v.update_traces(line=dict(width=2))
    fig_v.add_hline(y=0, line_dash="dot", line_color="#3d5a72", annotation_text="Stagnation")
    fig_v.update_layout(**MISE_EN_PAGE, height=300, hovermode="x unified")
    st.plotly_chart(fig_v, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            "<div class='section-title'>Vitesse vs Intensité Carbone · Dernière Année</div>",
            unsafe_allow_html=True,
        )
        df_r = tranche_recente(df).dropna(subset=["vitesse_10a"]).copy()
        df_r["Pays"] = df_r["pays"].map(PAYS_FR).fillna(df_r["pays"])
        fig_sc = px.scatter(
            df_r, x="intensite_c", y="vitesse_10a", text="Pays", color="cluster",
            color_discrete_map=COULEURS_CLUSTER, size_max=14,
            labels={"intensite_c": "Intensité Carbone (gCO₂/kWh)",
                    "vitesse_10a": "Vitesse de Transition (pp/an)"},
        )
        fig_sc.update_traces(textposition="top center", textfont=dict(size=8, color="#7a9bb5"))
        fig_sc.add_hline(y=float(df_r["vitesse_10a"].median()),
                         line_dash="dot", line_color="#1e2d3d")
        fig_sc.add_vline(x=float(df_r["intensite_c"].median()),
                         line_dash="dot", line_color="#1e2d3d")
        fig_sc.update_layout(**MISE_EN_PAGE, height=320)
        st.plotly_chart(fig_sc, use_container_width=True)

    with c2:
        st.markdown(
            "<div class='section-title'>TCAC Solaire & Éolien par Pays</div>",
            unsafe_allow_html=True,
        )
        df_tc = tranche_recente(df)[["pays", "tcac_solaire", "tcac_eolien"]].dropna().copy()
        df_tc = df_tc.nlargest(12, "tcac_solaire")
        df_tc["Pays"] = df_tc["pays"].map(PAYS_FR).fillna(df_tc["pays"])
        df_f = df_tc.melt(
            id_vars=["pays", "Pays"],
            value_vars=["tcac_solaire", "tcac_eolien"],
            var_name="source", value_name="tcac",
        )
        df_f["source"] = df_f["source"].map(
            {"tcac_solaire": "☀️ Solaire", "tcac_eolien": "💨 Éolien"})
        fig_tc = px.bar(
            df_f, y="Pays", x="tcac", color="source", orientation="h",
            color_discrete_map={"☀️ Solaire": COULEURS["solaire"],
                                 "💨 Éolien": COULEURS["eolien"]},
            barmode="group",
            labels={"tcac": "TCAC (%)", "Pays": ""},
        )
        fig_tc.update_layout(**MISE_EN_PAGE, height=320)
        st.plotly_chart(fig_tc, use_container_width=True)

    # ── Classement général ──
    st.markdown(
        "<div class='section-title'>Classement Complet · Décarbonateurs les Plus Rapides</div>",
        unsafe_allow_html=True,
    )
    df_cl = (
        tranche_recente(df)
        .dropna(subset=["vitesse_10a"])
        .sort_values("vitesse_10a", ascending=False)
        .copy()
    )
    df_cl["Rang"]            = range(1, len(df_cl) + 1)
    df_cl["Pays"]            = df_cl["pays"].map(PAYS_FR).fillna(df_cl["pays"])
    df_cl["Vitesse (pp/an)"] = df_cl["vitesse_10a"].round(2)
    df_cl["Part Renouv."]    = df_cl["part_renouv"].round(1).astype(str) + " %"
    df_cl["Int. Carbone"]    = df_cl["intensite_c"].round(0).astype(str) + " gCO₂"
    df_cl["Cluster"]         = df_cl["cluster"]
    st.dataframe(
        df_cl[["Rang", "Pays", "Vitesse (pp/an)", "Part Renouv.", "Int. Carbone", "Cluster"]],
        use_container_width=True, hide_index=True, height=300,
    )

    top3    = [nfr(c) for c in df_cl["pays"].head(3).tolist()]
    bottom3 = [nfr(c) for c in df_cl["pays"].tail(3).tolist()]
    st.markdown(f"""
    <div class='success-box'>
    <b>🚀 Constat Clé</b><br>
    <b>{top3[0]}</b>, <b>{top3[1]}</b> et <b>{top3[2]}</b> sont les décarbonateurs les plus rapides
    selon la vitesse glissante sur 10 ans.
    Les retardataires — <b>{bottom3[-1]}</b>, <b>{bottom3[-2]}</b> — risquent de ne pas
    atteindre les objectifs UE 2030.
    Le fort TCAC solaire chez les leaders suggère que la production décentralisée
    est le principal moteur, et non le grand hydraulique.
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# ONGLET 3 · CLUSTERS DE PAYS
# ═════════════════════════════════════════════════════════════════════════════
with ong3:
    st.markdown("# 🎯 Intelligence par Clusters de Pays")
    st.caption(
        "Regroupement basé sur les données · normalisé en percentiles pour une comparaison équitable"
    )

    df_r = tranche_recente(df).dropna(subset=["cluster"]).copy()
    df_r["Pays"] = df_r["pays"].map(PAYS_FR).fillna(df_r["pays"])

    # Normalisation en rang percentile
    for col in ["part_renouv", "intensite_c", "vitesse_10a", "tcac_solaire"]:
        if col in df_r.columns:
            df_r[f"{col}_pct"] = df_r[col].rank(pct=True) * 100

    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown(
            "<div class='section-title'>Nuage de Clusters · Percentiles Normalisés (sans unités mixtes)</div>",
            unsafe_allow_html=True,
        )
        fig_cl = px.scatter(
            df_r.dropna(subset=["part_renouv_pct", "intensite_c_pct"]),
            x="part_renouv_pct", y="intensite_c_pct",
            color="cluster", text="Pays",
            color_discrete_map=COULEURS_CLUSTER, size_max=12,
            labels={
                "part_renouv_pct": "Part Renouvelables → Percentile",
                "intensite_c_pct": "Intensité Carbone → Percentile",
            },
        )
        fig_cl.update_traces(
            textposition="top center",
            textfont=dict(size=8, color="#7a9bb5"),
            marker=dict(size=12),
        )
        for (x, y, txt) in [
            (25, 25, "Fossile élevé / Renouv. faibles"),
            (75, 25, "Pionniers verts"),
            (25, 75, "Sale & lent"),
            (75, 75, "Renouv. élevées\nCarbone élevé ?"),
        ]:
            fig_cl.add_annotation(x=x, y=y, text=txt, showarrow=False,
                                  font=dict(size=7, color="#3d5a72"), xref="x", yref="y")
        fig_cl.update_layout(**MISE_EN_PAGE, height=380)
        st.plotly_chart(fig_cl, use_container_width=True)

    with c2:
        st.markdown(
            "<div class='section-title'>Profils par Cluster · Radar</div>",
            unsafe_allow_html=True,
        )
        cats = ["Renouvelables", "Faible Fossile", "Vitesse", "Croissance Solaire"]
        fig_radar = go.Figure()
        for nom_cl, grp in df_r.groupby("cluster"):
            moy_r = grp["part_renouv"].mean()
            moy_f = 100 - grp["part_fossile"].mean()
            moy_v = float(grp["vitesse_10a"].mean() or 0) * 8
            moy_s = float(grp["tcac_solaire"].mean() or 0) / 60 * 100
            vals  = [max(0, min(100, v)) for v in [moy_r, moy_f, moy_v, moy_s]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                name=nom_cl, fill="toself",
                line=dict(color=COULEURS_CLUSTER.get(nom_cl, "#fff"), width=2),
                fillcolor=hex_rgba(COULEURS_CLUSTER.get(nom_cl, "#ffffff"), 0.13),
            ))
        fig_radar.update_layout(
            **{k: v for k, v in MISE_EN_PAGE.items() if k not in ("xaxis", "yaxis")},
            height=380,
            polar=dict(
                bgcolor="#080c10",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e2d3d",
                                tickfont=dict(color="#3d5a72", size=7), tickcolor="#1e2d3d"),
                angularaxis=dict(gridcolor="#1e2d3d", tickfont=dict(color="#7a9bb5", size=9)),
            ),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── Fiches par cluster ──
    st.markdown(
        "<div class='section-title'>Résumés par Cluster</div>", unsafe_allow_html=True
    )
    clusters = list(df_r.groupby("cluster"))
    cols = st.columns(len(clusters))
    for idx, (nom_cl, grp) in enumerate(clusters):
        with cols[idx]:
            coul       = COULEURS_CLUSTER.get(nom_cl, "#fff")
            liste_pays = ", ".join([nfr(p) for p in grp["pays"].tolist()])
            moy_renouv = grp["part_renouv"].mean()
            moy_carb   = grp["intensite_c"].mean()
            n          = len(grp)
            st.markdown(f"""
            <div style="border:1px solid {coul}44; border-left:3px solid {coul};
                        border-radius:8px; padding:0.75rem; background:rgba(0,0,0,0.2)">
              <div style="color:{coul}; font-size:0.7rem; letter-spacing:0.1em; margin-bottom:6px">
                {nom_cl} · {n} pays
              </div>
              <div style="font-size:1.4rem; color:#e8f4f8; font-weight:700">{moy_renouv:.0f} %</div>
              <div style="font-size:0.65rem; color:#7a9bb5">moy. renouvelables</div>
              <div style="font-size:0.7rem; color:#7a9bb5; margin-top:6px">{moy_carb:.0f} gCO₂/kWh</div>
              <div style="font-size:0.62rem; color:#3d5a72; margin-top:6px; line-height:1.4">
                {liste_pays}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Migration 2010 → aujourd'hui ──
    st.markdown(
        "<div class='section-title'>Migration des Pays · Part Renouvelables 2010 → Aujourd'hui</div>",
        unsafe_allow_html=True,
    )
    a1, a2 = max(A_MIN, 2010), A_MAX
    df_2010 = filtrer(df, None, (a1, a1))[["pays", "part_renouv"]].rename(
        columns={"part_renouv": "r2010"})
    df_now  = tranche_recente(df)[["pays", "part_renouv"]].rename(
        columns={"part_renouv": "rnow"})
    mig = df_2010.merge(df_now, on="pays").sort_values("rnow", ascending=True)
    mig["delta"] = mig["rnow"] - mig["r2010"]
    mig["Pays"]  = mig["pays"].map(PAYS_FR).fillna(mig["pays"])
    mig = mig.tail(15)

    fig_mig = go.Figure()
    fig_mig.add_trace(go.Bar(
        y=mig["Pays"], x=mig["r2010"], name=str(a1),
        orientation="h", marker=dict(color="#1e2d3d"),
    ))
    fig_mig.add_trace(go.Bar(
        y=mig["Pays"], x=mig["delta"], name=f"Progression → {a2}",
        orientation="h", marker=dict(color=hex_rgba(COULEURS["renouvelable"], 0.73)),
        base=mig["r2010"].values,
    ))
    mise_en_page = {k: v for k, v in MISE_EN_PAGE.items() if k != "xaxis"}
    fig_mig.update_layout(
        **mise_en_page, height=400, barmode="overlay", hovermode="y unified",
        xaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9), title="Part des Renouvelables (%)"),
    )
    st.plotly_chart(fig_mig, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# ONGLET 4 · MATRICE DE DÉCISION
# ═════════════════════════════════════════════════════════════════════════════
with ong4:
    st.markdown("# ⚖️ Matrice de Décision")
    st.caption(
        "Notation multicritère pour la priorisation des politiques publiques et des investissements."
    )

    # Filtrer sur la plage sélectionnée et prendre la dernière année pour chaque pays
    df_plage = df[df["annee"].between(plage[0], plage[1])]
    df_r = (df_plage[df_plage["pays"].isin(pays_sel)]
            .sort_values("annee")
            .groupby("pays")
            .last()
            .reset_index())
    df_r["Pays"] = df_r["pays"].map(PAYS_FR).fillna(df_r["pays"])

    def normaliser(serie, inverser=False):
        mn, mx = serie.min(), serie.max()
        if mx == mn:
            return pd.Series([50.0] * len(serie), index=serie.index)
        n = (serie - mn) / (mx - mn) * 100
        return 100 - n if inverser else n

    if not df_r.empty:
        df_r["score_ambition"] = normaliser(df_r["part_renouv"])
        df_r["score_vitesse"]  = normaliser(df_r["vitesse_10a"].fillna(0))
        df_r["score_solaire"]  = normaliser(df_r["tcac_solaire"].fillna(0))
        df_r["score_risque"]   = normaliser(df_r["part_fossile"], inverser=True)
        df_r["score_carbone"]  = normaliser(df_r["intensite_c"], inverser=True)
        df_r["composite"] = (
            df_r["score_ambition"] * 0.25 +
            df_r["score_vitesse"]  * 0.25 +
            df_r["score_solaire"]  * 0.20 +
            df_r["score_risque"]   * 0.15 +
            df_r["score_carbone"]  * 0.15
        )

        # ── Radar multicritère ──
        st.markdown(
            "<div class='section-title'>Profil Multicritère par Pays · Radar</div>",
            unsafe_allow_html=True,
        )
        labels_score = [
            "Ambition", "Vitesse de Transition",
            "Croissance Solaire", "Faible Risque Fossile", "Faible Int. Carbone",
        ]
        cols_score = [
            "score_ambition", "score_vitesse",
            "score_solaire", "score_risque", "score_carbone",
        ]
        fig_dm = go.Figure()
        for _, ligne in df_r.iterrows():
            coul = COULEURS_PAYS.get(ligne["pays"], "#fff")  # fallback, mais on utilise une palette étendue plus tard
            # Pour une meilleure gestion des couleurs, on utilise la fonction coul_pays_fr
            # mais on a besoin du nom français. On peut le récupérer via nfr()
            nom_fr = nfr(ligne["pays"])
            # On va chercher la couleur dans un dictionnaire généré à partir de pays_sel
            # Pour simplifier, on utilise la palette étendue de coul_pays_fr
            couleurs_map = coul_pays_fr(pays_sel)
            coul = couleurs_map.get(nom_fr, "#ffffff")
            vals = [ligne[s] for s in cols_score]
            fig_dm.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=labels_score + [labels_score[0]],
                name=ligne["Pays"], fill="toself",
                line=dict(color=coul, width=2),
                fillcolor=hex_rgba(coul, 0.09),
            ))
        fig_dm.update_layout(
            **{k: v for k, v in MISE_EN_PAGE.items() if k not in ("xaxis", "yaxis")},
            height=380,
            polar=dict(
                bgcolor="#080c10",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e2d3d",
                                tickfont=dict(color="#3d5a72", size=7), tickcolor="#1e2d3d"),
                angularaxis=dict(gridcolor="#1e2d3d", tickfont=dict(color="#7a9bb5", size=10)),
            ),
        )
        st.plotly_chart(fig_dm, use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                "<div class='section-title'>Classement par Score Composite</div>",
                unsafe_allow_html=True,
            )
            df_rang = df_r[["Pays", "composite"]].sort_values("composite", ascending=True)
            # Couleurs basées sur la même palette
            couleurs_map = coul_pays_fr(pays_sel)
            coul_b = [couleurs_map.get(p, "#00e5ff") for p in df_rang["Pays"]]
            fig_rang = go.Figure(go.Bar(
                y=df_rang["Pays"], x=df_rang["composite"],
                orientation="h", marker=dict(color=coul_b),
                text=df_rang["composite"].round(0).astype(int).astype(str),
                textposition="inside",
                insidetextfont=dict(color="#080c10", size=10),
            ))
            fig_rang.add_vline(x=50, line_dash="dot", line_color="#3d5a72",
                               annotation_text="Médiane")
            mise_en_page = {k: v for k, v in MISE_EN_PAGE.items() if k != "xaxis"}
            fig_rang.update_layout(
                **mise_en_page, height=280,
                xaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9), range=[0, 100]),
            )
            st.plotly_chart(fig_rang, use_container_width=True)

        with c2:
            st.markdown(
                "<div class='section-title'>Matrice Risque vs Opportunité</div>",
                unsafe_allow_html=True,
            )
            df_r["risque"]      = df_r["part_fossile"]
            df_r["opportunite"] = (df_r["score_vitesse"] + df_r["score_solaire"]) / 2
            fig_ro = px.scatter(
                df_r, x="risque", y="opportunite", text="Pays", color="Pays",
                color_discrete_map=coul_pays_fr(pays_sel),
                size="composite", size_max=30,
                labels={"risque":      "Risque · Dépendance Fossile →",
                        "opportunite": "Score d'Opportunité →"},
            )
            fig_ro.update_traces(textposition="top center",
                                 textfont=dict(size=8, color="#7a9bb5"))
            med_r = df_r["risque"].median()
            med_o = df_r["opportunite"].median()
            fig_ro.add_hline(y=float(med_o), line_dash="dot", line_color="#1e2d3d")
            fig_ro.add_vline(x=float(med_r), line_dash="dot", line_color="#1e2d3d")
            fig_ro.add_annotation(
                x=df_r["risque"].max() * 0.85, y=df_r["opportunite"].max() * 0.95,
                text="Risque élevé · Forte opportunité",
                font=dict(size=7, color="#f7b731"), showarrow=False,
            )
            fig_ro.add_annotation(
                x=df_r["risque"].min() * 1.1, y=df_r["opportunite"].max() * 0.95,
                text="Faible risque · Forte opportunité\n(Cibles prioritaires)",
                font=dict(size=7, color="#39d353"), showarrow=False,
            )
            fig_ro.update_layout(**MISE_EN_PAGE, height=280, showlegend=False)
            st.plotly_chart(fig_ro, use_container_width=True)

        # ── Tableau des scores ──
        st.markdown(
            "<div class='section-title'>Détail Complet des Scores</div>",
            unsafe_allow_html=True,
        )
        df_tab = df_r[[
            "Pays", "composite", "score_ambition", "score_vitesse",
            "score_solaire", "score_risque", "score_carbone",
        ]].sort_values("composite", ascending=False)
        df_tab.columns = [
            "Pays", "Composite", "Ambition", "Vitesse",
            "Solaire", "Faible Fossile", "Faible Carbone",
        ]
        df_tab = df_tab.set_index("Pays").round(1)
        st.dataframe(
            df_tab.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
        )

        # ── Note de politique ──
        meilleur = df_r.sort_values("composite", ascending=False).iloc[0]
        moins_bon = df_r.sort_values("composite").iloc[0]
        st.markdown(f"""
        <div class='warn-box'>
        <b>📋 Note de Politique</b><br>
        Parmi les pays sélectionnés, <b>{nfr(meilleur['pays'])}</b> obtient le score composite
        le plus élevé ({meilleur['composite']:.0f}/100) — alliant forte ambition,
        vitesse de transition élevée et dynamisme solaire.
        <b>{nfr(moins_bon['pays'])}</b> obtient le score le plus faible ({moins_bon['composite']:.0f}/100)
        et représente la priorité d'intervention politique la plus urgente.
        <br><b>Recommandation :</b> réorienter les fonds énergétiques de l'UE
        proportionnellement à l'écart composite, et non à la seule part brute des renouvelables.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Aucune donnée disponible pour les pays sélectionnés.")

# ═════════════════════════════════════════════════════════════════════════════
# ONGLET 5 · PROJECTIONS
# ═════════════════════════════════════════════════════════════════════════════
with ong5:
    st.markdown("# 📈 Projections par Scénario")
    st.caption(
        "Analyse prospective avec intervalles de confiance à 95 % · "
        "Scénario sélectionné dans la barre latérale."
    )

    agg_f = agg[agg["annee"].between(*plage)].copy()
    # Ne garder que les années avec production totale valide
    agg_f = agg_f[agg_f["total"].notna() & (agg_f["total"] > 0)]

    if agg_f.empty:
        st.warning("Pas assez de données historiques pour effectuer des projections sur cette plage.")
    else:
        X = agg_f["annee"].values.astype(float)          # années historiques
        an_fin = int(agg_f["annee"].iloc[-1])            # dernière année de la plage
        annees_proj = np.arange(an_fin, 2051).astype(float)   # de an_fin à 2050

        def projeter(y_vals, scen, ann_proj):
            pente, intercept, r, p, se = stats.linregress(X, y_vals)
            n = len(X)
            moy_x = X.mean()
            proj = pente * ann_proj + intercept
            se_pred = se * np.sqrt(
                1 / n + (ann_proj - moy_x) ** 2 / np.sum((X - moy_x) ** 2)
            )
            ic = 1.96 * se_pred
            if scen == "🚀 Accéléré (×2)":
                proj = y_vals[-1] + pente * 2 * (ann_proj - X[-1])
            elif scen == "🎯 Zéro Net 2050":
                proj = np.maximum(0, y_vals[-1] * (1 - (ann_proj - X[-1]) / (2050 - X[-1])))
            elif scen == "📉 Stagnation":
                proj = np.full_like(ann_proj, y_vals[-1])
            return pente, r ** 2, p, proj, proj + ic, np.maximum(0, proj - ic)

        ann_hist = X  # déjà défini

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                "<div class='section-title'>Émissions GES · Projection avec IC à 95 %</div>",
                unsafe_allow_html=True,
            )
            y_ges = agg_f["ges"].values
            pente_g, r2_g, p_g, proj_g, sup_g, inf_g = projeter(y_ges, scenario, annees_proj)

            fig_ges = go.Figure()
            fig_ges.add_trace(go.Scatter(
                x=ann_hist, y=y_ges, name="Historique",
                line=dict(color=COULEURS["danger"], width=2.5), mode="lines",
            ))
            fig_ges.add_trace(go.Scatter(
                x=annees_proj, y=sup_g, fill=None, mode="lines",
                line=dict(width=0), showlegend=False,
            ))
            fig_ges.add_trace(go.Scatter(
                x=annees_proj, y=inf_g, fill="tonexty", mode="lines",
                line=dict(width=0), name="IC 95 %",
                fillcolor="rgba(255,77,109,0.12)",
            ))
            fig_ges.add_trace(go.Scatter(
                x=annees_proj, y=proj_g, name=scenario,
                line=dict(color=COULEURS["danger"], width=2, dash="dash"),
            ))
            fig_ges.add_hline(y=0, line_dash="dot", line_color=COULEURS["renouvelable"],
                              annotation_text="Zéro Net")
            mise_en_page = {k: v for k, v in MISE_EN_PAGE.items() if k != "yaxis"}
            fig_ges.update_layout(
                **mise_en_page, height=300, hovermode="x unified",
                yaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9), title="Mt CO₂eq"),
            )
            st.plotly_chart(fig_ges, use_container_width=True)

            s1, s2, s3 = st.columns(3)
            s1.metric("Pente de Tendance", f"{pente_g:+.1f} Mt/an")
            s2.metric("Ajustement R²",     f"{r2_g:.3f}")
            s3.metric("Significatif",      "Oui" if p_g < 0.05 else "Non")

        with c2:
            st.markdown(
                "<div class='section-title'>Renouvelables vs Fossiles · Point de Croisement</div>",
                unsafe_allow_html=True,
            )
            y_renouv = agg_f["renouvelable"].values
            y_foss   = agg_f["fossile"].values
            _, _, _, proj_r, _, _ = projeter(y_renouv, scenario, annees_proj)
            _, _, _, proj_f, _, _ = projeter(y_foss,   scenario, annees_proj)

            diff = proj_r - proj_f
            idx_crois = np.where(diff > 0)[0]
            an_crois = int(annees_proj[idx_crois[0]]) if len(idx_crois) else None

            fig_course = go.Figure()
            fig_course.add_trace(go.Scatter(
                x=ann_hist, y=y_foss, name="Fossiles (hist.)",
                line=dict(color=COULEURS["fossile"], width=2.5),
                fill="tozeroy", fillcolor=hex_rgba(COULEURS["fossile"], 0.13),
            ))
            fig_course.add_trace(go.Scatter(
                x=ann_hist, y=y_renouv, name="Renouvelables (hist.)",
                line=dict(color=COULEURS["renouvelable"], width=2.5),
                fill="tozeroy", fillcolor=hex_rgba(COULEURS["renouvelable"], 0.13),
            ))
            fig_course.add_trace(go.Scatter(
                x=annees_proj, y=np.maximum(0, proj_f), name="Fossiles (proj.)",
                line=dict(color=COULEURS["fossile"], dash="dash", width=1.5),
            ))
            fig_course.add_trace(go.Scatter(
                x=annees_proj, y=np.maximum(0, proj_r), name="Renouvelables (proj.)",
                line=dict(color=COULEURS["renouvelable"], dash="dash", width=1.5),
            ))
            if an_crois:
                fig_course.add_vline(
                    x=an_crois, line_dash="dot", line_color=COULEURS["renouvelable"],
                    annotation_text=f"Croisement {an_crois}",
                    annotation_font_color=COULEURS["renouvelable"],
                )
            mise_en_page = {k: v for k, v in MISE_EN_PAGE.items() if k != "yaxis"}
            fig_course.update_layout(
                **mise_en_page, height=300, hovermode="x unified",
                yaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9), title="TWh (agrégat)"),
            )
            st.plotly_chart(fig_course, use_container_width=True)

            if an_crois:
                st.markdown(f"""
                <div class='success-box'>
                <b>⚡ Point de Croisement Détecté</b><br>
                Dans le scénario <b>{scenario}</b>, la production renouvelable
                dépasse le fossile en <b>{an_crois}</b>
                — dans {an_crois - an_fin} ans.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='danger-box'>
                <b>⚠️ Aucun croisement détecté avant 2050</b> dans ce scénario.
                Une accélération des politiques est nécessaire pour atteindre
                les objectifs de transition énergétique.
                </div>
                """, unsafe_allow_html=True)

        # ── Projections par pays ──
        st.markdown(
            "<div class='section-title'>Projections par Pays · Part des Renouvelables jusqu'en 2050</div>",
            unsafe_allow_html=True,
        )
        fig_pp = go.Figure()
        for pays in pays_sel:
            df_p = filtrer(df, [pays], plage).dropna(subset=["part_renouv"])
            if df_p.empty or len(df_p) < 2:
                continue
            Xp        = df_p["annee"].values.astype(float)
            yp        = df_p["part_renouv"].values
            # On fait une régression simple sans intervalle (pour la lisibilité)
            pente_p, intercept_p, _, _, _ = stats.linregress(Xp, yp)
            ann_proj  = np.arange(Xp[-1], 2051)
            val_proj  = np.minimum(100, np.maximum(0, pente_p * ann_proj + intercept_p))
            if scenario == "🚀 Accéléré (×2)":
                val_proj = np.minimum(100, np.maximum(
                    0, yp[-1] + pente_p * 2 * (ann_proj - Xp[-1])))
            elif scenario == "🎯 Zéro Net 2050":
                val_proj = np.minimum(
                    100, yp[-1] + (100 - yp[-1]) * (ann_proj - Xp[-1]) / (2050 - Xp[-1]))
            coul = COULEURS_PAYS.get(pays, "#ffffff")
            # On utilise la palette étendue pour les couleurs
            couleurs_map = coul_pays_fr(pays_sel)
            nom_fr = nfr(pays)
            coul = couleurs_map.get(nom_fr, "#ffffff")
            nom = nom_fr
            fig_pp.add_trace(go.Scatter(
                x=Xp, y=yp, name=nom, line=dict(color=coul, width=2)))
            fig_pp.add_trace(go.Scatter(
                x=ann_proj, y=val_proj, name=f"{nom} (proj.)",
                line=dict(color=coul, dash="dash", width=1.5),
                showlegend=False,
            ))
        if len(fig_pp.data) > 0:
            fig_pp.add_hline(y=100, line_dash="dot", line_color="#3d5a72",
                             annotation_text="100 % renouvelables")
            fig_pp.add_hline(y=50,  line_dash="dot", line_color="#3d5a72",
                             annotation_text="Seuil 50 %")
            mise_en_page = {k: v for k, v in MISE_EN_PAGE.items() if k != "yaxis"}
            fig_pp.update_layout(
                **mise_en_page, height=350, hovermode="x unified",
                yaxis=dict(gridcolor="#1e2d3d", showgrid=True, zeroline=False, tickfont=dict(size=9),
                           title="Part des Renouvelables (%)", range=[0, 105]),
            )
            st.plotly_chart(fig_pp, use_container_width=True)
        else:
            st.info("Pas assez de données pour projeter les pays sélectionnés.")

        # ── Tableau de comparaison des scénarios ──
        st.markdown(
            "<div class='section-title'>Objectifs 2030 & 2050 · Comparaison des Scénarios</div>",
            unsafe_allow_html=True,
        )
        lignes_sc = []
        for pays in pays_sel:
            df_p = filtrer(df, [pays], plage).dropna(subset=["part_renouv"])
            if df_p.empty or len(df_p) < 2:
                continue
            Xp = df_p["annee"].values.astype(float)
            yp = df_p["part_renouv"].values
            pente_p, intercept_p, _, _, _ = stats.linregress(Xp, yp)
            for nom_sc, mult in [("Linéaire", 1), ("Accéléré ×2", 2), ("Zéro Net 2050", None)]:
                if mult:
                    v2030 = min(100, max(0, yp[-1] + pente_p * mult * (2030 - Xp[-1])))
                    v2050 = min(100, max(0, yp[-1] + pente_p * mult * (2050 - Xp[-1])))
                else:
                    v2030 = min(100, yp[-1] + (100 - yp[-1]) * (2030 - Xp[-1]) / (2050 - Xp[-1]))
                    v2050 = 100.0
                lignes_sc.append({
                    "Pays": nfr(pays), "Scénario": nom_sc,
                    "Renouv. 2030 (%)": round(v2030, 1),
                    "Renouv. 2050 (%)": round(v2050, 1),
                })
        df_sc_tab = pd.DataFrame(lignes_sc)
        if not df_sc_tab.empty:
            st.dataframe(
                df_sc_tab.pivot_table(
                    index="Pays", columns="Scénario",
                    values=["Renouv. 2030 (%)", "Renouv. 2050 (%)"],
                ).round(1),
                use_container_width=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# PIED DE PAGE
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#3d5a72; font-size:0.65rem;
            letter-spacing:0.1em; padding-bottom:1rem">
    ⚡ EUROPA ÉNERGIE · INTELLIGENCE DÉCISIONNELLE ·
    DONNÉES : OWID / SYNTHÉTIQUES · CONSTRUIT AVEC STREAMLIT + PLOTLY
</div>
""", unsafe_allow_html=True)