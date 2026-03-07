# 🧠 Neura AI

> *Intelligence that researches, reasons & writes*

Neura is a production-grade Multi-Agent AI Research Assistant that searches the web, retrieves knowledge from uploaded documents, fact-checks findings, and writes comprehensive research reports — all in real time.

🔗 **Live App:** [getneura.vercel.app](https://getneura.vercel.app)

---

## ✨ Features

- **Multi-Agent Pipeline** — 5 specialized agents run in sequence: RAG Retriever → Web Researcher → Fact Checker → Summarizer → Writer
- **Hybrid RAG** — Dense (OpenAI embeddings) + Sparse (BM25) search with RRF merging and Cohere reranking
- **Document Upload** — Upload PDFs, TXT, MD, and CSV files to the knowledge base
- **Streaming Reports** — Reports stream in real time with a typewriter effect
- **Citations Panel** — Every report includes sources and citations
- **Research History** — All reports are auto-saved and accessible from the History tab
- **Export** — Download reports as Markdown or PDF

---

## 🏗️ Architecture

```
Frontend (Next.js + Vercel)
        ↓
Backend (FastAPI + Render)
        ↓
┌─────────────────────────────┐
│     LangGraph Orchestrator  │
│                             │
│  RAG Agent                  │
│    → Hybrid Search          │
│    → Cohere Rerank          │
│  Researcher Agent           │
│    → Tavily Web Search      │
│  Fact Checker Agent         │
│  Summarizer Agent           │
│  Writer Agent               │
└─────────────────────────────┘
        ↓
PostgreSQL + pgvector (Render)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, Python 3.11, LangGraph, LangChain |
| AI | OpenAI GPT-4o, text-embedding-3-small |
| Search | Tavily API |
| Reranking | Cohere rerank-english-v3.0 |
| Database | PostgreSQL + pgvector |
| Hosting | Vercel (frontend) + Render (backend) |

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop

### 1. Clone the repo
```bash
git clone https://github.com/srishtichawla/neura.git
cd neura
```

### 2. Set up environment variables
```bash
cp backend/.env.example backend/.env
# Fill in your API keys
```

Required keys:
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
COHERE_API_KEY=...
DATABASE_URL=postgresql://researchuser:researchpass@localhost:5432/research_db
```

### 3. Start the database
```bash
docker-compose up -d
```

### 4. Start the backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🚀

---

## 📁 Project Structure

```
neura/
├── backend/
│   ├── agents/          # 5 LangGraph agents
│   ├── api/             # FastAPI routes
│   ├── db/              # PostgreSQL connection
│   ├── graph/           # LangGraph orchestrator
│   ├── rag/             # Hybrid retrieval pipeline
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/             # Next.js pages
│   └── lib/             # Zustand store
└── docker-compose.yml
```

---

## 🌐 Deployment

- **Frontend:** Deployed on [Vercel](https://vercel.com)
- **Backend:** Deployed on [Render](https://render.com)
- **Database:** PostgreSQL on Render


