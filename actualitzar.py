import json
import re
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

print("REINTEGRA - PROVA DE LECTURA AIRTABLE")
print("Data:", datetime.now(ZoneInfo("Europe/Madrid")))
with open("fonts.json", encoding="utf-8") as fitxer:
    fonts = json.load(fitxer)["fonts"]

font = next(f for f in fonts if f["nom"] == "Sobirà Dinàmic")
peticio = urllib.request.Request(
    font["url"], headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(peticio, timeout=30) as resposta:
    contingut = resposta.read().decode("utf-8", errors="replace")
    print("Estat HTTP:", resposta.status)
    print("Mida resposta:", len(contingut))

ids = sorted(set(re.findall(r"rec[A-Za-z0-9]{14}", contingut)))
print("Identificadors de registre diferents detectats:", len(ids))
print("Mostra identificadors:", ids[:5])

titols = [
    "Gerocultor/a",
    "RECEPCIONISTA",
    "OBSERVADORS/ES NIVOLÒGICS/QUES",
    "RESPONSABLE DE GESTIÓ",
]
for titol in titols:
    print(f"Títol {titol!r} present a la resposta:", titol.lower() in contingut.lower())

print("Aquesta és una prova diagnòstica; encara no actualitza la web.")
