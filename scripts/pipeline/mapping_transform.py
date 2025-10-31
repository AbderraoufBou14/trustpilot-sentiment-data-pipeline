
from datetime import datetime, date
import hashlib, json, os, glob

try:
    from bson import ObjectId
except ImportError:
    ObjectId = type("ObjectId", (), {}) 

def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, ObjectId):
        return str(o)
    return str(o)

# ------------- Normalisation (utilisée pour produire le NDJSON) -------------
def normalize(doc: dict) -> dict:
    d = dict(doc)

    # a) reponse_entreprise -> bool
    if "reponse_entreprise" in d:
        if isinstance(d["reponse_entreprise"], str):
            d["reponse_entreprise"] = (d["reponse_entreprise"].strip().lower() in {"oui", "true", "1"})

    # b) _id stable (sha1) basé sur champs stables
    base_date = d.get("date_avis")
    if isinstance(base_date, datetime):
        base_date = base_date.isoformat()

    # certains jeux de données utilisent "contenu_texte" (préféré) et pas "texte"
    contenu = d.get("contenu_texte", d.get("texte", ""))

    if d.get("langue"):
        d["langue"] = str(d["langue"]).strip().lower()
        
    sig = f"{base_date}|{d.get('titre_avis','')}|{contenu}"
    d["_id"] = hashlib.sha1(sig.encode("utf-8")).hexdigest()[:10]

    return d

# ------------- Ecriture NDJSON (1 JSON par ligne) -------------
def clean_raw_to_ndjson(raw_dir="/opt/airflow/data/raw", out_dir="/opt/airflow/data/clean"):
    os.makedirs(out_dir, exist_ok=True)

    if os.path.isfile(raw_dir):
        json_files = [raw_dir]
    elif os.path.isdir(raw_dir):
        json_files = glob.glob(os.path.join(raw_dir, "reviews_*.json"))
    else:
        raise FileNotFoundError(f"Chemin introuvable: {raw_dir}")

    if not json_files:
        raise FileNotFoundError(f"Aucun fichier trouvé dans {raw_dir}")

    last_out = None
    for file in json_files:
        base = os.path.basename(file).replace(".json", "")
        out_path = os.path.join(out_dir, f"{base}.ndjson")

        with open(file, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
            docs = json.load(f_in)
            for doc in docs:
                f_out.write(json.dumps(normalize(doc), ensure_ascii=False, default=_json_default) + "\n")

        last_out = out_path
        print(f"✅ Fichier nettoyé : {out_path}")

    return last_out

