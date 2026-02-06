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
        """Extrait les informations du président de séance.
        
        Format attendu: "Sous la présidence de M. Jean-François FOUNTAINE, Maire"
        """
        result = {
            "civilite": "",
            "nom": "",
            "prenom": "",
            "fonction": ""
        }
        
        match = self.search_pattern('president')
        if match:
            result["civilite"] = self._normalize_civilite(match.group(1))
            result["prenom"] = match.group(2)  # Prénom (ex: Jean-François)
            result["nom"] = match.group(3).upper()  # NOM (ex: FOUNTAINE)
            if match.lastindex >= 4 and match.group(4):
                # Nettoyer la fonction - seulement le premier mot (ex: "Maire")
                fonction = match.group(4).strip()
                fonction = re.split(r'[\n\r,]', fonction)[0].strip()
                result["fonction"] = fonction
        
        return result
    
    def _extract_secretaire(self) -> dict:
        """Extrait les informations du secrétaire de séance.
        
        Formats attendus:
        - "Secrétaires de Séance : M. SABATIER et M. DUBOIS"
        - "Secrétaire : M. Prénom NOM"
        """
        result = {
            "civilite": "",
            "nom": "",
            "prenom": ""
        }
        
        # Pattern pour secrétaire(s) avec juste le nom en majuscules
        match = self.search_pattern('secretaire')
        if match:
            result["civilite"] = self._normalize_civilite(match.group(1))
            result["nom"] = match.group(2).upper()
            # Chercher le prénom dans la liste des membres
            prenom = self._find_prenom(result["nom"])
            if prenom:
                result["prenom"] = prenom
        
        return result
    
    def _extract_rapporteur(self) -> dict:
        """Extrait les informations du rapporteur."""
        result = {
            "civilite": "",
            "nom": "",
            "prenom": "",
            "fonction": ""
        }
        
        match = self.search_pattern('rapporteur')
        if match:
            civilite = self._normalize_civilite(match.group(1))
            nom = match.group(2)
            
            # Vérifier si c'est "le Maire" (titre, pas un nom)
            if nom.lower() in ['maire', 'le']:
                # Le rapporteur est "le Maire" - utiliser le président
                result["fonction"] = "Maire"
                # On peut essayer de récupérer le nom du président
                president = self._extract_president()
                if president.get("nom"):
                    result["civilite"] = president.get("civilite", "")
                    result["nom"] = president.get("nom", "")
                    result["prenom"] = president.get("prenom", "")
            else:
                result["civilite"] = civilite
                result["nom"] = nom.upper()
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
