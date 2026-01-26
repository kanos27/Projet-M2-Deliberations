"""
Extracteur pour les listes de membres (présents et absents).
"""
import re
from .base import BaseExtractor


class MembresExtractor(BaseExtractor):
    """Extracteur pour les listes de membres présents et absents."""
    
    def extract(self) -> dict:
        """Extrait les listes de membres."""
        self.data = {
            "membres_presents": self._extract_presents(),
            "membres_absents": self._extract_absents()
        }
        return self.data
    
    def _extract_presents(self) -> list:
        """Extrait la liste des membres présents."""
        # Chercher la section "Membres présents :"
        match = re.search(
            r'[Mm]embres\s+présents\s*:\s*\n?([\s\S]+?)(?:[Mm]embres\s+absents|Secrétaire)',
            self.text
        )
        
        if not match:
            return []
        
        section = match.group(1)
        return self._parse_membres_list(section)
    
    def _extract_absents(self) -> list:
        """Extrait la liste des membres absents avec leurs procurations."""
        # Chercher la section "Membres absents :"
        match = re.search(
            r'[Mm]embres\s+absents\s*:\s*\n?([\s\S]+?)(?:Secrétaire|n°\s*\d)',
            self.text
        )
        
        if not match:
            return []
        
        section = match.group(1)
        return self._parse_absents_list(section)
    
    def _parse_membres_list(self, section: str) -> list:
        """Parse une section de membres en liste structurée."""
        membres = []
        
        # Pattern pour extraire "Civilité Prénom NOM"
        # Gère les noms composés avec tirets
        pattern = r'(M\.|Mme)\s+([A-Za-zÀ-ÿ\-]+(?:\s+[A-Za-zÀ-ÿ\-]+)?)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+(?:\s+[A-ZÀ-ÿ\-]+)?)'
        
        for match in re.finditer(pattern, section):
            civilite = match.group(1)
            prenom = match.group(2).strip()
            nom = match.group(3).strip().upper()
            
            # Nettoyer le prénom (enlever les majuscules finales qui seraient du nom)
            prenom_parts = prenom.split()
            clean_prenom = []
            for part in prenom_parts:
                if not part.isupper():
                    clean_prenom.append(part)
            prenom = ' '.join(clean_prenom) if clean_prenom else prenom_parts[0] if prenom_parts else ''
            
            membres.append({
                "civilite": civilite,
                "nom": nom,
                "prenom": prenom
            })
        
        return membres
    
    def _parse_absents_list(self, section: str) -> list:
        """Parse la liste des absents avec leurs procurations."""
        absents = []
        
        # Pattern pour absents avec procuration
        pattern_proc = r'(M\.|Mme)\s+([A-Za-zÀ-ÿ\-]+)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)\s*\(pouvoir\s+à\s+(M\.|Mme)\s+([A-Za-zÀ-ÿ\-]+)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)\)'
        
        for match in re.finditer(pattern_proc, section, re.IGNORECASE):
            absent = {
                "civilite": match.group(1),
                "nom": match.group(3).upper(),
                "prenom": match.group(2),
                "procuration": {
                    "civilite": match.group(4),
                    "nom": match.group(6).upper(),
                    "prenom": match.group(5)
                }
            }
            absents.append(absent)
        
        # Pattern pour absents sans procuration (lignes seules)
        # Chercher les membres qui n'ont pas de "(pouvoir à"
        pattern_simple = r'(M\.|Mme)\s+([A-Za-zÀ-ÿ\-]+)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)(?!\s*\(pouvoir)'
        
        # Enlever les lignes déjà traitées
        section_cleaned = re.sub(pattern_proc, '', section, flags=re.IGNORECASE)
        
        for match in re.finditer(pattern_simple, section_cleaned):
            absent = {
                "civilite": match.group(1),
                "nom": match.group(3).upper(),
                "prenom": match.group(2)
            }
            # Éviter les doublons
            if not any(a['nom'] == absent['nom'] for a in absents):
                absents.append(absent)
        
        return absents
