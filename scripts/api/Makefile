# Nom du projet
PROJECT_NAME=showroomprive_api
PORT=8000

# Fichier compose
COMPOSE=docker compose

.PHONY: build up down logs restart ps portkill

# Construire l'image
build:
	$(COMPOSE) build

# Lancer les services en arrière-plan
up:
	$(COMPOSE) up -d

# Arrêter et supprimer les conteneurs
down:
	$(COMPOSE) down

# Redémarrer
restart: down up

# Voir les logs de l'API
logs:
	$(COMPOSE) logs -f api

# Liste des conteneurs qui tournent
ps:
	$(COMPOSE) ps

# Vérifie si le port est occupé (par défaut 8000)
check-port:
	@echo "==> Ports écoutés sur $(PORT)"
	@lsof -i :$(PORT) || echo "Port $(PORT) libre ✅"

# Kill le process qui occupe le port 
portkill:
	@PID=$$(lsof -t -i :$(PORT)); \
	if [ -n "$$PID" ]; then \
	  echo "🔴 Port $(PORT) occupé par PID $$PID. On kill..."; \
	  kill -9 $$PID; \
	else \
	  echo "✅ Port $(PORT) libre"; \
	fi
# lancer l'api
api-run:
	uvicorn app.main:app --reload