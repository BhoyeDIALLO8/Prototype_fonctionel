"""
Module de collecte et d'analyse des avis clients avec API Flask intégrée

Ce script combine:
1. La collecte des avis depuis différentes plateformes (Google, App Store, Trustpilot)
2. L'analyse des avis avec NLP et LLM (OpenAI GPT)
3. Une API REST Flask pour exposer les fonctionnalités
4. Génération de rapports et visualisations

Architecture du module:
- Classes API pour chaque plateforme (GoogleReviewsAPI, AppStoreAPI, TrustpilotAPI)
- Classe principale ReviewScraper pour orchestrer la collecte et l'analyse
- API REST Flask pour l'intégration frontend
- Utilitaires d'analyse et de traitement des données

Fonctionnalités principales:
- Collecte automatisée des avis depuis plusieurs plateformes
- Analyse de sentiment utilisant OpenAI GPT-3.5
- Extraction de sujets et de tendances
- Génération de KPIs et de rapports
- API REST pour l'intégration avec le frontend

Dépendances:
- flask: Pour l'API REST
- flask-cors: Pour gérer les requêtes cross-origin
- requests: Pour les appels API REST
- openai: Pour l'analyse de sentiment avancée
- json: Pour la manipulation des données JSON
- datetime: Pour la gestion des dates
- re: Pour le traitement des expressions régulières

Auteur: Data Consulting Team
Date: 2025
"""

import json
import re
import random
from datetime import datetime, timedelta
import os
from collections import Counter
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration des clés API et variables d'environnement
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', 'AIzaSyDrLEMdap24kyWsXVCNYb3wD91hd7U_01u')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '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')

# Configuration de l'API OpenAI
openai.api_key = OPENAI_API_KEY

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)  # Active CORS pour permettre les requêtes cross-origin

# Configuration Flask
app.config['JSON_AS_ASCII'] = False  # Support UTF-8
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite 16MB

## Classe principale pour la gestion des avis Google Places
## Gère toutes les interactions avec l'API Google Places

class GoogleReviewsAPI:
    """
    Client pour l'API Google Places Reviews.
    
    Cette classe gère l'interaction avec l'API Google Places pour:
    - Rechercher des entreprises
    - Récupérer leurs avis
    - Formater les données pour l'analyse
    
    Attributes:
        api_key (str): Clé d'API Google Places
        base_url (str): URL de base pour les requêtes API
    """

     ## Initialise le client API avec la clé d'authentification
    
    def __init__(self, api_key: str = GOOGLE_API_KEY):
        """
        Initialise le client API avec la clé d'authentification.
        
        Args:
            api_key (str): Clé d'API Google Places
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"

      ## Recherche l'ID unique d'un lieu sur Google Places
    def get_place_id(self, business_name: str, location: str) -> Optional[str]:
        """
        Recherche l'ID unique d'un lieu sur Google Places.
        
        Args:
            business_name (str): Nom de l'entreprise
            location (str): Localisation (ville, pays)
            
        Returns:
            Optional[str]: ID du lieu ou None si non trouvé
        """
        endpoint = f"{self.base_url}/findplacefromtext/json"
        params = {
            'input': f"{business_name} {location}",
            'inputtype': 'textquery',
            'fields': 'place_id',
            'key': self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['candidates']:
                return data['candidates'][0]['place_id']
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche du lieu: {e}")
            return None
        
## Récupère les avis clients pour un lieu donné
    def get_reviews(self, place_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les avis clients pour un lieu donné.
        
        Args:
            place_id (str): ID du lieu Google
            max_results (int): Nombre maximum d'avis à récupérer
            
        Returns:
            List[Dict[str, Any]]: Liste des avis formatés
        """
        endpoint = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'reviews,rating,user_ratings_total',
            'key': self.api_key,
            'language': 'fr'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                reviews = data['result'].get('reviews', [])
                return [{
                    'id': f"google_{i}",
                    'platform': 'Google Reviews',
                    'author': review['author_name'],
                    'rating': review['rating'],
                    'text': review['text'],
                    'date': datetime.fromtimestamp(review['time']).strftime('%Y-%m-%d'),
                    'language': review['language']
                } for i, review in enumerate(reviews[:max_results])]
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des avis: {e}")
            return []

## Classe pour la gestion des avis de l'App Store
## Gère la récupération et le formatage des avis depuis l'App Store
class AppStoreAPI:
    """
    Client pour l'API Apple App Store.
    
    Gère la récupération des avis depuis l'App Store en:
    - Recherchant les applications
    - Collectant leurs avis
    - Formatant les données pour l'analyse
    
    Attributes:
        base_url (str): URL de base pour les requêtes API
    """

  ## Initialise le client API App Store
    def __init__(self):
        """Initialise le client API App Store."""
        self.base_url = "https://itunes.apple.com"
    
## Recherche l'ID d'une application sur l'App Store
    def get_app_id(self, app_name: str) -> Optional[str]:
        """
        Recherche l'ID d'une application sur l'App Store.
        
        Args:
            app_name (str): Nom de l'application
            
        Returns:
            Optional[str]: ID de l'application ou None si non trouvée
        """
        endpoint = f"{self.base_url}/search"
        params = {
            'term': app_name,
            'entity': 'software',
            'country': 'fr'
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['resultCount'] > 0:
                return str(data['results'][0]['trackId'])
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche de l'application: {e}")
            return None

  ## Récupère et formate les avis d'une application
    def get_reviews(self, app_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les avis pour une application donnée.
        
        Args:
            app_id (str): ID de l'application
            max_results (int): Nombre maximum d'avis à récupérer
            
        Returns:
            List[Dict[str, Any]]: Liste des avis formatés
        """
        endpoint = f"{self.base_url}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            data = response.json()
            
            reviews = data.get('feed', {}).get('entry', [])
            if not isinstance(reviews, list):
                reviews = [reviews]
            
            return [{
                'id': f"appstore_{i}",
                'platform': 'Apple App Store',
                'author': review['author']['name']['label'],
                'rating': int(review['im:rating']['label']),
                'text': review['content']['label'],
                'date': review['updated']['label'][:10],
                'title': review['title']['label']
            } for i, review in enumerate(reviews[:max_results])]
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des avis: {e}")
            return []

## Classe pour la gestion des avis Trustpilot
## Gère l'interaction avec l'API Trustpilot et le formatage des données
class TrustpilotAPI:
    """
    Client pour l'API Trustpilot.
    
    Gère l'interaction avec l'API Trustpilot pour:
    - Identifier les entreprises
    - Collecter leurs avis
    - Formater les données pour l'analyse
    
    Attributes:
        base_url (str): URL de base de l'API
        business_units_url (str): URL pour les endpoints business
        reviews_url (str): URL pour les endpoints des avis
    """
   ## Initialise le client API Trustpilot avec les URLs de base  
    def __init__(self):
        """Initialise le client API Trustpilot."""
        self.base_url = "https://api.trustpilot.com/v1"
        self.business_units_url = f"{self.base_url}/business-units"
        self.reviews_url = f"{self.base_url}/reviews"

    ## Recherche l'ID d'une entreprise sur Trustpilot
    def get_business_unit(self, domain: str) -> Optional[str]:
        """
        Recherche l'ID d'une entreprise sur Trustpilot.
        
        Args:
            domain (str): Nom de domaine de l'entreprise
            
        Returns:
            Optional[str]: ID de l'entreprise ou None si non trouvée
        """
        endpoint = f"{self.business_units_url}/find"
        params = {'domain': domain}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return data['id']
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la recherche de l'entreprise: {e}")
            return None
        
    ## Récupère et formate les avis d'une entreprise
    def get_reviews(self, business_unit_id: str = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les avis pour une entreprise donnée.
        
        Args:
            business_unit_id (str): ID de l'entreprise
            max_results (int): Nombre maximum d'avis à récupérer
            
        Returns:
            List[Dict[str, Any]]: Liste des avis formatés
        """
        if not business_unit_id:
            return []
        
        endpoint = f"{self.reviews_url}/business-unit/{business_unit_id}"
        params = {
            'language': 'fr',
            'page': 1,
            'perPage': max_results
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            return [{
                'id': f"trustpilot_{i}",
                'platform': 'Trustpilot',
                'author': review['consumer']['displayName'],
                'rating': review['stars'],
                'text': review['text'],
                'date': review['createdAt'][:10],
                'title': review.get('title', '')
            } for i, review in enumerate(data['reviews'][:max_results])]
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des avis: {e}")
            return []

## Classe principale pour l'orchestration de la collecte et l'analyse des avis
## Coordonne toutes les opérations de collecte, analyse et génération de rapports
class ReviewScraper:
    """
    Orchestrateur principal pour la collecte et l'analyse des avis.
    
    Cette classe coordonne:
    - La collecte des avis depuis différentes plateformes
    - L'analyse de sentiment avec OpenAI
    - L'extraction des sujets
    - Le calcul des KPIs
    
    Attributes:
        business_name (str): Nom de l'entreprise
        language (str): Langue des avis à collecter
        google_api (GoogleReviewsAPI): Client API Google
        appstore_api (AppStoreAPI): Client API App Store
        trustpilot_api (TrustpilotAPI): Client API Trustpilot
        reviews (List): Liste des avis collectés
    """

## Initialise le scraper avec les paramètres de base et les clients API
    def __init__(self, business_name: str, language: str = 'fr'):
        """
        Initialise le scraper avec les paramètres de base.
        
        Args:
            business_name (str): Nom de l'entreprise
            language (str): Langue des avis (défaut: 'fr')
        """
        self.business_name = business_name
        self.language = language
        self.google_api = GoogleReviewsAPI()
        self.appstore_api = AppStoreAPI()
        self.trustpilot_api = TrustpilotAPI()
        self.reviews = []

## Collecte les avis depuis toutes les plateformes configurées
    def collect_reviews(self, max_results: int = 100) -> None:
        """
        Collecte les avis depuis toutes les plateformes configurées.
        
        Args:
            max_results (int): Nombre maximum d'avis par plateforme
        """
        # Collecte depuis Google Reviews
        place_id = self.google_api.get_place_id(self.business_name, "France")
        if place_id:
            google_reviews = self.google_api.get_reviews(place_id, max_results)
            self.reviews.extend(google_reviews)
        
        # Collecte depuis App Store
        app_id = self.appstore_api.get_app_id(self.business_name)
        if app_id:
            appstore_reviews = self.appstore_api.get_reviews(app_id, max_results)
            self.reviews.extend(appstore_reviews)
        
        # Collecte depuis Trustpilot
        business_unit_id = self.trustpilot_api.get_business_unit(f"{self.business_name}.com")
        if business_unit_id:
            trustpilot_reviews = self.trustpilot_api.get_reviews(business_unit_id, max_results)
            self.reviews.extend(trustpilot_reviews)
    
## Analyse le sentiment d'un texte avec OpenAI GPT
    def analyze_sentiment_with_openai(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un texte avec OpenAI GPT.
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            Dict[str, Any]: Résultats de l'analyse avec sentiment, score et sujets
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analysez le sentiment de l'avis suivant et attribuez-lui une note entre 0 et 1, 0 étant très négatif et 1 très positif. Identifiez également les principaux sujets mentionnés."},
                    {"role": "user", "content": text}
                ]
            )
            
            analysis = response.choices[0].message.content
            
            # Extraction du score et du sentiment
            score_match = re.search(r'(\d+(\.\d+)?)', analysis)
            score = float(score_match.group(1)) if score_match else 0.5
            
            sentiment = 'positive' if score >= 0.7 else 'negative' if score <= 0.3 else 'neutral'
            
            # Extraction des sujets
            topics_match = re.findall(r'Topics?:?\s*([^\.]+)', analysis)
            topics = [topic.strip() for topic in topics_match[0].split(',')] if topics_match else []
            
            return {
                'sentiment': sentiment,
                'score': score,
                'topics': topics,
                'confidence': 0.8
            }
            
        except Exception as e:
            print(f"Erreur lors de l'analyse du sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'topics': [],
                'confidence': 0.0
            }
        
    ## Analyse tous les avis collectés 
    def analyze_reviews(self) -> List[Dict[str, Any]]:
        """
        Analyse tous les avis collectés.
        
        Returns:
            List[Dict[str, Any]]: Liste des avis avec leur analyse
        """
        for review in self.reviews:
            sentiment_analysis = self.analyze_sentiment_with_openai(review['text'])
            review.update(sentiment_analysis)
        return self.reviews
    
    ## Calcule les KPIs à partir des avis analysés
    def calculate_kpis(self) -> Dict[str, Any]:
        """
        Calcule les KPIs à partir des avis analysés.
        
        Returns:
            Dict[str, Any]: KPIs calculés (moyennes, distributions)
        """
        if not self.reviews:
            return {
                'average_rating': 0,
                'sentiment_score': 0,
                'review_count': 0,
                'platform_distribution': {},
                'sentiment_distribution': {},
                'top_topics': []
            }
        
        # Calcul des KPIs
        ratings = [review['rating'] for review in self.reviews]
        sentiments = [review['sentiment'] for review in self.reviews if 'sentiment' in review]
        platforms = [review['platform'] for review in self.reviews]
        topics = [topic for review in self.reviews if 'topics' in review for topic in review['topics']]
        
        # Distribution des plateformes
        platform_counts = Counter(platforms)
        platform_distribution = {
            platform: count / len(self.reviews) * 100 
            for platform, count in platform_counts.items()
        }
        
        # Distribution des sentiments
        sentiment_counts = Counter(sentiments)
        sentiment_distribution = {
            sentiment: count / len(sentiments) * 100 
            for sentiment, count in sentiment_counts.items()
        }
        
        # Top sujets
        topic_counts = Counter(topics)
        top_topics = topic_counts.most_common(5)
        
        return {
            'average_rating': sum(ratings) / len(ratings),
            'sentiment_score': sentiment_distribution.get('positive', 0),
            'review_count': len(self.reviews),
            'platform_distribution': platform_distribution,
            'sentiment_distribution': sentiment_distribution,
            'top_topics': top_topics
        }
    
## Extrait les principaux sujets d'un texte avec OpenAI
    def extract_topics(self, text: str) -> List[str]:
        """
        Extrait les principaux sujets d'un texte avec OpenAI.
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            List[str]: Liste des sujets identifiés
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the main topics discussed in the following text. Return them as a comma-separated list."},
                    {"role": "user", "content": text}
                ]
            )
            
            topics = response.choices[0].message.content.split(',')
            return [topic.strip() for topic in topics]
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des sujets: {e}")
            return []

# Routes API Flask

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de vérification de l'état de l'API.
    
    Returns:
        dict: État de l'API avec timestamp
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/companies', methods=['POST'])
def register_company():
    """
    Enregistre une nouvelle entreprise pour l'analyse.
    
    Expected payload:
    {
        "name": "string",
        "location": "string",
        "app_name": "string",
        "domain": "string"
    }
    
    Returns:
        dict: Détails de l'entreprise enregistrée
    """
    try:
        data = request.get_json()
        
        # Validation des données requises
        required_fields = ['name', 'location', 'app_name', 'domain']
        if not all(field in data for field in required_fields):
            return jsonify({
                'error': 'Missing required fields',
                'required': required_fields
            }), 400
        
        # Initialisation du scraper pour l'entreprise
        global global_scraper
        global_scraper = ReviewScraper(
            business_name=data['name'],
            language='fr'
        )
        
        return jsonify({
            'message': 'Company registered successfully',
            'company': {
                'name': data['name'],
                'location': data['location'],
                'app_name': data['app_name'],
                'domain': data['domain'],
                'registered_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to register company',
            'details': str(e)
        }), 500

@app.route('/api/reviews/collect', methods=['POST'])
def collect_reviews():
    """
    Déclenche la collecte des avis pour une entreprise.
    
    Expected payload:
    {
        "platforms": ["google", "appstore", "trustpilot"],
        "limit_per_platform": number
    }
    
    Returns:
        dict: Résumé de la collecte des avis
    """
    try:
        if global_scraper is None:
            return jsonify({
                'error': 'No company registered. Please register a company first.'
            }), 400
        
        data = request.get_json()
        platforms = data.get('platforms', ['google', 'appstore', 'trustpilot'])
        limit = data.get('limit_per_platform', 100)
        
        # Collecte des avis depuis chaque plateforme
        reviews_count = {
            'google': 0,
            'appstore': 0,
            'trustpilot': 0
        }
        
        if 'google' in platforms:
            google_reviews = global_scraper.google_api.get_reviews(
                place_id='example_place_id',
                max_results=limit
            )
            reviews_count['google'] = len(google_reviews)
            global_scraper.reviews.extend(google_reviews)
        
        if 'appstore' in platforms:
            appstore_reviews = global_scraper.appstore_api.get_reviews(
                app_id='example_app_id',
                max_results=limit
            )
            reviews_count['appstore'] = len(appstore_reviews)
            global_scraper.reviews.extend(appstore_reviews)
        
        if 'trustpilot' in platforms:
            trustpilot_reviews = global_scraper.trustpilot_api.get_reviews(
                max_results=limit
            )
            reviews_count['trustpilot'] = len(trustpilot_reviews)
            global_scraper.reviews.extend(trustpilot_reviews)
        
        return jsonify({
            'message': 'Reviews collected successfully',
            'total_reviews': len(global_scraper.reviews),
            'reviews_per_platform': reviews_count
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to collect reviews',
            'details': str(e)
        }), 500

@app.route('/api/reviews/analyze', methods=['POST'])
def analyze_reviews():
    """
    Analyse les avis collectés.
    
    Returns:
        dict: Résultats de l'analyse avec KPIs
    """
    try:
        if global_scraper is None:
            return jsonify({
                'error': 'No company registered. Please register a company first.'
            }), 400
        
        if not global_scraper.reviews:
            return jsonify({
                'error': 'No reviews to analyze. Please collect reviews first.'
            }), 400
        
        # Analyse des avis
        analyzed_reviews = global_scraper.analyze_reviews()
        
        # Calcul des KPIs
        kpis = global_scraper.calculate_kpis()
        
        return jsonify({
            'message': 'Reviews analyzed successfully',
            'kpis': kpis,
            'reviews_count': len(analyzed_reviews)
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to analyze reviews',
            'details': str(e)
        }), 500

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """
    Génère un rapport complet d'analyse.
    
    Expected payload:
    {
        "format": "json",
        "include_reviews": boolean
    }
    
    Returns:
        dict: Rapport d'analyse complet
    """
    try:
        if global_scraper is None:
            return jsonify({
                'error': 'No company registered. Please register a company first.'
            }), 400
        
        data = request.get_json()
        include_reviews = data.get('include_reviews', True)
        
        # Génération du rapport
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "business_name": global_scraper.business_name,
                "total_reviews": len(global_scraper.reviews)
            },
            "kpis": global_scraper.calculate_kpis()
        }
        
        if include_reviews:
            report["reviews"] = global_scraper.reviews
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to generate report',
            'details': str(e)
        }), 500

@app.route('/api/sentiment', methods=['POST'])
def analyze_text_sentiment():
    """
    Analyse le sentiment d'un texte donné.
    
    Expected payload:
    {
        "text": "string"
    }
    
    Returns:
        dict: Résultat de l'analyse de sentiment
    """
    try:
        data = request.get_json()
        
        if 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text'
            }), 400
        
        if global_scraper is None:
            global_scraper = ReviewScraper("temp", "fr")
        
        # Analyse du sentiment
        sentiment_analysis = global_scraper.analyze_sentiment_with_openai(data['text'])
        
        return jsonify({
            'sentiment': sentiment_analysis['sentiment'],
            'score': sentiment_analysis['score'],
            'confidence': sentiment_analysis['confidence']
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to analyze sentiment',
            'details': str(e)
        }), 500

@app.route('/api/topics', methods=['POST'])
def extract_topics():
    """
    Extrait les sujets d'un texte donné.
    
    Expected payload:
    {
        "text": "string"
    }
    
    Returns:
        dict: Sujets identifiés
    """
    try:
        data = request.get_json()
        
        if 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text'
            }), 400
        
        if global_scraper is None:
            global_scraper = ReviewScraper("temp", "fr")
        
        # Extraction des sujets
        topics = global_scraper.extract_topics(data['text'])
        
        return jsonify({
            'topics': topics
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to extract topics',
            'details': str(e)
        }), 500

def main():
    """
    Point d'entrée principal de l'application.
    Configure et démarre le serveur Flask.
    """
    # Configuration du port et du mode debug
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Démarrage du serveur
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main()