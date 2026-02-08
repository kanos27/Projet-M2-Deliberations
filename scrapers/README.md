# Scrapers

Module de récupération de délibérations depuis différentes sources.

## Utilisation

```bash
python -m scrapers.larochelle [options]
```

### Options communes

| Option | Description |
|--------|-------------|
| `--local PATH`, `-l PATH` | Sauvegarde les PDFs dans un répertoire local |
| `--bucket NOM`, `-b NOM` | Utilise un bucket MinIO personnalisé |
| `--force`, `-f` | Force le re-téléchargement des documents existants |

### Options spécifiques (La Rochelle)

| Option | Description |
|--------|-------------|
| `-n NUM`, `--num NUM` | Nombre de documents à récupérer (défaut: 10) |
| `--page-size SIZE` | Taille des pages pour la pagination (défaut: 10) |

### Exemples

```bash
# Mode cloud (MinIO + MongoDB)
python -m scrapers.larochelle -n 50

# Mode local
python -m scrapers.larochelle --local ./pdfs -n 20

# Forcer le re-téléchargement
python -m scrapers.larochelle --force
```

## Créer un nouveau scraper

1. Créer une classe héritant de `BaseScraper`
2. Implémenter `fetch_pdf_links()` pour récupérer les liens PDF
3. Optionnel : surcharger `add_scraper_arguments()` et `run_with_args()` pour des arguments spécifiques

```python
from .base import BaseScraper

class MonScraper(BaseScraper):
    def __init__(self, local_mode=False, local_path=None):
        super().__init__("mon-bucket", "ma-source", local_mode, local_path)

    def fetch_pdf_links(self, num_documents=10, page_size=10):
        # Récupérer et retourner une liste de dicts avec: url, filename, title
        return [{"url": "...", "filename": "...", "title": "..."}]

if __name__ == "__main__":
    MonScraper.run_from_cli()
```

## Modes de fonctionnement

- **Mode cloud** (défaut) : upload vers MinIO, métadonnées dans MongoDB
- **Mode local** (`--local`) : sauvegarde dans un répertoire, pas de connexion aux services
