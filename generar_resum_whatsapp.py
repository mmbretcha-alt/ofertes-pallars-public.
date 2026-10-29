"""Compara el recull públic amb l'última instantània desada.
La primera execució estableix la base i no marca anuncis preexistents com a nous.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
STATE = ROOT / "estat_ofertes.json"
REPORT = ROOT / "resum_whatsapp.txt"
URL = "https://mmbretcha-alt.github.io/ofertes-pallars-public./"
soup = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
previous = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None

def normalize(s):
    return re.sub(r"\\s+", " ", s or "").strip().casefold()

found = {}
for section in soup.select("section.section"):
    h = section.find("h2")
    if h is None:
        continue
    source = re.sub(r"\\s*\\([^)]*\\)\\s*$", "", h.get_text(" ", strip=True))
    for article in section.find_all("article"):
        strong = article.find("strong")
        if not strong:
            continue
        name = strong.get_text(" ", strip=True)
        anchor = article.find("a", href=True)
        link = anchor["href"] if anchor else ""
        # Prioritzem enllaç de l'anunci (quan existeix) i títol en altres casos.
        key = hashlib.sha256((normalize(source) + "|" + (link if "Consell Comarcal del Pallars Jussà" not in source else normalize(name))).encode("utf-8")).hexdigest()[:20]
        found[key] = {"font": source, "titol": name, "url": link}

today = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
old = previous.get("anuncis", {}) if previous else {}
new = {k: v for k, v in found.items() if k not in old} if previous else {}
by_source = {}
for item in new.values():
    by_source[item["font"]] = by_source.get(item["font"], 0) + 1
lines = [
    "📢 OFERTES DE FEINA ALS PALLARS",
    "Actualització: " + today,
    "",
]
if previous is None:
    lines += ["Primer registre establert: encara no es poden comptar novetats respecte d'ahir."]
elif new:
    lines += ["Novetats detectades respecte de l'última comprovació: " + str(len(new))]
    for source, count in sorted(by_source.items()):
        lines.append(f"• {source}: {count}")
    lines += ["", "Ofertes i documents nous:"]
    for item in list(new.values())[:12]:
        lines.append("• " + item["titol"][:145] + " (" + item["font"] + ")")
    if len(new) > 12:
        lines.append(f"… i {len(new)-12} més")
else:
    lines += ["No s'han detectat registres nous respecte de l'última comprovació."]
lines += ["", "🔗 Consulta les ofertes i els documents:", URL, "", "Comprova sempre els terminis i la vigència a la font original.", "Associació Reintegra"]
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
STATE.write_text(json.dumps({"data": today, "anuncis": found}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Registres totals: {len(found)}; novetats: {len(new)}; base anterior: {bool(previous)}")
