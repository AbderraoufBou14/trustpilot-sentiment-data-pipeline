from typing import Any, Dict
from bson import ObjectId

def serialize_one(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if isinstance(d.get("_id"), ObjectId):
        d["_id"] = str(d["_id"])
    return d

