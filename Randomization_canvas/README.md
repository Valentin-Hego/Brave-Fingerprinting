## Installation et Configuration

Suivez ces étapes pour configurer votre environnement local et installer les dépendances nécessaires.

### 1. Création de l'environnement virtuel (venv)

Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances.

- **Sur Windows :**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **Sur macOS/Linux :**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 2. Installation des dépendances

Une fois l'environnement activé, installez les paquets requis :

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Lancement du projet

```bash
python farbling.py
```
