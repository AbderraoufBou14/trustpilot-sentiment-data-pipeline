
# 🧠 Trustpilot Showroomprivé Sentiment Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API%20REST-green)
![Airflow](https://img.shields.io/badge/Airflow-Orchestration-orange)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-Search-yellow)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML%20Pipeline-red)
![Docker](https://img.shields.io/badge/Docker-Compose-lightblue)
![Makefile](https://img.shields.io/badge/Automation-Makefile-lightgrey)

---

## projet

Pipeline complet de Data Engineering et de Machine Learning pour l’analyse des avis Trustpilot (cas Showroomprivé.com), conçu pour être facilement déployable et portable via Docker Compose.

Objectifs : 
    - Centraliser les avis clients collectés sur Trustpilot dans une base de données NoSQL (MongoDB Atlas).
    - Prédire automatiquement le sentiment client (positif ou négatif) grâce à un modèle de Machine Learning.
    - Alimenter des tableaux de bord Kibana pour une recherche textuelle optimisée et une analyse visuelle approfondie des avis.
    
---

## 🧩 Architecture globale
```mermaid
flowchart LR
    %% --- Daily DAG: scrape -> clean -> load ES & Mongo ---
    subgraph D[Airflow - Daily DAG]
        D1[Scraping]
        D2|JSON|[Transformation - Normalization - Mapping pour ES]
        D3[Load to MongoDB]
        D4[Load to Elasticsearch]
        D1 --> D2 --> D3; D2 --> D4
    end

    %% --- Weekly DAG: train model from MongoDB ---
    subgraph W[Airflow - Weekly DAG]
        W1[Train ML from MongoDB - ML NLP Modele: TF-IDF + LogReg]
        W2[Export model joblib]
        W1 --> W2
    end

    %% --- Storages and services ---
    M[MongoDB Atlas - clean]
    E[Elasticsearch]
    G[FastAPI API]
    K[Kibana Dashboards]

    %% --- Data flows between DAGs and storages ---
    D3 --> M
    D4 --> E
    M --> W1
    W2 --> G
    E --> K
```
## ⚙️ Commandes clés
```bash
make up-all        # Lancer toute la stack infra ( conteneurs docker )
make down-all      # Stopper les conteneurs
make logs-api      # Voir les logs FastAPI
```

## 📸 Captures (à insérer)
- docs/screenshots/kibana_dashboard.png
- docs/screenshots/api_docs.png

---

## 📈 Exemple d'utilisation
```bash
curl -X POST "http://localhost:8000/predict/v1"      -H "Content-Type: application/json"      -d '{"text": "Livraison rapide et produit conforme"}'
```
Réponse :
```json
{"label": "positive", "probability": 0.93}
```

---

## 🧱 Auteur
**Abderraouf Boukarma**  
📧 boukarmaadberraouf@gmail.com  
🔗 [GitHub](https://github.com/AbderraoufBou14)
