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

## Metadata Extractor

L'extracteur de métadonnées permet d'analyser les PDFs de délibérations et d'en extraire les informations structurées (collectivité, séance, vote, membres, etc.).

### Mode Cloud (par défaut)

Le mode cloud récupère les PDFs depuis un bucket MinIO et sauvegarde les métadonnées dans MongoDB.

```bash
# Traiter tous les PDFs du bucket
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations

# Traiter un nombre limité de PDFs
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations -n 10

# Avec mode debug (sauvegarde les textes extraits dans MinIO sous debug/)
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations -d
```

### Mode Local

Le mode local permet de traiter des fichiers locaux et génère des fichiers JSON en sortie.

```bash
# Traiter un répertoire de PDFs
python -m conversion.extractors.orchestrator --local ./pdfs -o output.json

# Traiter un fichier unique
python -m conversion.extractors.orchestrator --local ./document.pdf -o metadata.json

# Avec mode debug (sauvegarde les textes extraits localement)
python -m conversion.extractors.orchestrator --local ./pdfs -d
```

### Options

| Option | Description |
|--------|-------------|
| `--bucket`, `-b` | Nom du bucket MinIO (mode cloud) |
| `--local`, `-l` | Chemin local vers un fichier ou répertoire (mode local) |
| `-n`, `--num` | Nombre maximum de PDFs à traiter (mode cloud uniquement) |
| `-o`, `--output` | Fichier JSON de sortie (mode local uniquement) |
| `-c`, `--communes` | Fichier CSV de référence des communes |
| `-d`, `--debug` | Sauvegarde les textes extraits (MinIO ou local selon le mode) |

### Variables d'environnement

Le mode cloud utilise les variables d'environnement suivantes (avec valeurs par défaut) :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `MINIO_ENDPOINT` | `localhost:9000` | Point d'accès MinIO |
| `MINIO_ACCESS_KEY` | `minioadmin` | Clé d'accès MinIO |
| `MINIO_SECRET_KEY` | `minioadmin` | Clé secrète MinIO |
| `MINIO_SECURE` | `false` | Utiliser HTTPS pour MinIO |
| `MONGO_URL` | `mongodb://admin:admin@localhost:27017` | URL de connexion MongoDB |

### Structure des métadonnées

Chaque entrée MongoDB contient :
- `filename` : Nom du fichier PDF source
- `bucket` : Bucket MinIO source
- `extracted_at` : Date d'extraction
- `full_metadata` : Métadonnées complètes (collectivité, délibération, séance, vote, membres, etc.)
- `scdl_metadata` : Métadonnées au format SCDL légal
