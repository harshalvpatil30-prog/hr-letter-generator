import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Flowable
from reportlab.platypus.flowables import HRFlowable

from paths import app_path

# ---------- Company details (edit these) ----------
COMPANY = {
    "name": "ShreeGURU Consulting",
    "ref_prefix": "SGC",
    "header_lines": [
        "Business / Registered Address: 202, Daffodils, Sector-8, Ulwe, Navi-Mumbai",
        "GSTIN: 27AMCPD1095Q1ZR",
        "HR Email: shreeguru.consulting@gmail.com | Phone: [+91 7028163624] | "
        "Website: https://www.shreeguruconsulting.com",
    ],
    "footer": "CONFIDENTIAL | For the named recipient and authorized HR use only.",
    "logo": app_path("assets", "logo.png"),
    "signatory_name": "Hirabai Dudhade",
    "signatory_title": "Founder & Managing Director",
}

# ---------- Colours and page geometry ----------
TEAL = colors.HexColor("#075E5B")
LIGHT = colors.HexColor("#F1F5F5")
LINE = colors.HexColor("#CFE0E0")
GRAY = colors.HexColor("#555555")

PAGE_W, PAGE_H = A4
LEFT = RIGHT = 2.2 * cm
CONTENT_W = PAGE_W - LEFT - RIGHT
TOP_MARGIN = 6.0 * cm        # room for the header
BOTTOM_MARGIN = 2.6 * cm     # room for the footer

# ---------- Text styles ----------
body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=16,
                      textColor=colors.HexColor("#222222"), spaceAfter=6)
small = ParagraphStyle("small", parent=body, fontSize=9.5, leading=13, spaceAfter=0)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=20,
                       leading=24, textColor=TEAL, spaceAfter=10)
heading = ParagraphStyle("heading", parent=body, fontName="Helvetica-Bold", fontSize=11.5,
                         textColor=TEAL, spaceBefore=10, spaceAfter=4, keepWithNext=1)
clause_head = ParagraphStyle("clause_head", parent=body, fontName="Helvetica-Bold",
                             spaceAfter=2, keepWithNext=1)
                             
# Filled in by SigAnchor while the PDF is built; read by signer.py
ANCHOR = {}


# ---------- Header + footer + "Page X of Y" ----------
class NumberedCanvas(rl_canvas.Canvas):
    """Saves every page first, so the footer can say 'Page 2 of 3'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._draw_chrome(total)
            super().showPage()
        super().save()

    def _draw_chrome(self, total):
        c = self
        c.saveState()

        # Teal bar across the top
        c.setFillColor(TEAL)
        c.rect(0, PAGE_H - 0.5 * cm, PAGE_W, 0.5 * cm, stroke=0, fill=1)

        # Logo (skipped if missing) and company name
        text_x = LEFT
        if os.path.exists(COMPANY["logo"]):
            c.drawImage(COMPANY["logo"], LEFT, PAGE_H - 4.0 * cm, width=3.6 * cm,
                        height=2.0 * cm, preserveAspectRatio=True, anchor="w", mask="auto")
            text_x = LEFT + 4.2 * cm
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(text_x, PAGE_H - 2.9 * cm, COMPANY["name"])

        # Small grey address lines
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        y = PAGE_H - 4.3 * cm
        for line in COMPANY["header_lines"]:
            c.drawString(text_x, y, line)
            y -= 0.38 * cm

        # Teal divider under the header
        c.setStrokeColor(TEAL)
        c.setLineWidth(0.8)
        c.line(LEFT, PAGE_H - 5.4 * cm, PAGE_W - RIGHT, PAGE_H - 5.4 * cm)

        # Footer
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(LEFT, 1.9 * cm, PAGE_W - RIGHT, 1.9 * cm)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(LEFT, 1.4 * cm, COMPANY["footer"])
        c.drawRightString(PAGE_W - RIGHT, 1.4 * cm, f"Page {self._pageNumber} of {total}")

        c.restoreState()


# ---------- Reusable building blocks ----------
def info_bar(ref: str, date_text: str):
    """Grey bar: REFERENCE on the left, DATE on the right."""
    right_style = ParagraphStyle("r", parent=small, alignment=TA_RIGHT)
    t = Table(
        [[Paragraph(f"<b>REFERENCE</b>&nbsp;&nbsp;{escape(ref)}", small),
          Paragraph(f"<b>DATE</b>&nbsp;&nbsp;{escape(date_text)}", right_style)]],
        colWidths=[CONTENT_W * 0.65, CONTENT_W * 0.35],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def subject_line(text: str):
    return [
        Paragraph(f'<font color="#075E5B"><b>SUBJECT&nbsp;&nbsp;{escape(text)}</b></font>',
                  ParagraphStyle("subj", parent=body, spaceBefore=10, spaceAfter=2)),
        HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=10),
    ]


def details_table(rows):
    """rows = [(label, value), ...] -> shaded-label grid like 'Engagement details'."""
    label_style = ParagraphStyle("lab", parent=small, fontName="Helvetica-Bold")
    data = [[Paragraph(escape(k), label_style), Paragraph(escape(v), small)] for k, v in rows]
    t = Table(data, colWidths=[5.2 * cm, CONTENT_W - 5.2 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


class SigAnchor(Flowable):
    """Invisible space for the digital-signature stamp. It records where it was drawn."""

    def __init__(self, w=8 * cm, h=2.3 * cm):
        super().__init__()
        self.width, self.height = w, h

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        x, y = self.canv.absolutePosition(0, 0)
        ANCHOR["box"] = (x, y, x + self.width, y + self.height)
        ANCHOR["page"] = self.canv.getPageNumber() - 1     # 0-based page index


def signature_block(acceptance: bool = False):
    """Returns a list of flowables. The caller wraps it in KeepTogether."""
    label = ParagraphStyle("sg", parent=small, fontName="Helvetica-Bold", textColor=TEAL)
    items = [
        HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=10, spaceAfter=8),
        Paragraph("AUTHORIZED SIGNATORY", label),
        Spacer(1, 4),
        Paragraph(f"For {escape(COMPANY['name'])}", body),
        SigAnchor(),
        Paragraph(escape(COMPANY["signatory_name"]), small),
        Paragraph(escape(COMPANY["signatory_title"]), small),
    ]
    if acceptance:
        items += [
            Spacer(1, 0.8 * cm),
            Paragraph("CANDIDATE ACCEPTANCE: ____________________________"
                      "&nbsp;&nbsp;&nbsp;&nbsp;DATE: _______________", small),
        ]
    return items