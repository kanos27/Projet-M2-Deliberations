# Projet-M2-Deliberations
Le Projet de groupe de fin de M2, dont l'objectif est ici l'extraction structurée et automatisées d'informations de délibérations de collectivités

## Quick Start

```bash
# Start MinIO
docker-compose up -d

# Install deps
pip install -r requirements.txt

# Run scraper (La Rochelle)
python -m scrapers.larochelle -n 50
```

MinIO UI: http://127.0.0.1:9001 (minioadmin/minioadmin)
