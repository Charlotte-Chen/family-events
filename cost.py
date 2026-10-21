"""從各來源的價格欄位與介紹文字抽出費用；抓不到就標「費用未公告」，不猜。"""
import re
FW = str.maketrans("０１２３４５６７８９，＄：", "0123456789,$:")
LABEL = r"(全票|半票|優待票|優惠票|敬老票|愛心票|學生票|兒童票|孩童票|成人票|大人票|一般票|早鳥票|單人票|親子票|雙人票|家庭票|套票|報名費|材料費|課程費用|活動費用|費用|票價|門票|每人|每組|每位|每堂|每場|一人|一組)"
NUM = r"(?:NT\$|NTD|新臺幣|新台幣|\$)?\s*(\d{1,5}(?:,\d{3})?)\s*(?:元|NT)?"
FREE = r"免費參加|免費入場|免費索票|免費報名|免費參與|免費觀賞|免費活動|完全免費|自由入場|自由參加|免報名費|不收費|免費$|^免費|費用[:：]?\s*免費|活動費用[:：]?\s*免費|費用資訊\s*免費|入場方式[:：]?\s*免費"
NEED_TICKET = r"須憑.{0,6}門票|需憑.{0,6}門票|憑.{0,4}門票入|須購.{0,4}門票|需購.{0,4}門票|購票入館|購票入園|另購.{0,4}門票"
def _n(x): return int(x.replace(",", ""))
def labeled(t):
    out = []
    for m in re.finditer(LABEL + r"\s*[:：為約]?\s*" + NUM, t):
        lab, v = m.group(1), _n(m.group(2))
        if v < 10 or v > 50000: continue
        lab = {"優待票": "優待", "優惠票": "優惠", "活動費用": "費用", "課程費用": "費用", "門票": "門票", "每人": "每人", "一人": "每人"}.get(lab, lab)
        s = f"{lab} NT${v:,}"
        if s not in out: out.append(s)
    return out
def from_field(p):
    """結構化價格欄位，例如「全票100元，半票70元」「400,600,800」「免費」。"""
    p = (p or "").translate(FW).strip()
    if not p: return None
    if re.search(r"免費|免票|不收費|自由入場", p) and not re.search(r"\d{2,}\s*元|NT\$\s*\d", p): return "免費"
    lb = labeled(p)
    if lb: return "／".join(lb[:4])
    q = re.sub(r"(?<!\d)(\d{1,2}),(\d{3})(?!\d)", r"\1\2", p).replace("NT$", "").replace("元", "").replace("起", "")
    nums = sorted({int(x) for x in re.split(r"[,、/\s~\-–]+", q) if x.isdigit() and 10 <= int(x) <= 50000})
    if nums and re.fullmatch(r"[\d,、/\s~\-–]+", q):
        return f"NT${nums[0]:,}" if len(nums) == 1 else f"NT${nums[0]:,}–{nums[-1]:,}"
    return None
def from_text(t):
    t = (t or "").translate(FW)
    lb = labeled(t)
    if lb: return "／".join(lb[:4])
    m = re.search(r"(?:NT\$|新臺幣|新台幣)\s*(\d{2,5}(?:,\d{3})?)\s*元?", t) or re.search(r"(\d{2,5})\s*元\s*/\s*(?:人|位|組)", t)
    if m: return f"NT${_n(m.group(1)):,}" + ("／人" if "/" in m.group(0) else "")
    if re.search(FREE, t, re.M):
        return "免費（需購入館門票）" if re.search(NEED_TICKET, t) else "免費"
    return None
def apply(e):
    c = e.get("cost") or from_field(e.get("price")) or from_text(e.get("priceText")) or from_text(e.get("description"))
    e["cost"] = c or "費用未公告"
    e["free"] = True if e["cost"].startswith("免費") else (False if "NT$" in e["cost"] else None)
    return e

# ---- OPENTIX 售票頁：讀頁面內 schema.org AggregateOffer 的 lowPrice/highPrice（robots.txt 允許；快取避免重抓） ----
import json, os, time, urllib.request
CACHE = "data/pricecache.json"
def enrich_opentix(events, max_new=120):
    from adapters.common import _CTX, UA
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    new = 0
    for e in events:
        u = e.get("ticketUrl") or ""
        if "opentix.life/program/" not in u or from_field(e.get("price")): continue
        if u not in cache:
            if new >= max_new: continue
            new += 1; time.sleep(1.0)
            try:
                h = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40, context=_CTX).read().decode("utf-8", "replace")
                lo = [int(x) for x in re.findall(r'"lowPrice":(\d+)', h)]; hi = [int(x) for x in re.findall(r'"highPrice":(\d+)', h)]
                cache[u] = [min(lo), max(hi)] if lo and hi else []
            except Exception as ex:
                print("opentix fail", u, ex); continue
        v = cache.get(u)
        if v:
            e["cost"] = f"NT${v[0]:,}" if v[0] == v[1] else f"NT${v[0]:,}–{v[1]:,}"
            e["costSource"] = "OPENTIX 售票頁"
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False, indent=0)
    return new
