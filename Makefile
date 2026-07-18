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

dev: ## Inicia o webhook FastAPI (Tag 1)
	uv run uvicorn crmToVoice.webhook:app --reload

##@ Qualidade

test: test-unit test-integration ## Corre todos os testes

test-unit: ## Corre os testes unitários
	uv run pytest tests/unit

test-integration: ## Corre os testes de integração (precisa de credenciais reais)
	uv run pytest tests/integration

lint: ## Verifica o código com ruff
	uv run ruff check .

format: ## Formata o código com ruff
	uv run ruff format .

typecheck: ## Verifica tipos com pyright
	uv run pyright

check: lint typecheck test ## Corre lint + typecheck + testes

##@ Avaliação (LangSmith, precisa de credenciais reais)

eval-all-tools: ## Corre os evaluators LangSmith do agente all-tools interpret_speech (US-T1-02)
	uv run python scripts/eval_all_tools_agent.py

##@ Airtable (manual)

airtable-add: ## Cria um Lead + Imóvel + Visita ligados entre si no Airtable, com todos os campos preenchidos
	uv run python scripts/airtable_manage.py add

airtable-delete: ## Apaga um registo (TABLE=leads|imoveis|visitas ID=recXXXXXXXXXXXXXX) ou TODOS os registos das 3 tabelas se não indicares nenhum (pede confirmação)
	@if [ -n "$(TABLE)$(ID)" ] && { [ -z "$(TABLE)" ] || [ -z "$(ID)" ]; }; then \
		echo "Uso: make airtable-delete TABLE=leads|imoveis|visitas ID=recXXXXXXXXXXXXXX (ou nenhum, para apagar tudo)"; \
		exit 1; \
	fi
	uv run python scripts/airtable_manage.py delete $(TABLE) $(ID)

##@ Limpeza

clean: ## Remove o .venv
	rm -rf .venv

.PHONY: help setup dev test test-unit test-integration lint format typecheck check eval-all-tools airtable-add airtable-delete clean
