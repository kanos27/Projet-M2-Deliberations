"""
Orchestrateur principal pour l'extraction de métadonnées.
Combine tous les extracteurs modulaires pour produire un JSON complet.
Produit deux fichiers : output.json (complet) et output_legal.json (SCDL).
"""
import json
import os
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF

from .collectivite import CollectiviteExtractor, CommuneReference
from .deliberation import DeliberationExtractor
from .prefecture import PrefectureExtractor
from .seance import SeanceExtractor
from .vote import VoteExtractor
from .membres import MembresExtractor
from .paragraphes import ParagraphesExtractor


class DeliberationOrchestrator:
    """Orchestrateur pour l'extraction complète des métadonnées d'une délibération."""
    
    def __init__(self, communes_csv_path: str = None, debug: bool = False):
        """
        Initialise l'orchestrateur.
        
        Args:
            communes_csv_path: Chemin vers le CSV des communes (pour SIRET/PREF_ID)
            debug: Active le mode debug (sauvegarde du texte extrait)
        """
        self.debug = debug
        
        # Charger la référence des communes
        self.commune_ref = None
        if communes_csv_path:
            self.commune_ref = CommuneReference(communes_csv_path)
        else:
            # Essayer le chemin par défaut
            default_csv = Path(__file__).parent.parent / "communes_reference.csv"
            if default_csv.exists():
                self.commune_ref = CommuneReference(str(default_csv))
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF {pdf_path}: {e}")
        return text
    
    def process_pdf(self, pdf_path: str) -> dict:
        """
        Traite un PDF et extrait toutes les métadonnées.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Dictionnaire des métadonnées structurées
        """
        # Extraire le texte
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            return {"error": f"Impossible d'extraire le texte de {pdf_path}"}
        
        # Mode debug : sauvegarder le texte extrait
        if self.debug:
            debug_path = Path(pdf_path).with_suffix('.txt')
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"[DEBUG] Texte sauvegardé dans {debug_path}")
        
        # Construire le résultat
        result = {
            "_metadata": {
                "source_file": os.path.basename(pdf_path),
                "extraction_date": datetime.now().isoformat(),
                "version": "2.0.0"
            }
        }
        
        # Exécuter chaque extracteur
        # Collectivité (avec référence communes)
        collectivite_ext = CollectiviteExtractor(text, self.commune_ref)
        result["collectivite"] = collectivite_ext.extract()
        
        # Délibération
        delib_ext = DeliberationExtractor(text)
        result["deliberation"] = delib_ext.extract()
        
        # Préfecture (récupérer pref_id depuis collectivité)
        pref_ext = PrefectureExtractor(text)
        pref_data = pref_ext.extract()
        # Ajouter pref_id si disponible
        pref_id = collectivite_ext.get_pref_id()
        if pref_id:
            pref_data["id"] = pref_id
        result["prefecture"] = pref_data
        
        # Séance
        seance_ext = SeanceExtractor(text)
        result["seance"] = seance_ext.extract()
        
        # Vote
        vote_ext = VoteExtractor(text)
        result["vote"] = vote_ext.extract()
        
        # Membres
        membres_ext = MembresExtractor(text)
        membres_data = membres_ext.extract()
        result["membres_presents"] = membres_data.get("membres_presents", [])
        result["membres_absents"] = membres_data.get("membres_absents", [])
        
        # Paragraphes et contenus textuels
        para_ext = ParagraphesExtractor(text)
        para_data = para_ext.extract()
        result["considerants"] = para_data.get("considerants", {})
        result["commission_consultee"] = para_data.get("commission_consultee", {})
        result["decision"] = para_data.get("decision", "")
        result["paragraphes"] = para_data.get("paragraphes", {})
        
        return result
    
    def convert_to_scdl(self, full_data: dict) -> dict:
        """
        Convertit les données complètes au format SCDL légal.
        
        Args:
            full_data: Données extraites complètes
            
        Returns:
            Dictionnaire au format SCDL (template_metadata_info.txt)
        """
        # Extraire les données imbriquées
        collectivite = full_data.get("collectivite", {})
        deliberation = full_data.get("deliberation", {})
        prefecture = full_data.get("prefecture", {})
        vote = full_data.get("vote", {})
        
        # Construire le format SCDL
        scdl = {
            "COLL_NOM": collectivite.get("nom", ""),
            "COLL_SIRET": collectivite.get("siret", ""),
            "DELIB_ID": deliberation.get("id", "").replace("DCM", ""),
            "DELIB_DATE": deliberation.get("date", ""),
            "DELIB_MATIERE_CODE": deliberation.get("matiere", {}).get("code", ""),
            "DELIB_MATIERE_NOM": deliberation.get("matiere", {}).get("nom", ""),
            "DELIB_OBJET": deliberation.get("objet", ""),
            "BUDGET_ANNEE": "",
            "BUDGET_NOM": "",
            "PREF_ID": prefecture.get("id", ""),
            "PREF_DATE": prefecture.get("date_envoi", ""),
            "VOTE_EFFECTIF": vote.get("membres_en_exercice"),
            "VOTE_REEL": vote.get("votants"),
            "VOTE_POUR": vote.get("votes_pour"),
            "VOTE_CONTRE": vote.get("votes_contre"),
            "VOTE_ABSTENTION": vote.get("abstentions"),
            "DELIB_URL": deliberation.get("url_document", "")
        }
        
        return scdl
    
    def process_directory(self, pdf_dir: str, output_path: str = None) -> tuple:
        """
        Traite tous les PDFs d'un répertoire.
        Produit deux fichiers : output.json (complet) et output_legal.json (SCDL).
        
        Args:
            pdf_dir: Chemin vers le répertoire contenant les PDFs
            output_path: Chemin de sortie pour le JSON complet (optionnel)
            
        Returns:
            Tuple (résultats complets, résultats SCDL)
        """
        results_full = []
        results_scdl = []
        pdf_dir = Path(pdf_dir)
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"Traitement de {len(pdf_files)} fichier(s) PDF...")
        
        for pdf_path in pdf_files:
            print(f"  - {pdf_path.name}")
            # Extraction complète
            result_full = self.process_pdf(str(pdf_path))
            results_full.append(result_full)
            
            # Conversion SCDL
            result_scdl = self.convert_to_scdl(result_full)
            results_scdl.append(result_scdl)
        
        # Déterminer les chemins de sortie
        if output_path:
            output_full = Path(output_path)
            output_legal = output_full.parent / "output_legal.json"
        else:
            output_full = pdf_dir / "output.json"
            output_legal = pdf_dir / "output_legal.json"
        
        # Sauvegarder les fichiers
        with open(output_full, 'w', encoding='utf-8') as f:
            json.dump(results_full, f, ensure_ascii=False, indent=2)
        print(f"Collection complète sauvegardée dans {output_full}")
        
        with open(output_legal, 'w', encoding='utf-8') as f:
            json.dump(results_scdl, f, ensure_ascii=False, indent=2)
        print(f"Collection SCDL sauvegardée dans {output_legal}")
        
        return results_full, results_scdl
    
    def to_json(self, data: dict, indent: int = 2) -> str:
        """Convertit les données en JSON formaté."""
        return json.dumps(data, ensure_ascii=False, indent=indent)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extraction de métadonnées de délibérations PDF"
    )
    parser.add_argument(
        'input',
        help="Fichier PDF ou répertoire contenant des PDFs"
    )
    parser.add_argument(
        '-o', '--output',
        help="Fichier JSON de sortie"
    )
    parser.add_argument(
        '-c', '--communes',
        help="Fichier CSV de référence des communes"
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help="Mode debug (sauvegarde le texte extrait)"
    )
    
    args = parser.parse_args()
    
    # Créer l'orchestrateur
    orchestrator = DeliberationOrchestrator(
        communes_csv_path=args.communes,
        debug=args.debug
    )
    
    # Traiter l'entrée
    input_path = Path(args.input)
    
    if input_path.is_file():
        result_full = orchestrator.process_pdf(str(input_path))
        result_scdl = orchestrator.convert_to_scdl(result_full)
        
        if args.output:
            output_full = Path(args.output)
            output_legal = output_full.parent / f"{output_full.stem}_legal.json"
            
            with open(output_full, 'w', encoding='utf-8') as f:
                json.dump(result_full, f, ensure_ascii=False, indent=2)
            print(f"Collection complète sauvegardée dans {output_full}")
            
            with open(output_legal, 'w', encoding='utf-8') as f:
                json.dump(result_scdl, f, ensure_ascii=False, indent=2)
            print(f"Collection SCDL sauvegardée dans {output_legal}")
        else:
            print("=== Collection complète ===")
            print(orchestrator.to_json(result_full))
            print("\n=== Collection SCDL ===")
            print(orchestrator.to_json(result_scdl))
            
    elif input_path.is_dir():
        output = args.output or str(input_path / "output.json")
        orchestrator.process_directory(str(input_path), output)
    else:
        print(f"Erreur: {args.input} n'existe pas")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
