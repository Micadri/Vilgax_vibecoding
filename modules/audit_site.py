"""
╔═══════════════════════════════════════════════════════════════╗
║              VILGAX - modules/audit_site.py                    ║
║              VERSION FINALE - EXTRACTION MAXIMALE              ║
╚═══════════════════════════════════════════════════════════════╝
"""

import re
import requests
from typing import Dict, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

import config


# ═════════════════════════════════════════════════════════════
# 1. FONCTION PRINCIPALE
# ═════════════════════════════════════════════════════════════

def audit_website(url: str) -> Tuple[Dict[str, str], str]:
    """
    Audite un site web avec Selenium UNIQUEMENT pour garantir la qualité maximale.
    """
    
    audit_data = {
        "Email_Scrapé": config.VALUE_NOT_FOUND,
        "Pixel_FB": "NON",
        "Mobile_OK": "NON",
        "CMS": config.VALUE_NOT_FOUND
    }
    
    cleaned_text = ""
    
    if not url or url == config.VALUE_NOT_FOUND:
        return audit_data, cleaned_text
    
    url = normalize_url(url)
    
    print(f"   🔬 Audit Selenium de : {url}")
    
    return audit_with_selenium(url)


# ═════════════════════════════════════════════════════════════
# 2. AUDIT AVEC SELENIUM (MODE PRODUCTION)
# ═════════════════════════════════════════════════════════════

def audit_with_selenium(url: str) -> Tuple[Dict[str, str], str]:
    """
    Audit complet avec Selenium pour capturer le JavaScript.
    """
    
    audit_data = {
        "Email_Scrapé": config.VALUE_NOT_FOUND,
        "Pixel_FB": "NON",
        "Mobile_OK": "NON",
        "CMS": config.VALUE_NOT_FOUND
    }
    
    cleaned_text = ""
    driver = None
    
    try:
        # Configure Chrome en mode headless
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        
        # Lance Chrome
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(15)
        
        # Charge la page
        driver.get(url)
        
        # Attend que le JavaScript charge (3 secondes)
        time.sleep(3)
        
        # Scroll pour charger le lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Récupère le HTML final
        html_content = driver.page_source
        
        # Parse avec BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extrait le texte visible
        cleaned_text = soup.get_text(separator=" ", strip=True)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # ─────────────────────────────────────────────────────────
        # PIXEL FACEBOOK
        # ─────────────────────────────────────────────────────────
        
        if 'fbevents.js' in html_content or 'facebook-pixel' in html_content.lower():
            audit_data["Pixel_FB"] = "OUI"
        
        # ─────────────────────────────────────────────────────────
        # MOBILE FRIENDLY
        # ─────────────────────────────────────────────────────────
        
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta or 'viewport' in html_content.lower():
            audit_data["Mobile_OK"] = "OUI"
        
        # ─────────────────────────────────────────────────────────
        # CMS DÉTECTION (ÉTENDUE)
        # ─────────────────────────────────────────────────────────
        
        html_lower = html_content.lower()
        
        # WordPress
        if any(sign in html_lower for sign in ['wp-content', 'wp-includes', '/wp-json/', 'wordpress', 'wp-admin']):
            audit_data["CMS"] = "WordPress"
        
        # Wix
        elif any(sign in html_lower for sign in ['wix.com', 'wixstatic', 'x-wix-', '_wix', 'wix-']):
            audit_data["CMS"] = "Wix"
        
        # Shopify
        elif any(sign in html_lower for sign in ['cdn.shopify.com', 'shopify', 'shopify-cdn']):
            audit_data["CMS"] = "Shopify"
        
        # Webflow
        elif 'webflow' in html_lower:
            audit_data["CMS"] = "Webflow"
        
        # Squarespace
        elif 'squarespace' in html_lower:
            audit_data["CMS"] = "Squarespace"
        
        # Détection générique via generator
        if audit_data["CMS"] == config.VALUE_NOT_FOUND:
            generator_meta = soup.find('meta', attrs={'name': 'generator'})
            if generator_meta:
                generator_content = generator_meta.get('content', '').lower()
                if 'wordpress' in generator_content:
                    audit_data["CMS"] = "WordPress"
                elif 'wix' in generator_content:
                    audit_data["CMS"] = "Wix"
                elif 'shopify' in generator_content:
                    audit_data["CMS"] = "Shopify"
        
        # ─────────────────────────────────────────────────────────
        # EMAIL EXTRACTION (ULTRA-ROBUSTE)
        # ─────────────────────────────────────────────────────────
        
        # Méthode 1 : Recherche dans le texte visible
        emails = extract_emails_ultra(cleaned_text)
        
        if emails:
            audit_data["Email_Scrapé"] = emails[0]
            print(f"      ✓ Email trouvé dans le texte visible : {emails[0]}")
        else:
            # Méthode 2 : Recherche dans le HTML brut
            emails_html = extract_emails_ultra(html_content)
            
            if emails_html:
                audit_data["Email_Scrapé"] = emails_html[0]
                print(f"      ✓ Email trouvé dans le HTML : {emails_html[0]}")
            else:
                # Méthode 3 : Recherche dans les liens mailto:
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                
                if mailto_links:
                    email_from_mailto = mailto_links[0]['href'].replace('mailto:', '').split('?')[0].strip()
                    audit_data["Email_Scrapé"] = email_from_mailto
                    print(f"      ✓ Email trouvé via mailto : {email_from_mailto}")
                else:
                    # Méthode 4 : Recherche dans les attributs data-* et autres
                    all_text = soup.get_text() + ' ' + str(soup)
                    emails_final = extract_emails_ultra(all_text)
                    
                    if emails_final:
                        audit_data["Email_Scrapé"] = emails_final[0]
                        print(f"      ✓ Email trouvé dans les attributs : {emails_final[0]}")
        
        print(f"      ✓ Audit terminé : {audit_data}")
    
    except TimeoutException:
        print(f"      ⚠️ Timeout Selenium (15s)")
    
    except WebDriverException as e:
        print(f"      ⚠️ Erreur Selenium : {e}")
    
    except Exception as e:
        print(f"      ❌ Erreur critique : {e}")
    
    finally:
        if driver:
            driver.quit()
    
    return audit_data, cleaned_text


# ═════════════════════════════════════════════════════════════
# 3. EXTRACTION EMAIL ULTRA-ROBUSTE
# ═════════════════════════════════════════════════════════════

def extract_emails_ultra(text: str) -> list:
    """
    Extraction email avec regex ultra-permissive et filtrage intelligent.
    """
    
    # Regex email très permissive
    email_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    emails_raw = re.findall(email_pattern, text, re.IGNORECASE)
    
    # Filtre les faux positifs
    valid_emails = []
    
    # Extensions de fichiers à exclure
    invalid_extensions = [
        '.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.svg', '.webp', 
        '.ico', '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf'
    ]
    
    # Domaines génériques à exclure
    invalid_domains = [
        'example.com', 'test.com', 'domain.com', 'email.com', 
        'mail.com', 'yoursite.com', 'yourdomain.com', 'sib.com',
        'schema.org', 'www.w3.org'
    ]
    
    for email in emails_raw:
        email_clean = email.strip().lower()
        
        # Exclut les fichiers
        if any(ext in email_clean for ext in invalid_extensions):
            continue
        
        # Exclut les domaines génériques
        if any(domain in email_clean for domain in invalid_domains):
            continue
        
        # Exclut les emails trop courts ou invalides
        if len(email_clean) < 6 or email_clean.count('@') != 1:
            continue
        
        # Exclut les emails se terminant par des caractères bizarres
        if email_clean.endswith(('.', ',', ';', ':', '!')):
            email_clean = email_clean[:-1]
        
        valid_emails.append(email_clean)
    
    # Retire les doublons tout en gardant l'ordre
    return list(dict.fromkeys(valid_emails))


# ═════════════════════════════════════════════════════════════
# 4. HELPERS
# ═════════════════════════════════════════════════════════════

def normalize_url(url: str) -> str:
    """Normalise une URL."""
    url = url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    return url
