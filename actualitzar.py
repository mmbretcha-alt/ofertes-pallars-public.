
import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

print("REINTEGRA - COMPROVACIO DE FONTS")
print("Data:", datetime.now(ZoneInfo("Europe/Madrid")))
print("--------------------------------")

with open("fonts.json", encoding="utf-8") as f:
    configuracio = json.load(f)

font = next(
    f for f in configuracio["fonts"]
    if f["nom"] == "Sobirà Dinàmic"
)

url = font["url"]

print("Font:", font["nom"])
print("URL:", url)

peticio = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

try:
    with urllib.request.urlopen(
        peticio, timeout=30
    ) as resposta:
        contingut = resposta.read().decode(
            "utf-8", errors="replace"
        )
        print("Estat HTTP:", resposta.status)
        print("Mida resposta:", len(contingut))
        print(
            "Conté identificadors de registres:",
            "rec" in contingut
        )
        print("Prova de connexió completada.")

except Exception as error:
    print("ERROR de connexió:", error)
    raise
