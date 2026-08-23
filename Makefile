.PHONY: build test fmt lint generate-sdks sync-plugin-tool-maps validate-plugins

PYTHON ?= python3
CODEX_HOME ?= $(HOME)/.codex
PLUGIN_VALIDATOR ?= $(CODEX_HOME)/skills/.system/plugin-creator/scripts/validate_plugin.py
SKILL_VALIDATOR ?= $(CODEX_HOME)/skills/.system/skill-creator/scripts/quick_validate.py

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

sync-plugin-tool-maps:
	$(PYTHON) scripts/sync-agent-tool-maps.py

validate-plugins:
	$(PYTHON) $(PLUGIN_VALIDATOR) plugins/lingmind
	$(PYTHON) $(PLUGIN_VALIDATOR) plugins/lingmind-operator
	@for skill in plugins/lingmind/skills/* plugins/lingmind-operator/skills/*; do \
		$(PYTHON) $(SKILL_VALIDATOR) "$$skill" || exit 1; \
	done
	$(PYTHON) scripts/sync-agent-tool-maps.py --check
	$(PYTHON) scripts/validate-agent-plugins.py
	@jq empty .agents/plugins/marketplace.json
