# Apple Financial RAG — Telegram Bot

A Retrieval-Augmented Generation (RAG) system that answers questions about Apple Inc. financials via a Telegram bot. Built on n8n, Pinecone, and Claude.

---

## How It Works

```
User → Telegram Bot
            │
            ▼
   n8n: Telegram Trigger
            │
            ▼
       AI Agent (Claude via OpenRouter)
       └── Tool: Pinecone Vector Store (apple-rag)
                      └── Embeddings: text-embedding-3-small (1024 dims)
            │
            ▼
   n8n: Send reply to Telegram
            │
            ▼
       User receives answer
```

The user sends a question to the Telegram bot. The AI Agent retrieves relevant passages from Apple's financial documents stored in Pinecone, Claude generates a grounded answer, and the reply is sent back to the user.

---

## Data Sources

Five Apple financial documents are ingested into the vector store:

| File | Period |
|------|--------|
| `FY24_Q3_Consolidated_Financial_Statements.pdf` | Q3 FY2024 |
| `FY25_Q2_Consolidated_Financial_Statements.pdf` | Q2 FY2025 |
| `FY26_Q1_Consolidated_Financial_Statements.pdf` | Q1 FY2026 |
| `_10-K-2025-As-Filed.pdf` | Annual Report 2025 |

PDFs are stored in Google Drive (folder ID: `1kOpDlQSVktGDx7ft5Xag-aB-q0rOIP9f`) and are **not** committed to this repo.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Workflow automation | [n8n](https://n8n.io) (self-hosted at `ahmadmadi.cfd`) |
| LLM | Claude (`anthropic/claude-sonnet-4-6`) via OpenRouter |
| Vector store | Pinecone — index `apple-rag`, 1024 dims, cosine |
| Embeddings | OpenAI `text-embedding-3-small` (1024 dims) |
| Document storage | Google Drive |
| Bot interface | Telegram Bot API |

---

## Repository Structure

```
├── workflows/
│   ├── Apple_RAG_Financial_QA.json       # Main Telegram bot workflow
│   └── Apple_RAG_Auto_Ingest_Weekly.json # Weekly auto-ingestion workflow
├── tools/
│   ├── ingest_pdfs.py                    # Python ingestion script (fastest method)
│   └── requirements.txt                  # Python dependencies
├── CLAUDE.md                             # Full architecture & ops reference
└── README.md
```

---

## n8n Workflows

| Workflow | Purpose | Status |
|----------|---------|--------|
| Apple RAG - Financial Q&A | Main production Telegram bot | Active |
| Apple RAG - Auto Ingest Weekly | Runs every Monday 06:00, ingests new Drive PDFs | Active |
| Apple RAG - PDF Ingestion | One-time manual ingestion | Run manually as needed |

> **Note:** Telegram allows only one active webhook per bot. Only the Financial Q&A workflow should be active at a time.

---

## Setup

### 1. Pinecone

Create an index named `apple-rag`:
- Dimensions: **1024** (not 1536)
- Metric: cosine
- Type: Serverless

### 2. Ingest PDFs — Python (fastest)

```bash
pip install -r tools/requirements.txt

set OPENAI_API_KEY=sk-...
set PINECONE_API_KEY=pcsk-...
python tools/ingest_pdfs.py
```

Reads PDFs from `apple date/`, chunks them (800 chars, 150 overlap), embeds with `text-embedding-3-small` at 1024 dims, and upserts into Pinecone.

### 3. Ingest PDFs — n8n

1. Upload PDFs to the Google Drive folder
2. Open the PDF Ingestion workflow in n8n
3. Click **Execute workflow**

### 4. Import workflows into n8n

Import the two JSON files from `workflows/` into your n8n instance, then configure credentials:

| Credential | Used for |
|-----------|---------|
| OpenAI account | Embeddings (`text-embedding-3-small`) |
| OpenAI account 2 (OpenRouter) | Claude LLM |
| PineconeApi account | Vector store |
| Google Drive account | PDF source |
| Telegram Apple Bot | Bot interface |

### 5. Activate the bot

Open the **Apple RAG - Financial Q&A** workflow in n8n and toggle the **Active** switch.

---

## Weekly Auto-Ingestion

The auto-ingest workflow runs every **Monday at 06:00**. It lists all PDFs in the Google Drive folder, filters to files modified in the last 8 days, and ingests any new ones into Pinecone automatically.

To add a new Apple document: upload the PDF to the Google Drive folder — it will be picked up the following Monday.

---

## Example Questions

- *"What was Apple's revenue in Q1 FY2026?"*
- *"How did gross margin change between Q3 FY2024 and Q2 FY2025?"*
- *"What are the main risk factors mentioned in the 2025 10-K?"*
- *"What is Apple's current cash position?"*

---

## Known Issues

| Issue | Fix |
|-------|-----|
| Embedding dimension mismatch | Pinecone index must be 1024 dims; set `options.dimensions: 1024` on all embedding nodes |
| n8n API activation fails for LangChain workflows | Activate manually in the n8n UI — never via REST API |
| n8n API returns 401 | Use `X-N8N-API-KEY` header, not `Authorization: Bearer` |
