# Omarchy Pulse — server

The backend for [Omarchy Pulse](https://github.com/ecylmz/omarchy-pulse): it
counts how many Omarchy systems are active right now, per area, per country,
and worldwide.

**Go + SQLite, one static binary.** Live presence is a map in memory with a
180-second TTL; SQLite holds five-minute aggregate snapshots. No Redis, no
PostgreSQL, no accounts, no sessions.

[`SPEC.md`](SPEC.md) is the design document: the product principles, the
geographic model, the privacy model, and the threat model. Read §4 and §5 first
— they explain the one decision everything else follows from.

## Collect presence, not identity

A heartbeat carries a hand-picked country and area, and nothing else. There is
no session identifier, because the server derives one itself:

```
key = HMAC-SHA256(boot_secret, ip_prefix)
```

`boot_secret` is 32 random bytes generated at start-up and never written
anywhere, so a restart invalidates every key. The key lives only as a map entry
with a TTL. Nothing else is derived from it, nothing is persisted from it, and
no client address is written to any log (SPEC §16.2).

That is also what makes the count worth showing: one address is one presence,
so a shell loop cannot inflate it and cannot be in two places at once
(SPEC §4.3).

## API

```
POST /v1/heartbeat                                  → {world, country, subdivision, …}
GET  /v1/history?scope=subdivision&code=TR-55       → points + peaks
GET  /healthz
```

That is the whole API.

## Run locally

```sh
ALLOW_DIRECT=1 DB_PATH=./pulse.db go run .
```

`ALLOW_DIRECT=1` is required because the server refuses to start behind a proxy
with no trusted-proxy list — see `TRUSTED_PROXIES` below and SPEC §5.3.

```sh
make test          # go test -race ./...
make locations     # regenerate the ISO 3166 catalog for this repo and the plugin
make nginx-conf    # refresh Cloudflare's ranges for deploy/
```

## Configuration

| Variable | Default | |
|---|---|---|
| `TRUSTED_PROXIES` | — | Reverse-proxy CIDRs. Required unless `ALLOW_DIRECT=1`. |
| `ALLOW_DIRECT` | — | `1` when clients really do connect directly. |
| `DB_PATH` | `/data/pulse.db` | |
| `PORT` | `5000` | |
| `PRESENCE_TTL_SECONDS` | `180` | |
| `HEARTBEAT_SECONDS` | `60` | Cadence handed to clients in the response. |
| `MIN_BEAT_SECONDS` | `5` | Per-key rate limit. Must not exceed the TTL. |
| `SNAPSHOT_SECONDS` | `300` | |
| `HISTORY_CACHE_SECONDS` | `30` | |
| `IPV6_PREFIX_BITS` | `56` | |
| `MAX_KEYS` | `200000` | |

## Deploy

Dockerfile build, one persistent volume, and two nginx files from `deploy/`
whose headers explain where each goes and why the placement matters:

```sh
dokku apps:create pulse
dokku domains:set pulse pulse.example.com
dokku storage:ensure-directory pulse
dokku storage:mount pulse /var/lib/dokku/data/storage/pulse:/data
dokku config:set pulse TRUSTED_PROXIES=172.17.0.0/16
git push dokku main
dokku letsencrypt:enable pulse
```

The nginx files are not optional extras: one carries the real-client-address
configuration the whole anti-abuse model depends on, one carries the rate limit
and turns off request logging. Installing the app without them leaves the count
forgeable and client addresses on disk.

## License

[MIT](LICENSE)
