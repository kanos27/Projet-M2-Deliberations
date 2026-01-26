import pymupdf
import re
import json
import csv
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher


class CommuneReference:
    """Classe pour gérer la référence des communes"""
    
    def __init__(self, csv_path=None):
        self.communes = {}
        if csv_path is None:
            csv_path = Path(__file__).parent / "communes_reference.csv"
        self.load_communes(csv_path)
    
    def load_communes(self, csv_path):
        """Charge les données de référence depuis le CSV"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nom = row['COLL_NOM'].strip()
                    self.communes[nom.lower()] = {
                        'COLL_SIRET': row['COLL_SIRET'].strip(),
                        'PREF_ID': row['PREF_ID'].strip()
                    }
        except FileNotFoundError:
            print(f"Avertissement: Fichier de référence {csv_path} non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement des communes: {e}")
    
    def similarity(self, a, b):
        """Calcule la similarité entre deux chaînes (0 à 1)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_commune(self, nom_recherche, seuil=0.8):
        """Trouve une commune avec correspondance flexible
        
        Args:
            nom_recherche: Nom de la commune à rechercher
            seuil: Seuil de similarité minimum (0 à 1)
        
        Returns:
            Dictionnaire avec COLL_SIRET et PREF_ID, ou None
        """
        if not nom_recherche:
            return None
        
        nom_recherche_clean = nom_recherche.lower().strip()
        
        # Correspondance exacte
        if nom_recherche_clean in self.communes:
            return self.communes[nom_recherche_clean]
        
        # Correspondance floue
        best_match = None
        best_score = 0
        
        for nom_ref in self.communes.keys():
            score = self.similarity(nom_recherche_clean, nom_ref)
            if score > best_score and score >= seuil:
                best_score = score
                best_match = nom_ref
        
        if best_match:
            return self.communes[best_match]
        
        return None


class DeliberationMetadataExtractor:
    """Extracteur de métadonnées pour les délibérations au format SCDL"""
    
    def __init__(self, pdf_path, save_text=False, commune_ref=None):
        self.pdf_path = Path(pdf_path)
        self.text = ""
        self.metadata = {}
        self.save_text = save_text
        self.commune_ref = commune_ref
        
    def extract_text_from_pdf(self):
        """Extrait le texte du PDF avec PyMuPDF"""
        try:
            doc = pymupdf.open(self.pdf_path)
            self.text = ""
            for page in doc:
                self.text += page.get_text()
            doc.close()
            return self.text
        except Exception as e:
            print(f"Erreur lors de l'extraction du texte: {e}")
            return None
    
    def extract_delib_id(self):
        """Extrait l'identifiant de la délibération"""
        # Cherche des patterns comme DCM251215_01, DEL-2025-01, etc.
        patterns = [
            r'(?:DCM|DEL|DELIB)[\s-]?(\d{6}[_-]\d{2})',  # DCM251215_01
            r'(?:Délibération|DELIBERATION)\s+(?:n°|N°|numéro)?\s*[:.]?\s*([A-Z0-9-_]+)',
            r'(?:N°|n°)\s*([A-Z0-9-_/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                delib_id = match.group(1) if match.lastindex else match.group(0)
                return delib_id.strip()
        
        # Fallback: utiliser le nom du fichier
        return self.pdf_path.stem
    
    def extract_delib_date(self):
        """Extrait la date de la délibération"""
        # Patterns pour différents formats de date
        patterns = [
            # Format: 15 décembre 2025, 15 Décembre 2025
            r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            # Format: 15/12/2025, 15-12-2025
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # Format: 2025-12-15
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        ]
        
        mois_fr = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                if i == 0:  # Format texte avec mois en lettres
                    day = match.group(1).zfill(2)
                    month = mois_fr.get(match.group(2).lower(), '01')
                    year = match.group(3)
                    return f"{year}-{month}-{day}"
                elif i == 1:  # Format JJ/MM/AAAA
                    day = match.group(1).zfill(2)
                    month = match.group(2).zfill(2)
                    year = match.group(3)
                    return f"{year}-{month}-{day}"
                elif i == 2:  # Format AAAA-MM-JJ
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    day = match.group(3).zfill(2)
                    return f"{year}-{month}-{day}"
        
        return None
    
    def extract_objet(self):
        """Extrait l'objet de la délibération"""
        patterns = [
            r'(?:Objet|OBJET)\s*[:.-]\s*(.+?)(?:\n\n|\r\n\r\n|Vu|VU|Considérant)',
            r'(?:Intitulé|INTITULE)\s*[:.-]\s*(.+?)(?:\n\n|\r\n\r\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.DOTALL | re.IGNORECASE)
            if match:
                objet = match.group(1).strip()
                # Nettoie le texte
                objet = re.sub(r'\s+', ' ', objet)
                return objet[:500]  # Limite à 500 caractères
        
        return None
    
    def extract_pref_date(self):
        """Extrait la date de réception en préfecture"""
        pattern = r'Reçu en préfecture le\s+(\d{1,2})[/\s](\d{1,2})[/\s](\d{4})'
        match = re.search(pattern, self.text)
        
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{year}-{month}-{day}"
        
        return None
    
    def extract_vote_info(self):
        """Extrait les informations de vote"""
        vote_info = {
            'effectif': None,
            'reel': None,
            'pour': None,
            'contre': None,
            'abstention': None
        }
        
        # Recherche de la section de vote
        # Note: \s+ gère à la fois les espaces normaux et insécables (\xa0)
        patterns = {
            'effectif': r'Membres\s+en\s+exercice[\s\xa0]*:[\s\xa0]*(\d+)',
            'presents': r'Membres\s+présents[\s\xa0]*:[\s\xa0]*(\d+)',
            'procuration': r'Membres\s+ayant\s+donné\s+procuration[\s\xa0]*:[\s\xa0]*(\d+)',
            'votants': r'Votants[\s\xa0]*:[\s\xa0]*(\d+)',
            'pour': r'Votes?\s+pour[\s\xa0]*:[\s\xa0]*(\d+)',
            'contre': r'Votes?\s+contre[\s\xa0]*:[\s\xa0]*(\d+)',
            'abstention': r'Abstentions?[\s\xa0]*:[\s\xa0]*(\d+)',
        }
        
        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                results[key] = int(match.group(1))
        
        # Remplir le dictionnaire
        if 'effectif' in results:
            vote_info['effectif'] = results['effectif']
        
        # VOTE_REEL = votants (ou présents + procurations)
        if 'votants' in results:
            vote_info['reel'] = results['votants']
        elif 'presents' in results and 'procuration' in results:
            vote_info['reel'] = results['presents'] + results['procuration']
        elif 'presents' in results:
            vote_info['reel'] = results['presents']
        
        if 'pour' in results:
            vote_info['pour'] = results['pour']
        
        # Pour contre et abstention, on accepte 0 comme valeur valide
        if 'contre' in results:
            vote_info['contre'] = results['contre']
        
        if 'abstention' in results:
            vote_info['abstention'] = results['abstention']
        
        return vote_info
    
    def extract_coll_nom(self):
        """Extrait le nom de la collectivité"""
        patterns = [
            r'(?:Commune|COMMUNE|Ville|VILLE|Conseil municipal|CONSEIL MUNICIPAL)\s+(?:de|DE|d\'|D\')\s+([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s-]+)',
            r'(Mairie|MAIRIE)\s+(?:de|DE)\s+([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                # Prend le dernier groupe capturé
                nom = match.group(match.lastindex)
                return nom.strip()
        
        return None
    
    def generate_metadata_dict(self):
        """Génère un dictionnaire de métadonnées"""
        if not self.text:
            self.extract_text_from_pdf()
        
        # Extraire les informations de vote
        vote_info = self.extract_vote_info()
        
        # Extraire le nom de la commune
        coll_nom = self.extract_coll_nom() or ''
        
        # Chercher les infos complémentaires dans la référence
        coll_siret = ''
        pref_id = ''
        if self.commune_ref and coll_nom:
            commune_data = self.commune_ref.find_commune(coll_nom)
            if commune_data:
                coll_siret = commune_data['COLL_SIRET']
                pref_id = commune_data['PREF_ID']
        
        self.metadata = {
            'COLL_NOM': coll_nom,
            'COLL_SIRET': coll_siret,
            'DELIB_ID': self.extract_delib_id() or '',
            'DELIB_DATE': self.extract_delib_date() or '',
            'DELIB_MATIERE_CODE': '',  # À remplir manuellement
            'DELIB_MATIERE_NOM': '',  # À remplir manuellement
            'DELIB_OBJET': self.extract_objet() or '',
            'BUDGET_ANNEE': '',
            'BUDGET_NOM': '',
            'PREF_ID': pref_id,
            'PREF_DATE': self.extract_pref_date() or '',
            'VOTE_EFFECTIF': vote_info['effectif'] if vote_info['effectif'] is not None else '',
            'VOTE_REEL': vote_info['reel'] if vote_info['reel'] is not None else '',
            'VOTE_POUR': vote_info['pour'] if vote_info['pour'] is not None else '',
            'VOTE_CONTRE': vote_info['contre'] if vote_info['contre'] is not None else '',
            'VOTE_ABSTENTION': vote_info['abstention'] if vote_info['abstention'] is not None else '',
            'DELIB_URL': '',
        }
        
        return self.metadata
    
    def export_to_json(self, output_path):
        """Exporte les métadonnées vers un fichier JSON"""
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.metadata, jsonfile, ensure_ascii=False, indent=2)
        print(f"Métadonnées exportées vers {output_path}")
    
    def save_extracted_text(self, output_path):
        """Sauvegarde le texte extrait dans un fichier texte (pour debug)"""
        with open(output_path, 'w', encoding='utf-8') as txtfile:
            txtfile.write(self.text)
        print(f"Texte extrait sauvegardé vers {output_path}")
    
    def print_metadata(self):
        """Affiche les métadonnées extraites"""
        print("\n" + "="*60)
        print("MÉTADONNÉES EXTRAITES")
        print("="*60)
        for key, value in self.metadata.items():
            status = "✓" if value else "✗"
            print(f"{status} {key}: {value if value else '[À COMPLÉTER]'}")
        print("="*60 + "\n")


def process_all_pdfs(pdf_folder_path, output_folder_path=None, save_text=False, communes_csv=None):
    """Traite tous les fichiers PDF dans un dossier
    
    Args:
        pdf_folder_path: Chemin vers le dossier contenant les PDFs
        output_folder_path: Chemin vers le dossier de sortie (optionnel)
        save_text: Si True, sauvegarde le texte extrait en fichier .txt (pour debug)
        communes_csv: Chemin vers le CSV de référence des communes (optionnel)
    """
    pdf_folder = Path(pdf_folder_path)
    
    if not pdf_folder.exists():
        print(f"Erreur: Le dossier {pdf_folder} n'existe pas")
        return []
    
    # Charger la référence des communes
    commune_ref = CommuneReference(communes_csv)
    
    # Créer le dossier de sortie s'il n'existe pas
    if output_folder_path is None:
        output_folder = pdf_folder.parent / "metadata_output"
    else:
        output_folder = Path(output_folder_path)
    
    output_folder.mkdir(exist_ok=True)
    
    # Créer un sous-dossier pour les textes extraits si nécessaire
    if save_text:
        text_folder = output_folder / "extracted_texts"
        text_folder.mkdir(exist_ok=True)
        print(f"📝 Mode debug: Les textes extraits seront sauvegardés dans {text_folder}\n")
    
    # Trouver tous les fichiers PDF
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans {pdf_folder}")
        return []
    
    print(f"\n{'='*60}")
    print(f"Traitement de {len(pdf_files)} fichier(s) PDF")
    print(f"{'='*60}\n")
    
    results = []
    
    for pdf_file in pdf_files:
        print(f"\n{'─'*60}")
        print(f"Traitement de: {pdf_file.name}")
        print(f"{'─'*60}")
        
        try:
            # Créer l'extracteur avec la référence des communes
            extractor = DeliberationMetadataExtractor(pdf_file, save_text=save_text, commune_ref=commune_ref)
            
            # Extraire le texte
            text = extractor.extract_text_from_pdf()
            
            if text:
                print(f"✓ Texte extrait: {len(text)} caractères")
                
                # Sauvegarder le texte extrait si demandé (mode debug)
                if save_text:
                    output_txt = text_folder / f"{pdf_file.stem}_extracted.txt"
                    extractor.save_extracted_text(output_txt)
                
                # Générer les métadonnées
                metadata = extractor.generate_metadata_dict()
                
                # Nom du fichier JSON de sortie
                output_json = output_folder / f"{pdf_file.stem}_metadata.json"
                
                # Exporter vers JSON
                extractor.export_to_json(output_json)
                
                # Afficher les métadonnées
                extractor.print_metadata()
                
                results.append({
                    'pdf_file': pdf_file.name,
                    'output_json': output_json,
                    'success': True,
                    'metadata': metadata
                })
            else:
                print(f"✗ Erreur: Impossible d'extraire le texte")
                results.append({
                    'pdf_file': pdf_file.name,
                    'success': False,
                    'error': 'Extraction de texte échouée'
                })
        
        except Exception as e:
            print(f"✗ Erreur lors du traitement: {e}")
            results.append({
                'pdf_file': pdf_file.name,
                'success': False,
                'error': str(e)
            })
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ DU TRAITEMENT")
    print(f"{'='*60}")
    success_count = sum(1 for r in results if r['success'])
    print(f"✓ Fichiers traités avec succès: {success_count}/{len(results)}")
    print(f"✗ Fichiers en erreur: {len(results) - success_count}/{len(results)}")
    print(f"📁 Dossier de sortie: {output_folder}")
    print(f"{'='*60}\n")
    
    return results


def main():
    """Fonction principale pour tester l'extraction"""
    # Chemin vers le dossier PDF
    pdf_folder = Path(__file__).parent.parent / "pdf"
    output_folder = Path(__file__).parent.parent / "metadata_output"
    
    # Mode debug: mettre save_text=True pour sauvegarder les textes extraits
    # Utile pendant le développement pour analyser le contenu des PDFs
    DEBUG_MODE = True  # Mettre à False en production
    
    # Traiter tous les PDFs
    results = process_all_pdfs(pdf_folder, output_folder, save_text=DEBUG_MODE)
    
    return results


if __name__ == "__main__":
    main()
