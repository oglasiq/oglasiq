import asyncio
import json
import os
import random
import requests
from playwright.async_api import async_playwright
from datetime import datetime

# ============================================
# NASTAVITVE
# ============================================
TELEGRAM_TOKEN = "8522586477:AAE0tasQkHhHGZs8b0m5WtEWor-6J6NUUmw"
TELEGRAM_CHAT_ID = "1123416623"

VIDENI_OGLASI_FILE = "videni_oglasi.json"
ISKANJA_FILE = "iskanja.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

# Intervali osveževanja glede na paket (v sekundah)
INTERVALI = {
    "free": 24 * 60 * 60,      # 24 ur
    "starter": 3 * 60 * 60,    # 3 ure
    "pro": 60 * 60,             # 1 ura
    "premium": 20 * 60,         # 20 minut
}

# Privzeta iskanja (ko ni iskanja.json)
PRIVZETA_ISKANJA = [
    {
        "id": 1,
        "url": "https://www.bolha.com/rabljeno?q=zemljisce",
        "paket": "premium",
        "aktiven": True,
        "ime": "Zemljišče test"
    }
]

# ============================================
# POMOZNE FUNKCIJE
# ============================================
def nalozi_videne():
    if os.path.exists(VIDENI_OGLASI_FILE):
        with open(VIDENI_OGLASI_FILE, "r") as f:
            return json.load(f)
    return []

def shrani_videne(videni):
    with open(VIDENI_OGLASI_FILE, "w") as f:
        json.dump(videni, f)

def nalozi_iskanja():
    if os.path.exists(ISKANJA_FILE):
        with open(ISKANJA_FILE, "r") as f:
            return json.load(f)
    # Ce ni datoteke uporabi privzeta iskanja
    shrani_iskanja(PRIVZETA_ISKANJA)
    return PRIVZETA_ISKANJA

def shrani_iskanja(iskanja):
    with open(ISKANJA_FILE, "w") as f:
        json.dump(iskanja, f, ensure_ascii=False, indent=2)

def zazna_portal(url):
    portali = {
        "avto.net": "🇸🇮 Avto.net",
        "bolha.com": "🇸🇮 Bolha.com",
        "nepremicnine.net": "🇸🇮 Nepremicnine.net",
        "njuskalo.hr": "🇭🇷 Njuskalo.hr",
        "olx.ba": "🇧🇦 OLX.ba",
        "olx.hr": "🇭🇷 OLX.hr",
        "olx.rs": "🇷🇸 OLX.rs",
        "halooglasi.com": "🇷🇸 Halo Oglasi",
        "kupujemprodajem.com": "🇷🇸 KupujemProdajem",
        "mobile.de": "🇩🇪 Mobile.de",
        "autoscout24": "🇩🇪 AutoScout24",
        "willhaben.at": "🇦🇹 Willhaben",
        "subito.it": "🇮🇹 Subito.it",
        "olx.me": "🇲🇪 OLX.me",
    }
    for kljuc, ime in portali.items():
        if kljuc in url.lower():
            return ime
    return "🌐 Neznani portal"

def poslji_telegram(naslov, cena, link, portal, iskanje_ime=""):
    cas = datetime.now().strftime("%H:%M")
    sporocilo = (
        f"🔔 <b>Nov oglas — OglasIQ</b>\n\n"
        f"📋 {naslov}\n"
        f"💰 Cena: {cena}\n"
        f"🌐 {portal}\n"
        f"🕐 {cas}\n"
    )
    if iskanje_ime:
        sporocilo += f"🔍 Iskanje: {iskanje_ime}\n"
    sporocilo += f"\n🔗 {link}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": sporocilo,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        })
        if r.status_code == 200:
            print(f"  ✅ Poslano: {naslov[:50]}")
        else:
            print(f"  ❌ Telegram napaka: {r.text}")
    except Exception as e:
        print(f"  ❌ Napaka: {e}")

# ============================================
# UNIVERZALNI SCRAPER
# ============================================
async def preveri_url(page, iskanje):
    url = iskanje.get("url", "")
    portal = zazna_portal(url)
    ime = iskanje.get("ime", "Brez imena")

    print(f"\n🔍 Preverjam: {portal}")
    print(f"   URL: {url[:60]}...")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))

        videni = nalozi_videne()
        novi = 0

        # BOLHA.COM
        if "bolha.com" in url:
            oglasi = await page.query_selector_all("article.entity-body")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3.entity-title a")
                    if not naslov_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await naslov_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.bolha.com" + link
                    cena_el = await oglas.query_selector("strong.price-box")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # AVTO.NET
        elif "avto.net" in url:
            oglasi = await page.query_selector_all("div.GO-Results-Row")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("div.GO-Results-Naziv")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.avto.net" + link
                    cena_el = await oglas.query_selector("div.GO-Results-Cena")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # NEPREMICNINE.NET
        elif "nepremicnine.net" in url:
            oglasi = await page.query_selector_all("div.oglas_container")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("span.title")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.nepremicnine.net" + link
                    cena_el = await oglas.query_selector("strong.price-box")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # NJUSKALO.HR
        elif "njuskalo.hr" in url:
            oglasi = await page.query_selector_all("li.EntityList-item")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3.entity-title a")
                    if not naslov_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await naslov_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.njuskalo.hr" + link
                    cena_el = await oglas.query_selector("strong.price-box")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # OLX (BA, HR, RS, ME)
        elif "olx." in url:
            oglasi = await page.query_selector_all("div.css-1sw3lwy, div.ooa-1t3a3hp, li[data-cy='l-card']")
            if not oglasi:
                oglasi = await page.query_selector_all("div.item-box, div[data-cy='l-card']")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3, h4, p[data-cy='ad-card-title']")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        base = url.split("/")[0] + "//" + url.split("/")[2]
                        link = base + link
                    cena_el = await oglas.query_selector("p[data-testid='ad-price'], div.price, strong")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # MOBILE.DE
        elif "mobile.de" in url:
            oglasi = await page.query_selector_all("div.cBox-body--resultitem, article.result-item")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3.headline, span.h3")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.mobile.de" + link
                    cena_el = await oglas.query_selector("div.price-block, span.price")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # WILLHABEN
        elif "willhaben.at" in url:
            oglasi = await page.query_selector_all("article[data-testid='ad-card']")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3, span[data-testid='ad-title']")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.willhaben.at" + link
                    cena_el = await oglas.query_selector("span[data-testid='price']")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # AUTOSCOUT24
        elif "autoscout24" in url:
            oglasi = await page.query_selector_all("article.cldt-summary-full-item, div[data-item-name='listing']")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h2, a.cldt-summary-titles")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.autoscout24.com" + link
                    cena_el = await oglas.query_selector("span.cldt-price, p.price")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        # HALO OGLASI
        elif "halooglasi.com" in url:
            oglasi = await page.query_selector_all("div.offer-body, article.classified")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h3, h2, a.offer-title")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.halooglasi.com" + link
                    cena_el = await oglas.query_selector("div.price-box, span.price")
                    cena = await cena_el.inner_text() if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), cena.strip(), link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        else:
            # GENERICNI SCRAPER za neznane portale
            print(f"  ⚠️  Portal ni v seznamu — poskusam generično...")
            oglasi = await page.query_selector_all("article, div.item, li.ad, div.ad-item")
            for oglas in oglasi[:10]:
                try:
                    naslov_el = await oglas.query_selector("h2, h3, h4")
                    link_el = await oglas.query_selector("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = await naslov_el.inner_text()
                    link = await link_el.get_attribute("href")
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov.strip(), "Preveri oglas", link, portal, ime)
                        novi += 1
                        await asyncio.sleep(1)
                except:
                    continue

        shrani_videne(videni)
        print(f"  ✅ {portal}: {novi} novih oglasov")

    except Exception as e:
        print(f"  ❌ Napaka pri {portal}: {e}")

# ============================================
# GLAVNI PROGRAM
# ============================================
async def main():
    print("=" * 50)
    print("🚀 OglasIQ se zaganja...")
    print("=" * 50)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        zadnje_preverjanje = {}

        while True:
            iskanja = nalozi_iskanja()
            cas_zdaj = asyncio.get_event_loop().time()

            print(f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            print(f"📋 Naloženih iskanj: {len(iskanja)}")

            for iskanje in iskanja:
                if not iskanje.get("aktiven", True):
                    continue

                iid = iskanje.get("id", 0)
                paket = iskanje.get("paket", "free")
                interval = INTERVALI.get(paket, INTERVALI["free"])
                zadnje = zadnje_preverjanje.get(iid, 0)

                if cas_zdaj - zadnje >= interval:
                    context = await browser.new_context(
                        user_agent=random.choice(USER_AGENTS),
                        viewport={"width": 1920, "height": 1080},
                        locale="sl-SI",
                        extra_http_headers={
                            "Accept-Language": "sl-SI,sl;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                        }
                    )
                    page = await context.new_page()

                    await preveri_url(page, iskanje)
                    zadnje_preverjanje[iid] = cas_zdaj

                    await context.close()
                    await asyncio.sleep(random.uniform(3, 7))
                else:
                    preostalo = int(interval - (cas_zdaj - zadnje))
                    minute = preostalo // 60
                    print(f"  ⏳ Iskanje {iid}: naslednje čez {minute} min")

            print("\n💤 Čakam 5 minut do naslednjega cikla...")
            await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())