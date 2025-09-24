import os
import csv
import time
import random
import logging
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def ensure_dir(path: str) -> None:
    """Crea directorio si no existe."""
    if not os.path.exists(path):
        os.makedirs(path)

def save_articles(articles: List[Dict[str, str]], label: str, portal: str,
                  base_dir: str = "data_scraped") -> None:
    """
    Guarda cada noticia en un archivo .txt dentro de /<base_dir>/<label>/.
    - articles: lista de dicts con keys: title, description, url
    - label: "verdad" o "falso"
    - portal: nombre del portal (ej: 'bbc')
    """
    save_path = os.path.join(base_dir, label)
    ensure_dir(save_path)

    # Usamos zfill del enumerate para nombres estables
    for idx, article in enumerate(articles, 1):
        filename = f"{portal}_{str(idx).zfill(3)}.txt"
        filepath = os.path.join(save_path, filename)
        # Escritura segura con reemplazo de None por cadenas vacías
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Fuente: {portal}\n")
            f.write(f"URL: {article.get('url','')}\n")
            f.write(f"Título: {article.get('title','')}\n\n")
            f.write(f"Descripción: {article.get('description','')}\n")

    logging.info("Guardadas %d noticias en %s", len(articles), save_path)

def save_articles_csv(articles: List[Dict[str, str]], label: str, portal: str,
                      base_dir: str = "data_scraped",
                      filename: str = "noticiasColombiaCheck.csv") -> None:
    """
    Guarda noticias en un CSV único (append mode).
    - articles: lista de dicts con keys: title, description, url
    - label: "Verdad" o "Falso"
    - portal: nombre del portal (ej: 'bbc')
    - veracidad: 1 si 'verdad', 0 si 'falso'
    """
    save_path = os.path.join(base_dir, filename)
    ensure_dir(base_dir)

    veracidad = 1 if label.lower() == "verdad" else 0
    file_exists = os.path.isfile(save_path)

    with open(save_path, "a", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["fuente", "titulo", "descripcion", "url", "veracidad"])

        for article in articles:
            writer.writerow([
                portal,
                article.get("title", ""),
                article.get("description", ""),
                article.get("url", ""),
                veracidad
            ])

    logging.info("Guardadas %d noticias en %s", len(articles), save_path)

_DEFAULT_HEADERS = [
    # Rotación simple de user-agents comunes
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"},
]

def get_html_requests(url: str, *, sleep_time: float = 1.0,
                      timeout: int = 15, max_retries: int = 3) -> Optional[BeautifulSoup]:
    """
    Descarga una página HTML usando requests con pequeños retries y devuelve BeautifulSoup.
    Devuelve None si falla.
    """
    for attempt in range(1, max_retries + 1):
        try:
            headers = random.choice(_DEFAULT_HEADERS)
            resp = requests.get(url, headers=headers, timeout=timeout)
            if 200 <= resp.status_code < 300:
                # Respetar un pequeño sleep (anti-baneo)
                if sleep_time:
                    time.sleep(sleep_time)
                return BeautifulSoup(resp.text, "html.parser")
            else:
                logging.warning("Status %s en %s (intento %d/%d)",
                                resp.status_code, url, attempt, max_retries)
        except requests.RequestException as e:
            logging.warning("Error de red en %s (intento %d/%d): %s",
                            url, attempt, max_retries, e)
        # Backoff lineal mínimo
        time.sleep(0.5 * attempt)

    logging.error("No se pudo obtener HTML de %s después de %d intentos", url, max_retries)
    return None

def parse_article(container, title_selector: str, body_selector: str) -> Tuple[str, str]:
    """
    Extrae (title, description) desde un contenedor BeautifulSoup con selectores CSS.
    Si no encuentra, devuelve cadenas limpias.
    """
    title_el = container.select_one(title_selector)
    body_el = container.select_one(body_selector)

    # Limpieza defensiva
    title = (title_el.get_text(strip=True) if title_el else "") or ""
    description = (body_el.get_text(strip=True) if body_el else "") or ""

    return title, description

def scrape_colombiacheck(limit: int = 75, max_pages: int = 30, sleep_time: float = 2) -> List[Dict[str, str]]:
    """
    Scraper para ColombiaCheck.
    Paginación vía query param page.
    Retorna: lista de dicts con keys: title, description, url
    """
    BASE_URL = "https://colombiacheck.com/chequeos?page={}"
    articles: List[Dict[str, str]] = []
    seen_urls = set()
    page = 1

    while len(articles) < limit and page <= max_pages:
        url = BASE_URL.format(page)
        soup = get_html_requests(url, sleep_time=sleep_time)
        if not soup:
            break

        cheques = soup.select("div.Chequeo.Chequeo-fila")
        if not cheques:
            # Si el layout cambia, intentamos otro selector fallback mínimo
            cheques = soup.select("div.view-content .Chequeo")
            if not cheques:
                logging.info("No se encontraron elementos de chequeo en la página %s", page)
                break

        for cheque in cheques:
            a_tag = cheque.select_one("a")
            if not a_tag:
                continue

            link = a_tag.get("href") or ""
            if link and not link.startswith("http"):
                link = "https://colombiacheck.com" + link

            if not link or link in seen_urls:
                continue
            seen_urls.add(link)

            title_selector = "h3.Chequeo-texto-titulo"
            body_selector = "p.Chequeo-texto-parrafo"
            title, description = parse_article(cheque, title_selector, body_selector)

            articles.append({
                "title": title,
                "description": description,
                "url": link
            })

            if len(articles) >= limit:
                break

        page += 1
        # Respetar politicas de scraping
        time.sleep(sleep_time)

    return articles

if __name__ == "__main__":
    noticias = scrape_colombiacheck(limit=75)
    save_articles(noticias, label="falso", portal="colombiaCheck")
    save_articles_csv(noticias, label="falso", portal="colombiaCheck")
    print(f"\nSe extrajeron {len(noticias)} noticias de ColombiaCheck.")
