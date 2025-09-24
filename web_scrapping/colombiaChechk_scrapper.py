import time
from base_scraper import get_html_requests, parse_article
from utils.file_manager import save_articles
from utils.csv_manager import save_articles_csv


def scrape_colombiacheck(limit=75, max_pages=30, sleep_time=2):
    """
    Scraper para ColombiaCheck.
    Cambiando de paginacion a traves de la url.
    """
    BASE_URL = "https://colombiacheck.com/chequeos?page={}"
    articles = []
    seen_urls = set()
    page = 1

    while len(articles) < limit and page <= max_pages:
        url = BASE_URL.format(page)
        soup = get_html_requests(url, sleep_time=sleep_time)
        if not soup:
            break

        cheques = soup.select("div.Chequeo.Chequeo-fila")
        if not cheques:
            break

        for cheque in cheques:
            a_tag = cheque.select_one("a")
            if not a_tag:
                continue
            link = a_tag.get("href")
            if link and not link.startswith("http"):
                link = "https://colombiacheck.com" + link

            if link in seen_urls:
                continue
            seen_urls.add(link)

            # titulo y descripcion
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
        time.sleep(sleep_time)

    return articles


if __name__ == "__main__":
    noticias = scrape_colombiacheck(limit=75)
    save_articles(noticias, label="falso", portal="colombiaCheck")
    save_articles_csv(noticias, label="falso", portal="colombiaCheck")
    print(f"\nSe extrajeron {len(noticias)} noticias de ColombiaCheck.")
    # for i, n in enumerate(noticias, 1):
    #     print(f"\n{i}. {n['title']}\n   {n['description']}\n   {n['url']}")
