# SPEC v0.1 — Threads 政治貼文協同行為偵測

## 1. 目標與非目標
**目標**
1. 針對指定政治主題／帳號的貼文，蒐集留言並建立資料集。
2. 以「留言時間、文字、帳號特徵、帳號間關聯」偵測協同行為跡象。
3. 輸出帳號群集（cluster）與每個群集／帳號的「協同行為分數」及可解釋的證據。

**非目標**
- 不判定個人政治立場、不公開指控個別帳號為網軍、不做真實身分還原（deanonymization）。
- 不追蹤私人帳號、不蒐集非公開內容。

## 2. 可行性結論
| 子任務 | 可行性 | 說明 |
|---|---|---|
| 留言頻率／時間分析 | 高 | 同步發文、突發（burst）、24h 作息異常皆可量化 |
| 留言文字／關鍵詞分析 | 高 | TF-IDF、n-gram、embedding 近似度、複製貼上偵測 |
| 帳號配對／群集 | 中高 | 共同回覆同貼文、時間共現、文字相似構成帳號圖，做社群偵測 |
| 判定「是網軍」的機率 | **低（僅能給旁證）** | 無 ground truth；高分也可能是粉絲團、動員、機器人式正常行銷。只能輸出「協同性」，不能輸出「身分」 |
| 資料蒐集 | 受限 | 見 `docs/DATA_ACCESS.md`；Threads 無公開留言搜尋 API，爬蟲違反 ToS 且易被封 |

## 3. 系統架構
```
collector → raw store → normalizer → feature extractors → account graph → clustering/scoring → report
```
- `collector/`：可插拔來源（官方 API、Meta Content Library 匯出、研究者提供之 CSV）。
- `storage/`：SQLite（開發）→ PostgreSQL（正式）；原始資料與衍生資料分表。
- `features/`：時間、文字、帳號、網路四類特徵。
- `graph/`：帳號—貼文二部圖，投影為帳號相似圖。
- `scoring/`：非監督式為主，輸出分數＋證據。
- `report/`：Jupyter / HTML 報告，帳號一律以雜湊 ID 呈現。
- 語言：Python 3.11+；pandas/polars、networkx/igraph、scikit-learn、jieba/CKIP（繁中斷詞）、sentence-transformers（多語 embedding）。

## 4. 資料模型（最小集合）
- `posts(post_id, author_hash, created_at, text, topic_tags, url_hash)`
- `comments(comment_id, post_id, parent_comment_id, author_hash, created_at, text, like_count, reply_count)`
- `accounts(author_hash, first_seen, follower_count, following_count, post_count, bio_text_hash, has_default_avatar, account_created_at?, verified)`
- 帳號 ID 在入庫時以加鹽雜湊（salt 不入庫）取代；原始 handle 僅存在加密的對照表，且可設定保存期限。

## 5. 特徵與偵測訊號
**時間**
- 留言間隔分布、同一貼文下的 burst（滑動視窗內新增留言數 z-score）。
- 帳號活動時段熵（24h 均勻 → 疑似自動化／輪班）。
- 帳號對的「時間共現」：Δt < 閾值內同時出現在同一貼文的次數。

**文字**
- 近似重複：MinHash/SimHash、embedding cosine > τ。
- 模板與微幅改寫（換同義詞、插入表情）。
- 提詞分析：貼文層級 TF-IDF／c-TF-IDF 主題詞，比較群集 vs. 全體的詞頻差異（log-odds）。
- 重複外部連結、固定 hashtag 組合。

**帳號**
- 追蹤/被追蹤比、貼文數、帳號年齡、預設頭像、bio 空白或相似。
- 以上僅作弱特徵，不單獨定罪。

**網路**
- 帳號對的 Jaccard／加權共同回覆貼文數 → 帳號相似圖。
- Louvain/Leiden 偵測群集；群集內密度、一致性（同進同出）、與基準模型比較。

## 6. 評分方法
1. **協同性分數（群集層級）**：時間共現 × 文字相似 × 網路密度，各自以隨機化基準（permutation / configuration model）標準化為 z 或 p-value，再合併。
2. **帳號層級異常分數**：Isolation Forest／規則特徵，僅用於排序待人工覆核對象。
3. **每個分數附證據**：列出代表性留言對、時間軸、共現貼文清單。
4. 結果分級：`low / medium / high coordination`，**不使用「網軍機率」字樣**。

## 7. 驗證
- 合成資料：以已知參數植入 bot 群集，量測 precision/recall。
- 公開基準：Twitter/X 公開 Information Operations 資料集（跨平台參考）。
- 人工標註：抽樣覆核，至少 2 位標註者，計算 Cohen's κ。
- 假陽性檢查：官方帳號粉絲社群、活動動員、迷因接龍須能被辨識並降分。

## 8. 里程碑
1. M0：文件（本 Spec、DATA_ACCESS、ETHICS）定稿；決定資料來源。
2. M1：資料 schema ＋ 匯入器 ＋ 匿名化。
3. M2：特徵管線（時間、文字）＋ 探索性報告。
4. M3：帳號圖 ＋ 群集 ＋ 評分 ＋ 證據報告。
5. M4：驗證實驗與誤判分析。

## 9. 待決事項
- 資料來源：Meta Content Library 申請 vs. Threads API 授權範圍 vs. 手動研究資料集？
- 研究單位／IRB 或倫理審查是否需要？
- 成果是否公開？公開形式（只放群集層級統計？）
- 分析範圍：特定選舉週期或特定議題？
