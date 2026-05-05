#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Exemple de transformation des indicateurs pour une application Streamlit

Ce script propose un exemple de transformation des données FAOSTAT
en vue de leur utilisation dans une application Streamlit.

Auteur : Gary Lynam
Date: 2026-02-24"""

from __future__ import annotations
from ast import Global
import argparse, re, sys
from pathlib import Path
import pandas as pd
import re as re
import numpy as np

# Charger les données à partir du fichier CSV
file_path = Path("1_Donnees/Emissions_livestock_E_Europe_PROPRE.csv")
df = pd.read_csv(file_path)

#-------------------------------------------------------------------------------------------------------------------------
################################################################################
### Section 1: Filtrer les données pour les régions et categories d'intérêt  ###  
################################################################################

# On va créer des flags pour les différentes régions d'Europe, en utilisant des ensembles de pays pour chaque région.

EU = {"Austria","Belgium","Bulgaria","Croatia","Cyprus","Czechia","Czech Republic","Denmark","Estonia",
      "Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg",
      "Malta","Netherlands (Kingdom of the)","Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden"}

EEA_PLUS_UK = EU.union({"Iceland","Liechtenstein","Norway","United Kingdom of Great Britain and Northern Ireland","Switzerland"})

# Ajouter des colonnes de flags pour chaque région
df["region_EU"] = df["Area 3 Original"].isin(EU)
df["region_EUEEAUK"] = df["Area 3 Original"].isin(EEA_PLUS_UK)

#-------------------------------------------------------------------------------------------------------------------------

#######################################################################################
### Section 2: Créer des flags pour les différentes catégories d'animaux d'élevage  ###
#######################################################################################

# On va maintenant créer des colonnes flags (TRUE ou FALSE) pour les différentes niveau de catégories d'animaux d'élevage.
# On peut créer des ensembles de catégories d'animaux pour chaque niveau de classification, et dire
# Categorie 1 = "All Animals" si la catégorie d'origine est "All Animals", Categorie 2 = Aggregate et categorie 3 = Atomic sinon.

AGGREGATE_LIST   = ["Camels and Llamas","Cattle","Mules and Asses","Poultry Birds","Sheep and Goats","Swine"]
ATOMIC_LIST      = ["Asses","Buffalo","Camels","Swine, breeding","Swine, market","Turkeys",
                    "Cattle, dairy","Cattle, non-dairy","Chickens, broilers","Chickens, layers",
                    "Ducks","Goats","Horses","Sheep"]

df["is_all"] = df["Categorie 1"] == "All Animals"
df["is_aggregated"] = df["Categorie 2"].isin([*AGGREGATE_LIST])
df["is_atomic"] = df["Categorie 3"].isin([*ATOMIC_LIST])

# Vérification : les trois colonnes doivent exister
expected_flags = {"is_all", "is_aggregated", "is_atomic"}
missing = expected_flags.difference(df.columns)
if missing:
    raise KeyError(f"Colonnes manquantes : {', '.join(sorted(missing))}")

# Création vectorisée de la colonne categorie_type
df["categorie_type"] = np.select(
    condlist   = [df["is_all"], df["is_aggregated"], df["is_atomic"]],
    choicelist = ["All", "aggregated", "atomic"],
    default    = pd.NA           # même famille que les chaînes
)

# Fusionner les trois colonnes de catégories (mutuellement exclusives) en une seule
df["Categorie_animal"] = (
    df[["Categorie 1", "Categorie 2", "Categorie 3"]]  # sélection des colonnes sources
      .bfill(axis=1)                                   # propage la première valeur non nulle vers la gauche
      .iloc[:, 0]                                      # récupère ensuite cette valeur (colonne la plus à gauche)
)

# Supprimer les lignes où Categorie_animal est vide ou Source != "FAO TIER 1" (qui correspond à des données non fiables ou non pertinentes pour notre analyse)
df = df[
    df["Categorie_animal"].notna() & 
    (df["Categorie_animal"].str.strip() != "") &
    (df["Source"] == "FAO TIER 1")
]

# (optionnel) Supprimer les anciennes colonnes si elles ne sont plus nécessaires
df.drop(columns=["Categorie 1", "Categorie 2", "Categorie 3"], inplace=True)

#-------------------------------------------------------------------------------------------------------------------------

#################################################################################################################
### Section 3: Convertir les emissions de CH4 et N2O en equivalent de CO2 pour créer de nouveaux indicateurs  ###
#################################################################################################################

### Convertir les emissions en equivalent de CO2

# Global Warming Potential (GWP) valeurs pour methane (CH4) et nitrous oxide (N2O) sont 27.2 et 273. 
# Ces valeurs sont utilisées pour convertir les émissions de CH4 et N2O en équivalent CO2, afin de permettre une comparaison directe entre les différents gaz à effet de serre.)
GWP_CH4 = 27.2      # AR6 - GWP100  (Selon le Intergovernmental Panel on Climate Change (AR6) : 
GWP_N2O = 273       # AR6 - GWP100

# Colonnes d'identification (Area 3, Annee, Categorie 1, Categorie 2, Categorie 3)

# ===================================================================
# 1) CO2_eq depuis CH4
# ===================================================================

# On sélectionne uniquement les lignes dont la colonne "Indicateur"
# contient le texte "Emissions CH4".
# - str.contains(..., na=False) évite les erreurs si Indicateur contient des NaN.
# - .copy() est IMPORTANT : ça évite le fameux warning "SettingWithCopyWarning"
#   et ça garantit qu'on travaille sur une copie indépendante.
df_ch4 = df[df["Indicateur"].str.contains("Emissions CH4", na=False)].copy()

# Conversion CH4 -> CO2_eq
# On multiplie la valeur (ex: kt CH4) par le facteur GWP_CH4 pour obtenir du "CO2 équivalent".
df_ch4["Valeur"] = df_ch4["Valeur"] * GWP_CH4

# On renomme l'indicateur pour que ce soit clair que ce n'est plus du CH4 brut,
# mais du CH4 converti en CO2_eq.
df_ch4["Indicateur"] = "Livestock Emissions CH4 (CO2_eq)"

# Optionnel mais recommandé : si tu as une colonne "Unite", mets l'unité cohérente.
df_ch4["Unite"] = "kt CO2 eq"

# Vérification rapide : on imprime 5 premières lignes pour voir si tout va bien.
print("df_ch4:", df_ch4.head())


# ===================================================================
# 2) CO2_eq depuis N2O
# ===================================================================

# Même logique, mais pour N2O
df_n2o = df[df["Indicateur"].str.contains("Emissions N2O", na=False)].copy()

# Conversion N2O -> CO2_eq
df_n2o["Valeur"] = df_n2o["Valeur"] * GWP_N2O

# Renommage de l'indicateur
df_n2o["Indicateur"] = "Livestock Emissions N2O (CO2_eq)"

# Unité
df_n2o["Unite"] = "kt CO2 eq"

# Vérification
print("df_n2o:", df_n2o.head())


# ===================================================================
# 3) Ajouter ces nouveaux indicateurs au DataFrame original
# ===================================================================

# pd.concat empile des DataFrames "l'un en dessous de l'autre"
# ignore_index=True recrée un index propre (0..N-1) après concaténation.
df = pd.concat([df, df_ch4, df_n2o], ignore_index=True)

# Sauvegarde intermédiaire (optionnelle) : ton dataset avec les 2 nouveaux indicateurs CO2_eq
#output_path = Path("1_Donnees/Emissions_livestock_E_Europe_PROPRE_indicateur_int.csv")
#df.to_csv(output_path, index=False)
#print(f"DataFrame nettoyé sauvegardé dans: {output_path}")


# ===================================================================
# 4) Créer l'indicateur Total = CH4(CO2_eq) + N2O(CO2_eq)
# ===================================================================

# Liste des deux indicateurs qu'on veut sommer
gas_inds = [
    "Livestock Emissions N2O (CO2_eq)",
    "Livestock Emissions CH4 (CO2_eq)",
]

# On veut faire une somme "par groupe" (par pays, année, catégories, etc.)
# Donc il nous faut des colonnes clés de regroupement (= tout sauf Indicateur et Valeur).
#
# - Indicateur : c'est l'étiquette (CH4 vs N2O vs Total)
# - Valeur : c'est la variable numérique qu'on additionne
keys = [c for c in df.columns if c not in ["Indicateur", "Valeur"]]

# On isole uniquement les lignes CH4(CO2_eq) et N2O(CO2_eq)
gas = df[df["Indicateur"].isin(gas_inds)].copy()

# Ici on calcule la somme par groupe, MAIS on utilise transform("sum")
# plutôt que groupby().sum() :
# - transform("sum") renvoie une série de même longueur que "gas"
# - donc chaque ligne garde toutes ses autres colonnes (Area, Année, catégories, etc.)
# dropna=False : si certaines colonnes keys ont des NaN, elles sont quand même considérées
#               comme faisant partie d'un groupe (au lieu d'être exclues).
gas["Valeur_total"] = gas.groupby(keys, dropna=False)["Valeur"].transform("sum")

# Maintenant, "Valeur_total" est répétée sur les 2 lignes du groupe (CH4 et N2O).
# Pour créer UNE SEULE ligne "Total" par groupe :
# - drop_duplicates(subset=keys) garde la première ligne unique pour chaque groupe
# - on supprime l'ancienne colonne "Valeur" (qui était CH4 ou N2O)
# - on renomme "Valeur_total" en "Valeur"
total_rows = (
    gas.drop_duplicates(subset=keys, keep="first")
       .drop(columns=["Valeur"])
       .rename(columns={"Valeur_total": "Valeur"})
)

# On met le bon nom d'indicateur
total_rows["Indicateur"] = "Total Livestock Emissions (CO2 eq)"

# Très important : on remet le même ordre de colonnes que df,
# pour que concat fonctionne proprement et que le CSV soit cohérent.
total_rows = total_rows[df.columns]

# Vérification
print("total_rows:", total_rows.head())


# ===================================================================
# 5) Ajouter les lignes Total au dataset final
# ===================================================================

# On concatène df (original + CH4_CO2eq + N2O_CO2eq)
# avec total_rows (Total CO2eq)
df_out = pd.concat([df, total_rows], ignore_index=True)


# ===================================================================
# 6) Traduction française des valeurs de données
# ===================================================================

# Les valeurs de la colonne "Indicateur" proviennent de la FAO en anglais.
# On les traduit ici pour que les tableaux de bord et exports soient en français.
TRADUCTION_INDICATEURS = {
    "Stocks":                              "Effectifs",
    "Livestock total (Emissions CH4)":     "Cheptel total (Emissions CH4)",
    "Livestock total (Emissions N2O)":     "Cheptel total (Emissions N2O)",
    "Livestock Emissions CH4 (CO2_eq)":    "Emissions CH4 du cheptel (CO2 eq.)",
    "Livestock Emissions N2O (CO2_eq)":    "Emissions N2O du cheptel (CO2 eq.)",
    "Total Livestock Emissions (CO2 eq)":  "Emissions totales du cheptel (CO2 eq.)",
}

# Les noms d'animaux proviennent également de la FAO en anglais.
TRADUCTION_CATEGORIES = {
    "All Animals":       "Tous les animaux",
    "Cattle":            "Bovins",
    "Poultry Birds":     "Volailles",
    "Sheep and Goats":   "Ovins et caprins",
    "Swine":             "Porcins",
    "Camels and Llamas": "Camelides",
    "Mules and Asses":   "Mulets et anes",
    "Asses":             "Anes",
    "Buffalo":           "Buffles",
    "Camels":            "Chameaux",
    "Cattle, dairy":     "Bovins laitiers",
    "Cattle, non-dairy": "Bovins non-laitiers",
    "Chickens, broilers":"Poulets de chair",
    "Chickens, layers":  "Poules pondeuses",
    "Ducks":             "Canards",
    "Goats":             "Caprins",
    "Horses":            "Chevaux",
    "Sheep":             "Ovins",
    "Swine, breeding":   "Porcins reproducteurs",
    "Swine, market":     "Porcins charcutiers",
    "Turkeys":           "Dindes",
}

# .replace() remplace chaque valeur trouvée dans le dictionnaire.
# Les valeurs absentes du dictionnaire sont laissées intactes.
df_out["Indicateur"]      = df_out["Indicateur"].replace(TRADUCTION_INDICATEURS)
df_out["Categorie_animal"] = df_out["Categorie_animal"].replace(TRADUCTION_CATEGORIES)

print("Traductions appliquées.")
print("Indicateurs uniques :", sorted(df_out["Indicateur"].unique()))
print("Catégories uniques   :", sorted(df_out["Categorie_animal"].dropna().unique()))


# ===================================================================
# 7) Sauvegarde finale
# ===================================================================

output_path_filter = Path("1_Donnees/Emissions_livestock_E_Europe_PROPRE_indicateur.csv")
df_out.to_csv(output_path_filter, index=False)
print(f"DataFrame final sauvegardé dans: {output_path_filter}")