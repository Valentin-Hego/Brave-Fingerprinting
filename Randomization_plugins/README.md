# Instructions de lancement
---
**Etape 1 :** Créer un envrionnement virtuel Python <br>
`python -m venv venv`

**Etape 2 :** Activer l'envrionnement <br>
`source ./venv/bin/activate`

**Etape 3 :** Installer les dépendances <br>
`pip install -r requirements.txt`

**Etape 4 :** Lancer le programme <br>
`python plugins.py`

**Etape 5:** Accepter le téléchargement <br>
Pour pouvoir fonctionner, le programme a besoin de télécharger un dictionnaire de langue anglaise, via le module python nltk. <br>
En appuyant sur une touche pour valider, vous acceptez de télécharger de dictionnaire sur votre machine (dans le dossier /home/<user>/nltk_data sur Linux).

# Instructions de debug
---
L'exécution de l'analyse peut prendre un certain temps en fonction des performances de votre machine. En cas de doute sur la progression du programme, vous pouvez changer la ligne 418 (la dernière) de _plugin.py_, en passant debug à True. Cela affichera le taux de complétion de la session en cours toutes les 1000 lignes traitées.