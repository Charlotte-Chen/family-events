"""新北市政府農業局「新北數位食農集章護照」活動總覽（agriculture-dfapass.ntpc.gov.tw/events）。
農業局粉專「稼日蒔光」的活動也彙整在這個官方平台。robots.txt 全站允許；列表頁伺服器端輸出的 Nuxt 資料。
只收有親子體驗內容（DIY、採收、闖關、兒童、食農體驗）的活動。"""
import re, json, html, time, urllib.request
from datetime import datetime, timedelta, timezone
from .common import _CTX, UA, categorize
NAME = "ntpcagri"
LABEL = "新北市農業局 食農護照活動（稼日蒔光）"
BASE = "https://www.agriculture-dfapass.ntpc.gov.tw"
TZ = timezone(timedelta(hours=8))
KIDS = r"親子|兒童|孩子|小朋友|大小朋友|DIY|手作|採收|採摘|闖關|體驗|食農"
def _get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def _devalue(arr):
    memo = {}
    def r(i):
        if not isinstance(i, int) or i < 0: return i
        if i in memo: return memo[i]
        v = arr[i]
        if isinstance(v, list):
            if v and isinstance(v[0], str) and v[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"): out = r(v[1])
            else: out = [r(x) for x in v]
        elif isinstance(v, dict): out = {k: r(x) for k, x in v.items()}
        else: out = v
        memo[i] = out; return out
    return r(0)
def _local(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(TZ)
def fetch(today):
    out, seen = [], set()
    for page in range(1, 6):
        h = _get(f"{BASE}/events" + (f"?page={page}" if page > 1 else ""))
        m = re.search(r'id="__NUXT_DATA__"[^>]*>([\s\S]*?)</script>', h)
        data = _devalue(json.loads(m.group(1)))["data"]
        recs = next((v for v in data.values() if isinstance(v, dict) and "Body" in v), None)
        body = (recs or {}).get("Body") or []
        new = 0
        for r in body:
            eid = r["StampEventId"]
            if eid in seen: continue
            seen.add(eid); new += 1
            s, e = _local(r["StartDateTime"]), _local(r["EndDateTime"])
            if e.date() < today: continue
            txt = re.sub(r"\*\*", "", html.unescape(re.sub(r"<[^>]+>", " ", r.get("Content") or "")))
            txt = re.sub(r"\s+", " ", txt).strip()
            title = r["Name"].strip()
            if not re.search(KIDS, title + txt): continue
            tm = re.search(r"(\d{1,2})[:：](\d{2})\s*[-－~～至]\s*(\d{1,2})[:：](\d{2})", txt)
            if not tm:
                t2 = re.search(r"(上午|下午)?\s*(\d{1,2})時\s*至\s*(上午|下午)?\s*(\d{1,2})時", txt)
                t1h = t2h = None
                if t2:
                    a = int(t2.group(2)) + (12 if t2.group(1) == "下午" and int(t2.group(2)) < 12 else 0)
                    b = int(t2.group(4)) + (12 if (t2.group(3) or t2.group(1)) == "下午" and int(t2.group(4)) < 12 else 0)
                    t1h, t2h = f"{a:02d}:00", f"{b:02d}:00"
            else:
                t1h, t2h = f"{int(tm.group(1)):02d}:{tm.group(2)}", f"{int(tm.group(3)):02d}:{tm.group(4)}"
            loc = re.search(r"(?:活動地點|地點)\s*[:：]?\s*([^。；;]{3,60}?)(?=\s*(?:活動簡介|活動日期|活動期間|。|；|;|$))", txt) or re.search(r"在\s*([^，。]{3,40}?(?:\([^)]*\)|（[^）]*）))\s*登場", txt)
            venue = (loc.group(1).strip() if loc else "") or (r.get("DistrictName") or "")
            sd, ed = s.date().isoformat(), e.date().isoformat()
            sess = {"start": sd + ("T" + t1h if t1h else ""), "end": ed + ("T" + t2h if t2h else ""),
                    "venue": venue, "address": "", "lat": None, "lng": None}
            out.append({"id": "ntpcagri:" + eid, "source": NAME, "title": title, "category": categorize(title + " " + txt),
                "start": sd, "end": ed, "sessions": [sess], "sessionCount": 1, "city": "新北市", "district": r.get("DistrictName") or "",
                "venue": venue, "address": "", "lat": None, "lng": None, "free": None, "price": "", "priceText": txt,
                "organizer": "新北市政府農業局", "description": txt[:500], "image": r.get("DefaultImageUrl") or "", "ticketUrl": "",
                "registrationUrl": "", "url": f"{BASE}/events/{eid}", "needsRegistration": False, "updatedAt": ""})
        if new == 0 or len(seen) >= int((recs or {}).get("Total") or 0): break
        time.sleep(2)
    return out
