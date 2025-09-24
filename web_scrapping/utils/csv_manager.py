import os
import csv

def ensure_dir(path):
    """Crea directorio si no existe."""
    if not os.path.exists(path):
        os.makedirs(path)


def save_articles_csv(articles, label, portal, base_dir="data_scraped", filename="noticiasColombiaCheck.csv"):
    """
    Guarda noticias en un CSV unica (append mode).
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

        # si es la primera vez, escribimos encabezados
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

    print(f"Guardadas {len(articles)} noticias en {save_path}")
