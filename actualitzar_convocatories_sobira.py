from pathlib import Path
from urllib.parse import urljoin, urlparse
import html
import re
import requests
from bs4 import BeautifulSoup

URL = "https://www.seu-e.cat/ca/web/ccpallarssobira/govern-obert-i-transparencia/informacio-institucional-i-organitzativa/empleats-publics/convocatories-de-personal"
INDEX = Path("index.html")

response = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=35)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
if "Convocatòries de personal" not in soup.get_text(" ", strip=True):
    raise RuntimeError("No s'ha identificat la pàgina de convocatòries; no es modifica la web.")

links = {}
for a in soup.find_all("a", href=True):
    label = a.get_text(" ", strip=True)
    href = urljoin(response.url, a["href"])
    if urlparse(href).hostname not in ("seu-e.cat", "www.seu-e.cat"):
        continue
    if "/documents/" not in urlparse(href).path:
        continue
    if not label or not re.search(r"bases|decret|convocat|descarrega|selecci[oó]", label, re.I):
        continue
    links[href] = label

if not links:
    raise RuntimeError("No s'han trobat documents; es conserva la web existent.")

print("Documents identificats:", len(links))
for url, label in links.items():
    print("-", label, url)

items = "".join(
    '<article><strong>' + html.escape(label) + '</strong><div><small>Document oficial · vigència pendent de verificar</small></div>'
    '<a href="' + html.escape(url, quote=True) + '" target="_blank" rel="noopener noreferrer">Descarregar document</a></article>'
    for url, label in links.items()
)
section = (
    '<section class="section"><h2>Consell Comarcal del Pallars Sobirà '
    '<small>(' + str(len(links)) + ' documents)</small></h2>'
    '<p><small>Documents detectats automàticament. La publicació no implica que el termini estigui obert. '
    '<a href="' + html.escape(URL, quote=True) + '">Comprovar convocatòries i terminis a la font oficial</a>.</small></p>'
    + items + '</section>'
)
current = INDEX.read_text(encoding="utf-8")
pattern = re.compile(r'<section class="section"><h2>Consell Comarcal del Pallars Sobirà(?:.*?)</section>', re.S)
if not pattern.search(current):
    raise RuntimeError("No s'ha trobat la secció de Sobirà a index.html; s'atura per seguretat.")
updated = pattern.sub(lambda _: section, current, count=1)
if updated != current:
    INDEX.write_text(updated, encoding="utf-8")
    print("Secció Sobirà actualitzada.")
else:
    print("Sense canvis en els documents de Sobirà.")
