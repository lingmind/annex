.PHONY: build test fmt lint generate-sdks test-generated-sdks validate-plugins

PYTHON ?= python3

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

test-generated-sdks:
	npm --prefix generated/typescript run build
	node scripts/test-generated-sdks.cjs
	$(PYTHON) scripts/test-generated-sdks.py
	cd generated/java && bash ./gradlew compileJava

validate-plugins:
	node scripts/test-dsh-plugin.mjs
	$(PYTHON) scripts/render-agent-plugins.py --check
	$(PYTHON) scripts/test-agent-distribution.py
	$(PYTHON) scripts/test-public-content.py
	$(PYTHON) scripts/test-configure-workbuddy-lingmind.py
	$(PYTHON) scripts/test-configure-doubao-lingmind.py
	$(PYTHON) scripts/validate-agent-plugins.py

.PHONY: render-agent-plugins release-agent-plugins setup-agent
render-agent-plugins:
	$(PYTHON) scripts/render-agent-plugins.py

release-agent-plugins:
	$(PYTHON) scripts/release-agent-plugins.py

AGENT ?= codex
LINGMIND_ENVIRONMENT_CODE ?=
setup-agent:
	$(PYTHON) scripts/setup-agent.py --agent "$(AGENT)" $(if $(strip $(LINGMIND_ENVIRONMENT_CODE)),--environment-code "$(LINGMIND_ENVIRONMENT_CODE)")
