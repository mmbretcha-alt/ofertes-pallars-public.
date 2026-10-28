
import re
import requests
from bs4 import BeautifulSoup

URL = (
    "https://www.pallarsjussa.cat/tramits-i-gestions/"
    "convocatories-de-personal"
)

resposta = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
)
resposta.raise_for_status()

sopa = BeautifulSoup(resposta.text, "html.parser")

print("Codi HTTP:", resposta.status_code)

expedients = {}
patro = re.compile(r"\b\d{1,6}/20\d{2}\b")

for element in sopa.find_all(
    ["h2", "h3", "h4", "h5", "p", "strong"]
):
    text = element.get_text(" ", strip=True)

    for expedient in patro.findall(text):
        if expedient not in expedients:
            expedients[expedient] = text[:250]

print("Expedients identificats:", len(expedients))

for expedient, descripcio in list(expedients.items())[:30]:
    print("---")
    print("Expedient:", expedient)
    print("Text:", descripcio)

print("---")
print("Prova finalitzada.")
print("La web publica no s'ha modificat.")
