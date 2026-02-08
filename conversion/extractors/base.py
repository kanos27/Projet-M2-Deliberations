"""
Classe de base pour tous les extracteurs.
"""
import re
from abc import ABC, abstractmethod
from .config import PATTERNS, MOIS_FR


class BaseExtractor(ABC):
    """Classe de base abstraite pour les extracteurs de métadonnées."""
    
    def __init__(self, text: str):
        self.text = text
        self.data = {}
    
    @abstractmethod
    def extract(self) -> dict:
        """Méthode principale d'extraction à implémenter."""
        pass
    
    def search_pattern(self, pattern_name: str, flags=re.IGNORECASE) -> re.Match | None:
        """Recherche un pattern prédéfini dans le texte."""
        if pattern_name in PATTERNS:
            return re.search(PATTERNS[pattern_name], self.text, flags)
        return None
    
    def search_all_patterns(self, pattern_name: str, flags=re.IGNORECASE) -> list:
        """Trouve toutes les occurrences d'un pattern."""
        if pattern_name in PATTERNS:
            return re.findall(PATTERNS[pattern_name], self.text, flags)
        return []
    
    def parse_date_texte(self, day: str, month_name: str, year: str) -> str:
        """Convertit une date textuelle en format ISO."""
        month = MOIS_FR.get(month_name.lower(), '01')
        return f"{year}-{month}-{day.zfill(2)}"
    
    def parse_date_numeric(self, day: str, month: str, year: str) -> str:
        """Convertit une date numérique en format ISO."""
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    def clean_text(self, text: str) -> str:
        """Nettoie un texte (espaces multiples, etc.)."""
        if not text:
            return ""
        # Remplace les espaces multiples par un seul
        text = re.sub(r'\s+', ' ', text)
        # Supprime les espaces en début/fin
        return text.strip()
    
    def extract_number(self, pattern_name: str) -> int | None:
        """Extrait un nombre depuis un pattern."""
        match = self.search_pattern(pattern_name)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                return None
        return None
