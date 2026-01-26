"""
Extracteur pour les informations de séance (lieu, président, secrétaire, rapporteur).
"""
import re
from .base import BaseExtractor


class SeanceExtractor(BaseExtractor):
    """Extracteur pour les informations de séance."""
    
    def extract(self) -> dict:
        """Extrait les informations de séance."""
        self.data = {
            "lieu": self._extract_lieu(),
            "president": self._extract_president(),
            "secretaire": self._extract_secretaire(),
            "rapporteur": self._extract_rapporteur()
        }
        return self.data
    
    def _extract_lieu(self) -> str:
        """Extrait le lieu de la séance."""
        match = self.search_pattern('seance_lieu')
        if match:
            lieu = self.clean_text(match.group(1))
            # Nettoyer les caractères de fin
            lieu = re.sub(r'[\n\r]+.*$', '', lieu)
            return lieu
        
        # Pattern alternatif
        match = re.search(r'dans\s+(?:la\s+)?([^.]+?(?:Hôtel de Ville|Mairie|salle)[^.]*)', 
                          self.text, re.IGNORECASE)
        if match:
            return self.clean_text(match.group(1))
        
        return ""
    
    def _extract_president(self) -> dict:
        """Extrait les informations du président de séance."""
        result = {
            "civilite": "",
            "nom": "",
            "prenom": "",
            "fonction": ""
        }
        
        match = self.search_pattern('president')
        if match:
            result["civilite"] = self._normalize_civilite(match.group(1))
            result["nom"] = match.group(2).upper()
            if match.group(3):
                result["fonction"] = match.group(3)
            
            # Chercher le prénom dans la liste des membres
            prenom = self._find_prenom(result["nom"])
            if prenom:
                result["prenom"] = prenom
            
            # Chercher la fonction si pas trouvée
            if not result["fonction"]:
                func_match = re.search(rf'{result["nom"]}[,\s]+([A-Za-zÀ-ÿ]+)', self.text)
                if func_match:
                    result["fonction"] = func_match.group(1)
        
        return result
    
    def _extract_secretaire(self) -> dict:
        """Extrait les informations du secrétaire de séance."""
        result = {
            "civilite": "",
            "nom": "",
            "prenom": ""
        }
        
        match = self.search_pattern('secretaire')
        if match:
            result["civilite"] = self._normalize_civilite(match.group(1))
            result["prenom"] = match.group(2)
            result["nom"] = match.group(3).upper()
        
        return result
    
    def _extract_rapporteur(self) -> dict:
        """Extrait les informations du rapporteur."""
        result = {
            "civilite": "",
            "nom": "",
            "prenom": ""
        }
        
        match = self.search_pattern('rapporteur')
        if match:
            result["civilite"] = self._normalize_civilite(match.group(1))
            result["nom"] = match.group(2).upper()
            
            # Chercher le prénom dans la liste des membres
            prenom = self._find_prenom(result["nom"])
            if prenom:
                result["prenom"] = prenom
        
        return result
    
    def _normalize_civilite(self, civ: str) -> str:
        """Normalise la civilité."""
        if not civ:
            return ""
        civ = civ.strip()
        if civ in ['M', 'M.']:
            return 'M.'
        if civ in ['Mme', 'Mme.']:
            return 'Mme'
        return civ
    
    def _find_prenom(self, nom: str) -> str:
        """Trouve le prénom associé à un nom dans le texte."""
        # Cherche dans la section des membres présents
        pattern = rf'(M\.|Mme)\s+([A-Za-zÀ-ÿ\-]+)\s+{nom}'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            return match.group(2)
        return ""
