"""
╔═══════════════════════════════════════════════════════════════╗
║                 VILGAX - modules/scraper_maps.py              ║
║              Module de Scraping Google Maps UNIVERSEL         ║
╚═══════════════════════════════════════════════════════════════╝
"""

import time
import random
import re
from typing import List, Dict, Optional, Tuple, Set

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)

# Import pour le géocodage (conversion ville → coordonnées GPS)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

import config
from modules.utils import format_url


# ═════════════════════════════════════════════════════════════
# 0. FONCTION DE GÉOCODAGE UNIVERSELLE
# ═════════════════════════════════════════════════════════════

def get_city_coordinates(city: str, country: str = "Belgium") -> Optional[Tuple[float, float]]:
    """
    Convertit un nom de ville en coordonnées GPS (latitude, longitude).
    Utilise Nominatim (OpenStreetMap) pour géocoder n'importe quelle ville
    du monde sans dictionnaire prédéfini.

    Args:
        city (str): Nom de la ville (ex: "Namur", "Paris", "Montréal")
        country (str): Pays pour affiner la recherche (défaut: "Belgium")

    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) ou None si échec
    """
    try:
        # Initialise le géocodeur avec un user-agent
        geolocator = Nominatim(user_agent="vilgax_prospection_bot")

        # Construit la requête : "Ville, Pays"
        location_query = f"{city}, {country}"
        print(f"  🌍 Géocodage de '{location_query}'...")

        # Cherche la localisation
        location = geolocator.geocode(location_query, timeout=10)

        if location:
            lat = location.latitude
            lon = location.longitude
            print(f"  ✓ Coordonnées trouvées : {lat}, {lon}")
            return (lat, lon)
        else:
            print(f"  ⚠️ Ville '{city}' introuvable")
            return None

    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"  ⚠️ Erreur de géocodage : {e}")
        return None
    except Exception as e:
        print(f"  ❌ Erreur inattendue lors du géocodage : {e}")
        return None


# ═════════════════════════════════════════════════════════════
# 1. FONCTION PRINCIPALE DE SCRAPING
# ═════════════════════════════════════════════════════════════

def scrape_google_maps(keyword: str, city: str, num_results: int) -> List[Dict[str, str]]:
    """
    Scrape Google Maps avec géocodage automatique universel et détection de duplicatas.
    """
    results = []
    seen_businesses: Set[str] = set()  # NOUVEAU : Set pour tracker les noms déjà vus
    driver = None

    try:
        # ─────────────────────────────────────────────────────────
        # 1.1 Géocodage de la ville (AUTOMATIQUE)
        # ─────────────────────────────────────────────────────────
        print(config.MSG_SCRAPING_START)
        print(f"🔍 Recherche : '{keyword}' à '{city}' ({num_results} résultats)")

        # Convertit la ville en coordonnées GPS
        coordinates = get_city_coordinates(city)
        if not coordinates:
            print(f"❌ Impossible de géocoder '{city}', abandon du scraping")
            return results

        lat, lon = coordinates

        # ─────────────────────────────────────────────────────────
        # 1.2 Initialisation de Chrome
        # ─────────────────────────────────────────────────────────
        chrome_options = webdriver.ChromeOptions()
        chrome_options.headless = config.CHROME_HEADLESS
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-geolocation")

        # OVERRIDE de la géolocalisation avec les coordonnées de la ville
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })

        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(config.IMPLICIT_WAIT)
        driver.maximize_window()

        # FORCE la géolocalisation via JavaScript
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
            "latitude": lat,
            "longitude": lon,
            "accuracy": 100
        })
        print(f"  📍 Géolocalisation forcée à : {lat}, {lon}")

        # ─────────────────────────────────────────────────────────
        # 1.3 Construction de l'URL avec coordonnées FORCÉES
        # ─────────────────────────────────────────────────────────
        # Format Google Maps : /maps/search/keyword/@lat,lng,15z
        zoom = "13z"  # Zoom adapté pour une ville
        search_query = keyword.replace(' ', '+')

        # URL avec coordonnées FORCÉES dans l'URL
        search_url = f"{config.GOOGLE_MAPS_URL}/search/{search_query}/@{lat},{lon},{zoom}"
        print(f"🌐 URL Google Maps : {search_url}")

        # Charge la page
        driver.get(search_url)

        # Attente longue pour éviter que Google Maps redirige
        time.sleep(5)

        # RE-FORCE les coordonnées après chargement (au cas où Google redirige)
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
            "latitude": lat,
            "longitude": lon,
            "accuracy": 100
        })

        # Vérifie qu'on est bien sur la bonne ville
        try:
            page_title = driver.title
            print(f"  📍 Page chargée : {page_title}")

            # Si la ville demandée n'apparaît pas dans le titre, on recharge
            if city.lower() not in page_title.lower():
                print(f"  ⚠️ Redirection détectée, rechargement forcé...")

                # Recharge avec une requête encore plus explicite
                explicit_url = f"{config.GOOGLE_MAPS_URL}/search/{search_query}+{city.replace(' ', '+')}/@{lat},{lon},{zoom}"
                driver.get(explicit_url)
                time.sleep(5)
        except:
            pass

        # Pause finale
        time.sleep(random.uniform(config.PAUSE_MIN, config.PAUSE_MAX))

        # ─────────────────────────────────────────────────────────
        # 1.4 Scroll de la sidebar
        # ─────────────────────────────────────────────────────────
        print(f"📜 Scroll de la sidebar pour charger {num_results} résultats...")

        sidebar_selector = "div[role='feed']"

        try:
            sidebar = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, sidebar_selector))
            )
        except TimeoutException:
            print("⚠️ Impossible de trouver la sidebar des résultats")
            return results

        scroll_count = 0
        previous_count = 0
        stale_scroll_count = 0

        while scroll_count < config.MAX_SCROLLS:
            current_results = driver.find_elements(
                By.CSS_SELECTOR,
                "a[href*='/maps/place/']"
            )
            current_count = len(current_results)
            print(f"  → {current_count} résultats chargés...")

            # MODIFICATION : On continue à scroller jusqu'à avoir assez de résultats UNIQUES
            if len(results) >= num_results:
                print(f"✅ {num_results} résultats uniques atteints !")
                break

            if current_count == previous_count:
                stale_scroll_count += 1
                if stale_scroll_count >= 3:
                    print(f"⚠️ Fin des résultats disponibles ({current_count} trouvés)")
                    break
            else:
                stale_scroll_count = 0

            previous_count = current_count

            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight",
                sidebar
            )

            time.sleep(random.uniform(1.5, 3))
            scroll_count += 1

        # ─────────────────────────────────────────────────────────
        # 1.5 Extraction des données avec détection de duplicatas
        # ─────────────────────────────────────────────────────────
        print(f"\n📊 Extraction des données des entreprises...")

        business_links = driver.find_elements(
            By.CSS_SELECTOR,
            "a[href*='/maps/place/']"
        )

        # MODIFICATION : On itère sur TOUS les liens, mais on s'arrête quand on a num_results UNIQUES
        for index, link in enumerate(business_links, start=1):
            # Arrêt si on a déjà le nombre de résultats uniques souhaité
            if len(results) >= num_results:
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(0.5)

                link.click()
                time.sleep(random.uniform(2, 3))

                business_data = extract_business_data(driver)

                if business_data.get("Nom") and business_data["Nom"] != config.VALUE_NOT_FOUND:
                    business_name = business_data["Nom"]
                    
                    # NOUVEAU : Vérification des duplicatas
                    if business_name in seen_businesses:
                        print(f"  [{len(results)+1}/{num_results}] ⚠️ DUPLICATA ignoré : {business_name}")
                        continue
                    
                    # Ajoute le nom au set de tracking
                    seen_businesses.add(business_name)
                    
                    # Ajoute aux résultats
                    results.append(business_data)
                    print(f"  [{len(results)}/{num_results}] ✓ {business_name}")
                else:
                    print(f"  [?/{num_results}] ✗ Nom introuvable")

                time.sleep(random.uniform(config.PAUSE_MIN, config.PAUSE_MAX))

            except (StaleElementReferenceException, NoSuchElementException) as e:
                print(f"  [?/{num_results}] ⚠️ Erreur : {e}")
                continue
            except Exception as e:
                print(f"  [?/{num_results}] ❌ Erreur : {e}")
                continue

        print(f"\n✅ Scraping terminé : {len(results)} entreprises UNIQUES extraites")

    except WebDriverException as e:
        print(f"❌ Erreur Selenium : {e}")
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
    finally:
        if driver:
            print("🔒 Fermeture du navigateur Chrome...")
            driver.quit()

    return results


# ═════════════════════════════════════════════════════════════
# 2. EXTRACTION DES DONNÉES D'UNE ENTREPRISE
# ═════════════════════════════════════════════════════════════

def extract_business_data(driver) -> Dict[str, str]:
    """
    Extrait les données d'une entreprise depuis le panneau Google Maps.
    """
    data = {
        "Nom": config.VALUE_NOT_FOUND,
        "Adresse": config.VALUE_NOT_FOUND,
        "Téléphone": config.VALUE_NOT_FOUND,
        "Site": config.VALUE_NOT_FOUND
    }

    # NOM
    try:
        name_element = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf.lfPIob")
        data["Nom"] = name_element.text.strip()
    except:
        try:
            name_element = driver.find_element(By.TAG_NAME, "h1")
            if name_element.is_displayed():
                data["Nom"] = name_element.text.strip()
        except:
            try:
                title = driver.title
                if " - Google Maps" in title:
                    data["Nom"] = title.replace(" - Google Maps", "").strip()
                elif title and title != "Google Maps":
                    data["Nom"] = title.strip()
            except:
                pass

    if data["Nom"] and data["Nom"] != config.VALUE_NOT_FOUND:
        data["Nom"] = ' '.join(data["Nom"].split())
        data["Nom"] = re.sub(r'[★☆]\s*[\d.,]+\s*·?\s*', '', data["Nom"])

    # ADRESSE
    try:
        address_button = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
        aria_label = address_button.get_attribute("aria-label")
        data["Adresse"] = aria_label.replace("Adresse:", "").replace("Adresse :", "").strip()
    except:
        try:
            address_element = driver.find_element(By.XPATH, "//button[contains(@data-item-id, 'address')]")
            aria_label = address_element.get_attribute("aria-label")
            data["Adresse"] = aria_label.replace("Adresse:", "").replace("Adresse :", "").strip()
        except:
            pass

    # TÉLÉPHONE
    try:
        phone_button = driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
        aria_label = phone_button.get_attribute("aria-label")
        data["Téléphone"] = aria_label.replace("Téléphone:", "").replace("Téléphone :", "").strip()
    except:
        try:
            phone_element = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Téléphone') or contains(@aria-label, 'Phone')]")
            aria_label = phone_element.get_attribute("aria-label")
            data["Téléphone"] = aria_label.replace("Téléphone:", "").replace("Téléphone :", "").replace("Phone:", "").strip()
        except:
            pass

    # SITE WEB
    try:
        website_link = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
        raw_url = website_link.get_attribute("href").strip()
        data["Site"] = format_url(raw_url)
    except:
        try:
            website_link = driver.find_element(By.XPATH, "//a[contains(@data-item-id, 'authority') or contains(@aria-label, 'Site')]")
            raw_url = website_link.get_attribute("href").strip()
            data["Site"] = format_url(raw_url)
        except:
            pass

    return data


def validate_num_results(num_results: int) -> int:
    """Valide le nombre de résultats."""
    if num_results < config.MIN_RESULTS:
        return config.MIN_RESULTS
    if num_results > config.MAX_RESULTS:
        return config.MAX_RESULTS
    return num_results
