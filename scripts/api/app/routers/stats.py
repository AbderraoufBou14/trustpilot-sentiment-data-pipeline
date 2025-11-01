from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from core.config import get_collection
from services.statistics import build_match, stats_pipeline, to_stats_out
from schemas import StatsOut

router = APIRouter(prefix="", tags=["stats"])

def reviews_col():
    return get_collection()

@router.get(
    "/stats",
    response_model=StatsOut,
    tags=["stats"],
    summary="Statistiques agrégées sur les avis clients",
    description="Retourne des indicateurs calculés à partir des avis : moyenne des étoiles, répartition, top pays et taux de réponse."
)
async def stats(
    stars: Optional[int] = Query(None, ge=1, le=5),
    pays: Optional[str] = Query(None, min_length=2, max_length=2),
    langue: Optional[str] = Query(None, min_length=2, max_length=5),
    date_from: Optional[date] = Query(None),
    col = Depends(reviews_col),
):
    """
    Endpoint de statistiques sur les avis clients.

    - **Méthode** : GET  
    - **Entrée (query params)** : `stars`, `pays`, `langue`, `date_from`  
    - **Sortie** : objet `StatsOut` (moyenne, distribution, top pays, taux de réponse) 
    """
    match = build_match(stars, pays, langue, date_from)
    agg = list(col.aggregate(stats_pipeline(match)))
    facet = agg[0] if agg else {}
    return to_stats_out(facet)

