import csv
from datetime import datetime, date

from letter_engine import generate_experience_letter, PRONOUNS
from signer import sign_pdf
from drive_sync import upload_pdf, get_service, get_or_create_folder


def parse_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unrecognised date '{text}' (use DD-MM-YYYY)")


def row_to_data(row: dict) -> dict:
    """Convert one CSV row into the dict the engine expects, or raise ValueError."""
    name = (row.get("name") or "").strip().title()
    role = (row.get("role") or "").strip()
    if not name or not role:
        raise ValueError("name and role are required")

    gender = (row.get("gender") or "Other").strip().title()
    if gender not in PRONOUNS:
        raise ValueError(f"gender must be Male, Female or Other, not '{gender}'")

    start = parse_date(row.get("start_date") or "")
    end = parse_date(row.get("end_date") or "")
    if end < start:
        raise ValueError("end_date is before start_date")

    issue_text = (row.get("issue_date") or "").strip()
    return {
        "name": name, "role": role,
        "department": (row.get("department") or "").strip(),
        "gender": gender, "start_date": start, "end_date": end,
        "issue_date": parse_date(issue_text) if issue_text else date.today(),
    }


def run_bulk(csv_path: str, upload: bool = False, progress=None) -> list:
    """Process every row. Returns a list of {line, name, ok, error} dicts."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    service = folder_id = None
    if upload:                                   # log in once, reuse for all rows
        service = get_service()
        folder_id = get_or_create_folder(service)

    results = []
    for i, row in enumerate(rows, start=2):      # line 1 is the header
        label = (row.get("name") or "?").strip()
        try:
            data = row_to_data(row)
            signed = sign_pdf(generate_experience_letter(data))
            if upload:
                upload_pdf(signed, service, folder_id)
            results.append({"line": i, "name": label, "ok": True, "error": ""})
        except Exception as e:
            results.append({"line": i, "name": label, "ok": False, "error": str(e)})
        if progress:
            progress(len(results), len(rows))
    return results


if __name__ == "__main__":
    for r in run_bulk("employees.csv", upload=False):
        print(r)