import numpy as np
import pandas as pd
import hashlib
import base64
import os
import matplotlib.pyplot as plt
from scipy import stats
from io import BytesIO
from PIL import Image

# ---------------------------------------------------------
# EXTRACTION DU DATASET
# ---------------------------------------------------------
def get_canvas_from_file(filepath="../utils/extension1.txt"):
    if not os.path.exists(filepath):
        print(f"Fichier {filepath} introuvable.")
        return None
        
    print(f"Chargement et filtrage de {filepath} avec Pandas...")
    
    try:
        # Chargement brut: on utilise un séparateur nul (\x00) pour que 
        # Pandas lise chaque ligne du fichier SQL comme une seule colonne brute.
        df = pd.read_csv(filepath, sep='\x00', header=None, names=['ligne_brute'], engine='python', on_bad_lines='skip')
        
        # Extraction vectorisée : on cherche l'en-tête d'un PNG base64 (iVBORw0KGgo)
        # La fonction va créer une nouvelle colonne avec le base64, ou NaN s'il n'y a rien.
        extractions = df['ligne_brute'].str.extract(r'(iVBORw0KGgo[A-Za-z0-9+/=]+)')
        
        # 3. Nettoyage : on supprime toutes les lignes vides (NaN)
        canvas_valides = extractions.dropna()
        
        if not canvas_valides.empty:
            # On récupère la première chaîne base64 valide
            b64_string = canvas_valides.iloc[0, 0]
            
            # Décodage en image NumPy
            img_data = base64.b64decode(b64_string)
            img = Image.open(BytesIO(img_data)).convert('RGBA')
            return np.array(img)
            
    except Exception as e:
        print(f"Erreur lors du traitement Pandas : {e}")
        
    print("Aucun canvas valide trouvé.")
    return None

# ---------------------------------------------------------
# SIMULATION DE LA DEFENSE (BRAVE FARBLING)
# ---------------------------------------------------------
def brave_farbling(canvas, session_id="s1", domain="test.com", pixels_to_mod=256):
    # Implémentation du mécanisme de randomisation de Brave (Default mode)
    img = canvas.copy()
    h, w, _ = img.shape
    total_pixels = w * h
    
    # Brave modifie un seul canal RGB, déterminé par le domaine visité
    channel = ord(domain[0]) % 3
    
    # La clé de bruit dépend du contenu de l'image ET de la session
    raw_data = img.tobytes()
    context = f"{session_id}_{domain}".encode('utf-8')
    key = hashlib.sha256(context + raw_data).digest()
    
    # Initialisation du générateur pseudo-aléatoire
    seed = int.from_bytes(key[:8], byteorder='little')
    rng = np.random.default_rng(seed)
    
    # Sélection des pixels à altérer (256 max)
    indices = rng.choice(total_pixels, size=min(pixels_to_mod, total_pixels), replace=False)
    rows, cols = indices // w, indices % w
    
    # Application du bruit (opération XOR sur le canal)
    img[rows, cols, channel] ^= 1
    
    return img

# ---------------------------------------------------------
# ATTAQUE STATISTIQUE (MAJORITY VOTE)
# ---------------------------------------------------------
def attack_majority_vote(canvases):
    # Superpose les canvas bruités et extrait la valeur majoritaire pour chaque pixel
    stacked = np.stack(canvases)
    mode_result = stats.mode(stacked, axis=0, keepdims=False)
    return mode_result.mode

# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------
def evaluate(max_sessions=10):
    print("Démarrage de l'évaluation expérimentale...")
    
    original_canvas = get_canvas_from_file()
    if original_canvas is None:
        print("Erreur: Impossible de charger l'image de référence.")
        return [], []

    total_values = original_canvas.size
    print(f"Canvas de référence chargé ({total_values} valeurs RGBA).")
    
    collected_canvases = []
    sessions_list = []
    success_rates = []
    
    # Simulation de la collecte d'empreintes sur plusieurs sessions
    for n in range(1, max_sessions + 1):
        # Le navigateur génère l'empreinte bruitée
        noisy_canvas = brave_farbling(original_canvas, session_id=str(n))
        collected_canvases.append(noisy_canvas)
        
        # L'attaquant reconstruit l'image
        reconstructed = attack_majority_vote(collected_canvases)
        
        # Calcul de la précision de l'attaque
        errors = np.sum(reconstructed != original_canvas)
        rate = 100.0 * (total_values - errors) / total_values
        
        sessions_list.append(n)
        success_rates.append(rate)
        
        print(f"Session {n:02d} | Erreurs: {errors:<4} | Précision: {rate:.5f}%")
        
    return sessions_list, success_rates

# ---------------------------------------------------------
# VISUALISATION DES RESULTATS
# ---------------------------------------------------------
def plot_results(x, y):
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker='o', color='#d62728', linewidth=2)
    
    plt.title("Efficacité de l'attaque statistique sur le Farbling")
    plt.xlabel("Nombre de sessions collectées (N)")
    plt.ylabel("Précision de la reconstruction (%)")
    
    plt.ylim(99.8, 100.02)
    plt.xticks(x)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig("resultats_attaque.png")
    print("Graphique généré : resultats_attaque.png")
    plt.show()

# ==========================================
# TESTS
# ==========================================
def test_extraction():
    print("--- Début du test d'extraction du dataset ---")
    
    filepath = "../utils/extension1.txt" 

    canvas_array = get_canvas_from_file(filepath)
    
    # Vérification de la présence de données
    if canvas_array is None:
        print("Test échoué : La fonction a retourné 'None'. Vérifie le chemin du fichier ou le contenu.")
        return
        
    print("\n Extraction réussie !")
    
    # Vérification du type (Doit être un tableau NumPy pour la suite de ton attaque)
    print(f"Type de l'objet : {type(canvas_array)}")
    if isinstance(canvas_array, np.ndarray):
        print("Format NumPy validé.")
    else:
        print("Attention, ce n'est pas un tableau NumPy.")
        
    # Vérification des dimensions (Doit être Hauteur x Largeur x 4 canaux RGBA)
    shape = canvas_array.shape
    print(f"Dimensions (Hauteur, Largeur, Canaux) : {shape}")
    if len(shape) == 3 and shape[2] == 4:
        print("Canaux RGBA validés.")
    else:
        print("Le format n'est pas RGBA (il manque l'Alpha ou ce n'est pas une image couleur).")
        
    # Vérification des valeurs brutes
    print(f"Type des données (dtype) : {canvas_array.dtype}")
    print(f"Valeur min : {canvas_array.min()} / Valeur max : {canvas_array.max()} (devrait être entre 0 et 255)")
    
    # Preuve par l'image 
    print("\n Affichage du Canvas extrait (ferme la fenêtre pour terminer le test)...")
    plt.figure(figsize=(6, 4))
    plt.imshow(canvas_array)
    plt.title(f"Canvas FPStalker (Dimensions : {shape[1]}x{shape[0]})")
    plt.axis('off') # On cache les axes pour ne garder que l'image pure
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # test_extraction()
    x_vals, y_vals = evaluate(max_sessions=10)
    if x_vals:
        plot_results(x_vals, y_vals)