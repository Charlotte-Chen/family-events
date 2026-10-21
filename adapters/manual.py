"""手動加入的活動（data/manual.json）：使用者從 FB／Threads／IG 截圖等提供、官網核對過的活動。
每天建置時一併合併，不會被每日更新覆蓋。欄位：id, title, date（或 start_date/end_date）, start, end, venue, address, city, district,
price, free, organizer, url, registrationUrl, needsRegistration, regEnd, quota, topics, description。"""
import json, os
NAME = "manual"
LABEL = "手動加入"
PATH = os.path.join(os.path.dirname(__file__), "..", "data", "manual.json")
def fetch(today):
    out = []
    for m in json.load(open(PATH, encoding="utf-8")):
        sd = m.get("start_date") or m["date"]; ed = m.get("end_date") or m.get("date") or sd
        if ed < today.isoformat(): continue
        st, et = m.get("start", ""), m.get("end", "")
        sess = {"start": sd + (f"T{st}" if st else ""), "end": ed + (f"T{et}" if et else ("" if ed == sd else "")),
                "venue": m.get("venue", ""), "address": m.get("address", ""), "lat": None, "lng": None}
        for k in ("regEnd", "quota", "left"):
            if m.get(k): sess[k] = m[k]
        out.append({"id": "manual:" + m["id"], "source": NAME, "title": m["title"], "category": m.get("category", "other"),
            "start": sd, "end": ed, "sessions": [sess], "sessionCount": 1, "city": m.get("city", ""), "district": m.get("district", ""),
            "venue": m.get("venue", ""), "address": m.get("address", ""), "lat": None, "lng": None,
            "free": m.get("free"), "price": m.get("price", ""), "priceText": m.get("price", ""), "organizer": m.get("organizer", ""),
            "description": m.get("description", ""), "image": "", "ticketUrl": "", "registrationUrl": m.get("registrationUrl", ""),
            "url": m.get("url", ""), "needsRegistration": bool(m.get("needsRegistration")), "topicsHint": m.get("topics", []), "updatedAt": ""})
    return out
