import os
import json
import time
from collections import Counter
from elasticsearch import Elasticsearch, helpers

ES_URL   = os.getenv("ES_URL")               
ES_INDEX = os.getenv("ES_INDEX", "avis")    
# Mapping avec analyseurs FR/ES/IT 
index_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "normalizer": {
                "lc_ascii": {
                    "type": "custom",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "titre_avis": {
                "type": "text",
                "fields": {
                    "fr": {"type": "text", "analyzer": "french"},
                    "es": {"type": "text", "analyzer": "spanish"},
                    "it": {"type": "text", "analyzer": "italian"}
                },
                "copy_to": ["fulltext"]  
            },
            "contenu_texte": {
                "type": "text",
                "fields": {
                    "fr": {"type": "text", "analyzer": "french"},
                    "es": {"type": "text", "analyzer": "spanish"},
                    "it": {"type": "text", "analyzer": "italian"}
                },
                "copy_to": ["fulltext"]  
            },
            "texte_entreprise": {
                "type": "text",
                "fields": {
                    "fr": {"type": "text", "analyzer": "french"},
                    "es": {"type": "text", "analyzer": "spanish"},
                    "it": {"type": "text", "analyzer": "italian"}
                }
            },
            # champ agrégé pour recherches globales (titre + contenu_text)
            "fulltext": {
                "type": "text",
                "fields": {
                    "fr": {"type": "text", "analyzer": "french"},
                    "es": {"type": "text", "analyzer": "spanish"},
                    "it": {"type": "text", "analyzer": "italian"}
                }
            },

            "nombre_etoile": {"type": "integer"},
            "date_avis": {"type": "date"},
            "date_reponse_entreprise": {"type": "date", "null_value": None},
            "pays": {"type": "keyword", "normalizer": "lc_ascii"},
            "langue": {"type": "keyword", "normalizer": "lc_ascii"},
            "reponse_entreprise": {"type": "boolean"}
        }
    }
}

def _gen_actions(ndjson_path: str, index: str):
    missing_id = 0
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                src = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[NDJSON] Ligne {line_no}: JSON invalide ({e}); doc ignoré.")
                continue

            doc_id = src.get("_id")
            if not doc_id:
                missing_id += 1
                if missing_id <= 5:
                    print(f"[NDJSON] Ligne {line_no}: _id manquant; doc ignoré.")
                elif missing_id == 6:
                    print("[NDJSON] Plusieurs _id manquants; suppression des logs similaires.")
                continue

            src = dict(src)      
            src.pop("_id", None)

            yield {
                "_op_type": "index",   
                "_index": index,
                "_id": str(doc_id),
                "_source": src,
            }

def ingest_to_es(ndjson_path: str) -> int:
    if not ES_URL:
        raise RuntimeError("ES_URL absent de l'environnement.")

    es = Elasticsearch(ES_URL)

    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX, body=index_body)

    start = time.time()

    success, errors = helpers.bulk(
        es,
        _gen_actions(ndjson_path, ES_INDEX),
        chunk_size=500,
        request_timeout=120,
        refresh="wait_for",
        raise_on_error=False,
    )

    elapsed = time.time() - start
    print(f"✅ {success} documents indexés dans {ES_INDEX} en {elapsed:.2f}s")

    if errors:
        print(f"⚠️ {len(errors)} documents en erreur (voir résumé ci-dessous).")
        reasons = []
        for e in errors[:100]:
            item = e.get("index") or e.get("create") or e.get("update") or {}
            err  = item.get("error", {})
            et   = err.get("type", "unknown")
            er   = err.get("reason", "")
            cb   = (err.get("caused_by") or {}).get("reason", "")
            reasons.append(f"{et} | {er} | {cb}")
        cnt = Counter(reasons)
        print("— Top erreurs:")
        for reason, n in cnt.most_common(10):
            print(f"   • {n} × {reason}")
    return success
