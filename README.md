# 週末帶孩子去哪｜台灣親子活動

網站：https://charlotte-chen.github.io/family-events/

每天台灣時間 05:00，GitHub Actions 會執行 `build.py`，從各資料來源抓活動，篩出親子活動、去掉已結束的，重建 `data/events.json` 並部署到 GitHub Pages。

## 資料來源（adapters/）
| 模組 | 來源 | 授權 |
|---|---|---|
| `moc.py` | 文化部文化資料開放服務網 藝文活動（全部類別） | 政府資料開放授權條款第1版 |
| `ntpc.py` | 新北市政府資料開放平臺 活動訊息 | 政府資料開放授權條款 |
| `atpass.py` | 新北市立圖書館活動報名系統（場次、名額、報名起訖；每頁間隔 1.5 秒） | 公開網頁 |

| `mocreg.py` | 文化部藝文活動報名系統 event.culture.tw/mocweb/reg/（臺博館、人權館、史博館、臺史博、國美館、臺文館、工藝中心、史前館）：場次、報名期間、名額、剩餘名額 | 公開網頁 |
| `tam.py` | 臺北市立天文科學教育館 活動報名總覽（星姊姊說故事等） | 公開網頁 |
| `ntsec.py` | 國立臺灣科學教育館 活動行事曆（逐日；同日展場活動合併成一張卡） | 公開網頁 |
| `beclass.py` | BeClass 線上報名「幼兒/親子」分類（先雙北再全台，60 天內；詳細頁取地點、費用、報名期限、限額/尚餘；排除純家長講座、哺乳、品茗等）。每次請求間隔 1.5 秒，robots.txt 全站允許 | 公開網頁 |
| `huanmin.py` | 蟾蜍山煥民新村「當期活動」官網（Accupass 上常見的親子工作坊主辦場館）。日期、時段、地點取自官網，報名連結用官網「前往報名」；只收親子活動；遵守 robots.txt Crawl-delay 10 秒 | 公開網頁 |
| `ntpcagri.py` | 新北市農業局「新北數位食農集章護照」活動總覽（農業局粉專「稼日蒔光」的活動彙整於此官方平台）；只收有 DIY／採收／闖關等親子體驗的活動 | 公開網頁（Nuxt 資料） |
| `thcpfarm.py` | 臺北客家農場（臺北市客家文化主題公園「客家農場」活動，農活時節日食農體驗，含時間、地點、費用） | 公開網頁 |
| `tsf.py` | 臺灣科學節（教育部、國科會）活動總覽：官網前端使用的公開 JSON，一次請求取得全部場次（日期、時間、地點、費用、對象）；排除論壇、競賽與國高中以上活動；主題自動標「科學」 | 公開 JSON |
| `manual.py` | 手動加入的活動（`data/manual.json`），使用者提供、官網核對過；每日更新會一併合併、不會被覆蓋 | 手動 |

> 評估後未接：ACCUPASS 活動通（服務條款 §5.3 禁止透過非官方介面取得服務、§8.2 禁止散布內容或製作衍生作品）。

文化部「親子」類（category=4）全部收錄，不做關鍵字篩選；其他類別用 `adapters/common.py` 的關鍵字判斷。

## 後處理（postprocess.py）
- 每個場次展開成「某一天的一場」（occurrences）。介紹中明列的日期、「每週六」「每月第N個週六」等規則會展開成各個日期，並標上「↻ 每週六」說明。
- 單一時段跨越 7 天以上、又沒有週期資訊的，歸為「常設與長期展覽」，放在頁面最下方折疊區。
- 沒座標的活動用 OpenStreetMap Nominatim 轉座標（每秒 1 次，快取在 `data/geocache.json`）；找不到時退回行政區中心（近似）。
- 跨來源重複（去掉【分館】前綴後同名、同月份）優先保留：atpass > moc > ntpc。
- 每個來源抓成功時會存 `data/raw/<來源>.json`；某天抓失敗就沿用上次的資料。

## 新增資料來源
1. 在 `adapters/` 新增 `xxx.py`，提供 `NAME`、`LABEL`、`fetch(today) -> list[dict]`。
2. 每筆活動依下列共同格式輸出（沒有的欄位給空字串或 null）。
3. 把模組加進 `adapters/__init__.py` 的 `ADAPTERS`。
某個來源抓取失敗時，會沿用上次的資料，不會把整站清空。

```
id, source, title, category(puppet|magic|story|music|dance|theatre|camp|exhibition|film|other),
start, end (YYYY-MM-DD), sessions[{start, end (YYYY-MM-DDTHH:MM), venue, address, lat, lng}], sessionCount,
city, district, venue, address, lat, lng, free(true/false/null), price, organizer, description, image,
ticketUrl, registrationUrl, url, needsRegistration, updatedAt
```
親子判斷關鍵字與分類規則在 `adapters/common.py`。卡片標題連結優先順序：ticketUrl → registrationUrl → url。

## 年齡、主題與「先搶報名」
- `postprocess.parse_age` 從標題、介紹、場次名稱抓年齡（如「大班至國小三年級」「6-13歲」「小一以上」「0-3歲」），轉成年齡分組 `ageBuckets`。
- `postprocess.TOPICS` 用關鍵字標主題（科學、天文、歷史、自然、藝術、語言）；adapter 也可直接給 `tags`。
- 場次有 `regStart`、`regEnd`、`quota`、`left`、`status` 時，網頁最上方「先搶報名」會依開放或截止時間排序列出。

## 費用
`cost.py`：依序取 adapter 給的 `cost`、價格欄位 `price`、詳細頁文字 `priceText`、介紹 `description`；OPENTIX 售票頁讀 schema.org AggregateOffer 的最低／最高票價（快取在 `data/pricecache.json`）；科教館讀官方「票價總覽」的常設展門票。都抓不到就顯示「費用未公告」，不猜。
