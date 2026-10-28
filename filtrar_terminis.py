
"""Classificacio prudent dels terminis dels consells comarcals.

No confirma convocatories obertes ni modifica la web publica.
"""
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

SOURCE = Path("terminis_per_verificar.json")
TARGET = Path("resultat_filtre_terminis.json")

INSCRIPCIO = (
    "presentacio de sollicituds",
    "presentacio dinstancies",
    "termini de presentacio",
    "presentar sollicituds",
    "presentar instancies",
)

ALTRES_FASES = (
    "termini de reclamacions",
    "termini per esmenes",
    "termini per a esmenes",
    "termini de deu dies",
    "recurs contencios",
    "llista dadmesos",
    "baremacio",
    "fase doposicio",
)

def normalitzar(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text if not unicodedata.combining(c)
    )
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()

def classificar(document):
    fragments = document.get("fragments_de_termini", [])
    lectura = document.get("lectura", "")

    resultat = {
        "font": document.get("font", ""),
        "document": document.get("document", ""),
        "url": document.get("url", ""),
        "lectura": lectura,
        "categoria": "altres_documents_o_errors",
        "estat_inscripcio": "no_verificat",
        "fragments_rellevants": [],
        "requereix_revisio": True,
    }

    if lectura != "text llegit":
        resultat["motiu"] = "Lectura no completada"
        return resultat

    for fragment in fragments:
        text = normalitzar(fragment)

        if any(terme in text for terme in INSCRIPCIO):
            resultat["fragments_rellevants"].append(fragment)

    if resultat["fragments_rellevants"]:
        resultat["categoria"] = "possible_convocatoria"
        resultat["motiu"] = (
            "Conté referències a inscripció, "
            "però no se n'ha verificat la vigència"
        )
    elif any(
        terme in normalitzar(f)
        for f in fragments
        for terme in ALTRES_FASES
    ):
        resultat["motiu"] = "Possibles tràmits d'altres fases"
    else:
        resultat["motiu"] = "Sense indicis suficients d'inscripció"

    return resultat

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(
            "Falta terminis_per_verificar.json. "
            "Cal recuperar-lo de l'execucio de lectura."
        )

    dades = json.loads(SOURCE.read_text(encoding="utf-8"))
    documents = dades.get("documents", [])
    resultats = [classificar(doc) for doc in documents]

    candidats = [
        r for r in resultats
        if r["categoria"] == "possible_convocatoria"
    ]

    sortida = {
        "data_analisi": datetime.now().astimezone().isoformat(),
        "avis": (
            "Classificacio orientativa. "
            "No hi ha cap convocatoria oberta verificada."
        ),
        "documents_examinats": len(resultats),
        "possibles_convocatories": len(candidats),
        "documents": resultats,
    }

    TARGET.write_text(
        json.dumps(sortida, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Documents examinats:", len(resultats))
    print("Possibles convocatories per revisar:", len(candidats))
    print("Altres documents o errors:", len(resultats) - len(candidats))
    print("Resultat:", TARGET)
    print("La web publica no s'ha modificat.")

if __name__ == "__main__":
    main()
