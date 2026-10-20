"""新北市立圖書館 活動報名系統（atpass.ntpclib.gov.tw）。網站無 robots.txt（404）；每頁間隔 1.5 秒禮貌抓取。
每一筆是一個「場次」，有日期時間、名額、報名起訖與報名頁連結。"""
import re, time, html, ssl, urllib.request, urllib.parse, http.cookiejar
from .common import is_family, categorize, _CTX
NAME = "atpass"
LABEL = "新北市立圖書館活動報名"
SVC = "8e109e8bb57a4b44b21e31c34db87dba"
LIST = f"https://atpass.ntpclib.gov.tw/activities/{SVC}"
DETAIL = f"https://atpass.ntpclib.gov.tw/activities/detail?svcId={SVC}&cntId="
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def fetch(today, max_pages=40):
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_CTX), urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0 (family-events bot; +https://github.com/Charlotte-Chen/family-events)")]
    h = op.open(LIST, timeout=60).read().decode("utf-8", "replace")
    tok = re.search(r'name="_csrf" value="([^"]+)"', h).group(1)
    out, seen = {}, set()
    for page in range(1, max_pages + 1):
        if page > 1:
            time.sleep(1.5)
            d = urllib.parse.urlencode({"csrfToken": tok, "_csrf": tok, "page": page, "isPage": "true", "pageSize": 10,
                "orderField": "registrationStart", "orderType": "asc", "searchTownshipdist": "", "searchSessionDate": "", "searchActivityName": ""}).encode()
            h = op.open(LIST, d, timeout=60).read().decode("utf-8", "replace")
        items = h.split('<div class="eventsApplyListDetail">')[1:]
        if not items: break
        new = 0
        for it in items:
            m = re.search(r'listDetailTitleText">([\s\S]*?)</p>', it)
            if not m: continue
            parts = re.split(r"<br\s*/?>", m.group(1))
            act = re.sub(r"^活動：", "", _t(parts[0])); ses = re.sub(r"^場次：", "", _t(parts[1])) if len(parts) > 1 else ""
            dt = re.search(r'listDetailDataTime">\s*<span>([^<]+)</span>', it)
            cid = re.search(r"showSessionDetail\('(\w+)'\)", it)
            if not dt or not cid: continue
            dts = dt.group(1).strip()
            key = (cid.group(1), dts, ses)
            if key in seen: continue
            seen.add(key); new += 1
            if dts[:10] < today.isoformat(): continue
            if not is_family(act + " " + ses + " " + _t(it)[:300], act): continue
            q = re.search(r'listMessageQuota">[\s\S]*?<p>([^<]*)</p>', it)
            reg = re.findall(r'listMessageTimeText">\s*<p>([^<]+)</p>\s*<span>~</span>\s*<p>([^<]+)</p>', it)
            br = re.search(r"《([^》]+)》", ses) or re.search(r"【([^】]+)】", act)
            branch = br.group(1) if br else ""
            if branch in ("全市",): branch = ""
            venue = ("新北市立圖書館" + branch) if branch and "圖書" not in branch else (branch or "新北市立圖書館")
            ev = out.setdefault(cid.group(1), {"id": f"atpass:{cid.group(1)}", "source": NAME, "title": act,
                "category": categorize(act + " " + ses), "sessions": [], "city": "新北市", "district": "", "venue": venue,
                "address": "", "lat": None, "lng": None, "free": None, "price": "", "organizer": "新北市立圖書館",
                "description": _t(re.search(r'eventsApplyListContainerText">([\s\S]*?)</p>', it).group(1))[:300] if 'eventsApplyListContainerText' in it else "",
                "image": "", "ticketUrl": "", "registrationUrl": DETAIL + cid.group(1), "url": DETAIL + cid.group(1),
                "needsRegistration": True, "updatedAt": ""})
            ev["sessions"].append({"start": dts[:10] + ("T" + dts[11:16] if len(dts) >= 16 else ""), "end": "", "venue": venue,
                "address": "", "lat": None, "lng": None, "name": ses[:80],
                "quota": q.group(1).strip() if q else "",
                "regStart": reg[0][0][:16] if reg else "", "regEnd": reg[0][1][:16] if reg else ""})
        if new == 0: break
    res = []
    for e in out.values():
        e["sessions"].sort(key=lambda s: s["start"])
        e["start"] = e["sessions"][0]["start"][:10]; e["end"] = e["sessions"][-1]["start"][:10]
        e["sessionCount"] = len(e["sessions"])
        res.append(e)
    return res
