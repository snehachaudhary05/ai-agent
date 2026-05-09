"""
Generates a clean portrait PDF of Form XIV from Copyright_Form_XIV_Sitekraft.txt
"""

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TXT_FILE = os.path.join(PROJECT_ROOT, "Copyright_Form_XIV_Sitekraft.txt")
OUT_PDF  = os.path.join(PROJECT_ROOT, "Form_XIV_Registeration.pdf")


def safe(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")


def make_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    with open(TXT_FILE, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        text = line.rstrip("\n")

        # Blank line
        if text.strip() == "":
            pdf.ln(3)
            continue

        # Separator lines (===, ━━━, ───)
        if all(c in "=━─ " for c in text) and len(text.strip()) > 5:
            pdf.set_draw_color(0, 0, 0)
            pdf.set_line_width(0.3)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)
            continue

        # Section headings (all caps lines like PART I, PART II etc.)
        stripped = text.strip()
        if stripped.isupper() and len(stripped) > 3 and not stripped.startswith("-"):
            pdf.set_font("Times", "B", 11)
            pdf.multi_cell(0, 6, safe(stripped), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
            continue

        # Bold label lines (lines ending with colon or starting with number+dot)
        import re
        if re.match(r"^\s*\d+\.", text) or stripped.endswith(":"):
            pdf.set_font("Times", "B", 10)
            pdf.multi_cell(0, 5.5, safe(stripped), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue

        # Checkbox lines
        if "[✓]" in text or "[ ]" in text:
            pdf.set_font("Courier", "", 10)
            pdf.multi_cell(0, 5.5, safe(stripped), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue

        # Normal text
        pdf.set_font("Times", "", 10)
        pdf.multi_cell(0, 5.5, safe(stripped), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(OUT_PDF)
    print(f"PDF saved: {OUT_PDF}")
    print(f"Pages: {pdf.page}")


if __name__ == "__main__":
    make_pdf()
