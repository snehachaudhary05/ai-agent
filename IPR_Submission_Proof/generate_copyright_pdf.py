"""
Copyright Submission PDF Generator - Form XIV (India)
Creates a submission-ready source code PDF per Indian Copyright Office requirements:
  - Programs > 20 pages: first 25 + last 25 pages of source code
  - File size must be < 5 MB
  - No redactions
"""

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pypdf import PdfWriter, PdfReader
from datetime import datetime
import io

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ── Metadata (fill these in before submitting) ───────────────────────────────
META = {
    "title":         "Sitekraft - AI-Powered Website Builder",
    "author":        "Sneha Chaudhary & Koustubh Kukreti",
    "year":          "2026",
    "language":      "Python 3.12, JavaScript (React 19)",
    "nature":        "Computer Program / Literary Work",
    "description": (
        "Sitekraft is a web application designed and developed by Sneha Chaudhary and "
        "Koustubh Kukreti. It takes a business description as input and generates a complete, "
        "responsive React website. The backend is written in Python using FastAPI and integrates "
        "the Google Gemini API for intelligent code generation. Stock images are fetched through "
        "the Pexels API, and the finished website is automatically deployed to Vercel. "
        "The frontend is built with React 19 and Vite, featuring dark mode support and "
        "a guided onboarding flow for users."
    ),
    "modules": [
        "autonomous_agent.py          - Core website generation and orchestration logic",
        "autonomous_agent_react_helper.py - React code generation helper utilities",
        "react_builder.py             - React component builder and code assembler",
        "react_template_generator.py  - Dynamic page template generation engine",
        "react_api_routes.py          - FastAPI REST API endpoints",
        "vercel_deployer.py           - Vercel deployment pipeline",
        "professional_copywriter.py   - Content and copy generation module",
        "groq_helper.py               - Groq API integration",
        "openrouter_helper.py         - OpenRouter multi-model API integration",
        "pexels_helper.py             - Pexels stock image API integration",
        "image_proxy.py               - Image proxy and caching layer",
        "supabase_config.py           - Supabase database configuration",
        "App.jsx                      - Main React frontend application",
        "Onboarding.jsx               - User onboarding and business input flow",
        "useTheme.js                  - Theme management hook",
    ],
}

FULL_PDF = os.path.join(PROJECT_ROOT, "SourceCode.pdf")
OUT_PDF  = os.path.join(PROJECT_ROOT, "SourceCode_CopyrightSubmission.pdf")

PAGES_EACH_SIDE = 25   # first 25 + last 25 code pages


def safe(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")


def build_cover_pdf() -> bytes:
    """Return bytes of a 2-page PDF: cover + module index."""
    pdf = FPDF()
    pdf.set_margins(25, 30, 25)
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Page 1: Cover ────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)

    # Title
    pdf.set_font("Times", "B", 18)
    pdf.multi_cell(0, 10, safe(META["title"]),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # Subtitle
    pdf.set_font("Times", "", 13)
    pdf.multi_cell(0, 8, "Source Code for Copyright Registration",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    # Simple underline
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)

    # Details as plain label: value lines
    pdf.set_font("Times", "", 12)
    details = [
        ("Author",               META["author"]),
        ("Year of Creation",     META["year"]),
        ("Nature of Work",       META["nature"]),
        ("Programming Language", META["language"]),
        ("Date",                 datetime.now().strftime("%d %B %Y")),
        ("Form",                 "Form XIV - Indian Copyright Office"),
    ]
    for label, value in details:
        pdf.set_font("Times", "B", 12)
        pdf.cell(60, 8, safe(label + ":"))
        pdf.set_font("Times", "", 12)
        pdf.multi_cell(0, 8, safe(value),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Description
    pdf.set_font("Times", "B", 12)
    pdf.cell(0, 8, "Description of Work:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 12)
    pdf.multi_cell(0, 7, safe(META["description"]),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Note
    pdf.set_font("Times", "I", 11)
    note = (
        "Note: As per Indian Copyright Office requirements for computer programs exceeding "
        "20 pages, this document includes the first 25 pages and last 25 pages of the source "
        "code. The complete source code is available for inspection upon request."
    )
    pdf.multi_cell(0, 6, safe(note), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Page 2: Module List ──────────────────────────────────────────────────
    pdf.add_page()

    pdf.set_font("Times", "B", 14)
    pdf.cell(0, 10, "List of Source Files", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Times", "", 11)
    pdf.multi_cell(0, 7,
        "The following files form the complete original work submitted for copyright registration:",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    for i, mod in enumerate(META["modules"], 1):
        pdf.set_font("Times", "", 11)
        pdf.multi_cell(0, 7, safe(f"{i}.  {mod}"),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(6)
    pdf.set_font("Times", "B", 11)
    pdf.cell(0, 7, "Project Structure:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 11)
    structure = [
        "backend/   -  Python FastAPI backend with AI and helper modules",
        "frontend/  -  React 19 + Vite frontend application",
    ]
    for line in structure:
        pdf.cell(0, 7, safe(line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())


def build_separator_pdf() -> bytes:
    """Single page indicating omitted middle section."""
    pdf = FPDF()
    pdf.set_margins(25, 30, 25)
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(80)
    pdf.set_font("Times", "B", 13)
    pdf.multi_cell(0, 9,
        "--- Middle Section Omitted ---",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("Times", "", 11)
    pdf.multi_cell(0, 7,
        "As per the Indian Copyright Office requirement for computer programs exceeding "
        "20 pages, only the first 25 pages and last 25 pages of the source code are "
        "included in this submission. The complete source code is available for "
        "inspection upon request.",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())


def merge_pdfs():
    # 1. Build cover + module index
    cover_bytes = build_cover_pdf()

    # 2. Read full source PDF
    full_reader = PdfReader(FULL_PDF)
    total_pages = len(full_reader.pages)
    print(f"Full PDF pages: {total_pages}")

    # Page indices in full PDF:
    #   0 = cover, 1 = TOC, 2..N-1 = source code pages
    code_pages_start = 2          # 0-indexed, first source page
    code_pages_end   = total_pages - 1   # 0-indexed, last source page
    total_code_pages = code_pages_end - code_pages_start + 1
    print(f"Source code pages: {total_code_pages}")

    writer = PdfWriter()

    # Add cover + module index pages
    cover_reader = PdfReader(io.BytesIO(cover_bytes))
    for page in cover_reader.pages:
        writer.add_page(page)

    def add_page_upright(writer, page):
        """Add a page with rotation cleared so it displays upright."""
        if "/Rotate" in page:
            del page["/Rotate"]
        writer.add_page(page)

    # First 25 code pages
    first_end = min(code_pages_start + PAGES_EACH_SIDE, total_pages)
    for i in range(code_pages_start, first_end):
        add_page_upright(writer, full_reader.pages[i])

    # Separator (only if there are pages in the middle)
    if total_code_pages > PAGES_EACH_SIDE * 2:
        sep_bytes = build_separator_pdf()
        sep_reader = PdfReader(io.BytesIO(sep_bytes))
        writer.add_page(sep_reader.pages[0])

    # Last 25 code pages
    last_start = max(total_pages - PAGES_EACH_SIDE, first_end)
    for i in range(last_start, total_pages):
        add_page_upright(writer, full_reader.pages[i])

    with open(OUT_PDF, "wb") as f:
        writer.write(f)

    size_mb = os.path.getsize(OUT_PDF) / 1024 / 1024
    final_pages = len(writer.pages)
    print(f"\nSubmission PDF saved: {OUT_PDF}")
    print(f"Pages : {final_pages}  (cover×2 + {PAGES_EACH_SIDE} first + 1 sep + {PAGES_EACH_SIDE} last)")
    print(f"Size  : {size_mb:.2f} MB  (limit: 5 MB)  {'OK' if size_mb < 5 else 'OVER LIMIT'}")


if __name__ == "__main__":
    if not os.path.exists(FULL_PDF):
        print("SourceCode.pdf not found. Run generate_source_pdf.py first.")
    else:
        merge_pdfs()
