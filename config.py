"""
╔═══════════════════════════════════════════════════════════════╗
║                    VILGAX - config.py                          ║
║                  Configuration Centrale                        ║
╚═══════════════════════════════════════════════════════════════╝

RÔLE :
Ce fichier centralise toutes les constantes et configurations du projet VILGAX.
Il sert de source unique de vérité pour les paramètres techniques.

PLACE DANS L'ARCHITECTURE :
- Importé par tous les autres modules (app.py, scraper_maps.py, audit_site.py, ia_filter.py)
- Aucune dépendance externe (fichier de base)
- Permet de modifier les paramètres sans toucher au code métier

RÉFÉRENCE CAHIER DES CHARGES :
- Section 2 : Stack technique
- Section 4 : Contraintes critiques (timeouts, pauses)
"""

import os


# ═════════════════════════════════════════════════════════════
# 1. CONFIGURATION IA LOCALE (LM Studio)
# ═════════════════════════════════════════════════════════════

# URL du serveur LM Studio local (compatible OpenAI API)
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"

# Clé API locale (valeur fixe pour LM Studio)
LM_STUDIO_API_KEY = "local-lm-studio"

# Timeout pour les requêtes IA (en secondes)
# Si le modèle ne répond pas, on marque "UNKNOWN"
IA_TIMEOUT = 30


# ═════════════════════════════════════════════════════════════
# 2. CONFIGURATION SCRAPING GOOGLE MAPS
# ═════════════════════════════════════════════════════════════

# URL de base Google Maps
GOOGLE_MAPS_URL = "https://www.google.com/maps"

# Mode headless désactivé (Chrome visible)
CHROME_HEADLESS = False

# Timeout pour le chargement d'une page (secondes)
PAGE_LOAD_TIMEOUT = 15

# Timeout implicite pour trouver les éléments (secondes)
IMPLICIT_WAIT = 10

# Pause minimum entre les actions (secondes)
# Évite la détection anti-bot
PAUSE_MIN = 2

# Pause maximum entre les actions (secondes)
PAUSE_MAX = 5

# Nombre maximum de scrolls dans la sidebar Google Maps
# Sécurité pour éviter les boucles infinies
MAX_SCROLLS = 200


# ═════════════════════════════════════════════════════════════
# 3. CONFIGURATION AUDIT TECHNIQUE
# ═════════════════════════════════════════════════════════════

# Timeout pour charger un site web à auditer (secondes)
AUDIT_TIMEOUT = 10

# User-Agent pour les requêtes HTTP
# Simule un navigateur classique
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Headers HTTP standard
HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


# ═════════════════════════════════════════════════════════════
# 4. DÉTECTION TECHNIQUE (CMS, PIXEL FB, MOBILE)
# ═════════════════════════════════════════════════════════════

# Signatures pour détecter WordPress
WORDPRESS_SIGNATURES = [
    "wp-content",
    "wp-includes",
    "/wp-json/",
    "wordpress"
]

# Signatures pour détecter Wix
WIX_SIGNATURES = [
    "wix.com",
    "wixstatic.com",
    "X-Wix-"
]

# Signatures pour détecter Shopify
SHOPIFY_SIGNATURES = [
    "cdn.shopify.com",
    "shopify",
    "Shopify.theme"
]

# Signature Pixel Facebook
FACEBOOK_PIXEL_SIGNATURE = "fbevents.js"

# Balise meta viewport (mobile-friendly)
VIEWPORT_META = '<meta name="viewport"'


# ═════════════════════════════════════════════════════════════
# 5. REGEX EMAIL
# ═════════════════════════════════════════════════════════════

# Pattern regex pour extraire les emails
# Capture les emails standards (ex: contact@example.com)
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


# ═════════════════════════════════════════════════════════════
# 6. CONFIGURATION EXPORT CSV
# ═════════════════════════════════════════════════════════════

# Dossier de sortie pour les exports
EXPORT_FOLDER = "exports"

# Nom du fichier CSV par défaut
CSV_FILENAME = "results.csv"

# Séparateur CSV (point-virgule)
CSV_SEPARATOR = ";"

# Encodage CSV (UTF-8 avec BOM pour Excel)
CSV_ENCODING = "utf-8-sig"

# En-têtes du CSV final
CSV_COLUMNS = [
    "Nom",
    "Téléphone",
    "Site",
    "Email_Scrapé",
    "Pixel_FB",
    "Mobile_OK",
    "CMS",
    "IA_Relevant"
]


# ═════════════════════════════════════════════════════════════
# 7. STREAMLIT UI
# ═════════════════════════════════════════════════════════════

# Titre de l'application
APP_TITLE = "🛸 VILGAX - Prospection B2B Automatisée"

# Texte du bouton de lancement
LAUNCH_BUTTON_TEXT = "LANCER L'ATTAQUE"

# Limites du slider de résultats
MIN_RESULTS = 1
MAX_RESULTS = 100
DEFAULT_RESULTS = 20


# ═════════════════════════════════════════════════════════════
# 8. MESSAGES SYSTÈME
# ═════════════════════════════════════════════════════════════

# Valeurs par défaut pour les données manquantes
VALUE_NOT_FOUND = "NOT_FOUND"
VALUE_UNKNOWN = "UNKNOWN"
VALUE_ERROR = "ERROR"

# Messages de log
MSG_SCRAPING_START = "🔍 Démarrage du scraping Google Maps..."
MSG_AUDIT_START = "🔬 Audit technique en cours..."
MSG_IA_START = "🤖 Filtrage IA en cours..."
MSG_EXPORT_SUCCESS = "✅ Export CSV terminé !"
MSG_EXPORT_ERROR = "❌ Erreur lors de l'export CSV"


# ═════════════════════════════════════════════════════════════
# 9. INITIALISATION AUTOMATIQUE
# ═════════════════════════════════════════════════════════════

def init_folders():
    """
    Crée le dossier exports/ si inexistant.
    
    Appelé au démarrage de l'application pour garantir
    que les exports peuvent être sauvegardés.
    
    Returns:
        bool: True si création réussie, False sinon
    """
    try:
        os.makedirs(EXPORT_FOLDER, exist_ok=True)
        return True
    except Exception as e:
        print(f"⚠️ Impossible de créer le dossier {EXPORT_FOLDER}: {e}")
        return False


# ═════════════════════════════════════════════════════════════
# 10. PROMPT IA (TEMPLATE)
# ═════════════════════════════════════════════════════════════

def get_ia_prompt(keyword: str, text_content: str) -> str:
    """
    Génère le prompt système pour le filtrage IA local.
    
    Ce prompt demande au modèle LM Studio de valider la pertinence
    d'une entreprise par rapport au mot-clé de recherche.
    
    Args:
        keyword (str): Mot-clé de recherche utilisateur
        text_content (str): Texte nettoyé du site web
    
    Returns:
        str: Prompt formaté prêt à envoyer au modèle
    
    RÉFÉRENCE CAHIER DES CHARGES :
    Section 3.D - Filtrage IA
    """
    return f"""Est-ce que l'activité de cette entreprise correspond au mot-clé "{keyword}" ?
Réponds STRICTEMENT par TRUE ou FALSE.

Contenu du site :
{text_content[:1500]}"""


# ═════════════════════════════════════════════════════════════
# FIN DU FICHIER config.py
# ═════════════════════════════════════════════════════════════
