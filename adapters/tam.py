"""臺北市立天文科學教育館「活動報名總覽」與各活動頁（星姊姊說故事等）。"""
import re, html, time, urllib.request
from datetime import date
from .common import _CTX, UA, categorize
NAME = "tam"
LABEL = "臺北市立天文科學教育館 活動報名"
LIST = "https://tam.gov.taipei/News.aspx?n=0258A8C5F361FF53&sms=C859FAFAA10995CD"
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def _get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def _roc(s):
    m = re.match(r"(\d{2,3})[/-](\d{1,2})[/-](\d{1,2})", s.strip())
    return date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3))) if m else None
def fetch(today):
    h = _get(LIST); out = []
    links = re.findall(r'<a href="(https://tam\.gov\.taipei/Active_Content\.aspx\?[^"]+)" title="([^"]+)"', h)
    for u, ttl in dict.fromkeys(links):
        time.sleep(1.2)
        try: p = _get(html.unescape(u))
        except Exception as ex: print("tam fail", u, ex); continue
        body = re.sub(r"<(script|style)[\s\S]*?</\1>", "", p)
        tx = _t(body)
        nm = re.search(r"<h3[^>]*>([\s\S]*?)</h3>", body); name = _t(nm.group(1)) if nm else _t(ttl)
        reg = re.search(r"報名日期[:：]\s*([\d/]+)\s*[~～-]\s*([\d/]+)", tx)
        rs, re_ = (_roc(reg.group(1)), _roc(reg.group(2))) if reg else (None, None)
        sess = []
        for m in re.finditer(r"(\d{1,2})月(\d{1,2})日\s*[（(][一二三四五六日][）)]\s*(\d{1,2}:\d{2})\s*[-~～]\s*(\d{1,2}:\d{2})", tx):
            y = today.year if int(m.group(1)) >= today.month - 1 else today.year + 1
            try: d = date(y, int(m.group(1)), int(m.group(2)))
            except ValueError: continue
            if d < today: continue
            sess.append({"start": f"{d}T{int(m.group(3).split(':')[0]):02d}:{m.group(3).split(':')[1]}", "end": f"{d}T{int(m.group(4).split(':')[0]):02d}:{m.group(4).split(':')[1]}",
                "venue": "臺北市立天文科學教育館", "address": "臺北市士林區基河路363號", "lat": 25.0957, "lng": 121.5185,
                "regStart": rs.isoformat() if rs else "", "regEnd": re_.isoformat() if re_ else ""})
        if not sess: continue
        loc = re.search(r"活動地點[:：]\s*([^。\s]{2,30})", tx); aud = re.search(r"活動對象[:：]\s*([^。]{2,80})", tx)
        for s in sess:
            if loc: s["venue"] = "天文館 " + loc.group(1)
        desc = (("對象：" + aud.group(1) + "。") if aud else "") + tx[tx.find(name) + len(name):][:400] if name in tx else ""
        out.append({"id": "tam:" + re.search(r"ss=(\w+)", u).group(1), "source": NAME, "title": name, "category": categorize(name + desc),
            "start": sess[0]["start"][:10], "end": sess[-1]["start"][:10], "sessions": sess, "sessionCount": len(sess),
            "city": "臺北市", "district": "士林區", "venue": sess[0]["venue"], "address": "臺北市士林區基河路363號", "lat": 25.0957, "lng": 121.5185,
            "free": None, "price": "", "priceText": tx[tx.find(name):][:3000] if name in tx else "", "organizer": "臺北市立天文科學教育館", "description": desc,
            "image": "", "ticketUrl": "", "registrationUrl": html.unescape(u).replace("Active_Content", "Active_Content"), "url": html.unescape(u),
            "needsRegistration": True, "tags": ["天文", "科學"], "updatedAt": ""})
    return out
