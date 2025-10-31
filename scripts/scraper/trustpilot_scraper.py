import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup, FeatureNotFound
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------- Config scraping -------------------------- #

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MIN_DELAY = 1.5   # délai mini entre pages (secondes)
MAX_DELAY = 3.5   # délai maxi entre pages (secondes)

# --------------------------- Modèle de données ----------------------- #

@dataclass
class Review:
    titre_avis: Optional[str]
    contenu_texte: Optional[str]
    nombre_etoile: Optional[int]
    date_avis: Optional[str]
    pays: Optional[str]
    langue: Optional[str]
    reponse_entreprise: str              
    texte_entreprise: Optional[str]
    date_reponse_entreprise: Optional[str]
# --------------------------- Outils réseau --------------------------- #

def make_session() -> requests.Session:
    """Session Requests avec retries & backoff."""
    s = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.2,                 # 1.2s, 2.4s, 4.8s...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s

def polite_sleep():
    """Pause avec jitter pour éviter un pattern trop régulier."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

# --------------------------- Extraction HTML ------------------------- #

def extract_text(article: BeautifulSoup) -> Optional[str]:
    p = article.find("p", attrs={"data-service-review-text-typography": True}) or article.find("p")
    return p.get_text(" ", strip=True) if p else None

def extract_title(article: BeautifulSoup) -> Optional[str]:
    h2 = article.find("h2")
    return h2.get_text(strip=True) if h2 else None

def extract_date(article: BeautifulSoup) -> Optional[str]:
    t = article.find("time")
    return t.get("datetime") if t else None

def extract_country(article: BeautifulSoup) -> Optional[str]:
    ctry = article.find("span", {"data-consumer-country-typography": "true"})
    return ctry.get_text(strip=True) if ctry else None

def extract_rating(article: BeautifulSoup) -> Optional[int]:
    tag = article.select_one('[data-service-review-rating]')
    try:
        return int(tag.get("data-service-review-rating")) if tag else None
    except (TypeError, ValueError):
        return None

def extract_lang(article: BeautifulSoup) -> Optional[str]:
    content_div = article.select_one('[data-review-content="true"]')
    if not content_div:
        return None
    lang_attr = content_div.get("lang") or content_div.get("xml:lang")
    return lang_attr.split("-")[0].lower() if lang_attr else None

def company_response_flag(article) -> str:
    """Renvoie 'oui' si la carte de réponse existe, sinon 'non'."""
    reponse_div = article.select_one('div.CDS_Card_card__485220.CDS_Card_borderRadius-m__485220.styles_wrapper__WD_1K')
    return "oui" if reponse_div else "non"

def company_response_text(article) -> Optional[str]:
    """Renvoie le texte de la réponse de l'entreprise s'il existe, sinon None."""
    p = article.find("p", {"data-service-review-business-reply-text-typography": "true"})
    return p.get_text(strip=True) if p else None

def extract_reponse_date(article: BeautifulSoup) -> Optional[str]:
    reponse_div = article.select_one('div.CDS_Card_card__485220.CDS_Card_borderRadius-m__485220.styles_wrapper__WD_1K')
    if not reponse_div:
        return None
    t = reponse_div.find("time")
    return t.get("datetime") if t and t.has_attr("datetime") else None

# --------------------------- Scraper principal ----------------------- #

def scrape_trustpilot_reviews(base_url: str, output_file: str = "reviews.json", max_pages: int = 1000) -> None:
    
    session = make_session()

    total_start = time.perf_counter()
    pages_ok = 0
    all_reviews: list[dict] = []

    for page in range(1, max_pages + 1):
        try:
            if page == 1:
                resp = session.get(base_url, timeout=(5, 20))
                requested_url = base_url
            else:
                resp = session.get(base_url, params={"page": page}, timeout=(5, 20))
                requested_url = resp.request.url
        except requests.RequestException as e:
            print(f"❌ Réseau: page {page}: {e}", file=sys.stderr)
            polite_sleep()
            continue

        print(f"📥 Page {page}/{max_pages} -> {requested_url}")

        if resp.status_code == 429:
            ra = resp.headers.get("Retry-After")
            wait = int(ra) if ra and ra.isdigit() else 30
            print(f"⏳ 429 Too Many Requests. Pause {wait}s…")
            time.sleep(wait)
            try:
                if page == 1:
                    resp = session.get(base_url, timeout=(5, 20))
                else:
                    resp = session.get(base_url, params={"page": page}, timeout=(5, 20))
            except requests.RequestException as e:
                print(f"❌ Réseau (après 429): page {page}: {e}", file=sys.stderr)
                polite_sleep()
                continue

        if resp.status_code >= 400:
            print(f"❌ HTTP {resp.status_code} sur {requested_url}", file=sys.stderr)
            polite_sleep()
            continue

        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except FeatureNotFound:
            soup = BeautifulSoup(resp.text, "html.parser")

        # Cible les conteneurs d'avis 
        articles = soup.find_all('div', class_='styles_cardWrapper__g8amG styles_show__Z8n7u' )
        if not articles:
            articles = soup.find_all('div', attrs={"data-service-review-card-paper": True})

        if not articles:
            print("ℹ️ Aucun avis trouvé (fin de pagination / blocage).")
            break

        # Extraction
        new_count = 0
        for art in articles:
            try:
                titre = extract_title(art)
                texte = extract_text(art)
                date_avis = extract_date(art)
                pays = extract_country(art)
                rating = extract_rating(art)
                langue = extract_lang(art)
                reponse = company_response_flag(art)
                reponse_text = company_response_text(art)
                response_date = extract_reponse_date(art)

                review = Review(
                    titre_avis=titre,
                    contenu_texte=texte,
                    nombre_etoile=rating,
                    date_avis=date_avis,
                    pays=pays,
                    langue=langue,
                    reponse_entreprise=reponse,
                    texte_entreprise=reponse_text,
                    date_reponse_entreprise=response_date
                )
                all_reviews.append(asdict(review))
                new_count += 1
            except Exception as e:
                print(f"⚠️ Erreur d'extraction sur un avis : {e}", file=sys.stderr)
                continue

        pages_ok += 1
        print(f"✅ Page {page}: {new_count} avis collectés (total: {len(all_reviews)})")
        polite_sleep()

    # Écriture JSON "normal" 
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=4, ensure_ascii=False)

    final_count = new_count

    elapsed = time.perf_counter() - total_start
    minutes = int(elapsed // 60)   
    seconds = int(elapsed % 60)   

    print("────────────────────────────────────────")
    print(f"🏁 Terminé : {pages_ok}/{max_pages} pages traitées & {final_count} avis colléctés")
    print(f"🕒 Durée totale : {minutes} min {seconds} s")
    print(f"💾 Fichier JSON : {output_file}")


if __name__ == "__main__":
    company_url = "https://www.trustpilot.com/review/www.showroomprive.com?languages=all"
    scrape_trustpilot_reviews(company_url, output_file="reviews.json", max_pages=10)
