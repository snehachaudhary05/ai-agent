"""
Source Code PDF Generator
Generates a formatted PDF of all source files in the project.
"""

import os
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SOURCE_FILES = [
    # Backend Python
    ("backend/autonomous_agent.py", "Backend - Core AI Agent"),
    ("backend/autonomous_agent_react_helper.py", "Backend - React Agent Helper"),
    ("backend/react_builder.py", "Backend - React Builder"),
    ("backend/react_template_generator.py", "Backend - React Template Generator"),
    ("backend/react_api_routes.py", "Backend - React API Routes"),
    ("backend/vercel_deployer.py", "Backend - Vercel Deployer"),
    ("backend/professional_copywriter.py", "Backend - Professional Copywriter"),
    ("backend/groq_helper.py", "Backend - Groq Helper"),
    ("backend/openrouter_helper.py", "Backend - OpenRouter Helper"),
    ("backend/pexels_helper.py", "Backend - Pexels Helper"),
    ("backend/pixabay_helper.py", "Backend - Pixabay Helper"),
    ("backend/image_proxy.py", "Backend - Image Proxy"),
    ("backend/supabase_config.py", "Backend - Supabase Config"),
    ("backend/requirements.txt", "Backend - Requirements"),
    ("backend/Dockerfile", "Backend - Dockerfile"),
    ("backend/render.yaml", "Backend - Render Config"),
    ("backend/runtime.txt", "Backend - Runtime"),
    # Frontend
    ("frontend/src/main.jsx", "Frontend - main.jsx"),
    ("frontend/src/App.jsx", "Frontend - App.jsx"),
    ("frontend/src/Onboarding.jsx", "Frontend - Onboarding.jsx"),
    ("frontend/src/useTheme.js", "Frontend - useTheme.js"),
    ("frontend/src/App.css", "Frontend - App.css"),
    ("frontend/src/Onboarding.css", "Frontend - Onboarding.css"),
    ("frontend/src/index.css", "Frontend - index.css"),
    ("frontend/index.html", "Frontend - index.html"),
    ("frontend/vite.config.js", "Frontend - vite.config.js"),
    ("frontend/eslint.config.js", "Frontend - eslint.config.js"),
    ("frontend/vercel.json", "Frontend - vercel.json"),
    ("frontend/package.json", "Frontend - package.json"),
]

PROJECT_TITLE = "Sitekraft - AI-Powered Website Builder - Source Code"
AUTHOR = "Sneha Chaudhary & Koustubh Kukreti"


def safe(text):
    """Strip non-latin-1 characters for built-in PDF fonts."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


class SourceCodePDF(FPDF):
    def header(self):
        if self.page_no() <= 2:
            return
        self.set_font("Times", "I", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, safe("Sitekraft - Source Code"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-13)
        self.set_font("Times", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"{self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)


def make_pdf():
    pdf = SourceCodePDF()
    pdf.set_margins(25, 25, 25)
    pdf.set_auto_page_break(auto=True, margin=18)

    # ── Cover page ──────────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(15)
    pdf.set_font("Times", "B", 20)
    pdf.multi_cell(0, 11, safe("Sitekraft - AI-Powered Website Builder"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Times", "", 14)
    pdf.multi_cell(0, 9, "Complete Source Code",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Times", "", 12)
    pdf.cell(40, 8, "Author:")
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, safe(AUTHOR), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Times", "", 12)
    pdf.cell(40, 8, "Date:")
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, datetime.now().strftime("%d %B %Y"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Times", "", 12)
    pdf.cell(40, 8, "Language:")
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, "Python 3.12, JavaScript (React 19)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, "About this project:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 12)
    desc = (
        "Sitekraft is a web application built by Sneha Chaudhary and Koustubh Kukreti. "
        "It takes a business description as input and generates a complete, responsive React "
        "website. The backend is written in Python using FastAPI and integrates the Google "
        "Gemini API for code generation. Stock images are fetched via the Pexels API and "
        "the finished site is deployed to Vercel. The frontend is built with React 19 and Vite."
    )
    pdf.multi_cell(0, 7, safe(desc), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, "Technologies used:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 12)
    stack = [
        "- Python 3.12, FastAPI, Uvicorn",
        "- Google Gemini API, Groq API, OpenRouter",
        "- React 19, Vite, Axios",
        "- Pexels API (stock images)",
        "- Vercel (deployment), Render (backend hosting)",
        "- Supabase (database)",
    ]
    for line in stack:
        pdf.cell(0, 7, safe(line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(8)
    pdf.set_font("Times", "", 12)
    pdf.cell(0, 7, safe(f"Total source files included: {len(SOURCE_FILES)}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Table of Contents ──────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Times", "B", 16)
    pdf.cell(0, 10, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Times", "", 11)
    for i, (rel_path, label) in enumerate(SOURCE_FILES, 1):
        entry = f"{i}.  {label}  —  {rel_path}"
        pdf.cell(0, 7, safe(entry), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Source files ───────────────────────────────────────────────────────────
    for i, (rel_path, label) in enumerate(SOURCE_FILES, 1):
        full_path = os.path.join(PROJECT_ROOT, rel_path.replace("/", os.sep))

        pdf.add_page()

        # Plain file header — just bold filename, no colors or boxes
        pdf.set_font("Times", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, safe(f"File {i}: {rel_path}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Times", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, safe(label), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(150, 150, 150)
        pdf.set_line_width(0.3)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)

        if not os.path.exists(full_path):
            pdf.set_font("Times", "I", 10)
            pdf.cell(0, 8, "  [File not found]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue

        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            pdf.set_font("Times", "I", 10)
            pdf.cell(0, 8, "  [Empty file]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue

        lines = content.split("\n")
        pdf.set_text_color(0, 0, 0)

        for line_num, raw_line in enumerate(lines, 1):
            raw_line = raw_line.replace("\t", "    ")
            safe_line = safe(raw_line) if raw_line.strip() else " "

            # Line number in plain black, small
            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(140, 140, 140)
            pdf.cell(10, 4.5, str(line_num), border=0)

            # Code in plain black
            pdf.set_font("Courier", "", 7.5)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 4.5, safe_line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    out_path = os.path.join(PROJECT_ROOT, "SourceCode.pdf")
    pdf.output(out_path)
    print(f"PDF saved to: {out_path}")
    print(f"Total pages: {pdf.page}")


if __name__ == "__main__":
    make_pdf()
