# Apple Financial RAG System — Telegram Bot

A RAG (Retrieval-Augmented Generation) system built on n8n. A user sends a question to a Telegram bot, the AI Agent retrieves relevant passages from Apple's financial documents via Pinecone, Claude generates the answer, and the reply is sent back to Telegram.

## Project Overview

**Goal:** Telegram bot that answers questions about Apple Inc. financials using 5 official documents (quarterly reports + 10-K).

**Scope of questions:** financial figures (revenue, EPS, balance sheet), period-over-period comparisons, strategic/risk information from 10-K filings.

---

## Architecture

```
User → Telegram Bot
              │
              ▼
     n8n: Telegram Trigger
              │
              ▼
         AI Agent (v1.7)
         ├── LLM: Claude via OpenRouter (anthropic/claude-sonnet-4-6)
         └── Tool: Pinecone Vector Store (apple-rag index)
                        └── Embeddings: text-embedding-3-small (1024 dims)
              │
              ▼
     n8n: Telegram → Send Message
              │
              ▼
         User receives answer
```

---

## Data Sources

All PDFs live in `apple date/` (also to be uploaded to Google Drive folder "Apple RAG Documents"):

| File | Period |
|------|--------|
| `FY24_Q3_Consolidated_Financial_Statements.pdf` | Q3 FY2024 |
| `FY25_Q2_Consolidated_Financial_Statements.pdf` | Q2 FY2025 |
| `FY26_Q1_Consolidated_Financial_Statements.pdf` | Q1 FY2026 |
| `_10-K-2025-As-Filed.pdf` | Annual Report 2025 |
| `_10-K-2025-As-Filed (1).pdf` | Duplicate — skip |

---

## n8n Workflows

| Workflow | ID | Purpose | Active |
|----------|----|---------|--------|
| Apple RAG - Financial Q&A | `KgRNnOTmNPrL3coZ` | **Main production bot** (Telegram trigger) | **Active ✓** |
| Apple RAG - Auto Ingest Weekly | `vt0HSGuCGMKLb1oi` | Runs every Monday 06:00 — ingests new Drive PDFs | **Active ✓** (auto-activated) |
| Apple RAG - PDF Ingestion | `sT6AEaqV5golwoAK` | One-time manual ingest via Google Drive | Run manually (no activation needed) |
| Apple RAG - Telegram Bot | `wG2LXqOEGwdog81G` | Backup/duplicate — **do NOT activate** (same bot token as above) | Inactive |

> **⚠️ Warning:** Telegram allows only one webhook per bot. Only ONE of the Telegram workflows can be active at a time. `KgRNnOTmNPrL3coZ` is the active one — do not activate `wG2LXqOEGwdog81G`.

**n8n instance:** https://ahmadmadi.cfd

---

## Credentials (configured in n8n)

| Service | Credential Name | ID |
|---------|----------------|----|
| OpenAI (embeddings) | OpenAi account | `2YuL8wspIFqhWuLo` |
| Claude via OpenRouter | OpenAi account 2 | `0iU6MihBKMuJf7qZ` |
| Pinecone | PineconeApi account | `FLRQ3tOF25qPe0iz` |
| Google Drive | Google Drive account | `c3asHHkV4Cpm87Nr` |
| Telegram Bot | Telegram Apple Bot | `8lA0N3rr2OhRfNOb` |

---

## Pinecone Vector Index

| Setting | Value |
|---------|-------|
| Index name | `apple-rag` |
| Embedding model | `text-embedding-3-small` |
| Dimensions | `1024` |
| Metric | `cosine` |

> **Note:** Index uses 1024 dimensions (not 1536). All embedding nodes must have `options.dimensions: 1024`.

---

## Google Drive

| Resource | Value |
|----------|-------|
| Folder name | Apple RAG Documents |
| Folder ID | `1kOpDlQSVktGDx7ft5Xag-aB-q0rOIP9f` |
| Owner | ahmadmadi2006@gmail.com |

---

## Setup Checklist

- [x] **1. Pinecone index created** — `apple-rag` (1024 dims, cosine, Serverless)
- [x] **2. Google Drive folder created** — "Apple RAG Documents" (`1kOpDlQSVktGDx7ft5Xag-aB-q0rOIP9f`)
- [x] **3. Telegram Bot workflow created** — `wG2LXqOEGwdog81G`
- [x] **4. PDF Ingestion workflow created** — `sT6AEaqV5golwoAK`
- [ ] **5. Ingest PDFs** — choose ONE method:
  - **Method A (Python — fastest):** `set OPENAI_API_KEY=sk-...` then `python tools/ingest_pdfs.py`
  - **Method B (n8n):** Upload 4 PDFs to Google Drive folder, then run workflow `sT6AEaqV5golwoAK` in n8n UI
- [ ] **6. Activate Telegram bot** — open https://ahmadmadi.cfd/workflow/wG2LXqOEGwdog81G → toggle Active switch
- [ ] **7. Test** — send a question to the Telegram bot

---

## Common Tasks

### Run PDF ingestion — Python method (fastest)
```bat
cd "c:\Users\ahmad\Downloads\VS code\pro 3"
set OPENAI_API_KEY=sk-YOUR-KEY-HERE
python tools\ingest_pdfs.py
```

### Run PDF ingestion — n8n method
1. Upload 4 PDFs to Google Drive folder `1kOpDlQSVktGDx7ft5Xag-aB-q0rOIP9f`
2. Open https://ahmadmadi.cfd/workflow/sT6AEaqV5golwoAK
3. Click **Execute workflow** (no activation needed)
4. Verify vectors in Pinecone dashboard

### How weekly auto-ingest works
- Workflow `vt0HSGuCGMKLb1oi` fires every **Monday at 06:00**
- Lists all PDFs in the Google Drive folder
- Keeps only files whose `modifiedTime` is within the **last 8 days**
- Downloads and ingests each new file into Pinecone
- If no new files → workflow ends silently
- **To add a new document:** just upload the PDF to the Google Drive folder — it will be ingested the following Monday automatically

### Activate the Telegram bot
Open https://ahmadmadi.cfd/workflow/KgRNnOTmNPrL3coZ — it is already active. If it ever gets deactivated, toggle the **Active** switch in the top-right corner of the n8n UI.

### Test the Telegram bot
Send any question to the bot. Check n8n execution log at https://ahmadmadi.cfd/workflow/KgRNnOTmNPrL3coZ for debug.

### Add a new Apple document
- Python method: add PDF to `apple date/`, re-run `python tools/ingest_pdfs.py`
- n8n method: upload PDF to Google Drive folder, re-run ingestion workflow

### Modify AI Agent system prompt
Open workflow `wG2LXqOEGwdog81G` → "Apple Financial Agent" node → Options → System Message.

### Change the LLM model
Open workflow `wG2LXqOEGwdog81G` → "Claude via OpenRouter" node → Model field.
Format: `anthropic/claude-sonnet-4-6`, `anthropic/claude-opus-4-8`, etc.

---

## Known Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| "object is not iterable" activating via API | n8n v1.104.1 bug with LangChain node combos | Activate manually in n8n UI only |
| Ingestion finds no files (n8n method) | No PDFs in Google Drive folder | Upload PDFs to folder `1kOpDlQSVktGDx7ft5Xag-aB-q0rOIP9f` |
| Embedding dimension mismatch | Pinecone index is 1024 dims, default is 1536 | All embeddingsOpenAi nodes must have `options.dimensions: 1024` |
| n8n API returns 401 | Using `Authorization: Bearer` header | Switch to `X-N8N-API-KEY` header |
| OpenRouter model not found | Wrong model name format | Use `anthropic/claude-*` prefix |
| Old Pinecone credential failing | `8zCHlZInYJKXaDlw` had wrong API key | Use `FLRQ3tOF25qPe0iz` |

---

## n8n REST API Notes

- **Base URL:** `https://ahmadmadi.cfd/api/v1/`
- **Auth:** `X-N8N-API-KEY` header — `Authorization: Bearer` does NOT work
- **Workflow activation:** Must be done in n8n UI for any workflow containing LangChain nodes
