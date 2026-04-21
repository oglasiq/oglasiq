import json
import os
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

TELEGRAM_TOKEN = "8522586477:AAE0tasQkHhHGZs8b0m5WtEWor-6J6NUUmw"
TELEGRAM_CHAT_ID = "1123416623"

VIDENI_OGLASI_FILE = "/tmp/videni_oglasi.json"
API_URL = "https://clever-beauty-production-3d95.up.railway.app"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"},
]

INTERVALI = {
    "free": 24 * 60 * 60,
    "starter": 3 * 60 * 60,
    "pro": 60 * 60,
    "premium": 20 * 60,
}

def nalozi_videne():
    if os.path.exists(VIDENI_OGLASI_FILE):
        with open(VIDENI_OGLASI_FILE, "r") as f:
            return json.load(f)
    return []

def shrani_videne(videni):
    with open(VIDENI_OGLASI_FILE, "w") as f:
        json.dump(videni, f)

def nalozi_iskanja():
    try:
        r = requests.get(f"{API_URL}/iskanja", timeout=10)
        if r.status_code == 200:
            iskanja = r.json()
            print(f"  ✅ Naloženih {len(iskanja)} iskanj iz API")
            return iskanja
        else:
            print(f"  ❌ API napaka: {r.status_code}")
            return []
    except Exception as e:
        print(f"  ❌ Ne morem doseči API: {e}")
        return []

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
        "mobile.de": "🇩🇪 Mobile.de",
        "autoscout24": "🇩🇪 AutoScout24",
        "willhaben.at": "🇦🇹 Willhaben",
        "subito.it": "🇮🇹 Subito.it",
    }
    for kljuc, ime in portali.items():
        if kljuc in url.lower():
            return ime
    return "🌐 Portal"

def poslji_telegram(naslov, cena, link, portal, iskanje_ime=""):
    cas = datetime.now().strftime("%H:%M")
    sporocilo = (
        f"🔔 <b>Nov oglas — OglasIQ</b>\n\n"
        f"📋 {naslov}\n"
        f"💰 {cena}\n"
        f"🌐 {portal}\n"
        f"🕐 {cas}\n"
    )
    if iskanje_ime:
        sporocilo += f"🔍 {iskanje_ime}\n"
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

def fetch_url(url):
    headers = random.choice(HEADERS_LIST).copy()
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    headers["Accept-Language"] = "sl-SI,sl;q=0.9,en;q=0.8"
    r = requests.get(url, headers=headers, timeout=15)
    return BeautifulSoup(r.content, "html.parser")

def preveri_url(iskanje):
    urls = iskanje.get("urls", [])
    if not urls:
        url = iskanje.get("url", "")
        if url:
            urls = [url]

    ime = iskanje.get("ime", "")

    for url in urls:
        if not url:
            continue

        portal = zazna_portal(url)
        print(f"\n🔍 Preverjam: {portal}")
        print(f"   URL: {url[:60]}...")

        try:
            soup = fetch_url(url)
            videni = nalozi_videne()
            novi = 0

            if "bolha.com" in url:
                oglasi = soup.select("article.entity-body")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("h3.entity-title a")
                    if not naslov_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = naslov_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.bolha.com" + link
                    cena_el = oglas.select_one("strong.price-box")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            elif "nepremicnine.net" in url:
                oglasi = soup.select("div.oglas_container")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("span.title")
                    link_el = oglas.select_one("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = link_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.nepremicnine.net" + link
                    cena_el = oglas.select_one("strong.price-box")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            elif "avto.net" in url:
                oglasi = soup.select("div.GO-Results-Row")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("div.GO-Results-Naziv")
                    link_el = oglas.select_one("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = link_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.avto.net" + link
                    cena_el = oglas.select_one("div.GO-Results-Cena")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            elif "njuskalo.hr" in url:
                oglasi = soup.select("li.EntityList-item")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("h3.entity-title a")
                    if not naslov_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = naslov_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.njuskalo.hr" + link
                    cena_el = oglas.select_one("strong.price-box")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            elif "olx." in url:
                oglasi = soup.select("div[data-cy='l-card'], li[data-cy='l-card']")
                if not oglasi:
                    oglasi = soup.select("div.item-box")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("h3, h4, p[data-cy='ad-card-title']")
                    link_el = oglas.select_one("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = link_el.get("href", "")
                    if link and not link.startswith("http"):
                        base = url.split("/")[0] + "//" + url.split("/")[2]
                        link = base + link
                    cena_el = oglas.select_one("p[data-testid='ad-price'], div.price")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            elif "mobile.de" in url:
                oglasi = soup.select("div.cBox-body--resultitem, article.cBox")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("span.h3-headline, div.headline-block")
                    link_el = oglas.select_one("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = link_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.mobile.de" + link
                    cena_el = oglas.select_one("div.price-block, span.price-unit")
                    cena = cena_el.get_text(strip=True) if cena_el else "Cena ni navedena"
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, cena, link, portal, ime)
                        novi += 1

            else:
                oglasi = soup.select("article, div.item, li.ad")
                for oglas in oglasi[:10]:
                    naslov_el = oglas.select_one("h2, h3, h4")
                    link_el = oglas.select_one("a")
                    if not naslov_el or not link_el:
                        continue
                    naslov = naslov_el.get_text(strip=True)
                    link = link_el.get("href", "")
                    if link and link not in videni:
                        videni.append(link)
                        poslji_telegram(naslov, "Preveri oglas", link, portal, ime)
                        novi += 1

            shrani_videne(videni)
            print(f"  ✅ {portal}: {novi} novih oglasov")

        except Exception as e:
            print(f"  ❌ Napaka pri {portal}: {e}")

        time.sleep(random.uniform(2, 5))

def main():
    print("=" * 50)
    print("🚀 OglasIQ se zaganja...")
    print("=" * 50)

    zadnje_preverjanje = {}

    while True:
        iskanja = nalozi_iskanja()
        cas_zdaj = time.time()

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
                preveri_url(iskanje)
                zadnje_preverjanje[iid] = cas_zdaj
                time.sleep(random.uniform(3, 7))
            else:
                preostalo = int(interval - (cas_zdaj - zadnje))
                minute = preostalo // 60
                print(f"  ⏳ Iskanje {iid}: čez {minute} min")

        print("\n💤 Čakam 5 minut...")
        time.sleep(300)

if __name__ == "__main__":
    main()