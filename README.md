<div align="center">

# 🧠 Neura AI
### *Intelligence that researches, reasons & writes*

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-getneura.vercel.app-6366f1?style=for-the-badge)](https://getneura.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-srishtichawla%2Fneura-181717?style=for-the-badge&logo=github)](https://github.com/srishtichawla/neura)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=nextdotjs)](https://nextjs.org)

---

**Neura is not just a search engine. It thinks.**

Give it any topic — Neura deploys 5 AI agents in sequence, searches the web, retrieves knowledge from your documents, fact-checks everything, and delivers a beautifully written research report in real time.

</div>

---

## ⚡ What makes Neura different?

| Feature | Neura | ChatGPT | Perplexity |
|--------|-------|---------|------------|
| Multi-agent pipeline | ✅ | ❌ | ❌ |
| Upload your own docs | ✅ | ✅ | ❌ |
| Hybrid RAG (dense + sparse) | ✅ | ❌ | ❌ |
| Fact-checking agent | ✅ | ❌ | ❌ |
| Streaming report | ✅ | ✅ | ✅ |
| Open source | ✅ | ❌ | ❌ |

---

## 🎬 How it works

```
You type a topic
       ↓
📚  RAG Agent       → searches your uploaded documents
🔍  Research Agent  → searches the live web via Tavily
✅  Fact Checker    → verifies and cross-references findings
📝  Summarizer      → condenses key insights
✍️   Writer Agent   → crafts a full research report
       ↓
🚀  Streamed to you in real time
```

---

## ✨ Features

- **5 Specialized AI Agents** — each with a distinct role in the research pipeline
- **Hybrid RAG** — combines OpenAI embeddings + BM25 keyword search with RRF merging
- **Cohere Reranking** — re-scores retrieved chunks for maximum relevance
- **Document Upload** — drop in PDFs, TXT, MD, or CSV files to your knowledge base
- **Real-time Streaming** — watch the report write itself, word by word
- **Citations Panel** — every claim is backed by a source
- **Research History** — every report auto-saved, searchable anytime
- **Export** — download as Markdown or print as PDF

---

## 🛠️ Tech Stack

```
Frontend  →  Next.js 15 · TypeScript · Tailwind CSS · Zustand
Backend   →  FastAPI · Python 3.11 · LangGraph · LangChain
AI        →  OpenAI GPT-4o · text-embedding-3-small
Search    →  Tavily API
Reranker  →  Cohere rerank-english-v3.0
Database  →  PostgreSQL + pgvector
Deploy    →  Vercel + Render
```

---

## 🚀 Run Locally

```bash
# 1. Clone
git clone https://github.com/srishtichawla/neura.git && cd neura

# 2. Start database
docker-compose up -d

# 3. Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py

# 4. Frontend
cd ../frontend && npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

### Required API Keys
| Key | Get it from |
|-----|------------|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `COHERE_API_KEY` | [dashboard.cohere.com](https://dashboard.cohere.com) |

---

## 📁 Project Structure

```
neura/
├── backend/
│   ├── agents/        # rag_agent, researcher, fact_checker, summarizer, writer
│   ├── api/           # FastAPI routes
│   ├── db/            # PostgreSQL + pgvector setup
│   ├── graph/         # LangGraph orchestrator
│   ├── rag/           # ingest, retriever, query_rewriter
│   └── main.py
├── frontend/
│   ├── app/           # Next.js pages + UI
│   └── lib/           # Zustand store
└── docker-compose.yml
```

---

<div align="center">

Built with ❤️ by [Srishti Chawla](https://github.com/srishtichawla)

*If you found this useful, give it a ⭐*

</div>
