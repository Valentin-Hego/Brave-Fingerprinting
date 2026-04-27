import hashlib
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import Counter


# PARTIE 1 : CHARGEMENT ET PARSING DU DATASET (FPStalker)
# Le dataset FPStalker est fourni sous forme de dump SQL dans un .txt
# On utilise des expressions régulières et une fonction maison pour extraire les données proprement sans avoir besoin de monter une base MySQL

def parser_ligne_sql(ligne):
    """Sépare les valeurs d'une ligne SQL en gérant les guillemets et les virgules"""
    result = []
    valeur_actuelle = []
    dans_chaine = False
    echappement = False
    guillemets = None

    for char in ligne:
        if echappement:
            valeur_actuelle.append(char)
            echappement = False
        elif char == '\\' and dans_chaine:
            valeur_actuelle.append(char)
            echappement = True
        elif char in ("'", '"') and not dans_chaine:
            dans_chaine = True
            guillemets = char
        elif char == guillemets and dans_chaine:
            dans_chaine = False
            guillemets = None
        elif char == ',' and not dans_chaine:
            val = ''.join(valeur_actuelle).strip()
            result.append(None if val.upper() == 'NULL' else val)
            valeur_actuelle = []
        else:
            valeur_actuelle.append(char)

    val = ''.join(valeur_actuelle).strip()
    result.append(None if val.upper() == 'NULL' else val)
    return result

def charger_dataset(chemin_fichier):
    lignes_donnees = []
    colonnes = None

    # On cherche les colonnes dans la requête INSERT INTO
    motif_col = re.compile(r'INSERT INTO `extensionDataScheme` \((.+?)\) VALUES', re.DOTALL)
    # On cherche le contenu entre les parenthèses des valeurs
    motif_val = re.compile(r'\((.+?)\)(?:,\s*\n|\s*;)', re.DOTALL)

    with open(chemin_fichier, 'r', encoding='utf-8', errors='replace') as f:
        contenu = f.read()

    match_col = motif_col.search(contenu)
    if match_col:
        colonnes = [c.strip().strip('`') for c in match_col.group(1).split(',')]

    for match in motif_val.finditer(contenu):
        ligne_brute = match.group(1)
        valeurs = parser_ligne_sql(ligne_brute)
        if colonnes and len(valeurs) == len(colonnes):
            lignes_donnees.append(valeurs)

    df = pd.DataFrame(lignes_donnees, columns=colonnes)
    print(f"[Dataset] {len(df)} empreintes chargées avec {len(df.columns)} attributs.")
    return df



# PARTIE 2 : simulation de la protection brave  : uniformisation
# le but : implémenter la logique "make Brave instances look as similar as possible".
# Pour cela, on modifie les attributs les plus discriminants (Canvas, WebGL, etc.) 
# en leur donnant une valeur générique commune à tous les utilisateurs.

HASH_BLOQUE = '0' * 40  # Valeur factice pour remplacer les hashs bloqués

def simuler_uniformisation_brave(df):
    """Applique les règles de protection Brave sur le dataset."""
    df_brave = df.copy()
    print(f"\n[Protection] Application des règles d'uniformisation Brave sur {len(df_brave)} empreintes...")

    for index, row in df.iterrows():
        # APIs Graphiques (Canvas et WebGL bloqués ou spoofés)
        df_brave.at[index, 'canvasJSHashed'] = HASH_BLOQUE
        df_brave.at[index, 'webGLJsHashed'] = HASH_BLOQUE
        df_brave.at[index, 'vendorWebGLJS'] = "Google Inc." # Tout le monde a ce vendor
        df_brave.at[index, 'rendererWebGLJS'] = "ANGLE"     # Tout le monde a ce renderer

        # Plugins
        df_brave.at[index, 'pluginsJS'] = ""
        df_brave.at[index, 'pluginsJSHashed'] = HASH_BLOQUE

        # langue (On ne garde que la langue principale sans le poids d'acceptation)
        langue = str(row.get('languageHttp', ''))
        if langue:
            # Eex: "fr-FR,fr;q=0.9" -> on garde juste "fr-FR"
            df_brave.at[index, 'languageHttp'] = langue.split(',')[0].split(';')[0].strip()

        # polices (Énumération bloquée)
        df_brave.at[index, 'fontsFlashHashed'] = HASH_BLOQUE

        # résolution d'écran Arrondie
        resolution = str(row.get('resolutionJS', ''))
        if 'x' in resolution:
            try:
                largeur, hauteur = map(int, resolution.lower().replace(' ', '').split('x'))
                largeur_arrondie = int(np.ceil(largeur / 100) * 100)
                hauteur_arrondie = int(np.ceil(hauteur / 100) * 100)
                df_brave.at[index, 'resolutionJS'] = f"{largeur_arrondie}x{hauteur_arrondie}"
            except ValueError:
                pass # Si le format est bizarre, on ignore

    print("[Protection] Uniformisation terminée.")
    return df_brave



# PARTIE 3 : METRIQUES D'EVALUATION (UNICITÉ ET ENTROPIE)

# Attributs classiquement utilisés pour le fingerprinting
ATTRIBUTS_FP = [
    'userAgentHttp', 'languageHttp', 'encodingHttp', 'orderHttp',
    'platformJS', 'timezoneJS', 'resolutionJS', 'dntJS',
    'cookiesJS', 'localJS', 'sessionJS',
    'pluginsJSHashed', 'canvasJSHashed', 'webGLJsHashed',
    'fontsFlashHashed', 'vendorWebGLJS', 'rendererWebGLJS',
    'adBlock', 'browserDetailed', 'browserVersion', 'osDetailed'
]

def calculer_metriques(df, contexte=""):
    """
    Calcule le pourcentage d'utilisateurs uniques et l'entropie de Shannon.
    """
    colonnes_utilisables = [c for c in ATTRIBUTS_FP if c in df.columns]
    donnees_fp = df[colonnes_utilisables].fillna('').astype(str)

    # Création d'un hash global pour chaque ligne pour identifier les empreintes exactes
    hash_empreintes = donnees_fp.apply(lambda row: hashlib.sha256('|'.join(row.values).encode()).hexdigest(), axis=1)
    
    compteur = Counter(hash_empreintes)
    total_empreintes = len(df)
    nombre_uniques = sum(1 for count in compteur.values() if count == 1)
    
    # Calcul de l'entropie de Shannon
    frequences = np.array(list(compteur.values())) / total_empreintes
    entropie = -np.sum(frequences * np.log2(frequences + 1e-12)) # 1e-12 évite le log(0)

    print(f"\n--- Résultats pour : {contexte} ---")
    print(f"Total empreintes : {total_empreintes}")
    print(f"Total uniques : {nombre_uniques} ({(nombre_uniques/total_empreintes)*100:.2f}%)")
    print(f"Entropie globale : {entropie:.3f} bits")

    return {
        'total': total_empreintes,
        'uniques': nombre_uniques,
        'pct_unique': (nombre_uniques/total_empreintes)*100,
        'entropie': entropie
    }


# PARTIE 4 : attaque par unicité résiduelle
# Stratégie de l'attaquant : 
# L'uniformisation de Brave empêche l'utilisation du Canvas, WebGL, etc.
# Mais un attaquant peut se rabattre sur les attributs passifs (User-Agent, Timezone, etc.)
# non protégés par Brave pour tenter de ré-identifier les utilisateurs

def attaque_empreinte_residuelle(df_uniformise):
    """Teste si l'on peut encore identifier des utilisateurs avec les attributs restants."""
    
    attributs_non_proteges = [
        'userAgentHttp', 'encodingHttp', 'platformJS', 'timezoneJS',
        'adBlock', 'browserVersion', 'osDetailed'
    ]
    
    colonnes_dispo = [c for c in attributs_non_proteges if c in df_uniformise.columns]
    donnees_restantes = df_uniformise[colonnes_dispo].fillna('').astype(str)
    
    resultats_attaque = []
    total = len(donnees_restantes)

    # Attaque sur chaque attribut individuellement
    for attribut in colonnes_dispo:
        compteur = Counter(donnees_restantes[attribut])
        uniques = sum(1 for c in compteur.values() if c == 1)
        resultats_attaque.append({
            'Cible': attribut,
            'Taux Unicité (%)': (uniques / total) * 100
        })

    # Attaque combinée avec tous les attributs non protégés
    empreintes_combinees = donnees_restantes.apply(lambda row: '|'.join(row.values), axis=1)
    uniques_combinees = sum(1 for c in Counter(empreintes_combinees).values() if c == 1)
    
    resultats_attaque.append({
        'Cible': 'COMBINAISON (Tous les attributs résiduels)',
        'Taux Unicité (%)': (uniques_combinees / total) * 100
    })

    df_resultats = pd.DataFrame(resultats_attaque).sort_values(by='Taux Unicité (%)', ascending=False)
    
    print("\n[Attaque] Analyse de l'unicité résiduelle :")
    print(df_resultats.to_string(index=False))
    return df_resultats




def exec(chemin_dataset):
    print("Démarrage de Brave Uniformisation")
    
    df_complet = charger_dataset(chemin_dataset)
    
    # On se concentre sur les utilisateurs Chrome pour avoir une base de comparaison saine
    df_base = df_complet[df_complet['browserDetailed'].str.contains('Chrome', case=False, na=False)].copy()
    if df_base.empty:
        df_base = df_complet.copy() # Fallback si la colonne n'est pas claire
    
    # situation de départ
    metriques_avant = calculer_metriques(df_base, "Chrome (Sans protection)")
    
    # Application de la défense Brave
    df_protege = simuler_uniformisation_brave(df_base)
    metriques_apres = calculer_metriques(df_protege, "Navigateur avec Uniformisation (Type Brave)")
    
    # Phase d'attaque
    resultats_attaque = attaque_empreinte_residuelle(df_protege)
    
    # VISUALISATION : Attributs les plus discriminants
    # On isole les attributs individuels ( retire la ligne de combinaison pour la clarté du graphique)
    df_plot = resultats_attaque[resultats_attaque['Cible'] != 'COMBINAISON (Tous les attributs résiduels)'].copy()
    # On trie dans l'ordre croissant pour avoir le plus discriminant en haut du graphique horizontal
    df_plot = df_plot.sort_values(by='Taux Unicité (%)', ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(df_plot['Cible'], df_plot['Taux Unicité (%)'], color='#3498db')
    
    plt.xlabel("Taux d'unicité résiduelle (%)")
    plt.title("Attributs les plus discriminants après l'uniformisation (Type Brave)")
    plt.xlim(0, max(100, df_plot['Taux Unicité (%)'].max() + 5)) # L'axe X va jusqu'à 100 ou s'adapte
    plt.grid(axis='x', linestyle='--', alpha=0.7)

    # Ajout des valeurs numériques à côté de chaque barre
    for bar in bars:
        largeur = bar.get_width()
        plt.text(largeur + 1, bar.get_y() + bar.get_height() / 2, 
                 f"{largeur:.2f}%", 
                 va='center', fontweight='bold', color='#2c3e50')
    
    plt.tight_layout()
    nom_graphique = 'attributs_discriminants.png'
    plt.savefig(nom_graphique)
    print(f"\nVisualisation graphique générée : {nom_graphique}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Erreur: pour le lancement cf readme")
    else:
        exec(sys.argv[1])