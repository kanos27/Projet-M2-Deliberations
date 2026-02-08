"""
Extracteur pour les informations de préfecture.
"""
import re
from .base import BaseExtractor


class PrefectureExtractor(BaseExtractor):
    """Extracteur pour les informations de préfecture."""
    
    def extract(self) -> dict:
        """Extrait les informations de préfecture."""
        self.data = {
            "id": self._extract_id(),
            "date_envoi": self._extract_date_envoi(),
            "date_reception": self._extract_date_reception(),
            "date_publication": self._extract_date_publication()
        }
        return self.data
    
    def _extract_id(self) -> str:
        """Extrait l'identifiant préfecture complet."""
        match = self.search_pattern('pref_id_complet')
        if match:
            return match.group(1)
        return ""
    
    def _extract_date_envoi(self) -> str:
        """Extrait la date d'envoi en préfecture."""
        match = self.search_pattern('pref_envoi')
        if match:
            return self.parse_date_numeric(match.group(1), match.group(2), match.group(3))
        return ""
    
    def _extract_date_reception(self) -> str:
        """Extrait la date de réception en préfecture."""
        match = self.search_pattern('pref_reception')
        if match:
            return self.parse_date_numeric(match.group(1), match.group(2), match.group(3))
        return ""
    
    def _extract_date_publication(self) -> str:
        """Extrait la date de publication."""
        match = self.search_pattern('pref_publication')
        if match:
            return self.parse_date_numeric(match.group(1), match.group(2), match.group(3))
        return ""
