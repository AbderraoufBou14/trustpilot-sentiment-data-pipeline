from fastapi import APIRouter, Body, HTTPException
from app.schemas import PredictIn, PredictOut
from app.services.maching_learning import predict_v1

router = APIRouter(prefix="", tags=["predict"])

@router.post(
    "/predict/v1",
    response_model=PredictOut,
    tags=["predict"],
    summary="Prédit le sentiment d’un texte (modèle V1)",
    description="Utilise le modèle TF-IDF + Logistic Regression pour déterminer le sentiment d’un texte donné."
)
async def predict_route_v1(payload: PredictIn = Body(...)):
    """
    Endpoint de prédiction de sentiment (version V1).

    - **Méthode** : POST  
    - **Entrée** : texte brut à analyser (`PredictIn`)  
    - **Sortie** : label prédit et probabilités. 
    """
    try:
        label, proba = predict_v1(payload.text)
        return PredictOut(version="v1", label=label, proba=proba)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"V1 error: {e}")

