![Python](https://img.shields.io/badge/Python-3.14-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C.svg?style=for-the-badge&logo=Prometheus&logoColor=white)
![Pi--hole](https://img.shields.io/badge/Pi--hole-96060C.svg?style=for-the-badge&logo=Pi-hole&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED.svg?style=for-the-badge&logo=Docker&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-0F1689.svg?style=for-the-badge&logo=Helm&logoColor=white)
![Task](https://img.shields.io/badge/Task-29BEB0.svg?style=for-the-badge&logo=Task&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64.svg?style=for-the-badge&logo=Ruff&logoColor=black)

# pihole-exporter

Prometheus exporter for [Pi-hole v6](https://pi-hole.net/). Exposes DNS query statistics, upstream
resolver metrics, gravity list info, and version data as Prometheus metrics.

## Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `pihole_up` | Gauge | 1 if the last scrape succeeded, 0 otherwise |
| `pihole_queries_total` | Gauge | Total DNS queries |
| `pihole_queries_blocked_total` | Gauge | Total blocked queries |
| `pihole_queries_percent_blocked` | Gauge | Percentage of queries blocked |
| `pihole_queries_unique_domains` | Gauge | Number of unique domains seen |
| `pihole_queries_forwarded` | Gauge | Forwarded queries |
| `pihole_queries_cached` | Gauge | Cached queries |
| `pihole_clients_active` | Gauge | Active clients |
| `pihole_clients_total` | Gauge | Total clients |
| `pihole_gravity_domains_being_blocked` | Gauge | Domains blocked by gravity |
| `pihole_gravity_last_update_timestamp` | Gauge | Last gravity update (epoch) |
| `pihole_query_type_count{type}` | Gauge | Queries by DNS type (A, AAAA, MX, …) |
| `pihole_upstream_queries_total{ip,port,name}` | Gauge | Queries per upstream server |
| `pihole_upstream_queries_failed{ip,port,name}` | Gauge | Failed queries per upstream server |
| `pihole_upstream_response_time_ms{ip,port,name}` | Gauge | Response time per upstream (ms) |
| `pihole_version_info{core}` | Gauge | Pi-hole version (always 1) |
| `pihole_scrape_duration_seconds` | Gauge | Duration of the last scrape |
| `pihole_scrape_errors_total` | Counter | Cumulative scrape errors |

## Configuration

All settings are read from environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `PIHOLE_HOST` | `localhost` | Pi-hole hostname or IP |
| `PIHOLE_PORT` | `80` | Pi-hole HTTP port |
| `PIHOLE_PASSWORD` | `` | Pi-hole admin password (leave empty if passwordless) |
| `PIHOLE_HTTPS` | `false` | Use HTTPS to connect to Pi-hole |
| `EXPORTER_PORT` | `9666` | Port the exporter listens on |
| `SCRAPE_INTERVAL` | `30` | Seconds between keep-alive sleeps |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## Usage

### Docker

```bash
docker run -d \
  -e PIHOLE_HOST=192.168.1.1 \
  -e PIHOLE_PASSWORD=yourpassword \
  -p 9666:9666 \
  ghcr.io/cdelgehier/pihole-exporter:latest
```

### Docker Compose

```yaml
services:
  pihole-exporter:
    image: ghcr.io/cdelgehier/pihole-exporter:latest
    environment:
      PIHOLE_HOST: 192.168.1.1
      PIHOLE_PASSWORD: yourpassword
    ports:
      - "9666:9666"
```

### Helm

```bash
helm install pihole-exporter oci://ghcr.io/cdelgehier/helm-charts/pihole-exporter \
  --set pihole.host=192.168.1.1 \
  --set pihole.passwordSecretRef.name=pihole-password
```

### ArgoCD (v3+)

Use the native OCI source format with `path: .` — do not use the Helm `chart:` field:

```yaml
- repoURL: oci://ghcr.io/cdelgehier/helm-charts/pihole-exporter
  path: .
  targetRevision: "0.2.1"
  helm:
    valuesObject:
      pihole:
        host: "pihole-web.pihole.svc.cluster.local"
```

## Development

```bash
# Install dependencies
task install

# Install pre-commit hooks
task pre-commit-install

# Run tests
task test

# Lint
task lint

# Run everything (CI)
task ci
```

## License

MIT
