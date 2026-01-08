# Ansible Monitoring Stack (ARM64) — with Docker Speedtest Exporter

Installs:
- Grafana (APT)
- Prometheus v3.6.0 (linux-arm64)
- Blackbox Exporter v0.27.0 (linux-arm64)
- Pushgateway v1.11.1 (linux-arm64)
- Docker + billimek/prometheus-speedtest-exporter:latest (port 9469)

Creates sudo users (ansibleadmin, monadmin), deploys your configs from `files/`, sets banners.

## Quick start
1) Edit `inventory.ini` (target IP & SSH user).
2) Review/replace configs in `files/` if needed.
3) Run:
   ansible-playbook -i inventory.ini site.yml
