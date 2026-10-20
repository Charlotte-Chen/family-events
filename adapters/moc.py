"""文化部文化資料開放服務網：藝文活動（全部類別）。授權：政府資料開放授權條款第1版。"""
from datetime import datetime
from .common import fetch_json, is_family, categorize, city_of, district_of, free_of, norm
NAME = "moc"
LABEL = "文化部藝文活動"
URL = "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all"
URL_KIDS = "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=4"
def _dt(s):
    try: return datetime.strptime(s.strip(), "%Y/%m/%d %H:%M:%S")
    except Exception: return None
def fetch(today):
    out = []
    rows = {}
    for x in fetch_json(URL_KIDS): x["category"] = "4"; rows[x["UID"]] = x   # 親子類：全部收錄，不做關鍵字篩選
    for x in fetch_json(URL): rows.setdefault(x["UID"], x)
    for x in rows.values():
        title = (x.get("title") or "").strip()
        desc = x.get("descriptionFilterHtml") or ""
        text = title + " " + desc[:600]
        if not (x.get("category") == "4" or is_family(text, title)): continue
        sessions = []
        for s in x.get("showInfo") or []:
            st, en = _dt(s.get("time","")), _dt(s.get("endTime",""))
            if not st: continue
            if (en or st).date() < today: continue
            sessions.append({"start": st.strftime("%Y-%m-%dT%H:%M"), "end": en.strftime("%Y-%m-%dT%H:%M") if en else "",
                "venue": (s.get("locationName") or "").strip(), "address": norm(s.get("location") or "").strip(),
                "lat": float(s["latitude"]) if s.get("latitude") else None, "lng": float(s["longitude"]) if s.get("longitude") else None,
                "price": (s.get("price") or "").strip(), "onSales": s.get("onSales")})
        if not sessions:
            # 沒有場次但整體日期有效
            try:
                e = datetime.strptime(x.get("endDate",""), "%Y/%m/%d").date()
                if e < today: continue
            except Exception: continue
            continue
        sessions.sort(key=lambda s: s["start"])
        f = sessions[0]
        city = city_of(f["address"], f["venue"])
        price = f["price"]
        free = free_of(price + " " + desc[:300])
        if free is None and f.get("onSales") == "N" and not price: free = True
        if f.get("onSales") == "Y" and free is None: free = False
        ticket = (x.get("webSales") or "").strip()
        src = (x.get("sourceWebPromote") or "").strip()
        out.append({"id": f"moc:{x.get('UID')}", "source": NAME, "title": title,
            "category": categorize(title + " " + desc[:200]), "start": sessions[0]["start"][:10],
            "end": max((s["end"] or s["start"])[:10] for s in sessions),
            "sessions": [{k: s[k] for k in ("start","end","venue","address","lat","lng")} for s in sessions[:60]],
            "sessionCount": len(sessions), "city": city, "district": district_of(f["address"], city),
            "venue": f["venue"], "address": f["address"], "lat": f["lat"], "lng": f["lng"],
            "free": free, "price": price[:120], "organizer": (x.get("showUnit") or ",".join(x.get("masterUnit") or [])).strip()[:60],
            "description": desc[:400], "image": x.get("imageUrl") or "",
            "ticketUrl": ticket, "registrationUrl": "", "url": src or f"https://cloud.culture.tw/frontsite/inquiry/eventInquiryAction.do?method=showEventDetail&uid={x.get('UID')}",
            "updatedAt": (x.get("editModifyDate") or "")})
    return out
