# scripts/ml/train_sentiment.py
import os
import re
import json
import datetime
from typing import Optional

import pandas as pd
from pymongo import MongoClient
from joblib import dump
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from pathlib import Path
from dotenv import load_dotenv

# ====== Chargement .env (racine du repo) ======
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def require_env(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Variable d'environnement manquante: {key}")
    return v

# ====== Variables d'environnement  ======
MONGO_URI = require_env("MONGO_URI")
MONGO_DB  = require_env("MONGO_DB")
MONGO_COL = require_env("MONGO_COL")

# Dossier des artefacts 
ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "ml_models")

# Alias stable utilisé par l'API (doit matcher MODEL_PATH côté API)
MODEL_ALIAS = os.path.join(ARTIFACTS_DIR, "model.joblib")

# Fichier de métadonnées
META_PATH = os.path.join(ARTIFACTS_DIR, "metadata.json")

# Seed
RANDOM_STATE = 42

# ====== Utilitaires ======
def check_mongo_connection() -> int:
    """Vérifie la connectivité à MongoDB et retourne un comptage rapide."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    col = client[MONGO_DB][MONGO_COL]
    count = col.estimated_document_count()
    print(f"[CHECK] {MONGO_DB}.{MONGO_COL} → {count} documents")
    if count == 0:
        raise ValueError("La collection Mongo est vide, impossible d'entraîner.")
    return count

def map_sentiment(stars) -> Optional[str]:
    try:
        s = int(stars)
    except Exception:
        return None
    return {1: "très_déçu", 2: "déçu", 3: "correct", 4: "satisfait", 5: "très_satisfait"}.get(s)

def basic_text_clean(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"http\S+|www\.\S+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_df_from_mongo() -> pd.DataFrame:
    client = MongoClient(MONGO_URI)
    col = client[MONGO_DB][MONGO_COL]
    cursor = col.find({}, {
        "titre_avis": 1, "contenu_texte": 1, "nombre_etoile": 1,
        "date_avis": 1, "langue": 1, "pays": 1
    })
    docs = list(cursor)
    if not docs:
        raise RuntimeError("Aucun document trouvé dans MongoDB.")

    df = pd.DataFrame(docs)
    for needed in ("titre_avis", "contenu_texte", "nombre_etoile"):
        if needed not in df.columns:
            raise RuntimeError(f"Colonne manquante: '{needed}'")

    df["titre_avis"] = df["titre_avis"].fillna("").astype(str)
    df["contenu_texte"] = df["contenu_texte"].fillna("").astype(str)
    df["texte_total"] = (df["titre_avis"] + " " + df["contenu_texte"]).map(basic_text_clean)
    df["sentiment"] = df["nombre_etoile"].map(map_sentiment)
    df = df[(df["texte_total"].str.len() >= 3) & df["sentiment"].notna()]
    if df.empty:
        raise RuntimeError("Après préparation, plus aucune donnée exploitable.")
    return df.reset_index(drop=True)

# ====== Main ======
def main() -> int:
    # 1) Pré-conditions
    check_mongo_connection()

    # 2) Chargement des données
    print(f"[INFO] Connexion Mongo → {MONGO_URI} | {MONGO_DB}.{MONGO_COL}")
    df = load_df_from_mongo()
    print(f"[INFO] Avis chargés: {len(df)}")

    X = df["texte_total"].tolist()
    y = df["sentiment"].tolist()
    if len(set(y)) < 2:
        print("[ERREUR] Une seule classe présente → impossible d’entraîner.")
        return 2

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    # 3) Entraînement
    pipeline = Pipeline(steps=[
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2)),
        ("clf", LogisticRegression(max_iter=200, class_weight="balanced", random_state=RANDOM_STATE)),
    ])
    print("[TRAIN] Entraînement...")
    pipeline.fit(X_train, y_train)
    print("[TRAIN] OK")

    # 4) Évaluation
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1m = f1_score(y_test, y_pred, average="macro")
    print(f"[METRICS] accuracy={acc:.4f} | f1_macro={f1m:.4f}")

    # 5) Sauvegarde des artefacts
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    versioned_model_path = os.path.join(ARTIFACTS_DIR, f"model_{ts}.joblib")

    dump(pipeline, versioned_model_path)  # version horodatée (par jour)
    dump(pipeline, MODEL_ALIAS)           # alias stable pour l’API

    meta = {
        "version": ts,
        "created_at_utc": ts,
        "algo": "LogisticRegression",
        "vectorizer": "TfidfVectorizer(1,2,max_features=50000,min_df=2)",
        "metrics": {"accuracy": acc, "f1_macro": f1m},
        "data": {"count": len(df), "db": MONGO_DB, "collection": MONGO_COL},
        "random_state": RANDOM_STATE,
        "artifact_paths": {"model_versioned": versioned_model_path, "model_alias": MODEL_ALIAS},
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[SAVE] Modèle: {versioned_model_path}")
    print(f"[SAVE] Alias:  {MODEL_ALIAS}")
    print(f"[SAVE] Métadonnées: {META_PATH}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[ERREUR] {e}")
        raise SystemExit(1)

