"""Cerca indicis de termini en els PDF públics, sense inferir dates d'obertura.
No modifica la web ni publica ofertes."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
import pymupdf

src=json.loads(Path("estat_consells.json").read_text(encoding="utf-8"))["fonts"]
patterns=[re.compile(p,re.I) for p in [
 r"termini.{0,90}(?:sol[·.]licit|inst[aà]nc|presentac|dies h[aà]bils)",
 r"(?:sol[·.]licit|inst[aà]nc|presentac).{0,90}termini",
 r"vint dies h[aà]bils|deu dies h[aà]bils|20 dies h[aà]bils",
]]
results=[]
for source, documents in src.items():
    for doc in documents:
        url=doc["url"]
        if not (urlparse(url).path.lower().endswith(".pdf") or "/documents/" in url):
            continue
        record={"font":source,"document":doc["titol_document"],"url":url,
                "fragments_de_termini":[],"lectura":"pendent"}
        try:
            response=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"},
                                  stream=True)
            response.raise_for_status()
            raw=bytearray()
            for chunk in response.iter_content(8192):
                raw.extend(chunk)
                if len(raw)>12_000_000:
                    raise ValueError("Document massa gran")
            pdf=pymupdf.open(stream=bytes(raw),filetype="pdf")
            if len(pdf)>120:
                raise ValueError("PDF amb massa pàgines")
            text=" ".join(page.get_text() for page in pdf)
            normalized=re.sub(r"\s+"," ",text)
            snippets=[]
            for pattern in patterns:
                for match in list(pattern.finditer(normalized))[:3]:
                    fragment=normalized[max(0,match.start()-140):match.end()+180]
                    if fragment not in snippets:
                        snippets.append(fragment)
            record["fragments_de_termini"]=snippets[:5]
            record["lectura"]="text llegit" if text.strip() else "sense text extraïble"
        except Exception as exc:
            record["lectura"]="no s'ha pogut llegir: "+type(exc).__name__
        results.append(record)
        print(source,"|",doc["titol_document"][:65],"|",record["lectura"],
              "| fragments:",len(record["fragments_de_termini"]))
Path("terminis_per_verificar.json").write_text(
    json.dumps({"avis":"Fragments orientatius. Cap termini o inscripció oberta verificats.",
                "documents":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Documents examinats:",len(results))
print("Amb algun fragment candidat:",sum(bool(r["fragments_de_termini"]) for r in results))
print("La web pública no s'ha modificat.")
