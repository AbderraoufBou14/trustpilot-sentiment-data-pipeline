from pymongo import MongoClient, InsertOne
from pymongo.errors import BulkWriteError
from datetime import datetime
import json, os  

# 1) Connexion Mongo via .env (URI complet Atlas)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME   = os.getenv("MONGO_DB",  "showroomprive_db")
COL_NAME  = os.getenv("MONGO_COL", "avis")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI absent de l'environnement. Assure-toi que ton `.env` est monté dans le container Airflow."
    )

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col = db[COL_NAME]



# ------------- Conversion légère pour dates AVANT insertion -------------
def _to_dt(x):
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x.replace("Z", "+00:00"))
        except Exception:
            return x
    return x



# ------------- Import NDJSON -> Mongo (ligne par ligne) -------------
def ingest_to_mongodb(ndjson_path: str, batch_size: int = 1000) -> int:
    inserted = 0
    batch = []

    with open(ndjson_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)  
            except json.JSONDecodeError as e:
                raise ValueError(f"NDJSON invalide à la ligne {i}: {e}") from e

            for key in ("date_avis", "date_reponse_entreprise"):
                if key in doc:
                    doc[key] = _to_dt(doc[key])

            batch.append(InsertOne(doc))
            if len(batch) >= batch_size:
                try:
                    res = col.bulk_write(batch, ordered=False)
                    inserted += res.inserted_count
                except BulkWriteError:
                    pass
                finally:
                    batch.clear()

    if batch:
        try:
            res = col.bulk_write(batch, ordered=False)
            inserted += res.inserted_count
        except BulkWriteError:
            pass

    return inserted
