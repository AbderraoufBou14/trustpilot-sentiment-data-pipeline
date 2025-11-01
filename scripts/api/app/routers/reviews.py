from typing import Optional, Dict, Any
from datetime import date, datetime, time, timezone
from fastapi import APIRouter, Depends, Query
from core.config import get_collection
from core.utils import serialize_one
from schemas import ReviewOut, ReviewsPage

router = APIRouter(prefix="", tags=["reviews"])

def reviews_col():
    return get_collection()

@router.get(
    "/avis",
    response_model=ReviewsPage,
    tags=["reviews"],
    summary="Liste des avis clients filtrables",
    description="Retourne les avis clients depuis MongoDB, avec possibilité de filtrer par étoiles, pays, langue ou date. Nombre d'avis limité à 100."
)
async def list_reviews(
    stars: Optional[int] = Query(None, ge=1, le=5),
    pays: Optional[str] = Query(None, min_length=2, max_length=8),
    langue: Optional[str] = Query(None, min_length=2, max_length=5),
    date_from: Optional[date] = Query(None),
    sort: str = Query("date_desc", pattern="^(date_desc|date_asc)$"),
    limit: int = Query(100, ge=1, le=100),
    col = Depends(reviews_col),
):
    """
    Endpoint de récupération des avis clients.

    - **Méthode** : GET  
    - **Entrée (query params)** : `stars`, `pays`, `langue`, `date_from`, `sort`, `limit`  
    - **Sortie** : objet `ReviewsPage`
    - **Tag** : reviews
    """
    query: Dict[str, Any] = {}
    if stars is not None:
        query["nombre_etoile"] = stars
    if pays:
        query["pays"] = pays
    if langue:
        query["langue"] = langue
    if date_from:
        dt_from = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
        query["date_avis"] = {"$gte": dt_from}

    sort_dir = -1 if sort == "date_desc" else 1
    cursor = col.find(query).sort("date_avis", sort_dir).limit(limit)
    docs = [serialize_one(d) for d in cursor]
    return ReviewsPage(count=len(docs), items=[ReviewOut(**d) for d in docs])
