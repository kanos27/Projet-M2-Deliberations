# scraper_service.py
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from config import TIMEOUT, HEADLESS_MODE
from utils import clean_title, download_pdf

class LaRochelleScraper:
    def __init__(self):
        self.driver = self._setup_driver()
        self.opened_years = set()

    def _setup_driver(self):
        options = Options()
        if HEADLESS_MODE:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options)

    def close(self):
        print("🏁 Fermeture du navigateur...")
        self.driver.quit()

    def open_url(self, url):
        print(f"connexion à {url}...")
        self.driver.get(url)
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "interior-article-moreContent-docs"))
        )
    
    def open_year_folder(self, year):
        if year in self.opened_years: return

        try:
            xpath = f"//ins[contains(@class, 'interior-article-moreContent-docs-title') and contains(text(), '{year}')]"
            el = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, xpath)))
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            time.sleep(0.5)
            
            try:
                el.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", el)
            
            time.sleep(1.5)
            self.opened_years.add(year)
        except Exception as e:
            print(f"   ⚠️ Erreur dossier {year}: {e}")

    def scrape_date(self, period_name, date_text, limit=10):
        results = []
        
        try:
            xpath = f"//ins[contains(@class, 'interior-article-moreContent-docs-title') and contains(text(), '{date_text}')]"
            date_elems = self.driver.find_elements(By.XPATH, xpath)
            
            if not date_elems: 
                print("date non trouvée")
                return []
            
            date_el = date_elems[0]
            parent = date_el.find_element(By.XPATH, "./ancestor::li[1]")
            uls = parent.find_elements(By.TAG_NAME, "ul")
            
            if not uls or not uls[0].is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_el)
                try: date_el.click()
                except: self.driver.execute_script("arguments[0].click();", date_el)
                time.sleep(1)
                uls = parent.find_elements(By.TAG_NAME, "ul")

            if not uls: return []

            links = uls[0].find_elements(By.CSS_SELECTOR, 'a[href*=".pdf"]')
            
            if len(links) > 1:
                txt = links[0].get_attribute("innerText").strip()
                if re.match(r'^\d+', txt) and int(re.match(r'^\d+', txt).group()) > 1:
                    links.reverse()

            count = 0
            for link in links:
                if count >= limit: break
                try:
                    raw_title = link.get_attribute("innerText").strip()
                    href = link.get_attribute('href')
                    
                    if href and not href.startswith('http'):
                        href = f"https://affichagelegal.larochelle.fr/{href.lstrip('/')}"

                    # Télécharger le PDF
                    pdf_filename = f"{period_name}_{count+1:03d}.pdf"
                    local_path = download_pdf(href, folder="pdf", filename=pdf_filename)

                    results.append({
                        'numero_ordre': count + 1,
                        'titre': clean_title(raw_title), 
                        'date_conseil': date_text,
                        'lien': href,
                        'fichier_local': local_path,
                        'periode': period_name,
                        'date_extraction': datetime.now().strftime('%Y-%m-%d')
                    })
                    count += 1
                    print(f"      ✓ {clean_title(raw_title)[:50]}...")
                except: continue
                
        except Exception as e:
            print(f"erreur scraping date {date_text}: {e}")
            
        return results