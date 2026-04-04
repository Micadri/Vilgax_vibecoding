"""
╔═══════════════════════════════════════════════════════════════╗
║                    VILGAX - modules/utils.py                  ║
║                Fonctions Utilitaires et Helpers               ║
╚═══════════════════════════════════════════════════════════════╝

RÔLE :
Ce module contient les fonctions utilitaires partagées par les autres modules.
Il centralise les outils de validation, formatage, gestion des pauses,
export CSV et logging.

PLACE DANS L'ARCHITECTURE :
- Importé par app.py, scraper_maps.py, audit_site.py, ia_filter.py
- Fournit des helpers pour la robustesse et la modularité
- Gère les pauses aléatoires et timeouts (anti-détection)
- Centralise la logique d'export CSV

RÉFÉRENCE CAHIER DES CHARGES :
- Section 2.5 : Stockage (RAM uniquement, Export CSV)
- Section 3.E : Output (CSV séparateur ;, UTF-8)
- Section 4 : Contraintes critiques (robustesse, pauses aléatoires, timeouts)
"""

import time
import random
import csv
import os
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

# Import de la configuration centrale
import config


# ═════════════════════════════════════════════════════════════
# 1. GESTION DES PAUSES ALÉATOIRES
# ═════════════════════════════════════════════════════════════

def random_pause(min_seconds: float = None, max_seconds: float = None) -> None:
    """
    Effectue une pause aléatoire pour simuler un comportement humain.
    Cette fonction est essentielle pour éviter la détection anti-bot
    sur Google Maps et les sites web audités.

    Args:
        min_seconds (float, optional): Durée minimale en secondes (défaut: config.PAUSE_MIN)
        max_seconds (float, optional): Durée maximale en secondes (défaut: config.PAUSE_MAX)

    Returns:
        None

    RÉFÉRENCE CAHIER DES CHARGES :
    Section 4 - Contraintes critiques (pauses aléatoires)
    """
    # Utilise les valeurs par défaut de config.py si non fournies
    if min_seconds is None:
        min_seconds = config.PAUSE_MIN
    if max_seconds is None:
        max_seconds = config.PAUSE_MAX

    # Génère une durée aléatoire entre min et max
    pause_duration = random.uniform(min_seconds, max_seconds)

    # Effectue la pause
    time.sleep(pause_duration)


def random_micro_pause(min_ms: int = 500, max_ms: int = 1500) -> None:
    """
    Effectue une micro-pause aléatoire (en millisecondes).
    Utile pour les actions rapides comme les clics ou scrolls.

    Args:
        min_ms (int): Durée minimale en millisecondes (défaut: 500ms)
        max_ms (int): Durée maximale en millisecondes (défaut: 1500ms)

    Returns:
        None
    """
    # Convertit les millisecondes en secondes
    pause_duration = random.uniform(min_ms / 1000, max_ms / 1000)

    # Effectue la pause
    time.sleep(pause_duration)


# ═════════════════════════════════════════════════════════════
# 2. EXPORT CSV
# ═════════════════════════════════════════════════════════════

def export_to_csv(data: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Exporte les données en fichier CSV selon les spécifications du cahier des charges.

    Args:
        data (List[Dict[str, Any]]): Liste de dictionnaires à exporter
        filename (str, optional): Nom du fichier (défaut: results_TIMESTAMP.csv)

    Returns:
        str: Chemin complet du fichier créé

    RÉFÉRENCE CAHIER DES CHARGES :
    Section 3.E - Output (CSV final, séparateur ;, UTF-8)
    """
    # Vérifie que les données ne sont pas vides
    if not data or len(data) == 0:
        print("⚠️ Aucune donnée à exporter")
        return ""

    # Génère le nom de fichier avec timestamp si non fourni
    if filename is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"results_{timestamp}.csv"

    # Construit le chemin complet du fichier
    filepath = os.path.join(config.EXPORT_FOLDER, filename)

    # Crée le dossier exports/ s'il n'existe pas
    os.makedirs(config.EXPORT_FOLDER, exist_ok=True)

    try:
        # Ouvre le fichier en mode écriture avec encodage UTF-8 + BOM
        # Le BOM permet à Excel d'ouvrir correctement les caractères accentués
        with open(filepath, 'w', newline='', encoding=config.CSV_ENCODING) as csvfile:
            # Crée le writer CSV avec séparateur point-virgule
            writer = csv.DictWriter(
                csvfile,
                fieldnames=config.CSV_COLUMNS,  # Colonnes définies dans config.py
                delimiter=config.CSV_SEPARATOR,  # Séparateur ";"
                extrasaction='ignore'  # Ignore les colonnes non définies
            )

            # Écrit l'en-tête (noms des colonnes)
            writer.writeheader()

            # Écrit chaque ligne de données
            for row in data:
                # Remplit les colonnes manquantes avec NOT_FOUND
                complete_row = {col: row.get(col, config.VALUE_NOT_FOUND) for col in config.CSV_COLUMNS}
                writer.writerow(complete_row)

        print(f"✅ Export CSV réussi : {filepath}")
        return filepath

    except PermissionError:
        print(f"❌ Erreur : Impossible d'écrire dans {filepath} (fichier ouvert ?)")
        return ""
    except Exception as e:
        print(f"❌ Erreur lors de l'export CSV : {e}")
        return ""


# ═════════════════════════════════════════════════════════════
# 3. VALIDATION DES DONNÉES
# ═════════════════════════════════════════════════════════════

def validate_business_data(data: Dict[str, Any]) -> bool:
    """
    Valide qu'un dictionnaire d'entreprise contient les champs obligatoires.
    Au minimum, le nom de l'entreprise doit être présent.

    Args:
        data (Dict[str, Any]): Dictionnaire de données d'entreprise

    Returns:
        bool: True si valide, False sinon
    """
    # Vérifie que c'est bien un dictionnaire
    if not isinstance(data, dict):
        return False

    # Vérifie que le champ "Nom" existe et n'est pas vide
    nom = data.get("Nom", "").strip()
    if not nom or nom == config.VALUE_NOT_FOUND:
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères interdits.

    Args:
        filename (str): Nom de fichier brut

    Returns:
        str: Nom de fichier nettoyé (compatible Windows/Linux/Mac)

    Caractères interdits : < > : " / \\ | ? *
    """
    # Liste des caractères interdits dans les noms de fichiers
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

    # Remplace chaque caractère interdit par un underscore
    clean_name = filename
    for char in forbidden_chars:
        clean_name = clean_name.replace(char, '_')

    # Supprime les espaces multiples
    clean_name = ' '.join(clean_name.split())

    return clean_name


# ═════════════════════════════════════════════════════════════
# 4. FORMATAGE DES DONNÉES
# ═════════════════════════════════════════════════════════════

def format_phone_number(phone: str) -> str:
    """
    Formate un numéro de téléphone en supprimant les caractères parasites.

    Args:
        phone (str): Numéro de téléphone brut

    Returns:
        str: Numéro de téléphone nettoyé

    Exemples:
        "+32 2 123 45 67" → "+32 2 123 45 67"
        "02/123.45.67" → "02 123 45 67"
        "Tel: 02 123 45 67" → "02 123 45 67"
    """
    # Si vide ou NOT_FOUND, retourne tel quel
    if not phone or phone == config.VALUE_NOT_FOUND:
        return phone

    # Supprime les préfixes courants
    phone = phone.replace("Téléphone:", "").replace("Tel:", "").replace("Phone:", "")

    # Supprime les espaces en début et fin
    phone = phone.strip()

    return phone


def format_url(url: str) -> str:
    """
    Formate une URL en supprimant les paramètres de tracking et en extrayant
    l'URL réelle depuis les URLs de redirection Google.

    Args:
        url (str): URL brute

    Returns:
        str: URL nettoyée

    Exemples:
        "https://www.google.com/url?q=https://www.ndepover.be/&opi=..." → "https://www.ndepover.be"
        "https://example.com?utm_source=google" → "https://example.com"
        "http://example.com#section" → "http://example.com"
    """
    # Si vide ou NOT_FOUND, retourne tel quel
    if not url or url == config.VALUE_NOT_FOUND:
        return url

    # Détecte et extrait l'URL réelle depuis les redirections Google
    if 'google.com/url' in url and 'q=' in url:
        try:
            # Parse l'URL pour extraire les paramètres
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            # Extrait le paramètre 'q' qui contient l'URL réelle
            if 'q' in params and len(params['q']) > 0:
                url = params['q'][0]
        except Exception as e:
            # En cas d'erreur de parsing, continue avec l'URL d'origine
            log_error(f"Erreur lors du parsing de l'URL Google: {e}", "WARNING")

    # Supprime les paramètres GET (après le ?)
    if '?' in url:
        url = url.split('?')[0]

    # Supprime les ancres (après le #)
    if '#' in url:
        url = url.split('#')[0]

    return url


# ═════════════════════════════════════════════════════════════
# 5. STATISTIQUES ET REPORTING
# ═════════════════════════════════════════════════════════════

def calculate_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcule des statistiques sur les données collectées.

    Args:
        data (List[Dict[str, Any]]): Liste des entreprises collectées

    Returns:
        Dict[str, Any]: Dictionnaire de statistiques

    Statistiques calculées:
    - total: Nombre total d'entreprises
    - with_website: Nombre d'entreprises avec site web
    - with_email: Nombre d'entreprises avec email trouvé
    - with_pixel_fb: Nombre d'entreprises avec Pixel Facebook
    - mobile_friendly: Nombre de sites mobile-friendly
    - ia_true: Nombre d'entreprises validées par l'IA
    - ia_false: Nombre d'entreprises rejetées par l'IA
    - ia_unknown: Nombre d'entreprises non analysées par l'IA
    """
    # Initialise les compteurs
    stats = {
        "total": len(data),
        "with_website": 0,
        "with_email": 0,
        "with_pixel_fb": 0,
        "mobile_friendly": 0,
        "ia_true": 0,
        "ia_false": 0,
        "ia_unknown": 0,
        "cms_wordpress": 0,
        "cms_wix": 0,
        "cms_shopify": 0
    }

    # Parcourt les données pour compter
    for business in data:
        # Compte les sites web
        if business.get("Site") and business.get("Site") != config.VALUE_NOT_FOUND:
            stats["with_website"] += 1

        # Compte les emails
        if business.get("Email_Scrapé") and business.get("Email_Scrapé") != config.VALUE_NOT_FOUND:
            stats["with_email"] += 1

        # Compte les Pixels Facebook
        if business.get("Pixel_FB") == "OUI":
            stats["with_pixel_fb"] += 1

        # Compte les sites mobile-friendly
        if business.get("Mobile_OK") == "OUI":
            stats["mobile_friendly"] += 1

        # Compte les résultats IA
        ia_result = business.get("IA_Relevant", config.VALUE_UNKNOWN)
        if ia_result == "TRUE":
            stats["ia_true"] += 1
        elif ia_result == "FALSE":
            stats["ia_false"] += 1
        else:
            stats["ia_unknown"] += 1

        # Compte les CMS
        cms = business.get("CMS", config.VALUE_NOT_FOUND)
        if cms == "WordPress":
            stats["cms_wordpress"] += 1
        elif cms == "Wix":
            stats["cms_wix"] += 1
        elif cms == "Shopify":
            stats["cms_shopify"] += 1

    return stats


def print_stats(stats: Dict[str, Any]) -> None:
    """
    Affiche les statistiques de manière formatée dans la console.

    Args:
        stats (Dict[str, Any]): Dictionnaire de statistiques (retour de calculate_stats)

    Returns:
        None
    """
    print("\n" + "=" * 60)
    print("📊 STATISTIQUES DE LA COLLECTE")
    print("=" * 60)

    # Statistiques générales
    print(f"\n🎯 RÉSULTATS GÉNÉRAUX")
    print(f"   • Total d'entreprises : {stats['total']}")
    print(f"   • Avec site web : {stats['with_website']} ({percentage(stats['with_website'], stats['total'])}%)")
    print(f"   • Avec email trouvé : {stats['with_email']} ({percentage(stats['with_email'], stats['total'])}%)")

    # Audit technique
    if stats['with_website'] > 0:
        print(f"\n🔬 AUDIT TECHNIQUE")
        print(f"   • Pixel Facebook : {stats['with_pixel_fb']} ({percentage(stats['with_pixel_fb'], stats['with_website'])}%)")
        print(f"   • Mobile-friendly : {stats['mobile_friendly']} ({percentage(stats['mobile_friendly'], stats['with_website'])}%)")
        print(f"   • WordPress : {stats['cms_wordpress']}")
        print(f"   • Wix : {stats['cms_wix']}")
        print(f"   • Shopify : {stats['cms_shopify']}")

    # Filtrage IA
    print(f"\n🤖 FILTRAGE IA")
    print(f"   • Pertinents (TRUE) : {stats['ia_true']}")
    print(f"   • Non pertinents (FALSE) : {stats['ia_false']}")
    print(f"   • Non analysés (UNKNOWN) : {stats['ia_unknown']}")

    print("\n" + "=" * 60 + "\n")


def percentage(part: int, total: int) -> float:
    """
    Calcule un pourcentage et l'arrondit à 2 décimales.

    Args:
        part (int): Valeur partielle
        total (int): Valeur totale

    Returns:
        float: Pourcentage arrondi (0.00 si total = 0)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


# ═════════════════════════════════════════════════════════════
# 6. GESTION DES ERREURS ET LOGGING
# ═════════════════════════════════════════════════════════════

def log_error(error_message: str, error_type: str = "ERROR") -> None:
    """
    Enregistre une erreur dans la console avec timestamp.

    Args:
        error_message (str): Message d'erreur à afficher
        error_type (str): Type d'erreur (ERROR, WARNING, INFO)

    Returns:
        None
    """
    # Génère le timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Choix de l'icône selon le type
    icons = {
        "ERROR": "❌",
        "WARNING": "⚠️",
        "INFO": "ℹ️",
        "SUCCESS": "✅"
    }

    icon = icons.get(error_type, "❓")

    # Affiche le message
    print(f"[{timestamp}] {icon} {error_type}: {error_message}")


def safe_execute(func, *args, default_return=None, **kwargs):
    """
    Exécute une fonction de manière sécurisée (try/except automatique).
    Cette fonction wrapper évite les crashs globaux en capturant
    toutes les exceptions et retournant une valeur par défaut.

    Args:
        func: Fonction à exécuter
        *args: Arguments positionnels de la fonction
        default_return: Valeur de retour par défaut en cas d'erreur
        **kwargs: Arguments nommés de la fonction

    Returns:
        Le retour de la fonction ou default_return en cas d'erreur

    RÉFÉRENCE CAHIER DES CHARGES :
    Section 4 - Contraintes critiques (aucun crash global)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(f"Erreur dans {func.__name__}: {e}", "ERROR")
        return default_return


# ═════════════════════════════════════════════════════════════
# 7. HELPERS DE VÉRIFICATION
# ═════════════════════════════════════════════════════════════

def is_empty_value(value: Any) -> bool:
    """
    Vérifie si une valeur est considérée comme vide.

    Args:
        value (Any): Valeur à vérifier

    Returns:
        bool: True si vide, False sinon

    Considéré comme vide:
    - None
    - Chaîne vide ""
    - Chaîne avec espaces uniquement "   "
    - NOT_FOUND
    - UNKNOWN
    - ERROR
    """
    # Si None
    if value is None:
        return True

    # Si chaîne de caractères
    if isinstance(value, str):
        value_stripped = value.strip()
        # Vérifie si vide ou valeur par défaut
        if not value_stripped or value_stripped in [config.VALUE_NOT_FOUND, config.VALUE_UNKNOWN, config.VALUE_ERROR]:
            return True

    return False


def count_non_empty(data: List[Dict[str, Any]], field: str) -> int:
    """
    Compte le nombre d'entrées avec une valeur non vide pour un champ donné.

    Args:
        data (List[Dict[str, Any]]): Liste de dictionnaires
        field (str): Nom du champ à vérifier

    Returns:
        int: Nombre d'entrées avec valeur non vide
    """
    count = 0
    for item in data:
        value = item.get(field)
        if not is_empty_value(value):
            count += 1
    return count


# ═════════════════════════════════════════════════════════════
# 8. PROGRESSBAR CONSOLE (OPTIONNEL)
# ═════════════════════════════════════════════════════════════

def print_progress_bar(current: int, total: int, prefix: str = "", length: int = 40) -> None:
    """
    Affiche une barre de progression dans la console.

    Args:
        current (int): Valeur actuelle
        total (int): Valeur totale
        prefix (str): Texte avant la barre
        length (int): Longueur de la barre en caractères

    Returns:
        None

    Exemple d'affichage:
    Scraping: [████████████████--------------------] 40% (20/50)
    """
    # Calcule le pourcentage
    percent = (current / total) * 100 if total > 0 else 0

    # Calcule le nombre de blocs remplis
    filled_length = int(length * current // total) if total > 0 else 0

    # Construit la barre
    bar = '█' * filled_length + '-' * (length - filled_length)

    # Affiche la barre (écrase la ligne précédente avec \r)
    print(f'\r{prefix} [{bar}] {percent:.1f}% ({current}/{total})', end='', flush=True)

    # Saut de ligne si terminé
    if current == total:
        print()


# ═════════════════════════════════════════════════════════════
# FIN DU FICHIER modules/utils.py
# ═════════════════════════════════════════════════════════════
