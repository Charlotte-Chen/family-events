"""把各來源活動展開成「每一天的場次」，判斷週期性與長期展覽，並做地址轉座標。"""
import re, json, time, os, urllib.parse
from datetime import date, timedelta
from adapters.common import _CTX, UA, city_of
import urllib.request
WD = "一二三四五六日"
WDMAP = {"一":0,"二":1,"三":2,"四":3,"五":4,"六":5,"日":6,"天":6}
LONG_DAYS = 7  # 單一時段跨越超過 7 天且無週期資訊 → 長期展覽

def _d(s): return date.fromisoformat(s[:10])
def recurrence_from_text(text, start, end):
    """解析 每週六 / 每週六、日 / 每月第N個週六，回傳日期清單與說明。"""
    m = re.search(r"每月第\s*([一二三四1-4])\s*個?\s*(?:週|星期|禮拜)([一二三四五六日天])", text)
    if m:
        n = "一二三四".find(m.group(1)) + 1 if m.group(1) in "一二三四" else int(m.group(1)); wd = WDMAP[m.group(2)]
        out, d = [], start
        while d <= end:
            if d.weekday() == wd and (d.day - 1) // 7 + 1 == n: out.append(d)
            d += timedelta(days=1)
        return out, f"每月第{n}個週{WD[wd]}"
    m = re.search(r"每(?:週|周|星期|禮拜)\s*([一二三四五六日天](?:\s*[、,及和與至~\-]\s*(?:週|星期)?[一二三四五六日天])*)", text)
    if m:
        g = m.group(1); wds = set()
        r = re.match(r"([一二三四五六日天])\s*[至~\-]\s*(?:週|星期)?([一二三四五六日天])", g)
        if r:
            a, b = WDMAP[r.group(1)], WDMAP[r.group(2)]; wds = set(range(a, b + 1))
        else:
            wds = {WDMAP[c] for c in g if c in WDMAP}
        out, d = [], start
        while d <= end:
            if d.weekday() in wds: out.append(d)
            d += timedelta(days=1)
        lab = "每週" + "、".join(WD[w] for w in sorted(wds))
        return out, lab
    return None, ""

def explicit_dates(desc, sd, ed):
    """抓出介紹裡明確列出的日期，如「10月24日（六）13:00」「11/07(六)」。"""
    out = {}
    for m in re.finditer(r"(\d{1,2})\s*[月/]\s*(\d{1,2})\s*日?\s*[（(]?[一二三四五六日]?[）)]?\s*(?:(上午|下午|晚上)?\s*(\d{1,2})[:：](\d{2}))?", desc):
        mo, da = int(m.group(1)), int(m.group(2))
        if not (1 <= mo <= 12 and 1 <= da <= 31): continue
        for y in (sd.year, ed.year):
            try: d = date(y, mo, da)
            except ValueError: continue
            if sd <= d <= ed:
                t = ""
                if m.group(4):
                    h = int(m.group(4)); h += 12 if m.group(3) in ("下午", "晚上") and h < 12 else 0; t = f"{h:02d}:{m.group(5)}"
                if d not in out or (t and not out[d]): out[d] = t
                break
    return sorted(out.items())

def expand(e, today):
    occ, rec = [], ""
    sess = e["sessions"]
    text = e["title"] + " " + (e.get("description") or "")
    for s in sess:
        sd = _d(s["start"]); ed = _d(s["end"]) if s.get("end") else sd
        t1 = s["start"][11:16]; t2 = s["end"][11:16] if s.get("end") else ""
        if t1 == "00:00" and t2 in ("", "00:00", "23:59"): t1 = t2 = ""
        base = {k: s.get(k) for k in ("venue","address","lat","lng","name","quota","regStart","regEnd") if s.get(k) not in (None, "")}
        span = (ed - sd).days
        if span == 0:
            occ.append({"date": sd.isoformat(), "t1": t1, "t2": t2, **base}); continue
        exp = explicit_dates(e.get("description") or "", sd, ed)
        if len(exp) >= 2 and not {d for d, _ in exp} <= {sd, ed}:
            occ += [{"date": d.isoformat(), "t1": tt or t1, "t2": t2 if not tt else "", **base} for d, tt in exp]; continue
        dates, lab = recurrence_from_text(text, max(sd, today), ed)
        if dates:
            rec = rec or lab
            occ += [{"date": d.isoformat(), "t1": t1, "t2": t2, **base} for d in dates]
        elif span <= 3 or (span <= LONG_DAYS and e["source"] == "moc"):
            for i in range(span + 1):
                d = sd + timedelta(days=i)
                if d >= today: occ.append({"date": d.isoformat(), "t1": t1, "t2": t2, **base})
        else:
            e.setdefault("_long", []).append({"from": sd.isoformat(), "to": ed.isoformat(), "t1": t1, "t2": t2, **base})
    occ = [o for o in occ if o["date"] >= today.isoformat()]
    seen = set(); uo = []
    for o in occ:
        k = (o["date"], o["t1"], o.get("venue"), o.get("name"))
        if k in seen: continue
        seen.add(k); o["city"] = city_of(o.get("address", ""), o.get("venue", "")) or e.get("city", ""); uo.append(o)
    occ = uo
    occ.sort(key=lambda o: (o["date"], o["t1"]))
    # 多場次同一星期幾 → 視為週期活動
    ndates = len({o["date"] for o in occ})
    if ndates < 2: rec = ""
    if not rec and ndates >= 3:
        wds = {_d(o["date"]).weekday() for o in occ}
        gaps = {(_d(b["date"]) - _d(a["date"])).days for a, b in zip(occ, occ[1:])}
        if len(wds) == 1 and gaps <= {7, 14, 0}: rec = "每週" + WD[wds.pop()] if gaps <= {7, 0} else "隔週" + WD[wds.pop()]
    if rec and occ:
        ts = {(o["t1"], o["t2"]) for o in occ}
        tt = ""
        if len(ts) == 1:
            a, b = ts.pop(); tt = f" {a}–{b}" if a and b else (f" {a}" if a else "")
        f, l = _d(occ[0]["date"]), _d(occ[-1]["date"])
        e["recurrence"] = rec; e["recurrenceNote"] = f"{rec}{tt}，{f.month}/{f.day}–{l.month}/{l.day}，共 {ndates} 天"
    e["occurrences"] = occ[:120]
    long = e.pop("_long", None)
    e["longRunning"] = bool(long) and not occ
    if long and not occ:
        L = max(long, key=lambda x: x["to"]); e["longRange"] = L
    del e["sessions"]
    return e

# ---- 地址轉座標（OpenStreetMap Nominatim；快取在 data/geocache.json；每秒 1 次） ----
CACHE = "data/geocache.json"
def geocode_all(events, max_new=80):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    new = 0
    def q(addr):
        nonlocal new
        if addr in cache: return cache[addr]
        if new >= max_new: return None
        new += 1; time.sleep(1.1)
        try:
            u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": addr, "format": "json", "limit": 1, "countrycodes": "tw"})
            r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA["User-Agent"], "Accept-Language": "zh-TW"}), timeout=30, context=_CTX).read())
            cache[addr] = [float(r[0]["lat"]), float(r[0]["lon"])] if r else []
        except Exception as ex:
            print("geocode fail", addr, ex); return None
        return cache[addr]
    for e in events:
        if e.get("lat") is not None: continue
        cands = []
        if e.get("address"): cands.append(re.sub(r"\d+樓.*$|\(.*?\)|（.*?）", "", e["address"]))
        if e.get("venue"): cands.append(e["venue"])
        if e.get("city") and e.get("district"): cands.append(e["city"] + e["district"])
        for c in cands:
            ll = q(c)
            if ll:
                e["lat"], e["lng"] = ll; e["geocoded"] = "district" if c == cands[-1] and e.get("district") and c.endswith(e["district"]) else True; break
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=0)
    for e in events:
        for o in e.get("occurrences", []):
            if o.get("lat") is None and e.get("lat") is not None: o["lat"], o["lng"] = e["lat"], e["lng"]
    return new
