"""Agrupa documents amb un rol identificat en candidats de procés.
Agrupació orientativa: no valida terminis ni afirma convocatòries obertes."""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

SOURCE = Path("estat_consells.json")
DEST = Path("processos_per_revisar.json")

RULES = [
 ("peo_conductor", r"peo[-_ ]conductor|peo-conductor", "Peó/ona conductor/a"),
 ("educacio_social", r"educador[-_ ]social|educacio[-_ ]social", "Educació social"),
 ("terapia_ocupacional", r"terapeuta[-_ ]ocupacional", "Terapeuta ocupacional"),
 ("dinamitzacio_civica", r"dinamitzador[-_ ]civic", "Dinamització cívica"),
 ("treball_social", r"treballador[a]?[-_ ]social", "Treball social"),
 ("joventut", r"joventut", "Joventut"),
 ("arxiu", r"tecnic[-_ ]arxiu", "Tècnic/a d'arxiu"),
 ("proteccio_civil", r"proteccio[-_ ]civil", "Protecció civil"),
 ("administracio", r"administratiu", "Administració"),
]
def norm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s)

def main():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    grouped=defaultdict(list)
    unclassified=0
    for source, docs in data["fonts"].items():
        for doc in docs:
            slug=norm(unquote(urlparse(doc["url"]).path))
            role=next(((key,title) for key,pat,title in RULES if re.search(pat,slug)),None)
            if role is None:
                unclassified+=1
                continue
            (key,title)=role
            grouped[(source,key,title)].append(doc)
    groups=[]
    for (source,key,title),docs in sorted(grouped.items()):
        groups.append({"font":source,"possible_lloc":title,
                       "clau_provisional":key,"nombre_documents":len(docs),
                       "documents":docs,"termini":None,
                       "estat_inscripcio":"No verificat",
                       "nota":"Documents agrupats pel text de l'URL; pot haver-hi més d'un procés del mateix perfil."})
    DEST.write_text(json.dumps({"advertiment":"Agrupació orientativa; no són ofertes noves verificades.","grups":groups},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Grups orientatius:",len(groups),"Documents sense perfil classificat:",unclassified)
    for group in groups: print(group["font"],"|",group["possible_lloc"],"| documents:",group["nombre_documents"])
    print("NO s'ha canviat la web ni s'ha confirmat cap convocatòria oberta.")
if __name__=="__main__": main()
