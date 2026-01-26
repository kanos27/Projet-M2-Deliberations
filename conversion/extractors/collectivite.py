"""
Extracteur pour les informations de la collectivité.
"""
import re
import csv
from pathlib import Path
from difflib import SequenceMatcher
from .base import BaseExtractor


class CommuneReference:
    """Classe pour gérer la référence des communes."""
    
    def __init__(self, csv_path=None):
        self.communes = {}
        if csv_path is None:
            csv_path = Path(__file__).parent.parent / "communes_reference.csv"
        self.load_communes(csv_path)
    
    def load_communes(self, csv_path):
        """Charge les données de référence depuis le CSV."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nom = row['COLL_NOM'].strip()
                    self.communes[nom.lower()] = {
                        'siret': row['COLL_SIRET'].strip(),
                        'pref_id': row['PREF_ID'].strip()
                    }
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Erreur chargement communes: {e}")
    
    def similarity(self, a: str, b: str) -> float:
        """Calcule la similarité entre deux chaînes."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find(self, nom_recherche: str, seuil: float = 0.8) -> dict | None:
        """Trouve une commune avec correspondance flexible."""
        if not nom_recherche:
            return None
        
        nom_clean = nom_recherche.lower().strip()
        
        # Correspondance exacte
        if nom_clean in self.communes:
            return self.communes[nom_clean]
        
        # Correspondance floue
        best_match = None
        best_score = 0
        
        for nom_ref in self.communes.keys():
            score = self.similarity(nom_clean, nom_ref)
            if score > best_score and score >= seuil:
                best_score = score
                best_match = nom_ref
        
        if best_match:
            return self.communes[best_match]
        
        return None


class CollectiviteExtractor(BaseExtractor):
    """Extracteur pour les informations de la collectivité."""
    
    def __init__(self, text: str, commune_ref: CommuneReference = None):
        super().__init__(text)
        self.commune_ref = commune_ref or CommuneReference()
    
    def extract(self) -> dict:
        """Extrait les informations de la collectivité."""
        nom = self._extract_nom()
        
        # Chercher SIRET dans la référence
        siret = ""
        if nom and self.commune_ref:
            ref_data = self.commune_ref.find(nom)
            if ref_data:
                siret = ref_data.get('siret', '')
        
        self.data = {
            "nom": f"Ville de {nom}" if nom else "",
            "siret": siret
        }
        return self.data
    
    def _extract_nom(self) -> str:
        """Extrait le nom de la collectivité."""
        # Pattern principal
        match = self.search_pattern('coll_nom')
        if match:
            return self.clean_text(match.group(1))
        
        # Patterns alternatifs
        patterns = [
            r"(?:Ville|VILLE)\s+(?:de|d')\s+([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s-]+?)(?:,|\.|\s*convoqué)",
            r"(?:Commune|COMMUNE)\s+(?:de|d')\s+([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s-]+?)(?:,|\.)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                return self.clean_text(match.group(1))
        
        return ""
    
    def get_pref_id(self, nom: str = None) -> str:
        """Récupère l'ID de préfecture depuis la référence."""
        if nom is None:
            nom = self._extract_nom()
        
        if nom and self.commune_ref:
            ref_data = self.commune_ref.find(nom)
            if ref_data:
                return ref_data.get('pref_id', '')
        return ""
