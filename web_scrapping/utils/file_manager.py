import os

def ensure_dir(path):
    """Crea directorio si no existe."""
    if not os.path.exists(path):
        os.makedirs(path)


def save_articles(articles, label, portal, base_dir="data_scraped"):
    """
    Guarda cada noticia en un archivo .txt dentro de /dataset/<label>/.
    - articles: lista de dicts con keys: title, description, url
    - label: "verdad" o "falso"
    - portal: nombre del portal (ej: 'bbc')
    """
    save_path = os.path.join(base_dir, label)
    ensure_dir(save_path)

    for idx, article in enumerate(articles, 1):
        filename = f"{portal}_{idx:03d}.txt"
        filepath = os.path.join(save_path, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Fuente: {portal}\n")
            f.write(f"URL: {article.get('url','')}\n")
            f.write(f"Título: {article.get('title','')}\n\n")
            f.write(f"Descripción: {article.get('description','')}\n")

    print(f"Guardadas {len(articles)} noticias en {save_path}")
