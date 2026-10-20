# 週末帶孩子去哪｜台灣親子活動

網站：https://charlotte-chen.github.io/family-events/

每天台灣時間 05:00，GitHub Actions 會執行 `build.py`，從各資料來源抓活動，篩出親子活動、去掉已結束的，重建 `data/events.json` 並部署到 GitHub Pages。

## 資料來源（adapters/）
| 模組 | 來源 | 授權 |
|---|---|---|
| `moc.py` | 文化部文化資料開放服務網 藝文活動（全部類別） | 政府資料開放授權條款第1版 |
| `ntpc.py` | 新北市政府資料開放平臺 活動訊息 | 政府資料開放授權條款 |

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
