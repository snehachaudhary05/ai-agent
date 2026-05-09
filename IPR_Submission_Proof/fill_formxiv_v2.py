"""
Fills official Form-XIV-Registration of Copyright.pdf with exact coordinates
extracted from pdfplumber. Uses pypdf + reportlab overlay approach.
Conversion: reportlab_y = 842 - pdfplumber_top - 8 (baseline adjustment)
"""

import io, os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

SNEHA_SIGN  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snehacc.jpeg")
KOSTUB_SIGN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kostubcc.jpeg")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_PDF  = os.path.join(PROJECT_ROOT, "Form-XIV-Registration of Copyright.pdf")
OUTPUT_PDF = os.path.join(PROJECT_ROOT, "Form_XIV_Registeration.pdf")

W, H = A4   # 595.27 x 841.89

def rl(y_pdf):
    """Convert pdfplumber top-y to reportlab baseline-y."""
    return 842 - y_pdf - 8

FONT = "Helvetica"
FONB = "Helvetica-Bold"
SZ   = 8.5
SZS  = 8.0
BLACK = (0, 0, 0)
RX   = 336   # right column x for pages 2 & 3

def t(c, x, y, text, size=SZ, bold=False):
    c.setFont(FONB if bold else FONT, size)
    c.setFillColorRGB(*BLACK)
    c.drawString(x, y, text)

def overlay_page1(c):
    # -- Section 2 table: blank row (between y_pdf 335 and 405) --
    t(c, 105, rl(355), "Not Applicable — Joint authors filing together, no other parties.")

    # -- Section 3: fee (between y_pdf 405.7 and 440.1) --
    t(c, 105, rl(422), "Rs.500/-  |  Online payment  |  28/04/2026  |  copyright.gov.in")

    # -- Section 4: communications address (between y_pdf 440.1 and 509.1) --
    t(c, 105, rl(458), "SNEHA CHAUDHARY", bold=True)
    t(c, 105, rl(470), "2922, Near Panjiri Plant, Rajpura, Punjab - 140401")
    t(c, 105, rl(482), "Phone: +91 7973235391  |  Email: chaudharysneha693@gmail.com")

    # -- Section 7: list of enclosures (between y_pdf 601.2 and 624.2) --
    t(c, 105, rl(616), "1. SoP  2. SoFP  3. Source Code PDF  4. Aadhaar/PAN of both applicants")

    # -- Place & Date --
    t(c, 135, rl(681), "Chitkara University, Rajpura")
    t(c, 135, rl(704), "28/04/2026")

    # Signatures page 1
    c.drawImage(SNEHA_SIGN,  360, rl(648), width=60, height=22, preserveAspectRatio=True, mask='auto')
    c.drawImage(KOSTUB_SIGN, 430, rl(648), width=60, height=22, preserveAspectRatio=True, mask='auto')


def overlay_page2(c):
    # Row 1 — Registration number (pdfplumber y=71.9)
    t(c, RX, rl(71.9),  "(To be filled by Copyright Office)")

    # Row 2 — Applicant (4 lines, 12pt spacing, last line well above border at y_pdf=146.7)
    t(c, RX, rl(97),  "1. SNEHA CHAUDHARY", bold=True, size=SZS)
    t(c, RX, rl(109), "   2922, Near Panjiri Plant, Rajpura, Punjab - 140401 | Indian", size=SZS)
    t(c, RX, rl(121), "2. KOUSTUBH KUKRETI", bold=True, size=SZS)
    t(c, RX, rl(133), "   3127/2, Sector 44D, Chandigarh - 160047 | Indian", size=SZS)

    # Row 3 — Nature of interest (pdfplumber y=146.6)
    t(c, RX, rl(146.6), "Author (Joint Authors — 50% each)")

    # Row 4 — Class and description (pdfplumber y=170.1)
    t(c, RX, rl(170.1), "Computer Software")
    t(c, RX, rl(180.1), "AI-powered full-stack website builder (JavaScript & Python)", size=SZS)

    # Row 5 — Title (pdfplumber y=193.6)
    t(c, RX, rl(193.6), "SITEKRAFT - AI-POWERED WEBSITE BUILDER")

    # Row 6 — Language (pdfplumber y=217.1)
    t(c, RX, rl(217.1), "JavaScript, Python")

    # Row 7 — Author (4 lines, last line above border at y_pdf=291.7)
    t(c, RX, rl(241), "1. SNEHA CHAUDHARY", bold=True, size=SZS)
    t(c, RX, rl(253), "   2922, Near Panjiri Plant, Rajpura, Punjab - 140401 | Indian", size=SZS)
    t(c, RX, rl(265), "2. KOUSTUBH KUKRETI", bold=True, size=SZS)
    t(c, RX, rl(277), "   3127/2, Sector 44D, Chandigarh - 160047 | Indian", size=SZS)

    # Row 8 — Published/Unpublished (pdfplumber y=291.7)
    t(c, RX, rl(291.7), "Unpublished")

    # Row 9 — First publication (pdfplumber y=315.2)
    t(c, RX, rl(315.2), "Not Applicable (work is unpublished)")

    # Row 10 — Subsequent publications (pdfplumber y=353.7)
    t(c, RX, rl(353.7), "Not Applicable")

    # Row 11 — Owners (pdfplumber y=392.1, next row at 450.2, space=58 pts)
    t(c, RX, rl(392.1), "1. SNEHA CHAUDHARY — 50% share (same as applicant)", size=SZS)
    t(c, RX, rl(402.1), "2. KOUSTUBH KUKRETI — 50% share (same as applicant)", size=SZS)
    t(c, RX, rl(412.1), "No assignments or licences granted.", size=SZS)

    # Row 12 — Others authorized (pdfplumber y=450.1)
    t(c, RX, rl(450.1), "Nil")

    # Row 13 — Artistic work location (pdfplumber y=485.1)
    t(c, RX, rl(485.1), "Not Applicable (Computer Software)")

    # Row 14 — Trade Marks (pdfplumber y=543.1)
    t(c, RX, rl(543.1), "Not Applicable")

    # Row 15 — Designs Act (pdfplumber y=612.6)
    t(c, RX, rl(612.6), "Not Applicable")

    # Row 16 — Industrial process (pdfplumber y=647.6)
    t(c, RX, rl(647.6), "Not Applicable")

    # Row 17 — Remarks (pdfplumber y=705.6, short single-line row)
    t(c, RX, rl(705.6), "Joint authorship. Co-authors & co-owners, 50% share each.")

    # Place & Date (pdfplumber y=766.0, 777.5)
    t(c, 135, rl(766.0), "Chitkara University, Rajpura")
    t(c, 135, rl(777.5), "28/04/2026")

    # Signatures page 2
    c.drawImage(SNEHA_SIGN,  360, rl(738), width=60, height=22, preserveAspectRatio=True, mask='auto')
    c.drawImage(KOSTUB_SIGN, 430, rl(738), width=60, height=22, preserveAspectRatio=True, mask='auto')


def overlay_page3(c):
    # Row 1a — original work? (pdfplumber y=134.1)
    t(c, RX, rl(134.1), "Yes")

    # Row 1b — translation public domain? (pdfplumber y=159.1)
    t(c, RX, rl(159.1), "No")

    # Row 1c — translation copyright? (pdfplumber y=196.2)
    t(c, RX, rl(196.2), "No")

    # Row 1d — adaptation public domain? (pdfplumber y=233.3)
    t(c, RX, rl(233.3), "No")

    # Row 1e — adaptation copyright? (pdfplumber y=270.5)
    t(c, RX, rl(270.5), "No")

    # Row 2 — translation/adaptation details (pdfplumber y=307.6)
    t(c, RX, rl(307.6), "Not Applicable")

    # Row 2a — title of original (pdfplumber y=356.9)
    t(c, RX, rl(356.9), "Nil")

    # Row 2b — language of original (pdfplumber y=381.9)
    t(c, RX, rl(381.9), "Nil")

    # Row 2c — author of original (pdfplumber y=406.7)
    t(c, RX, rl(406.7), "Nil")

    # Row 2d — publisher of original (pdfplumber y=468.3)
    t(c, RX, rl(468.3), "Nil")

    # Row 2e — authorization (pdfplumber y=517.6)
    t(c, RX, rl(517.6), "Nil")

    # Row 3 — Remarks (pdfplumber y=579.2)
    t(c, RX, rl(579.2), "This is an original computer programme.")
    t(c, RX, rl(591.2), "Not a translation or adaptation of any other work.")

    # Place & Date (pdfplumber y=671.3, 684.7)
    t(c, 135, rl(671.3), "Chitkara University, Rajpura")
    t(c, 135, rl(684.7), "28/04/2026")

    # Signatures page 3
    c.drawImage(SNEHA_SIGN,  360, rl(640), width=60, height=22, preserveAspectRatio=True, mask='auto')
    c.drawImage(KOSTUB_SIGN, 430, rl(640), width=60, height=22, preserveAspectRatio=True, mask='auto')


def make_overlay(fn):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    fn(c)
    c.save()
    buf.seek(0)
    return buf.read()


def main():
    reader = PdfReader(INPUT_PDF)
    writer = PdfWriter()

    overlays = [overlay_page1, overlay_page2, overlay_page3]

    for i, page in enumerate(reader.pages):
        if i < len(overlays):
            ovr = PdfReader(io.BytesIO(make_overlay(overlays[i]))).pages[0]
            page.merge_page(ovr)
        writer.add_page(page)

    with open(OUTPUT_PDF, "wb") as f:
        writer.write(f)
    print(f"Saved: {OUTPUT_PDF}  ({len(writer.pages)} pages)")


if __name__ == "__main__":
    main()
