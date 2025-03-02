# Prototype d'Analyse des Avis Clients (Version Python)

Ce projet est un prototype pour l'analyse des avis clients utilisant des techniques de NLP. Il récupère les avis de Google Reviews, les traite à l'aide du traitement du langage naturel, et génère des insights.

## Fonctionnalités

- Récupération des avis de Google Reviews
- Analyse de sentiment et extraction de mots-clés
- Analyse basée sur les catégories
- Insights générés
- Tableau de bord interactif pour la visualisation
- Export de données en CSV

## Stack Technique

- **Backend**: Python avec Flask
- **Traitement NLP**: Techniques NLP personnalisées en Python
- **Frontend**: HTML, CSS, JavaScript avec Bootstrap et Chart.js
- **Export de Données**: CSV natif Python

## Instructions d'Installation

1. Cloner le dépôt
2. Installer les dépendances:
   ```
   pip install -r requirements.txt
   ```
3. Démarrer le serveur:
   ```
   python app.py
   ```
4. Ouvrir votre navigateur et accéder à `http://localhost:3000`

## Structure du Projet

- `app.py`: Application principale Flask et logique d'analyse
- `templates/`: Fichiers HTML pour le frontend
- `static/`: Fichiers CSS, JavaScript et autres ressources statiques
- `exports/`: Dossier pour les fichiers CSV exportés

## Utilisation

1. Entrer un nom d'entreprise dans le tableau de bord
2. Spécifier le nombre d'avis à analyser
3. Cliquer sur "Analyser" pour démarrer le processus
4. Visualiser les résultats dans le tableau de bord
5. Exporter les données pour une analyse plus approfondie

## Limitations

- Le prototype actuel utilise des données simulées à des fins de démonstration
- Pour une utilisation en production, vous devriez implémenter une logique de scraping appropriée ou utiliser des API officielles

## Améliorations Futures

- Ajouter le support pour plus de sources d'avis (Trustpilot, App Store)
- Implémenter des techniques NLP plus avancées
- Ajouter l'authentification utilisateur et les rapports sauvegardés
- Implémenter la surveillance en temps réel des nouveaux avis