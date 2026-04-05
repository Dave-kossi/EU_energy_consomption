# ⚡ Europa Énergie — Tableau de Bord d'Intelligence Décisionnelle

Un tableau de bord interactif pour analyser la transition énergétique en Europe, construit avec Streamlit et Plotly. Ce projet fournit une vue stratégique complète de la consommation énergétique européenne, en se concentrant sur la décarbonation, les renouvelables et les projections futures.

## 🌟 Fonctionnalités Principales

### 📊 Vue d'Ensemble
- **Mix énergétique européen** : Répartition des sources d'énergie (fossiles, nucléaires, renouvelables)
- **Évolution temporelle** : Suivi des parts de renouvelables, fossiles et nucléaires
- **Comparaison par pays** : Analyse des pays sélectionnés sur une période donnée
- **Indicateurs clés** : Métriques essentielles avec deltas de progression

### 🚀 Analyse de la Vitesse de Transition
- **Vitesse glissante sur 10 ans** : Mesure du rythme de décarbonation (points de pourcentage/an)
- **TCAC solaire et éolien** : Taux de croissance annuel composé depuis 2010
- **Classement des décarbonateurs** : Pays les plus rapides dans leur transition
- **Corrélations** : Liens entre vitesse de transition et intensité carbone

### 🎯 Intelligence par Clusters de Pays
- **Classification automatique** : Regroupement des pays par profil énergétique
  - 🌿 Pionniers Verts : >60% renouvelables
  - ⚛️ Champions Nucléaires : >40% nucléaire
  - 🔄 En Transition : Profil intermédiaire
  - 🏭 Dépendants Fossiles : Forte intensité carbone
- **Migration 2010→aujourd'hui** : Évolution des positions des pays
- **Profils radar** : Comparaison multicritère normalisée

### ⚖️ Matrice de Décision
- **Scoring multicritère** : Évaluation des pays sur 5 dimensions
  - Ambition (part renouvelables)
  - Vitesse de transition
  - Croissance solaire
  - Faible risque fossile
  - Faible intensité carbone
- **Radar multicritère** : Profil visuel par pays
- **Matrice risque/opportunité** : Priorisation des interventions
- **Recommandations politiques** : Guide pour l'allocation des fonds

### 📈 Projections Prospectives
- **Scénarios multiples** :
  - 📈 Tendance Linéaire : Continuation des tendances actuelles
  - 🚀 Accéléré (×2) : Doublement de la vitesse de transition
  - 🎯 Zéro Net 2050 : Atteinte des objectifs climatiques
  - 📉 Stagnation : Arrêt de la progression
- **Intervalles de confiance** : Projections avec IC à 95%
- **Point de croisement** : Année où renouvelables dépassent fossiles
- **Projections par pays** : Trajectoires individuelles jusqu'en 2050

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip

### Installation des dépendances
```bash
pip install streamlit plotly scipy pandas numpy
```

### Données
Le projet utilise les données OWID (Our World in Data) pour l'énergie européenne. Placez le fichier `owid-energy-data-europe.json` dans le même dossier que `Energy_App.py`.

Si le fichier n'est pas présent, l'application génère automatiquement des données synthétiques réalistes basées sur des profils pays par pays.

## 🚀 Utilisation

### Lancement de l'application
```bash
streamlit run Energy_App.py
```

L'application s'ouvrira dans votre navigateur par défaut.

### Configuration
- **Pays à analyser** : Sélectionnez les pays européens à inclure dans l'analyse
- **Fenêtre temporelle** : Définissez la période d'analyse (2000-2023 typiquement)
- **Scénario de projection** : Choisissez le scénario prospectif

## 📁 Structure du Projet

```
EU_energy_consomption/
├── Energy_App.py          # Application principale Streamlit
├── README.md              # Ce fichier
└── owid-energy-data-europe.json  # Données OWID (optionnel)
```

## 🎨 Thème et Design

- **Thème sombre industriel** : Interface adaptée à l'analyse de données énergétiques
- **Palette de couleurs** : Codes couleur par source d'énergie et cluster
- **Responsive** : Optimisé pour différentes tailles d'écran
- **Typographie monospace** : Lisibilité maximale pour les données techniques

## 📊 Sources de Données

- **OWID Energy Data** : Base de données ouverte sur l'énergie mondiale
- **Données synthétiques** : Génération procédurale réaliste en l'absence de données réelles
- **Métriques calculées** :
  - Parts énergétiques (renouvelables, fossiles, nucléaire)
  - Intensité carbone (gCO₂/kWh)
  - Émissions GES (Mt CO₂eq)
  - TCAC solaire/éolien
  - Vitesse de transition glissante

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Pushez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Our World in Data** pour les données énergétiques ouvertes
- **Streamlit** et **Plotly** pour les frameworks de visualisation
- **SciPy** pour les analyses statistiques

---

<div align="center">
⚡ <strong>EUROPA ÉNERGIE</strong> · INTELLIGENCE DÉCISIONNELLE · DONNÉES : OWID / SYNTHÉTIQUES · CONSTRUIT AVEC STREAMLIT + PLOTLY ⚡
</div>