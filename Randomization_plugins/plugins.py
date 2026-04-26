import os
import hmac
import random
import string
import hashlib

import pandas as pd

from nltk import download
from nltk.corpus import words


# names = ['counter', 'id', 'addressHttp', 'creationDate', 'updateDate', 'endDate', 'userAgentHttp', 'acceptHttp', 'hostHttp', 'connectionHttp', 'encodingHttp', 'languageHttp', 'orderHttp', 'pluginsJS', 'platformJS', 'cookiesJS', 'dntJS', 'timezoneJS', 'resolutionJS', 'localJS', 'sessionJS', 'IEDataJS', 'canvasJS', 'webGLJs', 'fontsFlash', 'resolutionFlash', 'languageFlash', 'platformFlash', 'adBlock', 'vendorWebGLJS', 'rendererWebGLJS', 'octaneScore', 'sunspiderTime', 'pluginsJSHashed', 'canvasJSHashed', 'webGLJsHashed', 'fontsFlashHashed', 'osDetailed', 'browserDetailed', 'browserVersion']

# ---------------------------------------------------------
# EXTRACTION DU DATASET
# ---------------------------------------------------------
def get_plugins_from_file(filepath="../utils/database.sql"):
    """
    Parse un fichier en un jeu de données contenant des listes de plugins

    Paramètres:
    - filepath : String
        Chemin du fichier à charger
        "./utils/database.sql" par défaut

    Valeur de retour:
    - List
        Un jeu de données de listes de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]
        Jeu de données complet : [ [Liste de plugins], ... ]
    """

    if not os.path.exists(filepath):
        print(f"Fichier {filepath} introuvable.")
        return None
        
    print(f"Chargement et filtrage de {filepath} avec Pandas...")
    
    try:
        # Chargement brut: on utilise un séparateur nul (\x00) pour que 
        # Pandas lise chaque ligne du fichier SQL comme une seule colonne brute.
        df = pd.read_csv(filepath, sep='\x00', header=None, names=['ligne_brute'], engine='python', on_bad_lines='skip')

        # Extraction des listes de plugins contenues dans chaque ligne
        extractions = df['ligne_brute'].str.extract(r'(Plugin .*\. \',)')

        # On enlève les lignes vides
        extractions = extractions.dropna()

        if not extractions.empty:
            output = []
            # Pour chaque liste de plugins (chaque fingerprint) 
            for _, row in extractions.iterrows():
                
                # Nettoyage et parsing du dataset complet au format décrit dans la docstring 
                plugins = row[0][:-3]
                plugins = plugins.split(". ")

                tmp = []
                for plugin in plugins:
                    tmp.append(plugin[10:].split("; "))

                output.append(tmp)
            return output
           
    except Exception as e:
        print(f"Erreur lors du traitement Pandas : {e}")
        
    print("Aucun plugin trouvé.")
    return None

# ---------------------------------------------------------
# SIMULATION DE LA DEFENSE (BRAVE FARBLING)
# ---------------------------------------------------------
def lfsr_next(v):
    """
    Décale un entier. 

    Repris de l'implémentation du Brave Farbling. Code source d'origine :
    https://github.com/brave/brave-core/blob/master/third_party/blink/renderer/core/farbling/brave_session_cache.cc

    Paramètres :
    - v : Int
        L'entier à décaler

    Valeur de retour:
    - Int
        L'entier v décalé
    """

    return ((v >> 1) | (((v << 62) ^ (v << 61)) & (~(~0 << 63) << 62)));

def GenerateRandomString(seed, length, session_id, domain):
    """
    Génère un texte aléatoire d'une certaine taille, en utilisant hmac avec SHA256,
    et une graine, identifiant de session et nom de domaine spécifique

    Repris de l'implémentation du Brave Farbling. Code source d'origine :
    https://github.com/brave/brave-core/blob/master/third_party/blink/renderer/core/farbling/brave_session_cache.cc
    
    Paramètres :
    - seed : String
        La graine qui sera utilisée pour instancier la fonction de hashage
    - length : Int
        La longueur du texte à générer
    - session_id : String
        Le numéro de la session en cours
    - domain : String
        Le nom de domaine courant
    """

    kLettersForRandomStrings = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789. "
    kLettersForRandomStringsLength = 64
    
    # Génère un HMAC avec comme clé le contexte du Farbling (ici le numéro de la session et le nom de domaine du site)
    # et comme données la graine passée en paramètre
    context = f"{session_id}_{domain}".encode("utf-8")
    key = hmac.new(context, seed.encode("utf-8"), hashlib.sha256).hexdigest()

    v = key[:8]
    v = int(v, 16)
    
    value = ""
     
    for _ in range(0, length):
        c = kLettersForRandomStrings[v % kLettersForRandomStringsLength]
        value += c

        v = lfsr_next(v)
    
    return value

def farbling(plugins_list, session_id, domain):
    """
    Application du farbling par défaut sur une liste de plugins, avec un numéro de session et un nom de domaine donné
    Ici, la défense consiste simplement à ajouter 2 faux plugins, et à mélanger l'ordre dans la liste des plugins.

    Code source d'origine :
    https://github.com/brave/brave-core/pull/5989/changes/2794b2b4bbc32b487a8d6e125b0e568e9094550d#diff-e77a13fc2f4e540304b374a511e2c98c1ed23dd151c856659695695738286f90

    Paramètres:
    - plugins_list: List
        Une liste de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]

    Valeur de retour:
    - List
        La liste de plugins passée en paramètres avec 2 faux plugins supplémentaires,
        le tout mélangé aléatoirement
    """

    output = plugins_list.copy()
    
    # Génération des faux plugins
    fake_plugin_1_name = GenerateRandomString("PLUGIN_1_NAME", 8, session_id, domain)
    fake_plugin_1_filename = GenerateRandomString("PLUGIN_1_DESCRIPTION", 16, session_id, domain)
    fake_plugin_1_description = GenerateRandomString("PLUGIN_1_DESCRIPTION", 32, session_id, domain)

    fake_plugin_1 = [fake_plugin_1_name, fake_plugin_1_description, fake_plugin_1_filename]

    fake_plugin_2_name = GenerateRandomString("PLUGIN_2_NAME", 8, session_id, domain)
    fake_plugin_2_filename = GenerateRandomString("PLUGIN_2_DESCRIPTION", 16, session_id, domain)
    fake_plugin_2_description = GenerateRandomString("PLUGIN_2_DESCRIPTION", 32, session_id, domain)
    
    fake_plugin_2 = [fake_plugin_2_name, fake_plugin_2_description, fake_plugin_2_filename]

    # Ajout et mélange
    output.append(fake_plugin_1)
    output.append(fake_plugin_2)

    random.shuffle(output)

    return output 


def difference_plugins_list(plugin_list_1, plugin_list_2):
    """
    Calcule les plugins différents entre 2 listes.

    Paramètres:
    - plugin_list_1: List
        Une liste de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]
    - plugin_list_2: List
        Une liste de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]

    Valeurs de retour:
    - List
        Une liste des plugins différents
    """
    set1 = set([])
    set2 = set([])
    
    # Transformation des listes [nom, description, fichier] en une chaine de charactères
    # afin de pouvoir utiliser des ensembles (et particulièrement le non ensemliste)
    for elem in plugin_list_1:
        set1.add('; '.join(elem))
        for elem2 in plugin_list_2:
            set2.add('; '.join(elem2))

    diff = set1 - set2

    return diff

def compare_plugins_list(plugin_list_1, plugin_list_2):
    """
    Calcule la similarité entre deux listes de plugins. Les critères retenus sont:
    - Le nombre de différences entre les deux listes, 2 différences étant le nombre de 
      faux plugins ajoutés par le Farbling
    - La taille des éléments du plugin, un nom de 8 charactères, une description de 
      32 et un fichier de 16 sont signes de Farbling
    - L'absence de vrais mots dans le nom et la description du plugin, ceux générés
      par le Farbling étant aléatoires

    Paramètres:
    - plugin_list_1: List
        Une liste de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]
    - plugin_list_2: List
        Une liste de plugins au format suivant:
        Plugin individuel : [nom du plugin, description du plugin, fichier du plugin]
        Liste de plugins : [ [plugin individuel], ...]

    Valeurs de retour:
    - Int
        Indice de similarité entre les 2 listes de plugins. 0 si plus (ou moins) de 2 plugins de différence,
        1 si les titres/descriptions/fichiers des plugins font une taille suspecte, et 2 si aucun des mots
        du titre et de la description ne sont de vrais mots
    """

    diff = difference_plugins_list(plugin_list_1, plugin_list_2)
    distance = len(diff)
    
    # Si seulement 2 plugins différents entre les 2 listes
    if distance == 2:
        
        count_flase_plugins = 0
        suspicious_size = 0
        for elems in diff:
            
            # Calcul du nombre d'élements aillant un taille pouvant faire penser 
            # a un élément généré via Farbling
            suspicious_size = 0 
            splitted_plugin = elems.split('; ')
            try:
                if len(splitted_plugin[0]) == 8:
                    suspicious_size += 1
                if len(splitted_plugin[1]) == 32:
                    suspicious_size += 1
                if len(splitted_plugin[2]) == 16:
                    suspicious_size += 1
            except IndexError:
                continue
      
            # Si les 3 éléments ont une taille suspicieuse
            if suspicious_size == 3:
                
                # Calcul du nombre de mots existants dans la langue anglaise dans le titre et description du plugin
                splitted_title = splitted_plugin[0].split(' ')
                splitted_description = splitted_plugin[1].split(' ')
            
                total_title = 0
                for word in splitted_title:
                    if word.lower() in words.words():
                        total_title += 1

                total_description = 0
                for word in splitted_description:
                    if word.lower() in words.words():
                        total_description += 1
                
                # Si ni le titre ni la description n'ont de vrais mots
                if total_title==0 and total_description==0:
                    # Si il y a déjà un plugin qui a été détecté comme étant faux
                    if count_flase_plugins == 1: 
                        return 3
                    else:
                        count_flase_plugins += 1

        if suspicious_size == 3:
            return 2
        return 1

    return 0


def evaluate(max_sessions=10, debug=False):
    """
    La fonction va dans un premier temps prendre une liste de plugins au hasard dans le jeu de données, et en générer 10 versions farblées (en en gardant une comme base de travail).
    Elle va ensuite insérer ces versions à des indices spécifiques du jeu de données, et mélanger ce dernier.

    Ensuite, la fonction va parcourir chaque liste de plugins présentes dans le jeu de données, afin de les comparer avec la base de travail. 
    Si une liste de plugins est détectée comme similaire, elle sera affiché dans le total des "listes similaires"
    Si une liste de plugins est détectée comme similaire et fait partie de celles insérées dans le jeu de données, elles seront affichées dans le total des "listes identiques"

    paramètres:
    - max_sessions: Int
        Nombre de sessions de tests à affectuer 
        10 par défaut
    - debug: Bool
        True pour afficher les infos de débug, False sinon
        False par défaut

    Valeurs de retour:
    - None
        Ne renvoie rien, mais affiche les résultats dans la console
    """

    original_dataset = get_plugins_from_file()
    
    print("\nLe phase de calcul peut prendre un certain temps, en cas de doute activer l'option debug\n-> evaluate(debug=True) ligne 418\n")

    # Pour chaque session
    for i in range(max_sessions):

        print(f"Session n°{i+1}: ")

        working_dataset = original_dataset.copy()
        
        # Choix d'une liste de plugins aléatoire
        working_list = random.choice(working_dataset)

        base_indexes = []
        stored_farbled_lists = []
        
        ## Génération du jeu de données   

        # Création de 10 listes farblées, en utilisant un nom de domaine généré aléatoirement
        for j in range(10):
            tmp = working_list.copy()
    
            # Génération d'un nom de domaine
            website = ''.join(random.choices(string.ascii_lowercase, k=random.randint(8,20)))
            website += '.'
            website += ''.join(random.choices(string.ascii_lowercase, k=random.randint(2,3)))

            farbled_list = farbling(tmp, i, website)
            
            stored_farbled_lists.append(farbled_list)

            # Génération des indices du jeu de données auquels les listes farblées seront insérées
            base_indexes.append(random.randint(0, len(working_dataset)))
           
            # On garde la dernière liste générée comme liste de référence
            if j==9:
                working_list = farbled_list
       
        # Mélange du jeu de données
        random.shuffle(working_dataset)
       
        # Insertion des listes générées dans le jeu de données
        i = 0
        for index in base_indexes:
            working_dataset.insert(index, stored_farbled_lists[i]) 
            i+=1

        ## Attaque du jeu de données

        total = 0
        found_indexes = []

        debug_size = len(working_dataset)
        
        debug_dataset = []

        # Parcours du jeu de données
        for j in range(len(working_dataset)):
            
            if j%1000==0 and debug:
                print(f"\tCalcul des colonnes {j} à {j+1000} (sur {debug_size})")
            
            # Comparaion entre notre liste de référence et la liste courante
            # Si elle est très fortement similaire, on ajoute son indice dans une liste d'indices trouvés
            result = compare_plugins_list(working_list, working_dataset[j])
            if result == 3:
                # Possible d'utiliser le dataset de debug pour afficher toutes les listes similaires trouvées (voir ligne 393)
                # debug_dataset.append(working_dataset[j])
                found_indexes.append(j)
                total+=1

        # Ici, le total correspond au nombre de listes trouvées fortements simialires à notre liste de référence
        # Il arrive que le programme trouve plus (ou moins) de listes similaires que le nombre inséré dans le jeu de données
        # Les explications possibles de ce phénomène sont détaillées dans le rapport
        print(f"\n\tDans cette session, un total de {total} listes de plugins similaires ont été trouvées.")
        
        # Possible d'utiliser le dataset de debug pour afficher toutes les listes similaires trouvées (voir ligne 383)
        # Ici si nombre de listes trouvées >= 30
        # if total >= 30:
            # for elems in debug_dataset:
                # elems.sort()
                # print(elems)

        # Comptage du nombre d'indices trouvés qui font partie des indices insérés
        # L'intervale de validité se situe entre -10 et +10 car l'insertion des listes farblées au début de la fonction
        # a décalé tous les intervales précédents (et je n'ai pas trouvé de solution simple pour palier à ce problème)
        count = 0
        for f_index in found_indexes:
            for b_index in base_indexes:
                if (b_index -10) <= f_index and f_index <= (b_index + 10):
                    count += 1
                    break
        
        # Ici, le compte correspond au nombre de listes trouvées dont on est raisonnablement sûrs qu'il fasse partie de la 
        # liste originale. Ce compte est parfois un peu inexact, à cause notamment de l'intervale -10 +10
        print(f"\tEnviron {count} listes de plugins identiques ont été trouvées.\n")

if __name__ == "__main__":
    print("Le programme va télécharger un dictionnaire de langue anglaise (venant de la bibliothèque nltk)")
    input("Appuyez sur une touche pour confirmer le téléchargement, ou CTRL+C pour annuler l'opération.")
    download('words')
    evaluate(debug=False)
