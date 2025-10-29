COMPOSE_CMD ?= docker compose
COMPOSE_DIR ?= infrastructure/compose
STACK=all
ENV ?= infrastructure/compose/.env
ENV_FLAG := $(if $(wildcard $(ENV)),--env-file $(ENV),)
PROJECT ?=
PROJECT_FLAG := $(if $(PROJECT),-p $(PROJECT),)

# Résolution des fichiers compose
ifeq ($(STACK),all)
  FILES := $(wildcard $(COMPOSE_DIR)/*.yml) $(wildcard $(COMPOSE_DIR)/*.yaml)
else
  STACK_LIST := $(subst ,, ,$(STACK))
  FILES := $(foreach s,$(STACK_LIST), \
            $(firstword \
              $(wildcard $(COMPOSE_DIR)/$(s).docker-compose.yml) \
              $(wildcard $(COMPOSE_DIR)/$(s).docker-compose.yaml)))
  $(foreach s,$(STACK_LIST),$(if $(firstword \
      $(wildcard $(COMPOSE_DIR)/$(s).docker-compose.yml) \
      $(wildcard $(COMPOSE_DIR)/$(s).docker-compose.yaml)),,\
      $(error Stack introuvable: $(s))))
endif
COMPOSE_FILES := $(foreach f,$(FILES),-f $(f))
DC := $(COMPOSE_CMD) $(PROJECT_FLAG) $(COMPOSE_FILES) $(ENV_FLAG)

.DEFAULT_GOAL := help
.PHONY: up down restart ps logs tail build pull recreate reset list help

up:     ; $(DC) up -d --remove-orphans
down:   ; $(DC) down
restart:; $(DC) down && $(DC) up -d --remove-orphans
ps:     ; $(DC) ps
logs:   ; $(DC) logs --tail=200
tail:   ; $(DC) logs -f --tail=200
build:  ; $(DC) build $(if $(NO_CACHE),--no-cache,)
pull:   ; $(DC) pull
recreate:;$(DC) up -d --force-recreate --remove-orphans
reset:  ; $(DC) down -v
list:
	@echo "Fichiers détectés:"; for f in $(wildcard $(COMPOSE_DIR)/*.yml) $(wildcard $(COMPOSE_DIR)/*.yaml); do echo " - $$f"; done
help:
	@echo "Usage: STACK=all|airflow|airflow,api make [up|down|ps|logs|tail|build|pull|recreate|reset|list]"
	@echo "Exemples: make up ; STACK=airflow make logs ; PROJECT=dst ENV=.env.dev STACK=api make up"
