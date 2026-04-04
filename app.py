"""
╔═══════════════════════════════════════════════════════════════╗
║                    VILGAX - app.py                             ║
║           Interface Utilisateur Streamlit                      ║
╚═══════════════════════════════════════════════════════════════╝

RÔLE :
Fichier principal de l'application VILGAX. Gère l'interface utilisateur
avec Streamlit et orchestre l'appel aux modules de scraping, audit et IA.

PLACE DANS L'ARCHITECTURE :
- Point d'entrée de l'application (lancé via : streamlit run app.py)
- Importe config.py pour les constantes
- Appelle les modules dans modules/ pour le traitement
- Affiche les résultats en temps réel et génère le CSV final

RÉFÉRENCE CAHIER DES CHARGES :
- Section 2.2 : Interface Streamlit
- Section 3.A : Interface Utilisateur (formulaire latéral)
- Section 3.E : Output (tableau temps réel + CSV)
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Import de la configuration centrale
import config

# Import des modules VILGAX
from modules.scraper_maps import scrape_google_maps
from modules.audit_site import audit_website
from modules.ia_filter import filter_with_ia, test_lm_studio_connection
from modules.utils import export_to_csv, calculate_stats, print_stats


# ═════════════════════════════════════════════════════════════
# 1. CONFIGURATION DE LA PAGE STREAMLIT
# ═════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="VILGAX",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ═════════════════════════════════════════════════════════════
# 2. INITIALISATION DU DOSSIER D'EXPORT
# ═════════════════════════════════════════════════════════════

config.init_folders()


# ═════════════════════════════════════════════════════════════
# 3. INITIALISATION DE LA SESSION STREAMLIT
# ═════════════════════════════════════════════════════════════

if 'results' not in st.session_state:
    st.session_state.results = []

if 'is_running' not in st.session_state:
    st.session_state.is_running = False


# ═════════════════════════════════════════════════════════════
# 4. EN-TÊTE DE L'APPLICATION
# ═════════════════════════════════════════════════════════════

st.title(config.APP_TITLE)

st.markdown("""
**Mode OFFLINE HARDCORE** – Localhost uniquement  
Prospection B2B automatisée sans abonnement, sans cloud, sans API payante.
""")

st.divider()


# ═════════════════════════════════════════════════════════════
# 5. BARRE LATÉRALE - FORMULAIRE DE RECHERCHE
# ═════════════════════════════════════════════════════════════

with st.sidebar:
    
    st.header("⚙️ Paramètres de recherche")
    
    keyword = st.text_input(
        label="🔍 Mot-clé",
        value="",
        placeholder="Ex: plombier, restaurant, avocat...",
        help="Le type d'entreprise que vous recherchez"
    )
    
    city = st.text_input(
        label="📍 Ville",
        value="",
        placeholder="Ex: Bruxelles, Charleroi, Liège...",
        help="La ville où chercher les entreprises"
    )
    
    num_results = st.slider(
        label="📊 Nombre de résultats",
        min_value=config.MIN_RESULTS,
        max_value=config.MAX_RESULTS,
        value=config.DEFAULT_RESULTS,
        step=1,
        help="Nombre d'entreprises à scraper sur Google Maps"
    )
    
    st.markdown("---")
    
    launch_button = st.button(
        label=config.LAUNCH_BUTTON_TEXT,
        type="primary",
        use_container_width=True,
        disabled=st.session_state.is_running
    )
    
    st.markdown("---")
    
    st.subheader("🤖 IA Locale")
    
    st.code(config.LM_STUDIO_BASE_URL, language="text")
    
    st.info("Assurez-vous que LM Studio est lancé avec un modèle chargé.")


# ═════════════════════════════════════════════════════════════
# 6. ZONE PRINCIPALE - CONTENEURS D'AFFICHAGE
# ═════════════════════════════════════════════════════════════

status_container = st.container()
results_container = st.container()
export_container = st.container()


# ═════════════════════════════════════════════════════════════
# 7. LOGIQUE DE LANCEMENT DU SCRAPING (VERSION FINALE)
# ═════════════════════════════════════════════════════════════

if launch_button:
    
    if not keyword.strip():
        st.error("⚠️ Veuillez saisir un mot-clé de recherche.")
    
    elif not city.strip():
        st.error("⚠️ Veuillez saisir une ville.")
    
    else:
        # Réinitialise les résultats
        st.session_state.results = []
        st.session_state.is_running = True
        
        # Conteneur de statut unique
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            st.info(f"🚀 Lancement de VILGAX : **{keyword}** à **{city}** ({num_results} résultats)")
        
        # ─────────────────────────────────────────────────────────
        # ÉTAPE 1 : SCRAPING GOOGLE MAPS
        # ─────────────────────────────────────────────────────────
        
        with status_placeholder.container():
            st.info("🔍 Scraping Google Maps en cours...")
        
        raw_businesses = scrape_google_maps(keyword, city, num_results)
        
        if not raw_businesses or len(raw_businesses) == 0:
            with status_placeholder.container():
                st.error("❌ Aucune entreprise trouvée sur Google Maps")
            st.session_state.is_running = False
            st.stop()
        
        with status_placeholder.container():
            st.success(f"✅ {len(raw_businesses)} entreprises scrapées depuis Google Maps")
        
        # ─────────────────────────────────────────────────────────
        # ÉTAPE 2 : AUDIT TECHNIQUE + FILTRAGE IA
        # ─────────────────────────────────────────────────────────
        
        with status_placeholder.container():
            st.info("🔬 Audit technique et filtrage IA en cours...")
            progress_bar = st.progress(0)
            progress_text = st.empty()
        
        # Test de connexion LM Studio
        lm_studio_available = test_lm_studio_connection()
        
        # Pour chaque entreprise
        for index, business in enumerate(raw_businesses):
            
            # Met à jour la progression
            progress = (index + 1) / len(raw_businesses)
            progress_bar.progress(progress)
            progress_text.text(f"Traitement : {index + 1}/{len(raw_businesses)} - {business.get('Nom', 'UNKNOWN')}")
            
            # Initialise les valeurs par défaut
            business["Email_Scrapé"] = config.VALUE_NOT_FOUND
            business["Pixel_FB"] = "NON"
            business["Mobile_OK"] = "NON"
            business["CMS"] = config.VALUE_NOT_FOUND
            business["IA_Relevant"] = config.VALUE_UNKNOWN
            
            # Récupère l'URL du site
            site_url = business.get("Site", "")
            
            # Si l'entreprise a un site web
            if site_url and site_url != config.VALUE_NOT_FOUND:
                
                # AUDIT TECHNIQUE
                audit_data, cleaned_text = audit_website(site_url)
                
                # Enrichit les données
                business.update(audit_data)
                
                # FILTRAGE IA
                if lm_studio_available and cleaned_text and cleaned_text.strip():
                    ia_result = filter_with_ia(keyword, cleaned_text)
                    business["IA_Relevant"] = ia_result
            
            # Ajoute à la liste
            st.session_state.results.append(business)
        
        # Nettoie les éléments de progression
        progress_bar.empty()
        progress_text.empty()
        
        # ─────────────────────────────────────────────────────────
        # ÉTAPE 3 : EXPORT CSV
        # ─────────────────────────────────────────────────────────
        
        with status_placeholder.container():
            st.info("💾 Export CSV en cours...")
        
        csv_path = export_to_csv(st.session_state.results)
        
        # ─────────────────────────────────────────────────────────
        # ÉTAPE 4 : STATISTIQUES
        # ─────────────────────────────────────────────────────────
        
        stats = calculate_stats(st.session_state.results)
        print_stats(stats)
        
        with status_placeholder.container():
            st.success("🎉 Process VILGAX terminé avec succès !")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total entreprises", stats['total'])
            
            with col2:
                st.metric("Avec site web", stats['with_website'])
            
            with col3:
                st.metric("Avec email", stats['with_email'])
            
            with col4:
                st.metric("IA Pertinents", stats['ia_true'])
        
        # Fin du process
        st.session_state.is_running = False


# ═════════════════════════════════════════════════════════════
# 8. AFFICHAGE DU TABLEAU DE RÉSULTATS
# ═════════════════════════════════════════════════════════════

if len(st.session_state.results) > 0 and not st.session_state.is_running:
    
    with results_container:
        
        st.subheader("📋 Résultats de la prospection")
        
        df_results = pd.DataFrame(st.session_state.results)
        
        st.dataframe(
            df_results,
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"**Total : {len(st.session_state.results)} entreprise(s)**")


# ═════════════════════════════════════════════════════════════
# 9. BOUTON D'EXPORT CSV
# ═════════════════════════════════════════════════════════════

if len(st.session_state.results) > 0:
    
    with export_container:
        
        st.markdown("---")
        
        csv_data = pd.DataFrame(st.session_state.results).to_csv(
            sep=config.CSV_SEPARATOR,
            index=False,
            encoding=config.CSV_ENCODING
        )
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"results_{timestamp}.csv"
        
        st.download_button(
            label="💾 Télécharger le CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
        st.success(f"✅ Fichier prêt : **{filename}**")


# ═════════════════════════════════════════════════════════════
# 10. PIED DE PAGE
# ═════════════════════════════════════════════════════════════

st.divider()

st.caption("""
🛸 **VILGAX** – Version 1.0 FINAL  
Mode OFFLINE HARDCORE – Localhost uniquement  
Stack : Python 3.9+ | Streamlit | Selenium | LM Studio
""")
