import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://www.seu-e.cat/ca/web/ccpallarssobira/govern-obert-i-transparencia/informacio-institucional-i-organitzativa/empleats-publics/convocatories-de-personal"
r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
print("Codi HTTP:", r.status_code)
print("URL final:", r.url)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")
text = soup.get_text(" ", strip=True)
print("Titol:", soup.title.get_text(" ", strip=True) if soup.title else "(sense titol)")
print("Conte 'OFICINA JOVE':", "OFICINA JOVE" in text.upper())
print("Conte 'convocatoria':", "convocat" in text.lower())
print("Enllacos de documents/convocatories:")
n = 0
seen = set()
for a in soup.find_all("a", href=True):
    title = a.get_text(" ", strip=True)
    url = urljoin(r.url, a["href"])
    if not title or (title, url) in seen:
        continue
    if any(w in title.lower() for w in ["bases", "convocat", "decret", "joventut", "descarrega"]):
        seen.add((title, url))
        n += 1
        print(f"- {title[:180]} | {url}")
        if n >= 30:
            break
print("Enllacos candidats:", n)
print("Prova finalitzada. No s'ha modificat la web publica.")
