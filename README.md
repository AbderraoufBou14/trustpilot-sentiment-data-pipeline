# Trustpilot Sentiment Data Pipeline

Pipeline de Data Engineering pour collecter, transformer, indexer et exposer des **avis clients** (source : Trustpilot) avec **analyse de sentiments**.

## 🧱 Architecture (vue d’ensemble)
- **Scraping** (Python) → données brutes JSON/NDJSON  
- **Nettoyage & normalisation** → champs ISO, booléens, numériques, `_id` unique  
- **Stockage** → MongoDB (raw + clean)  
- **Indexation** → Elasticsearch (mapping linguistique FR/ES/IT + champ `fulltext`)  
- **Orchestration** → Airflow (DAG `trustpilot_daily`)  
- **API** → FastAPI (`/avis`, `/stats`, `/predict`, `/health`)  
- (Optionnel) **Visualisation** → Kibana / Streamlit

## 🧰 Stack principale
- Python (pandas, scikit-learn, joblib)
- MongoDB
- Elasticsearch + Kibana
- FastAPI + Uvicorn
- Apache Airflow
- Docker / Docker Compose

## ▶️ Démarrage rapide (local)
```bash
# Variables d'env (exemple)
cp .env.example .env

# Démarrer services (exemples selon ton repo)
docker compose -f infrastructure/compose/elasticsearch.kibana.yml up -d
docker compose -f infrastructure/compose/airflow.docker-compose.yml up -d
docker compose -f infrastructure/compose/api.docker-compose.yml up -d

