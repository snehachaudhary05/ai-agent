# Sitekraft — AI Website Builder

**Live demo:** [ai-agent-gold-rho.vercel.app](https://ai-agent-gold-rho.vercel.app)

An AI-powered website builder that generates complete, production-ready React websites from a simple text description and deploys them to Vercel instantly.

## Features

- **Conversational UI** — chat with the AI agent to describe your website
- **Full React/Vite generation** — produces real component-based code, not templates
- **Auto-deployment** — deploys generated sites directly to Vercel
- **Stock image integration** — pulls relevant images from Pexels & Pixabay
- **Supabase backend** — persists sessions and site data
- **Supports** e-commerce, booking pages, media uploads, and admin panels

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| AI | Google Gemini 2.5 Flash |
| Database | Supabase |
| Deployment | Vercel (generated sites), Render (backend) |
| Images | Pexels API, Pixabay API |

## Project Structure

```
responsive ai-agent/
├── backend/
│   ├── autonomous_agent.py        # Main FastAPI app & AI agent
│   ├── react_builder.py           # Gemini-powered React site generator
│   ├── vercel_deployer.py         # Automated Vercel deployment
│   ├── supabase_config.py         # Database manager
│   ├── pexels_helper.py           # Stock image fetching
│   ├── professional_copywriter.py # AI copywriting
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx                # Main chat interface
    │   └── Onboarding.jsx         # Onboarding flow
    └── package.json
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `VERCEL_TOKEN`, `PEXELS_API_KEY`

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
