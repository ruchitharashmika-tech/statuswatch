# StatusWatch: Secure CI/CD + GitOps Project

![CI](../../actions/workflows/ci.yml/badge.svg)

A mini uptime monitor (frontend + API + worker + Postgres) used as the
workload for a full DevSecOps pipeline.

## Architecture
_Add diagram -> docs/architecture.png_

## Run locally
```
docker compose up --build
```
Open http://localhost:8080

## Pipeline stages
- [x] Lint, unit tests (api, worker)
- [x] Hadolint, Gitleaks, Semgrep, Trivy (fs + image)
- [ ] SBOM (Syft)
- [ ] Cosign keyless signing + GHCR push
- [ ] ArgoCD deployment on kind (Helm/Kustomize)
- [ ] Kyverno: only signed images allowed
- [ ] Prometheus + Grafana dashboards

## Design decisions
_Why Trivy, keyless signing, pull-based CD..._

## Results
_Screenshots: blocked build -> fixed build_
