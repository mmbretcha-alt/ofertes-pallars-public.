"""Extreu títols i enllaços públics de Sobirà Dinàmic sense editar la web."""
import asyncio
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as f:
        fonts = json.load(f)["fonts"]
    url = next(x["url"] for x in fonts if x["nom"] == "Sobirà Dinàmic")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if not response or response.status != 200:
            raise RuntimeError(f"Resposta inesperada: {response.status if response else 'absent'}")
        await page.wait_for_timeout(12000)
        entries = await page.locator("a[href*='/rec']").evaluate_all("""elements =>
          elements.map(a => ({url: a.href.split('?')[0], title: a.innerText.trim()}))""")
        records = {}
        for entry in entries:
            match = re.search(r"/(rec[A-Za-z0-9]{14})(?:/|$)", entry["url"])
            title = " ".join(entry["title"].split())
            if not match or not title or title.casefold() == "més info":
                continue
            rid = match.group(1)
            if rid in records and records[rid]["titol"] != title:
                raise RuntimeError(f"Títols contradictoris per al registre {rid}")
            records[rid] = {"id": rid, "titol": title, "url": entry["url"]}
        await browser.close()
    if not records:
        raise RuntimeError("No s'han extret ofertes. No es genera un fitxer buit.")
    result = {
        "font": "Sobirà Dinàmic",
        "consultat_el": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "ofertes": sorted(records.values(), key=lambda x: x["id"])
    }
    with open("ofertes_sobira_prova.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Ofertes diferents extretes:", len(records))
    for item in result["ofertes"]:
        print(item["id"], "-", item["titol"])
    print("JSON de prova creat. Web pública no modificada.")

asyncio.run(main())
