# app/schemas.py
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer

# le model représentant un avis.
class ReviewOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    titre_avis: Optional[str] = None
    contenu_texte: Optional[str] = None
    nombre_etoile: Optional[int] = None
    date_avis: Optional[datetime] = None
    pays: Optional[str] = None
    langue: Optional[str] = None
    reponse_entreprise: Optional[bool] = None
    texte_entreprise: Optional[str] = None

    @field_serializer("date_avis")
    def _ser_datetime(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None

# Le model représentant la réponse paginée d'un ou plusieurs avis, selon la requete envoyée.
class ReviewsPage(BaseModel):
    count: int
    items: List[ReviewOut]

class StarsBucket(BaseModel):
    stars: int
    count: int

class TopItem(BaseModel):
    key: str
    count: int

class StatsOut(BaseModel):
    total_reviews: int
    avg_stars: Optional[float] = None
    stars_distribution: List[StarsBucket]
    top_pays: List[TopItem]
    response_rate: float  # entre 0 et 1


#################################

class PredictIn(BaseModel):
    text: str = Field(..., min_length=1, description="Texte d'avis")

class PredictOut(BaseModel):
    version: str
    label: str
    proba: Dict[str, float]