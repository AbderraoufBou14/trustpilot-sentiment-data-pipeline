from fastapi import FastAPI, Depends
from core.config import get_collection
from routers import reviews, stats, predict

app = FastAPI(title="Satisfaction Client API")

@app.get(
    "/health",
    tags=["health"],
    summary="Vérifie l’état de l’API et de la base de données",
    description="Endpoint de contrôle de santé (healthcheck) pour vérifier que l’API FastAPI et la base MongoDB sont accessibles."
)
async def health(col = Depends(get_collection)):
    """
    Endpoint de vérification de l’état de l’API et de MongoDB.

    - **Méthode** : GET  
    - **Sortie** : JSON indiquant le statut de l’API et de la base de données  
    - **Tag** : health  
    - **Exemples de réponses** :  
      - ✅ `{ "api": "ok", "db": "ok" }`  
      - ⚠️ `{ "api": "ok", "db": "error: OperationFailure: Authentication failed." }`
    """
    try:
        col.database.command("ping")
        return {"api": "ok", "db": "ok"}
    except Exception as e:
        return {"api": "ok", "db": f"error: {e.__class__.__name__}: {e}"}

app.include_router(reviews.router)
app.include_router(stats.router)
app.include_router(predict.router)
