
import json
import html
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ORIGEN = Path("estat_consells.json")
SORTIDA = Path("previsualitzacio_consells.html")

def main():
    dades = json.loads(ORIGEN.read_text(encoding="utf-8"))
    fonts = dades.get("fonts", {})

    parts = [
        '<!doctype html><html lang="ca">',
        '<head><meta charset="utf-8">',
        '<title>Previsualització dels consells</title></head>',
        '<body><h1>Documents dels consells comarcals</h1>',
        '<p>PROVA: documents detectats, no ofertes vigents verificades.</p>'
    ]

    for nom, documents in fonts.items():
        parts.append(f"<h2>{html.escape(nom)}</h2>")
        parts.append(f"<p>{len(documents)} documents detectats</p>")

        for document in documents:
            titol = html.escape(document.get("titol_document", "Sense títol"))
            url = html.escape(document.get("url", ""), quote=True)

            if not url.startswith("https://"):
                continue

            parts.append(
                f'<article><strong>{titol}</strong> '
                f'<a href="{url}" target="_blank" '
                f'rel="noopener noreferrer">Consultar document</a>'
                f'<p>Estat del termini: pendent de verificar</p>'
                f'</article><hr>'
            )

    ara = datetime.now(ZoneInfo("Europe/Madrid"))
    parts.append(
        f"<footer>Consulta: {ara:%d/%m/%Y %H:%M}</footer>"
    )
    parts.append("</body></html>")

    SORTIDA.write_text(
        "\n".join(parts), encoding="utf-8"
    )

    print("Previsualització generada:", SORTIDA)
    print("La web pública index.html no s'ha modificat.")

if __name__ == "__main__":
    main()
