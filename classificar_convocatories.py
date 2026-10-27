"""Classificació preliminar de documents públics; NO declara places obertes."""
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse

SOURCE = Path("estat_consells.json")
TARGET = Path("convocatories_per_revisar.json")
ROLE_PATTERNS = [
    (r"peo[-_ ]conductor", "Peó/ona conductor/a"),
    (r"educador[-_ ]social|educacio[-_ ]social", "Educació social"),
    (r"terapeuta[-_ ]ocupacional", "Terapeuta ocupacional"),
    (r"dinamitzador[-_ ]civic", "Dinamització cívica"),
    (r"treballador[a]?[-_ ]social", "Treball social"),
    (r"joventut", "Joventut"),
    (r"tecnic[-_ ]arxiu", "Tècnic/a d'arxiu"),
    (r"proteccio[-_ ]civil", "Protecció civil"),
    (r"administratiu", "Administració"),
]
STAGE_PATTERNS = [
    (r"admes|exclos|llistat", "Llista d'admesos/exclosos"),
    (r"rectific", "Rectificació"),
    (r"decret", "Decret"),
    (r"bases|convocatoria", "Bases o convocatòria"),
    (r"bop|dogc|boe", "Publicació oficial"),
]
def normalized(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value)

def classify(item, source):
    url = item["url"]
    slug = normalized(unquote(urlparse(url).path))
    title = item["titol_document"]
    role = next((name for pattern, name in ROLE_PATTERNS if re.search(pattern, slug)), None)
    stage = next((name for pattern, name in STAGE_PATTERNS if re.search(pattern, normalized(title)+"-"+slug)), "Document de procés")
    return {"font": source, "titol_document": title, "url": url,
            "possible_lloc": role, "tipus_document": stage,
            "termini": None, "estat_inscripcio": "Sense verificar",
            "requereix_revisio": True}

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    result = []
    for source, documents in data["fonts"].items():
        result += [classify(document, source) for document in documents]
    TARGET.write_text(json.dumps({"nota": "Classificació de documents, no ofertes verificades. No deduir terminis ni vigència.",
        "documents": result}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Documents classificats:", len(result))
    for source in data["fonts"]:
        group = [x for x in result if x["font"] == source]
        recognized = [x for x in group if x["possible_lloc"]]
        print(source, "- documents:", len(group), "- amb possible lloc:", len(recognized))
        for item in recognized:
            print("  POSSIBLE LLOC:", item["possible_lloc"], "-",item["tipus_document"], "-",item["url"])
    print("Cap termini ni convocatòria oberta confirmats. Web pública intacta.")

if __name__ == "__main__":
    main()
