"""Prova de lectura de fonts addicionals. No publica ni modifica la web."""
import asyncio
import json
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as f:
        sources = json.load(f)["fonts"]
    sources = [s for s in sources if s["nom"] != "Sobirà Dinàmic"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        for source in sources:
            print("\n=== FONT:", source["nom"], "===")
            url = source["url"]
            if "feinaactiva.gencat.cat" in url:
                url = "https://feinaactiva.gencat.cat/search/offers/list?province=25"
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                print("HTTP:", response.status if response else "sense resposta")
                print("URL final:", page.url)
                print("Títol de pàgina:", await page.title())
                text = await page.locator("body").inner_text(timeout=15000)
                print("Caràcters visibles:", len(text))
                print("Esmenta Pallars Jussà:", "pallars jussà" in text.lower())
                print("Esmenta Pallars Sobirà:", "pallars sobirà" in text.lower())
                if "feinaactiva" in url:
                    anchors = await page.locator("a[href*='/search/offers/detail/']").evaluate_all(
                        """a => a.map(x => ({text:x.innerText.trim(),href:x.href})).filter(x=>x.text)""")
                else:
                    anchors = await page.locator("a").evaluate_all(
                        """a => a.map(x => ({text:x.innerText.trim(),href:x.href})).filter(x=>x.text && /convocat|personal|ofert|treball|expedient/i.test(x.text)).slice(0,12)""")
                print("Enllaços candidats detectats:", len(anchors))
                for entry in anchors[:8]:
                    print("  -", " ".join(entry["text"].split())[:120], entry["href"][:180])
            except Exception as error:
                print("ERROR DE CONSULTA:", type(error).__name__, str(error)[:300])
        await browser.close()

asyncio.run(main())
