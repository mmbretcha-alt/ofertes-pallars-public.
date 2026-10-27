"""Seguiment dels documents públics dels consells comarcals.
Un document nou no implica una nova oferta ni un termini obert."""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

STATE = Path("estat_consells.json")
MAX_ITEMS = 500

async def main():
    with open("fonts.json", encoding="utf-8") as f:
        sources = [x for x in json.load(f)["fonts"] if x["nom"].startswith("Consell Comarcal")]
    snapshots = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        for source in sources:
            resp = await page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
            if resp is None or resp.status != 200:
                raise RuntimeError(f"Error HTTP a {source['nom']}: {resp.status if resp else 'cap resposta'}")
            await page.wait_for_timeout(4000)
            raw = await page.locator("a[href]").evaluate_all("""links => links.map(a => ({
                title: (a.innerText || '').replace(/\\s+/g,' ').trim(),
                url: a.href.split('#')[0].split('?')[0]
            })).filter(x => x.title && (/\\.pdf$/i.test(x.url) || /\/documents\//i.test(x.url)))""")
            unique = {}
            for item in raw:
                if not item["url"].startswith("https://"):
                    continue
                unique.setdefault(item["url"], {"titol_document": item["title"], "url": item["url"]})
            if not unique or len(unique) > MAX_ITEMS:
                raise RuntimeError(f"Nombre inesperat de documents a {source['nom']}: {len(unique)}")
            snapshots[source["nom"]] = sorted(unique.values(), key=lambda x: x["url"])
            print(source["nom"], "documents trobats:", len(unique))
        await browser.close()

    old = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"fonts": {}}
    baseline = not STATE.exists()
    for name, current in snapshots.items():
        previous = {x["url"] for x in old.get("fonts", {}).get(name, [])}
        added = [x for x in current if x["url"] not in previous]
        print("\nFont:", name)
        print("Documents nous respecte a la consulta anterior:", "línia base inicial" if baseline else len(added))
        if not baseline:
            for item in added:
                print("DOCUMENT NOU (NO ÉS NECESSÀRIAMENT UNA OFERTA):", item["titol_document"], item["url"])
    STATE.write_text(json.dumps({
        "consultat_el": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "avis": "Documents detectats; no s'ha validat que siguin places noves o amb inscripció oberta.",
        "fonts": snapshots
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Estat dels consells desat; index.html no modificat.")

asyncio.run(main())
