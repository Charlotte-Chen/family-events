"""共用工具：分類、縣市、親子判斷、免費判斷。"""
import re, json, ssl, urllib.request
# 台灣政府憑證缺 SKI 欄位，Python 3.13 嚴格模式會拒絕；仍驗證憑證，只關閉 X509 strict
_CTX = ssl.create_default_context()
_CTX.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
UA = {"User-Agent": "Mozilla/5.0 (family-events bot; +https://github.com/Charlotte-Chen/family-events)"}
def fetch_json(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
        return json.loads(r.read().decode("utf-8-sig"))

FAMILY_KW = ["親子","兒童","孩童","小朋友","幼兒","幼童","繪本","說故事","故事屋","故事時間","布袋戲","偶戲","人偶","魔術",
             "兒童劇","兒歌","童話","童書","科學營","夏令營","冬令營","小小","闔家","全家","寶寶","嬰幼兒","國小","學童","親職","family","Kids","kids"]
EXCLUDE_KW = ["成人限定","18歲以上","限18","樂齡","長者","銀髮","失智"]
def is_family(text, title=""):
    if any(k in title for k in EXCLUDE_KW): return False
    return any(k in text for k in FAMILY_KW)

CAT_RULES = [("puppet",["布袋戲","偶戲","人偶","戲偶","掌中"]),("magic",["魔術","馬戲","特技","雜技"]),
    ("story",["說故事","故事屋","故事時間","繪本","講故事"]),("music",["音樂會","音樂劇","演奏","合唱","兒歌","樂團","鋼琴"]),
    ("dance",["舞蹈","舞劇","芭蕾","舞團"]),("theatre",["兒童劇","劇團","劇場","戲劇","話劇"]),
    ("camp",["營隊","夏令營","冬令營","科學營","研習","工作坊","DIY","手作","課程","體驗"]),
    ("exhibition",["展覽","特展","書展","展出","常設展"]),("film",["電影","影展","影片","動畫"])]
CAT_LABEL = {"puppet":"偶戲布袋戲","magic":"魔術雜技","story":"說故事繪本","music":"音樂","dance":"舞蹈","theatre":"兒童劇場",
             "camp":"營隊工作坊","exhibition":"展覽","film":"電影","other":"其他"}
def categorize(text):
    for c, kws in CAT_RULES:
        if any(k in text for k in kws): return c
    return "other"

CITIES = ["臺北市","新北市","桃園市","臺中市","臺南市","高雄市","基隆市","新竹市","嘉義市","新竹縣","苗栗縣","彰化縣","南投縣",
          "雲林縣","嘉義縣","屏東縣","宜蘭縣","花蓮縣","臺東縣","澎湖縣","金門縣","連江縣"]
def norm(s): return (s or "").replace("台","臺")
def city_of(*texts):
    for t in texts:
        t = norm(t)
        best = None
        for c in CITIES:
            i = t.find(c)
            if i >= 0 and (best is None or i < best[0]): best = (i, c)
        if best: return best[1]
    return ""
def district_of(addr, city):
    a = norm(addr)
    m = re.search(re.escape(city) + r"([^\d\s市縣]{1,3}?[區鄉鎮市])", a) if city else None
    return m.group(1) if m else ""

def free_of(text):
    if re.search(r"免費|免票|免報名費|自由入場|不收費|免入場費", text): return True
    if re.search(r"\d+\s*元|售票|票價|NT\$|\$\s*\d", text): return False
    return None
