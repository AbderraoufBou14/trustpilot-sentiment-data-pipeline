from datetime import datetime, timedelta, timezone
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.python import get_current_context

import os
from scripts.scraper.trustpilot_scraper import scrape_trustpilot_reviews

from scripts.pipeline.mapping_transform import clean_raw_to_ndjson  

from scripts.pipeline.to_mongo import ingest_to_mongodb
from scripts.pipeline.to_es import  ingest_to_es

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

@dag(
    dag_id="trustpilot_daily",
    description="Trustpilot Showroomprivé - TaskFlow version",
    schedule_interval="0 6 * * *",
    start_date=datetime(2025, 10, 29),  
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["trustpilot","daily"],
)
def pipeline():

    @task()
    def scrape() -> str:
        """Scrape → retourne le chemin du JSON brut (XCom auto)."""
        ctx = get_current_context()

        # Date réelle d'exécution (UTC) au format AAAA-MM-JJ
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        data_dir = Variable.get("DATA_DIR", "/opt/airflow/data")
        base_url = Variable.get(
            "SCRAPE_BASE_URL",
            "https://www.trustpilot.com/review/www.showroomprive.com?languages=all"
        )
        max_pages = int(Variable.get("SCRAPE_MAX_PAGES", 10))

        out_dir = os.path.join(data_dir, "raw")
        os.makedirs(out_dir, exist_ok=True)

        # 👉 Nom du fichier basé sur la date réelle d’exécution
        out_path = os.path.join(out_dir, f"reviews_{today_str}.json")

        # Évite de rescraper si le fichier existe déjà et n’est pas vide
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path

        scrape_trustpilot_reviews(
            base_url=base_url,
            output_file=out_path,
            max_pages=max_pages
        )
        return out_path


    @task()
    def clean(raw_path: str) -> str:
        """
        Normalise le JSON brut en NDJSON et renvoie le chemin du fichier .ndjson.
        Le nom final inclut la date, ex:
        /opt/airflow/data/clean/reviews_2025-10-12.ndjson
        """
        data_dir = Variable.get("DATA_DIR", "/opt/airflow/data")
        out_dir = os.path.join(data_dir, "clean")
        os.makedirs(out_dir, exist_ok=True)
        ndjson_path = clean_raw_to_ndjson(raw_path, out_dir=out_dir)
        return ndjson_path


    @task()
    def to_mongo(clean_path: str) -> int:
        """Charge le NDJSON nettoyé dans MongoDB"""
        return ingest_to_mongodb(clean_path)

    @task()
    def to_es(clean_path: str) -> int:
        """Indexation ES via l'api (bulk) et retourne nombre de docs indexés."""
        return ingest_to_es(clean_path)

    raw = scrape()
    clean_path = clean(raw)
    to_mongo(clean_path)
    to_es(clean_path)

dag = pipeline()
