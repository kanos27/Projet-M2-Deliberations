"""
Script de test pour valider l'extraction des paragraphes.
Teste le ParagraphesExtractor sur les 5 documents exemples.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extractors.paragraphes import ParagraphesExtractor


def load_template(filename: str) -> str:
    """Charge un fichier template."""
    template_path = Path(__file__).parent / "template" / filename
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def test_document(name: str, text: str) -> dict:
    """Teste l'extraction sur un document."""
    print(f"\n{'='*80}")
    print(f"Test: {name}")
    print(f"{'='*80}")
    
    extractor = ParagraphesExtractor(text)
    result = extractor.extract()
    
    print(f"\n--- Introduction ({len(result.get('introduction', ''))} chars) ---")
    intro = result.get('introduction', '')[:500]
    print(intro + "..." if len(result.get('introduction', '')) > 500 else intro)
    
    print(f"\n--- Références juridiques ({len(result.get('references_juridiques', []))} refs) ---")
    for i, ref in enumerate(result.get('references_juridiques', [])[:5]):
        print(f"  {i+1}. {ref[:100]}...")
    
    print(f"\n--- Considérants ({len(result.get('considerants', []))} items) ---")
    for i, cons in enumerate(result.get('considerants', [])[:3]):
        print(f"  {i+1}. {cons[:100]}...")
    
    corps = result.get('corps_principal', {})
    print(f"\n--- Corps principal ---")
    print(f"  Sections numérotées: {len(corps.get('sections_numerotees', []))}")
    for section in corps.get('sections_numerotees', [])[:3]:
        print(f"    N°{section['numero']}: {section['titre'][:80]}...")
    
    print(f"  Points clés: {len(corps.get('points_cles', []))}")
    for i, point in enumerate(corps.get('points_cles', [])[:5]):
        print(f"    - {point[:80]}...")
    
    print(f"  Contenu libre: {len(corps.get('contenu_libre', ''))} chars")
    
    proposition = result.get('proposition', {})
    print(f"\n--- Proposition ---")
    print(f"  Texte complet: {len(proposition.get('texte_complet', ''))} chars")
    print(f"  Points: {len(proposition.get('points', []))}")
    for point in proposition.get('points', [])[:3]:
        print(f"    - {point[:80]}...")
    
    commission = result.get('commission_consultee', {})
    print(f"\n--- Commission consultée ---")
    print(f"  Numéro: {commission.get('numero')}")
    print(f"  Nom: {commission.get('nom')}")
    print(f"  Date réunion: {commission.get('date_reunion')}")
    print(f"  Avis: {commission.get('avis')}")
    
    return result


def main():
    """Teste l'extraction sur tous les documents exemples."""
    templates = [
        ("02_rapport_egalite_femmes_hommes_compil.txt", "Rapport Égalité F/H"),
        ("04_decision_modificative_2024-1.txt", "Décision Modificative"),
        ("dcm251117_01.txt", "Service Public Petite Enfance"),
        ("dcm251215_01_dob_2026.txt", "Débat Orientations Budgétaires"),
        ("dcm251215_03_comite_ethique_bilan_global_activite_2022_2025.txt", "Comité Éthique"),
    ]
    
    results = {}
    
    for filename, description in templates:
        try:
            text = load_template(filename)
            result = test_document(description, text)
            results[filename] = {
                "description": description,
                "extraction": result,
                "success": True
            }
        except Exception as e:
            print(f"\nERREUR pour {filename}: {e}")
            results[filename] = {
                "description": description,
                "error": str(e),
                "success": False
            }
    
    # Sauvegarder les résultats
    output_path = Path(__file__).parent / "template" / "test_paragraphes_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n\nRésultats sauvegardés dans: {output_path}")
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ")
    print("="*80)
    success_count = sum(1 for r in results.values() if r.get("success"))
    print(f"Documents traités avec succès: {success_count}/{len(templates)}")
    
    for filename, result in results.items():
        status = "✓" if result.get("success") else "✗"
        desc = result.get("description", filename)
        if result.get("success"):
            ext = result.get("extraction", {})
            intro_len = len(ext.get("introduction", ""))
            refs_count = len(ext.get("references_juridiques", []))
            cons_count = len(ext.get("considerants", []))
            sections_count = len(ext.get("corps_principal", {}).get("sections_numerotees", []))
            points_count = len(ext.get("corps_principal", {}).get("points_cles", []))
            prop_len = len(ext.get("proposition", {}).get("texte_complet", ""))
            print(f"  {status} {desc}: intro={intro_len}c, refs={refs_count}, cons={cons_count}, sections={sections_count}, points={points_count}, prop={prop_len}c")
        else:
            print(f"  {status} {desc}: {result.get('error')}")


if __name__ == "__main__":
    main()
