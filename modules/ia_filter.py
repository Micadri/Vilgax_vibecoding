"""
╔═══════════════════════════════════════════════════════════════╗
║              VILGAX - modules/ia_filter.py                     ║
║              Module de Filtrage IA Locale (LM Studio)          ║
╚═══════════════════════════════════════════════════════════════╝

RÔLE :
Ce module utilise LM Studio (API OpenAI-compatible locale) pour valider
la pertinence d'une entreprise par rapport au mot-clé de recherche.

PLACE DANS L'ARCHITECTURE :
- Appelé par app.py après audit_site.py
- Reçoit le texte nettoyé du site web et le mot-clé
- Interroge le serveur LM Studio local (http://localhost:1234/v1)
- Retourne TRUE, FALSE ou UNKNOWN selon la réponse du modèle

RÉFÉRENCE CAHIER DES CHARGES :
- Section 2.4 : IA Locale (LM Studio, localhost:1234)
- Section 3.D : Filtrage IA (prompt système, gestion timeout)
- Section 4 : Contraintes critiques (robustesse, timeouts gérés)
"""

import requests
import json
# ✅ CORRECT
from typing import Dict, Any


# Import de la configuration centrale
import config


# ═════════════════════════════════════════════════════════════
# 1. FONCTION PRINCIPALE DE FILTRAGE IA
# ═════════════════════════════════════════════════════════════

def filter_with_ia(keyword: str, website_text: str) -> str:
    """
    Interroge le modèle IA local pour valider la pertinence d'une entreprise.
    
    Cette fonction envoie le texte du site web au serveur LM Studio local
    avec un prompt demandant de répondre TRUE ou FALSE.
    
    Args:
        keyword (str): Mot-clé de recherche (ex: "plombier", "restaurant")
        website_text (str): Texte nettoyé du site web de l'entreprise
    
    Returns:
        str: "TRUE" si pertinent, "FALSE" si non pertinent, "UNKNOWN" en cas d'erreur
    
    RÉFÉRENCE CAHIER DES CHARGES :
    Section 3.D - Filtrage IA (LM Studio)
    """
    
    # Vérifie que le texte n'est pas vide
    if not website_text or website_text.strip() == "":
        print(f"      ⚠️ Texte vide, impossible d'analyser")
        return config.VALUE_UNKNOWN
    
    try:
        print(f"      🤖 Filtrage IA pour mot-clé : '{keyword}'")
        
        # ─────────────────────────────────────────────────────────
        # 1.1 Génération du prompt système
        # ─────────────────────────────────────────────────────────
        
        # Utilise la fonction get_ia_prompt() de config.py
        # Le prompt demande strictement TRUE ou FALSE
        prompt = config.get_ia_prompt(keyword, website_text)
        
        # ─────────────────────────────────────────────────────────
        # 1.2 Préparation de la requête API (format OpenAI)
        # ─────────────────────────────────────────────────────────
        
        # LM Studio expose une API compatible OpenAI
        # Endpoint : /v1/chat/completions
        api_url = f"{config.LM_STUDIO_BASE_URL}/chat/completions"
        
        # Headers de la requête HTTP
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.LM_STUDIO_API_KEY}"
        }
        
        # Payload JSON au format OpenAI Chat Completions
        payload = {
            "messages": [
                {
                    "role": "user",  # Rôle de l'utilisateur
                    "content": prompt  # Contenu du prompt généré
                }
            ],
            "temperature": 0.1,  # Température basse pour des réponses déterministes
            "max_tokens": 10,  # Limite à 10 tokens (TRUE ou FALSE + espace)
            "stream": False  # Pas de streaming, réponse unique
        }
        
        # ─────────────────────────────────────────────────────────
        # 1.3 Envoi de la requête au serveur LM Studio
        # ─────────────────────────────────────────────────────────
        
        # Effectue la requête POST avec timeout
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=config.IA_TIMEOUT  # Timeout de 30 secondes (config.py)
        )
        
        # Vérifie que la requête a réussi (code 200)
        response.raise_for_status()
        
        # ─────────────────────────────────────────────────────────
        # 1.4 Parsing de la réponse
        # ─────────────────────────────────────────────────────────
        
        # Parse la réponse JSON
        response_data = response.json()
        
        # Extrait le contenu de la réponse du modèle
        # Format OpenAI : response.choices[0].message.content
        ia_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Nettoie la réponse (supprime espaces, sauts de ligne)
        ia_response = ia_response.strip().upper()
        
        # ─────────────────────────────────────────────────────────
        # 1.5 Validation de la réponse
        # ─────────────────────────────────────────────────────────
        
        # Vérifie que la réponse est bien TRUE ou FALSE
        if "TRUE" in ia_response:
            print(f"         ✓ IA : TRUE (pertinent)")
            return "TRUE"
        
        elif "FALSE" in ia_response:
            print(f"         ✓ IA : FALSE (non pertinent)")
            return "FALSE"
        
        else:
            # Réponse inattendue du modèle
            print(f"         ⚠️ Réponse IA inattendue : '{ia_response}'")
            return config.VALUE_UNKNOWN
    
    except requests.exceptions.Timeout:
        # Timeout lors de la connexion au serveur LM Studio
        print(f"      ⚠️ Timeout IA ({config.IA_TIMEOUT}s) : serveur LM Studio non réactif")
        return config.VALUE_UNKNOWN
    
    except requests.exceptions.ConnectionError:
        # Impossible de se connecter au serveur LM Studio
        print(f"      ❌ Connexion impossible à LM Studio ({config.LM_STUDIO_BASE_URL})")
        print(f"         → Vérifiez que LM Studio est lancé avec un modèle chargé")
        return config.VALUE_UNKNOWN
    
    except requests.exceptions.HTTPError as e:
        # Erreur HTTP (404, 500, etc.)
        print(f"      ❌ Erreur HTTP LM Studio : {e}")
        return config.VALUE_UNKNOWN
    
    except KeyError as e:
        # Erreur lors du parsing de la réponse JSON
        print(f"      ❌ Format de réponse invalide : {e}")
        return config.VALUE_UNKNOWN
    
    except Exception as e:
        # Erreur inattendue
        print(f"      ❌ Erreur critique IA : {e}")
        return config.VALUE_UNKNOWN


# ═════════════════════════════════════════════════════════════
# 2. FONCTION DE TEST DE CONNEXION LM STUDIO
# ═════════════════════════════════════════════════════════════

def test_lm_studio_connection() -> bool:
    """
    Teste la connexion au serveur LM Studio local.
    
    Cette fonction vérifie si LM Studio est lancé et répond.
    Utile pour diagnostiquer les problèmes de connexion.
    
    Returns:
        bool: True si LM Studio répond, False sinon
    
    RÉFÉRENCE CAHIER DES CHARGES :
    Section 2.4 - IA Locale (LM Studio)
    """
    
    try:
        print(f"🔌 Test de connexion à LM Studio : {config.LM_STUDIO_BASE_URL}")
        
        # Tente de se connecter au endpoint /v1/models
        # Ce endpoint liste les modèles disponibles
        test_url = f"{config.LM_STUDIO_BASE_URL}/models"
        
        response = requests.get(
            test_url,
            timeout=5  # Timeout court pour le test
        )
        
        # Vérifie que la requête a réussi
        response.raise_for_status()
        
        print(f"   ✅ LM Studio est connecté et répond")
        
        # Affiche les modèles disponibles si présents
        try:
            models_data = response.json()
            models = models_data.get("data", [])
            
            if models:
                print(f"   📦 Modèles chargés :")
                for model in models:
                    model_id = model.get("id", "unknown")
                    print(f"      - {model_id}")
            else:
                print(f"   ⚠️ Aucun modèle chargé dans LM Studio")
        
        except Exception:
            pass  # Pas grave si on ne peut pas lister les modèles
        
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ LM Studio n'est pas accessible")
        print(f"   → Lancez LM Studio et chargez un modèle")
        return False
    
    except requests.exceptions.Timeout:
        print(f"   ⚠️ LM Studio ne répond pas (timeout)")
        return False
    
    except Exception as e:
        print(f"   ❌ Erreur lors du test : {e}")
        return False


# ═════════════════════════════════════════════════════════════
# 3. FONCTION DE FILTRAGE PAR LOTS (BATCH)
# ═════════════════════════════════════════════════════════════

def filter_batch(keyword: str, businesses: list) -> list:
    """
    Filtre un lot d'entreprises avec l'IA locale.
    
    Cette fonction prend une liste d'entreprises (avec leur texte nettoyé)
    et applique le filtrage IA sur chacune.
    
    Args:
        keyword (str): Mot-clé de recherche
        businesses (list): Liste de dictionnaires avec clé "website_text"
    
    Returns:
        list: Liste enrichie avec la clé "IA_Relevant"
    
    RÉFÉRENCE CAHIER DES CHARGES :
    Section 3.D - Filtrage IA
    """
    
    print(f"\n🤖 Filtrage IA de {len(businesses)} entreprises...")
    
    # Pour chaque entreprise, applique le filtrage IA
    for index, business in enumerate(businesses, start=1):
        
        # Récupère le texte nettoyé du site web
        website_text = business.get("website_text", "")
        
        # Si pas de texte, marque comme UNKNOWN
        if not website_text or website_text == "":
            business["IA_Relevant"] = config.VALUE_UNKNOWN
            print(f"   [{index}/{len(businesses)}] ⚠️ Pas de texte, marqué UNKNOWN")
            continue
        
        # Applique le filtrage IA
        ia_result = filter_with_ia(keyword, website_text)
        
        # Ajoute le résultat au dictionnaire
        business["IA_Relevant"] = ia_result
        
        print(f"   [{index}/{len(businesses)}] ✓ {business.get('Nom', 'UNKNOWN')} → {ia_result}")
    
    return businesses


# ═════════════════════════════════════════════════════════════
# 4. FONCTION DE NETTOYAGE DE RÉPONSE IA
# ═════════════════════════════════════════════════════════════

def clean_ia_response(raw_response: str) -> str:
    """
    Nettoie la réponse brute du modèle IA pour extraire TRUE ou FALSE.
    
    Certains modèles ajoutent du texte autour de la réponse.
    Cette fonction extrait uniquement TRUE ou FALSE.
    
    Args:
        raw_response (str): Réponse brute du modèle IA
    
    Returns:
        str: "TRUE", "FALSE" ou "UNKNOWN"
    
    Exemples:
        "TRUE" → "TRUE"
        "The answer is TRUE." → "TRUE"
        "FALSE - not relevant" → "FALSE"
        "I think maybe yes" → "UNKNOWN"
    """
    
    # Convertit en majuscules et supprime les espaces
    cleaned = raw_response.strip().upper()
    
    # Cherche le mot TRUE dans la réponse
    if "TRUE" in cleaned:
        return "TRUE"
    
    # Cherche le mot FALSE dans la réponse
    if "FALSE" in cleaned:
        return "FALSE"
    
    # Cherche des synonymes de TRUE
    if any(word in cleaned for word in ["YES", "OUI", "CORRECT", "MATCH"]):
        return "TRUE"
    
    # Cherche des synonymes de FALSE
    if any(word in cleaned for word in ["NO", "NON", "INCORRECT", "MISMATCH"]):
        return "FALSE"
    
    # Si rien de reconnu, retourne UNKNOWN
    return config.VALUE_UNKNOWN


# ═════════════════════════════════════════════════════════════
# 5. FONCTION DE GÉNÉRATION DE STATISTIQUES
# ═════════════════════════════════════════════════════════════

def get_ia_stats(businesses: list) -> dict:
    """
    Calcule des statistiques sur les résultats du filtrage IA.
    
    Args:
        businesses (list): Liste d'entreprises avec clé "IA_Relevant"
    
    Returns:
        dict: Statistiques (total, TRUE, FALSE, UNKNOWN, taux de pertinence)
    
    Exemple de retour:
        {
            "total": 50,
            "TRUE": 35,
            "FALSE": 10,
            "UNKNOWN": 5,
            "taux_pertinence": 70.0
        }
    """
    
    total = len(businesses)
    count_true = sum(1 for b in businesses if b.get("IA_Relevant") == "TRUE")
    count_false = sum(1 for b in businesses if b.get("IA_Relevant") == "FALSE")
    count_unknown = sum(1 for b in businesses if b.get("IA_Relevant") == config.VALUE_UNKNOWN)
    
    # Calcule le taux de pertinence (TRUE / total analysé)
    analyzed = count_true + count_false
    taux_pertinence = (count_true / analyzed * 100) if analyzed > 0 else 0.0
    
    return {
        "total": total,
        "TRUE": count_true,
        "FALSE": count_false,
        "UNKNOWN": count_unknown,
        "taux_pertinence": round(taux_pertinence, 2)
    }


# ═════════════════════════════════════════════════════════════
# 6. FONCTION DE RETRY AVEC BACKOFF
# ═════════════════════════════════════════════════════════════

def filter_with_retry(keyword: str, website_text: str, max_retries: int = 3) -> str:
    """
    Applique le filtrage IA avec mécanisme de retry en cas d'erreur.
    
    Si le serveur LM Studio est temporairement surchargé, cette fonction
    réessaie plusieurs fois avant de retourner UNKNOWN.
    
    Args:
        keyword (str): Mot-clé de recherche
        website_text (str): Texte nettoyé du site web
        max_retries (int): Nombre maximum de tentatives (défaut: 3)
    
    Returns:
        str: "TRUE", "FALSE" ou "UNKNOWN"
    
    RÉFÉRENCE CAHIER DES CHARGES :
    Section 4 - Contraintes critiques (robustesse)
    """
    
    import time
    
    for attempt in range(1, max_retries + 1):
        
        # Tente le filtrage IA
        result = filter_with_ia(keyword, website_text)
        
        # Si le résultat est valide (TRUE ou FALSE), retourne immédiatement
        if result in ["TRUE", "FALSE"]:
            return result
        
        # Si UNKNOWN et qu'il reste des tentatives, attend avant de réessayer
        if result == config.VALUE_UNKNOWN and attempt < max_retries:
            print(f"         → Tentative {attempt}/{max_retries} échouée, retry dans 2s...")
            time.sleep(2)  # Pause de 2 secondes entre chaque tentative
        
    # Toutes les tentatives ont échoué
    return config.VALUE_UNKNOWN


# ═════════════════════════════════════════════════════════════
# FIN DU FICHIER modules/ia_filter.py
# ═════════════════════════════════════════════════════════════
