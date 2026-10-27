"""Diagnòstic de blocs de convocatòries, sense escriure a la web."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as f:
        sources = [x for x in json.load(f)["fonts"] if x["nom"].startswith("Consell Comarcal")]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        for source in sources:
            print("\nFONT:", source["nom"])
            try:
                response = await page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(4000)
                print("HTTP:", response.status if response else "sense resposta")
                if not response or response.status != 200:
                    continue
                candidates = await page.locator("a[href]").evaluate_all("""links => links
                  .filter(a => /convocat|bases|decret|personal|anunci/i.test(a.innerText) &&
                          (/pdf|documents|convocatoria/i.test(a.href)))
                  .slice(0,18)
                  .map(a => ({
                     text: a.innerText.trim().replace(/\\s+/g,' ').slice(0,110),
                     url: a.href,
                     context: (a.closest('tr, article, li, .views-row, .field-item, p')?.innerText||'').trim().replace(/\\s+/g,' ').slice(0,350),
                     ancestor: a.parentElement?.parentElement?.tagName || ''
                  }))""")
                print("Candidats de documents:", len(candidates))
                for i, c in enumerate(candidates, 1):
                    print(f"{i}. TÍTOL: {c['text']}")
                    print("   CONTEXT:", c["context"])
                    print("   URL:", c["url"])
                print("NOTA: candidats sense confirmar termini o vigència.")
            except Exception as exc:
                print("ERROR:", type(exc).__name__, str(exc)[:250])
        await browser.close()

asyncio.run(main())
