"""Diagnòstic de convocatòries dels dos consells. No modifica la web."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    with open("fonts.json", encoding="utf-8") as file:
        sources = [s for s in json.load(file)["fonts"] if s["nom"].startswith("Consell Comarcal")]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        for source in sources:
            print("\n=== ", source["nom"], " ===")
            try:
                response = await page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                print("HTTP:", response.status if response else "sense resposta")
                if not response or response.status != 200:
                    continue
                data = await page.locator("body").evaluate("""body => {
                  const selected = [...body.querySelectorAll("a[href]")].map(a => ({
                    title: (a.innerText||"").replace(/\\s+/g," ").trim(),
                    url: a.href,
                    context: (a.closest("li, tr, article, .views-row, .field, p")?.innerText||"").replace(/\\s+/g," ").trim().slice(0,220)
                  })).filter(x => x.title && (/(convocat|bases|borsa|selecci|personal|descarrega|anunci)/i.test(x.title+" "+x.context) || /\\.pdf(\\?|$)/i.test(x.url)));
                  return selected.slice(0,35);
                }""")
                print("Enllaços amb context rellevant:", len(data))
                for i, item in enumerate(data, 1):
                    print(f"[{i}] TEXT:", item["title"][:140])
                    print("    CONTEXT:", item["context"][:220])
                    print("    URL:", item["url"][:240])
            except Exception as error:
                print("ERROR:", type(error).__name__, str(error)[:220])
        await browser.close()

asyncio.run(main())
