import time
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_html_requests(url, headers=None, sleep_time=1):
    """
    Descarga el HTML de una pagina usando requests.
    Retorna BeautifulSoup o None si falla.
    """
    try:
        if headers is None:
            headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        time.sleep(sleep_time)
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[ERROR requests] {url} -> {e}")
        return None


def init_selenium_driver(headless=True):
    """
    Inicializa un driver de Selenium con opciones por defecto y sin logs molestos.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")  # nueva forma más estable
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--mute-audio")
    options.add_argument("--log-level=3")

    # Quitar logs de DevTools
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    service.log_path = "NUL"   # en Windows (o "/dev/null" en Linux/Mac)

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_html_selenium(url, sleep_time=3, headless=True):
    """
    Descarga el HTML usando Selenium.
    Retorna BeautifulSoup o None si falla.
    """
    try:
        driver = init_selenium_driver(headless=headless)
        driver.get(url)
        time.sleep(sleep_time)
        html = driver.page_source
        driver.quit()
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"[ERROR selenium] {url} -> {e}")
        return None


def scroll_page(driver, times=3, wait=2):
    """
    Scrollea la pagina hacia abajo 'times' veces con espera entre scrolls.
    """
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait)


def incremental_scroll(driver, wait=2, step=800):
    """
    Hace scroll incremental hacia abajo en pasos de `step` píxeles.
    """
    current_pos = driver.execute_script("return window.pageYOffset;")
    driver.execute_script(f"window.scrollTo(0, {current_pos + step});")
    time.sleep(wait)


def extract_links(soup, css_selector, limit=None):
    """
    Extrae enlaces desde un BeautifulSoup dado un selector CSS.
    Retorna lista de URLs absolutas.
    """
    if not soup:
        return []

    links = []
    for tag in soup.select(css_selector):
        href = tag.get("href")
        if href and href.startswith("http"):
            links.append(href)
    if limit:
        links = links[:limit]
    return links


def parse_article(soup, title_selector, body_selector):
    """
    Extrae titulo y cuerpo de un articulo segun selectores CSS.
    Retorna (titulo, texto) o (None, None) si falla.
    """
    if not soup:
        return None, None

    try:
        title = soup.select_one(title_selector)
        body = soup.select(body_selector)

        title_text = title.get_text(strip=True) if title else None
        body_text = " ".join([p.get_text(strip=True) for p in body]) if body else None

        return title_text, body_text
    except Exception as e:
        print(f"[ERROR parsing] {e}")
        return None, None
