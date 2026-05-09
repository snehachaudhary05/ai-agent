"""
Creates a clean, fully filled Form XIV for Copyright Registration.
Replicates the official form layout with all applicant details filled in.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF   = os.path.join(PROJECT_ROOT, "Form_XIV_Registeration.pdf")

W, H = A4

styles = getSampleStyleSheet()

def S(name, **kw):
    base = styles[name]
    return ParagraphStyle(name + str(kw), parent=base, **kw)

normal   = S("Normal",   fontSize=9,  leading=13)
bold     = S("Normal",   fontSize=9,  leading=13, fontName="Helvetica-Bold")
small    = S("Normal",   fontSize=8,  leading=11)
center   = S("Normal",   fontSize=10, leading=14, alignment=TA_CENTER)
title    = S("Normal",   fontSize=13, leading=18, fontName="Helvetica-Bold", alignment=TA_CENTER)
heading  = S("Normal",   fontSize=11, leading=15, fontName="Helvetica-Bold", alignment=TA_CENTER)
justify  = S("Normal",   fontSize=9,  leading=13, alignment=TA_JUSTIFY)

BLACK = colors.black
LGREY = colors.Color(0.92, 0.92, 0.92)

def p(text, style=normal):
    return Paragraph(text, style)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BLACK)

def sp(h=0.2):
    return Spacer(1, h * cm)


# ── Shared data ───────────────────────────────────────────────────────────────
SNEHA = (
    "SNEHA CHAUDHARY<br/>"
    "2922, Near Panjiri Plant, Rajpura, Punjab – 140401<br/>"
    "Phone: +91 7973235391 | Email: chaudharysneha693@gmail.com<br/>"
    "Nationality: Indian"
)
KOUST = (
    "KOUSTUBH KUKRETI<br/>"
    "3127/2, Sector 44D, Chandigarh – 160047<br/>"
    "Phone: +91 7347299940 | Email: koustubhkukreti@gmail.com<br/>"
    "Nationality: Indian"
)
PLACE = "Chitkara University, Rajpura"
DATE  = "26/04/2026"


def tbl(data, col_widths, row_heights=None):
    t = Table(data, colWidths=col_widths, rowHeights=row_heights)
    t.setStyle(TableStyle([
        ("BOX",         (0,0), (-1,-1), 0.5, BLACK),
        ("INNERGRID",   (0,0), (-1,-1), 0.4, BLACK),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0), (-1,-1), 5),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("BACKGROUND",  (0,0), (0,-1), LGREY),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8.5),
    ]))
    return t


# ── Page 1: Form XIV cover letter ────────────────────────────────────────────
def page1():
    story = []

    story.append(p("FORM XIV", title))
    story.append(p("Application for Registration of Copyright", heading))
    story.append(p("[See rule 70]", center))
    story.append(sp(0.4))
    story.append(hr())
    story.append(sp(0.3))

    story.append(p("To,", normal))
    story.append(p(
        "The Registrar of Copyrights,<br/>"
        "Copyright Office,<br/>"
        "4th Floor, Jeevan Deep Building,<br/>"
        "Parliament Street, New Delhi – 110001", normal))
    story.append(sp(0.3))
    story.append(p("Sir,", normal))
    story.append(sp(0.2))
    story.append(p(
        "In accordance with section 45 of the Copyright Act, 1957 (14 of 1957), I hereby apply for "
        "registration of copyright and request that entries may be made in the Register of Copyrights "
        "as in the enclosed 'Statement of Particulars' sent herewith.", justify))
    story.append(sp(0.3))

    # Point 1
    story.append(p("<b>1.</b> I also send herewith duly completed the Statement of Further Particulars "
                   "relating to the work.", normal))
    story.append(sp(0.2))

    # Point 2
    story.append(p("<b>2.</b> In accordance with rule 70 of the Copyright Rules, 2012, I have sent "
                   "copies of this letter and the enclosed statements to the other parties concerned:", normal))
    story.append(sp(0.15))

    t2 = tbl([
        [p("Names and addresses of the parties", bold), p("Date of Dispatch", bold)],
        [p("Not Applicable — Joint authors filing together.\nNo separate publisher or other parties.", small), p("—", small)],
    ], col_widths=[12*cm, 4.5*cm], row_heights=[0.6*cm, 1.2*cm])
    story.append(t2)
    story.append(sp(0.3))

    # Point 3
    story.append(p("<b>3.</b> The prescribed fee has been paid, as per details below:", normal))
    story.append(sp(0.15))
    t3 = tbl([
        [p("S.No.", bold), p("DD/IPO No.", bold), p("Date", bold), p("Amount", bold), p("Name of Bank", bold)],
        [p("1", small), p("(Online payment ref.)", small), p(DATE, small), p("₹500/-", small), p("copyright.gov.in portal", small)],
    ], col_widths=[1*cm, 4*cm, 3*cm, 2.5*cm, 5.5*cm], row_heights=[0.6*cm, 0.7*cm])
    story.append(t3)
    story.append(sp(0.3))

    # Point 4
    story.append(p("<b>4.</b> Communications on this subject may be addressed to:", normal))
    story.append(sp(0.1))
    story.append(p(
        "<b>SNEHA CHAUDHARY</b><br/>"
        "2922, Near Panjiri Plant, Rajpura, Punjab – 140401<br/>"
        "Phone: +91 7973235391 | Email: chaudharysneha693@gmail.com", normal))
    story.append(sp(0.3))

    # Point 5
    story.append(p(
        "<b>5.</b> I hereby declare that to the best of my knowledge and belief, no person, "
        "other than to whom a notice has been sent as per paragraph 2 above has any claim or "
        "interest or dispute to my copyright of this work or to its use by me.", justify))
    story.append(sp(0.2))

    # Point 6
    story.append(p(
        "<b>6.</b> I hereby verify that the particulars given in this Form and the Statement of "
        "Particulars and Statement of Further Particulars are true to the best of my knowledge, "
        "belief and information and nothing has been concealed therefrom.", justify))
    story.append(sp(0.2))

    # Point 7
    story.append(p("<b>7.</b> List of enclosures:", normal))
    story.append(p("&nbsp;&nbsp;&nbsp;1. Statement of Particulars", normal))
    story.append(p("&nbsp;&nbsp;&nbsp;2. Statement of Further Particulars", normal))
    story.append(p("&nbsp;&nbsp;&nbsp;3. Source Code — SourceCode_CopyrightSubmission.pdf", normal))
    story.append(p("&nbsp;&nbsp;&nbsp;4. Identity proof of both applicants (Aadhaar/PAN)", normal))
    story.append(sp(0.4))

    story.append(p("Yours faithfully,", normal))
    story.append(sp(0.8))
    story.append(p("(Signature of the Applicant)", normal))
    story.append(sp(0.3))

    sig_table = tbl([
        [p("Place: " + PLACE, normal), p("", normal)],
        [p("Date: " + DATE, normal),   p("", normal)],
    ], col_widths=[10*cm, 6.5*cm])
    story.append(sig_table)

    return story


# ── Page 2: Statement of Particulars ────────────────────────────────────────
def page2():
    story = []

    story.append(p("STATEMENT OF PARTICULARS", heading))
    story.append(sp(0.3))
    story.append(hr())
    story.append(sp(0.3))

    rows = [
        [p("1.", bold), p("Registration number", normal),
         p("(To be filled by the Copyright Office)", small)],

        [p("2.", bold), p("Name, Address and\nNationality of the Applicant", normal),
         p(SNEHA + "<br/><br/>" + KOUST, small)],

        [p("3.", bold), p("Nature of the applicant's interest\nin the copyright of the work", normal),
         p("Author (Joint Authors — 50% share each)", small)],

        [p("4.", bold), p("Class and description of the work", normal),
         p("Computer Software<br/>AI-powered full-stack website builder (JavaScript & Python)", small)],

        [p("5.", bold), p("Title of the work", normal),
         p("<b>SITEKRAFT — AI-POWERED WEBSITE BUILDER</b>", small)],

        [p("6.", bold), p("Language of the work", normal),
         p("JavaScript, Python", small)],

        [p("7.", bold), p("Name, address and nationality\nof the author and, if deceased,\ndate of decease", normal),
         p(SNEHA + "<br/><br/>" + KOUST + "<br/><br/>Neither author is deceased.", small)],

        [p("8.", bold), p("Whether work is Published\nor Unpublished", normal),
         p("Unpublished", small)],

        [p("9.", bold), p("Year and country of first publication\nand name, address and nationality\nof the publishers", normal),
         p("Not Applicable (work is unpublished)", small)],

        [p("10.", bold), p("Years and countries of subsequent\npublications, if any", normal),
         p("Not Applicable", small)],

        [p("11.", bold), p("Names, address and nationalities\nof the owners of the various rights\ncomprising the copyright and\nextent of rights held by each", normal),
         p("1. SNEHA CHAUDHARY — 50% share (all rights)<br/>"
           "2. KOUSTUBH KUKRETI — 50% share (all rights)<br/>"
           "No assignments or licences granted.", small)],

        [p("12.", bold), p("Names, addresses and nationalities\nof other persons authorized to\nassign or license the rights", normal),
         p("Nil", small)],

        [p("13.", bold), p("If artistic work, location of\noriginal work", normal),
         p("Not Applicable (Computer Software, not Artistic Work)", small)],

        [p("14.", bold), p("If artistic work used in relation\nto goods — Trade Mark certificate", normal),
         p("Not Applicable", small)],

        [p("15.", bold), p("If artistic work — registered\nunder Designs Act 2000", normal),
         p("Not Applicable", small)],

        [p("16.", bold), p("If artistic work — applied\nthrough industrial process", normal),
         p("Not Applicable", small)],

        [p("17.", bold), p("Remarks, if any", normal),
         p("This is a work of joint authorship. Both applicants are co-authors "
           "and co-owners with equal 50% share each. The work is an original "
           "computer programme created entirely by the authors.", small)],
    ]

    t = Table(rows, colWidths=[0.8*cm, 6*cm, 9.7*cm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.5, BLACK),
        ("INNERGRID",    (0,0), (-1,-1), 0.4, BLACK),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("BACKGROUND",   (0,0), (1,-1), LGREY),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
    ]))
    story.append(t)
    story.append(sp(0.4))

    story.append(p("(Signature of the Applicant)", normal))
    story.append(sp(0.2))
    story.append(p("Place: " + PLACE, normal))
    story.append(p("Date: "  + DATE,  normal))

    return story


# ── Page 3: Statement of Further Particulars ─────────────────────────────────
def page3():
    story = []

    story.append(p("STATEMENT OF FURTHER PARTICULARS", heading))
    story.append(p("(For Literary, including Software, Dramatic, Musical and Artistic Works only)", center))
    story.append(sp(0.3))
    story.append(hr())
    story.append(sp(0.3))

    rows = [
        [p("1.", bold),    p("Is the work to be registered", normal),  p("", small)],
        [p("(a)", bold),   p("an original work?", normal),              p("Yes", small)],
        [p("(b)", bold),   p("translation of a work in the public domain?", normal), p("No", small)],
        [p("(c)", bold),   p("a translation of a work in which copyright subsists?", normal), p("No", small)],
        [p("(d)", bold),   p("an adaptation of a work in the public domain?", normal), p("No", small)],
        [p("(e)", bold),   p("an adaptation of a work in which copyright subsists?", normal), p("No", small)],

        [p("2.", bold),    p("If the work is a translation or adaptation of a work in which\ncopyright subsists:", normal), p("Not Applicable", small)],
        [p("(a)", bold),   p("Title of the original work.", normal),    p("Nil", small)],
        [p("(b)", bold),   p("Language of the original work.", normal), p("Nil", small)],
        [p("(c)", bold),   p("Name, address and nationality of the author of the original work.", normal), p("Nil", small)],
        [p("(d)", bold),   p("Name, address and nationality of the publisher of the original work.", normal), p("Nil", small)],
        [p("(e)", bold),   p("Particulars of the authorization for translation or adaptation.", normal), p("Nil", small)],

        [p("3.", bold),    p("Remarks, if any.", normal),
         p("This is an original computer programme. It is not a translation or adaptation of any other work.", small)],
    ]

    t = Table(rows, colWidths=[0.8*cm, 8.5*cm, 7.2*cm])
    t.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.5, BLACK),
        ("INNERGRID",    (0,0), (-1,-1), 0.4, BLACK),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("BACKGROUND",   (0,0), (1,-1), LGREY),
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8.5),
    ]))
    story.append(t)
    story.append(sp(0.4))

    story.append(p("(Signature of the Applicant)", normal))
    story.append(sp(0.2))
    story.append(p("Place: " + PLACE, normal))
    story.append(p("Date: "  + DATE,  normal))

    return story


def main():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    story = []
    story += page1()
    story += [PageBreak()]
    story += page2()
    story += [PageBreak()]
    story += page3()

    doc.build(story)
    print(f"Saved: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
