"""
Configuration et constantes pour l'extraction de métadonnées des délibérations.
"""

# Mapping des mois français vers numéros
MOIS_FR = {
    'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
    'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
    'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
}

# Patterns regex pour l'extraction
PATTERNS = {
    # Dates
    'date_texte': r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
    'date_slash': r'(\d{1,2})[/](\d{1,2})[/](\d{4})',
    'date_iso': r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
    
    # Identifiants
    'delib_id': r'(?:DCM|DEL|DELIB)[\s-]?(\d{6}[_-]\d{2})',
    'pref_id_complet': r'ID\s*:\s*(\d{3}-\d+-\d+-[A-Z0-9_]+-[A-Z]+)',
    
    # Préfecture
    'pref_envoi': r'Envoyé en préfecture le\s+(\d{1,2})[/](\d{1,2})[/](\d{4})',
    'pref_reception': r'Reçu en préfecture le\s+(\d{1,2})[/](\d{1,2})[/](\d{4})',
    'pref_publication': r'Publié le\s+(\d{1,2})[/](\d{1,2})[/](\d{4})',
    
    # Collectivité
    'coll_nom': r"(?:Conseil\s+municipal|CONSEIL\s+MUNICIPAL)\s+(?:de\s+la\s+)?(?:Ville\s+(?:de|d')\s+)?([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s-]+?)(?:,|\s*convoqué)",
    
    # Séance
    'seance_date': r'[Ss]éance\s+du\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
    'seance_lieu': r"s'est\s+réuni[e]?\s+le\s+\d{1,2}\s+\w+\s+\d{4}\s+dans\s+(?:la\s+)?(.+?)(?:\.|$)",
    'convocation': r'convoqué\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
    
    # Président/Secrétaire/Rapporteur
    'president': r'[Ss]ous\s+la\s+présidence\s+de\s+(M\.|Mme|M)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)(?:,\s*([A-Za-zÀ-ÿ]+))?',
    'secretaire': r'[Ss]ecrétaire\s*:\s*(M\.|Mme|M)\s+([A-Za-zÀ-ÿ\-]+)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)',
    'rapporteur': r'[Rr]apporteur\s*:\s*(M\.|Mme|M)\s+([A-ZÀ-ÿ][A-ZÀ-ÿ\-]+)',
    
    # Vote - avec gestion des espaces insécables
    'vote_effectif': r'Membres\s+en\s+exercice[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_presents': r'Membres\s+présents[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_procurations': r'Membres\s+ayant\s+donné\s+procuration[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_votants': r'Votants[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_suffrages': r'Suffrages\s+exprimés[\s\xa0]*:[\s\xa0]*(\d+)?',
    'vote_pour': r'Votes?\s+pour[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_contre': r'Votes?\s+contre[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_abstention': r'Abstentions?[\s\xa0]*:[\s\xa0]*(\d+)',
    'vote_resultat': r"(ADOPTÉE?[ESs]*\s+À\s+L'UNANIMITÉ|ADOPTÉE?[ESs]*|REJETÉE?[ESs]*)",
    
    # Objet et décision
    'objet_titre': r'n°\s*\d+\s*\n+([A-ZÀ-ÿ][A-ZÀ-ÿ\s\'\-\d]+)\n',
    'commission': r'[Cc]ommission\s+n°\s*(\d+)\s*\(([^)]+)\)\s+réunie\s+le\s+(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
}
