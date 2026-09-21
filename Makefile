PLUGIN_DIR ?= ../omarchy-pulse

.PHONY: test build locations nginx-conf

test:
	go test -race ./...

build:
	go build -o pulse .

# Regenerates the catalog for this repo and, when the plugin checkout is next
# door, for the plugin too — the two must not drift apart by hand.
locations:
	python3 tools/gen-locations.py --out locations.json --also $(PLUGIN_DIR)/locations.json

nginx-conf:
	tools/gen-cloudflare-nginx.sh > deploy/cloudflare-realip.conf
