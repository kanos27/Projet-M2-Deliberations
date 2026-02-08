"""
Extracteur pour les informations de vote.
"""
import re
from .base import BaseExtractor


class VoteExtractor(BaseExtractor):
    """Extracteur pour les informations de vote."""
    
    def extract(self) -> dict:
        """Extrait les informations de vote."""
        self.data = {
            "membres_en_exercice": self._extract_effectif(),
            "membres_presents": self._extract_presents(),
            "membres_procurations": self._extract_procurations(),
            "votants": self._extract_votants(),
            "suffrages_exprimes": self._extract_suffrages(),
            "votes_pour": self._extract_pour(),
            "votes_contre": self._extract_contre(),
            "abstentions": self._extract_abstentions(),
            "resultat": self._extract_resultat()
        }
        return self.data
    
    def _extract_effectif(self) -> int | None:
        """Extrait l'effectif théorique (membres en exercice)."""
        return self.extract_number('vote_effectif')
    
    def _extract_presents(self) -> int | None:
        """Extrait le nombre de membres présents."""
        return self.extract_number('vote_presents')
    
    def _extract_procurations(self) -> int | None:
        """Extrait le nombre de procurations."""
        return self.extract_number('vote_procurations')
    
    def _extract_votants(self) -> int | None:
        """Extrait le nombre de votants."""
        return self.extract_number('vote_votants')
    
    def _extract_suffrages(self) -> int | None:
        """Extrait le nombre de suffrages exprimés."""
        match = self.search_pattern('vote_suffrages')
        if match and match.group(1):
            return int(match.group(1))
        # Si pas de valeur explicite, calculer depuis les autres
        pour = self._extract_pour()
        contre = self._extract_contre()
        if pour is not None and contre is not None:
            return pour + contre
        return None
    
    def _extract_pour(self) -> int | None:
        """Extrait le nombre de votes pour."""
        return self.extract_number('vote_pour')
    
    def _extract_contre(self) -> int | None:
        """Extrait le nombre de votes contre."""
        return self.extract_number('vote_contre')
    
    def _extract_abstentions(self) -> int | None:
        """Extrait le nombre d'abstentions."""
        return self.extract_number('vote_abstention')
    
    def _extract_resultat(self) -> str:
        """Extrait le résultat du vote."""
        match = self.search_pattern('vote_resultat')
        if match:
            resultat = match.group(1).upper()
            # Normaliser
            if 'UNANIMITÉ' in resultat:
                return "ADOPTÉE À L'UNANIMITÉ"
            elif 'ADOPTÉE' in resultat or 'ADOPTE' in resultat:
                return "ADOPTÉE"
            elif 'REJETÉE' in resultat or 'REJETE' in resultat:
                return "REJETÉE"
        return ""
