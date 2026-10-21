"""國科會 Kiss Science（kissscience.tw）：Kids' Science 親子科學日、科學走讀。官網無 robots.txt 限制；每次請求間隔 2 秒。
只取官網明列的日期、時間、地點、費用與報名連結；主題標「科學」。"""
import re, html, time, urllib.request
from .common import _CTX, UA, city_of
NAME = "kissscience"
LABEL = "國科會 Kiss Science"
BASE = "https://kissscience.tw/"
KIDS = BASE + "motion.asp?siteid=100616&menuid=14388&lgid=1"
WALK = BASE + "motion.asp?siteid=100616&menuid=14389&lgid=1"
def _get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def _t(h):
    h = re.sub(r"<(script|style)[\s\S]*?</\1>", "", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).replace("\xa0", " ").strip()
def _ev(eid, title, d, t1, t2, venue, addr, price, url, reg, need, desc):
    return {"id": "kissscience:" + eid, "source": NAME, "title": title, "category": "other", "start": d, "end": d,
        "sessions": [{"start": f"{d}T{t1}" if t1 else d, "end": f"{d}T{t2}" if t2 else "", "venue": venue, "address": addr, "lat": None, "lng": None}],
        "sessionCount": 1, "city": city_of(addr, venue) or "", "district": "", "venue": venue, "address": addr, "lat": None, "lng": None,
        "free": True if price.startswith("免費") else None, "price": price, "priceText": price, "organizer": "國家科學及技術委員會",
        "description": desc[:500], "image": "", "ticketUrl": "", "registrationUrl": reg, "url": url, "needsRegistration": need,
        "topicsHint": ["科學"], "updatedAt": ""}
def fetch(today):
    out = []
    t = _t(_get(KIDS))
    m = re.search(r"活動時間\s*[:：]\s*(\d{4})/(\d{1,2})/(\d{1,2})\s*\([^)]*\)\s*(\d{1,2}:\d{2})\s*[~～-]\s*(\d{1,2}:\d{2})\s*活動地點\s*[:：]\s*(.+?)活動費用\s*[:：]\s*(\S+)", t)
    if m:
        d = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        loc = m.group(6).strip(); a = re.search(r"（([^）]+)）", loc)
        venue = re.sub(r"（[^）]*）", "", loc).strip(); addr = a.group(1) if a else ""
        if d >= today.isoformat():
            i = t.find("精彩活動"); desc = t[i:i + 600] if i >= 0 else ""
            sub = re.search(r"(\S{2,20})\s*活動時間", t)
            out.append(_ev("kids-" + d, "Kids' Science 親子科學日" + (f"：{sub.group(1)}" if sub else ""), d, m.group(4).zfill(5), m.group(5).zfill(5), venue, addr,
                           m.group(7), KIDS, "", False, "國科會 Kiss Science 親子科學活動。" + desc))
    time.sleep(2)
    h = _get(WALK); t = _t(h)
    free = "免費" if "免費開放" in t else ""
    regs = re.findall(r'href="([^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*立即報名', h)
    blocks = re.findall(r"(\S{2,30})\s+(\d{4})\.(\d{2})\.(\d{2})\s+[一二三四五六日]\s+集合地點\s+(\d{1,2}:\d{2})\s+(.+?)（([^）]+)）\s+參訪行程\s+(.+?)(?=立即報名)", t)
    for k, (title, y, mo, da, t1, place, addr, plan) in enumerate(blocks):
        d = f"{y}-{mo}-{da}"
        if d < today.isoformat(): continue
        ends = re.findall(r"(\d{1,2}:\d{2})\s*~", plan); t2 = ends[-1] if ends else ""
        reg = html.unescape(regs[k]) if k < len(regs) else WALK
        if reg.startswith("/") or not reg.startswith("http"): reg = BASE + reg.lstrip("/")
        out.append(_ev(f"walk-{d}-{k}", f"科學走讀：{title.strip()}", d, t1.zfill(5), t2.zfill(5) if t2 else "", f"集合：{place.strip()}", addr, free,
                       WALK, reg, True, "國科會 Kiss Science 科學走讀（專車接送、導覽解說）。行程：" + plan))
    return out
