# **📘 SalesOps Autopilot**

## **Product Requirements Document (PRD) v1.1**

**LLM-Driven, Engineering-Executable, Final Acceptance Spec**

**Status**: FINAL  
 **This document is the single source of truth for development, testing, and acceptance.**

---

## **1\. Product Vision**

打造一款 **AI-native SalesOps Web App**，讓企業銷售人員僅需透過「自然語言描述目標客戶」，即可自動完成：

* 市場與公司探索（Market & Account Discovery）

* 聯絡人識別與聯絡方式取得（Contact Intelligence）

* 個人化、多週期開發信件生成（Outbound Sequencing）

* 銷售 Pipeline 與 BANT 紀錄（Sales Qualification）

將「銷售狩獵（Prospecting）」轉化為  
 **LLM 驅動的自動化決策與執行流程**

---

## **2\. Target Users**

* B2B Sales

* Sales Operations

* Business Development

* Founder / Solo Sales

* RevOps / Growth Team

---

## **3\. Core Interaction Model – Text-to-SalesOps**

### **3.1 Natural Language Input**

使用者僅透過自然語言輸入，例如：

「幫我找台灣與日本的醫療 AI 新創公司，規模 20–200 人，近一年有募資或新聞曝光，優先找負責 IT、數位轉型或營運的主管。」

系統不得要求使用者填寫表單或選擇 dropdown。

---

### **3.2 LLM as Intent Parser & Planner**

LLM 僅負責：

1. **意圖理解**

2. **結構化輸出**

3. **任務規劃（不可直接執行）**

LLM **嚴禁直接呼叫外部 API、爬蟲或資料庫**。

---

## **4\. High-Level LLM-Driven System Architecture**

`flowchart TB`

  `U[User<br/>Natural Language Input]`

  `FE[Frontend<br/>React + TS]`

  `API[FastAPI Backend]`

  `LLM[LLM Intent Parser<br/>Strict JSON]`

  `ORCH[Task Orchestrator<br/>State Machine]`

  `BUS[Celery Task Bus]`

  `DB[(PostgreSQL)]`

  `REDIS[(Redis)]`

  `LOG[(Audit Log)]`

  `U --> FE --> API --> LLM --> ORCH`

  `ORCH --> BUS`

  `ORCH --> DB`

  `ORCH --> LOG`

  `BUS --> DB`

  `BUS --> LOG`

  `REDIS --- BUS`

---

## **5\. Functional Requirements (FR)**

### **FR-1：自然語言需求解析**

* 使用者輸入自由文字

* 系統輸出結構化 Intent JSON

* 無人工欄位對齊

**驗收標準**

* 100% JSON schema 合法

* 不可混入自然語言

---

### **FR-2：公司搜尋與市場探索**

資料來源（強制）：

* LinkedIn（Playwright / Selenium）

* Crunchbase（API / Sitemap Scrape）

* 台灣：104、商業新聞

* 亞洲：Wantedly、Korean Suppliers、Google News

---

### **FR-3：聯絡人識別與 Email 取得**

**強制工具順序**

1. LinkedIn Employee Scraping

2. MailScout（Email Pattern \+ SMTP Verify）

3. theHarvester（OSINT）

❌ 禁止 Hunter / Snov 等 SaaS

---

### **FR-4：新聞與背景蒐集**

* NewsAPI.org

* Google News fallback

* newspaper3k 萃取

---

### **FR-5：5 封連貫式開發信件**

* 固定 5 封

* 前後語境必須引用

* 多語（zh-TW / en / ja / ko）

---

### **FR-6：Pipeline 管道（Kanban）**

階段：

* Identified

* Contacted

* Follow-up

* Engaged

* Qualified

* Dropped

---

### **FR-7：BANT 紀錄**

* Budget

* Authority

* Need

* Timeline

---

## **6\. End-to-End Sequence Diagram（工程關鍵）**

`sequenceDiagram`

  `autonumber`

  `User->>Frontend: Input natural language`

  `Frontend->>API: POST /intents`

  `API->>LLM: Parse intent`

  `LLM-->>API: Intent JSON`

  `API->>Orchestrator: Create execution plan`

  `Orchestrator->>Celery: Dispatch tasks`

  `Celery->>Workers: Run search / enrich / generate`

  `Workers->>DB: Persist results`

  `Orchestrator->>DB: Update pipeline & BANT`

  `API-->>Frontend: Aggregated results`

---

## **7\. Internal Orchestration Protocol (MANDATORY)**

### **7.1 Intent JSON Schema**

`{`

  `"$schema": "http://json-schema.org/draft-07/schema#",`

  `"title": "SalesOpsIntent",`

  `"type": "object",`

  `"required": ["intent_id", "raw_text", "filters", "actions"],`

  `"properties": {`

    `"intent_id": { "type": "string" },`

    `"raw_text": { "type": "string" },`

    `"language": { "type": "string" },`

    `"filters": {`

      `"type": "object",`

      `"properties": {`

        `"industries": { "type": "array", "items": { "type": "string" } },`

        `"regions": { "type": "array", "items": { "type": "string" } },`

        `"company_size": { "type": "string" },`

        `"keywords": { "type": "array", "items": { "type": "string" } },`

        `"roles": { "type": "array", "items": { "type": "string" } }`

      `}`

    `},`

    `"actions": {`

      `"type": "array",`

      `"items": {`

        `"type": "string",`

        `"enum": [`

          `"search_companies",`

          `"find_contacts",`

          `"collect_news",`

          `"generate_emails",`

          `"schedule_emails",`

          `"update_pipeline"`

        `]`

      `}`

    `}`

  `}`

`}`

---

### **7.2 Task Object Schema**

`{`

  `"task_id": "uuid",`

  `"intent_id": "uuid",`

  `"task_type": "search_companies",`

  `"status": "queued | running | success | failed",`

  `"retry_count": 0,`

  `"idempotency_key": "intent_id + task_type + entity_id",`

  `"payload": {},`

  `"created_at": "ISO-8601"`

`}`

---

## **8\. Failure Handling & Idempotency**

`stateDiagram-v2`

  `Queued --> Running`

  `Running --> Success`

  `Running --> Failed`

  `Failed --> Retrying`

  `Retrying --> Queued`

  `Failed --> DeadLetter`

* Redis lock mandatory

* DeadLetter 必須 UI 可見

---

## **9\. Technical Stack (MANDATORY)**

| Layer | Choice |
| ----- | ----- |
| Frontend | React \+ TypeScript |
| Backend | FastAPI (Python) |
| Workers | Celery |
| Queue / Lock | Redis |
| DB | PostgreSQL |
| Scraping | Playwright / Selenium |
| LLM | GPT-4 / LLaMA |
| Translation | LibreTranslate |

---

## **10\. Acceptance Criteria (FINAL)**

本產品 **只有在以下全部成立時才算完成**：

1. 使用者輸入一句自然語言

2. 系統自動完成：

   * 公司搜尋

   * 聯絡人取得

   * Email 產生

   * 排程

   * Pipeline \+ BANT

3. 全流程可回溯、可編輯、可驗證

4. 無違反本 PRD 任一條款

---

## **11\. Enforcement Clause**

❗ **任何程式碼若偏離本 PRD，視為不合格實作**  
 ❗ Codex / Agent 必須以本文件為最高優先權

