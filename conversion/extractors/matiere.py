"""
Extracteur pour la matière/sujet de la délibération.
Utilise un modèle HuggingFace gratuit pour classifier le document
selon la nomenclature ACTES officielle.
"""
import os
import re
import json
import time
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

from .base import BaseExtractor

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration HuggingFace
# Use the unified OpenAI-compatible chat completions endpoint via router
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Token REQUIRED for HuggingFace Inference API

# Modèles disponibles (testés et validés pour la classification française)
MODELS = {
    # Qwen 2.5 7B - Rapide et précis pour le français (recommandé)
    "default": "Qwen/Qwen2.5-7B-Instruct",
    # Llama 3.2 3B - Plus léger, bonne performance
    "light": "meta-llama/Llama-3.2-3B-Instruct",
    # Qwen 2.5 72B - Plus lent mais très précis
    "large": "Qwen/Qwen2.5-72B-Instruct",
    # Llama 3.1 8B - Alternative équilibrée
    "balanced": "meta-llama/Llama-3.1-8B-Instruct",
}


class NomenclatureParser:
    """Parse et structure la nomenclature ACTES depuis le fichier texte."""
    
    def __init__(self, nomenclature_path: str = None):
        self.nomenclature = {}
        self.flat_nomenclature = {}  # code -> nom complet avec hiérarchie
        
        if nomenclature_path is None:
            # Chemin par défaut
            nomenclature_path = Path(__file__).parent.parent / "template" / "nomenclature_actes.txt"
        
        if Path(nomenclature_path).exists():
            self._parse_file(nomenclature_path)
    
    def _parse_file(self, filepath: str):
        """Parse le fichier de nomenclature."""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Le fichier a un format particulier : 
        # Les codes sont sur des lignes séparées (ex: "1", "1", "1" puis "MARCHES PUBLICS")
        # On doit collecter les chiffres jusqu'à trouver le texte
        
        current_codes = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            # Ignorer les lignes vides et les headers
            if not line or line.startswith('Préfecture') or line.startswith('CODE') or \
               line.startswith('Nomenclature') or line == 'D.R.C.':
                current_codes = []
                continue
            
            # Vérifier si c'est un code (chiffre seul, possiblement avec espaces)
            if re.match(r'^\d+\s*$', line):
                current_codes.append(line.strip())
                continue
            
            # C'est un texte - construire le code à partir des chiffres accumulés
            if current_codes and not line.startswith('/'):
                code = '.'.join(current_codes)
                nom = line.strip()
                
                # Nettoyer le nom (supprimer les suffixes de pages, etc.)
                nom = re.sub(r'\s*\d+/\d+\s*$', '', nom)
                
                # Ne pas écraser un code existant avec un nom générique
                if nom and len(nom) > 1:
                    if code not in self.nomenclature or len(nom) > len(self.nomenclature.get(code, "")):
                        self.nomenclature[code] = nom
                        self.flat_nomenclature[code] = nom
            
            # Reset pour le prochain bloc
            current_codes = []
        
        # Ajouter les catégories principales manuellement
        self._ensure_main_categories()
        
        # Ajouter des sous-catégories importantes
        self._add_important_subcategories()
    
    def _ensure_main_categories(self):
        """S'assure que les catégories principales sont présentes."""
        main_categories = {
            "1": "COMMANDE PUBLIQUE",
            "2": "URBANISME", 
            "3": "DOMAINE ET PATRIMOINE",
            "4": "FONCTION PUBLIQUE",
            "5": "INSTITUTIONS ET VIE POLITIQUE",
            "6": "LIBERTÉS PUBLIQUES ET POUVOIRS DE POLICE",
            "7": "FINANCES LOCALES",
            "8": "DOMAINES DE COMPÉTENCES PAR THÈMES",
            "9": "AUTRES DOMAINES DE COMPÉTENCE"
        }
        
        for code, nom in main_categories.items():
            if code not in self.nomenclature:
                self.nomenclature[code] = nom
                self.flat_nomenclature[code] = nom
    
    def _add_important_subcategories(self):
        """Ajoute des sous-catégories importantes souvent utilisées."""
        # Compléter avec des codes importants s'ils ne sont pas déjà présents
        important_codes = {
            # Finances locales
            "7.1": "DÉCISIONS BUDGÉTAIRES",
            "7.1.1": "Budgets primitifs",
            "7.1.2": "Autres documents budgétaires (BS, DM, CA)",
            "7.1.3": "Débat d'orientation budgétaire",
            "7.2": "FISCALITÉ",
            "7.3": "EMPRUNTS",
            "7.4": "INTERVENTIONS ÉCONOMIQUES",
            "7.5": "SUBVENTIONS",
            "7.5.1": "Subventions aux associations",
            
            # Domaines thématiques
            "8.1": "ENSEIGNEMENT",
            "8.2": "AIDE SOCIALE",
            "8.3": "VOIRIE",
            "8.4": "AMÉNAGEMENT DU TERRITOIRE",
            "8.5": "POLITIQUE DE LA VILLE, HABITAT, LOGEMENT",
            "8.6": "EMPLOI, FORMATION PROFESSIONNELLE",
            "8.7": "TRANSPORTS",
            "8.8": "ENVIRONNEMENT",
            "8.9": "CULTURE",
            
            # Institutions
            "5.1": "ÉLECTION EXÉCUTIF",
            "5.2": "FONCTIONNEMENT DES ASSEMBLÉES",
            "5.3": "DÉSIGNATION DES REPRÉSENTANTS",
            "5.4": "DÉLÉGATIONS DE POUVOIRS ET DE FONCTIONS",
            "5.6": "EXERCICE DES MANDATS LOCAUX",
            "5.7": "INTERCOMMUNALITÉ",
            
            # Commande publique
            "1.1": "MARCHÉS PUBLICS",
            "1.2": "DÉLÉGATIONS DE SERVICE PUBLIC (DSP)",
            "1.4": "AUTRES CONTRATS",
            
            # Urbanisme
            "2.1": "DOCUMENTS D'URBANISME",
            "2.2": "ACTES RELATIFS AU DROIT D'OCCUPATION",
            "2.3": "DROIT DE PRÉEMPTION URBAIN",
            
            # Domaine et patrimoine
            "3.1": "ACQUISITIONS",
            "3.2": "ALIÉNATIONS",
            "3.3": "LOCATIONS",
            
            # Fonction publique
            "4.1": "PERSONNELS TITULAIRES ET STAGIAIRES",
            "4.2": "PERSONNELS CONTRACTUELS",
            "4.5": "RÉGIME INDEMNITAIRE",
            
            # Police
            "6.1": "POLICE MUNICIPALE",
            
            # Autres domaines
            "9.1": "AUTRES DOMAINES DE COMPÉTENCE DES COMMUNES",
            "9.4": "VŒUX ET MOTIONS",
        }
        
        for code, nom in important_codes.items():
            if code not in self.nomenclature:
                self.nomenclature[code] = nom
                self.flat_nomenclature[code] = nom
    
    def get_simplified_nomenclature(self) -> str:
        """Retourne une version simplifiée pour le prompt LLM."""
        # Grouper par catégorie principale
        categories = {}
        for code, nom in sorted(self.nomenclature.items()):
            main_cat = code.split('.')[0]
            if main_cat not in categories:
                categories[main_cat] = []
            categories[main_cat].append(f"{code}: {nom}")
        
        result = []
        for cat_num in sorted(categories.keys(), key=lambda x: int(x) if x.isdigit() else 99):
            result.extend(categories[cat_num][:15])  # Limiter par catégorie
        
        return '\n'.join(result[:80])  # Limiter le total
    
    def get_code_name(self, code: str) -> str:
        """Retourne le nom correspondant à un code."""
        return self.nomenclature.get(code, "")
    
    def find_closest_code(self, partial_code: str) -> tuple:
        """Trouve le code le plus proche d'un code partiel."""
        if partial_code in self.nomenclature:
            return partial_code, self.nomenclature[partial_code]
        
        # Chercher un code parent
        parts = partial_code.split('.')
        while parts:
            test_code = '.'.join(parts)
            if test_code in self.nomenclature:
                return test_code, self.nomenclature[test_code]
            parts.pop()
        
        return "9.1", "Autres domaines de compétence des communes"


class MatiereExtractor(BaseExtractor):
    """
    Extracteur de la matière/sujet de la délibération.
    Utilise l'API HuggingFace Inference (gratuite) pour classifier.
    """
    
    def __init__(self, text: str, nomenclature_path: str = None, 
                 use_llm: bool = True, model_name: str = "default"):
        super().__init__(text)
        self.nomenclature = NomenclatureParser(nomenclature_path)
        self.use_llm = use_llm
        self.model_name = MODELS.get(model_name, MODELS["default"])
        self.api_url = HF_API_URL  # Single endpoint for chat completions
        
        # Headers pour l'API HuggingFace
        self.headers = {"Content-Type": "application/json"}
        if HF_TOKEN:
            self.headers["Authorization"] = f"Bearer {HF_TOKEN}"
    
    def extract(self) -> dict:
        """Extrait la matière de la délibération."""
        self.data = {
            "code": "",
            "nom": "",
            "confidence": 0.0,
            "method": ""
        }
        
        # Étape 1: Essayer la classification par mots-clés (rapide)
        keyword_result = self._classify_by_keywords()
        if keyword_result and keyword_result.get("confidence", 0) >= 0.8:
            self.data = keyword_result
            self.data["method"] = "keywords"
            return {"code": self.data["code"], "nom": self.data["nom"]}
        
        # Étape 2: Utiliser le LLM si activé
        if self.use_llm:
            llm_result = self._classify_with_llm()
            if llm_result and llm_result.get("code"):
                self.data = llm_result
                self.data["method"] = "llm"
                return {"code": self.data["code"], "nom": self.data["nom"]}
        
        # Étape 3: Fallback sur les mots-clés même avec faible confiance
        if keyword_result and keyword_result.get("code"):
            self.data = keyword_result
            self.data["method"] = "keywords_fallback"
            return {"code": self.data["code"], "nom": self.data["nom"]}
        
        # Pas de classification possible
        return {"code": "", "nom": ""}
    
    def _extract_relevant_text(self) -> str:
        """
        Extrait uniquement la partie pertinente du document pour la classification.
        Supprime les en-têtes, signatures, listes de membres, etc.
        """
        text = self.text
        
        # Supprimer l'en-tête jusqu'à "n° X" ou "OBJET"
        header_patterns = [
            r'^.*?(?=n°\s*\d+)',  # Jusqu'au numéro de délibération
            r'^.*?(?=OBJET\s*:)',  # Jusqu'à l'objet
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                text = text[match.end():]
                break
        
        # Supprimer la liste des membres (présents/absents)
        text = re.sub(
            r'Membres?\s+(?:présents?|absents?)\s*:.*?(?=(?:n°|Secrétaire|Rapporteur|\n\n))',
            '', text, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Supprimer le bloc de vote final
        text = re.sub(
            r'(?:CES\s+DISPOSITIONS|MISES?\s+AUX\s+VOIX).*?(?=Délais|$)',
            '', text, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Supprimer les signatures et métadonnées de fin
        text = re.sub(
            r'(?:#signature#|Signé électroniquement|Délais et voies de recours).*',
            '', text, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Supprimer les références préfecture
        text = re.sub(
            r'Envoyé en préfecture.*?(?=\n|$)',
            '', text, flags=re.IGNORECASE
        )
        text = re.sub(r'ID\s*:\s*\d{3}-.*', '', text)
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()[:3000]  # Limiter la taille
    
    def _extract_objet(self) -> str:
        """Extrait l'objet/titre de la délibération."""
        patterns = [
            # Pattern "n° X" suivi d'un titre en majuscules (avec accents et chiffres)
            r'n°\s*\d+\s*\n([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŒÆÇ][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŒÆÇ0-9\s\'\-\(\),\.\/]+?)(?:\nRapporteur|\n[A-Z][a-z])',
            # Pattern plus souple pour titres en majuscules après n°
            r'n°\s*\d+\s*\n(.+?)(?:\nRapporteur)',
            # Pattern "Objet :"
            r'(?:Objet|OBJET)\s*[:.-]\s*(.+?)(?:\n\n|Vu|VU)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.DOTALL)
            if match:
                objet = match.group(1).strip()
                # Nettoyer les retours à la ligne et espaces multiples
                objet = re.sub(r'\s+', ' ', objet)
                # Supprimer les éventuels suffixes de pagination
                objet = re.sub(r'\s*CM_\d+.*$', '', objet)
                objet = re.sub(r'\s*\d+/\d+\s*$', '', objet)
                if len(objet) > 10:
                    return objet[:300]
        
        return ""
    
    def _classify_by_keywords(self) -> dict:
        """Classification rapide basée sur des mots-clés."""
        text_lower = self.text.lower()
        objet = self._extract_objet().lower()
        
        # Priorité à l'objet : poids x3 si le mot-clé est dans l'objet
        objet_weight = 3
        
        # Règles de mots-clés par catégorie
        # (code, [mots-clés], poids_base)
        keyword_rules = [
            # Petite enfance / Aide sociale (prioritaire car spécifique)
            ("8.2", ["petite enfance", "crèche", "accueil du jeune enfant", "accueil jeune enfant",
                     "halte-garderie", "assistante maternelle", "assistant maternel",
                     "relais petite enfance", "ram ", "sppe", "service public de la petite enfance",
                     "multi-accueil", "micro-crèche", "jardin d'enfants", "aide sociale",
                     "ccas", "action sociale", "insertion sociale"], 2),
            
            # Finances locales
            ("7.1.1", ["budget primitif", "bp 20", "budget principal"], 3),
            ("7.1.2", ["décision modificative", "dm 20", "budget supplémentaire", "bs 20",
                       "compte administratif", "ca 20"], 3),
            ("7.1.3", ["débat d'orientation", "dob 20", "orientations budgétaires"], 3),
            ("7.2", ["fiscalité", "taxe foncière", "taxe d'habitation", "taux d'imposition",
                     "cotisation foncière"], 2),
            ("7.3", ["emprunt", "prêt bancaire", "garantie d'emprunt", "ligne de trésorerie"], 2),
            ("7.4", ["subvention aux entreprises", "aide aux entreprises", 
                     "intervention économique", "zone d'activité"], 2),
            ("7.5.1", ["subvention association", "subventions aux associations"], 2),
            ("7.5", ["subvention", "aide financière"], 1),
            
            # Domaines thématiques
            ("8.1", ["enseignement", "école primaire", "école élémentaire", "école maternelle",
                     "groupe scolaire", "cantine scolaire", "périscolaire", "instituteur",
                     "carte scolaire", "rythmes scolaires"], 2),
            ("8.3", ["voirie", "route communale", "chaussée", "trottoir", "éclairage public",
                     "travaux de voirie", "réfection de voirie"], 2),
            ("8.4", ["aménagement du territoire", "plu ", "plui", "scot",
                     "plan local d'urbanisme"], 2),
            ("8.5", ["logement social", "habitat", "hlm", "politique de la ville",
                     "rénovation urbaine", "quartier prioritaire"], 2),
            ("8.6", ["emploi", "formation professionnelle", "insertion professionnelle",
                     "mission locale", "plie"], 2),
            ("8.7", ["transport en commun", "mobilité", "bus", "tramway", "piste cyclable",
                     "vélo", "stationnement"], 2),
            ("8.8", ["environnement", "eau potable", "assainissement", "déchet",
                     "collecte des déchets", "station d'épuration", "développement durable",
                     "transition écologique"], 2),
            ("8.9", ["culture", "musée", "bibliothèque", "médiathèque", "spectacle",
                     "festival", "conservatoire", "théâtre municipal"], 2),
            
            # Institutions
            ("5.1", ["élection du maire", "élection des adjoints", "installation du conseil"], 3),
            ("5.2", ["règlement intérieur", "fonctionnement de l'assemblée",
                     "égalité femmes", "égalité hommes", "rapport égalité", "parité",
                     "situation en matière d'égalité",
                     "éthique", "déontologie", "déontologue", "charte éthique"], 2),
            ("5.4", ["délégation de pouvoir", "délégation de fonction", "délégation au maire"], 2),
            ("5.6", ["indemnité des élus", "indemnité de fonction", "mandat local",
                     "frais de déplacement des élus"], 2),
            ("5.7", ["intercommunalité", "epci", "communauté d'agglomération",
                     "communauté de communes", "transfert de compétences",
                     "intérêt communautaire"], 2),
            
            # Commande publique
            ("1.1", ["marché public", "appel d'offres", "mapa", "commission d'appel d'offres",
                     "lot n°", "procédure adaptée", "consultation"], 2),
            ("1.2", ["délégation de service public", "dsp", "concession", "affermage"], 2),
            ("1.4", ["convention", "partenariat", "protocole d'accord"], 1),
            
            # Urbanisme
            ("2.1", ["plu", "plui", "document d'urbanisme", "modification du plu",
                     "révision du plu", "zone urbaine"], 3),
            ("2.2", ["permis de construire", "autorisation d'urbanisme", "certificat d'urbanisme",
                     "déclaration préalable"], 2),
            ("2.3", ["préemption", "droit de préemption", "dup"], 2),
            
            # Domaine et patrimoine
            ("3.1", ["acquisition immobilière", "achat de terrain", "acquisition foncière",
                     "acquisition d'un bien"], 2),
            ("3.2", ["cession", "vente immobilière", "aliénation", "déclassement"], 2),
            ("3.3", ["bail", "location", "loyer", "mise à disposition de locaux"], 1),
            
            # Fonction publique
            ("4.1", ["création de poste", "suppression de poste", "tableau des effectifs",
                     "personnel titulaire", "mutation"], 2),
            ("4.2", ["recrutement", "contrat de travail", "agent contractuel", "cdd", "cdi"], 2),
            ("4.5", ["régime indemnitaire", "rifseep", "prime", "indemnité horaire",
                     "nbi", "cia", "ifse"], 2),
            
            # Police
            ("6.1", ["police municipale", "arrêté municipal", "arrêté du maire",
                     "réglementation de la circulation", "stationnement interdit"], 2),
            ("6.4", ["ouverture le dimanche", "dérogation dominicale"], 2),
            
            # Autres
            ("9.4", ["vœu", "motion", "soutien à", "solidarité avec"], 3),
            ("9.1", ["divers", "questions diverses"], 1),
        ]
        
        scores = {}
        for code, keywords, base_weight in keyword_rules:
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    score += base_weight
                if kw in objet:
                    score += base_weight * objet_weight  # Poids triple si dans l'objet
            if score > 0:
                # Éviter les doublons - garder le meilleur score pour chaque code
                if code not in scores or score > scores[code]:
                    scores[code] = score
        
        if not scores:
            return None
        
        # Trouver le meilleur score
        best_code = max(scores, key=scores.get)
        best_score = scores[best_code]
        
        # Calculer la confiance (normalisée)
        max_possible = 15  # Score maximum attendu (base 2 * 3 matches + objet bonus)
        confidence = min(1.0, best_score / max_possible)
        
        # Récupérer le nom depuis la nomenclature
        nom = self.nomenclature.get_code_name(best_code)
        if not nom:
            best_code, nom = self.nomenclature.find_closest_code(best_code)
        
        return {
            "code": best_code,
            "nom": nom,
            "confidence": confidence
        }
    
    def _classify_with_llm(self, max_retries: int = 2) -> dict:
        """
        Classification via l'API HuggingFace Inference.
        Utilise un modèle d'instruction pour classifier le document.
        REQUIRES: HF_TOKEN environment variable set with valid HuggingFace token.
        """
        # Vérifier que le token est présent
        if not HF_TOKEN:
            print("[MatiereExtractor] ⚠️ HF_TOKEN non défini - LLM désactivé")
            print("[MatiereExtractor] Pour utiliser le LLM, définissez la variable d'environnement HF_TOKEN")
            print("[MatiereExtractor] Obtenir un token gratuit: https://huggingface.co/settings/tokens")
            return None
        
        # Préparer le contexte
        relevant_text = self._extract_relevant_text()
        objet = self._extract_objet()
        
        # Construire le prompt système et utilisateur (format chat)
        system_prompt = """Tu es un expert en classification de documents administratifs français selon la nomenclature ACTES.
Réponds UNIQUEMENT avec un objet JSON valide contenant le code et le nom de la catégorie."""

        # Nomenclature simplifiée mais complète pour les catégories principales
        nomenclature_simple = """NOMENCLATURE ACTES - Catégories principales:
1: COMMANDE PUBLIQUE (marchés publics, DSP, contrats)
2: URBANISME (PLU, permis, préemption)
3: DOMAINE ET PATRIMOINE (acquisitions, cessions, locations)
4: FONCTION PUBLIQUE (personnel, recrutement, régime indemnitaire)
5: INSTITUTIONS ET VIE POLITIQUE
  5.1: Élection de l'exécutif
  5.2: Fonctionnement des assemblées (règlement intérieur, éthique, égalité femmes-hommes)
  5.4: Délégations de pouvoirs
  5.6: Exercice des mandats locaux
  5.7: Intercommunalité
6: LIBERTÉS PUBLIQUES ET POUVOIRS DE POLICE
7: FINANCES LOCALES
  7.1.1: Budget primitif
  7.1.2: Autres documents budgétaires (DM, BS, CA, compte administratif)
  7.1.3: Débat d'orientation budgétaire (DOB)
  7.2: Fiscalité
  7.3: Emprunts
  7.5: Subventions
8: DOMAINES DE COMPÉTENCES PAR THÈMES
  8.1: Enseignement
  8.2: Aide sociale (petite enfance, CCAS, action sociale)
  8.3: Voirie
  8.7: Transports
  8.8: Environnement
  8.9: Culture
9: AUTRES DOMAINES"""

        user_prompt = f"""Classifie cette délibération de collectivité territoriale française:

OBJET: {objet}

EXTRAIT DU CONTENU:
{relevant_text[:1000]}

{nomenclature_simple}

INSTRUCTION: Analyse le document et identifie la catégorie ACTES la plus appropriée.
Réponds UNIQUEMENT avec ce format JSON exact:
{{"code": "X.Y.Z", "nom": "Nom de la catégorie"}}"""

        # Appel API avec retry (format OpenAI chat completions)
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 100,
                        "temperature": 0.1
                    },
                    timeout=60
                )
                
                if response.status_code == 503:
                    # Modèle en cours de chargement
                    wait_time = response.json().get("estimated_time", 20)
                    print(f"[MatiereExtractor] Modèle en chargement, attente {wait_time}s...")
                    time.sleep(min(wait_time, 30))
                    continue
                
                if response.status_code == 429:
                    # Rate limit
                    print("[MatiereExtractor] Rate limit atteint, attente 10s...")
                    time.sleep(10)
                    continue
                
                if response.status_code == 401:
                    print("[MatiereExtractor] ❌ Token HF_TOKEN invalide ou expiré")
                    return None
                
                if response.status_code != 200:
                    print(f"[MatiereExtractor] Erreur API: {response.status_code} - {response.text}")
                    continue
                
                result = response.json()
                
                # Parser la réponse (format OpenAI chat completions)
                if "choices" in result and len(result["choices"]) > 0:
                    text_response = result["choices"][0].get("message", {}).get("content", "")
                elif isinstance(result, dict):
                    text_response = result.get("generated_text", str(result))
                else:
                    text_response = str(result)
                
                return self._parse_llm_response(text_response)
                
            except requests.exceptions.Timeout:
                print(f"[MatiereExtractor] Timeout (tentative {attempt + 1}/{max_retries})")
                continue
            except Exception as e:
                print(f"[MatiereExtractor] Erreur: {e}")
                continue
        
        return None
    
    def _parse_llm_response(self, response: str) -> dict:
        """Parse la réponse du LLM pour extraire code et nom."""
        # Essayer de parser en JSON
        try:
            # Chercher un objet JSON dans la réponse
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                code = data.get("code", "")
                nom = data.get("nom", "")
                
                if code:
                    # Valider et corriger le code
                    if code not in self.nomenclature.nomenclature:
                        code, nom = self.nomenclature.find_closest_code(code)
                    elif not nom:
                        nom = self.nomenclature.get_code_name(code)
                    
                    return {
                        "code": code,
                        "nom": nom,
                        "confidence": 0.85
                    }
        except json.JSONDecodeError:
            pass
        
        # Fallback: chercher un pattern de code
        code_match = re.search(r'\b(\d+(?:\.\d+)*)\b', response)
        if code_match:
            code = code_match.group(1)
            code, nom = self.nomenclature.find_closest_code(code)
            return {
                "code": code,
                "nom": nom,
                "confidence": 0.6
            }
        
        return None


# Fonction utilitaire pour utilisation standalone
def classify_document(text: str, nomenclature_path: str = None, 
                      use_llm: bool = True) -> tuple:
    """
    Classifie un document selon la nomenclature ACTES.
    
    Args:
        text: Texte du document
        nomenclature_path: Chemin vers le fichier de nomenclature
        use_llm: Utiliser le LLM pour les cas difficiles
        
    Returns:
        Tuple (code, nom)
    """
    extractor = MatiereExtractor(text, nomenclature_path, use_llm)
    result = extractor.extract()
    return result.get("code", ""), result.get("nom", "")
