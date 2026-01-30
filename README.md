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
- Web UI: localhost:3000

## Metadata Extractor

L'extracteur de métadonnées permet d'analyser les PDFs de délibérations et d'en extraire les informations structurées (collectivité, séance, vote, membres, etc.).

### Mode Cloud (par défaut)

Le mode cloud récupère les PDFs depuis un bucket MinIO et sauvegarde les métadonnées dans MongoDB.

**Par défaut, seuls les nouveaux fichiers sont traités** (ceux qui n'ont pas encore de métadonnées dans MongoDB).

```bash
# Traiter uniquement les NOUVEAUX PDFs du bucket
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations

# Traiter un nombre limité de nouveaux PDFs
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations -n 10

# Mode FORCE : supprime les métadonnées existantes et retraite tout
python -m conversion.extractors.orchestrator --bucket larochelle-deliberations --force

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
| `--force`, `-f` | Supprime les métadonnées existantes et retraite tout (mode cloud) |

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

## API

L'API FastAPI expose les documents et métadonnées via des endpoints REST.

**Documentation interactive** : http://127.0.0.1:8000/docs

### Endpoints Documents

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/documents` | Liste tous les documents |
| `GET` | `/documents/{id}` | Récupère un document par son ID |
| `GET` | `/documents/by-url?url=...` | Récupère un document par son URL |
| `GET` | `/documents/by-filename/{filename}` | Récupère un document par son nom |
| `GET` | `/documents/{id}/metadata` | Récupère un document avec ses métadonnées |
| `GET` | `/sources` | Liste toutes les sources disponibles |

### Endpoints Métadonnées

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/metadata` | Liste les métadonnées (avec paramètre `format`) |
| `GET` | `/metadata/count` | Compte le nombre de métadonnées |
| `GET` | `/metadata/buckets` | Liste les buckets avec métadonnées |
| `GET` | `/metadata/{id}` | Récupère les métadonnées par ID |
| `GET` | `/metadata/by-filename/{filename}` | Récupère les métadonnées par nom de fichier |
| `GET` | `/metadata/search/by-delib-id?delib_id=...` | Recherche par ID de délibération |

### Paramètre `format`

Les endpoints métadonnées acceptent un paramètre `format` :
- `full` (défaut) : Retourne `full_metadata` et `scdl_metadata`
- `complete` : Retourne uniquement `full_metadata`
- `scdl` : Retourne uniquement `scdl_metadata`

### Recherche

```bash
# Recherche dans les métadonnées
GET /search?q=subvention&limit=10
```

## Matière Classification Tester

Outil de test et validation pour la classification automatique de la matière/sujet des délibérations selon la nomenclature ACTES. Compare la méthode par mots-clés avec les modèles LLM.

```bash
# Test sur un dossier
python -m conversion.matiere_tester --folder conversion/template -o results.json

# Test sur un fichier unique
python -m conversion.matiere_tester --file path/to/document.pdf

# Comparaison multi-modèles (4 LLM)
python -m conversion.matiere_tester --folder path/ --compare-models

# Test depuis bucket MinIO
python -m conversion.matiere_tester --bucket larochelle-deliberations --prefix path/
```

### Options

| Option | Description |
|--------|-------------|
| `--file`, `-f` | Fichier unique à tester |
| `--folder`, `-d` | Dossier contenant des documents |
| `--bucket`, `-b` | Bucket MinIO à tester |
| `--output`, `-o` | Fichier JSON de sortie (défaut: test_results.json) |
| `--compare-models`, `-c` | Tester tous les modèles LLM disponibles |
| `--models`, `-m` | Modèles spécifiques à tester (default, light, large, balanced) |
| `--recursive`, `-r` | Rechercher dans les sous-dossiers |
| `--quiet`, `-q` | Supprime l'affichage de progression |

### Variables d'environnement

```bash
# Token HuggingFace (requis pour classification LLM)
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
```

Obtenir un token : https://huggingface.co/settings/tokens

**Note** : L'API HuggingFace gratuite a une limite de crédits mensuelle (~1000-2000 requêtes). En cas d'erreur 402, utiliser uniquement les mots-clés ou souscrire à HuggingFace PRO
