"""蟾蜍山煥民新村「當期活動」（官網 huanminvillage.taipei，Accupass 常見親子工作坊主辦場館）。
日期、時間、地點都取自官網；報名連結用官網上的「前往報名」（常指向 Accupass）。robots.txt Crawl-delay 10，每次請求間隔 10 秒。"""
import re, html, time, unicodedata, urllib.request
from .common import _CTX, UA, is_family, categorize
NAME = "huanmin"
LABEL = "蟾蜍山煥民新村 當期活動"
BASE = "https://huanminvillage.taipei"
VENUE, ADDR = "蟾蜍山煥民新村", "臺北市大安區羅斯福路四段119巷66弄12號"
KIDS = r"親子|兒童|孩子|小朋友|小小|大小朋友|家長陪同|幼兒|繪本"
def _get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
def _txt(s):
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", "", s); s = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", s)
    s = unicodedata.normalize("NFKC", html.unescape(re.sub(r"<[^>]+>", "", s)))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", s))
def fetch(today):
    h = _get(BASE + "/events"); out = []
    for m in re.finditer(r'href="(/event/(\d+))" title="([^"]+)"', h):
        seg = _txt(h[m.end(): m.end() + 1500].split("entity-row")[0])
        ds = re.findall(r"(\d{4}) / (\d{2}) / (\d{2})", seg)
        if not ds: continue
        end = "-".join(ds[-1])
        if end < today.isoformat(): continue
        time.sleep(0 if __import__("os").environ.get("FAST") else 10)
        d = _get(BASE + m.group(1)); t = _txt(d); title = html.unescape(m.group(3))
        body = t[t.find("活動地點"):][:4000]
        if __import__("os").environ.get("FAST"): print(title, bool(re.search(KIDS, title + seg + body)), is_family(title + " " + seg + " " + body, title))
        if not (re.search(KIDS, title + seg + body) and is_family(title + " " + seg + " " + body, title)): continue
        tr = re.search(r"活動時間\s*(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})?\s*~\s*(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})?", t)
        s0, e0 = (tr.group(1), tr.group(3)) if tr else ("-".join(ds[0]), end)
        y = int(s0[:4]); sessions = []
        for line in body.split("\n"):
            sm = re.search(r"^(.{2,40}?)\s*[｜|]\s*(\d{1,2})\.(\d{1,2})\D{0,4}?(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})", line.strip())
            if sm:
                dd = f"{y}-{int(sm.group(2)):02d}-{int(sm.group(3)):02d}"
                if dd < s0: dd = f"{y+1}" + dd[4:]
                sessions.append({"start": f"{dd}T{sm.group(4)}", "end": f"{dd}T{sm.group(5)}", "name": re.sub(r"^\W+", "", sm.group(1)).strip(),
                                 "venue": VENUE, "address": ADDR, "lat": None, "lng": None})
        if not sessions:
            sessions = [{"start": s0 + (("T" + tr.group(2)) if tr and tr.group(2) else ""), "end": e0 + (("T" + tr.group(4)) if tr and tr.group(4) else ""),
                         "venue": VENUE, "address": ADDR, "lat": None, "lng": None}]
        reg = re.search(r'href="([^"]+)"[^>]*>\s*前往報名', d)
        desc = body.split("\n", 3)[-1][:600]
        out.append({"id": "huanmin:" + m.group(2), "source": NAME, "title": title, "category": categorize(title + " " + desc),
            "start": s0, "end": e0, "sessions": sessions, "sessionCount": len(sessions), "city": "臺北市", "district": "大安區",
            "venue": VENUE, "address": ADDR, "lat": None, "lng": None, "free": None, "price": "", "priceText": body,
            "organizer": "蟾蜍山煥民新村", "description": desc, "image": "", "ticketUrl": "",
            "registrationUrl": html.unescape(reg.group(1)) if reg else "", "url": BASE + m.group(1),
            "needsRegistration": bool(reg), "updatedAt": ""})
    return out
