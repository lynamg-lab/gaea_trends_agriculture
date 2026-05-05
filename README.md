# Modèle Streamlit GAEA — Scripts & Utilisation

> Ce dépôt contient des **modèles Streamlit** destinés à la formation des stagiaires (FR/EN).
> Les scripts du dossier `2_Scriptes/` peuvent évoluer ; ce README reste valide même quand de nouveaux
> fichiers sont ajoutés ou renommés.

---

## Dossiers

```
.
├─ 1_Donnees/                        # Données (sources & préparées)
│  ├─ Emissions_livestock_E_Europe_NOFLAG.csv
│  ├─ Emissions_livestock_E_Europe_PROPRE.csv
│  ├─ Emissions_livestock_E_Europe_PROPRE_indicateur.csv
│  ├─ livestock_PREPARED_total_stocks.csv
│  ├─ ISO_regions_M49.csv
│  └─ emissions_exemple.csv
├─ 2_Scriptes/                       # Scripts de traitement et application Streamlit
│  ├─ 01_nettoyage_donnees_fao.py
│  ├─ 01b_transformation_indicateurs.py
│  └─ 02_streamlit_tableaudebord_agriculture.py
├─ requirements.txt
└─ README.md
```

### À propos de `2_Scriptes/`

Le dossier **2_Scriptes/** contient les scripts de traitement des données et l'application Streamlit :
- `01_nettoyage_donnees_fao.py` : nettoyage et préparation des données brutes FAO.
- `01b_transformation_indicateurs.py` : transformation et calcul des indicateurs.
- `02_streamlit_tableaudebord_agriculture.py` : tableau de bord Streamlit principal (FR).

Chaque script modele suit la même logique d'interface :
- Onglet **Tendances temporelles** (courbes) — export CSV.
- Onglet **Composition** (camembert Total_CO2e) — export CSV.
- Onglet **Carte** (Total_CO2e Europe, groupe `All`) — export CSV (Plotly requis).

---

## Installation

Prérequis : Python 3.9+

```bash
pip install -r requirements.txt
```
Contenu recommandé pour `requirements.txt` :

```
streamlit>=1.36
pandas>=2.0
altair>=5.0
plotly>=5.0  # requis pour l'onglet Carte
```

---

## Schéma du CSV « préparé » (format long)

Colonnes **obligatoires** :

| Colonne          | Type   | Description                                                   |
|------------------|--------|---------------------------------------------------------------|
| `Area`           | str    | Pays ou zone                                                  |
| `Item`           | str    | Catégorie / item (ex. « Cattle », « Dairy Cattle »)           |
| `Year`           | int    | Année                                                         |
| `Metric`         | str    | `Total_CO2e` ou `Stocks` (périmètre du modèle)                |
| `Value`          | float  | Valeur numérique                                              |
| `item_kind`      | str    | `All` \| `aggregated` \| `atomic`                             |
| `region_europe`  | bool   | True si le pays est en Europe                                 |
| `region_EU`      | bool   | True si le pays est dans l'UE                                 |
| `region_EUEEAUK` | bool   | True si UE/EEE/R.-Uni                                         |

---

## Lancer l'application

Depuis la racine du dépôt (n'oubliez pas de définir votre chemin vers ce dossier) :

```bash
streamlit run 2_Scriptes/02_streamlit_tableaudebord_agriculture.py
```

Sous Windows (PowerShell) :
```powershell
py -m streamlit run .\2_Scriptes\02_streamlit_tableaudebord_agriculture.py
```

Par défaut, le script lit un chemin `DEFAULT_PREPARED`. Si le fichier n'existe pas,
**uploadez** un CSV via l'interface.

---

## Guide d'utilisation rapide

1. **Métrique & période** : choisissez `Total_CO2e` ou `Stocks`, puis la plage d'années.
2. **Groupe d'items** : `Tous` (exclusif), `Agrégés`, ou `Atomiques`.
3. **Mode d'affichage** : total **régional** (Europe/UE/UE+EEE+R.-Uni) ou **Pays**.
4. **Pays** : *Top 10* (option « Ajouter la Suisse ») ou *Personnalisé* (max 12).
5. **Onglets** : courbes / camembert / carte — **tous exportables en CSV**.

---

## Adapter à une autre thématique

- **Dupliquez** un script existant dans `2_Scriptes/` et renommez-le (ex. `transport_template_fr.py`).  
- Mettez à jour `DEFAULT_PREPARED` vers votre CSV au **même schéma**.  
- Ajustez `st.title(...)` et, si besoin, `metric_unit_label(...)` pour de nouvelles métriques.

---

## Checklist

- Le curseur d'années couvre la plage `Year` de votre CSV.  
- Le groupe d'items choisi contient des valeurs pour l'année ciblée.  
- Plotly installé pour l'onglet **Carte** ; noms pays compatibles (ex. UK → `United Kingdom`).

---

## Dépannage

- « CSV préparé introuvable » : corrigez `DEFAULT_PREPARED` ou uploadez un CSV.  
- Camembert vide : vérifier la présence de `item_kind == aggregated`.  
- Carte vide : valider `region_europe == True` et la présence de `Total_CO2e` pour `All`.  
- Purger cache : menu Streamlit → *Clear cache* (utilise `@st.cache_data`).

---

- Crédits : Équipe Statistiques (GAEA) — modèle commenté pour stagiaires (FR/EN).
