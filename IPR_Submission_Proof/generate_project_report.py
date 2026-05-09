"""
Project Report PDF Generator - Sitekraft
Covers: Objectives, Methodology, Implementation, Results
"""

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(PROJECT_ROOT, "ProjectReport_Sitekraft.pdf")

AUTHOR   = "Sneha Chaudhary & Koustubh Kukreti"
YEAR     = "2026"
RED      = (220, 38, 38)
DARK     = (20, 20, 20)
GREY     = (90, 90, 90)
LTGREY   = (150, 150, 150)
BGLIGHT  = (248, 248, 248)


def s(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ─── PDF class ────────────────────────────────────────────────────────────────

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(22, 22, 22)
        self.set_auto_page_break(auto=True, margin=18)
        self._current_chapter = ""

    def header(self):
        if self.page_no() <= 2:          # no header on cover / TOC
            return
        # Thin red top rule
        self.set_draw_color(*RED)
        self.set_line_width(0.4)
        self.line(self.l_margin, 14, self.w - self.r_margin, 14)
        self.set_y(16)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*LTGREY)
        self.cell(0, 5, s("Sitekraft  —  AI-Powered Website Builder  |  Project Report"), align="L",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_draw_color(*LTGREY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(*LTGREY)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")
        self.set_text_color(*DARK)

    # ── helpers ──────────────────────────────────────────────────────────────

    def h1(self, text):
        """Chapter heading"""
        self.ln(4)
        self.set_fill_color(*RED)
        self.rect(self.l_margin, self.get_y(), 4, 9, "F")
        self.set_x(self.l_margin + 7)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*DARK)
        self.cell(0, 9, s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*RED)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

    def h2(self, text):
        """Section heading"""
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*RED)
        self.cell(0, 7, s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(1)

    def h3(self, text):
        """Sub-section heading"""
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 50, 50)
        self.cell(0, 6, s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)

    def body(self, text, indent=0):
        """Paragraph body text"""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        if indent:
            self.set_x(self.l_margin + indent)
        self.multi_cell(0, 5.8, s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def bullet(self, items, indent=6):
        """Bulleted list"""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        for item in items:
            self.set_x(self.l_margin + indent)
            self.cell(5, 5.8, s("-"))
            self.multi_cell(0, 5.8, s(item), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def numbered(self, items, indent=6):
        """Numbered list"""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        for i, item in enumerate(items, 1):
            self.set_x(self.l_margin + indent)
            self.cell(7, 5.8, s(f"{i}."))
            self.multi_cell(0, 5.8, s(item), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def table(self, headers, rows, col_widths=None):
        """Simple table"""
        usable = self.w - self.l_margin - self.r_margin
        if col_widths is None:
            w = usable / len(headers)
            col_widths = [w] * len(headers)

        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*RED)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, s(h), border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK)
        for ri, row in enumerate(rows):
            if ri % 2 == 0:
                self.set_fill_color(250, 250, 250)
            else:
                self.set_fill_color(240, 240, 240)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6.5, s(str(cell)), border=1, fill=True)
            self.ln()
        self.ln(3)

    def info_box(self, text, bg=(240, 249, 255)):
        """Highlighted info box"""
        self.set_fill_color(*bg)
        self.set_draw_color(180, 220, 240)
        self.set_line_width(0.3)
        y0 = self.get_y()
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(30, 80, 120)
        self.multi_cell(0, 6, s(text), border=1, fill=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(2)

    def code_block(self, lines):
        """Monospace code block"""
        self.set_fill_color(30, 30, 30)
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.2)
        self.set_font("Courier", "", 7.8)
        self.set_text_color(220, 220, 220)
        for line in lines:
            self.set_x(self.l_margin + 2)
            self.cell(0, 4.8, s(line), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(3)


# ─── Build report ─────────────────────────────────────────────────────────────

def build():
    pdf = ReportPDF()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Red header band
    pdf.set_fill_color(*RED)
    pdf.rect(0, 0, 210, 55, "F")

    pdf.set_y(12)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, 13, "Sitekraft", align="C",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 14)
    pdf.multi_cell(0, 8, "AI-Powered Website Builder", align="C",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(62)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 9, "PROJECT REPORT", align="C",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*RED)
    pdf.set_line_width(0.7)
    pdf.line(45, pdf.get_y(), 165, pdf.get_y())
    pdf.ln(8)

    # Meta info box
    pdf.set_fill_color(250, 250, 250)
    pdf.set_draw_color(210, 210, 210)
    pdf.set_line_width(0.3)
    lm = pdf.l_margin
    bx = lm + 10
    bw = pdf.w - lm * 2 - 20
    by = pdf.get_y()
    rows_h = 8 * 6 + 10
    pdf.rect(bx, by, bw, rows_h, "FD")

    meta = [
        ("Author",            AUTHOR),
        ("Year",              YEAR),
        ("Nature of Work",    "Computer Program / Literary Work"),
        ("Backend Language",  "Python 3.12  |  FastAPI"),
        ("Frontend Language", "JavaScript (React 19)  |  Vite"),
        ("AI Model",          "Google Gemini 2.5 Flash"),
        ("Deployment",        "Vercel (sites) + Render (backend)"),
        ("Live Demo",         "ai-agent-gold-rho.vercel.app"),
    ]
    pdf.set_y(by + 4)
    for label, value in meta:
        pdf.set_x(bx + 4)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*DARK)
        pdf.cell(50, 6.5, s(label + ":"))
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6.5, s(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, "Abstract", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    abstract = (
        "Sitekraft is an end-to-end AI-powered website builder developed by Sneha Chaudhary "
        "and Koustubh Kukreti. It transforms a plain-language business description into a "
        "fully deployed, production-ready React website in under a minute. The system combines "
        "a conversational multi-step onboarding UI with a Python FastAPI backend that "
        "orchestrates Google Gemini 2.5 Flash for code generation, the Pexels API for "
        "contextual stock photography, an AI copywriter for professional content, and "
        "the Vercel API for zero-configuration deployment. The result is a live, "
        "publicly accessible website — with no manual coding required from the user."
    )
    pdf.multi_cell(0, 5.8, s(abstract), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Red footer band
    pdf.set_fill_color(*RED)
    pdf.rect(0, 282, 210, 15, "F")
    pdf.set_y(285)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, s(f"Generated: {datetime.now().strftime('%d %B %Y')}"), align="C")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 10, "Table of Contents", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*RED)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    toc = [
        ("1.", "Introduction & Objectives"),
        ("2.", "System Architecture"),
        ("3.", "Technology Stack"),
        ("4.", "Methodology"),
        ("4.1", "  User Onboarding Flow"),
        ("4.2", "  AI Code Generation Pipeline"),
        ("4.3", "  Image Integration"),
        ("4.4", "  AI Copywriting"),
        ("4.5", "  Automated Deployment"),
        ("5.", "Implementation Details"),
        ("5.1", "  Backend — Python / FastAPI"),
        ("5.2", "  Frontend — React / Vite"),
        ("6.", "Key Features"),
        ("7.", "Results & Testing"),
        ("8.", "Challenges & Solutions"),
        ("9.", "Conclusion & Future Work"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "B" if not num[1:].startswith(".") or len(num) == 2 else "", 10)
        pdf.set_text_color(*DARK if "." not in num[1:] else GREY)
        dots_space = pdf.w - pdf.l_margin - pdf.r_margin - 14
        pdf.cell(12, 7, s(num))
        pdf.cell(0, 7, s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 1 — INTRODUCTION & OBJECTIVES
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("1.  Introduction & Objectives")

    pdf.h2("1.1  Background")
    pdf.body(
        "Creating a professional website traditionally requires expertise in web "
        "development (HTML, CSS, JavaScript, React), backend programming, cloud "
        "deployment, UI/UX design, and copywriting. This high barrier prevents millions "
        "of small business owners — salon owners, restaurant operators, fitness coaches, "
        "clothing retailers — from establishing a meaningful online presence."
    )
    pdf.body(
        "The rapid advancement of large language models (LLMs), particularly "
        "Google Gemini 2.5 Flash, has made it feasible to automate the entire software "
        "development and deployment pipeline. Sitekraft exploits this capability to "
        "remove every technical obstacle between a business owner and a live website."
    )

    pdf.h2("1.2  Problem Statement")
    pdf.body(
        "Small and medium-sized business owners lack the technical knowledge and "
        "financial resources to commission custom websites. Existing website builders "
        "(Wix, Squarespace) require significant manual configuration and produce "
        "template-based output that lacks uniqueness and performance. There is a need "
        "for a system that:"
    )
    pdf.bullet([
        "Requires zero technical knowledge from the user",
        "Generates unique, component-based React code — not templates",
        "Automatically selects relevant photography and writes professional copy",
        "Deploys a live, publicly accessible URL with one click",
        "Supports multiple business verticals out of the box",
    ])

    pdf.h2("1.3  Objectives")
    pdf.numbered([
        "Design and implement a conversational multi-step onboarding interface that "
        "collects all information needed to build a complete website.",
        "Build an AI orchestration backend that coordinates LLM code generation, "
        "image retrieval, and copywriting into a single automated pipeline.",
        "Integrate Google Gemini 2.5 Flash to generate syntactically correct, "
        "production-ready React/Vite source code from structured business data.",
        "Fetch and embed contextually appropriate stock photography using the "
        "Pexels and Pixabay APIs.",
        "Generate professional marketing copy (headlines, taglines, descriptions) "
        "using an AI copywriting module with multi-model fallback.",
        "Automate website deployment to Vercel, returning a live URL to the user "
        "within seconds of submission.",
        "Support diverse business types: restaurants, salons, clothing stores, gyms, "
        "real estate agencies, coaching centers, and online stores.",
    ])

    pdf.h2("1.4  Scope")
    pdf.body(
        "Sitekraft generates single-page React applications with multiple sections "
        "(hero, services/products, about, contact/booking). It supports "
        "image uploads from the business owner, color theme selection, and style "
        "preferences (modern, bold, elegant, simple, dark). The generated code is "
        "real React JSX — not HTML templates — and is compiled and deployed "
        "automatically to the Vercel CDN."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 2 — SYSTEM ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("2.  System Architecture")

    pdf.h2("2.1  High-Level Overview")
    pdf.body(
        "Sitekraft follows a client-server architecture with a clear separation "
        "between the user-facing frontend, the AI orchestration backend, and "
        "external third-party APIs."
    )

    pdf.info_box(
        "User Browser  -->  React Frontend (Vercel CDN)\n"
        "                         |\n"
        "                    REST / HTTP\n"
        "                         |\n"
        "             Python FastAPI Backend (Render)\n"
        "            /        |        |        \\\n"
        "    Gemini AI   Pexels API  Pixabay   Vercel Deploy API\n"
        "   (code + copy)  (images) (images)   (live URL)"
    )

    pdf.h2("2.2  Component Breakdown")
    pdf.table(
        ["Component", "Technology", "Responsibility"],
        [
            ["Frontend SPA",       "React 19 + Vite",         "Onboarding UI, chat interface, result display"],
            ["API Server",         "FastAPI + Uvicorn",        "REST endpoints, session management, orchestration"],
            ["AI Agent",           "autonomous_agent.py",      "Conversation state, business analysis, routing"],
            ["React Builder",      "react_builder.py",         "Gemini-powered React code generation"],
            ["Template Engine",    "react_template_generator.py","Project scaffold, package.json, Vite config"],
            ["Copywriter",         "professional_copywriter.py","Hero copy, taglines, service descriptions"],
            ["Image Fetcher",      "pexels_helper.py / pixabay_helper.py", "Stock photo retrieval"],
            ["Vercel Deployer",    "vercel_deployer.py",       "ZIP creation, Vercel API calls, URL return"],
            ["Image Proxy",        "image_proxy.py",           "Proxy and cache external images for the backend"],
            ["DB Config",          "supabase_config.py",       "Supabase storage/DB configuration"],
        ],
        [55, 48, 65]
    )

    pdf.h2("2.3  Data Flow")
    pdf.numbered([
        "User completes 8-step onboarding (business type, name, location, services, "
        "colors, style, logo/images).",
        "Frontend POSTs structured JSON to /api/build-react-website.",
        "Backend analyses the request and calls ReactWebsiteBuilder.generate_react_website().",
        "Gemini 2.5 Flash generates all React components (Navbar, Hero, Services, "
        "About, Contact, Footer) and writes utility CSS.",
        "PexelsHelper / PixabayHelper fetch contextually relevant images for each service.",
        "ProfessionalCopywriter generates hero headline, tagline, and all section copy.",
        "react_template_generator assembles the full Vite project structure "
        "(package.json, vite.config.js, index.html, all JSX/CSS files).",
        "VercelDeployer packages the project as a deployment payload and calls the "
        "Vercel API, receiving back a live HTTPS URL.",
        "Frontend displays the live URL, a downloadable ZIP, and an inline preview.",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 3 — TECHNOLOGY STACK
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("3.  Technology Stack")

    pdf.h2("3.1  Backend")
    pdf.table(
        ["Library / Service", "Version", "Role"],
        [
            ["Python",                   "3.12",    "Core runtime"],
            ["FastAPI",                  "0.115",   "Async REST API framework"],
            ["Uvicorn",                  "0.30.6",  "ASGI server"],
            ["google-generativeai",      "0.8.3",   "Gemini SDK for code & copy generation"],
            ["httpx",                    "0.27.2",  "Async HTTP client for Vercel API"],
            ["requests",                 "2.32.3",  "Synchronous HTTP for image APIs"],
            ["python-multipart",         "0.0.12",  "File upload parsing"],
            ["python-dotenv",            "1.0.1",   "Environment variable management"],
            ["supabase",                 "2.9.1",   "Database / storage (optional)"],
            ["Pydantic",                 "2.9.2",   "Request/response validation"],
            ["Groq SDK",                 "latest",  "Alternative LLM (fallback)"],
            ["OpenRouter",               "REST",    "Multi-model LLM gateway (fallback)"],
        ],
        [60, 28, 80]
    )

    pdf.h2("3.2  Frontend")
    pdf.table(
        ["Library", "Version", "Role"],
        [
            ["React",          "19.2.0",  "UI component framework"],
            ["Vite",           "7.3.1",   "Build tool and dev server"],
            ["Axios",          "1.13.5",  "HTTP client for API calls"],
            ["JSZip",          "3.10.1",  "Client-side ZIP download of generated site"],
            ["ESLint",         "9.39.1",  "Code linting"],
        ],
        [55, 28, 85]
    )

    pdf.h2("3.3  External APIs & Services")
    pdf.table(
        ["Service", "Purpose"],
        [
            ["Google Gemini 2.5 Flash", "Primary LLM: React code generation and website copy"],
            ["Groq API",                "Fallback LLM for copywriting"],
            ["OpenRouter",              "Secondary fallback multi-model gateway"],
            ["Pexels API",              "High-quality stock photography (landscape/portrait)"],
            ["Pixabay API",             "Additional stock images with business context search"],
            ["Vercel Deploy API",       "Automated deployment of generated React projects"],
            ["Render",                  "Cloud hosting of FastAPI backend"],
            ["Supabase",               "Optional database for session/site data persistence"],
        ],
        [65, 103]
    )

    pdf.h2("3.4  AI Models")
    pdf.body(
        "The primary AI model is Google Gemini 2.5 Flash, chosen for its large "
        "context window (1M tokens), strong code generation capability, and low "
        "latency suitable for interactive use. The copywriting module uses a "
        "cascade of models: OpenRouter first (for variety of available models), "
        "then Groq (for speed), and finally Gemini (as a guaranteed fallback). "
        "This multi-model approach ensures high availability."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 4 — METHODOLOGY
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("4.  Methodology")

    pdf.h2("4.1  User Onboarding Flow")
    pdf.body(
        "The frontend presents an 8-step guided onboarding wizard implemented in "
        "Onboarding.jsx. Each step collects a specific piece of information and "
        "validates it before proceeding. The steps are:"
    )
    pdf.table(
        ["Step", "Input Collected", "UI Element"],
        [
            ["1", "Business type (restaurant, salon, gym, clothing, etc.)", "Icon card grid"],
            ["2", "Business name",                                           "Text input"],
            ["3", "City / Location",                                         "Text input"],
            ["4", "Services or products offered",                           "Tag input with add/remove"],
            ["5", "Brand color (primary)",                                   "Color picker + quick swatches"],
            ["6", "Website style (modern, bold, elegant, simple, dark)",    "Style card grid"],
            ["7", "Logo and service images (optional upload)",              "File uploader with preview"],
            ["8", "Review and submit",                                       "Summary card + Build button"],
        ],
        [12, 95, 60]
    )
    pdf.body(
        "Uploaded images are compressed client-side using the Canvas API (max "
        "1200x900 px, JPEG quality 0.78) and Base64-encoded before being sent to "
        "the backend. This avoids multipart upload complexity and keeps payloads "
        "manageable."
    )

    pdf.h2("4.2  AI Code Generation Pipeline")
    pdf.body(
        "The ReactWebsiteBuilder class in react_builder.py orchestrates website "
        "generation as follows:"
    )
    pdf.numbered([
        "Business analysis: The structured onboarding data is passed to Gemini "
        "with a prompt requesting a JSON analysis object containing business_name, "
        "business_type, detected services, color recommendations, and suitable "
        "React component list.",
        "Component generation: For each required component (Navbar, Hero, Services, "
        "About, Contact, Footer), a targeted prompt asks Gemini to generate "
        "self-contained JSX with inline Tailwind-style class names and all logic "
        "included.",
        "Supabase feature detection: The feature list is parsed to determine whether "
        "the site needs a booking form, product gallery, contact form, or media "
        "upload — which triggers additional Supabase backend wiring.",
        "Project assembly: react_template_generator.generate_complete_project() "
        "stitches all components, a theme config, package.json, vite.config.js, "
        "index.html, and utility CSS into a complete project file dictionary.",
        "Optional deployment: If the user opts to deploy, VercelDeployer packages "
        "the file dictionary and calls the Vercel API.",
    ])

    pdf.h2("4.3  Image Integration")
    pdf.body(
        "Images are fetched from two sources to maximise relevance and availability:"
    )
    pdf.bullet([
        "Pexels API: searched with a query built from the service name + business "
        "type. Returns large2x quality JPEG URLs. Up to 10 unique images per request.",
        "Pixabay API: used as a secondary source, searched with combined "
        "service+business_type query. Falls back to curated Unsplash URLs if the "
        "API key is absent.",
        "Image URLs are embedded directly into the generated JSX as src attributes. "
        "No images are stored on the backend — all are served from CDN.",
    ])

    pdf.h2("4.4  AI Copywriting")
    pdf.body(
        "The ProfessionalCopywriter class generates all text content shown on the "
        "website before code generation begins, so the AI has real copy to embed:"
    )
    pdf.bullet([
        "hero_headline: A punchy 6-10 word headline matching the business vibe.",
        "hero_subtext: A 1-2 sentence supporting description.",
        "tagline: Short brand slogan.",
        "about_text: 2-3 sentence 'About Us' section.",
        "service_descriptions: Individual 1-sentence descriptions for each service.",
        "cta_text: Call-to-action button label.",
    ])
    pdf.body(
        "The copywriter is aware of the style_vibe (modern, bold, elegant, etc.) "
        "and adjusts tone accordingly. Service categories and subcategories are "
        "included in the prompt to ensure descriptions are specific and accurate."
    )

    pdf.h2("4.5  Automated Deployment")
    pdf.body(
        "VercelDeployer.create_deployment() takes a dictionary of {file_path: "
        "file_content} and calls the Vercel REST API v13. The process is:"
    )
    pdf.numbered([
        "Project name is slugified (lowercased, spaces replaced with hyphens).",
        "Each file's content is Base64-encoded and submitted as a files array.",
        "A framework preset of 'vite' is set in the deployment configuration.",
        "The API responds with a deployment ID and initial status.",
        "The deployer polls the deployment status endpoint until status is 'READY' "
        "or a timeout occurs.",
        "The final deployment URL (e.g. project-abc123.vercel.app) is returned "
        "to the frontend.",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 5 — IMPLEMENTATION DETAILS
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("5.  Implementation Details")

    pdf.h2("5.1  Backend — Python / FastAPI")

    pdf.h3("autonomous_agent.py  (3,091 lines)")
    pdf.body(
        "The main FastAPI application. Defines all REST endpoints, manages "
        "in-memory chat sessions (CHAT_SESSIONS dict), and implements the "
        "conversational AI chatbot alongside the direct website builder. "
        "Key endpoints:"
    )
    pdf.table(
        ["Endpoint", "Method", "Description"],
        [
            ["/api/build-react-website",   "POST", "Main build trigger — full generation + optional deploy"],
            ["/api/chat",                   "POST", "Conversational AI chat for iterative website editing"],
            ["/api/deploy-react/{id}",      "POST", "Deploy a previously generated site to Vercel"],
            ["/api/download/{id}",          "GET",  "Download generated site as ZIP"],
            ["/api/upload-image",           "POST", "Receive and store uploaded business images"],
            ["/api/health",                 "GET",  "Health check endpoint"],
        ],
        [60, 18, 90]
    )

    pdf.h3("react_builder.py  (1,185 lines)")
    pdf.body(
        "Core code generation logic. ReactWebsiteBuilder.generate_react_website() "
        "is the main async method. It builds a detailed structured prompt for "
        "Gemini 2.5 Flash containing business context, color scheme, available "
        "images, required features, and explicit JSX formatting instructions. "
        "The AI response is parsed with regex to extract individual component files."
    )

    pdf.h3("react_template_generator.py")
    pdf.body(
        "Generates the full Vite project scaffold: package.json with correct "
        "dependencies (react, react-dom, vite), vite.config.js, index.html "
        "with CDN font links, and the src/ directory structure. Also injects "
        "the theme colors into a CSS variables file (index.css)."
    )

    pdf.h3("vercel_deployer.py")
    pdf.body(
        "Handles all Vercel API communication. Uses httpx for async HTTP. "
        "Implements retry logic for deployment polling with exponential backoff. "
        "Slugifies project names to satisfy Vercel's naming constraints. "
        "Forces personal account mode (team_id=None) to ensure public accessibility."
    )

    pdf.h3("professional_copywriter.py")
    pdf.body(
        "Implements a three-tier LLM cascade: OpenRouter -> Groq -> Gemini. "
        "Each tier is tried in sequence; the first successful JSON response is "
        "used. The prompt is identical across all tiers to ensure consistent "
        "output structure. Response is parsed as JSON and validated against "
        "required keys before returning."
    )

    pdf.h2("5.2  Frontend — React / Vite")

    pdf.h3("Onboarding.jsx  (1,076 lines)")
    pdf.body(
        "A fully controlled multi-step form with 8 steps. Each step is a "
        "separate functional component (StepWrapper, StepBusinessType, "
        "StepName, StepLocation, StepServices, StepColors, StepStyle, "
        "StepImages, StepReview). State is managed with useState at the top "
        "level and passed down as props. Navigation between steps is linear "
        "with a Back button."
    )
    pdf.body(
        "The image upload step uses a FileReader + Canvas pipeline "
        "(toCompressedBase64 function) to compress uploaded images client-side "
        "before sending. This reduces payload size from several MB to under 200 KB "
        "per image while maintaining visual quality suitable for website use."
    )

    pdf.h3("App.jsx  (880 lines)")
    pdf.body(
        "Renders the ResultView after the build completes. Displays the deployed "
        "URL as a clickable link, a 'Download ZIP' button (uses JSZip to package "
        "the returned file dictionary), an 'Open Preview' modal that renders the "
        "generated HTML/JSX in an iframe, and a dark/light theme toggle "
        "(useTheme hook). Also contains the generatePreviewHTML() function that "
        "assembles a standalone HTML preview from the generated component data."
    )

    pdf.h3("useTheme.js")
    pdf.body(
        "Custom React hook that reads/writes the theme preference to localStorage "
        "and applies a 'dark' CSS class to document.documentElement. Provides "
        "a [theme, toggleTheme] tuple to any consuming component."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 6 — KEY FEATURES
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("6.  Key Features")

    pdf.h2("6.1  Multi-Business-Type Support")
    pdf.body(
        "Sitekraft is purpose-built to handle 8 distinct business verticals, "
        "each with a tailored component set, service taxonomy, and visual style:"
    )
    pdf.table(
        ["Business Type", "Generated Sections", "Special Features"],
        [
            ["Restaurant / Cafe",    "Menu, Gallery, Reservations",   "Category tabs for menu items"],
            ["Clothing Store",       "Products, Collections",         "Product grid with filters"],
            ["Salon / Spa",          "Services, Team, Booking",       "Service category navigation"],
            ["Gym / Fitness",        "Classes, Trainers, Pricing",    "Class schedule display"],
            ["Real Estate",          "Listings, Agent, Contact",      "Property card layout"],
            ["Coaching / Classes",   "Programs, Testimonials, Enroll","Course card grid"],
            ["Online Store",         "Products, Cart concept, FAQ",   "E-commerce product layout"],
            ["Other Business",       "Flexible sections",             "Generic professional layout"],
        ],
        [38, 52, 78]
    )

    pdf.h2("6.2  Real React Code Generation")
    pdf.body(
        "Unlike template-based website builders, Sitekraft generates actual "
        "React JSX component files. The output includes:"
    )
    pdf.bullet([
        "Separate component files: Navbar.jsx, Hero.jsx, Services.jsx, "
        "About.jsx, Contact.jsx, Footer.jsx",
        "A main App.jsx that imports and composes all components",
        "A theme-aware index.css with CSS custom properties for colors",
        "A complete package.json with all required npm dependencies",
        "A vite.config.js for the Vite build system",
        "An index.html with Google Fonts (Poppins, Inter) pre-loaded",
    ])

    pdf.h2("6.3  Intelligent Image Selection")
    pdf.body(
        "For each service or product in the business listing, the image fetch "
        "pipeline builds a contextual query: e.g. for a salon offering 'Bridal "
        "Makeup' the query becomes 'Bridal Makeup salon beauty'. This produces "
        "far more relevant images than generic business photography."
    )

    pdf.h2("6.4  One-Click Deployment")
    pdf.body(
        "The entire path from 'Submit' button click to live URL takes under 60 "
        "seconds on average. No account creation, no domain configuration, no "
        "build settings — the user receives a vercel.app subdomain URL "
        "immediately."
    )

    pdf.h2("6.5  Image Upload Support")
    pdf.body(
        "Business owners can upload their own logo and up to 10 service/product "
        "images. The images are compressed, Base64-encoded, and embedded directly "
        "into the generated website, ensuring the final site reflects the actual "
        "business branding rather than generic stock photos."
    )

    pdf.h2("6.6  Dark / Light Theme")
    pdf.body(
        "The result view supports a dark/light mode toggle via the useTheme hook. "
        "The preference is persisted in localStorage so it survives page reloads."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 7 — RESULTS & TESTING
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("7.  Results & Testing")

    pdf.h2("7.1  Live Deployment")
    pdf.body(
        "Sitekraft is fully deployed and publicly accessible at:"
    )
    pdf.info_box("https://ai-agent-gold-rho.vercel.app")
    pdf.body(
        "The frontend is hosted on Vercel's global CDN. The backend is hosted "
        "on Render (Python/FastAPI). Both services use environment variables "
        "for all API keys and no secrets are committed to the repository."
    )

    pdf.h2("7.2  Test Cases")
    pdf.table(
        ["Test Scenario", "Input", "Expected Output", "Result"],
        [
            ["Restaurant site",    "Name: Bella Casa, Location: Mumbai,\nServices: Pizza, Pasta, Wine",
             "Menu sections with food images, booking form",  "PASS"],
            ["Clothing store",     "Name: TrendZone, Style: Bold, Products: Kurtis, Lehengas",
             "Product grid with filter tabs, vibrant colors", "PASS"],
            ["Salon site",         "Name: Glow Studio, Spa services, Elegant style",
             "Service cards, team section, booking",          "PASS"],
            ["Vercel deployment",  "Any valid build request with deploy=true",
             "Live HTTPS URL returned within 60 seconds",     "PASS"],
            ["Image upload",       "User uploads JPG logo > 2 MB",
             "Compressed to <200 KB, embedded in site",       "PASS"],
            ["Dark mode",          "Toggle button click",
             "Theme switches, persisted in localStorage",     "PASS"],
            ["ZIP download",       "Download button on result page",
             "Valid ZIP file containing all project files",   "PASS"],
        ],
        [30, 55, 50, 18]
    )

    pdf.h2("7.3  Performance Observations")
    pdf.table(
        ["Metric", "Observed Value"],
        [
            ["Average build time (code gen only)",        "15-25 seconds"],
            ["Average build + deploy time",               "45-70 seconds"],
            ["Generated site Lighthouse Performance",     "85-95 / 100"],
            ["Generated site Lighthouse Accessibility",   "90-98 / 100"],
            ["Frontend bundle size (Sitekraft UI)",       "~180 KB (gzipped)"],
            ["Source code PDF size",                      "0.47 MB (229 pages)"],
            ["Copyright submission PDF size",             "0.10 MB (53 pages)"],
        ],
        [100, 68]
    )

    pdf.h2("7.4  Business Types Tested")
    pdf.bullet([
        "Restaurant / Cafe  — fully functional menu with category filtering",
        "Salon / Spa        — service cards, team section, appointment booking form",
        "Clothing Store     — product grid with category and subcategory tabs",
        "Gym / Fitness      — class schedule, trainer profiles, pricing cards",
        "Online Store       — product listing with add-to-cart UI concept",
        "Coaching Center    — program descriptions, testimonials, enrollment CTA",
        "Real Estate        — property listing cards, agent contact form",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 8 — CHALLENGES & SOLUTIONS
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("8.  Challenges & Solutions")

    challenges = [
        (
            "LLM Output Consistency",
            "Gemini sometimes returns malformed JSX or omits closing tags, "
            "causing React compilation errors.",
            "Implemented regex-based post-processing to extract component boundaries, "
            "added explicit JSX formatting instructions in the prompt (require "
            "self-closing tags, no undefined variables), and wrapped generation in "
            "a retry loop with error feedback."
        ),
        (
            "Image Relevance",
            "Generic business-type queries (e.g. 'salon') returned images that "
            "did not match specific services.",
            "Combined service name + business type in every image query. Added "
            "random offset in Pexels pagination to avoid always returning the same "
            "first result, and used Pixabay as a secondary source with its own "
            "contextual query."
        ),
        (
            "Vercel Deployment Naming",
            "Vercel rejects project names with spaces, uppercase letters, or "
            "special characters.",
            "All project names are passed through a slugify function: lowercased, "
            "spaces replaced with hyphens, all non-alphanumeric characters stripped. "
            "A random 4-character suffix is appended to avoid name collisions."
        ),
        (
            "Large Image Uploads",
            "Business owners uploading original photos (3-10 MB) caused timeouts "
            "and oversized API payloads.",
            "Client-side compression using the HTML5 Canvas API resizes images to "
            "max 1200x900 px at JPEG quality 0.78, reliably reducing file size to "
            "under 200 KB before any network transfer."
        ),
        (
            "Frontend/Backend CORS on Production",
            "FastAPI CORS policies blocked requests from the Vercel-deployed "
            "frontend when testing with the production backend URL.",
            "Set allow_origins=['*'] in development. For production, the frontend "
            "uses the same domain as the backend (served by FastAPI's StaticFiles), "
            "eliminating the cross-origin issue entirely."
        ),
        (
            "AI Copywriting Reliability",
            "Single-model copywriting calls occasionally timed out or returned "
            "non-JSON responses.",
            "Implemented a three-tier fallback: OpenRouter -> Groq -> Gemini. "
            "Each tier retries once before moving to the next. This approach "
            "achieves near-100% reliability at the cost of slightly higher latency "
            "on fallback paths."
        ),
    ]

    for title, problem, solution in challenges:
        pdf.h2(title)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*RED)
        pdf.cell(0, 5.8, "Problem:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.body(problem)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(0, 130, 60)
        pdf.cell(0, 5.8, "Solution:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*DARK)
        pdf.body(solution)

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPTER 9 — CONCLUSION & FUTURE WORK
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.h1("9.  Conclusion & Future Work")

    pdf.h2("9.1  Conclusion")
    pdf.body(
        "Sitekraft successfully demonstrates that a fully autonomous AI-powered "
        "website builder is both technically feasible and practically useful. "
        "The system combines a large language model (Google Gemini 2.5 Flash) "
        "with domain-specific orchestration, contextual image retrieval, AI "
        "copywriting, and automated cloud deployment to produce production-ready "
        "React websites in under a minute — without any technical input from "
        "the user."
    )
    pdf.body(
        "The project makes a meaningful contribution to the accessibility of web "
        "development for small business owners. Rather than relying on static "
        "templates, it generates genuine component-based React code that is "
        "maintainable, extensible, and performant. The modular architecture — "
        "with separate modules for building, copying, image fetching, and "
        "deploying — ensures each concern is independently testable and replaceable."
    )
    pdf.body(
        "The multi-model fallback strategy in the copywriting pipeline and the "
        "AI retry logic in the builder demonstrate production-grade reliability "
        "engineering practices applied to an LLM-based system."
    )

    pdf.h2("9.2  Future Work")
    pdf.numbered([
        "Multi-page websites: Extend generation to support multiple routes "
        "(Home, About, Blog, Shop) using React Router.",
        "Real-time streaming: Stream the generated code to the frontend as "
        "Gemini produces it, giving users live feedback instead of waiting.",
        "Post-deployment editing: Allow users to describe changes in natural "
        "language after deployment, triggering a targeted re-generation and "
        "re-deploy of only the affected component.",
        "Custom domain support: Integrate the Vercel domain API so users can "
        "attach their own domain to the generated site.",
        "Database integration: Expose Supabase tables for booking, contact form "
        "submissions, and product inventory directly in the generated site.",
        "SEO meta generation: Automatically generate Open Graph tags, "
        "meta descriptions, and structured data (JSON-LD) for each site.",
        "Analytics injection: Embed a lightweight analytics script (e.g., "
        "Plausible or Vercel Analytics) into every generated site.",
        "Mobile app: Build a React Native version of the onboarding flow so "
        "business owners can create their website from a smartphone.",
    ])

    pdf.h2("9.3  Summary")
    pdf.info_box(
        "Sitekraft proves that the combination of a well-designed multi-step "
        "onboarding UI, a reliable LLM orchestration backend, and automated "
        "deployment can remove every technical barrier between a business owner "
        "and a live, professional website. The system is open for use at "
        "https://ai-agent-gold-rho.vercel.app"
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SAVE
    # ══════════════════════════════════════════════════════════════════════════
    pdf.output(OUT_PDF)
    size_mb = os.path.getsize(OUT_PDF) / 1024 / 1024
    print(f"Report saved : {OUT_PDF}")
    print(f"Pages        : {pdf.page}")
    print(f"Size         : {size_mb:.2f} MB")


if __name__ == "__main__":
    build()
