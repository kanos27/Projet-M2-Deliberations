"""
Extracteur pour le contenu textuel principal de la délibération.

Objectif : Extraire le texte principal (corps) de la délibération, 
en excluant les métadonnées déjà extraites par d'autres modules :
- En-tête (EXTRAIT DU REGISTRE...)
- Informations de séance (membres présents, absents, président...)
- Numéro et titre de la délibération
- Rapporteur
- Vote et décision finale
- Signatures et pied de page

Le texte principal correspond au contenu explicatif de la délibération,
entre le rapporteur et la décision finale.
"""
import re
from .base import BaseExtractor


class ParagraphesExtractor(BaseExtractor):
    """Extracteur pour le contenu textuel principal de la délibération."""
    
    def extract(self) -> dict:
        """
        Extrait le contenu textuel principal.
        
        Returns:
            dict avec:
            - texte_integral: le texte complet du corps de la délibération
            - references_juridiques: liste des "Vu le/la..." 
            - considerants: liste des "Considérant que..."
            - proposition: texte de la proposition finale
            - commission_consultee: infos sur la commission consultée
        """
        # Extraire le texte principal (corps de la délibération)
        texte_principal = self._extract_texte_principal()
        
        self.data = {
            "texte_integral": texte_principal,
            "references_juridiques": self._extract_references_juridiques(),
            "considerants": self._extract_considerants(),
            "proposition": self._extract_proposition(),
            "commission_consultee": self._extract_commission(),
        }
        return self.data
    
    def _extract_texte_principal(self) -> str:
        """
        Extrait le texte principal de la délibération.
        
        Le texte principal commence après le rapporteur et se termine
        avant la décision finale (LE CONSEIL MUNICIPAL...).
        
        On exclut également :
        - Les lignes "Envoyé en préfecture..."
        - Les lignes "Reçu en préfecture..."
        - Les lignes "Publié le..."
        - Les lignes "ID : ..."
        - Les références de page "CM_XX_..."
        """
        text = self.text
        
        # 1. Trouver le début du contenu (après le rapporteur)
        start_pos = 0
        
        # Chercher "Rapporteur : M./Mme XXX" suivi d'un saut de ligne
        rapporteur_patterns = [
            r'[Rr]apporteur\s*:\s*(?:M\.|Mme|M)\s+[^\n]+\n',
            r'[Rr]apporteur\s*:\s*[^\n]+\n',
        ]
        for pattern in rapporteur_patterns:
            match = re.search(pattern, text)
            if match:
                start_pos = match.end()
                break
        
        # Si pas de rapporteur trouvé, chercher après le titre en majuscules
        if start_pos == 0:
            # Pattern: n° XX suivi du titre en majuscules
            title_match = re.search(
                r'n[°o]\s*\d+\s*\n+[A-ZÀ-ÿ][A-ZÀ-ÿ\s\'\-\d,\.]+\n',
                text
            )
            if title_match:
                start_pos = title_match.end()
        
        # 2. Trouver la fin du contenu (avant la décision)
        end_pos = len(text)
        
        # Patterns de fin (décision du conseil)
        end_patterns = [
            r'\n\s*LE\s+CONSEIL\s+MUNICIPAL\s+(?:PREND\s+ACTE|DÉCIDE|ADOPTE|AUTORISE)',
            r'\n\s*CES\s+DISPOSITIONS[^\n]+ADOPT[ÉE]+S?',
            r'\n\s*Membres\s+en\s+exercice\s*:',
            r'\n\s*(?:Pour|Contre|Abstentions?)\s*:\s*\d+',
            r'\n\s*P\.\s*[Ll]e\s+[Mm]aire',  # Signature
        ]
        
        for pattern in end_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.start() < end_pos:
                    end_pos = match.start()
        
        # 3. Extraire le texte brut
        if start_pos >= end_pos:
            return ""
        
        texte_brut = text[start_pos:end_pos]
        
        # 4. Nettoyer le texte
        texte_nettoye = self._nettoyer_texte(texte_brut)
        
        return texte_nettoye
    
    def _nettoyer_texte(self, texte: str) -> str:
        """
        Nettoie le texte en supprimant les éléments parasites.
        """
        if not texte:
            return ""
        
        # Supprimer les références de page (CM_01_24/04/23_1/2)
        texte = re.sub(r'CM_\d+_[\d/]+_\d+/\d+', '', texte)
        
        # Supprimer les lignes de préfecture
        texte = re.sub(r'Envoyé en préfecture le\s*[\d/]+\s*\n?', '', texte)
        texte = re.sub(r'Reçu en préfecture le\s*[\d/]+\s*\n?', '', texte)
        texte = re.sub(r'Publié le\s*[\d/]*\s*\n?', '', texte)
        
        # Supprimer les ID de document
        texte = re.sub(r'ID\s*:\s*[\d\-A-Z_]+\s*\n?', '', texte)
        
        # Supprimer les lignes vides multiples
        texte = re.sub(r'\n{3,}', '\n\n', texte)
        
        # Nettoyer les espaces multiples
        texte = re.sub(r'[ \t]+', ' ', texte)
        
        # Supprimer les espaces en début/fin de ligne
        texte = '\n'.join(line.strip() for line in texte.split('\n'))
        
        # Supprimer les lignes vides au début et à la fin
        texte = texte.strip()
        
        return texte
    
    def _extract_references_juridiques(self) -> list:
        """
        Extrait les références juridiques (Vu le..., Vu la...).
        """
        references = []
        
        # Pattern pour "Vu le/la/l'/les..."
        vu_pattern = r'Vu\s+((?:le|la|l\'|les)\s+[^;]+?)(?:;\s*|(?=\nVu\s)|(?=\n[Cc]onsidérant)|(?=\nIl\s+est\s+proposé)|$)'
        matches = re.findall(vu_pattern, self.text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            ref = self.clean_text(f"Vu {match}")
            if ref and len(ref) > 10 and ref not in references:
                references.append(ref)
        
        return references
    
    def _extract_considerants(self) -> list:
        """
        Extrait les considérants (Considérant que...).
        """
        considerants = []
        
        # Pattern pour "Considérant que..."
        pattern = r'[Cc]onsidérant\s+((?:que\s+)?[^;]+?)(?:;\s*|,\s*\n|(?=\n[Cc]onsidérant)|(?=\nIl\s+est\s+proposé)|$)'
        matches = re.findall(pattern, self.text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            text = self.clean_text(f"Considérant {match}")
            if text and len(text) > 30 and text not in considerants:
                considerants.append(text)
        
        return considerants
    
    def _extract_proposition(self) -> dict:
        """
        Extrait la proposition soumise au Conseil municipal.
        
        La proposition est généralement au format :
        "Il est proposé au Conseil municipal... de [action]"
        """
        proposition = {
            "texte": "",
        }
        
        # Pattern principal - capture le texte de la proposition jusqu'à la décision
        # On veut capturer : "Il est proposé... de prendre acte/d'autoriser/de..."
        prop_patterns = [
            # Format: "Il est proposé au Conseil municipal, en accord avec la commission..., de [action]"
            r'Il\s+est\s+proposé\s+(?:au\s+Conseil\s+municipal|à\s+l\'assemblée\s+délibérante)[^.]*,\s*de\s+([^.]+\.)',
            # Format: "Il est proposé au Conseil municipal de [action]"
            r'Il\s+est\s+proposé\s+(?:au\s+Conseil\s+municipal|à\s+l\'assemblée\s+délibérante)\s+de\s+([^.]+\.)',
            # Format avec deux-points: "Il est proposé au Conseil municipal : - point 1 - point 2"
            r'Il\s+est\s+proposé\s+(?:au\s+Conseil\s+municipal|à\s+l\'assemblée\s+délibérante)[^:]*:\s*\n((?:[-–•]\s*[^\n]+\n?)+)',
        ]
        
        for pattern in prop_patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                prop_text = match.group(1).strip()
                # Limiter à 2000 caractères max pour éviter de capturer trop
                if len(prop_text) > 2000:
                    prop_text = prop_text[:2000] + "..."
                proposition["texte"] = self._nettoyer_texte(prop_text)
                break
        
        return proposition
    
    def _extract_commission(self) -> dict:
        """Extrait les informations sur la commission consultée."""
        commission = {
            "numero": None,
            "nom": "",
            "date_reunion": "",
            "avis": ""
        }
        
        # Pattern pour la commission
        pattern = r'(?:en\s+accord\s+avec\s+la\s+)?[Cc]ommission\s+n[°o]\s*(\d+)\s*\(([^)]+)\)\s+réunie\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})'
        
        match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
        if match:
            commission["numero"] = int(match.group(1))
            # Nettoyer le nom
            nom = match.group(2).strip()
            nom = re.sub(r'\s+', ' ', nom)
            commission["nom"] = nom
            jour = match.group(3).zfill(2)
            mois = self._mois_to_num(match.group(4))
            annee = match.group(5)
            commission["date_reunion"] = f"{annee}-{mois}-{jour}"
        
        # Chercher l'avis
        if re.search(r'en\s+accord', self.text, re.IGNORECASE):
            commission["avis"] = "favorable"
        elif re.search(r'avis\s+favorable', self.text, re.IGNORECASE):
            commission["avis"] = "favorable"
        elif re.search(r'avis\s+défavorable', self.text, re.IGNORECASE):
            commission["avis"] = "défavorable"
        
        return commission
    
    def _mois_to_num(self, mois: str) -> str:
        """Convertit un nom de mois en numéro."""
        from .config import MOIS_FR
        return MOIS_FR.get(mois.lower(), '01')
