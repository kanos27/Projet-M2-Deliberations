"""
Extracteur pour les paragraphes et le contenu textuel de la délibération.
"""
import re
from .base import BaseExtractor


class ParagraphesExtractor(BaseExtractor):
    """Extracteur pour les paragraphes principaux de la délibération."""
    
    def extract(self) -> dict:
        """Extrait les paragraphes et contenus textuels."""
        self.data = {
            "considerants": self._extract_considerants(),
            "commission_consultee": self._extract_commission(),
            "decision": self._extract_decision(),
            "paragraphes": self._extract_paragraphes()
        }
        return self.data
    
    def _extract_considerants(self) -> dict:
        """Extrait les considérants (contexte juridique et textuel)."""
        considerants = {
            "contexte_juridique": [],
            "contenu_textuel": []
        }
        
        # Contexte juridique : Vu le..., Vu la..., Vu l'article...
        vu_pattern = r"(Vu\s+(?:le|la|l'|les)\s+[^;]+(?:;|$))"
        vu_matches = re.findall(vu_pattern, self.text, re.IGNORECASE)
        if vu_matches:
            contexte = ' '.join([m.strip() for m in vu_matches])
            considerants["contexte_juridique"].append(contexte)
        
        # Chercher aussi les articles de loi mentionnés
        article_pattern = r"(L'article\s+L[\s\d\-]+[^\.]+\.)"
        article_matches = re.findall(article_pattern, self.text)
        for match in article_matches:
            text = self.clean_text(match)
            if text and len(text) > 20:
                if text not in considerants["contexte_juridique"]:
                    considerants["contexte_juridique"].append(text)
        
        # Contenu textuel : Considérant...
        considerant_pattern = r'[Cc]onsidérant\s+([^;]+?)(?:;|\n\n|[Cc]onsidérant)'
        considerant_matches = re.findall(considerant_pattern, self.text, re.DOTALL)
        for match in considerant_matches:
            text = self.clean_text(match)
            if text and len(text) > 20:
                considerants["contenu_textuel"].append(f"Considérant {text}")
        
        # Chercher aussi "Conformément à la réglementation..."
        conforme_pattern = r'(Conformément\s+à\s+la\s+réglementation[^\.]+\.)'
        conforme_matches = re.findall(conforme_pattern, self.text)
        for match in conforme_matches:
            text = self.clean_text(match)
            if text:
                considerants["contenu_textuel"].append(text)
        
        # Chercher "En application de ces dispositions..."
        application_pattern = r'(En\s+application\s+de\s+ces\s+dispositions[^\.]+\.)'
        application_matches = re.findall(application_pattern, self.text)
        for match in application_matches:
            text = self.clean_text(match)
            if text:
                considerants["contenu_textuel"].append(text)
        
        return considerants
    
    def _extract_commission(self) -> dict:
        """Extrait les informations sur la commission consultée."""
        commission = {
            "numero": None,
            "nom": "",
            "date_reunion": "",
            "avis": ""
        }
        
        # Pattern pour la commission avec différents formats
        patterns = [
            r'[Cc]ommission\s+n[°o]\s*(\d+)\s*\(([^)]+)\)\s+réunie\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            r'[Cc]ommission\s+n[°o]\s*(\d+)\s*\(([^)]+)\)[^r]*réunie\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                commission["numero"] = int(match.group(1))
                # Nettoyer le nom (enlever les sauts de ligne)
                nom = match.group(2).strip()
                nom = re.sub(r'\s+', ' ', nom)
                commission["nom"] = nom
                jour = match.group(3).zfill(2)
                mois = self._mois_to_num(match.group(4))
                annee = match.group(5)
                commission["date_reunion"] = f"{annee}-{mois}-{jour}"
                break
        
        # Chercher l'avis
        if re.search(r'avis\s+favorable', self.text, re.IGNORECASE):
            commission["avis"] = "favorable"
        elif re.search(r'avis\s+défavorable', self.text, re.IGNORECASE):
            commission["avis"] = "défavorable"
        elif re.search(r'prendre\s+acte', self.text, re.IGNORECASE):
            commission["avis"] = "prise d'acte"
        
        return commission
    
    def _extract_decision(self) -> str:
        """Extrait la décision finale."""
        patterns = [
            # Pattern principal
            r'Il\s+est\s+proposé\s+au\s+Conseil\s+municipal[^:]*:\s*\n?\s*[-•]?\s*([^\n]+)',
            # Décision simple
            r'[Dd]écide\s*:\s*\n?\s*[-•]?\s*([^\n]+)',
            # Arrête
            r'[Aa]rrête\s*:\s*\n?\s*[-•]?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.DOTALL)
            if match:
                decision = self.clean_text(match.group(1))
                # Limiter la longueur
                if len(decision) > 500:
                    decision = decision[:500] + "..."
                return decision
        
        return ""
    
    def _extract_paragraphes(self) -> dict:
        """Extrait les paragraphes numérotés principaux."""
        paragraphes = {}
        
        # 1. Pattern pour les paragraphes numérotés N° X : ...
        pattern_no = r'N[°o]\s*(\d+)\s*:\s*([^\n]+(?:\n(?!N[°o]\s*\d)[^\n]+)*)'
        matches = re.findall(pattern_no, self.text)
        
        for num, content in matches:
            key = f"paragraphe_{num}"
            content_clean = self._clean_paragraph(content)
            if content_clean:
                paragraphes[key] = content_clean
        
        # 2. Si pas trouvé, chercher les sections numérotées "1. Titre", "2. Titre"
        if not paragraphes:
            pattern_num = r'^\s*(\d+)\.\s*\n?([A-ZÀ-Ÿ][^\n]+)'
            matches = re.findall(pattern_num, self.text, re.MULTILINE)
            
            for num, title in matches:
                key = f"section_{num}"
                title_clean = self.clean_text(title)
                if title_clean and len(title_clean) > 5:
                    paragraphes[key] = title_clean
        
        # 3. Chercher les grandes sections thématiques (titres en majuscules ou spécifiques)
        if not paragraphes or len(paragraphes) < 3:
            section_patterns = [
                # Sections de type "Le contexte national", "Budget 2026"
                r'((?:Le\s+)?[Cc]ontexte\s+national[^\n]*)',
                r'(Situation\s+financière[^\n]*)',
                r'(Budget\s+\d{4}[^\n]*)',
                r'(Marchés\s+financiers[^\n]*)',
                r'(Projet\s+de\s+loi\s+de\s+finances[^\n]*)',
            ]
            
            idx = len(paragraphes) + 1
            for pattern in section_patterns:
                match = re.search(pattern, self.text, re.IGNORECASE)
                if match:
                    title = self.clean_text(match.group(1))
                    if title and len(title) > 5:
                        key = f"theme_{idx}"
                        if key not in paragraphes and title not in paragraphes.values():
                            paragraphes[key] = title
                            idx += 1
        
        # 4. Extraire les points clés avec puces (► ou •)
        bullet_pattern = r'►([^\n►]+)'
        bullet_matches = re.findall(bullet_pattern, self.text)
        if bullet_matches:
            points_cles = []
            for match in bullet_matches[:10]:  # Limiter à 10 points
                point = self.clean_text(match)
                if point and len(point) > 10:
                    points_cles.append(point)
            if points_cles:
                paragraphes["points_cles"] = points_cles
        
        # 5. Chercher "s'articule autour des points suivants" et extraire la liste
        articule_pattern = r"s'articule\s+autour\s+des\s+points\s+suivants\s*:\s*([\s\S]+?)(?:Il\s+est\s+proposé|$)"
        match = re.search(articule_pattern, self.text, re.IGNORECASE)
        if match:
            contenu = match.group(1)
            # Extraire les items numérotés
            items_pattern = r'(\d+)\.\s*\n?([^\n\d]+)'
            items = re.findall(items_pattern, contenu)
            if items:
                structure = {}
                for num, titre in items:
                    structure[f"point_{num}"] = self.clean_text(titre)
                if structure:
                    paragraphes["structure_document"] = structure
        
        return paragraphes
    
    def _clean_paragraph(self, content: str) -> str:
        """Nettoie un paragraphe en enlevant les éléments parasites."""
        content_clean = self.clean_text(content)
        # Enlever les références de page et préfecture
        content_clean = re.sub(r'CM_\d+_[\d/]+_\d+/\d+', '', content_clean)
        content_clean = re.sub(r'Envoyé en préfecture le[\d/\s]+', '', content_clean)
        content_clean = re.sub(r'Reçu en préfecture le[\d/\s]+', '', content_clean)
        content_clean = re.sub(r'Publié le[\d/\s]+', '', content_clean)
        content_clean = re.sub(r'ID\s*:\s*[\d\-A-Z_]+', '', content_clean)
        content_clean = re.sub(r'\s+', ' ', content_clean).strip()
        
        if len(content_clean) > 2000:
            content_clean = content_clean[:2000] + "..."
        return content_clean
    
    def _mois_to_num(self, mois: str) -> str:
        """Convertit un nom de mois en numéro."""
        from .config import MOIS_FR
        return MOIS_FR.get(mois.lower(), '01')
    def _mois_to_num(self, mois: str) -> str:
        """Convertit un nom de mois en numéro."""
        from .config import MOIS_FR
        return MOIS_FR.get(mois.lower(), '01')
