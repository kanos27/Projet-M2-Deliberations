# utils.py
import re
import os
import pandas as pd
import requests
from datetime import datetime

def clean_title(raw_title):
    """nettoie le titre"""
    if not raw_title:
        return ""
    return re.sub(r'(?i)pdf\s*[\d,.]+\s*[KM]o$', '', raw_title).strip()

def download_pdf(url, folder="pdf", filename=None):
    """télécharge un PDF depuis une URL"""
    if not url:
        return None
    
    os.makedirs(folder, exist_ok=True)
    
    if not filename:
        filename = url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename += '.pdf'
    
    filepath = os.path.join(folder, filename)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f"erreur téléchargement {filename}: {e}")
        return None

def save_to_excel(data_list, filename="resultats_larochelle.xlsx"):
    """sauvegarde les données dans un fichier Excel (pour l'instant)"""
    if not data_list:
        return

    df = pd.DataFrame(data_list)
    try:
        df.to_excel(filename, index=False)
        print(f"fichier sauvegardé sous {filename}")
    except Exception as e:
        print(f"erreur lors de la sauvegarde Excel: {e}")
