"""新北市政府資料開放平臺：新北市活動訊息。授權：政府資料開放授權條款。"""
import re
from datetime import datetime
from .common import fetch_json, is_family, categorize, city_of, district_of, free_of, norm
NAME = "ntpc"
LABEL = "新北市政府活動"
URL = "https://data.ntpc.gov.tw/api/datasets/029e3fc2-1927-4534-8702-da7323be969b/json?size=1000"
def _d(s):
    try: return datetime.strptime(s.strip(), "%m/%d/%Y").date()
    except Exception: return None
def _time(desc):
    m = re.search(r"(上午|下午|晚上)?\s*(\d{1,2})[:：](\d{2})", desc)
    if not m: return ""
    h = int(m.group(2))
    if m.group(1) in ("下午","晚上") and h < 12: h += 12
    return f"{h:02d}:{m.group(3)}"
def fetch(today):
    out = []
    for page in range(0, 5):
        rows = fetch_json(URL + f"&page={page}")
        if not rows: break
        for x in rows:
            title = (x.get("title") or "").strip(); desc = x.get("description") or ""
            if not is_family(title + " " + desc[:600], title): continue
            st, en = _d(x.get("activeDate","")), _d(x.get("activeEndDate","")) 
            if not st: continue
            en = en or st
            if en < today: continue
            t = _time(desc)
            addr = norm(x.get("address") or ""); place = (x.get("place") or "").strip()
            city = city_of(addr, place, title) or "新北市"
            m = re.search(r"https?://[^\s，。）)]+", desc)
            reg = m.group(0) if (m and "報名" in desc) else ""
            out.append({"id": f"ntpc:{x.get('id')}", "source": NAME, "title": title,
                "category": categorize(title + " " + desc[:200]), "start": st.isoformat(), "end": en.isoformat(),
                "sessions": [{"start": st.isoformat() + ("T"+t if t else ""), "end": en.isoformat() if en > st else "", "venue": place, "address": addr, "lat": None, "lng": None}],
                "sessionCount": 1, "city": city, "district": district_of(addr, city), "venue": place, "address": addr,
                "lat": None, "lng": None, "free": free_of((x.get("money") or "") + " " + desc), "price": (x.get("money") or "")[:120],
                "organizer": (x.get("author") or "").strip()[:60], "description": desc[:400], "image": x.get("picUrl") or "",
                "ticketUrl": "", "registrationUrl": reg, "url": (x.get("aboutUrl") or "").strip(),
                "needsRegistration": ("須報名" in desc or "需報名" in desc or "請報名" in desc or "報名網址" in desc) and "無須報名" not in desc and "免報名" not in desc,
                "updatedAt": x.get("modifiedDate") or ""})
        if len(rows) < 1000: break
    return out
