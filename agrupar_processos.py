
"""Agrupacio provisional de documents de convocatories.

No confirma que els documents pertanyin al mateix expedient.
No modifica la web publica.
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
    (r"coordinador.{0,45}juridic", "Coordinació jurídica"),
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
    parts = [
        doc.get("document", ""),
        doc.get("url", ""),
        *doc.get("fragments_rellevants", []),
    ]
    text = normalitzar(" ".join(parts))

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
            "Falta resultat_filtre_terminis.json"
        )

    dades = json.loads(SOURCE.read_text(encoding="utf-8"))

    candidats = [
        doc for doc in dades.get("documents", [])
        if doc.get("categoria") == "possible_convocatoria"
    ]

    grups = {}
    pendents = []

    for doc in candidats:
        font = doc.get("font", "")
        perfil = detectar_perfil(doc)
        expedient = detectar_expedient(doc)

        fitxa = {
            "titol": doc.get("document", ""),
            "url": doc.get("url", ""),
            "expedient_detectat": expedient,
            "estat_inscripcio": "no_verificat",
        }

        if not perfil:
            pendents.append({
                "font": font,
                "document": fitxa,
                "motiu": "Perfil professional no identificat",
                "requereix_revisio": True,
            })
            continue

        clau = (font, perfil)

        if clau not in grups:
            grups[clau] = {
                "font": font,
                "perfil": perfil,
                "tipus_agrupacio": "provisional_per_perfil",
                "mateix_expedient_confirmat": False,
                "estat_inscripcio": "no_verificat",
                "requereix_revisio": True,
                "documents": [],
            }

        if not any(
            d["url"] == fitxa["url"]
            for d in grups[clau]["documents"]
        ):
            grups[clau]["documents"].append(fitxa)

    grups_ordenats = sorted(
        grups.values(),
        key=lambda grup: (grup["font"], grup["perfil"]),
    )

    sortida = {
        "data_analisi": datetime.now(
            ZoneInfo("Europe/Madrid")
        ).isoformat(),
        "avis": (
            "Agrupacio provisional per perfil. "
            "Els documents d'un grup poden correspondre "
            "a expedients diferents. Cap oferta oberta "
            "ni cap termini vigent ha estat confirmat."
        ),
        "documents_candidats": len(candidats),
        "perfils_agrupats": len(grups_ordenats),
        "documents_sense_perfil": len(pendents),
        "grups": grups_ordenats,
        "pendents_identificacio": pendents,
    }

    DEST.write_text(
        json.dumps(
            sortida, ensure_ascii=False, indent=2
        ) + "\n",
        encoding="utf-8",
    )

    print("Documents candidats:", len(candidats))
    print("Perfils agrupats:", len(grups_ordenats))
    print("Documents sense perfil:", len(pendents))
    print("Resultat:", DEST)
    print("Cap oferta oberta confirmada.")
    print("La web publica no s'ha modificat.")


if __name__ == "__main__":
    main()
