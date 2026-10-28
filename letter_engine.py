import os
import re
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

import style
from style import (COMPANY, body, title, heading, clause_head, NumberedCanvas, LEFT, RIGHT,
                   TOP_MARGIN, BOTTOM_MARGIN, info_bar, subject_line,
                   details_table, signature_block)
from paths import app_path
from refs import next_reference

PRONOUNS = {
    "Male":   {"subj": "he",   "obj": "him",  "poss": "his"},
    "Female": {"subj": "she",  "obj": "her",  "poss": "her"},
    "Other":  {"subj": "they", "obj": "them", "poss": "their"},
}


def fmt_date(d: date) -> str:
    return d.strftime("%d-%B-%Y")          # 07-October-2026 (same as your sample)


def fmt_inr(n) -> str:
    """1250000 -> '12,50,000' (Indian digit grouping)."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    last3, rest = s[-3:], s[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return ",".join(parts + [last3])


def _make_path(ref: str, name: str, output_dir):
    """File name includes the reference number, so two people with the same name never clash."""
    output_dir = output_dir or app_path("output")
    os.makedirs(output_dir, exist_ok=True)
    safe_ref = ref.replace("/", "_")
    safe_name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return os.path.join(output_dir, f"{safe_ref}_{safe_name}.pdf")


def _build(path: str, story: list, doc_title: str):
    style.ANCHOR.clear()                   # forget the previous document's stamp position
    doc = SimpleDocTemplate(
        path, pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
        title=doc_title, author=COMPANY["name"],
    )
    doc.build(story, canvasmaker=NumberedCanvas)


# =====================================================================
def generate_experience_letter(data: dict, output_dir: str = None) -> str:
    name_raw = data["name"].strip().title()
    name, role = escape(name_raw), escape(data["role"])
    dept_raw = data.get("department", "")
    p = PRONOUNS[data.get("gender", "Other")]
    company = escape(COMPANY["name"])

    ref = data.get("reference") or next_reference(f"{COMPANY['ref_prefix']}/EXP", data["issue_date"])
    path = _make_path(ref, name_raw, output_dir)

    rows = [("Employee name", name_raw), ("Designation", data["role"])]
    if dept_raw:
        rows.append(("Department", dept_raw))
    rows += [("Date of joining", fmt_date(data["start_date"])),
             ("Last working day", fmt_date(data["end_date"]))]

    dept_text = f" in the {escape(dept_raw)} department" if dept_raw else ""

    story = [
        Paragraph("EXPERIENCE CERTIFICATE", title),
        info_bar(ref, fmt_date(data["issue_date"])),
        *subject_line("Experience certificate"),
        Paragraph("To Whom It May Concern,", body),
        Paragraph(f"This is to certify that <b>{name}</b> was employed with <b>{company}</b> "
                  f"as <b>{role}</b>{dept_text}. The details of service are given below.", body),
        Spacer(1, 4),
        details_table(rows),
        Spacer(1, 0.4 * cm),
        Paragraph(f"During this period, {p['poss']} conduct and performance were found to be "
                  f"satisfactory, and {p['subj']} was sincere and dedicated towards "
                  f"{p['poss']} responsibilities.", body),
        Paragraph(f"We wish {p['obj']} all the best in {p['poss']} future endeavours.", body),
        Spacer(1, 0.5 * cm),
        KeepTogether(signature_block()),
    ]
    _build(path, story, f"Experience Certificate - {name_raw}")
    return path


# =====================================================================
def generate_contract(data: dict, output_dir: str = None) -> str:
    name_raw = data["name"].strip().title()
    name, role = escape(name_raw), escape(data["role"])
    company = escape(COMPANY["name"])

    ref = data.get("reference") or next_reference(f"{COMPANY['ref_prefix']}/CON", data["issue_date"])
    path = _make_path(ref, name_raw, output_dir)

    key_terms = [
        ("Position", data["role"]),
        ("Joining date", fmt_date(data["start_date"])),
        ("Probation", f"{data['probation_months']} months"),
        ("Annual CTC", f"INR {fmt_inr(data['salary'])} per annum, payable monthly, "
                       "subject to statutory deductions."),
        ("Notice period", f"{data['notice_days']} days written notice, or salary in lieu."),
        ("Working hours", "9 hours per day, Monday to Friday."),
    ]

    # Add or remove clauses freely: (heading, text)
    clauses = [
        ("Position and duties",
         f"The Employee is appointed as <b>{role}</b> and shall perform the duties assigned "
         "by the Company from time to time."),
        ("Probation",
         "The Company may confirm or extend the probation period in writing."),
        ("Confidentiality",
         "The Employee shall not disclose confidential information of the Company "
         "during or after employment."),
        ("Governing law",
         "This agreement is governed by the laws of India. Courts in Pune shall have jurisdiction."),
    ]

    story = [
        Paragraph("EMPLOYMENT AGREEMENT", title),
        info_bar(ref, fmt_date(data["issue_date"])),
        Spacer(1, 0.4 * cm),
        Paragraph(f"<b>To:</b> {name}<br/>{escape(data.get('address', ''))}", body),
        *subject_line("Employment agreement"),
        Paragraph(f"Dear {name},", body),
        Paragraph(f"This agreement is made between <b>{company}</b> (the \"Company\") and "
                  f"<b>{name}</b> (the \"Employee\") on the terms below.", body),
        Paragraph("Key terms", heading),
        details_table(key_terms),
        Paragraph("Terms and conditions", heading),
    ]

    # Hold the last clause back so it always sits on the same page as the signatures
    tail = []
    for i, (head, text) in enumerate(clauses, start=1):
        block = [Paragraph(f"{i}. {escape(head)}", clause_head), Paragraph(text, body)]
        if i == len(clauses):
            tail = block
        else:
            story += block

    tail += [
        Spacer(1, 0.3 * cm),
        Paragraph("Please indicate acceptance by signing below and returning a copy to HR.", body),
    ]
    story.append(KeepTogether(tail + signature_block(acceptance=True)))

    _build(path, story, f"Employment Agreement - {name_raw}")
    return path


# ---------- Quick test ----------
if __name__ == "__main__":
    sample = {
        "name": "rahul sharma", "role": "Software Engineer", "department": "Engineering",
        "gender": "Male", "address": "Flat 12, Kothrud, Pune 411038",
        "salary": 1250000, "probation_months": 6, "notice_days": 60,
        "start_date": date(2026, 11, 1), "end_date": date(2027, 10, 31),
        "issue_date": date.today(),
    }
    print("Letter:  ", generate_experience_letter(sample))
    print("Contract:", generate_contract(sample))