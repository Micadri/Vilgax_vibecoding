# 🛸 PROJET VILGAX – Cahier des Charges Final
Version : 1.0 FINAL
Statut : SOURCE DE VÉRITÉ ABSOLUE
Mode : OFFLINE HARDCORE – LOCALHOST UNIQUEMENT

---

## 0. RÈGLE FONDAMENTALE

Toute implémentation DOIT :
- Se référer explicitement à ce document
- Être tracée dans un fichier de suivi
- Être commentée comme du code humain
- Ne RIEN supposer qui n’est pas écrit ici

---

## 1. CONCEPT

VILGAX est un outil de prospection B2B automatisé fonctionnant **exclusivement en local**.

Objectif :
Transformer un PC standard en outil de prospection automatisée :
- Sans abonnement
- Sans cloud
- Sans API payante

---

## 2. STACK TECHNIQUE (IMMUTABLE)

### 2.1 Environnement
- OS : Windows 10 / 11
- Exécution : Localhost
- Python : 3.9 minimum

### 2.2 Interface
- Streamlit
- Lancement via terminal :
  `streamlit run app.py`

### 2.3 Scraping
- Selenium
- Chrome visible (`headless = False`)
- ChromeDriver local

### 2.4 IA Locale
- LM Studio
- Serveur OpenAI-compatible local :
  `http://localhost:1234/v1`
- Modèle chargé manuellement par l’utilisateur

### 2.5 Stockage
- RAM uniquement
- Export final CSV
- Aucun SGBD

---

## 3. WORKFLOW FONCTIONNEL

### A. Interface Utilisateur (Streamlit)
Formulaire latéral :
- Mot-clé (string)
- Ville (string)
- Nombre de résultats (slider 1–100)
- Bouton : "LANCER L’ATTAQUE"

---

### B. Scraping Google Maps

- Source unique : https://www.google.com/maps
- Requête : "[Mot-clé] à [Ville]"
- Scroll infini de la sidebar
- Nombre demandé = **nombre d’entrées brutes Google Maps**
- Données extraites :
  - Nom
  - Adresse
  - Téléphone
  - Site web (si présent)

---

### C. Audit Technique (VILGAX)

Pour chaque entreprise AVEC site :

Pages autorisées :
- Homepage
- Page contact si lien détecté

Analyses :
- Pixel Facebook → détection `fbevents.js`
- Mobile friendly → `<meta name="viewport">`
- CMS détecté :
  - WordPress
  - Wix
  - Shopify
- Email scraping :
  - Regex
  - Si absent → `NOT_FOUND`

---

### D. Filtrage IA (LM Studio)

- Texte visible nettoyé
- Prompt système :

> "Est-ce que l'activité de cette entreprise correspond au mot-clé [X] ?  
> Réponds STRICTEMENT par TRUE ou FALSE."

- Si erreur / timeout / modèle absent :
  → `IA_Relevant = UNKNOWN`

---

### E. Output

- Tableau Streamlit en temps réel
- CSV final :
  - Séparateur `;`
  - UTF-8

Colonnes :
- Nom
- Téléphone
- Site
- Email_Scrapé
- Pixel_FB
- Mobile_OK
- CMS
- IA_Relevant

---

## 4. CONTRAINTES CRITIQUES

- Robustesse > vitesse
- Aucun crash global
- Timeouts gérés
- Pauses aléatoires
- Code modulaire
- Commentaires humains partout

---

## 5. ARCHITECTURE FICHIERS

VILGAX/
├── app.py
├── config.py
├── requirements.txt
├── modules/
│   ├── scraper_maps.py
│   ├── audit_site.py
│   ├── ia_filter.py
│   └── utils.py
├── exports/
│   └── results.csv
└── 01_SUIVI_IMPLEMENTATION.md

---

## 6. PROMPT SYSTÈME CLAUDE (INTÉGRÉ)

Claude DOIT :
- Lire ce fichier comme loi absolue
- Générer UN fichier par réponse
- Commenter chaque fonction
- Documenter chaque décision
- Ne jamais inventer de fonctionnalités