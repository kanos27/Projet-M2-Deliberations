# Projet-M2-Deliberations
Le Projet de groupe de fin de M2, dont l'objectif est ici l'extraction structurée et automatisées d'informations de délibérations de collectivités

## Quick Start

```bash
# Start services (MinIO + MongoDB + API)
docker-compose up -d

# Install deps
pip install -r requirements.txt

# Run scraper (La Rochelle)
python -m scrapers.larochelle -n 50
```

- MinIO UI: http://127.0.0.1:9001 (minioadmin/minioadmin)
- API: http://127.0.0.1:8000/docs
- MongoDB: localhost:27017 (admin/admin)
