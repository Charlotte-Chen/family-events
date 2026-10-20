"""國立臺灣科學教育館 活動行事曆（展場教育活動：科學 show、工作坊、定時導覽）。逐日抓 activityCalendar.aspx?dt=，間隔 1.5 秒。
同一天的展場活動合併成一張卡（「今日展場活動 N 場」），避免洗版。"""
import re, html, time, urllib.request
from datetime import timedelta
from .common import _CTX, UA
NAME = "ntsec"
LABEL = "國立臺灣科學教育館 活動行事曆"
URL = "https://www.ntsec.gov.tw/article/activityCalendar.aspx?a=17&dt="
DAYS = 35
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def fetch(today):
    occ = []
    for i in range(DAYS):
        d = (today + timedelta(days=i)).isoformat()
        if i: time.sleep(1.5)
        h = None
        for k in range(3):
            try: h = urllib.request.urlopen(urllib.request.Request(URL + d, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace"); break
            except Exception as ex: print("ntsec retry", d, ex); time.sleep(3)
        if h is None: continue
        items = re.findall(r'<p class="title">([\s\S]*?)</p>\s*<p class="txt">([\d-]+)</p>\s*<p class="txt">時間\s*:\s*([\d:]+)~([\d:]+)</p>', h)
        items = [(_t(a), b, c, e) for a, b, c, e in items if b == d]
        if not items: continue
        items.sort(key=lambda x: x[2])
        names = []
        for a, *_ in items:
            k = re.sub(r"^[^-]+-", "", a)
            if k not in names: names.append(k)
        occ.append({"date": d, "items": items, "names": names})
    out = []
    for o in occ:
        its = o["items"]
        out.append({"id": f"ntsec:{o['date']}", "source": NAME,
            "title": f"科教館展場活動：{'、'.join(o['names'][:4])}{' 等' if len(o['names']) > 4 else ''}（{len(its)} 場）",
            "category": "camp", "start": o["date"], "end": o["date"],
            "sessions": [{"start": f"{o['date']}T{its[0][2]}", "end": f"{o['date']}T{its[-1][3]}", "venue": "國立臺灣科學教育館",
                "address": "臺北市士林區士商路189號", "lat": 25.0961, "lng": 121.5154}],
            "sessionCount": 1, "city": "臺北市", "district": "士林區", "venue": "國立臺灣科學教育館", "address": "臺北市士林區士商路189號",
            "lat": 25.0961, "lng": 121.5154, "free": None, "price": "需購展場門票",
            "organizer": "國立臺灣科學教育館",
            "description": "當日場次：" + "；".join(f"{a[2]} {a[0]}" for a in its[:30]),
            "image": "", "ticketUrl": "", "registrationUrl": "", "url": URL + o["date"], "needsRegistration": False,
            "tags": ["科學"], "updatedAt": ""})
    return out
