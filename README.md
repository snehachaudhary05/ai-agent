# Sitekraft — AI-Powered Website Builder

**Live demo:** [ai-agent-gold-rho.vercel.app](https://ai-agent-gold-rho.vercel.app)

---

## Team Details

| Roll Number | Name |
|-------------|------|
| 2210990857 | Sneha Chaudhary |
| 2210990517 | Koustubh Kukreti |

**Project Title:** SITEKRAFT — AI-POWERED WEBSITE BUILDER

**Type:** Copyright

**Current Status:** Copyright Filed — Diary No. SW-20230/2026-CO, Filing Date: 28/04/2026 (Receipt No. 240456)

---

## About

An AI-powered website builder that generates complete, production-ready React websites from a simple text description and deploys them to Vercel instantly.

## Features

- **Conversational UI** — chat with the AI agent to describe your website
- **Full React/Vite generation** — produces real component-based code, not templates
- **Auto-deployment** — deploys generated sites directly to Vercel
- **Stock image integration** — pulls relevant images from Pexels & Pixabay
- **Supports** e-commerce, booking pages, media uploads, and contact forms

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| AI | Google Gemini 2.5 Flash |
| Deployment | Vercel (generated sites), Render (backend) |
| Images | Pexels API, Pixabay API |

## Repository Structure

```
├── IPR_Submission_Proof/       # Copyright Form-XIV, NOC, submission PDFs
├── Report_and_PPT/             # Project report
├── backend/                    # Python FastAPI backend & AI agent
│   ├── autonomous_agent.py
│   ├── react_builder.py
│   ├── vercel_deployer.py
│   ├── pexels_helper.py
│   ├── professional_copywriter.py
│   └── requirements.txt
└── frontend/                   # React/Vite frontend
    ├── src/
    │   ├── App.jsx
    │   └── Onboarding.jsx
    └── package.json
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys: `GEMINI_API_KEY`, `VERCEL_TOKEN`, `PEXELS_API_KEY`

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn autonomous_agent:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` with the API at `http://localhost:8000`.

## How It Works

1. User describes their website in the chat interface
2. The AI agent (Gemini 2.5 Flash) generates a complete React/Vite project
3. Professional copywriting and stock images are added automatically
4. The site is zipped and deployed to Vercel via the API
5. A live URL is returned to the user
