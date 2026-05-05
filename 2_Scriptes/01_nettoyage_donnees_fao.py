#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Nettoyage de code Python pour une application Streamlit

Ce script propose un exemple de nettoyage des données FAOSTAT
en vue de leur utilisation dans une application Streamlit.
Il inclut des fonctions pour le chargement, le nettoyage
et l'enregistrement des données.

À considérer comme un support pédagogique,
pour lequel un template formaté sera fourni.

Auteur : Gary Lynam
Date: 2026-02-24"""

from __future__ import annotations
import argparse, re, sys
from pathlib import Path
import pandas as pd
import re as re

#-----------------------------------------------------#
### Section 1: Charger et comprendre les données    ###
#-----------------------------------------------------#

# Charger les données à partir du fichier CSV
file_path = Path("1_Donnees/Emissions_livestock_E_Europe_NOFLAG.csv")
df = pd.read_csv(file_path)

# Comprendre ce qu'on a chargé        
print("Lignes et colonnes:", df.shape)  # (lignes, colonnes)
print("Noms des colonnes:",df.columns)     # noms des colonnes
print(df.head(3))     # 3 premières lignes des colonnes        

# Contrôles de qualité de base sur le DataFrame chargé pour identifier les problèmes potentiels dans les données avant de les nettoyer.
missing = df.isna().sum().sort_values(ascending=False)
print(missing.head(10))
print("Doublons:", df.duplicated().sum())

# On voit que les données sont dans un format "wide" avec des colonnes pour chaque année (ex: "Y1990", "Y1991", etc.).
# Identifier les colonnes années d'intérêt (ici, les colonnes qui correspondent à des années, par exemple "Y1990", "Y1991", etc.)
year_cols = [c for c in df.columns if re.fullmatch(r"Y\d{4}", c)]
print(year_cols[:5], "...", year_cols[-5:])


#-------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------#
### Section 2: Transformer les données - Wide à Long  ###
#-------------------------------------------------------#

# Ensuite on va changer le format du df en format long, pour faciliter les analyses et visualisations ultérieures.
# On utilise la fonction melt de pandas pour transformer les colonnes d'années en une seule colonne "Year" et les valeurs correspondantes dans une colonne "Value"
id_cols = [c for c in df.columns if c not in year_cols]

df_long = df.melt(
    id_vars=id_cols,
    value_vars=year_cols,
    var_name="Annee",
    value_name="Valeur"
)

df_long["Annee"] = df_long["Annee"].str[1:].astype(int)

print(df_long.head(3))

# Convertir la colonne "Valeur" en numérique, en gérant les erreurs de conversion (par exemple, les valeurs non numériques seront converties en NaN)
df_long["Valeur"] = pd.to_numeric(df_long["Valeur"], errors="coerce")

# Ensuite, on va nettoyer les colonnes de texte en supprimant les espaces inutiles et en s'assurant que les types de données sont corrects.
text_cols = ["Area", "Item", "Element", "Unit", "Source"]
for col in text_cols:
    if col in df_long.columns:
        df_long[col] = df_long[col].astype("string").str.strip()


#-------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------#
### Section 3: Merger les metadonnées géographiques   ###
#-------------------------------------------------------#

# Merger les données avec un autre DataFrame de métadonnées, si nécessaire. Par exemple, si vous avez un DataFrame de métadonnées qui contient des informations supplémentaires sur les zones géographiques ou les éléments, vous pouvez le fusionner avec votre DataFrame principal pour enrichir vos données.
# On voit que les données de notre df viennent de la FAO, et que les zones géographiques sont codées par des codes ISO. On peut créer un DataFrame de métadonnées pour faire le lien entre les codes ISO et les noms des zones géographiques.

# Le format de la colonne Area code (M49) ne matche pas celui de la colonne country-code du df_iso49, 
# il faut les harmoniser avant de faire le merge. 

# Charger les données à partir du fichier CSV
file_path_iso49 = Path("1_Donnees/ISO_regions_M49.csv")
df_iso49 = pd.read_csv(file_path_iso49)

print(df_long[["Area Code (M49)"]].head()) # Afficher uniquement ces colonnes (en-têtes + aperçu)
print(df_iso49[["country-code"]].head())

# 1) Nettoyer df_long : "'008" -> "008"
#    - On garde uniquement les chiffres
#    - On force sur 3 caractères avec des zéros à gauche (format M49)
df_long["Area Code (M49)"] = (
    df_long["Area Code (M49)"]
    .astype(str)
    .str.replace(r"\D", "", regex=True)   # ne garder que les chiffres (on enleve tout caractère qui n'est pas un chiffre.)
    .str.zfill(3)                        # ex: 8 -> "008"
)

# 2) Nettoyer df_iso49 : 8 -> "008"
#    - On convertit en numérique (les valeurs invalides deviennent NaN)
#    - On passe en entier nullable (Int64), puis en texte
#    - On applique le même padding à 3 chiffres
df_iso49["country-code"] = (
    pd.to_numeric(df_iso49["country-code"], errors="coerce")
    .astype("Int64")                      # entier nullable (gère les NaN)
    .astype(str)
    .replace("<NA>", pd.NA)               # éviter la chaîne "<NA>"
    .str.zfill(3)
)

print(df_long[["Area Code (M49)"]].head())
print(df_iso49[["country-code"]].head())


# 3) Fusion (merge) sur les codes harmonisés
df_merged = df_long.merge(
    df_iso49,
    left_on="Area Code (M49)",
    right_on="country-code",
    how="left",
    validate="m:1"                        # optionnel : plusieurs lignes df_long -> 1 ligne df_iso49
)
print(df_merged.head(3))     # 3 premières lignes des colonnes        

#####################################
# Contrôles de qualité après le merge
#####################################

# 1) Taux de correspondance (combien de lignes df_long ont trouvé un match ?)
match_rate = df_merged["country-code"].notna().mean()
print(f"Taux de match: {match_rate:.2%} ({df_merged['country-code'].notna().sum()}/{len(df_merged)})")

# 2) Quels codes M49 n'ont PAS trouvé de correspondance ?
unmatched_codes = (
    df_merged.loc[df_merged["country-code"].isna(), "Area Code (M49)"]
    .dropna()
    .unique()
)
print("Nombre de codes non appariés:", len(unmatched_codes))
print("Exemples de codes non appariés:", unmatched_codes[:20])

# 3) Vérifier qu'on n'a pas de doublons côté df_iso49 (sinon le merge peut dupliquer des lignes)
dup_iso = df_iso49["country-code"].duplicated().sum()
print("Doublons dans df_iso49['country-code']:", dup_iso)

# 4) Vérifier que le nombre de lignes n'a pas augmenté (signe classique d'un many-to-many accidentel)
print("Lignes df_long:", len(df_long))
print("Lignes df_merged:", len(df_merged))

# 5) Contrôle aléatoire: afficher quelques lignes mergées pour inspection visuelle
cols_check = ["Area Code (M49)", "country-code"]
# + ajoute ici une ou deux colonnes "nom de pays" si elles existent dans df_iso49
print(df_merged[cols_check].sample(10, random_state=42))


#-------------------------------------------------------------------------------------------------------------------------
#------------------------------------------#
### Section 4: Imposer la modèle Gaea21  ###
#------------------------------------------#

# Maintenant on veut mettre en place notre modele des données pour l'appli Streamlit, en renommant les colonnes pour qu'elles soient plus claires et en réorganisant les colonnes dans un ordre logique.
# Créer un nouveau DataFrame avec les nouvelles colonnes, en remplissant les colonnes existantes et en laissant les autres vides ou avec des valeurs par défaut
new_columns = ["Source","Source lien","Source date","Projet","Sous-projet","Dimension","Sous-dimension","Sous-sous dimension",
    "Indicateur","Valeur","Unite","Categorie 1","Categorie 2","Categorie 3","Area 1","Area 2","Area 3","Area 1 Original","Area 2 Original","Area 3 Original",
    "Annee","Mois","Jour"]
df_new = pd.DataFrame(index=df_merged.index, columns=new_columns)

df_new["Source"] = df_merged["Source"]
df_new["Area 1"] = df_merged["region"]
df_new["Area 1 Original"] = df_merged["region"]
df_new["Area 2"] = df_merged["sub-region"]
df_new["Area 2 Original"] = df_merged["sub-region"]
df_new["Area 3"] = df_merged["name"]
df_new["Area 3 Original"] = df_merged["Area"]
df_new["Categorie 1"] = df_merged["Item"]
df_new["Indicateur"] = df_merged["Element"]
df_new["Unite"] = df_merged["Unit"]
df_new["Annee"] = df_merged["Annee"]
df_new["Valeur"] = df_merged["Valeur"]

# Remplir les colonnes de métadonnées avec des valeurs constantes ou par défaut
SOURCE_LIEN = "https://www.fao.org/faostat/en/#data"
SOURCE_DATE = pd.to_datetime("24/02/2026", dayfirst=True)  # datetime64[ns]
df_new["Source lien"] = SOURCE_LIEN
df_new["Source date"] = SOURCE_DATE
df_new["Projet"] = "Statistiques"
df_new["Sous-projet"] = "Trends"
df_new["Dimension"] = "Agriculture-Durable"
df_new["Sous-dimension"] = "Livestock"
df_new["Sous-sous dimension"] = "Emissions"

# Nettoyer toutes les colonnes texte de df_new (strip des espaces/caractères invisibles)
for col in df_new.select_dtypes(include="object").columns:
    df_new[col] = df_new[col].astype(str).str.strip()

print("Noms des colonnes:",df_new.columns)     # noms des colonnes nouvelles
print(df_new.head(3))     # 3 premières lignes des colonnes nouvelles

# Les données de FAOSAT a des pays qui n'existe plus. Alors, on va lister des pays (valeurs) 
# présents dans "Area 3 Original" mais absents de "Area 3"

# valeurs uniques non-nulles
orig = set(df_new["Area 3 Original"].dropna().astype(str).str.strip().unique())
new = set(df_new["Area 3"].dropna().astype(str).str.strip().unique())  
missing_in_area3 = sorted(orig - new)

print(f"Nb de valeurs de 'Area 3 Original' absentes de 'Area 3' : {len(missing_in_area3)}")
print(missing_in_area3)

# Maintenant on va filtrer les lignes avec les pays plus existants, en se basant sur la colonne "Area 3 Original".
# On peut décider de les garder ou de les enlever selon l'objectif de l'analyse. 
pays_enlever = ['Belgium-Luxembourg', 'Czechoslovakia', 'Serbia and Montenegro', 'USSR', 'Yugoslav SFR']
df_new = df_new[~df_new["Area 3 Original"].isin(pays_enlever)].copy()

# Vérification : s'assurer que le filtre a bien fonctionné
still_present = df_new["Area 3 Original"].isin(pays_enlever).sum()
print(f"Lignes restantes à enlever: {still_present}")  # doit afficher 0

#-------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------#
### Section 4b: Garder les indicateurs pertinents   ###
#-----------------------------------------------------#

# Maintenant, on va filtrer les indicateurs pour ne garder que ceux qui sont pertinents pour notre application Streamlit. 
# Par exemple, on peut décider de ne garder que les indicateurs liés aux émissions de gaz à effet de serre (GES) provenant du secteur de l'élevage.

# Garder uniquement ces indicateurs (dans la colonne "indicateur")
keep = [
    "Stocks",
    "Livestock total (Emissions N2O)",
    "Livestock total (Emissions CH4)",
]
df_filtered = df_new[df_new["Indicateur"].isin(keep)].copy()

#----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------#
### Section 4c: Organiser les categories pour le modèle   ###
#-----------------------------------------------------------#

# Ensuite, pour ces données on veut modifier les categories d'unités pour les rendre plus compréhensibles. 

# d'abord on va regarder les valeurs uniques de la colonnes "categorie 1" pour identifier les différentes unités présentes
print("Unités présentes dans 'Categorie 1':", df_filtered["Categorie 1"].unique())  

"""
              'Asses',            'Buffalo',      'Cattle, dairy',
  'Cattle, non-dairy', 'Chickens, broilers',   'Chickens, layers',
              'Ducks',              'Goats',             'Horses',
  'Mules and hinnies',              'Sheep',    'Swine, breeding',
      'Swine, market',            'Turkeys',        'All Animals',
             'Cattle',           'Chickens',    'Mules and Asses',
      'Poultry Birds',    'Sheep and Goats',              'Swine',
             'Camels',  'Camels and Llamas'  
             """

CATEGORIE1 = ["All Animals"]
CATEGORIE2 = [
    "Camels and Llamas", "Cattle", "Mules and Asses", "Poultry Birds",
    "Sheep and Goats", "Swine"
]
CATEGORIE3 = [
    "Asses", "Buffalo", "Camels", "Swine, breeding", "Swine, market", "Turkeys",
    "Cattle, dairy", "Cattle, non-dairy", "Chickens, broilers", "Chickens, layers",
    "Ducks", "Goats", "Horses", "Sheep"
]
EXCLUDE = ["Chickens", "Mules and hinnies", "(blank)", ""]

# Avant de comencer, on va enlever les groups qu'on ne veut pas (ex: "Chickens", "Mules and hinnies", "(blank)", "")
df_filtered = df_filtered[~df_filtered["Categorie 1"].isin(EXCLUDE)].copy()

# On peut ensuite appliquer ces catégories à notre DataFrame filtré, en créant de nouvelles colonnes 
# "Categorie 1", "Categorie 2" et "Categorie 3" en fonction des valeurs de la colonne "Categorie 1" d'origine.

# Ici on crée une fonction qui va vérifier à quelle catégorie appartient chaque ligne, 
# et remplir les nouvelles colonnes en conséquence.
def categorize(row):        
    if row["Categorie 1"] in CATEGORIE1:
        return pd.Series([row["Categorie 1"], pd.NA, pd.NA])
    elif row["Categorie 1"] in CATEGORIE2:
        return pd.Series([pd.NA, row["Categorie 1"], pd.NA])
    elif row["Categorie 1"] in CATEGORIE3:
        return pd.Series([pd.NA, pd.NA, row["Categorie 1"]])
    else:
        return pd.Series([pd.NA, pd.NA, pd.NA])


df_filtered[["Categorie 1", "Categorie 2", "Categorie 3"]] = df_filtered.apply(categorize, axis=1)

# Fusionner les trois colonnes de catégories (mutuellement exclusives) en une seule
df_filtered["Categorie_animal"] = (
    df_filtered[["Categorie 1", "Categorie 2", "Categorie 3"]]
      .bfill(axis=1)
      .iloc[:, 0]
)


# Supprimer les lignes où Categorie_animal est vide ou Source != "FAO TIER 1"
df_filtered = df_filtered[
    df_filtered["Categorie_animal"].notna() &
    (df_filtered["Categorie_animal"].str.strip() != "") &
    (df_filtered["Source"] == "FAO TIER 1")
]

print(df_filtered[["Categorie_animal"]].head(10))

#---------------------------------------------------------------------------------------------
#------------------------------------------------------#
### Section 5: Verifications finales et sauvegarde   ###
#------------------------------------------------------#

# Vérifs finales (cohérence) des données avant de les sauvegarder dans un nouveau fichier CSV, 
# prêt à être utilisé dans l'application Streamlit.

print("Valeurs invalides:", df_filtered["Valeur"].isna().sum())
print("Année min/max:", df_filtered["Annee"].min(), df_filtered["Annee"].max())

neg = (df_filtered["Valeur"] < 0).sum()
print("Valeurs négatives:", neg)

# Si on trouve des valeurs invalides, on peut décider de les remplacer par 0 ou de les supprimer, selon le contexte et l'objectif de l'analyse.
df_filtered["Valeur"] = df_filtered["Valeur"].fillna(0)
print("Valeurs invalides:", df_filtered["Valeur"].isna().sum())  # doit afficher 0

# Enfin, on peut sauvegarder le DataFrame nettoyé dans un nouveau fichier CSV, prêt à être mettre dans notre base de données centralisée.
output_path = Path("1_Donnees/Emissions_livestock_E_Europe_PROPRE.csv")
df_filtered.to_csv(output_path, index=False)
print(f"DataFrame nettoyé sauvegardé dans: {output_path}")