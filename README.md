
# 🧠 Trustpilot Showroomprivé Sentiment Pipeline

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API%20REST-green)
![Airflow](https://img.shields.io/badge/Airflow-Orchestration-orange)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-Search-yellow)
![Docker](https://img.shields.io/badge/Docker-Compose-lightblue)
![Status](https://img.shields.io/badge/Status-Stable-success)

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
    A[Trustpilot Scraper ] --> B[MongoDB Atlas (Raw)]
    B --> C[Nettoyage & Normalisation ]
    C --> D[MongoDB Atlas (Clean)]
    D --> E[Elasticsearch ]
    D --> F[TF-IDF + Logistic Regression ]
    F -->|Model.joblib| G[ API FastAPI ]
    F -->|Weekly retrain| H[ Airflow DAG ]
    H --> D
    H --> F
```
---

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
