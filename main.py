# main.py
from config import BASE_URL, TARGET_DATES
from scraper_service import LaRochelleScraper
from utils import save_to_excel

def main():
    print("démarrage scraping")
    
    bot = LaRochelleScraper()
    all_data = []

    try:
        bot.open_url(BASE_URL)

        for period, date_text in TARGET_DATES.items():
            print(f"--- traitement de la période {period} ({date_text}) ---")
            
            year = date_text.split('-')[0]
            
            bot.open_year_folder(year)
            
            data = bot.scrape_date(period, date_text)
            all_data.extend(data)

    except Exception as e:
        print(f"erreur générale: {e}")
    
    finally:
        bot.close()
        
        save_to_excel(all_data)

if __name__ == "__main__":
    main()