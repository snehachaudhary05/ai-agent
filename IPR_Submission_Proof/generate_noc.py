"""
Generates NOC (No Objection Certificate) from Koustubh Kukreti
authorising Sneha Chaudhary to file copyright application on behalf of both.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

KOSTUB_SIGN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kostubcc.jpeg")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF   = os.path.join(PROJECT_ROOT, "NOC_Koustubh_Kukreti.pdf")

styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name + str(kw), parent=styles[name], **kw)

normal  = S("Normal", fontSize=11, leading=16)
bold    = S("Normal", fontSize=11, leading=16, fontName="Helvetica-Bold")
center  = S("Normal", fontSize=12, leading=18, fontName="Helvetica-Bold", alignment=TA_CENTER)
justify = S("Normal", fontSize=11, leading=16, alignment=TA_JUSTIFY)
small   = S("Normal", fontSize=10, leading=14)

def sp(h=0.4):
    return Spacer(1, h * cm)

def main():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=3*cm, rightMargin=3*cm,
        topMargin=3*cm, bottomMargin=3*cm,
    )

    story = []

    # Title
    story.append(Paragraph("NO OBJECTION CERTIFICATE", center))
    story.append(sp(0.3))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(sp(0.5))

    # Date and place
    story.append(Paragraph("Date: 28/04/2026", normal))
    story.append(Paragraph("Place: Chitkara University, Rajpura", normal))
    story.append(sp(0.5))

    # Subject
    story.append(Paragraph(
        "<b>Subject: No Objection Certificate for Filing Copyright Registration Application "
        "for the work titled \"SITEKRAFT — AI-POWERED WEBSITE BUILDER\"</b>", normal))
    story.append(sp(0.5))

    # Body
    story.append(Paragraph("To,", normal))
    story.append(Paragraph(
        "The Registrar of Copyrights,<br/>"
        "Copyright Office,<br/>"
        "4th Floor, Jeevan Deep Building,<br/>"
        "Parliament Street, New Delhi – 110001", normal))
    story.append(sp(0.5))

    story.append(Paragraph("Sir/Madam,", normal))
    story.append(sp(0.3))

    story.append(Paragraph(
        "I, <b>KOUSTUBH KUKRETI</b>, residing at <b>3127/2, Sector 44D, Chandigarh – 160047</b>, "
        "Indian National, hereby state as follows:", justify))
    story.append(sp(0.3))

    story.append(Paragraph(
        "1. I am the <b>co-author and co-owner</b> (50% share) of the computer programme/software "
        "titled <b>\"SITEKRAFT — AI-POWERED WEBSITE BUILDER\"</b>, jointly created with "
        "<b>SNEHA CHAUDHARY</b>, residing at 2922, Near Panjiri Plant, Rajpura, Punjab – 140401.", justify))
    story.append(sp(0.2))

    story.append(Paragraph(
        "2. I have <b>no objection</b> whatsoever to <b>SNEHA CHAUDHARY</b> filing the application "
        "for registration of copyright in the above-mentioned work before the Copyright Office, "
        "Government of India, on behalf of both of us as joint applicants.", justify))
    story.append(sp(0.2))

    story.append(Paragraph(
        "3. I confirm that the said work is an <b>original computer programme</b> jointly created "
        "by both of us through our combined skill, labour, and creative effort, and is not a copy "
        "of any existing work.", justify))
    story.append(sp(0.2))

    story.append(Paragraph(
        "4. I confirm that I hold <b>50% share</b> of all rights comprising the copyright in the "
        "said work, and no assignment or licence of copyright has been granted by me to any person.", justify))
    story.append(sp(0.2))

    story.append(Paragraph(
        "5. The particulars given above are true and correct to the best of my knowledge, "
        "belief and information.", justify))
    story.append(sp(0.8))

    story.append(Paragraph("Yours faithfully,", normal))
    story.append(sp(0.3))

    # Koustubh's signature image
    story.append(Image(KOSTUB_SIGN, width=4*cm, height=1.5*cm))
    story.append(sp(0.2))

    # Signature block
    story.append(Paragraph("______________________________", normal))
    story.append(Paragraph("<b>KOUSTUBH KUKRETI</b>", bold))
    story.append(Paragraph("Co-Author & Co-Owner (50%)", normal))
    story.append(Paragraph("3127/2, Sector 44D, Chandigarh – 160047", normal))
    story.append(Paragraph("Phone: +91 7347299940", normal))
    story.append(Paragraph("Email: koustubhkukreti@gmail.com", normal))
    story.append(sp(0.5))
    story.append(HRFlowable(width="100%", thickness=0.5))
    story.append(sp(0.3))
    story.append(Paragraph(
        "<i>This No Objection Certificate is issued in connection with the copyright registration "
        "application for the work \"SITEKRAFT — AI-POWERED WEBSITE BUILDER\" under the "
        "Copyright Act, 1957 (14 of 1957), India.</i>", small))

    doc.build(story)
    print(f"Saved: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
