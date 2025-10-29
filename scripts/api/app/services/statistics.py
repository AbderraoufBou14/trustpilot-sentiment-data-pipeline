from typing import Any, Dict, List
from datetime import datetime, time, timezone
from app.schemas import StarsBucket, TopItem, StatsOut

def build_match(stars, pays, langue, date_from) -> Dict[str, Any]:
    match: Dict[str, Any] = {}
    if stars is not None: match["nombre_etoile"] = stars
    if pays:              match["pays"] = pays
    if langue:            match["langue"] = langue
    if date_from:
        dt_from = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
        match["date_avis"] = {"$gte": dt_from}
    return match

def stats_pipeline(match: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"$match": match},
        {"$facet": {
            "total": [{"$count": "count"}],
            "avg_stars": [{"$group": {"_id": None, "avg": {"$avg": "$nombre_etoile"}}}],
            "by_star": [
                {"$group": {"_id": "$nombre_etoile", "count": {"$count": {}}}},
                {"$sort": {"_id": 1}}
            ],
            "top_pays": [
                {"$group": {"_id": "$pays", "count": {"$count": {}}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ],
            "response_rate": [
                {"$group": {"_id": "$reponse_entreprise", "count": {"$count": {}}}}
            ],
        }}
    ]

def to_stats_out(facet: Dict[str, Any]) -> StatsOut:
    total_reviews = (facet.get("total", [{}])[0].get("count", 0) if facet.get("total") else 0)
    avg_part = facet.get("avg_stars", [])
    avg_stars = round(float(avg_part[0]["avg"]), 3) if avg_part else None
    by_star = facet.get("by_star", [])
    counts_map = {d["_id"]: d["count"] for d in by_star if isinstance(d.get("_id"), int)}
    stars_distribution = [StarsBucket(stars=s, count=counts_map.get(s, 0)) for s in range(1, 6)]
    top_pays_raw = facet.get("top_pays", [])
    top_pays = [TopItem(key=d["_id"], count=d["count"]) for d in top_pays_raw]
    resp_raw = facet.get("response_rate", [])
    true_count = next((d["count"] for d in resp_raw if d.get("_id") is True), 0)
    response_rate = (true_count / total_reviews) if total_reviews else 0.0
    return StatsOut(
        total_reviews=total_reviews,
        avg_stars=avg_stars,
        stars_distribution=stars_distribution,
        top_pays=top_pays,
        response_rate=response_rate,
    )
