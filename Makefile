CYAN := \033[36m
RESET := \033[0m

.DEFAULT_GOAL := help

##@ Geral

help: ## Mostra esta mensagem de ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make $(CYAN)<comando>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n%s\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

setup: ## Cria .venv e instala dependências
	uv sync

##@ Desenvolvimento

dev: ## Inicia LangGraph Studio (desenvolvimento de agentes)
	uv run langgraph dev

##@ Qualidade

test: ## Corre os testes
	uv run pytest

lint: ## Verifica o código com ruff
	uv run ruff check .

format: ## Formata o código com ruff
	uv run ruff format .

typecheck: ## Verifica tipos com pyright
	uv run pyright

check: lint typecheck test ## Corre lint + typecheck + testes

##@ Limpeza

clean: ## Remove o .venv
	rm -rf .venv

.PHONY: help setup dev test lint format typecheck check clean
