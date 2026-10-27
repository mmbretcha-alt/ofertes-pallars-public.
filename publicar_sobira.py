"""Actualitza la secció pública de Sobirà Dinàmic amb dades de la vista Airtable."""
import asyncio
import html
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

WEB = Path("index.html")
STATE = Path("estat_sobira.json")

async def llegir_ofertes():
    with open("fonts.json", encoding="utf-8") as f:
        fonts = json.load(f)["fonts"]
    url = next(f["url"] for f in fonts if f["nom"] == "Sobirà Dinàmic")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="ca-ES")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if response is None or response.status != 200:
            raise RuntimeError("Airtable no ha retornat HTTP 200")
        await page.wait_for_timeout(12000)
        links = await page.locator("a[href*='/rec']").evaluate_all("""elements =>
          elements.map(a => ({url: a.href.split('?')[0], title: a.innerText.trim()}))""")
        await browser.close()
    result = {}
    for item in links:
        match = re.search(r"/(rec[A-Za-z0-9]{14})(?:/|$)", item["url"])
        title = " ".join(item["title"].split())
        if not match or not title or title.casefold() == "més info":
            continue
        rid = match.group(1)
        if rid in result and result[rid]["titol"] != title:
            raise RuntimeError("Registre amb títols contradictoris")
        result[rid] = {"id": rid, "titol": title, "url": item["url"]}
    return result

async def main():
    offers = await llegir_ofertes()
    original = WEB.read_text(encoding="utf-8")
    pattern = re.compile(r'<section class="section"><h2>Sobirà Dinàmic\b.*?</section>', re.S)
    match = pattern.search(original)
    if match is None:
        raise RuntimeError("No es troba la secció de Sobirà Dinàmic")
    previous = set(re.findall(r"/(rec[A-Za-z0-9]{14})", match.group()))
    if len(offers) == 0 or (previous and len(offers) < max(1, len(previous) // 2)):
        raise RuntimeError("Consulta incompleta o buida. Es conserva la web anterior.")
    current = set(offers)
    print("Ofertes actuals:", len(current))
    print("Noves:", len(current - previous), sorted(current - previous))
    print("No detectades:", len(previous - current), sorted(previous - current))
    rows = []
    for offer in offers.values():
        url = html.escape(offer["url"], quote=True)
        title = html.escape(offer["titol"])
        rows.append(f'<article><strong>{title}</strong><div><small></small></div><a href="{url}" rel="noopener noreferrer" target="_blank">Consultar font original</a></article>')
    stamp = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M")
    section = ('<section class="section"><h2>Sobirà Dinàmic <small>('
               + str(len(offers)) + ')</small></h2>'
               + '<p><small>Consulta automàtica: ' + stamp + ' (hora local). Comproveu sempre la vigència a la font.</small></p>'
               + ''.join(rows) + '</section>')
    updated = original[:match.start()] + section + original[match.end():]
    # Eliminar l'avís inicial obsolet només si encara té exactament el text conegut.
    old_notice = ("<strong>Primera publicació: 27/10/2026.</strong> Les dades següents són una instantània inicial. La pàgina encara no s'actualitza automàticament. Les ofertes poden haver caducat: comprova sempre les bases i els terminis a la font original.")
    new_notice = ("<strong>Actualització de Sobirà Dinàmic automatitzada.</strong> Les altres fonts continuen pendents d'automatització. Comprova sempre les bases i els terminis a la font original.")
    updated = updated.replace(old_notice, new_notice)
    WEB.write_text(updated, encoding="utf-8")
    STATE.write_text(json.dumps({
        "consulta": datetime.now(ZoneInfo("Europe/Madrid")).isoformat(),
        "font": "Sobirà Dinàmic",
        "ofertes": sorted(offers.values(), key=lambda x: x["id"]),
        "noves_respecte_a_la_web_anterior": sorted(current - previous),
        "no_detectades_respecte_a_la_web_anterior": sorted(previous - current),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Fitxers actualitzats. Les altres seccions de la web es conserven.")

asyncio.run(main())
