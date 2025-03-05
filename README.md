# Data Consulting - Analyse des Avis Clients

Application d'analyse des avis clients utilisant des techniques avancées de NLP et LLM pour extraire des insights pertinents depuis différentes plateformes d'avis.

## 🚀 Fonctionnalités

- 📊 **Collecte automatisée des avis** depuis :
  - Google Reviews
  - Apple App Store
  - Trustpilot

- 🧠 **Analyse avancée** avec :
  - Analyse de sentiment via OpenAI GPT
  - Extraction de sujets clés
  - Identification des tendances
  - Génération de KPIs

- 📈 **Visualisations interactives** :
  - Distribution des sentiments
  - Évolution des notes
  - Analyse des sujets récurrents
  - Comparaisons entre plateformes

- 🔄 **API REST complète** pour :
  - Enregistrement d'entreprises
  - Collecte d'avis
  - Analyse de texte
  - Génération de rapports

## 📋 Prérequis

- Python 3.8+
- Node.js 18+
- Clés API pour :
  - Google Places API
  - OpenAI API
  - Trustpilot API (optionnel)

## 🛠️ Installation

1. **Cloner le projet**

```bash
git clone https://github.com/votre-organisation/data-consulting.git
cd data-consulting
```

2. **Installer les dépendances Python**

```bash
cd python
pip install -r requirements.txt
```

3. **Installer les dépendances Node.js**

```bash
cd ..
npm install
```

4. **Configuration des variables d'environnement**

Créer un fichier `.env` à la racine du projet :

```env
GOOGLE_API_KEY=votre_clé_google
OPENAI_API_KEY=votre_clé_openai
TRUSTPILOT_API_KEY=votre_clé_trustpilot
FLASK_ENV=development
```

## 🚀 Démarrage

1. **Lancer le backend Flask**

```bash
cd python
python app.py
```

Le serveur démarre sur `http://localhost:5000`

2. **Lancer le frontend React**

```bash
npm run dev
```

L'application est accessible sur `http://localhost:5173`

## 📚 Documentation API

### Endpoints principaux

- `POST /api/companies` : Enregistrer une nouvelle entreprise
- `POST /api/reviews/collect` : Collecter les avis
- `POST /api/reviews/analyze` : Analyser les avis collectés
- `POST /api/reports/generate` : Générer un rapport d'analyse
- `POST /api/sentiment` : Analyser le sentiment d'un texte
- `POST /api/topics` : Extraire les sujets d'un texte

### Exemple d'utilisation

```javascript
// Enregistrer une entreprise
const response = await fetch('http://localhost:5000/api/companies', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Ma Société",
    location: "Paris, France",
    app_name: "Mon Application",
    domain: "masociete.com"
  })
});
```

## 📊 Structure du projet

```
data-consulting/
├── python/                 # Backend Flask
│   ├── app.py             # Point d'entrée Flask
│   ├── review_scraper.py  # Logique d'analyse
│   └── requirements.txt   # Dépendances Python
├── src/                   # Frontend React
│   ├── components/        # Composants React
│   ├── pages/            # Pages de l'application
│   └── App.tsx           # Composant racine
├── .env                  # Variables d'environnement
└── package.json         # Configuration Node.js
```

## 🔧 Configuration

### Google Places API

1. Créer un projet sur Google Cloud Console
2. Activer l'API Places
3. Générer une clé API
4. Ajouter la clé dans `.env`

### OpenAI API

1. Créer un compte sur OpenAI
2. Générer une clé API
3. Ajouter la clé dans `.env`

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forker le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add AmazingFeature'`)
4. Pusher sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📧 Contact

Data Consulting Team - contact@dataconsulting.com

Lien du projet : [https://github.com/votre-organisation/data-consulting](https://github.com/votre-organisation/data-consulting)