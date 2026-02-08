"""
Extracteur pour les informations de la délibération.
"""
import re
from .base import BaseExtractor
from .config import MOIS_FR


class DeliberationExtractor(BaseExtractor):
    """Extracteur pour les informations de la délibération."""
    
    def extract(self) -> dict:
        """Extrait les informations de la délibération."""
        self.data = {
            "id": self._extract_id(),
            "numero": self._extract_numero(),
            "date": self._extract_date(),
            "date_convocation": self._extract_date_convocation(),
            "matiere": {
                "code": "",  # À enrichir manuellement ou via IA
                "nom": ""
            },
            "objet": self._extract_objet(),
            "resume": "",  # À enrichir manuellement ou via IA
            "url_document": ""
        }
        return self.data
    
    def _extract_id(self) -> str:
        """Extrait l'identifiant de la délibération."""
        # Pattern DCM/DEL
        match = self.search_pattern('delib_id')
        if match:
            return f"DCM{match.group(1)}"
        
        # Pattern dans l'ID préfecture
        match = self.search_pattern('pref_id_complet')
        if match:
            # Extraire la partie DCM de l'ID complet
            full_id = match.group(1)
            dcm_match = re.search(r'(DCM\d+_\d+)', full_id)
            if dcm_match:
                return dcm_match.group(1)
        
        return ""
    
    def _extract_numero(self) -> int | None:
        """Extrait le numéro de la délibération."""
        # Cherche "n° X" ou "N° X"
        match = re.search(r'n°\s*(\d+)', self.text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_date(self) -> str:
        """Extrait la date de la délibération (date de séance)."""
        # Date dans "Séance du..."
        match = self.search_pattern('seance_date')
        if match:
            return self.parse_date_texte(match.group(1), match.group(2), match.group(3))
        
        # Date textuelle générique
        match = self.search_pattern('date_texte')
        if match:
            return self.parse_date_texte(match.group(1), match.group(2), match.group(3))
        
        return ""
    
    def _extract_date_convocation(self) -> str:
        """Extrait la date de convocation."""
        match = self.search_pattern('convocation')
        if match:
            return self.parse_date_texte(match.group(1), match.group(2), match.group(3))
        return ""
    
    def _extract_objet(self) -> str:
        """Extrait l'objet de la délibération."""
        # Cherche le titre après "n° X"
        match = self.search_pattern('objet_titre')
        if match:
            objet = self.clean_text(match.group(1))
            if len(objet) > 10:  # Éviter les faux positifs
                return objet
        
        # Pattern alternatif avec "Objet :"
        patterns = [
            r'(?:Objet|OBJET)\s*[:.-]\s*(.+?)(?:\n\n|\r\n\r\n|Vu|VU|Considérant)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
            if match:
                objet = self.clean_text(match.group(1))
                return objet[:500]
        
        return ""
