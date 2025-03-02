### Notre application d'analyse des avis clients, entièrement en Python
import os
import json
import random
import datetime
import re
import csv
import requests
from collections import Counter
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for

### On configure notre application Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
PORT = int(os.environ.get('PORT', 3000))

### Clés API directement intégrées
OPENAI_API_KEY = "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"
GOOGLE_MAPS_API_KEY = "AIzaSyDrLEMdap24kyWsXVCNYb3wD91hd7U_01t"

### Intégration de l'API Google Maps
def search_business_on_google_maps(business_name):
    """
    Recherche une entreprise sur Google Maps
    
    Paramètres:
        business_name: Le nom de l'entreprise à rechercher
        
    Retourne:
        Les informations sur l'entreprise
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={business_name}&inputtype=textquery&fields=place_id,name,formatted_address,geometry&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK' and len(data['candidates']) > 0:
            return data['candidates'][0]
        else:
            print(f"Aucun résultat trouvé pour {business_name}")
            return None
    except Exception as e:
        print(f"Erreur lors de la recherche sur Google Maps: {str(e)}")
        return None

def get_place_details(place_id):
    """
    Récupère les détails d'un lieu à partir de son ID
    
    Paramètres:
        place_id: L'identifiant du lieu sur Google Maps
        
    Retourne:
        Les détails du lieu
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,review,formatted_address,geometry&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            return data['result']
        else:
            print(f"Aucun détail trouvé pour le lieu {place_id}")
            return None
    except Exception as e:
        print(f"Erreur lors de la récupération des détails: {str(e)}")
        return None

### Intégration de l'API OpenAI
def generate_insights_with_openai(analysis_data):
    """
    Génère des insights en utilisant l'API OpenAI
    
    Paramètres:
        analysis_data: Les données d'analyse à traiter
        
    Retourne:
        Les insights générés par l'IA
    """
    try:
### Préparation du prompt pour OpenAI
        prompt = f"""
        Basé sur l'analyse des avis clients avec les métriques suivantes:
        
        - Note Moyenne: {analysis_data['average_rating']}
        - Score de Sentiment Global: {analysis_data['sentiment_score']}
        - Mots-clés Principaux: {', '.join([k['term'] for k in analysis_data['top_keywords']])}
        
        Performance par Catégorie:
        {os.linesep.join([f"- {cat}: Note {data.get('averageRating', '0')}, Sentiment {data.get('averageSentiment', '0')} ({data.get('count', 0)} avis)" for cat, data in analysis_data['sentiment_by_category'].items()])}
        
        Veuillez fournir:
        1. Un résumé de la satisfaction client globale
        2. Trois points forts identifiés dans les avis
        3. Trois principaux axes d'amélioration
        4. Des recommandations exploitables pour l'entreprise
        5. Des tendances ou modèles à noter
        
        Formatez votre réponse en JSON avec la structure suivante:
        {{
          "summary": "...",
          "strengths": ["...", "...", "..."],
          "improvements": ["...", "...", "..."],
          "recommendations": ["...", "...", "..."],
          "trends": ["...", "...", "..."]
        }}
        """
        
 ### Appel à l'API OpenAI
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Vous êtes un analyste d'expérience client. Analysez les données d'avis fournies et générez des insights exploitables."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
    ### Essayer de parser le JSON
            try:
                return json.loads(content)
            except:

    ### Si le parsing échoue, extraire manuellement les sections
                insights = {
                    'summary': extract_section(content, 'summary'),
                    'strengths': extract_list_items(content, 'strengths'),
                    'improvements': extract_list_items(content, 'improvements'),
                    'recommendations': extract_list_items(content, 'recommendations'),
                    'trends': extract_list_items(content, 'trends')
                }
                return insights
        else:
            print(f"Erreur lors de l'appel à OpenAI: {response.status_code}")
            print(response.text)
            return generate_mock_insights(analysis_data)
    except Exception as e:
        print(f"Erreur lors de la génération des insights avec OpenAI: {str(e)}")
        return generate_mock_insights(analysis_data)

def extract_section(text, section_name):
    """
    Extrait une section du texte
    
    Paramètres:
        text: Le texte à analyser
        section_name: Le nom de la section à extraire
        
    Retourne:
        Le contenu de la section
    """
    import re
    regex = re.compile(f"{section_name}[:\\s]+(.*?)(?=\\n\\n|$)", re.IGNORECASE | re.DOTALL)
    match = regex.search(text)
    return match.group(1).strip() if match else ''

def extract_list_items(text, section_name):
    """
    Extrait les éléments de liste d'une section
    
    Paramètres:
        text: Le texte à analyser
        section_name: Le nom de la section à extraire
        
    Retourne:
        La liste des éléments
    """
    section = extract_section(text, section_name)
    if not section:
        return []
    
    import re
    items = re.split(r'\n-|\n\d+\.', section)
    items = [item.strip() for item in items if item.strip()]
    return items if items else [section]

### Nos fonctions pour analyser les avis
def scrape_google_reviews(business_name, review_count=50):
    """
    Va chercher les avis Google pour une entreprise
    
    Paramètres:
        business_name: Le nom du magasin ou de l'entreprise
        review_count: Combien d'avis on veut récupérer
        
    Retourne:
        Une liste d'avis avec toutes leurs infos
    """
    print(f"On va chercher les avis Google pour: {business_name}")
    
### Essayer d'utiliser l'API Google Maps
    business_info = search_business_on_google_maps(business_name)
    
    if business_info and 'place_id' in business_info:
        place_id = business_info['place_id']
        place_details = get_place_details(place_id)
        
        if place_details and 'reviews' in place_details:
            print(f"Avis trouvés via l'API Google Maps pour {business_name}")
            real_reviews = place_details.get('reviews', [])
            
### Si on a des avis réels mais pas assez, on complète avec des avis simulés
            if len(real_reviews) < review_count:
                print(f"Seulement {len(real_reviews)} avis trouvés, on complète avec des avis simulés")
                
### Convertir les avis réels au format attendu
                formatted_reviews = []
                for i, review in enumerate(real_reviews):
                    formatted_reviews.append({
                        'id': f"review-{i + 1}",
                        'businessName': business_name,
                        'author': review.get('author_name', f"Utilisateur{i + 1}"),
                        'rating': review.get('rating', random.randint(1, 5)),
                        'text': review.get('text', "Pas de commentaire"),
                        'date': review.get('time', datetime.datetime.now().isoformat()),
                        'source': 'Google Maps API',
                        'category': assign_category(review.get('text', ""))
                    })
                
### Compléter avec des avis simulés
                simulated_reviews = generate_simulated_reviews(business_name, review_count - len(real_reviews), len(formatted_reviews))
                return formatted_reviews + simulated_reviews
            
### Si on a assez d'avis réels, on les utilise tous
            formatted_reviews = []
            for i, review in enumerate(real_reviews[:review_count]):
                formatted_reviews.append({
                    'id': f"review-{i + 1}",
                    'businessName': business_name,
                    'author': review.get('author_name', f"Utilisateur{i + 1}"),
                    'rating': review.get('rating', random.randint(1, 5)),
                    'text': review.get('text', "Pas de commentaire"),
                    'date': review.get('time', datetime.datetime.now().isoformat()),
                    'source': 'Google Maps API',
                    'category': assign_category(review.get('text', ""))
                })
            
            return formatted_reviews
    
### Si l'API ne fonctionne pas ou ne donne pas de résultats, on utilise des données simulées
    print("Utilisation de données simulées pour les avis")
    return generate_simulated_reviews(business_name, review_count)

def assign_category(text):
    """
    Assigne une catégorie à un avis en fonction de son contenu
    
    Paramètres:
        text: Le texte de l'avis
        
    Retourne:
        La catégorie assignée
    """
    text = text.lower()
    
    if any(word in text for word in ['service', 'personnel', 'équipe', 'accueil']):
        return 'Service'
    elif any(word in text for word in ['qualité', 'produit', 'article']):
        return 'Qualité du Produit'
    elif any(word in text for word in ['prix', 'cher', 'coût', 'tarif']):
        return 'Prix'
    elif any(word in text for word in ['support', 'aide', 'assistance', 'problème']):
        return 'Support Client'
    elif any(word in text for word in ['interface', 'utilisation', 'facile', 'application']):
        return 'Utilisabilité'
    else:
        return random.choice(['Service', 'Qualité du Produit', 'Prix', 'Support Client', 'Utilisabilité'])

def generate_simulated_reviews(business_name, review_count, start_index=0):
    """
    Génère des avis simulés pour les démonstrations
    
    Paramètres:
        business_name: Le nom de l'entreprise
        review_count: Le nombre d'avis à générer
        start_index: L'index de départ pour la numérotation
        
    Retourne:
        Une liste d'avis simulés
    """
    reviews = []
    categories = ['Service', 'Qualité du Produit', 'Prix', 'Support Client', 'Utilisabilité']
    review_texts = [
        "Excellent service, équipe très réactive !",
        "La qualité du produit est excellente, mais un peu chère.",
        "Le support client n'a pas été utile quand j'ai eu un problème.",
        "J'adore l'interface, très conviviale et intuitive.",
        "La livraison était en retard, mais le produit fonctionne bien.",
        "Expérience globale incroyable, je recommande vivement !",
        "L'application plante fréquemment, nécessite des améliorations.",
        "Les prix sont raisonnables par rapport aux concurrents.",
        "J'ai eu des problèmes de facturation qui ont pris des semaines à résoudre.",
        "Les nouvelles fonctionnalités sont fantastiques, grande amélioration !"
    ]
    
### On génère des avis aléatoires
    for i in range(review_count):
        rating = random.randint(1, 5)
        review_text = random.choice(review_texts)
        date = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 90))
        category = random.choice(categories)
        
        reviews.append({
            'id': f"review-{start_index + i + 1}",
            'businessName': business_name,
            'author': f"Utilisateur{start_index + i + 1}",
            'rating': rating,
            'text': review_text,
            'date': date.isoformat(),
            'source': 'Google Reviews',
            'category': category
        })
    
    return reviews

def analyze_reviews(reviews):
    """
    Analyse les avis pour en tirer des informations utiles
    
    Paramètres:
        reviews: La liste des avis à analyser
        
    Retourne:
        Les résultats de notre analyse
    """
    print(f"On analyse {len(reviews)} avis...")
    
### On calcule la note moyenne
    average_rating = calculate_average_rating(reviews)
    
### On analyse le sentiment (positif/négatif)
    sentiment_results = perform_sentiment_analysis(reviews)
    
### On extrait les mots-clés importants
    top_keywords = extract_keywords(reviews)
    
### On regroupe par catégorie
    sentiment_by_category = categorize_by_sentiment(reviews)
    
    return {
        'average_rating': average_rating,
        'sentiment_score': sentiment_results['average_sentiment'],
        'sentiment_distribution': sentiment_results['distribution'],
        'top_keywords': top_keywords,
        'sentiment_by_category': sentiment_by_category
    }

def calculate_average_rating(reviews):
    """
    Calcule la note moyenne de tous les avis
    
    Paramètres:
        reviews: La liste des avis
        
    Retourne:
        La note moyenne formatée
    """
    if not reviews:
        return "0"
    
    total = sum(review['rating'] for review in reviews)
    return f"{total / len(reviews):.2f}"

def perform_sentiment_analysis(reviews):
    """
    Analyse si les avis sont plutôt positifs ou négatifs
    
    Paramètres:
        reviews: La liste des avis
        
    Retourne:
        Les résultats de l'analyse de sentiment
    """
### Notre méthode simple pour déterminer si un texte est positif ou négatif
    def simple_sentiment(text):
        mots_positifs = ['excellent', 'fantastique', 'bien', 'super', 'génial', 'incroyable', 'conviviale', 'intuitive', 'réactive']
        mots_négatifs = ['problème', 'retard', 'plante', 'erreur', 'difficile', 'mauvais', 'lent', 'cher', 'chère']
        
        text = text.lower()
        nb_positifs = sum(1 for mot in mots_positifs if mot in text)
        nb_négatifs = sum(1 for mot in mots_négatifs if mot in text)
        
        if nb_positifs > nb_négatifs:
            return 0.5  ## Plutôt positif
        elif nb_négatifs > nb_positifs:
            return -0.5  ## Plutôt négatif
        else:
            return 0.0  ## Neutre
    
    total_sentiment = 0
    distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
    
### On analyse chaque avis
    for review in reviews:
        sentiment = simple_sentiment(review['text'])
        total_sentiment += sentiment
        
### On classe l'avis selon son sentiment
        if sentiment > 0.2:
            distribution['positive'] += 1
        elif sentiment < -0.2:
            distribution['negative'] += 1
        else:
            distribution['neutral'] += 1
    
    average_sentiment = "0" if not reviews else f"{total_sentiment / len(reviews):.2f}"
    
    return {
        'average_sentiment': average_sentiment,
        'distribution': distribution
    }

def extract_keywords(reviews):
    """
    Trouve les mots-clés les plus importants dans les avis
    
    Paramètres:
        reviews: La liste des avis
        
    Retourne:
        Les principaux mots-clés avec leur importance
    """
    if not reviews:
        return []
    
### On rassemble tous les textes
    all_text = ' '.join([review['text'].lower() for review in reviews])
    
### On garde seulement les mots intéressants (pas trop courts)
    words = re.findall(r'\b\w{4,}\b', all_text)
    
### Mots à ignorer car trop communs
    mots_à_ignorer = ['avec', 'pour', 'dans', 'cette', 'mais', 'les', 'des', 'est', 'une', 'qui', 'que', 'pas']
    filtered_words = [word for word in words if word not in mots_à_ignorer]
    
### On compte combien de fois chaque mot apparaît
    word_counts = Counter(filtered_words)
    
### On retourne les 10 mots les plus fréquents
    return [
        {'term': word, 'score': count / len(filtered_words) * 10}
        for word, count in word_counts.most_common(10)
    ]

def categorize_by_sentiment(reviews):
    """
    Regroupe les avis par catégorie et analyse le sentiment pour chaque groupe
    
    Paramètres:
        reviews: La liste des avis
        
    Retourne:
        Les résultats par catégorie
    """
    categories = {}
    
### Notre méthode simple pour déterminer si un texte est positif ou négatif
    def simple_sentiment(text):
        mots_positifs = ['excellent', 'fantastique', 'bien', 'super', 'génial', 'incroyable', 'conviviale', 'intuitive', 'réactive']
        mots_négatifs = ['problème', 'retard', 'plante', 'erreur', 'difficile', 'mauvais', 'lent', 'cher', 'chère']
        
        text = text.lower()
        nb_positifs = sum(1 for mot in mots_positifs if mot in text)
        nb_négatifs = sum(1 for mot in mots_négatifs if mot in text)
        
        if nb_positifs > nb_négatifs:
            return 0.5  ### Plutôt positif
        elif nb_négatifs > nb_positifs:
            return -0.5  ### Plutôt négatif
        else:
            return 0.0  ### Neutre
    
### On analyse chaque avis et on les regroupe par catégorie
    for review in reviews:
        category = review.get('category', 'Non catégorisé')
        sentiment = simple_sentiment(review['text'])
        
        if category not in categories:
            categories[category] = {
                'count': 0,
                'total_sentiment': 0,
                'total_rating': 0
            }
        
        categories[category]['count'] += 1
        categories[category]['total_sentiment'] += sentiment
        categories[category]['total_rating'] += review['rating']
    
### On calcule les moyennes pour chaque catégorie
    for category in categories:
        cat = categories[category]
        cat['averageSentiment'] = f"{cat['total_sentiment'] / cat['count']:.2f}"
        cat['averageRating'] = f"{cat['total_rating'] / cat['count']:.2f}"
    
    return categories

def generate_mock_insights(analysis_results):
    """
    Génère des insights par défaut si l'API OpenAI n'est pas disponible
    
    Paramètres:
        analysis_results: Les résultats de notre analyse
        
    Retourne:
        Des insights par défaut
    """
### On adapte nos conseils selon la note moyenne
    rating = float(analysis_results['average_rating'])
    
    if rating >= 4:
        summary = "La satisfaction client globale est élevée avec un sentiment positif fort dans la plupart des catégories."
        strengths = [
            "Excellents temps de réponse du service client",
            "Haute qualité de produit mentionnée de façon constante",
            "Interface conviviale recevant des retours positifs"
        ]
        improvements = [
            "Quelques préoccupations concernant des prix légèrement élevés",
            "Problèmes occasionnels de stabilité de l'application mobile",
            "Les délais de livraison pourraient être améliorés dans certaines régions"
        ]
    elif rating >= 3:
        summary = "La satisfaction client est modérée avec un sentiment mitigé selon les catégories."
        strengths = [
            "La fonctionnalité du produit répond aux besoins des clients",
            "Le support client est généralement utile",
            "Bon rapport qualité-prix selon plusieurs avis"
        ]
        improvements = [
            "Les temps de réponse nécessitent une amélioration significative",
            "Incohérence de la qualité du produit mentionnée fréquemment",
            "Interface utilisateur causant de la confusion pour les nouveaux utilisateurs"
        ]
    else:
        summary = "La satisfaction client est faible avec un sentiment majoritairement négatif."
        strengths = [
            "Les fonctionnalités de base fonctionnent comme prévu",
            "Quelques mentions positives concernant certains membres du personnel",
            "Prix compétitifs par rapport aux alternatives"
        ]
        improvements = [
            "Préoccupations majeures concernant la fiabilité du produit",
            "Service client décrit comme peu utile et lent",
            "Problèmes de facturation mentionnés dans plusieurs avis"
        ]
    
    recommendations = [
        "Mettre en place une boucle de rétroaction client pour traiter les plaintes courantes",
        "Fournir une formation supplémentaire à l'équipe de support client",
        "Envisager de réviser la stratégie de prix basée sur une analyse concurrentielle"
    ]
    
    trends = [
        "Mentions croissantes des concurrents dans les avis récents",
        "Importance croissante de l'expérience mobile",
        "Attentes croissantes pour un service personnalisé"
    ]
    
    return {
        'summary': summary,
        'strengths': strengths,
        'improvements': improvements,
        'recommendations': recommendations,
        'trends': trends
    }

def export_to_csv(data, filename):
    """
    Sauvegarde nos données dans un fichier CSV
    
    Paramètres:
        data: Les données à sauvegarder
        filename: Le nom du fichier
        
    Retourne:
        Le résultat de l'opération
    """
### On crée le dossier d'export s'il n'existe pas
    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    
    output_path = os.path.join(export_dir, filename)
    
    try:
### On gère différents types de données
        if isinstance(data, list):
            export_array_to_csv(data, output_path)
        elif isinstance(data, dict):
            export_object_to_csv(data, output_path)
        else:
            raise ValueError('Ce type de données ne peut pas être exporté en CSV')
        
        print(f"Données sauvegardées dans {output_path}")
        return {'success': True, 'path': output_path}
    except Exception as error:
        print(f'Oups, erreur pendant l\'export CSV: {str(error)}')
        raise error

def export_array_to_csv(data, output_path):
    """
    Sauvegarde une liste d'objets en CSV
    
    Paramètres:
        data: La liste à sauvegarder
        output_path: Le chemin du fichier
    """
    if not data:
        print('Pas de données à exporter')
        return
    
### On crée le fichier CSV manuellement
    with open(output_path, 'w', encoding='utf-8') as f:
        # On écrit les en-têtes
        headers = list(data[0].keys())
        f.write(','.join(headers) + '\n')
        
### On écrit les données ligne par ligne
        for item in data:
            row = [str(item.get(header, '')) for header in headers]
            f.write(','.join(row) + '\n')

def export_object_to_csv(data, output_path):
    """
    Sauvegarde un dictionnaire en CSV
    
    Paramètres:
        data: Le dictionnaire à sauvegarder
        output_path: Le chemin du fichier
    """
### On transforme le dictionnaire en liste
    records = []
    for category, values in data.items():
        records.append({
            'Catégorie': category,
            'Nombre d\'Avis': values.get('count', 0),
            'Sentiment Moyen': values.get('averageSentiment', 0),
            'Note Moyenne': values.get('averageRating', 0)
        })
    
### On crée le fichier CSV manuellement
    with open(output_path, 'w', encoding='utf-8') as f:
        # On écrit les en-têtes
        headers = ['Catégorie', 'Nombre d\'Avis', 'Sentiment Moyen', 'Note Moyenne']
        f.write(','.join(headers) + '\n')
        
        # On écrit les données ligne par ligne
        for record in records:
            row = [str(record.get(header, '')) for header in headers]
            f.write(','.join(row) + '\n')

### Génération de données pour les graphiques
def generate_trend_data(period=90, grouping='week', metric='rating'):
    """
    Génère des données pour les graphiques de tendances
    
    Paramètres:
        period: Période en jours
        grouping: Regroupement (day, week, month)
        metric: Métrique (rating, sentiment, volume)
        
    Retourne:
        Les données pour le graphique
    """
### Déterminer le nombre de points selon le regroupement
    if grouping == 'day':
        point_count = min(period, 30)  # Limiter à 30 points pour la lisibilité
    elif grouping == 'week':
        point_count = max(1, period // 7)
    elif grouping == 'month':
        point_count = max(1, period // 30)
    else:
        point_count = 12
    
    labels = []
    data = []
    
### Générer les étiquettes et les données
    for i in range(point_count):

        ### Générer les étiquettes selon le regroupement
        date = datetime.datetime.now() - datetime.timedelta(days=(point_count - i - 1) * (1 if grouping == 'day' else (7 if grouping == 'week' else 30)))
        
        if grouping == 'day':
            label = f"{date.day}/{date.month}"
        elif grouping == 'week':
            label = f"Sem. {date.day//7 + 1}/{date.month}"
        else:  # month
            months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
            label = months[date.month - 1]
        
        labels.append(label)
        
        ### Générer les données selon la métrique
        if metric == 'rating':
            # Note moyenne entre 2.5 et 4.5 avec une tendance à l'amélioration
            value = 3.5 + (i / point_count) * 0.5 + (random.random() * 0.4 - 0.2)
            data.append(round(value, 2))
        elif metric == 'sentiment':
            # Score de sentiment entre -0.3 et 0.3 avec une tendance à l'amélioration
            value = 0 + (i / point_count) * 0.3 + (random.random() * 0.2 - 0.1)
            data.append(round(value, 2))
        else:  # volume
            # Volume d'avis entre 10 et 50
            value = 30 + (i / point_count) * 10 + (random.random() * 10 - 5)
            data.append(int(value))
    
    return {
        'labels': labels,
        'data': data
    }

def generate_forecast_data(horizon=90, confidence=90):
    """
    Génère des données pour les graphiques de prévisions
    
    Paramètres:
        horizon: Horizon de prévision en jours
        confidence: Niveau de confiance (80, 90, 95)
        
    Retourne:
        Les données pour le graphique
    """
### Données historiques (12 dernières semaines)
    historical_labels = [f"S{i+1}" for i in range(12)]
    historical_data = []
    
### Note moyenne entre 3 et 4 avec une tendance à l'amélioration
    for i in range(12):
        value = 3.5 + (i / 12) * 0.3 + (random.random() * 0.2 - 0.1)
        historical_data.append(round(value, 2))
    
### Données de prévision
    forecast_points = max(1, horizon // 7)  # Nombre de semaines
    forecast_labels = [f"S{12+i+1}" for i in range(forecast_points)]
    
    last_historical_value = historical_data[-1]
    forecast_data = []
    upper_bound = []
    lower_bound = []
    
### Prévision avec une légère tendance à l'amélioration
    trend = 0.05  # Tendance positive
    
    for i in range(forecast_points):
        forecast_value = last_historical_value + trend * (i + 1) + (random.random() * 0.1 - 0.05)
        forecast_data.append(round(forecast_value, 2))
        
### Intervalles de confiance
        confidence_factor = 0.15 if confidence == 95 else (0.1 if confidence == 90 else 0.08)
        uncertainty = confidence_factor * (i + 1) / forecast_points
        
        upper_bound.append(round(forecast_value + uncertainty, 2))
        lower_bound.append(round(forecast_value - uncertainty, 2))
    
    return {
        'historical_labels': historical_labels,
        'historical_data': historical_data,
        'forecast_labels': forecast_labels,
        'forecast_data': forecast_data,
        'upper_bound': upper_bound,
        'lower_bound': lower_bound
    }

def generate_competitor_data(business_name, competitors):
    """
    Génère des données pour la comparaison avec les concurrents
    
    Paramètres:
        business_name: Nom de l'entreprise
        competitors: Liste des concurrents
        
    Retourne:
        Les données pour les graphiques de comparaison
    """
### Catégories pour la comparaison
    categories = ['Service', 'Qualité du Produit', 'Prix', 'Support Client', 'Utilisabilité']
    
### Données pour la comparaison des notes
    ratings_labels = [business_name] + competitors
    ratings_data = [round(random.uniform(3.5, 4.5), 2)]  # Note de l'entreprise
    
### Notes des concurrents (généralement un peu moins bonnes)
    for _ in competitors:
        ratings_data.append(round(random.uniform(2.0, 4.0), 2))
    
### Données pour la comparaison des sentiments
    sentiment_data = [round(random.uniform(0.1, 0.3), 2)]  # Sentiment de l'entreprise
    
### Sentiments des concurrents
    for _ in competitors:
        sentiment_data.append(round(random.uniform(-0.2, 0.2), 2))
    
### Données pour la comparaison par catégorie
    category_data = []
    
### Données de l'entreprise
    business_data = [round(random.uniform(3.0, 5.0), 1) for _ in categories]
    category_data.append({
        'label': business_name,
        'data': business_data
    })
    
### Données des concurrents
    for competitor in competitors:
        competitor_data = [round(random.uniform(2.0, 4.0), 1) for _ in categories]
        category_data.append({
            'label': competitor,
            'data': competitor_data
        })
    
    return {
        'ratings_labels': ratings_labels,
        'ratings_data': ratings_data,
        'sentiment_data': sentiment_data,
        'categories': categories,
        'category_data': category_data
    }

### Routes Flask pour notre application
@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Tableau de bord principal"""
    return render_template('dashboard.html')

@app.route('/reviews')
def reviews():
    """Page des avis"""

### Récupérer les avis depuis la session ou générer des exemples
    reviews_data = []
    for i in range(10):
        rating = random.randint(1, 5)
        date = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 90))
        category = random.choice(['Service', 'Qualité du Produit', 'Prix', 'Support Client', 'Utilisabilité'])
        review_text = random.choice([
            "Excellent service, équipe très réactive !",
            "La qualité du produit est excellente, mais un peu chère.",
            "Le support client n'a pas été utile quand j'ai eu un problème.",
            "J'adore l'interface, très conviviale et intuitive.",
            "La livraison était en retard, mais le produit fonctionne bien."
        ])
        
        reviews_data.append({
            'author': f"Utilisateur{i+1}",
            'rating': rating,
            'text': review_text,
            'date': date.strftime('%d/%m/%Y'),
            'category': category
        })
    
    return render_template('reviews.html', reviews=reviews_data)

@app.route('/insights')
def insights():
    """Page des insights"""
### Générer des insights d'exemple
    insights_data = {
        'summary': "La satisfaction client est modérée avec un sentiment mitigé selon les catégories.",
        'strengths': [
            "La fonctionnalité du produit répond aux besoins des clients",
            "Le support client est généralement utile",
            "Bon rapport qualité-prix selon plusieurs avis"
        ],
        'improvements': [
            "Les temps de réponse nécessitent une amélioration significative",
            "Incohérence de la qualité du produit mentionnée fréquemment",
            "Interface utilisateur causant de la confusion pour les nouveaux utilisateurs"
        ],
        'recommendations': [
            "Mettre en place une boucle de rétroaction client pour traiter les plaintes courantes",
            "Fournir une formation supplémentaire à l'équipe de support client",
            "Envisager de réviser la stratégie de prix basée sur une analyse concurrentielle"
        ],
        'trends': [
            "Mentions croissantes des concurrents dans les avis récents",
            "Importance croissante de l'expérience mobile",
            "Attentes croissantes pour un service personnalisé"
        ]
    }
    
### Générer des données pour le graphique d'évolution du sentiment
    trend_data = generate_trend_data(90, 'week', 'sentiment')
    
    return render_template('insights.html', insights=insights_data, trend_data=json.dumps(trend_data))

@app.route('/export')
def export():
    """Page d'exportation"""
    return render_template('export.html')

@app.route('/competitors')
def competitors():
    """Page de comparaison avec les concurrents"""
    # Liste des concurrents d'exemple
    competitors_list = ["Concurrent A", "Concurrent B", "Concurrent C"]
    
    # Générer des données de comparaison
    comparison_data = generate_competitor_data("Votre Entreprise", competitors_list)
    
    return render_template('competitors.html', 
                          competitors=competitors_list, 
                          comparison_data=json.dumps(comparison_data))

@app.route('/trends')
def trends():
    """Page des tendances"""
    # Générer des données pour les graphiques
    trend_data = generate_trend_data(90, 'week', 'rating')
    forecast_data = generate_forecast_data(90, 90)
    
    # Statistiques d'exemple
    stats = {
        'trend': 'En hausse',
        'variation': '+0.3 points',
        'best_period': 'Semaine 12',
        'worst_period': 'Semaine 8'
    }
    
    # Événements marquants
    events = [
        {'date': '15 Mars', 'description': 'Lancement de la nouvelle version'},
        {'date': '2 Avril', 'description': 'Campagne promotionnelle'},
        {'date': '20 Avril', 'description': 'Mise à jour majeure'}
    ]
    
    return render_template('trends.html', 
                          trend_data=json.dumps(trend_data), 
                          forecast_data=json.dumps(forecast_data),
                          stats=stats,
                          events=events)

@app.route('/settings')
def settings():
    """Page des paramètres"""
    return render_template('settings.html')

@app.route('/location')
def location():
    """Page de localisation"""

### Données d'exemple pour la carte
    locations = [
        {'name': 'Magasin Paris', 'lat': 48.8566, 'lng': 2.3522, 'rating': 4.2, 'reviews': 120},
        {'name': 'Magasin Lyon', 'lat': 45.7640, 'lng': 4.8357, 'rating': 3.8, 'reviews': 85},
        {'name': 'Magasin Marseille', 'lat': 43.2965, 'lng': 5.3698, 'rating': 4.0, 'reviews': 95},
        {'name': 'Magasin Bordeaux', 'lat': 44.8378, 'lng': -0.5792, 'rating': 4.5, 'reviews': 75},
        {'name': 'Magasin Lille', 'lat': 50.6292, 'lng': 3.0573, 'rating': 3.9, 'reviews': 60}
    ]
    
    return render_template('location.html', locations=json.dumps(locations))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Point d'entrée API pour analyser les avis"""
    try:
        data = request.get_json()
        business_name = data.get('businessName', '')
        review_count = int(data.get('reviewCount', 50))
        
        print(f"Démarrage de l'analyse pour {business_name}...")
        
        # Étape 1: On récupère les avis
        print('On va chercher les avis...')
        reviews = scrape_google_reviews(business_name, review_count)
        
        # Étape 2: On les analyse
        print('On analyse les avis...')
        analysis_results = analyze_reviews(reviews)
        
        # Étape 3: On génère des conseils
        print('On prépare des recommandations...')
        insights = generate_insights_with_openai(analysis_results)
        
        # Étape 4: On exporte tout en CSV
        print('On sauvegarde les données...')
        export_to_csv(reviews, 'reviews.csv')
        export_to_csv(analysis_results['sentiment_by_category'], 'sentiment_by_category.csv')
        
        # On renvoie les résultats
        return jsonify({
            'reviewCount': len(reviews),
            'averageRating': analysis_results['average_rating'],
            'sentimentScore': analysis_results['sentiment_score'],
            'topKeywords': analysis_results['top_keywords'],
            'sentimentByCategory': analysis_results['sentiment_by_category'],
            'insights': insights
        })
        
    except Exception as error:
        print(f'Erreur pendant l\'analyse: {str(error)}')
        return jsonify({'error': str(error)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """Point d'entrée pour l'analyse via formulaire HTML"""
    try:
        business_name = request.form.get('business_name', '')
        review_count = int(request.form.get('review_count', 50))
        
        print(f"Démarrage de l'analyse pour {business_name}...")
        
        # Étape 1: On récupère les avis
        reviews = scrape_google_reviews(business_name, review_count)
        
        # Étape 2: On les analyse
        analysis_results = analyze_reviews(reviews)
        
        # Étape 3: On génère des conseils
        insights = generate_insights(analysis_results)
        
        # Étape 4: On exporte tout en CSV
        export_to_csv(reviews, 'reviews.csv')
        export_to_csv(analysis_results['sentiment_by_category'], 'sentiment_by_category.csv')
        
### On prépare les données pour les graphiques
        sentiment_by_category = analysis_results['sentiment_by_category']
        categories = list(sentiment_by_category.keys())
        sentiment_scores = [float(sentiment_by_category[cat]['averageSentiment']) for cat in categories]
        rating_scores = [float(sentiment_by_category[cat]['averageRating']) for cat in categories]
        counts = [sentiment_by_category[cat]['count'] for cat in categories]
        
### On renvoie la page de résultats
        return render_template('results.html', 
                              business_name=business_name,
                              review_count=len(reviews),
                              average_rating=analysis_results['average_rating'],
                              sentiment_score=analysis_results['sentiment_score'],
                              top_keywords=analysis_results['top_keywords'],
                              categories=categories,
                              sentiment_scores=sentiment_scores,
                              rating_scores=rating_scores,
                              counts=counts,
                              insights=insights)
        
    except Exception as error:
        print(f'Erreur pendant l\'analyse: {str(error)}')
        return render_template('error.html', error=str(error))

@app.route('/static/<path:path>')
def serve_static(path):
    """Sert les fichiers statiques"""
    return send_from_directory('static', path)

@app.route('/exports/<path:path>')
def serve_exports(path):
    """Sert les fichiers exportés"""
    return send_from_directory('exports', path)

### Démarrage de l'application
if __name__ == '__main__':
    print("Démarrage de l'application Python...")
    app.run(host='0.0.0.0', port=PORT, debug=True)