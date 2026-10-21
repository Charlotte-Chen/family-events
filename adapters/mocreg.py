"""文化部「藝文活動報名系統」(event.culture.tw/mocweb/reg/<館所>)：國立臺灣博物館、國家人權博物館、國立歷史博物館等。
每個活動有場次、報名期間、名額與剩餘名額。每次請求間隔 1 秒。"""
import re, html, time, urllib.request, urllib.parse, http.cookiejar
from .common import is_family, categorize, city_of, _CTX
NAME = "mocreg"
LABEL = "文化部藝文活動報名系統（國立博物館）"
ORGS = {"NTM": ("國立臺灣博物館", "臺北市"), "NHRM": ("國家人權博物館", "新北市"), "NMH": ("國立歷史博物館", "臺北市"),
        "NMTH": ("國立臺灣歷史博物館", "臺南市"), "NTMOFA": ("國立臺灣美術館", "臺中市"), "NMTL": ("國立臺灣文學館", "臺南市"),
        "NTCRI": ("國立臺灣工藝研究發展中心", "南投縣"), "NMP": ("國立臺灣史前文化博物館", "臺東縣")}
BASE = "https://event.culture.tw/mocweb/reg/"
def _t(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def _dt(s):
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})\s+(\d{2}:\d{2})", s.strip()); return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}" if m else ""
def fetch(today):
    out = []
    for org, (oname, ocity) in ORGS.items():
        try:
            cj = http.cookiejar.CookieJar()
            op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_CTX), urllib.request.HTTPCookieProcessor(cj))
            op.addheaders = [("User-Agent", "Mozilla/5.0 (family-events bot; +https://github.com/Charlotte-Chen/family-events)")]
            op.open(BASE + f"{org}/QueryReg.init.ctr", timeout=40).read(); time.sleep(1)
            d = urllib.parse.urlencode({"dataVo.keyword": "", "dataVo.actKind": "", "advancedQuery": "N", "pager.currPage": 1, "pager.pageSize": 100, "dataVo.orderBy": ""}).encode()
            lst = op.open(BASE + f"{org}/QueryReg.listNew.ctr", d, timeout=40).read().decode("utf-8", "replace")
        except Exception as ex:
            print("mocreg list fail", org, ex); continue
        ids = list(dict.fromkeys(re.findall(r"actId=(\d+)", lst)))
        for aid in ids:
            i = lst.find(f"actId={aid}"); blk = _t(lst[max(0, i - 200): i + 3000])
            time.sleep(1)
            try: h = op.open(BASE + f"{org}/Detail.init.ctr?actId={aid}", timeout=40).read().decode("utf-8", "replace")
            except Exception as ex: print("mocreg detail fail", org, aid, ex); continue
            tm = re.search(r'<div class="title_\w+">\s*([^<]+?)\s*</div>', h)
            title = _t(re.search(r"<title>([\s\S]*?)</title>", h).group(1)) if re.search(r"<title>", h) else ""
            m = re.search(r"首頁 &gt; 活動明細[\s\S]{0,400}?</div>([\s\S]{0,600}?)<", h)
            tt = re.findall(r'class="[^"]*act_?[Tt]itle[^"]*"[^>]*>([\s\S]*?)<', h)
            # 活動名稱：用列表頁卡片上的標題
            nm = re.search(r'<div class="programDetailGroup">\s*<div class="title_01">([\s\S]*?)</div>', h)
            name = _t(nm.group(1)) if nm else ""
            if not name: continue
            a = h.find("活動內容介紹"); desc = _t(h[a: a + 6000])[6:700] if a > 0 else ""
            a, b = h.find('<div id="blockOriginal">'), h.find("<!-- 場次END -->")
            sess = []
            for box in re.sub(r"<!--[\s\S]*?-->", "", h[a:b]).split('class="programCardBox"')[1:]:
                rng = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2})\s*~\s*(\d{4}/\d{2}/\d{2} \d{2}:\d{2})", box)
                if not rng: continue
                st, en = _dt(rng.group(1)), _dt(rng.group(2))
                if (en or st)[:10] < today.isoformat(): continue
                sn = re.search(r'場次:</div>\s*<div class="">\s*([\s\S]*?)<span', box)
                bt = _t(box).replace("\u00a0", " ")
                pay = re.search(r'class="new_pay">([\s\S]*?)</div>', box)
                pay = _t(pay.group(1)) if pay else ""
                reg = re.search(r"報\s*名\s*期\s*間\s*(\d{4}/\d{2}/\d{2} \d{2}:\d{2})\s*~\s*(\d{4}/\d{2}/\d{2} \d{2}:\d{2})", bt)
                q = re.search(r"名\s*額\s*(\d+)", bt)
                left = re.search(r"正取剩\s*(\d+)\s*名", bt)
                ven = re.search(r"場\s*地\s*(.+?)\s*(?:名單|報名|截止|額滿|候補|未開放|$)", bt)
                addr = re.search(r"maps\?q=([^'\"]+)", box)
                btn = re.findall(r'value="(報名|截止|額滿|候補|未開放|尚未開放)"', box)
                sess.append({"start": st, "end": en if en[:10] == st[:10] else "", "venue": re.split(r"\s*(?:<|名\s*額|正取|講\s*師|備註|場次介紹)", _t(ven.group(1)))[0].strip() if ven else oname,
                    "address": urllib.parse.unquote(addr.group(1)) if addr else "", "lat": None, "lng": None,
                    "name": _t(sn.group(1))[:80] if sn else "", "pay": pay, "quota": q.group(1) if q else "",
                    "left": left.group(1) if left else "", "status": btn[-1] if btn else "",
                    "regStart": _dt(reg.group(1)).replace("T", " ") if reg else "", "regEnd": _dt(reg.group(2)).replace("T", " ") if reg else ""})
            if not sess: continue
            from postprocess import parse_age
            alltext = name + " " + desc + " " + " ".join(s["name"] for s in sess)
            ag = parse_age(alltext)
            strong = re.search(r"親子|兒童|小朋友|幼兒|孩子|孩童|寶寶|繪本|說故事|小小|家庭|國小|學童", name + " " + desc[:300])
            if not is_family(alltext, name) or not (strong or (ag and ag[0] <= 12)): continue
            if re.search(r"學校團體|團體預約|閱覽證|講座|研討會|論壇", name) and not re.search(r"親子|兒童", name): continue
            sess.sort(key=lambda s: s["start"])
            f = sess[0]
            free = None
            fulldesc = _t(h[h.find("活動內容介紹"): h.find("活動內容介紹") + 12000]) if "活動內容介紹" in h else ""
            out.append({"id": f"mocreg:{org}:{aid}", "source": NAME, "title": name, "category": categorize(name + " " + desc[:200]),
                "start": f["start"][:10], "end": max((s["end"] or s["start"])[:10] for s in sess), "sessions": sess, "sessionCount": len(sess),
                "city": "臺北市" if re.search(r"臺灣文學基地|（臺北）|\(臺北\)", name + f["venue"]) else (city_of(f["address"], f["venue"]) or ocity), "district": "", "venue": f["venue"], "address": f["address"],
                "lat": None, "lng": None, "free": free, "price": next((x["pay"] for x in sess if x.get("pay") and re.search(r"\d|免費", x["pay"])), ""), "priceText": fulldesc[:4000], "organizer": oname, "description": desc[:500], "image": "",
                "ticketUrl": "", "registrationUrl": BASE + f"{org}/Detail.init.ctr?actId={aid}", "url": BASE + f"{org}/Detail.init.ctr?actId={aid}",
                "needsRegistration": True, "updatedAt": ""})
    return out
