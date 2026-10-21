"""臺北客家農場（臺北市客家文化主題公園官網「客家農場」活動）。農活時節日等親子食農體驗，含時間、地點、費用。
robots.txt 全站允許；列表頁取時間/地點/費用，每次請求間隔 2 秒。"""
import re, html, time, urllib.request
from .common import _CTX, UA, is_family, categorize
NAME = "thcpfarm"
LABEL = "臺北客家農場 農活時節日"
LIST = "https://ssl.thcp.org.tw/events?category=%E5%AE%A2%E5%AE%B6%E8%BE%B2%E5%A0%B4&page={p}"
ADDR = "臺北市中正區汀州路3段2號"
def _get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def _t(s): return re.sub(r"[ \t\xa0]+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()
def fetch(today):
    out, seen = [], set()
    for p in range(1, 4):
        h = _get(LIST.format(p=p)); n = 0
        for m in re.finditer(r'feed-list-date">(\d{4})-\d\d-\d\d</div>\s*<div class="feed-list-title"><a href="(https://ssl\.thcp\.org\.tw/events/(\d+))">([^<]+)</a></div>\s*<div class="feed-list-content">([\s\S]*?)</div>', h):
            y, url, eid, title, body = int(m.group(1)), m.group(2), m.group(3), _t(m.group(4)), _t(m.group(5))
            if eid in seen: continue
            seen.add(eid); n += 1
            tm = re.search(r"時間\s*[:：]\s*(\d{1,2})/(\d{1,2})\D{0,5}?(\d{1,2}:\d{2})\s*[-~～]\s*(\d{1,2}:\d{2})", body) or \
                 re.search(r"(\d{1,2})/(\d{1,2})\([一二三四五六日]\)\s*(\d{1,2}:\d{2})\s*[-~～]\s*(\d{1,2}:\d{2})", title)
            if not tm: continue
            mo, da = int(tm.group(1)), int(tm.group(2))
            d = f"{y}-{mo:02d}-{da:02d}"
            if (today - __import__("datetime").date(y, mo, da)).days > 180: d = f"{y + 1}-{mo:02d}-{da:02d}"
            if d < today.isoformat(): continue
            if not (is_family(title + " " + body, title) or re.search(r"親子|6歲以上|未滿15歲|大小朋友|繪本", body + title)): continue
            fee = re.search(r"費用\s*[:：]\s*([^\n■]{1,60})", body)
            place = re.search(r"地點\s*[:：]\s*([^\n■]{1,30})", body)
            venue = "臺北市客家文化主題公園 " + (place.group(1).strip() if place else "客家農場")
            clean = re.sub(r"^【臺北客家農場】115年度農活時節日計畫-[^-]*-[^-]*-", "", title)
            out.append({"id": "thcpfarm:" + eid, "source": NAME, "title": "【臺北客家農場】" + clean if clean != title else title,
                "category": categorize(title + " " + body), "start": d, "end": d,
                "sessions": [{"start": f"{d}T{tm.group(3).zfill(5)}", "end": f"{d}T{tm.group(4).zfill(5)}", "venue": venue, "address": ADDR, "lat": None, "lng": None}],
                "sessionCount": 1, "city": "臺北市", "district": "中正區", "venue": venue, "address": ADDR, "lat": None, "lng": None,
                "free": None, "price": fee.group(1).strip() if fee else "", "priceText": body, "organizer": "財團法人台北市客家文化基金會",
                "description": body[:500], "image": "", "ticketUrl": "", "registrationUrl": url, "url": url, "needsRegistration": True, "updatedAt": ""})
        if n == 0 or f"page={p + 1}" not in h: break
        time.sleep(2)
    return out
