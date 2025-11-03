# ========= CONFIG =========
ENV_FILE := .env
COMPOSE  := docker compose --env-file $(ENV_FILE)

COMPOSE_DIR := infrastructure/compose
AIRFLOW := $(COMPOSE_DIR)/airflow.docker-compose.yml
API     := $(COMPOSE_DIR)/api.docker-compose.yml
ELASTIC := $(COMPOSE_DIR)/elasticsearch.docker-compose.yml

# Par défaut : tous les services. Surcharger avec: make up SERVICE=api
SERVICE ?= all

# ========= MACRO D’EXÉCUTION =========
define RUN_COMPOSE
	@case "$(SERVICE)" in \
		api)     $(COMPOSE) -f $(API) $(1) ;; \
		airflow) $(COMPOSE) -f $(AIRFLOW) $(1) ;; \
		elastic) $(COMPOSE) -f $(ELASTIC) $(1) ;; \
		all)     $(COMPOSE) -f $(AIRFLOW) -f $(API) -f $(ELASTIC) $(1) ;; \
		*) echo "Unknown SERVICE='$(SERVICE)'. Use api|airflow|elastic|all"; exit 1 ;; \
	esac
endef

# ========= COMMANDES =========
.PHONY: up down build restart logs ps prune help

up:
	$(call RUN_COMPOSE,up -d)

down:
	$(call RUN_COMPOSE,down)

build:
	$(call RUN_COMPOSE,build)

restart:
	@$(MAKE) down SERVICE=$(SERVICE)
	@$(MAKE) up SERVICE=$(SERVICE)

logs:
	$(call RUN_COMPOSE,logs -f)

ps:
	$(call RUN_COMPOSE,ps)
