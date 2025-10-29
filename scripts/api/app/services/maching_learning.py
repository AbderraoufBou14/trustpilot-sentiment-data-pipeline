import joblib
import numpy as np
from threading import Lock
from typing import Dict, Tuple
from app.core.config import get_model_v1_path


# modele ML (TF-IDF + LogReg) 
_model_v1 = None
_mlock_v1 = Lock()

def get_model_v1():
    global _model_v1
    if _model_v1 is None:
        with _mlock_v1:
            if _model_v1 is None:
                path = get_model_v1_path()
                mdl = joblib.load(path)
                _model_v1 = mdl
    return _model_v1

def predict_v1(text: str) -> Tuple[str, Dict[str, float]]:
    mdl = get_model_v1()
    probs = mdl.predict_proba([text])[0]
    classes = list(mdl.classes_)
    proba_map = {str(c): float(p) for c, p in zip(classes, probs)}
    label = str(classes[int(np.argmax(probs))])
    return label, proba_map

