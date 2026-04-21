## 1. Fonction `get_canvas_from_file` (L'Extraction)

**Son rôle :** Récupérer notre Dataset de FPStalker, c'est-à-dire une vraie empreinte Canvas non bruitée pour faire nos tests.

**Comment elle fonctionne :**

- Elle ouvre le dataset brut de FPStalker (`extension1.txt`).
- Comme ce fichier est un énorme dump SQL, on utilise **Pandas** pour lire les lignes et une **Regex** (expression régulière) pour repérer la signature typique d'une image PNG encodée en base64 (`iVBORw0KGgo...`).
- Elle décode cette chaîne de caractères et la transforme en une matrice de pixels (un tableau `numpy`). C'est cette matrice parfaite que l'attaquant essaiera de retrouver.

---

## 2. Fonction `brave_farbling` (La Simulation de la Défense)

**Son rôle :** Reproduire fidèlement le comportement du navigateur Brave (mode par défaut) lorsqu'un site web tente de lire le Canvas.

**Comment elle fonctionne :**

- Elle prend notre image parfaite et génère une clé unique en combinant le contenu de l'image, le domaine visité et l'ID de la session en cours (via un hash SHA-256).
- Cette clé sert de seed aléatoire pour sélectionner un maximum de **256 pixels** dans toute l'image.
- Pour ces 256 pixels, elle modifie **un seul canal de couleur** (Rouge, Vert ou Bleu) en inversant son bit de poids faible (opération XOR). Le reste de l'image (99.9% des pixels) reste intact.

---

## 3. Fonction `attack_majority_vote` (Le Cœur de l'Attaque)

**Son rôle :** Casser la randomisation de Brave en lissant le bruit accumulé sur plusieurs sessions.

**Comment elle fonctionne :**

- Elle prend en entrée une liste d'images bruitées (par exemple, 5 canvas collectés sur 5 sessions différentes de la victime).
- Elle superpose virtuellement ces images (empilement de matrices).
- Elle utilise la fonction `scipy.stats.mode` pour appliquer un **vote majoritaire** pixel par pixel et canal par canal. Si pour un pixel donné, la valeur d'origine est apparue 4 fois sur 5, l'algorithme tranche et conserve cette valeur dominante, éliminant ainsi le bruit minoritaire introduit par Brave.

---

## 4. Fonction `evaluate` (Le Chef d'Orchestre)

**Son rôle :** Lancer l'expérience de bout en bout et mesurer précisément le taux de réussite de l'attaque.

**Comment elle fonctionne :**

- Elle boucle sur un nombre défini de sessions (de 1 à 10).
- À chaque tour de boucle, elle demande à la fonction `brave_farbling` de générer une nouvelle version bruitée de l'image (comme si la victime revenait sur le site).
- Elle donne toutes les images collectées jusqu'à présent à l'attaquant (`attack_majority_vote`) pour tenter une reconstruction.
- **Mesure du succès :** Elle compare pixel par pixel l'image reconstruite avec l'image parfaite du dataset et compte le nombre exact d'erreurs restantes pour calculer un pourcentage de précision.

---

## 5. Fonction `plot_results` (La Visualisation)

**Son rôle :** Générer une preuve visuelle de notre expérimentation.

**Comment elle fonctionne :**

- Elle utilise la bibliothèque `matplotlib` pour tracer une courbe.
- En abscisse (X) : le nombre de sessions collectées par l'attaquant.
- En ordonnée (Y) : la précision de la reconstruction.
- Elle sauvegarde automatiquement le résultat sous forme d'image (`resultats_attaque.png`) pour l'intégrer facilement dans notre rapport.

---

## Résumé

L'algorithme de Brave est cassé car il est "trop doux". Pour ne pas dégrader l'affichage des sites web, il ne modifie qu'une infime fraction des pixels (256 max). Si un attaquant récolte le Canvas d'un même utilisateur sur 4 ou 5 sessions différentes, le bruit ajouté par Brave a très peu de chances de tomber deux fois sur le même pixel. Le vote majoritaire fonctionne donc à la perfection et restaure **100% de l'empreinte d'origine**.
