"""Diagnòstic de lectura d'una vista pública d'Airtable amb navegador real.
No publica ni modifica cap oferta."""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as f:
        fonts = json.load(f)["fonts"]
    url = next(x["url"] for x in fonts if x["nom"] == "Sobirà Dinàmic")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("HTTP:", response.status if response else "sense resposta")
        await page.wait_for_timeout(12000)
        text = await page.locator("body").inner_text(timeout=15000)
        print("URL final:", page.url)
        print("Caràcters visibles:", len(text))
        print("Títol de pàgina:", (await page.title())[:150])
        checks = ["Gerocultor", "Recepcionista", "Netejador", "OBSERVADORS"]
        for term in checks:
            print(f"Text d'oferta {term!r}:", term.lower() in text.lower())
        record_links = await page.locator("a[href*='rec']").count()
        print("Enllaços a registres visibles:", record_links)
        print("Fragments de text (màxim 700 caràcters):", re.sub(r"\\s+", " ", text)[:700])
        await browser.close()

asyncio.run(main())
