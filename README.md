# Audit & Attaques des Protections Anti-Fingerprinting de Brave

Projet d'étude en cybersécurité mené par **Valentin Hego**, **Lucien Gravot** et **Samuel Catellier** (Université de Rennes).

---

### Contexte : le fingerprinting, nouveau standard du tracking sur le web
Face au déclin des cookies tiers bloqués par la majorité des navigateurs modernes, le *browser fingerprinting* s'est imposé chez les traceurs web. En récoltant plus d'une quarantaine de métriques matérielles et logicielles (résolution d'écran, GPU, polices, configuration système), il devient possible d'identifier un utilisateur de manière unique sans stocker la moindre donnée sur son appareil.

Le navigateur **Brave** intègre nativement des mécanismes de défense pour briser cette traçabilité : l'injection de bruit aléatoire (*farbling*), la sous-division des données (*partitioning*) et la réduction de précision des métriques (*uniformisation*). 

Notre objectif à travers ce projet était de ré-implémenter ces défenses à partir de la documentation technique officielle de Brave afin d'en évaluer scientifiquement les limites opérationnelles.

---

### Notre démarche expérimentale
Pour garantir la reproductibilité des tests sans dépendre du comportement dynamique d'un navigateur en cours d'exécution, nous avons simulé les algorithmes de défense de Brave et les avons appliqués sur des données réelles.

- **Le dataset d'expérimentation :** Nous avons exploité le jeu de données public **FPStalker**, contenant plus de 15 000 empreintes réelles d'utilisateurs. Les empreintes Chrome ont été sélectionnées car Brave partage le même moteur sous-jacent (Chromium) et expose les mêmes surfaces d'attaque.
- **La modélisation des contre-mesures :** Implémentation en Python des fonctionnalités de *farbling* (Canvas, liste de plugins) et d'uniformisation (arrondis de résolution, masquage de la langue, harmonisation WebGL) en suivant scrupuleusement les spécifications et PRs de Brave.

*(Note : En raison de sa taille volumineuse, le dataset brut au format SQL ne figure pas sur ce dépôt, mais les scripts d'extraction et de traitement sont fournis).*

---

### Ce que nous avons démontré
Chacun d'entre nous s'est concentré sur un axe d'attaque spécifique pour vérifier si la combinaison des signaux permettait malgré tout de restaurer l'unicité des utilisateurs.

**1. Attaque sur l'uniformisation des attributs (Ma partie principale)**
L'uniformisation vise à réduire l'entropie en regroupant les utilisateurs dans des sous-ensembles identiques. En mesurant l'entropie de Shannon et le taux d'unicité sur notre jeu de données, j'ai constaté que l'uniformisation fait chuter le taux d'utilisateurs uniques de 80,12 % à 65,22 %. Cependant, pour préserver la compatibilité avec les sites web, Brave ne modifie pas certains attributs critiques comme le *User-Agent* ou le fuseau horaire. Ces attributs dits « résiduels » conservent une empreinte très forte : à eux seuls, ils permettent d'identifier de manière unique 36,85 % des utilisateurs.

**2. Attaque statistique sur le Canvas Farbling**
Brave altère légèrement le rendu de l'API Canvas en modifiant le bit de poids faible (LSB) d'un maximum de 256 pixels par domaine et par session. Nous avons développé une attaque par vote de majorité sur plusieurs sessions. Le résultat est sans appel : en collectant l'empreinte Canvas sur seulement 4 sessions différentes ($N=4$), l'attaque élimine totalement le bruit aléatoire et reconstruit l'image d'origine avec 100 % de précision.

**3. Contournement de la protection de la liste de plugins**
La protection en mode équilibré ajoute deux faux plugins aux noms et descriptions aléatoires. En définissant une heuristique basée sur la longueur des chaînes, l'absence de mots du dictionnaire anglais et les variations entre visites, notre algorithme a réussi à associer les empreintes modifiées d'un même utilisateur au sein de 15 000 profils en moins de 7 minutes.

---

### Enseignements & Bilan
Ces travaux illustrent le dilemme fondamental de la sécurité web : le compromis entre **confidentialité** et **utilisabilité**. 

Une protection stricte briserait le fonctionnement de nombreux sites web courants (ce qui a poussé Brave à abandonner son mode *Strict*). Le choix d'une protection modérée, bien qu'efficace au premier abord, laisse subsister suffisamment d'entropie résiduelle pour qu'un attaquant disposant de peu de ressources puisse ré-identifier un utilisateur à travers le temps ou les sessions.

---

### 🛠️ Stack & Outils
- **Langage :** Python (Pandas, NumPy, Regex)
- **Analyse de données & Métriques :** Entropie de Shannon, mesure de taux d'unicité, vote de majorité statistique
- **Sources & Références :** Dataset FPStalker, documentation technique de Brave Browser
