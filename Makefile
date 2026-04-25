.PHONY: build test fmt lint generate-sdks

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
