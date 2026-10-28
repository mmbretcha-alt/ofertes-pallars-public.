
import requests

URL = (
    "https://www.pallarsjussa.cat/tramits-i-gestions/"
    "convocatories-de-personal"
)

try:
    resposta = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    print("Codi HTTP:", resposta.status_code)
    print("Longitud resposta:", len(resposta.content))

    if resposta.ok:
        text = resposta.text.lower()
        print("Conté expedient 1223/2026:",
              "1223/2026" in text)
        print("Conté termini de presentació:",
              "termini de presentació" in text)
    else:
        print("La pàgina no permet aquesta lectura.")

except requests.RequestException as error:
    print("Error de connexió:", error)
