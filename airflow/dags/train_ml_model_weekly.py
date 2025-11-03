from datetime import datetime, timedelta
from airflow.decorators import dag, task

from scripts.ml.train_sentiment import check_mongo_connection, main as train_main

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

@dag(
    dag_id="ml_model_retraining_weekly",
    description="Ré-entrainement hebdomadaire du modèle TF-IDF + Logistic Regression",
    schedule_interval="0 6 * * 1",  # chaque lundi 06:00
    start_date=datetime(2025, 10, 29),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["trustpilot", "weekly"],
)
def pipeline():
    @task()
    def check_bdd_conn():
        return check_mongo_connection()

    @task()
    def train_ml_model():
        # exécute l'entraînement et écrit les artefacts
        return train_main()

    conn_check = check_bdd_conn()
    train = train_ml_model()
    conn_check >> train

dag = pipeline()
