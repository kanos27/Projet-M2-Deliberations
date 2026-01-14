import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

BASE_URL = "https://affichagelegal.larochelle.fr/conseil-municipal/deliberations-adoptees"
API_URL = f"{BASE_URL}?p_p_id=10068_WAR_fu&p_p_lifecycle=0&p_p_state=exclusive&p_p_mode=view&_10068_WAR_fu_currentURL=/conseil-municipal/deliberations-adoptees"


class LaRochelleScraper(BaseScraper):
    def __init__(self):
        super().__init__("larochelle-deliberations")

    def _fetch_page(self, from_idx: int, to_idx: int) -> str:
        url = f"{API_URL}&_10068_WAR_fu_from={from_idx}&_10068_WAR_fu_to={to_idx}"
        print(f"Fetching: from={from_idx} to={to_idx}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _extract_links(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", class_="link-pdf"):
            href = a.get("href")
            if href and href.endswith(".pdf"):
                links.append({
                    "url": href,
                    "title": a.get("title", ""),
                    "filename": href.split("/")[-1]
                })
        return links

    def fetch_pdf_links(self, num_documents: int, page_size: int) -> list[dict]:
        all_pdfs = []
        from_idx = 0
        while from_idx < num_documents:
            to_idx = min(from_idx + page_size, num_documents)
            try:
                html = self._fetch_page(from_idx, to_idx)
                pdfs = self._extract_links(html)
                all_pdfs.extend(pdfs)
                print(f"  Found {len(pdfs)} PDFs")
            except Exception as e:
                print(f"Error: {e}")
                break
            from_idx = to_idx
        return all_pdfs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num", type=int, default=10)
    parser.add_argument("--page-size", type=int, default=10)
    args = parser.parse_args()

    scraper = LaRochelleScraper()
    scraper.run(args.num, args.page_size)
