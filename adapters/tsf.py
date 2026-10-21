"""臺灣科學節（教育部、國科會主辦；官網 tsf.moe.edu.tw）活動總覽。
官網前端使用的公開 JSON（tsfapi.nmmba.gov.tw/webapi/main/2）一次給全部活動：場次日期/時間/地點、費用、對象、區域。
只抓 1 次請求；排除論壇研討、科學競賽與限國高中以上的活動。"""
import re, json, html, urllib.request
from datetime import date
from .common import _CTX, UA, city_of, categorize
NAME = "tsf"
LABEL = "臺灣科學節 活動總覽"
API = "https://tsfapi.nmmba.gov.tw/webapi/main/2?year={y}&lang=zh"
SKIP_CAT = {"main/2/14", "main/2/21"}  # 論壇及研討會、科學競賽
ADULT = r"18歲以上|國中\(含以上\)|高中|大專|教師研習|教師|研討|論壇|辯論"
VMAP = [(r"科教館|科學教育館|天文館|兒童新樂園", "臺北市"), (r"海洋科技|海科館|八斗子", "基隆市"), (r"自然科學博物館|科博館", "臺中市"), (r"科學工藝|科工館", "高雄市"), (r"海洋生物|海生館|車城", "屏東縣")]
AREA = {"北": "臺北市", "中": "臺中市", "南": "高雄市", "東": "花蓮縣"}
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def fetch(today):
    req = urllib.request.Request(API.format(y=today.year), data=b"", method="POST",
                                 headers={**UA, "Origin": "https://tsf.moe.edu.tw", "Referer": "https://tsf.moe.edu.tw/"})
    d = json.loads(urllib.request.urlopen(req, timeout=90, context=_CTX).read().decode("utf-8"))["data"]
    out = []
    for e in d.get("list") or []:
        if e.get("type") != "event" or e.get("category_url") in SKIP_CAT: continue
        title = (e.get("title") or "").strip(); target = e.get("target") or ""
        if re.search(ADULT, title + " " + target): continue
        content = e.get("content") or ""; desc = _t(content)
        sess = []
        for s in e.get("schedule") or []:
            ds = re.findall(r"\d{4}/\d{2}/\d{2}", s.get("date") or "")
            if not ds: continue
            a, b = ds[0].replace("/", "-"), ds[-1].replace("/", "-")
            if b < today.isoformat(): continue
            st, et = (s.get("st_time") or "").strip(), (s.get("ed_time") or "").strip()
            addr = (s.get("addr") or "").strip()
            sess.append({"start": a + (f"T{st}" if re.match(r"\d\d:\d\d", st) else ""),
                         "end": (b + (f"T{et}" if re.match(r"\d\d:\d\d", et) else "")) if (b != a or re.match(r"\d\d:\d\d", et)) else "",
                         "venue": addr, "address": "", "lat": None, "lng": None, "name": (s.get("memo") or "").strip()[:40]})
        if not sess: continue
        venue = sess[0]["venue"]
        area = (e.get("area") or [""])[0] if isinstance(e.get("area"), list) else ""
        city = city_of(venue) or next((c for rx, c in VMAP if re.search(rx, venue + title)), "") or city_of(desc[:200]) or AREA.get(area, "")
        fee = (e.get("fee") or "").strip()
        price = "免費" if fee == "免費" else ("免費（須購買入館門票）" if fee.startswith("免費(") else (fee if re.search(r"\d", fee) else ""))
        links = re.findall(r'href="(https?://[^"]+)"[^>]*>([\s\S]{0,60}?)</a>', content)
        reg = next((u for u, t in links if re.search(r"報名|預約|購票|forms|reurl|accupass|beclass", u + _t(t))), "")
        need = bool(reg) or bool(re.search(r"報名|預約", desc))
        url = "https://tsf.moe.edu.tw/" + (e.get("url") or "").lstrip("/")
        out.append({"id": "tsf:" + (e.get("url") or title).split("/")[-1], "source": NAME, "title": title,
            "category": categorize(title + " " + desc), "start": min(x["start"][:10] for x in sess), "end": max((x["end"] or x["start"])[:10] for x in sess),
            "sessions": sess, "sessionCount": len(sess), "city": city, "district": "", "venue": venue, "address": "", "lat": None, "lng": None,
            "free": True if price.startswith("免費") else None, "price": price, "priceText": fee + " " + desc[:400],
            "organizer": "臺灣科學節", "description": ("對象：" + target + "。" if target else "") + desc[:500], "image": e.get("image") or "",
            "ticketUrl": "", "registrationUrl": reg, "url": url, "needsRegistration": need, "topicsHint": ["科學"], "updatedAt": ""})
    return out
