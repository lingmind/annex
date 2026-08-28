.PHONY: build test fmt lint generate-sdks validate-plugins configure-codex-lingmind configure-workbuddy-lingmind configure-doubao-lingmind

PYTHON ?= python3
CODEX_APP_CLI := $(firstword $(wildcard /Applications/ChatGPT.app/Contents/Resources/codex /Applications/Codex.app/Contents/Resources/codex))
CODEX ?= $(or $(shell command -v codex 2>/dev/null),$(CODEX_APP_CLI))
CODEX_HOME ?= $(HOME)/.codex
PLUGIN_VALIDATOR ?= $(CODEX_HOME)/skills/.system/plugin-creator/scripts/validate_plugin.py
SKILL_VALIDATOR ?= $(CODEX_HOME)/skills/.system/skill-creator/scripts/quick_validate.py
CODEX_MARKETPLACE_OUTPUT ?= $(CURDIR)/.local/codex-marketplace
CODEX_MARKETPLACE_NAME ?= lingmind-configured
LINGMIND_APEX_URL ?= https://apex.lingmind.cn
LINGMIND_OAUTH_CLIENT_ID ?= lingmind-codex
LINGMIND_CALLBACK_PORT ?= 1455
LINGMIND_ENVIRONMENTS ?= beta
LINGMIND_DEFAULT_ENVIRONMENT ?=
CODEX_ENVIRONMENT_ARGS = $(foreach environment,$(LINGMIND_ENVIRONMENTS),--environment-code "$(environment)")
CODEX_DEFAULT_ENVIRONMENT_ARG = $(if $(strip $(LINGMIND_DEFAULT_ENVIRONMENT)),--default-environment "$(LINGMIND_DEFAULT_ENVIRONMENT)")
WORKBUDDY_HOME ?= $(HOME)/.workbuddy
DOUBAO_WORKSPACE ?= $(HOME)/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace
ENV ?=
WORKBUDDY_ENVIRONMENT_ARG = $(if $(strip $(ENV)),--environment-code "$(ENV)")
DOUBAO_ENVIRONMENT_ARG = $(if $(strip $(ENV)),--environment-code "$(ENV)")

build:
	go build ./...
	go build -o bin/lm ./cmd/lm

test:
	go test ./...

fmt:
	gofmt -w cmd internal pkg examples

lint:
	go vet ./...

generate-sdks:
	./scripts/generate-sdks.sh

validate-plugins:
	$(PYTHON) scripts/test-render-codex-plugins.py
	$(PYTHON) scripts/test-configure-workbuddy-lingmind.py
	$(PYTHON) scripts/test-configure-doubao-lingmind.py
	$(PYTHON) $(PLUGIN_VALIDATOR) plugins/lingmind
	$(PYTHON) $(PLUGIN_VALIDATOR) plugins/lingmind-operator
	@for skill in plugins/lingmind/skills/* plugins/lingmind-operator/skills/*; do \
		$(PYTHON) $(SKILL_VALIDATOR) "$$skill" || exit 1; \
	done
	@for skill in platforms/doubao/skills/*; do \
		$(PYTHON) $(SKILL_VALIDATOR) "$$skill" || exit 1; \
	done
	$(PYTHON) scripts/validate-agent-plugins.py
	@jq empty .agents/plugins/marketplace.json

configure-codex-lingmind:
	@if [ -z "$(CODEX)" ] || ! command -v "$(CODEX)" >/dev/null 2>&1; then \
		echo 'Codex CLI was not found. Set CODEX=/absolute/path/to/codex and retry.'; \
		exit 127; \
	fi
	@if [ -z "$(strip $(LINGMIND_ENVIRONMENTS))" ]; then \
		echo 'LINGMIND_ENVIRONMENTS is required, for example: make configure-codex-lingmind LINGMIND_ENVIRONMENTS="wf3b"'; \
		exit 2; \
	fi
	$(PYTHON) scripts/render-codex-plugins.py \
		--output "$(CODEX_MARKETPLACE_OUTPUT)" \
		--marketplace-name "$(CODEX_MARKETPLACE_NAME)" \
		--apex-url "$(LINGMIND_APEX_URL)" \
		--oauth-client-id "$(LINGMIND_OAUTH_CLIENT_ID)" \
		--callback-port "$(LINGMIND_CALLBACK_PORT)" \
		$(CODEX_ENVIRONMENT_ARGS) $(CODEX_DEFAULT_ENVIRONMENT_ARG)
	@marketplaces_json="$$('$(CODEX)' plugin marketplace list --json)" || { \
		echo 'Failed to list Codex plugin marketplaces.'; \
		exit 1; \
	}; \
	marketplace_root="$$(printf '%s\n' "$$marketplaces_json" | \
		$(PYTHON) -c 'import json, sys; name = sys.argv[1]; data = json.load(sys.stdin); print(next((item["root"] for item in data.get("marketplaces", []) if item.get("name") == name), ""))' \
		"$(CODEX_MARKETPLACE_NAME)")"; \
	if [ -z "$$marketplace_root" ]; then \
		'$(CODEX)' plugin marketplace add "$(CODEX_MARKETPLACE_OUTPUT)"; \
	elif [ "$$marketplace_root" != "$(abspath $(CODEX_MARKETPLACE_OUTPUT))" ]; then \
		echo "marketplace $(CODEX_MARKETPLACE_NAME) already points to $$marketplace_root"; \
		exit 2; \
	fi
	'$(CODEX)' plugin add "lingmind@$(CODEX_MARKETPLACE_NAME)"
	@echo 'LingMind MCP configuration installed. Start a new Codex task to load the updated connections.'

configure-workbuddy-lingmind:
	$(PYTHON) scripts/configure-workbuddy-lingmind.py \
		--workbuddy-home "$(WORKBUDDY_HOME)" \
		--apex-url "$(LINGMIND_APEX_URL)" \
		$(WORKBUDDY_ENVIRONMENT_ARG)

configure-doubao-lingmind:
	$(PYTHON) scripts/configure-doubao-lingmind.py \
		--doubao-workspace "$(DOUBAO_WORKSPACE)" \
		--apex-url "$(LINGMIND_APEX_URL)" \
		$(DOUBAO_ENVIRONMENT_ARG)
