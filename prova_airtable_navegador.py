"""Diagnòstic dels enllaços a ofertes públiques d'Airtable.
No publica ni modifica la web. No imprimeix dades personals de contacte."""
import asyncio
import json
from urllib.parse import urlsplit, urlunsplit
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as file:
        sources = json.load(file)["fonts"]
    url = next(s["url"] for s in sources if s["nom"] == "Sobirà Dinàmic")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(12000)
        print("HTTP:", response.status if response else "sense resposta")
        print("Pàgina:", await page.title())
        links = await page.locator("a[href*='rec']").evaluate_all("""elements =>
            elements.map(a => ({href: a.href, text: a.innerText.trim()}))""")
        unique = {}
        for link in links:
            address = link["href"].split("?")[0]
            if "/rec" not in address:
                continue
            unique.setdefault(address, [])
            label = " ".join(link["text"].split())
            if label and label not in unique[address]:
                unique[address].append(label)
        print("Enllaços totals:", len(links))
        print("URL de registres úniques:", len(unique))
        for n, (address, labels) in enumerate(unique.items(), 1):
            print(f"Registre {n}: {address}")
            print("  Text de l'enllaç:", " | ".join(labels)[:140] or "(sense text)")
        print("DIAGNÒSTIC: els textos d'enllaç no estan validats com a títols.")
        await browser.close()

asyncio.run(main())
