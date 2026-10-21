"""BeClass 線上報名系統「幼兒/親子」分類（range=Z），台北、新北、桃園。robots.txt 全站允許；每次請求間隔 1.5 秒。
列表頁給活動日期，詳細頁給時間、地點、費用、報名期限與名額。"""
import re, html, time, urllib.request
from datetime import datetime, timedelta, timezone
from .common import _CTX, UA, is_family, categorize, city_of
NAME = "beclass"
LABEL = "BeClass 線上報名（幼兒/親子，全台）"
LIST = "https://www.beclass.com/default.php?name=ShowList&op=catRank&range=Z&hotrank=&xarea={area}&page={page}"
AREAS = {"台北": "臺北市", "新北": "新北市", "": None}  # 先雙北，再全台（其餘縣市由地址判斷）
MAX_PAGES, MAX_DETAIL, HORIZON = 10, 150, 60
TZ = timezone(timedelta(hours=8))
ADULT = r"限家長|親職講座|母乳|哺乳|哺餵|品茗|口腔動作訓練|社區大學|親職教育|教保服務|教保員|研習|說明會|招募|志工|義工|講師培訓|師資|證照|員工|徵才|會員大會|理監事|問事|法會|灌頂"
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def _get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def fetch(today):
    items, seen = [], set()
    for area, city in AREAS.items():
        for page in range(1, MAX_PAGES + 1):
            time.sleep(1.5)
            h = _get(LIST.format(area=urllib.request.quote(area), page=page))
            i = h.find("頁次"); seg = h[i:]
            got = re.findall(r'href="(https://www\.beclass\.com/rid=\w+)"[^>]*>([\s\S]{0,400}?)</a>', seg)
            n = 0
            for u, t in got:
                tt = _t(t); m = re.search(r"\((\d{4}-\d{2}-\d{2})\)\s*$", tt)
                if not m or u in seen: continue
                seen.add(u); n += 1
                d = m.group(1); title = tt[: m.start()].strip()
                if d < today.isoformat() or d > (today + timedelta(days=HORIZON)).isoformat(): continue
                items.append((u, title, d, city))
            if n == 0 or f"page={page + 1}" not in h: break
    out = []
    for u, title, d, city in items[:MAX_DETAIL]:
        if re.search(ADULT, title): continue
        time.sleep(1.5)
        try: h = _get(u)
        except Exception as ex: print("beclass detail fail", u, ex); continue
        og = re.search(r'<meta property="og:description" content="([^"]*)"', h); desc = html.unescape(og.group(1)) if og else ""
        ogt = re.search(r'<meta property="og:title" content="([^"]*)"', h); tags = html.unescape(ogt.group(1)) if ogt else ""
        body = _t(re.sub(r"<(script|style)[\s\S]*?</\1>", "", h))
        ms = re.search(r"活動說明([\s\S]{0,3000}?)(?:活動地點資訊|報名前預先登入)", body)
        if ms and len(_t(ms.group(1))) > len(desc) * 0.5: desc = _t(ms.group(1)).replace("活動官網", " ")
        if not is_family(title + " " + desc, title) and "幼兒/親子" not in tags: continue
        if re.search(ADULT, desc[:200]) and not re.search(r"親子|兒童|孩子|幼兒", title): continue
        tm = re.search(r"(?:時間|時段)\s*[:：]\s*(上午|下午|晚上)?\s*(\d{1,2})[:：](\d{2})(?:\s*[-~～至]\s*(?:上午|下午|晚上)?\s*(\d{1,2})[:：](\d{2}))?", desc)
        t1 = t2 = ""
        if tm:
            h1 = int(tm.group(2)); h1 += 12 if tm.group(1) in ("下午", "晚上") and h1 < 12 else 0; t1 = f"{h1:02d}:{tm.group(3)}"
            if tm.group(4):
                h2 = int(tm.group(4)); h2 += 12 if h2 < h1 else 0; t2 = f"{h2:02d}:{tm.group(5)}"
        loc = re.search(r"(?:活動)?地點\s*[:：]\s*([^。\n]{2,40}?)(?=\s*(?:費用|對象|時間|日期|名額|報名|聯絡|有任何|※|$))", desc)
        venue = loc.group(1).strip(" ，,") if loc else ""
        lv = re.search(r"活動地點資訊\s*地點\s*[:：]\s*(.{2,60}?)\s*(?:顯示地圖|報名前)", body)
        address = lv.group(1).strip() if lv else ""
        if not venue: venue = re.sub(r"\s*\(.*$", "", address)
        pq = re.search(r"\(報名期限([\d.]+)\s*天([^)]*)\)", body)
        qa = re.search(r"限額(\d+)名", pq.group(2)) if pq else None
        ql = re.search(r"尚餘(\d+)人", pq.group(2)) if pq else None
        reg_end = (datetime.now(TZ) + timedelta(days=float(pq.group(1)))).strftime("%Y-%m-%d") if pq else ""
        full = "已額滿" in body or "報名已截止" in body
        # 活動結束日：介紹中明列的最後一個日期（給後處理展開成多場）
        last = d
        for mo, da in re.findall(r"(\d{1,2})\s*/\s*(\d{1,2})", desc):
            try:
                y = int(d[:4]); cand = datetime(y, int(mo), int(da)).date()
                if cand.isoformat() < d: cand = datetime(y + 1, int(mo), int(da)).date()
                if cand.isoformat() > last and (cand - datetime.fromisoformat(d).date()).days <= 120: last = cand.isoformat()
            except ValueError: pass
        rg = re.search(r"(\d{1,2})/(\d{1,2})[^~～\d/]{0,6}[~～\-－]\s*(\d{1,2})/(\d{1,2})", title)
        start = d
        if rg:
            try:
                y = int(d[:4]); a = datetime(y, int(rg.group(1)), int(rg.group(2))).date()
                if a.isoformat() > d: a = datetime(y - 1, a.month, a.day).date()
                if (datetime.fromisoformat(d).date() - a).days <= 62:
                    start = max(a, today).isoformat(); last = max(last, d)
            except ValueError: pass
        city = city or city_of(address + " " + venue + " " + title) or ""
        if not city: continue
        price = "免費" if "免費活動" in tags and not re.search(r"\d+\s*元", desc) else ""
        out.append({"id": "beclass:" + u.rsplit("=", 1)[1], "source": NAME, "title": title, "category": categorize(title + " " + desc[:200]),
            "start": start, "end": last,
            "sessions": [{"start": start + ("T" + t1 if t1 else ""), "end": (last + "T" + t2) if t2 else (last if last != start else ""),
                "venue": venue, "address": address, "lat": None, "lng": None,
                "quota": qa.group(1) if qa else "", "left": "0" if full else (ql.group(1) if ql else ""),
                "status": "額滿" if full else "", "regEnd": reg_end, "regStart": ""}],
            "sessionCount": 1, "city": city, "district": "", "venue": venue, "address": address, "lat": None, "lng": None,
            "free": None, "price": price, "priceText": desc, "organizer": "", "description": desc[:500], "image": "",
            "ticketUrl": "", "registrationUrl": u, "url": u, "needsRegistration": True, "updatedAt": ""})
    return out
