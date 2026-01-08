# config.py
BASE_URL = "https://affichagelegal.larochelle.fr/conseil-municipal/deliberations-adoptees"

# dates cibles
TARGET_DATES = {
    'décembre_2025': '2025-12-15',
    'novembre_2025': '2025-11-17',
    'décembre_2024': '2024-12-16',
    'novembre_2024': '2024-11-25'
}

# config
HEADLESS_MODE = True   # Mettre True pour cacher le navigateur
TIMEOUT = 10          