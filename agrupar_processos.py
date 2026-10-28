
"""Agrupacio prudent de convocatories dels consells.

No confirma terminis oberts ni modifica la web publica.
"""

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCE = Path("resultat_filtre_terminis.json")
DEST = Path("processos_per_revisar.json")

PERFILS = [
    (r"peo.{0,15}conductor", "Peó/ona conductor/a"),
    (r"educador.{0,12}social", "Educació social"),
    (r"terapeuta.{0,12}ocupacional", "Teràpia ocupacional"),
    (r"dinamitzador.{0,12}civic", "Dinamització cívica"),
    (r"treballador.{0,12}social", "Treball social"),
    (r"tecnic.{0,12}sisi", "Tècnic/a SISI"),
    (r"tecnic.{0,12}arxiu", "Tècnic/a d'arxiu"),
    (r"proteccio.{0,12}civil", "Protecció civil"),
    (r"coordinador.{0,30}juridic", "Coordinació jurídica"),
    (r"administratiu", "Administració"),
    (r"joventut", "Joventut"),
]

EXPEDIENT = re.compile(
    r"\b(?:expedient|exp)\.?\s*(?:num\.?|numero|n)?\s*"
    r"[:\-]?\s*(\d{1,6}\s*/\s*20\d{2})\b",
    re.IGNORECASE,
)


def normalitzar(text):
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(
        c for c in text if not unicodedata.combining(c)
    )
    return text.lower()


def detectar_perfil(doc):
    text = " ".join([
        doc.get("document", ""),
        doc.get("url", ""),
        *doc.get("fragments_rellevants", []),
    ])
    text = normalitzar(text)

    for patro, perfil in PERFILS:
        if re.search(patro, text):
            return perfil

    return None


def detectar_expedient(doc):
    textos = [
        doc.get("document", ""),
        *doc.get("fragments_rellevants", []),
    ]

    trobats = set()
    for text in textos:
        for valor in EXPEDIENT.findall(normalitzar(text)):
            trobats.add(re.sub(r"\s+", "", valor))

    if len(trobats) == 1:
        return next(iter(trobats))

    return None


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(
            "Falta resultat_filtre_terminis.json. "
            "Cal executar primer la lectura i el filtre."
        )

    dades = json.loads(SOURCE.read_text(encoding="utf-8"))

    candidats = [
        d for d in dades.get("documents", [])
        if d.get("categoria") == "possible_convocatoria"
    ]

    grups = {}
    sense_expedient = []

    for doc in candidats:
        font = doc.get("font", "")
        perfil = detectar_perfil(doc)
        expedient = detectar_expedient(doc)

        document = {
            "titol": doc.get("document", ""),
            "url": doc.get("url", ""),
            "perfil_detectat": perfil,
            "expedient_detectat": expedient,
        }

        if expedient:
            clau = (font, expedient)
            if clau not in grups:
                grups[clau] = {
                    "font": font,
                    "expedient": expedient,
                    "perfils_detectats": [],
                    "documents": [],
                    "estat_inscripcio": "no_verificat",
                    "requereix_revisio": True,
                }

            grup = grups[clau]
            if perfil and perfil not in grup["perfils_detectats"]:
                grup["perfils_detectats"].append(perfil)

            if not any(
                d["url"] == document["url"]
                for d in grup["documents"]
            ):
                grup["documents"].append(document)

        else:
            sense_expedient.append({
                "font": font,
                "perfil_possible": perfil,
                "document": document,
                "motiu": (
                    "Sense expedient identificat amb prou "
                    "certesa. No s'agrupa automaticament."
                ),
                "estat_inscripcio": "no_verificat",
            })

    sortida = {
        "data_analisi": datetime.now(
            ZoneInfo("Europe/Madrid")
        ).isoformat(),
        "avis": (
            "Agrupacio provisional per expedient explicit. "
            "No confirma ofertes obertes ni terminis vigents."
        ),
        "documents_candidats": len(candidats),
        "grups_amb_expedient": len(grups),
        "documents_sense_expedient": len(sense_expedient),
        "grups": list(grups.values()),
        "pendents_identificacio": sense_expedient,
    }

    DEST.write_text(
        json.dumps(sortida, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Documents candidats:", len(candidats))
    print("Grups amb expedient:", len(grups))
    print("Documents sense expedient:", len(sense_expedient))
    print("Resultat:", DEST)
    print("Cap oferta oberta confirmada.")
    print("La web publica no s'ha modificat.")


if __name__ == "__main__":
    main()
