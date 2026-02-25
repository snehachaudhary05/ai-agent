FROM python:3.12-slim

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy backend code ─────────────────────────────────────────────────────────
COPY . .

# ── Create runtime directories ────────────────────────────────────────────────
RUN mkdir -p generated_websites website_states static/uploads site_data

EXPOSE 8000

CMD uvicorn autonomous_agent:app --host 0.0.0.0 --port ${PORT:-8000}
