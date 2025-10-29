# 🚀 API de Prédiction de Sentiment — Projet Satisfaction Client

Cette API (FastAPI) permet d’analyser les **avis clients Trustpilot** (Showroomprivé) et de prédire leur **sentiment** à l’aide d’un modèle de Machine Learning (TF-IDF + Logistic Regression).

## ⚙️ etapes pour déployer l'api dans un container docker:

Ouvres le fichier `.env` et mets à jour:
2- L’adresse IP de la machine qui héberge la BDD. (eventuellement le motde passe et le username de la bdd)
3- le nom de la base de données 
4- le nom de la collection. 
Exemple :

```env
MONGO_URI=mongodb://datascientest:dst123@34.242.218.34:27017/showroomprive_db?authSource=admin
MONGO_DB=showroomprive_db 
MONGO_COL=avis

5- Construire et lancer le container:

docker compose build --no-cache
docker compose up -d

=====================================================================
🌍 Accéder à l’API

Swagger : 👉 http://localhost:8000/docs

Healthcheck : curl http://localhost:8000/health

=====================================================================
---------------------
Exemples de requêtes:
---------------------

la Route /predict:

curl -X POST "http://localhost:8000/predict/v1" \
     -H "Content-Type: application/json" \
     -d '{"text": "Livraison rapide et produit conforme, très satisfait."}'

la Route /avis:

curl -X GET "http://localhost:8000/avis?stars=5&langue=fr&date_from=2024-01-01&limit=10" \
     -H "accept: application/json"


la Route /stats:

curl -X GET "http://localhost:8000/stats?pays=FR&langue=fr&date_from=2024-01-01" \
     -H "accept: application/json"


## 📂 Structure du projet

Projet_satisfaction_etape_4/
├── app/ # Code source principal (routes, services, modèles, etc.)
├── artifacts/ # Contient le modèle entraîné (.joblib)
├── docker-compose.yml
├── Dockerfile
├── .env.docker # Variables d’environnement (à modifier)
└── requirements.txt
