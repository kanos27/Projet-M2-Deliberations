# Scraper Délibérations La Rochelle

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
```

## Configuration

Modifier `config.py` :
- `TARGET_DATES` : dates à scraper
- `HEADLESS_MODE` : `True` = arrière-plan, `False` = navigateur visible
- `TIMEOUT` : temps d'attente max (secondes)

## Utilisation

```bash
python main.py
```

## Résultats

- **PDFs** : dossier `pdf/` (format: `période_001.pdf`)
- **Excel** : `resultats_larochelle.xlsx` avec colonnes :
  - numero_ordre
  - titre
  - date_conseil
  - lien
  - periode
  - date_extraction
