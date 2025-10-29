import os
import re

import pandas as pd
from pymongo import MongoClient
from joblib import dump, load

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

import matplotlib.pyplot as plt

RANDOM_STATE = 42

# Connexion à la BDD
MONGO_URI = os.getenv("MONGO_URI", "mongodb://datascientest:dst123@54.217.155.194:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "showroomprive_db")
MONGO_COL = os.getenv("MONGO_COL", "silver_col")

#serialisation des articafts
ARTIFACTS_DIR = "artifacts"
PIPELINE_PATH = os.path.join(ARTIFACTS_DIR, "sentiment_pipeline.joblib")

print(f"MONGO_URI={MONGO_URI}\nMONGO_DB={MONGO_DB}\nMONGO_COL={MONGO_COL}")


# fonction pour créer les étiquetes
def map_sentiment(stars):
    try:
        s = int(stars)
    except Exception:
        return None
    if s == 1: return "très_déçu"        # ★☆☆☆☆
    if s == 2: return "déçu"             # ★★☆☆☆
    if s == 3: return "correct"          # ★★★☆☆
    if s == 4: return "satisfait"        # ★★★★☆
    if s == 5: return "très_satisfait"   # ★★★★★
    return None


def basic_text_clean(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"http\S+|www\.\S+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# 2. Consommation de la donnée (MongoDB) → DataFrame

def load_df_from_mongo(uri: str = MONGO_URI, db: str = MONGO_DB, colname: str = MONGO_COL) -> pd.DataFrame:
    """
    Charge les documents nécessaires depuis MongoDB et prépare un DataFrame.
    """
    client = MongoClient(uri)
    col = client[db][colname]
    cursor = col.find(
        {},
        {
            "titre_avis": 1,
            "contenu_texte": 1,
            "nombre_etoile": 1,
            "date_avis": 1,
            "langue": 1,
            "pays": 1,
        },
    )
    docs = list(cursor)
    if not docs:
        raise SystemExit("[ERREUR] Aucun document trouvé dans MongoDB.")

    df = pd.DataFrame(docs)

    # Vérification des colonnes indispensables
    for colname in ("titre_avis", "contenu_texte", "nombre_etoile"):
        if colname not in df.columns:
            raise SystemExit(f"[ERREUR] Colonne manquante dans MongoDB: '{colname}'")

    # Texte total (avec nettoyage)
    df["titre_avis"] = df["titre_avis"].fillna("").astype(str)
    df["contenu_texte"] = df["contenu_texte"].fillna("").astype(str)
    df["texte_total"] = (df["titre_avis"] + " " + df["contenu_texte"]).map(basic_text_clean)

    # Label supervisé à partir du nombre d'étoiles
    df["sentiment"] = df["nombre_etoile"].map(map_sentiment)

    # Filtrage minimal : texte non vide + label présent
    df = df[(df["texte_total"].str.len() >= 3) & df["sentiment"].notna()]

    if df.empty:
        raise SystemExit("[ERREUR] Après préparation, plus aucune donnée exploitable.")

    return df.reset_index(drop=True)

df = load_df_from_mongo()
print(f"[INFO] Nombre d'avis chargés: {len(df)}\n")
print("[INFO] Distribution des classes :")
print(df["sentiment"].value_counts())
df.head(5)

# 3. Split Train / Test

X = df["texte_total"].tolist()
y = df["sentiment"].tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y
)

# 4. Pipeline TF-IDF + Logistic Regression

pipeline = Pipeline(
    steps=[
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=50000,
            min_df=2
        )),
        ("clf", LogisticRegression(
            max_iter=200,
            n_jobs=None if hasattr(LogisticRegression, "n_jobs") else None,
            random_state=RANDOM_STATE,
            class_weight="balanced"
        ))
    ]
)

print("[TRAIN] Entraînement en cours…")
pipeline.fit(X_train, y_train)
print("[TRAIN] OK")

# 5. Évaluation simple

y_pred = pipeline.predict(X_test)
print("\n[REPORT] Classification report :\n")
print(classification_report(y_test, y_pred))

print("[CONFUSION] Matrice de confusion :")
cm = confusion_matrix(y_test, y_pred, labels=[
    "très_déçu","déçu","correct","satisfait","très_satisfait"
])
print(cm)

# Affichage d'une matrice de confusion normalisée (matplotlib)
try:
    import numpy as np
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
    fig = plt.figure(figsize=(6, 5))
    plt.imshow(cm_norm, interpolation="nearest")
    plt.title("Matrice de confusion (normalisée)")
    plt.colorbar()
    tick_marks = range(len(["très_déçu","déçu","correct","satisfait","très_satisfait"]))
    plt.xticks(tick_marks, ["très_déçu","déçu","correct","satisfait","très_satisfait"], rotation=45)
    plt.yticks(tick_marks, ["très_déçu","déçu","correct","satisfait","très_satisfait"])
    plt.tight_layout()
    plt.xlabel("Prédit")
    plt.ylabel("Réel")
    # plt.show()  # désactivé en script batch
except Exception as e:
    print(f"[WARN] Impossible d'afficher la matrice de confusion: {e}")

# 6. Sauvegarde du pipeline

os.makedirs(ARTIFACTS_DIR, exist_ok=True)
dump(pipeline, PIPELINE_PATH)
print(f"[SAVE] Pipeline sauvegardé dans : {PIPELINE_PATH}")

# *Petit check du model entrainé**

pipe_loaded = load(PIPELINE_PATH)

texts_demo = [
    "Muy buena experiencia, repetiré.",
    "experience horrible avec ce site, tres déçu",
    "livraison plutot pas mal."
]
preds = pipe_loaded.predict(texts_demo)
for text, pred in zip(texts_demo, preds):
    print(f"'{text}' : \033[1m{pred}\033[0m")
