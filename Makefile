# ========= CONFIG =========
COMPOSE_DIR := infrastructure/compose
ENV_FILE := .env
COMPOSE := docker compose --env-file .env

# Compose files
AIRFLOW := $(COMPOSE_DIR)/airflow.docker-compose.yml
API := $(COMPOSE_DIR)/api.docker-compose.yml
ELASTIC := $(COMPOSE_DIR)/elasticsearch.docker-compose.yml
ALL := -f $(AIRFLOW) -f $(API) -f $(ELASTIC)

# ========= ACTIONS =========
up:
	@case "$(arg)" in \
		api) $(COMPOSE) -f $(API) up -d ;; \
		airflow) $(COMPOSE) -f $(AIRFLOW) up -d ;; \
		elastic) $(COMPOSE) -f $(ELASTIC) up -d ;; \
		*) $(COMPOSE) $(ALL) up -d ;; \
	esac

down:
	@case "$(arg)" in \
		api) $(COMPOSE) -f $(API) down ;; \
		airflow) $(COMPOSE) -f $(AIRFLOW) down ;; \
		elastic) $(COMPOSE) -f $(ELASTIC) down ;; \
		*) $(COMPOSE) $(ALL) down ;; \
	esac

restart:
	@make down arg=$(arg)
	@make up arg=$(arg)

logs:
	@case "$(arg)" in \
		api) $(COMPOSE) -f $(API) logs -f showroomprive_api ;; \
		airflow) $(COMPOSE) -f $(AIRFLOW) logs -f airflow-webserver ;; \
		elastic) $(COMPOSE) -f $(ELASTIC) logs -f elasticsearch ;; \
		*) docker compose logs -f ;; \
	esac

ps:
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ========= SHORTCUTS =========
up-all down-all restart-all:  ; make $(subst -, ,$@) arg=all
up-api down-api restart-api:  ; make $(subst -, ,$@) arg=api
up-airflow down-airflow restart-airflow: ; make $(subst -, ,$@) arg=airflow
up-elastic down-elastic restart-elastic: ; make $(subst -, ,$@) arg=elastic
logs-api: ; make logs arg=api

help:
	@echo "Usage : make [up|down|restart|logs] [api|airflow|elastic|all]"
