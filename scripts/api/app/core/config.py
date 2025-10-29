import os 
from dotenv import load_dotenv
from pymongo import MongoClient

# chargement des variables d'environnement 
load_dotenv()

# Base de données Mongodb
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COL = os.getenv("MONGO_COL")

# Chemin ver le modele ML
MODEL_PATH = os.getenv("MODEL_V1_PATH")


_client = None

def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[MONGO_DB][MONGO_COL]

def get_model_path():
    return MODEL_PATH


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_model_v1_path() -> str:
    return os.getenv("MODEL_V1_PATH")
